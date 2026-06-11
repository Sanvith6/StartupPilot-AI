"""
StartupPilot AI — Knowledge Wiki Tests

Tests for the Knowledge Wiki system: models, compiler, navigator,
context assembler, and integration with the API.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# ══════════════════════════════════════════════════════════════════════════════
# Unit Tests: Models
# ══════════════════════════════════════════════════════════════════════════════


def test_topic_page_creation():
    """Test TopicPage model creation and validation."""
    from knowledge_wiki.models import TopicPage, TopicCategory, PageSource

    page = TopicPage(
        page_id="topic_healthcare_market",
        title="Healthcare Market Overview",
        category=TopicCategory.MARKET,
        summary="The healthcare market is growing rapidly.",
        content="## Healthcare Market\n\nDetailed content here.",
        key_facts=["Market size: $45B", "CAGR: 15.8%"],
        related_entities=["entity_zocdoc"],
        source_type=PageSource.DOCUMENT,
    )

    assert page.page_id == "topic_healthcare_market"
    assert page.category == TopicCategory.MARKET
    assert len(page.key_facts) == 2
    assert page.version == 1
    assert page.confidence == 0.8
    assert page.content_hash()  # Produces a hash


def test_entity_page_creation():
    """Test EntityPage model creation and validation."""
    from knowledge_wiki.models import EntityPage, EntityType, PageSource

    page = EntityPage(
        page_id="entity_zocdoc",
        name="Zocdoc",
        entity_type=EntityType.COMPANY,
        summary="Healthcare scheduling marketplace.",
        attributes={"funding": "$375M", "founded": "2007"},
        mentions=[{"source": "doc_1", "context_snippet": "Zocdoc raised $375M"}],
        source_type=PageSource.DOCUMENT,
    )

    assert page.name == "Zocdoc"
    assert page.entity_type == EntityType.COMPANY
    assert page.attributes["funding"] == "$375M"
    assert len(page.mentions) == 1


def test_wiki_index_keyword_search():
    """Test WikiIndex keyword indexing and search."""
    from knowledge_wiki.models import (
        WikiIndex, TopicPage, TopicCategory, PageSource,
    )

    index = WikiIndex()
    page = TopicPage(
        page_id="topic_ai_healthcare",
        title="AI Healthcare Market Trends",
        category=TopicCategory.MARKET,
        summary="AI is transforming healthcare.",
        content="Content here.",
    )
    index.add_topic(page)

    # Search for keywords
    results = index.search_keywords("healthcare market")
    assert "topic_ai_healthcare" in results

    # Search for non-matching keywords
    results = index.search_keywords("blockchain crypto")
    assert "topic_ai_healthcare" not in results


def test_wiki_index_cross_references():
    """Test bidirectional cross-references in WikiIndex."""
    from knowledge_wiki.models import (
        WikiIndex, TopicPage, EntityPage,
        TopicCategory, EntityType,
    )

    index = WikiIndex()
    topic = TopicPage(
        page_id="topic_market",
        title="Market Overview",
        category=TopicCategory.MARKET,
        summary="Market summary.",
        content="Content.",
        related_entities=["entity_zocdoc"],
    )
    entity = EntityPage(
        page_id="entity_zocdoc",
        name="Zocdoc",
        entity_type=EntityType.COMPANY,
        summary="Healthcare marketplace.",
        related_topics=["topic_market"],
    )
    index.add_topic(topic)
    index.add_entity(entity)

    # Check bidirectional backlinks
    backlinks = index.get_backlinks("topic_market")
    assert "entity_zocdoc" in backlinks

    backlinks = index.get_backlinks("entity_zocdoc")
    assert "topic_market" in backlinks


def test_knowledge_wiki_container():
    """Test KnowledgeWiki add/get/stats operations."""
    from knowledge_wiki.models import (
        KnowledgeWiki, TopicPage, EntityPage,
        TopicCategory, EntityType,
    )

    wiki = KnowledgeWiki(project_id="test-project")

    topic = TopicPage(
        page_id="topic_market",
        title="Market Overview",
        category=TopicCategory.MARKET,
        summary="Growing fast.",
        content="Details.",
        key_facts=["$45B TAM"],
    )
    entity = EntityPage(
        page_id="entity_company_a",
        name="Company A",
        entity_type=EntityType.COMPANY,
        summary="A competitor.",
    )

    wiki.add_topic_page(topic)
    wiki.add_entity_page(entity)

    assert wiki.get_page("topic_market") is not None
    assert wiki.get_page("entity_company_a") is not None
    assert wiki.get_page("nonexistent") is None

    stats = wiki.get_stats()
    assert stats["total_topic_pages"] == 1
    assert stats["total_entity_pages"] == 1
    assert stats["project_id"] == "test-project"


def test_slugify():
    """Test the slugify utility."""
    from knowledge_wiki.models import slugify

    assert slugify("Healthcare Market Overview") == "healthcare_market_overview"
    assert slugify("AI & ML Trends!") == "ai_ml_trends"
    assert slugify("  spaces  ") == "spaces"


# ══════════════════════════════════════════════════════════════════════════════
# Unit Tests: Navigator
# ══════════════════════════════════════════════════════════════════════════════


def test_navigator_search():
    """Test WikiNavigator multi-signal search."""
    from knowledge_wiki.models import (
        KnowledgeWiki, TopicPage, EntityPage,
        TopicCategory, EntityType,
    )
    from knowledge_wiki.navigator import WikiNavigator

    wiki = KnowledgeWiki(project_id="test")
    wiki.add_topic_page(TopicPage(
        page_id="topic_market", title="Healthcare Market",
        category=TopicCategory.MARKET, summary="Growing market.",
        content="Market content.", key_facts=["$45B"],
    ))
    wiki.add_topic_page(TopicPage(
        page_id="topic_tech", title="AI Technology Stack",
        category=TopicCategory.TECHNOLOGY, summary="Modern AI stack.",
        content="Tech content.",
    ))
    wiki.add_entity_page(EntityPage(
        page_id="entity_zocdoc", name="Zocdoc",
        entity_type=EntityType.COMPANY, summary="Marketplace.",
    ))

    nav = WikiNavigator(wiki)

    # Search should find relevant pages
    results = nav.search("healthcare market")
    assert len(results) > 0
    page_ids = [p.page_id for p in results]
    assert "topic_market" in page_ids

    # Entity name search
    results = nav.search("Zocdoc")
    assert any(
        getattr(p, "name", "") == "Zocdoc" or getattr(p, "title", "") == "Zocdoc"
        for p in results
    )


def test_navigator_category_browse():
    """Test browsing topics by category."""
    from knowledge_wiki.models import (
        KnowledgeWiki, TopicPage, TopicCategory,
    )
    from knowledge_wiki.navigator import WikiNavigator

    wiki = KnowledgeWiki(project_id="test")
    wiki.add_topic_page(TopicPage(
        page_id="topic_m1", title="Market 1",
        category=TopicCategory.MARKET, summary="S1", content="C1",
    ))
    wiki.add_topic_page(TopicPage(
        page_id="topic_t1", title="Tech 1",
        category=TopicCategory.TECHNOLOGY, summary="S2", content="C2",
    ))

    nav = WikiNavigator(wiki)

    market_topics = nav.get_topics(category=TopicCategory.MARKET)
    assert len(market_topics) == 1
    assert market_topics[0].page_id == "topic_m1"

    tech_topics = nav.get_topics(category=TopicCategory.TECHNOLOGY)
    assert len(tech_topics) == 1


def test_navigator_empty_wiki():
    """Test navigator with empty wiki."""
    from knowledge_wiki.models import KnowledgeWiki
    from knowledge_wiki.navigator import WikiNavigator

    wiki = KnowledgeWiki(project_id="empty")
    nav = WikiNavigator(wiki)

    assert nav.is_empty() is True
    assert nav.search("anything") == []
    assert nav.get_topics() == []
    assert nav.get_entities() == []


# ══════════════════════════════════════════════════════════════════════════════
# Unit Tests: Context Assembler
# ══════════════════════════════════════════════════════════════════════════════


def test_context_assembler_agent_specific():
    """Test that context assembler returns agent-appropriate content."""
    from knowledge_wiki.models import (
        KnowledgeWiki, TopicPage, EntityPage,
        TopicCategory, EntityType,
    )
    from knowledge_wiki.context_assembler import ContextAssembler

    wiki = KnowledgeWiki(project_id="test")
    wiki.add_topic_page(TopicPage(
        page_id="topic_market", title="Healthcare Market",
        category=TopicCategory.MARKET, summary="$45B market.",
        content="Market details.", key_facts=["$45B TAM", "15% CAGR"],
    ))
    wiki.add_entity_page(EntityPage(
        page_id="entity_zocdoc", name="Zocdoc",
        entity_type=EntityType.COMPANY, summary="Scheduling marketplace.",
        attributes={"funding": "$375M"},
    ))
    wiki.add_topic_page(TopicPage(
        page_id="topic_tech", title="Cloud Architecture",
        category=TopicCategory.TECHNOLOGY, summary="AWS stack.",
        content="Tech details.",
    ))

    assembler = ContextAssembler(wiki)

    # Competitor analysis agent should get companies
    context = assembler.assemble("competitor_analysis", "healthcare scheduling")
    assert "Zocdoc" in context
    assert "Knowledge Wiki" in context

    # Architecture agent should get technology content
    context = assembler.assemble("architecture_design", "healthcare scheduling")
    assert "Knowledge Wiki" in context


def test_context_assembler_empty_wiki():
    """Test assembler with empty wiki returns empty string."""
    from knowledge_wiki.models import KnowledgeWiki
    from knowledge_wiki.context_assembler import ContextAssembler

    wiki = KnowledgeWiki(project_id="empty")
    assembler = ContextAssembler(wiki)

    result = assembler.assemble("research", "test query")
    assert result == ""


def test_context_assembler_max_chars():
    """Test that context assembler respects max_chars budget."""
    from knowledge_wiki.models import (
        KnowledgeWiki, TopicPage, TopicCategory,
    )
    from knowledge_wiki.context_assembler import ContextAssembler

    wiki = KnowledgeWiki(project_id="test")
    # Add a page with lots of content
    wiki.add_topic_page(TopicPage(
        page_id="topic_big", title="Big Topic",
        category=TopicCategory.MARKET,
        summary="A big topic.",
        content="x" * 5000,
        key_facts=[f"Fact {i}" for i in range(20)],
    ))

    assembler = ContextAssembler(wiki)
    context = assembler.assemble("market_analysis", "test", max_chars=500)
    assert len(context) <= 500


# ══════════════════════════════════════════════════════════════════════════════
# Unit Tests: Compiler
# ══════════════════════════════════════════════════════════════════════════════


def test_compiler_heuristic_topic_extraction():
    """Test heuristic topic extraction (used when LLM is unavailable)."""
    from knowledge_wiki.compiler import KnowledgeCompiler
    from knowledge_wiki.models import PageSource

    compiler = KnowledgeCompiler()

    content = """
## Healthcare Market Overview

The healthcare scheduling market is valued at $45 billion.
Key trends include:
- AI adoption growing at 15% CAGR
- Telehealth integration accelerating
- Value-based care driving efficiency

## Regulatory Landscape

HIPAA compliance is mandatory for patient data handling.
- PHI encryption required
- BAA agreements with cloud providers
- Annual security audits
"""

    topics = compiler._heuristic_topic_extraction(
        content=content,
        startup_idea="AI healthcare scheduling",
        source_ids=["test"],
        source_type=PageSource.DOCUMENT,
    )

    assert len(topics) >= 1
    # Should identify market and regulation categories
    categories = {t.category.value for t in topics}
    assert len(categories) >= 1


def test_compiler_heuristic_entity_extraction():
    """Test heuristic entity extraction."""
    from knowledge_wiki.compiler import KnowledgeCompiler
    from knowledge_wiki.models import PageSource

    compiler = KnowledgeCompiler()

    content = """
Zocdoc has raised $375M in funding and dominates the patient marketplace.
Luma Health focuses on patient engagement. Qventus uses AI for operations.
"""

    entities = compiler._heuristic_entity_extraction(
        content=content,
        source_ids=["test"],
        source_type=PageSource.DOCUMENT,
    )

    # Should find multi-word capitalized names
    names = {e.name for e in entities}
    assert "Luma Health" in names


def test_compiler_incremental_merge(tmp_path):
    """Test incremental updates merge into existing pages."""
    from knowledge_wiki.compiler import KnowledgeCompiler
    from knowledge_wiki.models import (
        KnowledgeWiki, TopicPage, TopicCategory, PageSource,
    )

    compiler = KnowledgeCompiler(wiki_dir=str(tmp_path))

    wiki = KnowledgeWiki(project_id="merge-test")

    # Add initial page
    page1 = TopicPage(
        page_id="topic_market",
        title="Market Overview",
        category=TopicCategory.MARKET,
        summary="Small summary.",
        content="Initial content.",
        key_facts=["Fact A"],
    )
    compiler._merge_topic(wiki, page1)
    assert wiki.topic_pages["topic_market"].version == 1

    # Merge update with new facts
    page2 = TopicPage(
        page_id="topic_market",
        title="Market Overview",
        category=TopicCategory.MARKET,
        summary="A longer and better summary for the market.",
        content="Updated content with new data.",
        key_facts=["Fact A", "Fact B"],
    )
    compiler._merge_topic(wiki, page2)

    merged = wiki.topic_pages["topic_market"]
    assert merged.version == 2
    assert "Fact B" in merged.key_facts
    # Summary should be updated (longer is better)
    assert "longer" in merged.summary


def test_compiler_persistence(tmp_path):
    """Test wiki save/load round-trip."""
    from knowledge_wiki.compiler import KnowledgeCompiler
    from knowledge_wiki.models import (
        KnowledgeWiki, TopicPage, TopicCategory,
    )

    compiler = KnowledgeCompiler(wiki_dir=str(tmp_path))

    # Create and save wiki
    wiki = KnowledgeWiki(project_id="persist-test")
    wiki.add_topic_page(TopicPage(
        page_id="topic_test",
        title="Test Topic",
        category=TopicCategory.GENERAL,
        summary="A test.",
        content="Test content.",
    ))
    compiler._save(wiki)

    # Verify file exists
    wiki_file = tmp_path / "persist-test" / "wiki.json"
    assert wiki_file.exists()

    # Clear cache and reload
    compiler._wiki_cache.clear()
    loaded = compiler._load_from_disk("persist-test")

    assert loaded is not None
    assert loaded.project_id == "persist-test"
    assert "topic_test" in loaded.topic_pages
    assert loaded.topic_pages["topic_test"].title == "Test Topic"


# ══════════════════════════════════════════════════════════════════════════════
# Integration: API Endpoints
# ══════════════════════════════════════════════════════════════════════════════


def test_wiki_api_404_when_not_compiled(client: TestClient):
    """Test wiki API returns 404 when no wiki exists."""
    response = client.get("/wiki/nonexistent-project")
    assert response.status_code == 404


def test_existing_api_still_works(client: TestClient):
    """Verify existing endpoints are unaffected by wiki changes."""
    # Health check
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    # Agents
    response = client.get("/agents")
    assert response.status_code == 200
    assert len(response.json()["agents"]) == 8

    # Demo scenarios
    response = client.get("/demo/scenarios")
    assert response.status_code == 200
    assert len(response.json()["scenarios"]) == 5
