"""
StartupPilot AI — CrewAI Task Definitions

Defines tasks for each of the 8 agents. Tasks specify what the agent
should do, expected output format, and dependencies.

CrewAI components: Task
"""

from __future__ import annotations

import logging
from typing import Optional

from crewai import Agent, Task

logger = logging.getLogger(__name__)


def create_tasks(
    agents: dict[str, Agent],
    startup_idea: str,
    context: Optional[dict[str, str]] = None,
) -> dict[str, Task]:
    """Create tasks for all agents.

    Args:
        agents: Dict of agent_type → Agent instance.
        startup_idea: The startup idea being analyzed.
        context: Optional dict of prior agent outputs {agent_type: output}.

    Returns:
        Dict mapping agent type to Task instance.
    """
    ctx = context or {}

    tasks = {
        "research": Task(
            description=(
                f"Research the industry for the startup idea: '{startup_idea}'\n\n"
                "Provide a comprehensive industry overview including:\n"
                "1. Industry overview and current state\n"
                "2. Key trends and growth drivers (with data points)\n"
                "3. Market size and growth projections\n"
                "4. Regulatory landscape\n"
                "5. Technology enablers\n"
                "6. Key challenges and barriers\n\n"
                "Use specific data, statistics, and named sources."
            ),
            agent=agents["research"],
            expected_output=(
                "A comprehensive industry research report with specific data points, "
                "statistics, named sources, and clear categorization of trends, "
                "regulatory factors, and technology enablers."
            ),
        ),

        "market_analysis": Task(
            description=(
                f"Analyze the market opportunity for: '{startup_idea}'\n\n"
                f"Research findings: {ctx.get('research', 'Not yet available')[:500]}\n\n"
                "Provide:\n"
                "1. TAM estimation with methodology\n"
                "2. SAM estimation\n"
                "3. SOM estimation\n"
                "4. Market CAGR\n"
                "5. Customer segments and personas\n"
                "6. Pricing benchmarks\n"
                "7. Revenue model recommendations"
            ),
            agent=agents["market_analysis"],
            expected_output=(
                "A market analysis report with concrete TAM/SAM/SOM numbers, "
                "growth rates, customer segment definitions, and revenue model "
                "recommendations backed by data."
            ),
        ),

        "competitor_analysis": Task(
            description=(
                f"Identify and analyze competitors for: '{startup_idea}'\n\n"
                f"Market context: {ctx.get('market_analysis', 'Not yet available')[:500]}\n\n"
                "Provide:\n"
                "1. 5-8 direct competitors with details\n"
                "2. 3-5 indirect competitors\n"
                "3. Competitive advantage opportunities\n"
                "4. Barriers to entry"
            ),
            agent=agents["competitor_analysis"],
            expected_output=(
                "A competitive landscape analysis with named companies, their "
                "strengths/weaknesses, funding details, and clear differentiation "
                "opportunities for the startup."
            ),
        ),

        "swot_analysis": Task(
            description=(
                f"Create SWOT analysis for: '{startup_idea}'\n\n"
                f"Prior analysis context:\n"
                f"Research: {ctx.get('research', 'N/A')[:300]}\n"
                f"Market: {ctx.get('market_analysis', 'N/A')[:300]}\n"
                f"Competitors: {ctx.get('competitor_analysis', 'N/A')[:300]}\n\n"
                "Provide 5-7 points per quadrant plus strategic recommendations."
            ),
            agent=agents["swot_analysis"],
            expected_output=(
                "A comprehensive SWOT analysis with specific, actionable points "
                "in each quadrant, SO/WT strategies, and top 3 strategic priorities."
            ),
        ),

        "business_strategy": Task(
            description=(
                f"Create business strategy for: '{startup_idea}'\n\n"
                f"Analysis so far:\n"
                f"SWOT: {ctx.get('swot_analysis', 'N/A')[:300]}\n"
                f"Market: {ctx.get('market_analysis', 'N/A')[:300]}\n\n"
                "Provide: value proposition, business model, GTM strategy, "
                "product roadmap (MVP→V1→V2), team requirements, funding strategy, "
                "key metrics, and risk mitigation."
            ),
            agent=agents["business_strategy"],
            expected_output=(
                "A comprehensive business strategy with actionable plans for "
                "business model, go-to-market, product roadmap, team hiring, "
                "funding, KPIs, and risk mitigation."
            ),
        ),

        "architecture_design": Task(
            description=(
                f"Design cloud architecture for: '{startup_idea}'\n\n"
                f"Business context: {ctx.get('business_strategy', 'N/A')[:500]}\n\n"
                "Provide: system architecture, technology stack, specific cloud services, "
                "scalability plan, security architecture, and a Mermaid architecture diagram."
            ),
            agent=agents["architecture_design"],
            expected_output=(
                "A detailed cloud architecture design with specific AWS/GCP services, "
                "technology stack choices, scalability plan, security approach, and "
                "a Mermaid diagram describing the architecture."
            ),
        ),

        "cost_estimation": Task(
            description=(
                f"Estimate infrastructure costs for: '{startup_idea}'\n\n"
                f"Architecture: {ctx.get('architecture_design', 'N/A')[:500]}\n\n"
                "Provide monthly cost breakdown by service, costs at 3 growth stages "
                "(MVP: 0-1K users, Growth: 1K-10K, Scale: 10K-100K), "
                "first-year total, and optimization recommendations."
            ),
            agent=agents["cost_estimation"],
            expected_output=(
                "A detailed cost estimation with monthly breakdowns by service, "
                "costs at MVP/growth/scale stages, first-year projection, and "
                "specific cost optimization recommendations."
            ),
        ),

        "report_writing": Task(
            description=(
                f"Write a comprehensive startup analysis report for: '{startup_idea}'\n\n"
                "Compile ALL of the following analysis sections into a single professional report:\n\n"
                f"Research: {ctx.get('research', 'N/A')[:400]}\n"
                f"Market: {ctx.get('market_analysis', 'N/A')[:400]}\n"
                f"Competitors: {ctx.get('competitor_analysis', 'N/A')[:400]}\n"
                f"SWOT: {ctx.get('swot_analysis', 'N/A')[:400]}\n"
                f"Strategy: {ctx.get('business_strategy', 'N/A')[:400]}\n"
                f"Discussion: {ctx.get('discussion_transcript', 'N/A')[:400]}\n"
                f"Architecture: {ctx.get('architecture_design', 'N/A')[:400]}\n"
                f"Costs: {ctx.get('cost_estimation', 'N/A')[:400]}\n\n"
                "Format as clean Markdown with 10 sections."
            ),
            agent=agents["report_writing"],
            expected_output=(
                "A comprehensive, investor-grade startup analysis report in "
                "Markdown format with 10 sections covering all aspects of the analysis."
            ),
        ),
    }

    logger.info("Created %d tasks for '%s'", len(tasks), startup_idea[:50])
    return tasks
