"""
StartupPilot AI — Knowledge Compiler

LLM-powered agent that compiles raw document chunks and agent outputs
into structured wiki pages (TopicPage + EntityPage).

Supports:
    - Document compilation: raw chunks → topic/entity pages
    - Agent output compilation: agent results → living wiki pages
    - Incremental updates: merge into existing pages, bump version
    - Cross-reference detection: link topics ↔ entities automatically
    - Persistence: save/load wiki to/from JSON files

Interview talking point:
    "The Knowledge Compiler is itself an LLM-powered agent. It reads raw
     chunks, extracts structured topics and named entities, builds
     cross-references, and persists everything as a navigable wiki.
     It supports incremental updates — new documents merge into existing
     pages rather than creating duplicates."
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from knowledge_wiki.models import (
    EntityPage,
    EntityType,
    KnowledgeWiki,
    PageSource,
    TopicCategory,
    TopicPage,
    slugify,
)

logger = logging.getLogger(__name__)


# ── Compiler Prompts ──────────────────────────────────────────────────────────

TOPIC_EXTRACTION_PROMPT = """You are a Knowledge Compiler. Given document chunks about a startup idea, identify and structure the main topics.

Startup Idea: {startup_idea}

Document Content:
{content}

For each distinct topic you identify, output valid JSON (no markdown fences):
{{
  "topics": [
    {{
      "title": "Short descriptive title",
      "category": "market|technology|regulation|industry|strategy|financial|general",
      "summary": "2-3 sentence overview of this topic",
      "content": "Detailed structured content in markdown. Include specific data, numbers, and analysis.",
      "key_facts": ["Specific fact or statistic 1", "Specific fact or statistic 2"],
      "entity_mentions": ["Company A", "Technology B"]
    }}
  ]
}}

Rules:
- Group related information into coherent topics (do NOT create one topic per chunk)
- Each topic must be self-contained and useful on its own
- Extract specific facts, numbers, and claims as key_facts
- Identify ALL named entities mentioned (companies, technologies, regulations)
- Use these categories: market, technology, regulation, industry, strategy, financial, general
- Output ONLY valid JSON, no extra text"""

ENTITY_EXTRACTION_PROMPT = """You are an Entity Extractor. Given content about a startup idea, extract all named entities and their attributes.

Startup Idea: {startup_idea}

Content:
{content}

Output valid JSON (no markdown fences):
{{
  "entities": [
    {{
      "name": "Entity Name",
      "entity_type": "company|person|product|technology|regulation|organization",
      "summary": "Brief description",
      "attributes": {{
        "key1": "value1",
        "key2": "value2"
      }},
      "context_snippets": ["A sentence mentioning this entity..."]
    }}
  ]
}}

Rules:
- Extract ALL named entities, even minor ones
- For companies: include funding, founded year, strengths, weaknesses where available
- For technologies: include category, maturity level, use cases
- For regulations: include jurisdiction, impact, requirements
- For products: include features, pricing, target market
- Output ONLY valid JSON, no extra text"""


# ── Knowledge Compiler ────────────────────────────────────────────────────────


class KnowledgeCompiler:
    """LLM-powered agent that compiles raw content into structured wiki pages.

    Supports two compilation modes:
    1. Document compilation: raw uploaded document chunks
    2. Agent output compilation: results from agent analysis steps

    Both modes produce TopicPage and EntityPage instances that are merged
    into the project's KnowledgeWiki with incremental update support.

    Usage:
        compiler = KnowledgeCompiler()
        wiki = compiler.compile_documents(project_id, chunks, startup_idea)
        wiki = compiler.compile_agent_output(project_id, agent_type, output, startup_idea)
    """

    def __init__(self, wiki_dir: Optional[str] = None) -> None:
        self._wiki_dir = Path(wiki_dir or self._default_wiki_dir())
        self._wiki_dir.mkdir(parents=True, exist_ok=True)
        self._wiki_cache: dict[str, KnowledgeWiki] = {}

        logger.info("KnowledgeCompiler initialized. Storage: %s", self._wiki_dir)

    @staticmethod
    def _default_wiki_dir() -> str:
        from config import WIKI_DIR
        return str(WIKI_DIR)

    # ── Public API ────────────────────────────────────────────────────────

    def compile_documents(
        self,
        project_id: str,
        chunks: list[Any],
        startup_idea: str,
    ) -> KnowledgeWiki:
        """Compile document chunks into wiki pages.

        This is the primary entry point for document upload compilation.
        Chunks are LangChain Document objects from rag/loaders.py.

        Args:
            project_id: The project to compile for.
            chunks: List of LangChain Document objects (already chunked).
            startup_idea: The startup idea for context.

        Returns:
            Updated KnowledgeWiki for the project.
        """
        logger.info(
            "Compiling %d document chunks into wiki for project %s",
            len(chunks),
            project_id,
        )

        # Load or create wiki
        wiki = self._load_or_create(project_id)

        # Combine chunk content for LLM processing
        # Process in batches to stay within token limits
        batch_size = 5
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            content = "\n\n---\n\n".join(
                getattr(c, "page_content", str(c)) for c in batch
            )
            chunk_ids = [
                getattr(c, "metadata", {}).get("chunk_index", str(i + j))
                for j, c in enumerate(batch)
            ]

            # Extract topics
            topics = self._extract_topics(
                content, startup_idea, chunk_ids, PageSource.DOCUMENT
            )
            for topic in topics:
                self._merge_topic(wiki, topic)

            # Extract entities
            entities = self._extract_entities(
                content, startup_idea, chunk_ids, PageSource.DOCUMENT
            )
            for entity in entities:
                self._merge_entity(wiki, entity)

        # Build cross-references between topics and entities
        self._build_cross_references(wiki)

        wiki.compilation_count += 1
        wiki.updated_at = datetime.now(timezone.utc)

        # Persist
        self._save(wiki)

        logger.info(
            "Wiki compilation complete for %s: %d topics, %d entities",
            project_id,
            len(wiki.topic_pages),
            len(wiki.entity_pages),
        )

        return wiki

    def compile_agent_output(
        self,
        project_id: str,
        agent_type: str,
        output: str,
        startup_idea: str,
    ) -> KnowledgeWiki:
        """Compile an agent's output into wiki pages (living wiki).

        Called after each agent node completes. Extracts topics and entities
        from the agent's analysis and merges them into the wiki.

        Args:
            project_id: The project ID.
            agent_type: Which agent produced this output (e.g., 'research').
            output: The agent's text output.
            startup_idea: The startup idea for context.

        Returns:
            Updated KnowledgeWiki.
        """
        if not output or len(output) < 50:
            logger.debug("Agent output too short to compile: %s", agent_type)
            return self._load_or_create(project_id)

        logger.info(
            "Compiling %s agent output into wiki for project %s (%d chars)",
            agent_type,
            project_id,
            len(output),
        )

        wiki = self._load_or_create(project_id)

        source_ids = [f"agent:{agent_type}"]

        # Extract topics from agent output
        topics = self._extract_topics(
            output, startup_idea, source_ids, PageSource.AGENT
        )
        for topic in topics:
            self._merge_topic(wiki, topic)

        # Extract entities
        entities = self._extract_entities(
            output, startup_idea, source_ids, PageSource.AGENT
        )
        for entity in entities:
            self._merge_entity(wiki, entity)

        # Rebuild cross-references
        self._build_cross_references(wiki)

        wiki.compilation_count += 1
        wiki.updated_at = datetime.now(timezone.utc)
        self._save(wiki)

        logger.info(
            "Agent wiki update for %s: now %d topics, %d entities",
            project_id,
            len(wiki.topic_pages),
            len(wiki.entity_pages),
        )

        return wiki

    def get_wiki(self, project_id: str) -> Optional[KnowledgeWiki]:
        """Get the compiled wiki for a project, or None if not compiled."""
        if project_id in self._wiki_cache:
            return self._wiki_cache[project_id]
        return self._load_from_disk(project_id)

    # ── LLM Extraction ────────────────────────────────────────────────────

    def _extract_topics(
        self,
        content: str,
        startup_idea: str,
        source_ids: list[str],
        source_type: PageSource,
    ) -> list[TopicPage]:
        """Use LLM to extract structured topics from content."""
        try:
            from llm_router.router import LLMRouter

            router = LLMRouter()
            llm = router.get_llm("evaluation")  # Use cheap/fast model

            prompt = TOPIC_EXTRACTION_PROMPT.format(
                startup_idea=startup_idea,
                content=content[:6000],  # Token budget
            )

            response = llm.invoke(prompt)
            response_text = (
                response.content
                if hasattr(response, "content")
                else str(response)
            )

            data = self._parse_json_response(response_text)
            topics_data = data.get("topics", [])

            pages = []
            for t in topics_data:
                try:
                    category = self._parse_category(t.get("category", "general"))
                    page = TopicPage(
                        page_id=f"topic_{slugify(t['title'])}",
                        title=t["title"],
                        category=category,
                        summary=t.get("summary", ""),
                        content=t.get("content", ""),
                        key_facts=t.get("key_facts", []),
                        related_entities=[
                            f"entity_{slugify(e)}"
                            for e in t.get("entity_mentions", [])
                        ],
                        source_chunks=source_ids,
                        source_type=source_type,
                    )
                    pages.append(page)
                except Exception as e:
                    logger.warning("Failed to create topic page: %s", e)

            logger.info("Extracted %d topic pages from content", len(pages))
            return pages

        except Exception as e:
            logger.warning(
                "Topic extraction failed (LLM unavailable?): %s. "
                "Falling back to heuristic extraction.",
                e,
            )
            return self._heuristic_topic_extraction(
                content, startup_idea, source_ids, source_type
            )

    def _extract_entities(
        self,
        content: str,
        startup_idea: str,
        source_ids: list[str],
        source_type: PageSource,
    ) -> list[EntityPage]:
        """Use LLM to extract named entities from content."""
        try:
            from llm_router.router import LLMRouter

            router = LLMRouter()
            llm = router.get_llm("evaluation")

            prompt = ENTITY_EXTRACTION_PROMPT.format(
                startup_idea=startup_idea,
                content=content[:6000],
            )

            response = llm.invoke(prompt)
            response_text = (
                response.content
                if hasattr(response, "content")
                else str(response)
            )

            data = self._parse_json_response(response_text)
            entities_data = data.get("entities", [])

            pages = []
            for e in entities_data:
                try:
                    entity_type = self._parse_entity_type(
                        e.get("entity_type", "company")
                    )
                    mentions = [
                        {"source": ",".join(source_ids), "context_snippet": s}
                        for s in e.get("context_snippets", [])
                    ]
                    page = EntityPage(
                        page_id=f"entity_{slugify(e['name'])}",
                        name=e["name"],
                        entity_type=entity_type,
                        summary=e.get("summary", ""),
                        attributes=e.get("attributes", {}),
                        mentions=mentions,
                        source_chunks=source_ids,
                        source_type=source_type,
                    )
                    pages.append(page)
                except Exception as ex:
                    logger.warning("Failed to create entity page: %s", ex)

            logger.info("Extracted %d entity pages from content", len(pages))
            return pages

        except Exception as e:
            logger.warning(
                "Entity extraction failed: %s. Falling back to heuristic.",
                e,
            )
            return self._heuristic_entity_extraction(
                content, source_ids, source_type
            )

    # ── Incremental Merge ─────────────────────────────────────────────────

    def _merge_topic(self, wiki: KnowledgeWiki, new_page: TopicPage) -> None:
        """Merge a new topic page into the wiki.

        If a page with the same ID exists:
        - Append new key_facts (deduplicated)
        - Merge content (append new sections)
        - Merge related entities
        - Bump version
        """
        if new_page.page_id in wiki.topic_pages:
            existing = wiki.topic_pages[new_page.page_id]

            # Merge key facts (deduplicate)
            existing_facts = set(existing.key_facts)
            for fact in new_page.key_facts:
                if fact not in existing_facts:
                    existing.key_facts.append(fact)

            # Merge related entities
            existing_entities = set(existing.related_entities)
            for eid in new_page.related_entities:
                if eid not in existing_entities:
                    existing.related_entities.append(eid)

            # Merge source chunks
            existing_sources = set(existing.source_chunks)
            for src in new_page.source_chunks:
                if src not in existing_sources:
                    existing.source_chunks.append(src)
            # Append content if substantially different
            if new_page.content_hash() != existing.content_hash():
                existing.content += f"\n\n---\n\n### Update (v{existing.version + 1})\n{new_page.content}"
                
                # Prevent text growth bloat by keeping only the original definition + the last 4 updates
                parts = existing.content.split("\n\n---\n\n")
                if len(parts) > 5:
                    existing.content = parts[0] + "\n\n---\n\n" + "\n\n---\n\n".join(parts[-4:])

            # Update summary if new one is longer/better
            if len(new_page.summary) > len(existing.summary):
                existing.summary = new_page.summary

            existing.version += 1
            existing.updated_at = datetime.now(timezone.utc)
            existing.confidence = max(existing.confidence, new_page.confidence)

            logger.debug("Merged topic page '%s' (v%d)", existing.title, existing.version)
        else:
            wiki.add_topic_page(new_page)
            logger.debug("Created new topic page: '%s'", new_page.title)

    def _merge_entity(self, wiki: KnowledgeWiki, new_page: EntityPage) -> None:
        """Merge a new entity page into the wiki.

        If an entity with the same ID exists:
        - Merge attributes (new values override old for same keys)
        - Append new mentions
        - Merge related entities/topics
        - Bump version
        """
        if new_page.page_id in wiki.entity_pages:
            existing = wiki.entity_pages[new_page.page_id]

            # Merge attributes (new overrides old)
            existing.attributes.update(new_page.attributes)

            # Append new mentions
            existing.mentions.extend(new_page.mentions)

            # Merge related
            existing_related = set(existing.related_entities)
            for rid in new_page.related_entities:
                if rid not in existing_related:
                    existing.related_entities.append(rid)

            existing_topics = set(existing.related_topics)
            for tid in new_page.related_topics:
                if tid not in existing_topics:
                    existing.related_topics.append(tid)

            # Merge sources
            existing_sources = set(existing.source_chunks)
            for src in new_page.source_chunks:
                if src not in existing_sources:
                    existing.source_chunks.append(src)

            # Update summary if new one is more detailed
            if len(new_page.summary) > len(existing.summary):
                existing.summary = new_page.summary

            existing.version += 1
            existing.updated_at = datetime.now(timezone.utc)
            existing.confidence = max(existing.confidence, new_page.confidence)

            logger.debug("Merged entity page '%s' (v%d)", existing.name, existing.version)
        else:
            wiki.add_entity_page(new_page)
            logger.debug("Created new entity page: '%s'", new_page.name)

    # ── Cross-Reference Builder ───────────────────────────────────────────

    def _build_cross_references(self, wiki: KnowledgeWiki) -> None:
        """Build bidirectional links between topics and entities.

        Scans topic content for entity name mentions, and entity summaries
        for topic title mentions. Updates related_* fields on both sides.
        """
        # For each topic, find which entities it mentions
        for topic in wiki.topic_pages.values():
            content_lower = topic.content.lower() + " " + topic.summary.lower()
            for entity in wiki.entity_pages.values():
                if entity.name.lower() in content_lower:
                    if entity.page_id not in topic.related_entities:
                        topic.related_entities.append(entity.page_id)
                    if topic.page_id not in entity.related_topics:
                        entity.related_topics.append(topic.page_id)

        # Rebuild index cross-references
        for topic in wiki.topic_pages.values():
            wiki.index.add_topic(topic)
        for entity in wiki.entity_pages.values():
            wiki.index.add_entity(entity)

    # ── Persistence ───────────────────────────────────────────────────────

    def _load_or_create(self, project_id: str) -> KnowledgeWiki:
        """Load existing wiki from cache/disk, or create a new one."""
        if project_id in self._wiki_cache:
            return self._wiki_cache[project_id]

        loaded = self._load_from_disk(project_id)
        if loaded:
            self._wiki_cache[project_id] = loaded
            return loaded

        wiki = KnowledgeWiki(project_id=project_id)
        self._wiki_cache[project_id] = wiki
        return wiki

    def _save(self, wiki: KnowledgeWiki) -> None:
        """Persist wiki to disk as JSON."""
        project_dir = self._wiki_dir / wiki.project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        wiki_path = project_dir / "wiki.json"
        try:
            wiki_path.write_text(
                wiki.model_dump_json(indent=2),
                encoding="utf-8",
            )
            self._wiki_cache[wiki.project_id] = wiki
            logger.info("Wiki saved to %s", wiki_path)
        except Exception as e:
            logger.error("Failed to save wiki: %s", e)

    def _load_from_disk(self, project_id: str) -> Optional[KnowledgeWiki]:
        """Load wiki from JSON file on disk."""
        wiki_path = self._wiki_dir / project_id / "wiki.json"
        if wiki_path.exists():
            try:
                data = json.loads(wiki_path.read_text(encoding="utf-8"))
                wiki = KnowledgeWiki.model_validate(data)
                logger.info("Loaded wiki from disk for project %s", project_id)
                return wiki
            except Exception as e:
                logger.error("Failed to load wiki: %s", e)
        return None

    # ── Heuristic Fallbacks ───────────────────────────────────────────────
    # Used when LLM is unavailable (no API key / rate limited)

    def _heuristic_topic_extraction(
        self,
        content: str,
        startup_idea: str,
        source_ids: list[str],
        source_type: PageSource,
    ) -> list[TopicPage]:
        """Fallback topic extraction using text heuristics."""
        pages = []

        # Split on markdown headers
        sections = re.split(r'\n#{1,3}\s+', content)
        for i, section in enumerate(sections):
            if len(section.strip()) < 100:
                continue

            # Extract title from first line
            lines = section.strip().split("\n")
            title = lines[0].strip("# ").strip()
            if not title or len(title) > 80:
                title = f"Section {i + 1} — {startup_idea[:30]}"

            # Guess category from content keywords
            category = self._guess_category(section)

            # Extract bullet points as key facts
            key_facts = [
                line.strip("- •*").strip()
                for line in lines
                if line.strip().startswith(("-", "•", "*"))
                and len(line.strip()) > 20
            ][:8]

            page = TopicPage(
                page_id=f"topic_{slugify(title)}",
                title=title,
                category=category,
                summary=lines[0][:200] if lines else "",
                content=section.strip(),
                key_facts=key_facts,
                source_chunks=source_ids,
                source_type=source_type,
                confidence=0.5,  # Lower confidence for heuristic
            )
            pages.append(page)

        return pages[:10]  # Cap at 10 topics

    def _heuristic_entity_extraction(
        self,
        content: str,
        source_ids: list[str],
        source_type: PageSource,
    ) -> list[EntityPage]:
        """Fallback entity extraction using regex patterns."""
        pages = []
        seen_names: set[str] = set()

        # Match capitalized multi-word names (likely company/product names)
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        matches = re.findall(pattern, content)

        for name in matches:
            if name in seen_names or len(name) < 4:
                continue
            seen_names.add(name)

            page = EntityPage(
                page_id=f"entity_{slugify(name)}",
                name=name,
                entity_type=EntityType.COMPANY,
                summary=f"Entity mentioned in analysis context.",
                mentions=[{"source": ",".join(source_ids), "context_snippet": name}],
                source_chunks=source_ids,
                source_type=source_type,
                confidence=0.3,
            )
            pages.append(page)

        return pages[:20]  # Cap

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_json_response(text: str) -> dict:
        """Parse JSON from LLM response, handling markdown fences."""
        # Strip markdown code fences if present
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            logger.warning("Could not parse JSON from LLM response")
            return {}

    @staticmethod
    def _parse_category(value: str) -> TopicCategory:
        """Parse a category string into TopicCategory enum."""
        try:
            return TopicCategory(value.lower().strip())
        except ValueError:
            return TopicCategory.GENERAL

    @staticmethod
    def _parse_entity_type(value: str) -> EntityType:
        """Parse an entity type string into EntityType enum."""
        try:
            return EntityType(value.lower().strip())
        except ValueError:
            return EntityType.COMPANY

    @staticmethod
    def _guess_category(content: str) -> TopicCategory:
        """Guess topic category from content keywords."""
        lower = content.lower()
        scores = {
            TopicCategory.MARKET: sum(
                w in lower
                for w in ["market", "tam", "sam", "som", "revenue", "pricing", "customer"]
            ),
            TopicCategory.TECHNOLOGY: sum(
                w in lower
                for w in ["technology", "api", "cloud", "architecture", "software", "platform"]
            ),
            TopicCategory.REGULATION: sum(
                w in lower
                for w in ["regulation", "compliance", "hipaa", "gdpr", "legal", "law"]
            ),
            TopicCategory.INDUSTRY: sum(
                w in lower
                for w in ["industry", "sector", "trend", "growth", "adoption"]
            ),
            TopicCategory.STRATEGY: sum(
                w in lower
                for w in ["strategy", "competitive", "advantage", "positioning", "gtm"]
            ),
            TopicCategory.FINANCIAL: sum(
                w in lower
                for w in ["cost", "budget", "infrastructure", "pricing", "estimate"]
            ),
        }
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else TopicCategory.GENERAL
