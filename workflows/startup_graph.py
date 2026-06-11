"""
StartupPilot AI — LangGraph Startup Analysis Graph

The 10-node StateGraph that orchestrates the entire analysis pipeline.
This is the heart of the system — it connects CrewAI agents, AutoGen
discussions, human approval, and report generation into a single workflow.

LangGraph components: StateGraph, END, conditional_edges

Interview talking point:
    "The workflow is a 10-node LangGraph StateGraph with conditional edges.
     Nodes 1-5 run agent analysis sequentially, node 6 pauses for human
     approval with three possible outcomes (approve/reject/modify), then
     nodes 7-10 handle discussion, architecture, and report generation.
     Each node includes retry logic and LLM routing."
"""

from __future__ import annotations

import logging
import time
from typing import Any

from langgraph.graph import StateGraph, END

from workflows.state import StartupAnalysisState

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Node Functions — Each node reads state, does work, and returns updates
# ══════════════════════════════════════════════════════════════════════════════


def research_node(state: StartupAnalysisState) -> dict[str, Any]:
    """Node 1: Research Analyst — Industry research and trends."""
    return _run_agent_node(state, "research", "Research Analyst")


def market_analysis_node(state: StartupAnalysisState) -> dict[str, Any]:
    """Node 2: Market Analyst — TAM/SAM/SOM and market opportunity."""
    context = state.get("research", "")
    return _run_agent_node(state, "market_analysis", "Market Analyst", context)


def competitor_analysis_node(state: StartupAnalysisState) -> dict[str, Any]:
    """Node 3: Competitor Analyst — Competitive landscape."""
    context = f"{state.get('research', '')}\n{state.get('market_analysis', '')}"
    return _run_agent_node(state, "competitor_analysis", "Competitor Analyst", context)


def swot_analysis_node(state: StartupAnalysisState) -> dict[str, Any]:
    """Node 4: SWOT Strategist — SWOT analysis."""
    context = (
        f"Research: {state.get('research', '')[:500]}\n"
        f"Market: {state.get('market_analysis', '')[:500]}\n"
        f"Competitors: {state.get('competitors', '')[:500]}"
    )
    return _run_agent_node(state, "swot_analysis", "SWOT Strategist", context)


def business_strategy_node(state: StartupAnalysisState) -> dict[str, Any]:
    """Node 5: Business Consultant — Business strategy and GTM."""
    context = (
        f"Market: {state.get('market_analysis', '')[:400]}\n"
        f"SWOT: {state.get('swot', '')[:400]}\n"
        f"Competitors: {state.get('competitors', '')[:400]}"
    )
    # Include human feedback if this is a re-run after "modify"
    human_fb = state.get("human_feedback", {})
    if human_fb.get("action") == "modify" and human_fb.get("comments"):
        context += f"\n\nHuman Feedback (incorporate this): {human_fb['comments']}"

    updates = _run_agent_node(state, "business_strategy", "Business Consultant", context)
    
    # Clear human_feedback if we just ran a modification request to prevent infinite loops!
    if human_fb.get("action") == "modify":
        updates["human_feedback"] = {}
        
    return updates


def human_approval_node(state: StartupAnalysisState) -> dict[str, Any]:
    """Node 6: Human-in-the-Loop — Pause for approval.

    This node sets the status to 'awaiting_approval' and returns.
    The workflow pauses here until the user provides feedback via the API.
    The graph_runner handles resumption based on the approval decision.
    """
    logger.info("Workflow paused for human approval. Project: %s", state.get("project_id"))

    return {
        "status": "awaiting_approval",
        "current_step": "human_approval",
    }


def autogen_discussion_node(state: StartupAnalysisState) -> dict[str, Any]:
    """Node 7: AutoGen GroupChat — Multi-agent discussion."""
    from autogen_module.autogen_discussion import run_discussion

    startup_idea = state.get("startup_idea", "")

    logger.info("Starting AutoGen discussion for '%s'", startup_idea[:50])
    start_time = time.time()

    # Clear human_feedback since approval has been processed
    updates = {
        "human_feedback": {},
    }

    try:
        result = run_discussion(
            startup_idea=startup_idea,
            business_context=state.get("business_strategy", "")[:500],
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        metrics = state.get("execution_metrics", {})
        metrics["autogen_discussion"] = {
            "time_ms": elapsed_ms,
            "rounds": result.get("rounds", 0),
        }

        updates.update({
            "discussion_transcript": result.get("transcript", ""),
            "current_step": "autogen_discussion",
            "status": "running",
            "execution_metrics": metrics,
        })
        return updates

    except Exception as e:
        logger.error("AutoGen discussion failed: %s", e)
        errors = state.get("errors", [])
        errors.append(f"AutoGen discussion: {str(e)}")
        updates.update({
            "discussion_transcript": f"Discussion failed: {str(e)}",
            "errors": errors,
            "current_step": "autogen_discussion",
            "status": "running",
        })
        return updates


def architecture_cost_node(state: StartupAnalysisState) -> dict[str, Any]:
    """Node 8: Cloud Architect + Financial Analyst — Architecture and cost.

    Runs two agents sequentially: architecture design then cost estimation.
    Combined into one node because cost depends directly on architecture.
    """
    startup_idea = state.get("startup_idea", "")
    context = (
        f"Business Strategy: {state.get('business_strategy', '')[:500]}\n"
        f"Discussion Insights: {state.get('discussion_transcript', '')[:500]}"
    )

    # Run architecture design
    arch_result = _run_agent_chain(state, "architecture_design", startup_idea, context)

    # Run cost estimation with architecture as context
    cost_context = f"Architecture: {arch_result['output'][:800]}"
    cost_result = _run_agent_chain(state, "cost_estimation", startup_idea, cost_context)

    # Merge metrics
    metrics = state.get("execution_metrics", {})
    metrics["architecture_design"] = arch_result.get("metrics", {})
    metrics["cost_estimation"] = cost_result.get("metrics", {})

    return {
        "architecture": arch_result["output"],
        "cost_estimates": cost_result["output"],
        "current_step": "architecture_cost",
        "status": "running",
        "execution_metrics": metrics,
    }


def report_generation_node(state: StartupAnalysisState) -> dict[str, Any]:
    """Node 9: Report Writer — Compile final report."""
    from reports.generator import generate_report

    startup_idea = state.get("startup_idea", "")

    logger.info("Generating report for '%s'", startup_idea[:50])
    start_time = time.time()

    try:
        report = generate_report(state)

        elapsed_ms = int((time.time() - start_time) * 1000)
        metrics = state.get("execution_metrics", {})
        metrics["report_generation"] = {"time_ms": elapsed_ms}

        return {
            "report": report,
            "current_step": "report_generation",
            "status": "running",
            "execution_metrics": metrics,
        }

    except Exception as e:
        logger.error("Report generation failed: %s", e)
        errors = state.get("errors", [])
        errors.append(f"Report generation: {str(e)}")
        return {
            "report": f"Report generation failed: {str(e)}",
            "errors": errors,
            "current_step": "report_generation",
            "status": "running",
        }


def memory_storage_node(state: StartupAnalysisState) -> dict[str, Any]:
    """Node 10: Store results in memory for future analyses."""
    from agents.memory import MemoryManager
    from reports.diagrams import generate_diagrams

    project_id = state.get("project_id", "unknown")
    startup_idea = state.get("startup_idea", "")

    logger.info("Storing results in memory for project %s", project_id)

    try:
        # Generate diagrams
        diagrams = generate_diagrams(state)

        # Store to long-term memory
        memory = MemoryManager()
        memory.store_long_term(project_id, {
            "startup_idea": startup_idea,
            "status": "completed",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "research": state.get("research", "")[:1000],
            "market_analysis": state.get("market_analysis", "")[:1000],
            "competitors": state.get("competitors", "")[:1000],
            "swot": state.get("swot", "")[:1000],
            "business_strategy": state.get("business_strategy", "")[:1000],
            "architecture": state.get("architecture", "")[:1000],
            "cost_estimates": state.get("cost_estimates", "")[:1000],
            "execution_metrics": state.get("execution_metrics", {}),
        })

        return {
            "diagrams": diagrams,
            "status": "completed",
            "current_step": "completed",
        }

    except Exception as e:
        logger.error("Memory storage failed: %s", e)
        return {
            "diagrams": {},
            "status": "completed",
            "current_step": "completed",
        }


# ══════════════════════════════════════════════════════════════════════════════
# Graph Construction
# ══════════════════════════════════════════════════════════════════════════════


def _human_approval_router(state: StartupAnalysisState) -> str:
    """Route based on human approval decision.

    Returns the next node name based on the human's decision:
    - "approve" → continue to AutoGen discussion
    - "reject" → end the workflow
    - "modify" → re-run business strategy with feedback
    """
    feedback = state.get("human_feedback", {})
    action = feedback.get("action")

    if not action:
        logger.info("Workflow paused at Human Approval node. Ending current execution thread.")
        return "end"

    if action == "reject":
        logger.info("Human rejected the analysis. Ending workflow.")
        return "end"
    elif action == "modify":
        logger.info("Human requested modifications. Re-running business strategy.")
        return "modify"
    else:
        logger.info("Human approved. Continuing to AutoGen discussion.")
        return "approve"


def create_graph() -> StateGraph:
    """Create the 10-node LangGraph StateGraph.

    Graph structure:
        START → research_agent → market_analysis_agent → competitor → swot → business_strategy_agent
              → human_approval ─┬─ approve → discussion → arch_cost → report → memory → END
                                ├─ modify  → business_strategy_agent (loop back)
                                └─ reject  → END

    Returns:
        A compiled StateGraph ready for execution.
    """
    graph = StateGraph(StartupAnalysisState)

    # ── Add all 10 nodes ──────────────────────────────────────────────────
    graph.add_node("research_agent", research_node)
    graph.add_node("market_analysis_agent", market_analysis_node)
    graph.add_node("competitor_analysis", competitor_analysis_node)
    graph.add_node("swot_analysis", swot_analysis_node)
    graph.add_node("business_strategy_agent", business_strategy_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("autogen_discussion", autogen_discussion_node)
    graph.add_node("architecture_cost", architecture_cost_node)
    graph.add_node("report_generation", report_generation_node)
    graph.add_node("memory_storage", memory_storage_node)

    # ── Define edges ──────────────────────────────────────────────────────

    # Linear flow: START → research_agent → market_analysis_agent → competitor → swot → business_strategy_agent
    graph.set_entry_point("research_agent")
    graph.add_edge("research_agent", "market_analysis_agent")
    graph.add_edge("market_analysis_agent", "competitor_analysis")
    graph.add_edge("competitor_analysis", "swot_analysis")
    graph.add_edge("swot_analysis", "business_strategy_agent")
    graph.add_edge("business_strategy_agent", "human_approval")

    # Conditional edge at human approval
    graph.add_conditional_edges(
        "human_approval",
        _human_approval_router,
        {
            "approve": "autogen_discussion",
            "modify": "business_strategy_agent",
            "end": END,
        },
    )

    # Continue after approval
    graph.add_edge("autogen_discussion", "architecture_cost")
    graph.add_edge("architecture_cost", "report_generation")
    graph.add_edge("report_generation", "memory_storage")
    graph.add_edge("memory_storage", END)

    logger.info("Created StartupPilot workflow graph (10 nodes)")

    return graph


# ══════════════════════════════════════════════════════════════════════════════
# Internal Helpers
# ══════════════════════════════════════════════════════════════════════════════


def _run_agent_node(
    state: StartupAnalysisState,
    agent_type: str,
    agent_name: str,
    context: str = "",
) -> dict[str, Any]:
    """Run an agent node with metrics collection and error handling."""
    # Map agent_type to state field
    state_field = agent_type
    if agent_type == "competitor_analysis":
        state_field = "competitors"
    elif agent_type == "swot_analysis":
        state_field = "swot"

    # If output is already present, skip execution (makes the graph resumeable)
    # BUT do not skip if we are explicitly re-running business_strategy after a modification request!
    is_modification = (
        agent_type == "business_strategy"
        and state.get("human_feedback", {}).get("action") == "modify"
    )
    if state.get(state_field) and not is_modification:
        logger.info("Node '%s' already completed. Skipping execution.", agent_type)
        return {
            state_field: state[state_field],
            "current_step": agent_type,
            "status": "running"
        }

    project_id = state.get("project_id", "")
    startup_idea = state.get("startup_idea", "")

    # Execute Research Planner & Multi-Hop Navigator if wiki is available
    research_plans = dict(state.get("research_plans") or {})
    research_traces = dict(state.get("research_traces") or {})
    research_metrics = dict(state.get("research_metrics") or {})

    try:
        from knowledge_wiki.compiler import KnowledgeCompiler
        from knowledge_wiki.navigator import WikiNavigator
        from research_platform.planner import ResearchPlanner
        from research_platform.navigator import MultiHopNavigator

        compiler = KnowledgeCompiler()
        wiki = compiler.get_wiki(project_id)
        if wiki:
            navigator = WikiNavigator(wiki)
            
            # Step 1: Research Plan
            planner = ResearchPlanner()
            plan = planner.plan(project_id, startup_idea, agent_type, navigator)
            
            # Step 2: Multi-Hop Traversal
            navigator_agent = MultiHopNavigator()
            trace = navigator_agent.navigate(project_id, plan, navigator)
            
            # Save in state dicts (Pydantic model_dump uses datetime which needs serialization for JSON/FastAPI)
            # We'll serialize datetimes to ISO strings
            def serialize_datetime(obj):
                if isinstance(obj, dict):
                    return {k: serialize_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [serialize_datetime(v) for v in obj]
                elif hasattr(obj, "isoformat"):
                    return obj.isoformat()
                return obj

            research_plans[agent_type] = serialize_datetime(plan.model_dump())
            research_traces[agent_type] = serialize_datetime(trace.model_dump())
            research_metrics[agent_type] = serialize_datetime(trace.metrics)
            
            logger.info("Generated research plan and multi-hop trace for %s", agent_type)
    except Exception as e:
        logger.warning("Research Planner/Navigator execution failed (non-fatal): %s", e)

    result = _run_agent_chain(state, agent_type, state.get("startup_idea", ""), context)

    # Update metrics
    metrics = state.get("execution_metrics", {})
    metrics[agent_type] = result.get("metrics", {})

    # Update routing log
    routing_log = state.get("llm_routing_log", [])
    if result.get("metrics", {}).get("provider"):
        routing_log.append({
            "task": agent_type,
            "provider": result["metrics"]["provider"],
            "model": result["metrics"]["model_used"],
        })

    # ── Compile agent output into Knowledge Wiki (living wiki) ────────
    _compile_to_wiki(state, agent_type, result["output"])

    return {
        state_field: result["output"],
        "current_step": agent_type,
        "status": "running",
        "execution_metrics": metrics,
        "llm_routing_log": routing_log,
        "research_plans": research_plans,
        "research_traces": research_traces,
        "research_metrics": research_metrics,
    }


def _run_agent_chain(
    state: StartupAnalysisState,
    agent_type: str,
    startup_idea: str,
    context: str = "",
) -> dict[str, Any]:
    """Execute an agent chain with retry logic."""
    from agents.chains import RetrievalChain

    chain = RetrievalChain()
    project_id = state.get("project_id")

    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            result = chain.run(
                agent_type=agent_type,
                startup_idea=startup_idea,
                project_id=project_id,
                additional_context=context,
            )
            return result

        except Exception as e:
            last_error = e
            logger.warning(
                "Agent '%s' attempt %d/%d failed: %s",
                agent_type,
                attempt + 1,
                max_retries,
                e,
            )
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

    # All retries failed
    logger.error("Agent '%s' failed after %d retries: %s", agent_type, max_retries, last_error)
    return {
        "output": f"[Agent {agent_type} failed: {str(last_error)}]",
        "metrics": {"error": str(last_error)},
    }


def _compile_to_wiki(
    state: StartupAnalysisState,
    agent_type: str,
    output: str,
) -> None:
    """Compile an agent's output into the Knowledge Wiki (living wiki).

    This runs after every agent node, extracting topics and entities
    from the output and merging them into the project's wiki.
    Downstream agents can then read this structured knowledge via
    the ContextAssembler.

    Fails silently — wiki compilation errors should never break the workflow.
    """
    try:
        from knowledge_wiki.compiler import KnowledgeCompiler

        project_id = state.get("project_id", "")
        startup_idea = state.get("startup_idea", "")

        if not project_id or not output or len(output) < 100:
            return

        compiler = KnowledgeCompiler()
        wiki = compiler.compile_agent_output(
            project_id=project_id,
            agent_type=agent_type,
            output=output,
            startup_idea=startup_idea,
        )

        logger.info(
            "Wiki updated from '%s' output: %d topics, %d entities",
            agent_type,
            len(wiki.topic_pages),
            len(wiki.entity_pages),
        )

    except Exception as e:
        # Never break the workflow because of wiki compilation failure
        logger.debug("Wiki compilation for '%s' failed (non-fatal): %s", agent_type, e)
