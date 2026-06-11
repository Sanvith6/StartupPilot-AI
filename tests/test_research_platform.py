"""
StartupPilot AI — Research Platform Tests

Tests for the Research Planner, Multi-Hop Navigator, memory, state integration, and API.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from knowledge_wiki.models import KnowledgeWiki, TopicPage, TopicCategory, PageSource
from knowledge_wiki.navigator import WikiNavigator
from research_platform.models import (
    ResearchSubQuestion,
    ResearchPlan,
    EvidenceItem,
    ResearchTrace,
    ResearchMemory,
)
from research_platform.planner import ResearchPlanner
from research_platform.navigator import MultiHopNavigator


# ══════════════════════════════════════════════════════════════════════════════
# Unit Tests: Models
# ══════════════════════════════════════════════════════════════════════════════

def test_research_models():
    """Verify pydantic models validate fields properly."""
    sub_q = ResearchSubQuestion(
        question_id="q1",
        text="What are the competitor strengths?",
        target_pages=["entity_zocdoc"],
        status="pending"
    )
    assert sub_q.question_id == "q1"
    assert sub_q.status == "pending"

    plan = ResearchPlan(
        project_id="test-p",
        startup_idea="test idea",
        agent_type="research",
        sub_questions=[sub_q]
    )
    assert len(plan.sub_questions) == 1

    evidence = EvidenceItem(
        evidence_id="ev-1",
        page_id="entity_zocdoc",
        title_or_name="Zocdoc",
        fact="Zocdoc raised $375M.",
        relevance_reasoning="Funding evaluation."
    )
    assert evidence.evidence_id == "ev-1"

    trace = ResearchTrace(
        project_id="test-p",
        agent_type="research",
        navigation_path=["topic_market", "entity_zocdoc"],
        evidence_gathered=[evidence],
        reasoning_chain=["Visited topic_market first", "Hopped to entity_zocdoc"],
        depth=2,
        metrics={"pages_explored": 2}
    )
    assert trace.depth == 2
    assert len(trace.evidence_gathered) == 1


def test_research_memory():
    """Verify ResearchMemory learns and retrieves traversal paths."""
    mem = ResearchMemory(project_id="global")
    mem.learn_path("research:dynamics", ["topic_1", "topic_2"])
    
    assert mem.get_path("research:dynamics") == ["topic_1", "topic_2"]
    assert mem.get_path("nonexistent") is None


# ══════════════════════════════════════════════════════════════════════════════
# Unit Tests: Planner & Navigator Logic
# ══════════════════════════════════════════════════════════════════════════════

def test_research_planner_heuristic():
    """Verify planner decomposes objectives and targets appropriate categories."""
    wiki = KnowledgeWiki(project_id="test-p")
    wiki.add_topic_page(TopicPage(
        page_id="topic_industry_overview",
        title="Healthcare Scheduling Industry Overview",
        category=TopicCategory.INDUSTRY,
        summary="Industry trends.",
        content="General overview of healthcare.",
    ))
    wiki.add_topic_page(TopicPage(
        page_id="topic_regulatory_landscape",
        title="HIPAA Regulatory Compliance",
        category=TopicCategory.REGULATION,
        summary="Regulatory requirements.",
        content="Compliance rules.",
    ))

    navigator = WikiNavigator(wiki)
    planner = ResearchPlanner()
    
    # Run planning
    plan = planner.plan(
        project_id="test-p",
        startup_idea="AI healthcare scheduling",
        agent_type="research",
        navigator=navigator
    )

    assert plan.project_id == "test-p"
    assert len(plan.sub_questions) == 2
    
    # Check that q1 maps to industry and q2 to regulation
    q1 = plan.sub_questions[0]
    q2 = plan.sub_questions[1]
    assert "topic_industry_overview" in q1.target_pages
    assert "topic_regulatory_landscape" in q2.target_pages


def test_multi_hop_navigator_heuristic(tmp_path):
    """Verify navigator hops step-by-step, following relations and extracting evidence."""
    wiki = KnowledgeWiki(project_id="test-p")
    
    # 1. Topic page referring to Zocdoc
    wiki.add_topic_page(TopicPage(
        page_id="topic_market_opportunity",
        title="AI Healthcare Market Opportunity",
        category=TopicCategory.MARKET,
        summary="TAM/SAM/SOM sizing and competitor mentions.",
        content="The scheduling market has direct competitor Zocdoc dominating patient search.",
        related_entities=["entity_zocdoc"]
    ))
    
    # 2. Entity page about Zocdoc
    from knowledge_wiki.models import EntityPage, EntityType
    wiki.add_entity_page(EntityPage(
        page_id="entity_zocdoc",
        name="Zocdoc",
        entity_type=EntityType.COMPANY,
        summary="Competitor company with $375M funding.",
        attributes={"funding": "$375M", "founded": "2007"},
        related_topics=["topic_market_opportunity"]
    ))

    navigator = WikiNavigator(wiki)
    planner = ResearchPlanner()
    plan = planner.plan("test-p", "AI healthcare", "competitor_analysis", navigator)

    # Instantiate navigator with custom temp memory dir
    nav_agent = MultiHopNavigator(memory_dir=str(tmp_path), max_depth=3)
    trace = nav_agent.navigate("test-p", plan, navigator)

    assert trace.depth > 0
    assert len(trace.navigation_path) > 0
    assert len(trace.evidence_gathered) > 0
    assert trace.metrics["pages_explored"] > 0
    assert trace.metrics["evidence_count"] > 0


# ══════════════════════════════════════════════════════════════════════════════
# Integration Tests: State Graph & API Endpoints
# ══════════════════════════════════════════════════════════════════════════════

def test_graph_state_integration():
    """Verify that running a graph node registers planner and trace state."""
    from workflows.startup_graph import _run_agent_node
    from workflows.state import StartupAnalysisState
    from knowledge_wiki.compiler import KnowledgeCompiler
    
    # Compile a basic wiki first to trigger navigator
    compiler = KnowledgeCompiler()
    wiki = compiler._load_or_create("graph-test-project")
    wiki.add_topic_page(TopicPage(
        page_id="topic_industry_overview",
        title="Industry Overview",
        category=TopicCategory.INDUSTRY,
        summary="Core industry overview.",
        content="General overview content here.",
    ))
    compiler._save(wiki)

    state: StartupAnalysisState = {
        "project_id": "graph-test-project",
        "startup_idea": "AI appointment booking",
        "status": "running",
        "current_step": "research",
        "research_plans": {},
        "research_traces": {},
        "research_metrics": {},
    }

    # Run the research node function
    result = _run_agent_node(state, "research", "Research Analyst")

    assert "research_plans" in result
    assert "research_traces" in result
    assert "research_metrics" in result
    
    assert "research" in result["research_plans"]
    assert "research" in result["research_traces"]
    
    # Verify that retrieve_context returns the trace format
    from rag.retrieval import retrieve_context
    # Mock active analysis in memory
    from workflows.graph_runner import _active_analyses
    _active_analyses["graph-test-project"] = {
        "state": result,
        "started_at": 0
    }

    ctx = retrieve_context("test query", "graph-test-project", agent_type="research")
    assert "🔬 AGENTIC MULTI-HOP RESEARCH TRACE" in ctx
    assert "Navigation Path:" in ctx


def test_research_api_endpoints(client: TestClient):
    """Verify REST API research routes list plans and traces."""
    # Run the demo healthcare scenario to ensure state is populated
    response = client.post("/demo/run/ai-healthcare")
    assert response.status_code == 200
    
    # Query project research traces
    res = client.get("/research/demo-healthcare")
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == "demo-healthcare"
    assert "research" in data["plans"]
    assert "research" in data["traces"]
    assert len(data["traces"]["research"]["evidence_gathered"]) == 3

    # Query specific agent trace
    res_agent = client.get("/research/demo-healthcare/agent/research")
    assert res_agent.status_code == 200
    agent_data = res_agent.json()
    assert agent_data["agent_type"] == "research"
    assert len(agent_data["navigation_path"]) == 3
