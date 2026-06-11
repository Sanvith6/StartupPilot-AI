"""
StartupPilot AI — Context Assembler

Assembles optimized, agent-specific context from the Knowledge Wiki.
This is the bridge between the wiki and the LLM — it translates
structured wiki pages into the ideal context string for each agent type.

Key design:
    - Each agent type has a context map defining what wiki content it needs
    - Combines: wiki topics, entities, backlinks, and memory references
    - Falls back to raw document retrieval if no wiki exists
    - Respects a token budget to avoid prompt overflow
    - Formats context with source attribution for explainability

Interview talking point:
    "The Context Assembler is agent-aware. The Competitor Analyst gets
     company entities and market topics. The Cloud Architect gets technology
     topics. Context is assembled from the wiki with source attribution,
     not random chunks."
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from knowledge_wiki.models import (
    EntityPage,
    EntityType,
    KnowledgeWiki,
    TopicCategory,
    TopicPage,
)
from knowledge_wiki.navigator import WikiNavigator

logger = logging.getLogger(__name__)


# ── Agent Context Configuration ───────────────────────────────────────────────

# Maps each agent type to the wiki content categories it needs.
# The assembler uses this to filter which pages are relevant.

AGENT_CONTEXT_MAP: dict[str, dict[str, Any]] = {
    "research": {
        "topic_categories": [TopicCategory.INDUSTRY, TopicCategory.TECHNOLOGY, TopicCategory.GENERAL],
        "entity_types": [EntityType.TECHNOLOGY, EntityType.REGULATION, EntityType.ORGANIZATION],
        "priority": "breadth",  # Wants wide coverage
        "max_topics": 4,
        "max_entities": 6,
    },
    "market_analysis": {
        "topic_categories": [TopicCategory.MARKET, TopicCategory.INDUSTRY, TopicCategory.FINANCIAL],
        "entity_types": [EntityType.COMPANY, EntityType.PRODUCT],
        "priority": "depth",  # Wants detailed market data
        "max_topics": 3,
        "max_entities": 5,
    },
    "competitor_analysis": {
        "topic_categories": [TopicCategory.MARKET, TopicCategory.STRATEGY],
        "entity_types": [EntityType.COMPANY, EntityType.PRODUCT],
        "priority": "entities",  # Entity-heavy (needs companies)
        "max_topics": 2,
        "max_entities": 8,
    },
    "swot_analysis": {
        "topic_categories": [TopicCategory.MARKET, TopicCategory.INDUSTRY, TopicCategory.TECHNOLOGY],
        "entity_types": [EntityType.COMPANY, EntityType.TECHNOLOGY, EntityType.REGULATION],
        "priority": "breadth",
        "max_topics": 4,
        "max_entities": 5,
    },
    "business_strategy": {
        "topic_categories": [TopicCategory.MARKET, TopicCategory.STRATEGY, TopicCategory.INDUSTRY],
        "entity_types": [EntityType.COMPANY, EntityType.PRODUCT],
        "priority": "depth",
        "max_topics": 3,
        "max_entities": 4,
    },
    "architecture_design": {
        "topic_categories": [TopicCategory.TECHNOLOGY],
        "entity_types": [EntityType.TECHNOLOGY, EntityType.PRODUCT],
        "priority": "depth",
        "max_topics": 3,
        "max_entities": 6,
    },
    "cost_estimation": {
        "topic_categories": [TopicCategory.TECHNOLOGY, TopicCategory.FINANCIAL],
        "entity_types": [EntityType.TECHNOLOGY, EntityType.PRODUCT],
        "priority": "depth",
        "max_topics": 2,
        "max_entities": 4,
    },
    "report_writing": {
        "topic_categories": [
            TopicCategory.MARKET, TopicCategory.TECHNOLOGY,
            TopicCategory.INDUSTRY, TopicCategory.STRATEGY,
        ],
        "entity_types": [EntityType.COMPANY, EntityType.TECHNOLOGY],
        "priority": "breadth",
        "max_topics": 5,
        "max_entities": 5,
    },
}


# ── Context Assembler ─────────────────────────────────────────────────────────


class ContextAssembler:
    """Assembles agent-specific context from the Knowledge Wiki.

    Strategy:
    1. Look up which page categories this agent needs (AGENT_CONTEXT_MAP)
    2. Retrieve relevant pages from those categories
    3. Do a semantic search for query-specific pages
    4. Follow cross-references for deeper context
    5. Merge, deduplicate, and rank by relevance
    6. Format as structured context with source attribution
    7. Truncate to max_chars budget

    Usage:
        assembler = ContextAssembler(wiki)
        context = assembler.assemble("competitor_analysis", "AI healthcare scheduling")
    """

    def __init__(self, wiki: KnowledgeWiki) -> None:
        self._navigator = WikiNavigator(wiki)

    def assemble(
        self,
        agent_type: str,
        query: str,
        additional_context: str = "",
        max_chars: int = 4000,
    ) -> str:
        """Assemble optimized context for a specific agent from the wiki.

        Args:
            agent_type: Which agent this context is for.
            query: The search query (usually startup_idea + agent_type).
            additional_context: Extra context from prior agents or memory.
            max_chars: Maximum characters in the assembled context.

        Returns:
            Formatted context string with source attribution.
            Returns empty string if wiki is empty.
        """
        if self._navigator.is_empty():
            logger.debug("Wiki is empty for agent '%s'. No wiki context.", agent_type)
            return ""

        config = AGENT_CONTEXT_MAP.get(agent_type, AGENT_CONTEXT_MAP.get("research", {}))

        # ── 1. Category-based retrieval ───────────────────────────────────
        category_topics = self._get_category_topics(config)
        type_entities = self._get_type_entities(config)

        # ── 2. Query-based search (finds pages the category map might miss)
        search_results = self._navigator.search(
            query=f"{agent_type}: {query}",
            max_pages=3,
        )

        # ── 3. Cross-reference traversal for discovered pages ─────────────
        xref_pages = []
        top_page_ids = [p.page_id for p in (category_topics + type_entities)[:3]]
        for pid in top_page_ids:
            related = self._navigator.get_related(pid, max_results=2)
            xref_pages.extend(related)

        # ── 4. Deduplicate and merge all sources ──────────────────────────
        seen_ids: set[str] = set()
        topic_pages: list[TopicPage] = []
        entity_pages: list[EntityPage] = []

        for page in category_topics + [
            p for p in search_results if isinstance(p, TopicPage)
        ] + [p for p in xref_pages if isinstance(p, TopicPage)]:
            if page.page_id not in seen_ids:
                seen_ids.add(page.page_id)
                topic_pages.append(page)

        for page in type_entities + [
            p for p in search_results if isinstance(p, EntityPage)
        ] + [p for p in xref_pages if isinstance(p, EntityPage)]:
            if page.page_id not in seen_ids:
                seen_ids.add(page.page_id)
                entity_pages.append(page)

        # ── 5. Apply limits from config ───────────────────────────────────
        max_topics = config.get("max_topics", 4)
        max_entities = config.get("max_entities", 5)
        topic_pages = topic_pages[:max_topics]
        entity_pages = entity_pages[:max_entities]

        # ── 6. Format into structured context ─────────────────────────────
        context_parts: list[str] = []

        if topic_pages:
            context_parts.append("### 📖 Knowledge Wiki — Topics\n")
            for page in topic_pages:
                formatted = self._format_topic(page)
                context_parts.append(formatted)

        if entity_pages:
            context_parts.append("\n### 🏢 Knowledge Wiki — Entities\n")
            for page in entity_pages:
                formatted = self._format_entity(page)
                context_parts.append(formatted)

        if additional_context:
            context_parts.append(f"\n### 📝 Prior Analysis\n{additional_context}")

        # ── 7. Assemble and truncate ──────────────────────────────────────
        full_context = "\n".join(context_parts)

        if len(full_context) > max_chars:
            full_context = full_context[:max_chars - 50] + "\n\n[... context truncated for token budget]"

        logger.info(
            "Assembled %d chars of wiki context for '%s' (%d topics, %d entities)",
            len(full_context),
            agent_type,
            len(topic_pages),
            len(entity_pages),
        )

        return full_context

    def assemble_for_query(
        self,
        query: str,
        max_chars: int = 3000,
    ) -> str:
        """Assemble generic context for a search query (agent-agnostic).

        Used for ad-hoc retrieval when agent_type is unknown.
        """
        results = self._navigator.search(query, max_pages=6)
        if not results:
            return ""

        parts = ["### 📖 Knowledge Wiki Results\n"]
        for page in results:
            if isinstance(page, TopicPage):
                parts.append(self._format_topic(page))
            else:
                parts.append(self._format_entity(page))

        context = "\n".join(parts)
        if len(context) > max_chars:
            context = context[:max_chars - 50] + "\n\n[... truncated]"

        return context

    # ── Category/Type Retrieval ────────────────────────────────────────────

    def _get_category_topics(self, config: dict) -> list[TopicPage]:
        """Get topic pages for the categories this agent needs."""
        topics: list[TopicPage] = []
        for category in config.get("topic_categories", []):
            topics.extend(self._navigator.get_topics(category=category))
        return topics

    def _get_type_entities(self, config: dict) -> list[EntityPage]:
        """Get entity pages for the entity types this agent needs."""
        entities: list[EntityPage] = []
        for entity_type in config.get("entity_types", []):
            entities.extend(self._navigator.get_entities(entity_type=entity_type))
        return entities

    # ── Formatting ────────────────────────────────────────────────────────

    @staticmethod
    def _format_topic(page: TopicPage) -> str:
        """Format a topic page as agent-readable context."""
        parts = [f"**{page.title}** ({page.category.value})"]
        parts.append(page.summary)

        if page.key_facts:
            facts_str = "\n".join(f"  - {f}" for f in page.key_facts[:5])
            parts.append(f"Key Facts:\n{facts_str}")

        # Source attribution
        source_tag = (
            f"[source: {page.source_type.value}, v{page.version}]"
        )
        parts.append(source_tag)

        return "\n".join(parts) + "\n"

    @staticmethod
    def _format_entity(page: EntityPage) -> str:
        """Format an entity page as agent-readable context."""
        parts = [f"**{page.name}** ({page.entity_type.value})"]
        parts.append(page.summary)

        if page.attributes:
            attrs = []
            for k, v in list(page.attributes.items())[:6]:
                attrs.append(f"  - {k}: {v}")
            parts.append("\n".join(attrs))

        source_tag = (
            f"[source: {page.source_type.value}, v{page.version}]"
        )
        parts.append(source_tag)

        return "\n".join(parts) + "\n"
