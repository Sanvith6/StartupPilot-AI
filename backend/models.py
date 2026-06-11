"""
StartupPilot AI — API Models

Pydantic models for FastAPI request validation and response serialization.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Request Models ────────────────────────────────────────────────────────────

class AnalysisStartRequest(BaseModel):
    """Request schema to start a new startup analysis."""
    startup_idea: str = Field(
        ..., 
        description="The startup idea to analyze", 
        example="AI-powered healthcare scheduling platform"
    )
    project_id: Optional[str] = Field(
        None, 
        description="Optional project ID. If not provided, one will be generated.",
        example="health-1"
    )


class HumanApprovalRequest(BaseModel):
    """Request schema for human feedback on the workflow."""
    action: str = Field(
        ..., 
        description="Action to take. Must be one of: 'approve', 'reject', 'modify'.",
        example="approve"
    )
    comments: Optional[str] = Field(
        None, 
        description="Feedback or change requests to incorporate if action is 'modify'.",
        example="Focus more on AWS serverless services rather than container-based ones."
    )


# ── Response Models ───────────────────────────────────────────────────────────

class HealthStatusResponse(BaseModel):
    """Response schema for health check."""
    status: str = Field("healthy", example="healthy")
    timestamp: str = Field(..., example="2026-06-03T17:48:30Z")


class AgentDefinition(BaseModel):
    """Details of a single agent in the system."""
    id: str = Field(..., example="research")
    role: str = Field(..., example="Senior Research Analyst")
    goal: str = Field(..., example="Conduct comprehensive industry research and trend analysis")
    icon: str = Field(..., example="🔬")
    skills: list[str] = Field(..., example=["Industry Analysis", "Trend Identification"])


class AgentsListResponse(BaseModel):
    """Response schema listing all active agents."""
    agents: list[AgentDefinition]


class AnalysisStartResponse(BaseModel):
    """Response schema returned when an analysis begins."""
    project_id: str = Field(..., example="health-1")
    status: str = Field(..., example="running")
    message: str = Field(..., example="Analysis started successfully")


class AnalysisStatusResponse(BaseModel):
    """Status summary of a running or completed analysis."""
    project_id: str = Field(..., example="health-1")
    startup_idea: str = Field(..., example="AI-powered healthcare scheduling platform")
    status: str = Field(..., example="awaiting_approval")
    current_step: str = Field(..., example="human_approval")
    progress: int = Field(..., example=60)
    elapsed_seconds: int = Field(..., example=120)
    execution_metrics: dict[str, Any] = Field(default_factory=dict)
    llm_routing_log: list[dict[str, Any]] = Field(default_factory=list)
    memory_references: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    has_report: bool = Field(..., example=False)


class ReportResponse(BaseModel):
    """Response schema containing the final generated report and diagrams."""
    project_id: str = Field(..., example="health-1")
    startup_idea: str = Field(..., example="AI-powered healthcare scheduling platform")
    report: str = Field(..., description="Markdown content of the report")
    diagrams: dict[str, str] = Field(default_factory=dict, description="Mermaid diagrams: {architecture, workflow}")


class MetricsResponse(BaseModel):
    """Response schema for agent metrics."""
    project_id: str = Field(..., example="health-1")
    execution_metrics: dict[str, Any] = Field(default_factory=dict)
    llm_routing_log: list[dict[str, Any]] = Field(default_factory=list)


class DemoScenario(BaseModel):
    """Details of a pre-cached demo scenario."""
    id: str = Field(..., example="healthcare")
    name: str = Field(..., example="AI Healthcare")
    startup_idea: str = Field(..., example="AI-powered appointment scheduling platform")
    icon: str = Field(..., example="🏥")
    description: str = Field(..., example="AI-powered appointment scheduling platform")


class DemoScenariosResponse(BaseModel):
    """Response schema listing available demo scenarios."""
    scenarios: list[DemoScenario]


# ── Knowledge Wiki Response Models ────────────────────────────────────────────

class WikiStatsResponse(BaseModel):
    """Response schema for wiki statistics."""
    project_id: str = Field(..., example="health-1")
    total_topic_pages: int = Field(default=0, example=5)
    total_entity_pages: int = Field(default=0, example=8)
    total_keywords: int = Field(default=0, example=42)
    total_cross_references: int = Field(default=0, example=12)
    compilation_count: int = Field(default=0, example=3)
    categories: dict[str, int] = Field(default_factory=dict)
    entity_types: dict[str, int] = Field(default_factory=dict)
    created_at: str = Field(default="", example="2026-06-03T17:48:30Z")
    updated_at: str = Field(default="", example="2026-06-03T17:48:30Z")


class WikiPageResponse(BaseModel):
    """Response schema for a single wiki page (topic or entity)."""
    page_id: str = Field(..., example="topic_healthcare_market")
    page_type: str = Field(..., example="topic", description="'topic' or 'entity'")
    title: str = Field(..., example="Healthcare Scheduling Market")
    category_or_type: str = Field(..., example="market")
    summary: str = Field(default="")
    content: str = Field(default="")
    key_facts: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    related_pages: list[str] = Field(default_factory=list)
    source_type: str = Field(default="document", example="agent")
    version: int = Field(default=1)
    confidence: float = Field(default=0.8)


class WikiPageListResponse(BaseModel):
    """Response listing all pages in the wiki."""
    project_id: str
    topic_pages: list[WikiPageResponse] = Field(default_factory=list)
    entity_pages: list[WikiPageResponse] = Field(default_factory=list)
    stats: WikiStatsResponse


# ── Research Response Models ──────────────────────────────────────────────────

class ResearchSubQuestionResponse(BaseModel):
    """Schema for a single sub-question in the research plan."""
    question_id: str = Field(..., example="q1")
    text: str = Field(..., example="What are the key competitor strengths?")
    target_pages: list[str] = Field(default_factory=list)
    status: str = Field(..., example="completed")


class ResearchPlanResponse(BaseModel):
    """Schema for a research plan for a specific agent step."""
    project_id: str = Field(..., example="health-1")
    startup_idea: str = Field(..., example="AI scheduling")
    agent_type: str = Field(..., example="competitor_analysis")
    sub_questions: list[ResearchSubQuestionResponse] = Field(default_factory=list)
    created_at: str = Field(..., example="2026-06-03T17:48:30Z")


class EvidenceItemResponse(BaseModel):
    """Schema for collected evidence facts."""
    evidence_id: str = Field(..., example="ev-8b3d")
    page_id: str = Field(..., example="entity_zocdoc")
    title_or_name: str = Field(..., example="Zocdoc")
    fact: str = Field(..., example="Zocdoc raised $375M in funding.")
    relevance_reasoning: str = Field(..., example="Direct funding information for competitor evaluation.")
    timestamp: str = Field(..., example="2026-06-03T17:48:30Z")


class ResearchTraceResponse(BaseModel):
    """Schema for a multi-hop traversal log."""
    project_id: str = Field(..., example="health-1")
    agent_type: str = Field(..., example="competitor_analysis")
    navigation_path: list[str] = Field(default_factory=list, example=["topic_market_opportunity", "entity_zocdoc"])
    evidence_gathered: list[EvidenceItemResponse] = Field(default_factory=list)
    reasoning_chain: list[str] = Field(default_factory=list)
    depth: int = Field(default=0, example=2)
    metrics: dict[str, Any] = Field(default_factory=dict)


class ProjectResearchResponse(BaseModel):
    """Schema combining all research planner and trace records for a project."""
    project_id: str
    plans: dict[str, ResearchPlanResponse] = Field(default_factory=dict)
    traces: dict[str, ResearchTraceResponse] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
