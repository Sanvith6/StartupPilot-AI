"""
StartupPilot AI — Graph Runner

Async runner that compiles and executes the LangGraph workflow.
Handles workflow lifecycle: start, pause (HITL), resume, and completion.

LangGraph component: graph.compile(), graph.invoke()
"""

from __future__ import annotations

import logging
import time
import uuid
import threading
import json
from pathlib import Path
from typing import Any, Callable, Optional

from workflows.state import StartupAnalysisState
from workflows.startup_graph import create_graph
from config import get_settings

logger = logging.getLogger(__name__)

# In-memory store for active analyses
_active_analyses: dict[str, dict[str, Any]] = {}
_analyses_lock = threading.Lock()


def _save_active_analyses_backup() -> None:
    """Save serializable parts of _active_analyses to disk."""
    try:
        settings = get_settings()
        backup_path = Path(settings.memory_dir) / "active_analyses_backup.json"
        
        # Build serializable version (exclude CompiledGraph objects)
        serializable = {}
        for pid, data in _active_analyses.items():
            serializable[pid] = {
                "state": data["state"],
                "started_at": data.get("started_at", time.time())
            }
            
        with _analyses_lock:
            backup_path.write_text(json.dumps(serializable, indent=2, default=str), encoding="utf-8")
        logger.info("Active analyses backup saved successfully.")
    except Exception as e:
        logger.error("Failed to save active analyses backup: %s", e)


def load_active_analyses_backup() -> None:
    """Load active analyses from backup file on startup."""
    try:
        settings = get_settings()
        backup_path = Path(settings.memory_dir) / "active_analyses_backup.json"
        if backup_path.exists():
            with _analyses_lock:
                data = json.loads(backup_path.read_text(encoding="utf-8"))
            for pid, val in data.items():
                _active_analyses[pid] = {
                    "state": val["state"],
                    "started_at": val.get("started_at", time.time()),
                    "graph": None
                }
            logger.info("Restored %d active analyses from backup.", len(_active_analyses))
    except Exception as e:
        logger.error("Failed to load active analyses backup: %s", e)


def _prune_active_analyses() -> None:
    """Cap _active_analyses at 50 items, evicting the oldest completed/failed/stale ones."""
    if len(_active_analyses) <= 50:
        return
        
    logger.info("Active analyses count (%d) exceeds cap (50). Pruning...", len(_active_analyses))
    # Sort keys by started_at ascending
    sorted_keys = sorted(
        _active_analyses.keys(),
        key=lambda k: _active_analyses[k].get("started_at", 0)
    )
    
    # Try to remove completed/failed/rejected first
    removed_count = 0
    needed_removals = len(_active_analyses) - 50
    
    for pid in sorted_keys:
        state = _active_analyses[pid]["state"]
        status = state.get("status", "")
        if status in ("completed", "failed", "rejected", "not_found"):
            _active_analyses.pop(pid)
            removed_count += 1
            if removed_count >= needed_removals:
                break
                
    # If still too many, force remove oldest regardless of state
    if len(_active_analyses) > 50:
        sorted_keys = sorted(
            _active_analyses.keys(),
            key=lambda k: _active_analyses[k].get("started_at", 0)
        )
        for pid in sorted_keys:
            _active_analyses.pop(pid)
            removed_count += 1
            if len(_active_analyses) <= 50:
                break
                
    logger.info("Pruned %d analyses from memory.", removed_count)


def register_analysis(project_id: str, state: dict) -> None:
    """Register a new analysis session, prune if necessary, and save backup."""
    _active_analyses[project_id] = {
        "state": state,
        "started_at": time.time(),
        "graph": None
    }
    _prune_active_analyses()
    _save_active_analyses_backup()



def start_analysis(
    startup_idea: str,
    project_id: Optional[str] = None,
    on_status_update: Optional[Callable] = None,
) -> str:
    """Start a new startup analysis workflow.

    Args:
        startup_idea: The user's startup idea.
        project_id: Optional project ID (auto-generated if not provided).
        on_status_update: Optional callback for status updates.

    Returns:
        The project_id for tracking.
    """
    pid = project_id or str(uuid.uuid4())[:8]

    logger.info("Starting analysis for '%s' (project: %s)", startup_idea[:50], pid)

    # Initialize state
    initial_state: StartupAnalysisState = {
        "project_id": pid,
        "startup_idea": startup_idea,
        "status": "running",
        "current_step": "research",
        "execution_metrics": {},
        "llm_routing_log": [],
        "memory_references": [],
        "errors": [],
        "human_feedback": {},
        "research_plans": {},
        "research_traces": {},
        "research_metrics": {},
    }

    # Store analysis
    register_analysis(pid, initial_state)

    # Check for similar past analyses
    try:
        from agents.memory import MemoryManager
        memory = MemoryManager()
        similar = memory.search_similar_analyses(startup_idea)
        if similar:
            initial_state["memory_references"] = [s["project_id"] for s in similar]
            logger.info("Found %d similar past analyses", len(similar))
    except Exception as e:
        logger.debug("Memory search failed: %s", e)

    # Compile and run graph
    try:
        graph = create_graph()
        compiled = graph.compile()
        _active_analyses[pid]["graph"] = compiled

        # Run the graph — it will pause at human_approval_node
        result = compiled.invoke(initial_state)

        # Update stored state
        _active_analyses[pid]["state"] = result
        _save_active_analyses_backup()

        if on_status_update:
            on_status_update(pid, result.get("status"), result.get("current_step"))

        logger.info(
            "Analysis %s reached status: %s (step: %s)",
            pid,
            result.get("status"),
            result.get("current_step"),
        )

        return pid

    except Exception as e:
        logger.error("Analysis %s failed: %s", pid, e)
        _active_analyses[pid]["state"]["status"] = "failed"
        _active_analyses[pid]["state"]["errors"] = [str(e)]
        _save_active_analyses_backup()
        raise




def resume_analysis(
    project_id: str,
    human_feedback: dict,
) -> dict[str, Any]:
    """Resume a paused analysis after human approval.

    Args:
        project_id: The project ID to resume.
        human_feedback: Dict with {action: "approve"|"reject"|"modify", comments: str}

    Returns:
        The final state after workflow completion.
    """
    if project_id not in _active_analyses:
        raise ValueError(f"No active analysis found for project {project_id}")

    analysis = _active_analyses[project_id]
    state = analysis["state"]

    if state.get("status") != "awaiting_approval":
        raise ValueError(
            f"Analysis {project_id} is not awaiting approval "
            f"(status: {state.get('status')})"
        )

    logger.info(
        "Resuming analysis %s with feedback: %s",
        project_id,
        human_feedback.get("action"),
    )

    # Update state with human feedback
    state["human_feedback"] = human_feedback
    state["status"] = "running"

    # Re-compile and run from the current state
    try:
        graph = create_graph()
        compiled = graph.compile()

        # The graph will route based on human_feedback in state
        result = compiled.invoke(state)

        # Update stored state
        _active_analyses[project_id]["state"] = result
        _save_active_analyses_backup()

        logger.info(
            "Analysis %s completed with status: %s",
            project_id,
            result.get("status"),
        )

        return result

    except Exception as e:
        logger.error("Analysis %s resume failed: %s", project_id, e)
        state["status"] = "failed"
        state["errors"] = state.get("errors", []) + [str(e)]
        _save_active_analyses_backup()
        raise



def get_analysis_status(project_id: str) -> dict[str, Any]:
    """Get the current status of an analysis.

    Returns a summary dict with status, current step, progress, and metrics.
    """
    if project_id not in _active_analyses:
        # Check if it's a demo
        from demo.scenarios import get_demo_result
        demo = get_demo_result(project_id)
        if demo:
            return demo

        return {"status": "not_found", "project_id": project_id}

    state = _active_analyses[project_id]["state"]
    started_at = _active_analyses[project_id].get("started_at", 0)

    # Calculate progress
    steps = [
        "research", "market_analysis", "competitor_analysis",
        "swot_analysis", "business_strategy", "human_approval",
        "autogen_discussion", "architecture_cost", "report_generation",
        "memory_storage", "completed",
    ]
    current = state.get("current_step", "")
    progress = 0
    if current in steps:
        progress = int((steps.index(current) + 1) / len(steps) * 100)
    if state.get("status") == "completed":
        progress = 100

    return {
        "project_id": project_id,
        "startup_idea": state.get("startup_idea", ""),
        "status": state.get("status", "unknown"),
        "current_step": current,
        "progress": progress,
        "elapsed_seconds": int(time.time() - started_at) if started_at else 0,
        "execution_metrics": state.get("execution_metrics", {}),
        "llm_routing_log": state.get("llm_routing_log", []),
        "memory_references": state.get("memory_references", []),
        "errors": state.get("errors", []),
        "has_report": bool(state.get("report")),
    }


def get_analysis_state(project_id: str) -> Optional[dict[str, Any]]:
    """Get the full state of an analysis (for report generation, etc.)."""
    if project_id in _active_analyses:
        return dict(_active_analyses[project_id]["state"])

    # Check demos
    from demo.scenarios import get_demo_result
    return get_demo_result(project_id)


def list_analyses() -> list[dict]:
    """List all active/completed analyses."""
    results = []
    for pid, data in _active_analyses.items():
        state = data["state"]
        results.append({
            "project_id": pid,
            "startup_idea": state.get("startup_idea", ""),
            "status": state.get("status", "unknown"),
            "current_step": state.get("current_step", ""),
        })
    return results
