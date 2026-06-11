"""
StartupPilot AI — Wiki Navigator

Enables agents to browse, search, and traverse the Knowledge Wiki.
Provides semantic search, keyword lookup, category browsing,
entity lookup, and cross-reference traversal.

This is the "agent eyes" into the wiki — how agents discover
relevant knowledge before their tasks.

Interview talking point:
    "Agents don't just get raw chunks. They navigate a structured wiki
     using semantic search, keyword indexes, and cross-reference traversal.
     The Competitor Analyst agent can look up 'company' entities, follow
     backlinks to related market topics, and assemble exactly the context
     it needs."
"""

from __future__ import annotations

import logging
from typing import Optional, Union

from knowledge_wiki.models import (
    EntityPage,
    EntityType,
    KnowledgeWiki,
    TopicCategory,
    TopicPage,
)

logger = logging.getLogger(__name__)

PageType = Union[TopicPage, EntityPage]


class WikiNavigator:
    """Navigates the Knowledge Wiki to find relevant pages for agents.

    Supports multiple navigation strategies:
    1. Keyword search — match query words against the keyword index
    2. Category browse — get all topics in a category (market, tech, etc.)
    3. Entity lookup — find specific entities by name or type
    4. Cross-reference traversal — follow backlinks from a page
    5. Combined search — multi-signal ranking combining all strategies

    Usage:
        navigator = WikiNavigator(wiki)
        results = navigator.search("healthcare scheduling competitors", max_pages=5)
        companies = navigator.get_entities(entity_type=EntityType.COMPANY)
        related = navigator.get_related("entity_zocdoc")
    """

    def __init__(self, wiki: KnowledgeWiki) -> None:
        self._wiki = wiki

    @property
    def wiki(self) -> KnowledgeWiki:
        return self._wiki

    # ── Primary Search ────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        max_pages: int = 5,
        include_topics: bool = True,
        include_entities: bool = True,
    ) -> list[PageType]:
        """Multi-signal search across the wiki.

        Combines keyword index hits, title matching, and content relevance
        to rank and return the most relevant pages.

        Args:
            query: Natural language search query.
            max_pages: Maximum number of pages to return.
            include_topics: Whether to include topic pages.
            include_entities: Whether to include entity pages.

        Returns:
            List of TopicPage/EntityPage sorted by relevance.
        """
        if not query:
            return []

        # Score all pages
        page_scores: dict[str, float] = {}

        # Signal 1: Keyword index hits (strongest signal)
        keyword_hits = self._wiki.index.search_keywords(query)
        for i, page_id in enumerate(keyword_hits):
            # Decay score by position
            page_scores[page_id] = page_scores.get(page_id, 0) + max(1.0 - i * 0.1, 0.1)

        # Signal 2: Title/name matching
        query_lower = query.lower()
        query_words = set(query_lower.split())

        if include_topics:
            for page in self._wiki.topic_pages.values():
                title_words = set(page.title.lower().split())
                overlap = len(query_words & title_words)
                if overlap > 0:
                    score = overlap / max(len(query_words), 1) * 0.8
                    page_scores[page.page_id] = page_scores.get(page.page_id, 0) + score

        if include_entities:
            for page in self._wiki.entity_pages.values():
                # Exact name match is very strong
                if page.name.lower() in query_lower:
                    page_scores[page.page_id] = page_scores.get(page.page_id, 0) + 2.0
                else:
                    name_words = set(page.name.lower().split())
                    overlap = len(query_words & name_words)
                    if overlap > 0:
                        score = overlap / max(len(query_words), 1) * 0.6
                        page_scores[page.page_id] = page_scores.get(page.page_id, 0) + score

        # Signal 3: Key facts / summary content matching
        if include_topics:
            for page in self._wiki.topic_pages.values():
                fact_matches = sum(
                    1 for fact in page.key_facts
                    if any(w in fact.lower() for w in query_words if len(w) > 3)
                )
                if fact_matches:
                    page_scores[page.page_id] = page_scores.get(page.page_id, 0) + fact_matches * 0.3

        # Filter by type
        valid_ids = set()
        if include_topics:
            valid_ids.update(self._wiki.topic_pages.keys())
        if include_entities:
            valid_ids.update(self._wiki.entity_pages.keys())

        # Sort by score and return pages
        ranked = sorted(
            ((pid, score) for pid, score in page_scores.items() if pid in valid_ids),
            key=lambda x: x[1],
            reverse=True,
        )

        results: list[PageType] = []
        for page_id, _ in ranked[:max_pages]:
            page = self._wiki.get_page(page_id)
            if page:
                results.append(page)

        logger.debug(
            "Wiki search for '%s' → %d results (from %d scored)",
            query[:50],
            len(results),
            len(page_scores),
        )

        return results

    # ── Category Browsing ─────────────────────────────────────────────────

    def get_topics(
        self,
        category: Optional[TopicCategory] = None,
    ) -> list[TopicPage]:
        """Get topic pages, optionally filtered by category.

        Args:
            category: Filter by category (market, technology, etc.).
                      None returns all topics.

        Returns:
            List of TopicPage objects.
        """
        if category is None:
            return list(self._wiki.topic_pages.values())

        page_ids = self._wiki.index.topic_index.get(category.value, [])
        return [
            self._wiki.topic_pages[pid]
            for pid in page_ids
            if pid in self._wiki.topic_pages
        ]

    def get_entities(
        self,
        entity_type: Optional[EntityType] = None,
    ) -> list[EntityPage]:
        """Get entity pages, optionally filtered by type.

        Args:
            entity_type: Filter by type (company, technology, etc.).
                         None returns all entities.

        Returns:
            List of EntityPage objects.
        """
        if entity_type is None:
            return list(self._wiki.entity_pages.values())

        page_ids = self._wiki.index.entity_index.get(entity_type.value, [])
        return [
            self._wiki.entity_pages[pid]
            for pid in page_ids
            if pid in self._wiki.entity_pages
        ]

    # ── Entity Lookup ─────────────────────────────────────────────────────

    def get_entity_by_name(self, name: str) -> Optional[EntityPage]:
        """Find an entity page by name (case-insensitive)."""
        name_lower = name.lower()
        for page in self._wiki.entity_pages.values():
            if page.name.lower() == name_lower:
                return page
        return None

    # ── Cross-Reference Traversal ─────────────────────────────────────────

    def get_related(self, page_id: str, max_results: int = 10) -> list[PageType]:
        """Get pages related to a given page via cross-references.

        Follows backlinks in the index to find connected pages.

        Args:
            page_id: The page to find relations for.
            max_results: Maximum related pages to return.

        Returns:
            List of related TopicPage/EntityPage objects.
        """
        backlinks = self._wiki.index.get_backlinks(page_id)
        results: list[PageType] = []

        for related_id in backlinks[:max_results]:
            page = self._wiki.get_page(related_id)
            if page:
                results.append(page)

        return results

    # ── Page Retrieval ────────────────────────────────────────────────────

    def get_page(self, page_id: str) -> Optional[PageType]:
        """Get a specific page by ID."""
        return self._wiki.get_page(page_id)

    def get_all_pages(self) -> list[PageType]:
        """Get all pages in the wiki (topics + entities)."""
        pages: list[PageType] = []
        pages.extend(self._wiki.topic_pages.values())
        pages.extend(self._wiki.entity_pages.values())
        return pages

    # ── Statistics ────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get wiki navigation statistics."""
        return self._wiki.get_stats()

    def is_empty(self) -> bool:
        """Check if the wiki has any pages."""
        return (
            len(self._wiki.topic_pages) == 0
            and len(self._wiki.entity_pages) == 0
        )
