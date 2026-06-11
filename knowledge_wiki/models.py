"""
StartupPilot AI — Knowledge Wiki Data Models

Pydantic models for the structured knowledge wiki system.
Every piece of knowledge is stored as either a TopicPage or EntityPage,
interconnected via cross-references and navigable through WikiIndex.

Design decisions:
    - Pages are versioned with timestamps for freshness tracking
    - Each page tracks its source (document chunk vs agent output)
    - Cross-references are bidirectional (stored on both sides)
    - WikiIndex enables O(1) lookups by category, type, and keyword
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────


class TopicCategory(str, Enum):
    """Categories for topic pages."""
    MARKET = "market"
    TECHNOLOGY = "technology"
    REGULATION = "regulation"
    INDUSTRY = "industry"
    STRATEGY = "strategy"
    FINANCIAL = "financial"
    GENERAL = "general"


class EntityType(str, Enum):
    """Types of named entities."""
    COMPANY = "company"
    PERSON = "person"
    PRODUCT = "product"
    TECHNOLOGY = "technology"
    REGULATION = "regulation"
    ORGANIZATION = "organization"


class PageSource(str, Enum):
    """Origin of the knowledge — document upload or agent output."""
    DOCUMENT = "document"
    AGENT = "agent"


# ── Page Models ───────────────────────────────────────────────────────────────


class TopicPage(BaseModel):
    """A wiki page organized around a topic or theme.

    Topics are compiled from document chunks or agent outputs.
    Examples: 'Healthcare Scheduling Market', 'HIPAA Compliance',
              'AI Appointment Optimization Technology'.
    """

    page_id: str = Field(
        ..., description="Unique ID: 'topic_{slugified_title}'"
    )
    title: str = Field(
        ..., description="Human-readable topic title"
    )
    category: TopicCategory = Field(
        ..., description="Topic category for index navigation"
    )
    summary: str = Field(
        ..., description="2-3 sentence overview"
    )
    content: str = Field(
        ..., description="Full structured content (markdown)"
    )
    key_facts: list[str] = Field(
        default_factory=list,
        description="Extracted factual claims with specifics",
    )
    related_entities: list[str] = Field(
        default_factory=list,
        description="Entity page IDs this topic references",
    )
    related_topics: list[str] = Field(
        default_factory=list,
        description="Other topic page IDs cross-referenced",
    )
    source_chunks: list[str] = Field(
        default_factory=list,
        description="Original chunk IDs or agent types this was compiled from",
    )
    source_type: PageSource = Field(
        default=PageSource.DOCUMENT,
        description="Whether this came from an uploaded doc or agent output",
    )
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Compiler confidence in extraction quality",
    )
    version: int = Field(
        default=1,
        description="Incremented on each update",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def content_hash(self) -> str:
        """Hash of content for deduplication checks."""
        return hashlib.md5(self.content.encode()).hexdigest()[:12]


class EntityPage(BaseModel):
    """A wiki page about a specific named entity.

    Entities are companies, people, products, technologies, or regulations
    mentioned in documents or agent outputs.
    Examples: 'Zocdoc', 'HIPAA', 'AWS SageMaker'.
    """

    page_id: str = Field(
        ..., description="Unique ID: 'entity_{slugified_name}'"
    )
    name: str = Field(
        ..., description="Entity display name"
    )
    entity_type: EntityType = Field(
        ..., description="Entity classification"
    )
    summary: str = Field(
        ..., description="Brief description of the entity"
    )
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible key-value attributes (funding, founded, etc.)",
    )
    mentions: list[dict[str, str]] = Field(
        default_factory=list,
        description="[{source, context_snippet, sentiment}] — where this entity was mentioned",
    )
    related_entities: list[str] = Field(
        default_factory=list,
        description="Cross-references to other entity pages",
    )
    related_topics: list[str] = Field(
        default_factory=list,
        description="Topic pages that mention this entity",
    )
    source_chunks: list[str] = Field(
        default_factory=list,
        description="Chunk IDs or agent types that sourced this",
    )
    source_type: PageSource = Field(
        default=PageSource.DOCUMENT,
    )
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
    )
    version: int = Field(default=1)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def content_hash(self) -> str:
        """Hash of summary+attributes for deduplication."""
        raw = f"{self.summary}:{sorted(self.attributes.items())}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]


# ── Wiki Index ────────────────────────────────────────────────────────────────


class WikiIndex(BaseModel):
    """Navigable indexes for fast wiki lookup.

    Built automatically by the compiler after page creation.
    Enables O(1) lookups by category, type, keyword, and cross-reference.
    """

    topic_index: dict[str, list[str]] = Field(
        default_factory=dict,
        description="category → [topic_page_ids]",
    )
    entity_index: dict[str, list[str]] = Field(
        default_factory=dict,
        description="entity_type → [entity_page_ids]",
    )
    keyword_index: dict[str, list[str]] = Field(
        default_factory=dict,
        description="keyword → [page_ids (topic + entity)]",
    )
    cross_references: dict[str, list[str]] = Field(
        default_factory=dict,
        description="page_id → [related_page_ids] (bidirectional backlinks)",
    )

    def add_topic(self, page: TopicPage) -> None:
        """Register a topic page in all indexes."""
        cat = page.category.value
        if cat not in self.topic_index:
            self.topic_index[cat] = []
        if page.page_id not in self.topic_index[cat]:
            self.topic_index[cat].append(page.page_id)

        # Keyword index: extract words from title
        self._index_keywords(page.page_id, page.title)
        self._index_keywords(page.page_id, page.summary)

        # Cross-references
        self._add_cross_refs(page.page_id, page.related_entities)
        self._add_cross_refs(page.page_id, page.related_topics)

    def add_entity(self, page: EntityPage) -> None:
        """Register an entity page in all indexes."""
        etype = page.entity_type.value
        if etype not in self.entity_index:
            self.entity_index[etype] = []
        if page.page_id not in self.entity_index[etype]:
            self.entity_index[etype].append(page.page_id)

        # Keyword index
        self._index_keywords(page.page_id, page.name)
        self._index_keywords(page.page_id, page.summary)

        # Cross-references
        self._add_cross_refs(page.page_id, page.related_entities)
        self._add_cross_refs(page.page_id, page.related_topics)

    def _index_keywords(self, page_id: str, text: str) -> None:
        """Extract and index meaningful keywords from text."""
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "of", "in", "to", "for", "with", "on", "at", "from", "by",
            "about", "as", "into", "through", "during", "before", "after",
            "and", "but", "or", "nor", "not", "so", "yet", "both",
            "each", "every", "all", "any", "few", "more", "most",
            "other", "some", "such", "no", "only", "own", "same",
            "than", "too", "very", "just", "it", "its", "this", "that",
        }
        words = text.lower().split()
        for word in words:
            # Clean punctuation
            cleaned = "".join(c for c in word if c.isalnum())
            if cleaned and len(cleaned) > 2 and cleaned not in stop_words:
                if cleaned not in self.keyword_index:
                    self.keyword_index[cleaned] = []
                if page_id not in self.keyword_index[cleaned]:
                    self.keyword_index[cleaned].append(page_id)

    def _add_cross_refs(self, page_id: str, related_ids: list[str]) -> None:
        """Add bidirectional cross-references."""
        if page_id not in self.cross_references:
            self.cross_references[page_id] = []
        for related in related_ids:
            if related not in self.cross_references[page_id]:
                self.cross_references[page_id].append(related)
            # Bidirectional
            if related not in self.cross_references:
                self.cross_references[related] = []
            if page_id not in self.cross_references[related]:
                self.cross_references[related].append(page_id)

    def search_keywords(self, query: str) -> list[str]:
        """Find page IDs matching any keyword in the query."""
        query_words = query.lower().split()
        page_scores: dict[str, int] = {}
        for word in query_words:
            cleaned = "".join(c for c in word if c.isalnum())
            if cleaned in self.keyword_index:
                for page_id in self.keyword_index[cleaned]:
                    page_scores[page_id] = page_scores.get(page_id, 0) + 1

        # Sort by number of keyword hits
        sorted_pages = sorted(page_scores, key=page_scores.get, reverse=True)
        return sorted_pages

    def get_backlinks(self, page_id: str) -> list[str]:
        """Get all pages that reference this page."""
        return self.cross_references.get(page_id, [])


# ── Knowledge Wiki Container ─────────────────────────────────────────────────


class KnowledgeWiki(BaseModel):
    """Complete knowledge wiki for a project.

    Contains all topic pages, entity pages, and indexes.
    This is the unit that gets persisted and loaded per project.
    """

    project_id: str
    topic_pages: dict[str, TopicPage] = Field(
        default_factory=dict,
        description="page_id → TopicPage",
    )
    entity_pages: dict[str, EntityPage] = Field(
        default_factory=dict,
        description="page_id → EntityPage",
    )
    index: WikiIndex = Field(default_factory=WikiIndex)
    compilation_count: int = Field(
        default=0,
        description="Number of times compilation has run (incremental updates)",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def add_topic_page(self, page: TopicPage) -> None:
        """Add or update a topic page and rebuild index."""
        self.topic_pages[page.page_id] = page
        self.index.add_topic(page)
        self.updated_at = datetime.now(timezone.utc)

    def add_entity_page(self, page: EntityPage) -> None:
        """Add or update an entity page and rebuild index."""
        self.entity_pages[page.page_id] = page
        self.index.add_entity(page)
        self.updated_at = datetime.now(timezone.utc)

    def get_page(self, page_id: str) -> TopicPage | EntityPage | None:
        """Get any page by ID (topic or entity)."""
        return self.topic_pages.get(page_id) or self.entity_pages.get(page_id)

    def get_stats(self) -> dict[str, Any]:
        """Get wiki statistics for API responses."""
        return {
            "project_id": self.project_id,
            "total_topic_pages": len(self.topic_pages),
            "total_entity_pages": len(self.entity_pages),
            "total_keywords": len(self.index.keyword_index),
            "total_cross_references": sum(
                len(v) for v in self.index.cross_references.values()
            ),
            "compilation_count": self.compilation_count,
            "categories": {
                cat: len(ids)
                for cat, ids in self.index.topic_index.items()
            },
            "entity_types": {
                et: len(ids)
                for et, ids in self.index.entity_index.items()
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ── Utilities ─────────────────────────────────────────────────────────────────


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug for page IDs."""
    slug = text.lower().strip()
    slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)
    slug = "_".join(slug.split())
    return slug[:60]
