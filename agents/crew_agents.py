"""
StartupPilot AI — CrewAI Agent Definitions

8 specialized agents, each with a distinct role, goal, backstory,
tools, and memory. These agents are the core personas of the platform.

CrewAI components: Agent, Tool
"""

from __future__ import annotations

import logging
from typing import Optional

from crewai import Agent

from agents.tools import get_rag_tool, get_search_tool

logger = logging.getLogger(__name__)


def create_agents(
    startup_idea: str,
    project_id: Optional[str] = None,
    verbose: bool = True,
) -> dict[str, Agent]:
    """Create all 8 CrewAI agents for the startup analysis pipeline.

    Args:
        startup_idea: The startup idea being analyzed (used in backstories).
        project_id: Optional project ID for RAG tool scoping.
        verbose: Whether agents log their reasoning.

    Returns:
        Dict mapping agent type to Agent instance.
    """
    # Build tools list
    tools = []
    search_tool = get_search_tool()
    if search_tool:
        tools.append(search_tool)

    rag_tool = get_rag_tool(project_id) if project_id else None
    if rag_tool:
        tools.append(rag_tool)

    agents = {
        "research": Agent(
            role="Senior Research Analyst",
            goal=(
                "Conduct comprehensive industry research for the startup idea: "
                f"'{startup_idea}'. Identify key trends, market dynamics, regulatory "
                "factors, and technology enablers."
            ),
            backstory=(
                "You are a seasoned research analyst with 15 years of experience "
                "at McKinsey and Gartner. You specialize in technology startups and "
                "emerging industries. You are known for your thorough research methodology "
                "and ability to identify non-obvious market insights. Your reports have "
                "influenced investment decisions worth over $500M."
            ),
            tools=tools,
            memory=True,
            verbose=verbose,
            allow_delegation=False,
        ),

        "market_analysis": Agent(
            role="Senior Market Analyst",
            goal=(
                "Analyze the market opportunity for: "
                f"'{startup_idea}'. Estimate TAM/SAM/SOM, identify customer segments, "
                "and assess market timing."
            ),
            backstory=(
                "You are a market analyst who spent 10 years at Goldman Sachs and CB Insights. "
                "You specialize in TAM/SAM/SOM estimation using both top-down and bottom-up "
                "methodologies. You have a reputation for precise market sizing that VCs trust. "
                "Your analyses have helped raise over $200M in startup funding."
            ),
            tools=tools,
            memory=True,
            verbose=verbose,
            allow_delegation=False,
        ),

        "competitor_analysis": Agent(
            role="Competitive Intelligence Analyst",
            goal=(
                "Identify and analyze direct and indirect competitors for: "
                f"'{startup_idea}'. Create a competitive landscape map with "
                "strengths, weaknesses, and differentiation opportunities."
            ),
            backstory=(
                "You are a competitive intelligence specialist who has advised Fortune 500 "
                "companies on competitive strategy. You have an encyclopedic knowledge of "
                "the startup ecosystem and can identify both obvious and non-obvious competitors. "
                "You previously ran the competitive analysis team at Bain & Company."
            ),
            tools=tools,
            memory=True,
            verbose=verbose,
            allow_delegation=False,
        ),

        "swot_analysis": Agent(
            role="SWOT Strategist",
            goal=(
                "Create a comprehensive SWOT analysis for: "
                f"'{startup_idea}'. Provide actionable strategies for each quadrant "
                "and prioritized recommendations."
            ),
            backstory=(
                "You are a strategic consultant who has advised 200+ startups at Y Combinator "
                "and Sequoia Capital portfolio companies. You specialize in translating SWOT "
                "analysis into actionable strategies. Your framework for SO/WT strategy mapping "
                "is used by top accelerators worldwide."
            ),
            tools=tools,
            memory=True,
            verbose=verbose,
            allow_delegation=False,
        ),

        "business_strategy": Agent(
            role="Senior Business Consultant",
            goal=(
                "Create a comprehensive business strategy for: "
                f"'{startup_idea}'. Include business model, go-to-market strategy, "
                "product roadmap, team plan, and funding strategy."
            ),
            backstory=(
                "You are a serial entrepreneur and startup advisor who has helped launch "
                "50+ startups. You've served as a fractional CTO and CPO for multiple "
                "YC-backed companies. You are known for building practical, actionable "
                "business strategies that balance ambition with execution reality."
            ),
            tools=tools,
            memory=True,
            verbose=verbose,
            allow_delegation=False,
        ),

        "architecture_design": Agent(
            role="Principal Cloud Architect",
            goal=(
                "Design a scalable, secure cloud architecture for: "
                f"'{startup_idea}'. Include specific AWS/GCP services, technology stack, "
                "scalability plan, and architecture diagram."
            ),
            backstory=(
                "You are a principal cloud architect with 12 years of experience at AWS "
                "and top SaaS companies. You've designed systems that serve millions of users. "
                "You specialize in cloud-native architectures, microservices, and serverless "
                "patterns. You always design for the current scale while planning for 100x growth."
            ),
            tools=tools,
            memory=True,
            verbose=verbose,
            allow_delegation=False,
        ),

        "cost_estimation": Agent(
            role="Cloud Financial Analyst",
            goal=(
                "Estimate infrastructure costs at MVP, growth, and scale stages for: "
                f"'{startup_idea}'. Provide detailed monthly breakdowns and "
                "cost optimization recommendations."
            ),
            backstory=(
                "You are a FinOps engineer who has managed $10M+ cloud budgets at "
                "fast-growing startups. You specialize in AWS/GCP cost optimization and "
                "can estimate infrastructure costs with 85% accuracy based on architecture "
                "specifications. You always find ways to reduce costs by 30-40%."
            ),
            tools=tools,
            memory=True,
            verbose=verbose,
            allow_delegation=False,
        ),

        "report_writing": Agent(
            role="Senior Technical Writer",
            goal=(
                "Compile all analysis results into a comprehensive, investor-grade "
                f"report for: '{startup_idea}'. The report should be professional, "
                "well-structured, and actionable."
            ),
            backstory=(
                "You are a technical writer who creates investor-grade reports and strategy "
                "documents. You have written for TechCrunch, a16z, and top-tier consulting "
                "firms. You excel at synthesizing complex analysis into clear, compelling "
                "narratives that drive decision-making."
            ),
            tools=[],  # Report writer doesn't need search tools
            memory=True,
            verbose=verbose,
            allow_delegation=False,
        ),
    }

    logger.info("Created %d CrewAI agents for '%s'", len(agents), startup_idea[:50])
    return agents


def get_agent_info() -> list[dict]:
    """Return agent metadata for the API /agents endpoint.

    Returns a list of agent descriptions without creating actual Agent instances.
    """
    return [
        {
            "id": "research",
            "role": "Senior Research Analyst",
            "goal": "Conduct comprehensive industry research and trend analysis",
            "icon": "🔬",
            "skills": ["Industry Analysis", "Trend Identification", "Market Research"],
        },
        {
            "id": "market_analysis",
            "role": "Senior Market Analyst",
            "goal": "Estimate TAM/SAM/SOM and assess market opportunity",
            "icon": "📊",
            "skills": ["Market Sizing", "Customer Segmentation", "Revenue Modeling"],
        },
        {
            "id": "competitor_analysis",
            "role": "Competitive Intelligence Analyst",
            "goal": "Identify competitors and map the competitive landscape",
            "icon": "🎯",
            "skills": ["Competitor Mapping", "Differentiation Analysis", "Barrier Assessment"],
        },
        {
            "id": "swot_analysis",
            "role": "SWOT Strategist",
            "goal": "Create SWOT analysis with actionable strategies",
            "icon": "⚡",
            "skills": ["Strategic Analysis", "Risk Assessment", "Opportunity Mapping"],
        },
        {
            "id": "business_strategy",
            "role": "Senior Business Consultant",
            "goal": "Design business model, GTM strategy, and product roadmap",
            "icon": "💡",
            "skills": ["Business Modeling", "Go-to-Market", "Product Strategy"],
        },
        {
            "id": "architecture_design",
            "role": "Principal Cloud Architect",
            "goal": "Design scalable cloud architecture with specific services",
            "icon": "🏗️",
            "skills": ["System Design", "Cloud Architecture", "Scalability Planning"],
        },
        {
            "id": "cost_estimation",
            "role": "Cloud Financial Analyst",
            "goal": "Estimate infrastructure costs at each growth stage",
            "icon": "💰",
            "skills": ["FinOps", "Cost Optimization", "Cloud Pricing"],
        },
        {
            "id": "report_writing",
            "role": "Senior Technical Writer",
            "goal": "Compile all analysis into a comprehensive professional report",
            "icon": "✍️",
            "skills": ["Report Writing", "Data Synthesis", "Executive Communication"],
        },
    ]
