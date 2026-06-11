"""
StartupPilot AI — Multi-Hop Navigator

Step-by-step wiki network traversal, evidence extraction, and trace logging.
"""

from __future__ import annotations
import json
import logging
import re
import uuid
import threading
from datetime import datetime, timezone
from typing import Any, Optional, Union

_memory_lock = threading.Lock()

from knowledge_wiki.models import EntityPage, TopicPage
from knowledge_wiki.navigator import WikiNavigator
from llm_router.router import LLMRouter
from research_platform.models import (
    EvidenceItem,
    ResearchMemory,
    ResearchPlan,
    ResearchSubQuestion,
    ResearchTrace,
)

logger = logging.getLogger(__name__)

NAVIGATION_PROMPT = """You are an AI Researcher navigating a Knowledge Wiki to answer a specific research sub-question.

Sub-Question: {sub_question}

Current Page: {page_id}
Title/Name: {title}
Content:
{content}

Available Cross-References (Connected Pages):
{relations}

Already Visited Pages (do NOT revisit these to avoid loops):
{visited_pages}

Output valid JSON matching this schema (do NOT use markdown formatting or fences):
{{
  "evidence_found": "A specific factual claim or data point found on the current page that answers the sub-question, or null if none",
  "relevance_reasoning": "Explain why this evidence is relevant to answering the sub-question, or null",
  "reasoning_for_hop": "Your internal monologue: what did you learn on this page, and why are you choosing the next page to visit?",
  "next_page_to_visit": "The exact page_id of the next page to hop to from the Available Cross-References list, or null to stop"
}}

Rules:
- Read the content carefully. Extract at most one highly relevant evidence point.
- Choose "next_page_to_visit" ONLY from the "Available Cross-References" list.
- If you have gathered enough evidence, or none of the connected pages look relevant, set "next_page_to_visit" to null.
- Output ONLY valid JSON, no extra text."""


class MultiHopNavigator:
    """Agent that performs step-by-step navigation of the wiki, collecting evidence."""

    def __init__(
        self,
        router: Optional[LLMRouter] = None,
        max_depth: int = 4,
        memory_dir: Optional[str] = None
    ) -> None:
        self._router = router or LLMRouter()
        self._max_depth = max_depth
        self._memory = self._load_memory(memory_dir)

    def _load_memory(self, memory_dir: Optional[str]) -> ResearchMemory:
        # Load or create basic ResearchMemory
        # We can store it as a simple file inside memory directory
        from config import get_settings
        try:
            settings = get_settings()
            path = memory_dir or settings.memory_dir
        except Exception:
            path = "./data/memory"
            
        from pathlib import Path
        mem_path = Path(path) / "research_memory.json"
        
        if mem_path.exists():
            try:
                with _memory_lock:
                    data = json.loads(mem_path.read_text(encoding="utf-8"))
                return ResearchMemory.model_validate(data)
            except Exception:
                pass
        return ResearchMemory(project_id="global", successful_paths={})

    def _save_memory(self) -> None:
        from config import get_settings
        try:
            settings = get_settings()
            path = settings.memory_dir
        except Exception:
            path = "./data/memory"
            
        from pathlib import Path
        mem_path = Path(path) / "research_memory.json"
        mem_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with _memory_lock:
                mem_path.write_text(self._memory.model_dump_json(indent=2), encoding="utf-8")
        except Exception:
            pass

    def navigate(
        self,
        project_id: str,
        plan: ResearchPlan,
        navigator: WikiNavigator,
    ) -> ResearchTrace:
        """Execute step-by-step traversal across the wiki according to the plan.

        Args:
            project_id: Active project ID.
            plan: The ResearchPlan containing sub-questions.
            navigator: The WikiNavigator wrapper.

        Returns:
            A completed ResearchTrace.
        """
        logger.info("Starting Multi-Hop navigation on project %s", project_id)
        
        navigation_path = []
        evidence_gathered = []
        reasoning_chain = []
        max_achieved_depth = 0

        # Execute research path for each sub-question
        for sq in plan.sub_questions:
            logger.info("Exploring sub-question: '%s'", sq.text)
            
            # Determine starting page(s)
            start_pages = list(sq.target_pages)
            if not start_pages:
                # If no starting pages mapped, perform a quick keyword lookup to seed
                hits = navigator.search(sq.text, max_pages=2)
                start_pages = [p.page_id for p in hits]
                
            if not start_pages:
                # Still no starting page? Skip or log
                reasoning_chain.append(f"Sub-question '{sq.text}': No relevant entry pages found. Research skipped.")
                continue

            current_page_id = start_pages[0]
            visited = set()
            depth = 0

            # Check Research Memory for successful paths from previous queries
            mem_path = self._memory.get_path(f"{plan.agent_type}:{sq.text}")
            if mem_path:
                logger.info("Found cached research path in memory for query: %s", sq.text)
                # Re-traverse the cached path to gather fresh evidence
                for pid in mem_path:
                    if len(visited) >= self._max_depth:
                        break
                    page = navigator.get_page(pid)
                    if page:
                        current_page_id = pid
                        self._process_page_visit(
                            page=page,
                            sub_question=sq,
                            navigator=navigator,
                            visited=visited,
                            evidence_gathered=evidence_gathered,
                            reasoning_chain=reasoning_chain,
                            navigation_path=navigation_path
                        )
                sq.status = "completed"
                continue

            # Multi-Hop traversal loop
            while current_page_id and depth < self._max_depth:
                page = navigator.get_page(current_page_id)
                if not page or current_page_id in visited:
                    break
                
                visited.add(current_page_id)
                navigation_path.append(current_page_id)
                depth += 1
                max_achieved_depth = max(max_achieved_depth, depth)

                # Process the page: extract evidence and decide next hop
                next_page_id = self._process_step(
                    page=page,
                    sub_question=sq,
                    navigator=navigator,
                    visited=visited,
                    evidence_gathered=evidence_gathered,
                    reasoning_chain=reasoning_chain
                )
                
                current_page_id = next_page_id

            sq.status = "completed"
            
            # Cache the successful traversal path in memory
            if len(visited) > 1:
                self._memory.learn_path(f"{plan.agent_type}:{sq.text}", list(visited))
                self._save_memory()

        # Build final metrics
        metrics = {
            "pages_explored": len(set(navigation_path)),
            "evidence_count": len(evidence_gathered),
            "success": len(evidence_gathered) > 0,
            "max_depth": max_achieved_depth
        }

        logger.info(
            "Navigation trace finished: %d pages explored, %d evidence items gathered",
            metrics["pages_explored"],
            metrics["evidence_count"]
        )

        return ResearchTrace(
            project_id=project_id,
            agent_type=plan.agent_type,
            navigation_path=navigation_path,
            evidence_gathered=evidence_gathered,
            reasoning_chain=reasoning_chain,
            depth=max_achieved_depth,
            metrics=metrics
        )

    def _process_step(
        self,
        page: Union[TopicPage, EntityPage],
        sub_question: ResearchSubQuestion,
        navigator: WikiNavigator,
        visited: set[str],
        evidence_gathered: list[EvidenceItem],
        reasoning_chain: list[str]
    ) -> Optional[str]:
        """Perform a single step of hop evaluation."""
        page_type = "topic" if hasattr(page, "category") else "entity"
        title = page.title if page_type == "topic" else page.name
        content = page.content if page_type == "topic" else page.summary
        
        # Get relations
        related_pages = navigator.get_related(page.page_id)
        relations_text = "\n".join(
            f"- Page ID: {r.page_id} | Title: {r.title if hasattr(r, 'title') else r.name}"
            for r in related_pages
        )

        try:
            llm = self._router.get_llm(task_type="evaluation")
            prompt = NAVIGATION_PROMPT.format(
                sub_question=sub_question.text,
                page_id=page.page_id,
                title=title,
                content=content[:5000],
                relations=relations_text or "No connected pages available.",
                visited_pages=", ".join(visited) or "None"
            )

            response = llm.invoke(prompt)
            response_text = response.content if hasattr(response, "content") else str(response)
            
            decision = self._parse_json_response(response_text)
            
            # Extract evidence
            fact = decision.get("evidence_found")
            reasoning = decision.get("relevance_reasoning")
            if fact:
                evidence_gathered.append(
                    EvidenceItem(
                        evidence_id=str(uuid.uuid4())[:8],
                        page_id=page.page_id,
                        title_or_name=title,
                        fact=fact,
                        relevance_reasoning=reasoning or "Relevant fact."
                    )
                )

            # Log reasoning chain
            reasoning_chain.append(
                f"[{page.page_id}] {decision.get('reasoning_for_hop') or 'Browsing page.'}"
            )

            # Route to next page
            next_page = decision.get("next_page_to_visit")
            if next_page and next_page in [r.page_id for r in related_pages] and next_page not in visited:
                return next_page

        except Exception as e:
            logger.warning("LLM multi-hop traversal evaluation failed: %s. Using heuristic.", e)

        # Fallback to heuristic hop traversal
        return self._heuristic_process_step(
            page=page,
            sub_question=sub_question,
            navigator=navigator,
            visited=visited,
            evidence_gathered=evidence_gathered,
            reasoning_chain=reasoning_chain
        )

    def _process_page_visit(
        self,
        page: Union[TopicPage, EntityPage],
        sub_question: ResearchSubQuestion,
        navigator: WikiNavigator,
        visited: set[str],
        evidence_gathered: list[EvidenceItem],
        reasoning_chain: list[str],
        navigation_path: list[str]
    ) -> None:
        """Shorthand processor when running from memory (re-traversing cached path)."""
        visited.add(page.page_id)
        navigation_path.append(page.page_id)
        page_type = "topic" if hasattr(page, "category") else "entity"
        title = page.title if page_type == "topic" else page.name
        
        # Heuristically extract simple facts
        content = page.content if page_type == "topic" else page.summary
        facts = self._extract_heuristic_evidence_facts(content, sub_question.text)
        if facts:
            evidence_gathered.append(
                EvidenceItem(
                    evidence_id=str(uuid.uuid4())[:8],
                    page_id=page.page_id,
                    title_or_name=title,
                    fact=facts[0],
                    relevance_reasoning=f"Identified relevance from memory trace for question: {sub_question.text}"
                )
            )
        reasoning_chain.append(
            f"[{page.page_id}] Traversed cached memory path. Explored facts on {title}."
        )

    def _heuristic_process_step(
        self,
        page: Union[TopicPage, EntityPage],
        sub_question: ResearchSubQuestion,
        navigator: WikiNavigator,
        visited: set[str],
        evidence_gathered: list[EvidenceItem],
        reasoning_chain: list[str]
    ) -> Optional[str]:
        """Deterministic search/hop routing when LLM is unavailable."""
        page_type = "topic" if hasattr(page, "category") else "entity"
        title = page.title if page_type == "topic" else page.name
        content = page.content if page_type == "topic" else page.summary

        # 1. Look for sentences containing query keywords to extract as evidence
        facts = self._extract_heuristic_evidence_facts(content, sub_question.text)
        if facts:
            evidence_gathered.append(
                EvidenceItem(
                    evidence_id=str(uuid.uuid4())[:8],
                    page_id=page.page_id,
                    title_or_name=title,
                    fact=facts[0],
                    relevance_reasoning=f"Extracted heuristically for keywords matching '{sub_question.text}'"
                )
            )

        # 2. Pick next hop from cross-references
        related_pages = navigator.get_related(page.page_id)
        unvisited_relations = [r for r in related_pages if r.page_id not in visited]

        if not unvisited_relations:
            reasoning_chain.append(
                f"[{page.page_id}] Explored page. No unvisited connected pages found. Traversal complete."
            )
            return None

        # Prioritize relation whose title or category matches query keywords
        query_words = set(sub_question.text.lower().split())
        best_hop = unvisited_relations[0]
        max_overlap = -1

        for r in unvisited_relations:
            r_title = r.title if hasattr(r, "title") else r.name
            r_words = set(r_title.lower().split())
            overlap = len(query_words & r_words)
            if overlap > max_overlap:
                max_overlap = overlap
                best_hop = r

        reasoning_chain.append(
            f"[{page.page_id}] Heuristically analyzing relations. Decided to follow cross-reference to "
            f"'{best_hop.title if hasattr(best_hop, 'title') else best_hop.name}' ({best_hop.page_id})."
        )

        return best_hop.page_id

    def _extract_heuristic_evidence_facts(self, content: str, query: str) -> list[str]:
        """Splits content into sentences and filters for simple matching claims."""
        sentences = re.split(r'\. |\n', content)
        query_words = [w.lower() for w in query.split() if len(w) > 3]
        matches = []
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) > 15:
                if any(w in s_clean.lower() for w in query_words):
                    matches.append(s_clean)
        return matches[:2]

    @staticmethod
    def _parse_json_response(text: str) -> dict:
        """Parse JSON response, stripping markdown fences."""
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            raise
