"""
StartupPilot AI — Output Parsers

Pydantic models and output parsers for structured agent responses.
Each agent's output is parsed into a validated data model, ensuring
consistent, machine-readable results throughout the pipeline.

LangChain component: PydanticOutputParser, OutputFixingParser
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser


# ── Structured Output Models ──────────────────────────────────────────────────


class ResearchOutput(BaseModel):
    """Structured output from the Research Analyst agent."""

    industry_overview: str = Field(description="Overview of the industry and current state")
    key_trends: list[str] = Field(description="Key trends and growth drivers")
    market_size: str = Field(description="Market size and growth projections")
    regulatory_landscape: str = Field(description="Regulatory considerations")
    technology_enablers: list[str] = Field(description="Key technology enablers")
    challenges: list[str] = Field(description="Key challenges and barriers")
    summary: str = Field(description="Brief executive summary of research findings")


class MarketAnalysisOutput(BaseModel):
    """Structured output from the Market Analyst agent."""

    tam: str = Field(description="Total Addressable Market with estimation")
    sam: str = Field(description="Serviceable Addressable Market")
    som: str = Field(description="Serviceable Obtainable Market")
    growth_rate: str = Field(description="Market CAGR and growth rate")
    customer_segments: list[str] = Field(description="Target customer segments")
    pricing_benchmarks: str = Field(description="Pricing benchmarks in the market")
    revenue_model: str = Field(description="Recommended revenue model")
    summary: str = Field(description="Brief market opportunity summary")


class CompetitorOutput(BaseModel):
    """Structured output from the Competitor Analyst agent."""

    direct_competitors: list[dict] = Field(
        description="List of direct competitors with name, description, strengths, weaknesses"
    )
    indirect_competitors: list[str] = Field(description="Indirect competitors")
    competitive_advantages: list[str] = Field(description="Opportunities for differentiation")
    barriers_to_entry: list[str] = Field(description="Market barriers to entry")
    summary: str = Field(description="Brief competitive landscape summary")


class SWOTOutput(BaseModel):
    """Structured output from the SWOT Strategist agent."""

    strengths: list[str] = Field(description="Internal strengths")
    weaknesses: list[str] = Field(description="Internal weaknesses")
    opportunities: list[str] = Field(description="External opportunities")
    threats: list[str] = Field(description="External threats")
    key_recommendations: list[str] = Field(description="Top strategic recommendations")
    summary: str = Field(description="Brief SWOT summary")


class BusinessStrategyOutput(BaseModel):
    """Structured output from the Business Consultant agent."""

    value_proposition: str = Field(description="Core value proposition")
    business_model: str = Field(description="Revenue model and pricing")
    go_to_market: str = Field(description="Go-to-market strategy")
    product_roadmap: str = Field(description="MVP → V1 → V2 roadmap")
    team_requirements: str = Field(description="Key hires needed")
    funding_strategy: str = Field(description="Funding approach and milestones")
    key_metrics: list[str] = Field(description="KPIs to track")
    risks: list[str] = Field(description="Top risks and mitigations")
    summary: str = Field(description="Brief strategy summary")


class ArchitectureOutput(BaseModel):
    """Structured output from the Cloud Architect agent."""

    system_architecture: str = Field(description="High-level architecture description")
    technology_stack: dict = Field(description="Tech stack choices with justification")
    cloud_services: list[str] = Field(description="Specific cloud services to use")
    scalability_plan: str = Field(description="How to handle growth")
    security_architecture: str = Field(description="Security approach")
    mermaid_diagram: str = Field(description="Architecture as Mermaid diagram code")
    summary: str = Field(description="Brief architecture summary")


class CostEstimateOutput(BaseModel):
    """Structured output from the Financial Analyst agent."""

    monthly_breakdown: dict = Field(description="Cost breakdown by service category")
    mvp_cost: str = Field(description="Monthly cost for MVP stage (0-1K users)")
    growth_cost: str = Field(description="Monthly cost for growth stage (1K-10K users)")
    scale_cost: str = Field(description="Monthly cost for scale stage (10K-100K users)")
    first_year_total: str = Field(description="Total first-year cost projection")
    optimization_tips: list[str] = Field(description="Cost optimization recommendations")
    summary: str = Field(description="Brief cost summary")


# ── Parser Factory ────────────────────────────────────────────────────────────

# Map agent types to their output models
OUTPUT_MODELS: dict[str, type[BaseModel]] = {
    "research": ResearchOutput,
    "market_analysis": MarketAnalysisOutput,
    "competitor_analysis": CompetitorOutput,
    "swot_analysis": SWOTOutput,
    "business_strategy": BusinessStrategyOutput,
    "architecture_design": ArchitectureOutput,
    "cost_estimation": CostEstimateOutput,
}


def get_output_parser(agent_type: str) -> Optional[PydanticOutputParser]:
    """Get the output parser for a specific agent type.

    Args:
        agent_type: The type of agent (e.g., "research", "market_analysis").

    Returns:
        A PydanticOutputParser, or None for agents without structured output
        (e.g., report_writing returns free-form markdown).
    """
    model_class = OUTPUT_MODELS.get(agent_type)
    if model_class:
        return PydanticOutputParser(pydantic_object=model_class)
    return None


def get_format_instructions(agent_type: str) -> str:
    """Get format instructions string for a specific agent type.

    Useful for injecting into prompts to guide the LLM's output format.
    """
    parser = get_output_parser(agent_type)
    if parser:
        return parser.get_format_instructions()
    return "Respond in well-structured Markdown format."
