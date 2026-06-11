"""
StartupPilot AI — Research Planner

Decomposes agent analysis objectives into sub-questions and maps them to entry-point wiki pages.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from knowledge_wiki.navigator import WikiNavigator
from llm_router.router import LLMRouter
from research_platform.models import ResearchPlan, ResearchSubQuestion

logger = logging.getLogger(__name__)

PLANNER_PROMPT = """You are a Research Planner. Your task is to decompose a research objective for an AI agent into 2-3 specific sub-questions and map them to available pages in a Knowledge Wiki.

Startup Idea: {startup_idea}
Agent Type: {agent_type}

Available Wiki Pages:
{available_pages}

Output valid JSON matching this schema (do NOT use markdown formatting or fences):
{{
  "sub_questions": [
    {{
      "question_id": "q1",
      "text": "Specific research sub-question",
      "target_pages": ["page_id_1", "page_id_2"]
    }}
  ]
}}

Rules:
- Decompose the task into 2-3 specific, actionable sub-questions.
- Map each sub-question only to page_ids that are highly relevant from the "Available Wiki Pages" list.
- If no pages seem relevant for a sub-question, leave "target_pages" empty.
- Output ONLY valid JSON, no extra text."""


class ResearchPlanner:
    """Decomposes an agent's objective into sub-questions and entry-point wiki pages."""

    def __init__(self, router: Optional[LLMRouter] = None) -> None:
        self._router = router or LLMRouter()

    def plan(
        self,
        project_id: str,
        startup_idea: str,
        agent_type: str,
        navigator: WikiNavigator,
    ) -> ResearchPlan:
        """Create a research plan by decomposing the objective and mapping target pages.

        Args:
            project_id: The active project ID.
            startup_idea: The startup idea context.
            agent_type: The role of the agent executing (e.g. 'research').
            navigator: The wiki navigator to query available pages.

        Returns:
            A completed ResearchPlan object.
        """
        logger.info("Generating research plan for %s on project %s", agent_type, project_id)
        
        # Gather all pages in the wiki to present to the LLM
        all_pages = navigator.get_all_pages()
        
        # If the wiki is completely empty, return a default empty-mapped plan
        if not all_pages:
            logger.info("Wiki is empty for project %s. Using default empty-target plan.", project_id)
            return self._heuristic_plan(project_id, startup_idea, agent_type, navigator)

        try:
            # Build text representation of available pages
            pages_list = []
            for p in all_pages:
                page_type = "topic" if hasattr(p, "category") else "entity"
                category_or_type = p.category.value if page_type == "topic" else p.entity_type.value
                pages_list.append(
                    f"- Page ID: {p.page_id} | Type: {page_type} | Category: {category_or_type} | Title/Name: {p.title if page_type == 'topic' else p.name}\n"
                    f"  Summary: {p.summary}"
                )
            pages_text = "\n".join(pages_list)

            # Get LLM via router
            llm = self._router.get_llm(task_type="evaluation")
            prompt = PLANNER_PROMPT.format(
                startup_idea=startup_idea,
                agent_type=agent_type,
                available_pages=pages_text
            )

            response = llm.invoke(prompt)
            response_text = response.content if hasattr(response, "content") else str(response)
            
            data = self._parse_json_response(response_text)
            sub_questions_data = data.get("sub_questions", [])

            sub_questions = []
            for idx, sq in enumerate(sub_questions_data, 1):
                # Ensure targeted pages actually exist in the wiki
                valid_targets = [
                    pid for pid in sq.get("target_pages", [])
                    if navigator.get_page(pid) is not None
                ]
                
                sub_questions.append(
                    ResearchSubQuestion(
                        question_id=sq.get("question_id") or f"q{idx}",
                        text=sq["text"],
                        target_pages=valid_targets,
                        status="pending"
                    )
                )

            if sub_questions:
                logger.info("LLM Planner successfully created %d sub-questions", len(sub_questions))
                return ResearchPlan(
                    project_id=project_id,
                    startup_idea=startup_idea,
                    agent_type=agent_type,
                    sub_questions=sub_questions
                )

        except Exception as e:
            logger.warning("LLM planning failed: %s. Falling back to heuristic planner.", e)

        # Fallback to heuristic decomposition
        return self._heuristic_plan(project_id, startup_idea, agent_type, navigator)

    def _heuristic_plan(
        self,
        project_id: str,
        startup_idea: str,
        agent_type: str,
        navigator: WikiNavigator,
    ) -> ResearchPlan:
        """Fallback static decomposition of objectives based on agent type."""
        logger.info("Running heuristic planner for agent %s", agent_type)
        
        # Deconstruct templates
        templates = {
            "research": [
                ("What are the core industry dynamics and growth drivers?", ["industry"]),
                ("What is the regulatory and compliance landscape?", ["regulation"])
            ],
            "market_analysis": [
                ("What is the addressable market size (TAM/SAM/SOM)?", ["market"]),
                ("What are the primary customer segments and pricing?", ["market", "financial"])
            ],
            "competitor_analysis": [
                ("Who are the direct and indirect competitors?", ["company"]),
                ("What are the competitors' funding, strengths, and weaknesses?", ["company"])
            ],
            "swot_analysis": [
                ("What are the internal strengths and weaknesses of the startup idea?", ["market", "strategy"]),
                ("What are the external opportunities and threats in the industry?", ["market", "regulation", "industry"])
            ],
            "business_strategy": [
                ("What is the recommended go-to-market (GTM) strategy?", ["strategy"]),
                ("What are the pricing benchmarks and revenue models?", ["market", "financial"])
            ],
            "architecture_design": [
                ("What is the recommended technology stack?", ["technology"]),
                ("How do we ensure security and compliance in the architecture?", ["regulation", "technology"])
            ],
            "cost_estimation": [
                ("What are the baseline infrastructure costs at MVP stage?", ["financial", "technology"]),
                ("How do costs scale with growth?", ["financial"])
            ]
        }

        # Get sub-question specs for the agent, default to general if unknown
        specs = templates.get(agent_type) or [
            ("What is the primary objective of this phase?", ["general"]),
            ("What are the key dependencies and facts?", ["general"])
        ]

        sub_questions = []
        all_pages = navigator.get_all_pages()

        for idx, (text, cats) in enumerate(specs, 1):
            target_ids = []
            
            # Map based on page categories or entity types
            for p in all_pages:
                is_topic = hasattr(p, "category")
                p_cat = p.category.value if is_topic else p.entity_type.value
                if p_cat in cats:
                    target_ids.append(p.page_id)
            
            sub_questions.append(
                ResearchSubQuestion(
                    question_id=f"q{idx}",
                    text=text,
                    target_pages=target_ids,
                    status="pending"
                )
            )

        return ResearchPlan(
            project_id=project_id,
            startup_idea=startup_idea,
            agent_type=agent_type,
            sub_questions=sub_questions
        )

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
