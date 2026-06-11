"""
StartupPilot AI — Workflow State

TypedDict state schema shared across all LangGraph nodes.
This is the single source of truth that flows through the pipeline.

LangGraph component: TypedDict state
"""

from __future__ import annotations

from typing import TypedDict


class StartupAnalysisState(TypedDict, total=False):
    """State schema for the StartupPilot analysis workflow.

    Each LangGraph node reads from and writes to this shared state.
    Fields are populated sequentially as the workflow progresses.
    """

    # ── Input ─────────────────────────────────────────────────────────────
    project_id: str                    # Unique analysis ID
    startup_idea: str                  # User's startup idea

    # ── Agent Outputs (populated sequentially) ────────────────────────────
    research: str                      # Research Analyst output
    market_analysis: str               # Market Analyst output
    competitors: str                   # Competitor Analyst output
    swot: str                          # SWOT Strategist output
    business_strategy: str             # Business Consultant output

    # ── Human-in-the-Loop ─────────────────────────────────────────────────
    human_feedback: dict               # {action: "approve"|"reject"|"modify", comments: str}

    # ── Post-Approval Outputs ─────────────────────────────────────────────
    discussion_transcript: str         # AutoGen GroupChat transcript
    architecture: str                  # Cloud Architect output
    cost_estimates: str                # Financial Analyst output

    # ── Final Outputs ─────────────────────────────────────────────────────
    report: str                        # Generated report (Markdown)
    diagrams: dict                     # {architecture: str, workflow: str}

    # ── Knowledge Wiki ────────────────────────────────────────────────────
    wiki_compiled: bool                # Whether wiki compilation has been run
    wiki_stats: dict                   # {topic_pages, entity_pages, keywords, compilations}

    # ── Research Platform ─────────────────────────────────────────────────
    research_plans: dict[str, dict]    # Maps agent_type -> ResearchPlan serialized dict
    research_traces: dict[str, dict]   # Maps agent_type -> ResearchTrace serialized dict
    research_metrics: dict[str, dict]  # Maps agent_type -> Traversal metrics dict

    # ── Workflow Metadata ─────────────────────────────────────────────────
    status: str                        # pending|running|awaiting_approval|completed|failed|rejected
    current_step: str                  # Current node name
    execution_metrics: dict            # {node_name: {time_ms, tokens, model, cost}}
    llm_routing_log: list              # [{task, provider, model, reasoning}]
    memory_references: list            # IDs of related past analyses
    errors: list                       # Error messages
