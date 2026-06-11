"""
StartupPilot AI — API Routes

FastAPI router containing all endpoints for starting, monitoring, and approving analyses.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from backend import models
from backend.services import process_document_upload
from config import get_settings
from demo.scenarios import get_demo_scenarios, run_demo
from agents.crew_agents import get_agent_info
from workflows import graph_runner
from workflows.graph_runner import _active_analyses, register_analysis, _save_active_analyses_backup

from reports.generator import save_report_as_html, save_report_as_pdf

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Health & Info ─────────────────────────────────────────────────────────────

@router.get("/health", response_model=models.HealthStatusResponse)
def health_check():
    """Verify backend health and connection."""
    return {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


@router.get("/agents", response_model=models.AgentsListResponse)
def list_agents():
    """List all 8 CrewAI agents with their roles and goals."""
    return {"agents": get_agent_info()}


# ── Analysis Lifecycle ────────────────────────────────────────────────────────

@router.post("/analyze", response_model=models.AnalysisStartResponse)
def start_analysis_endpoint(
    request: models.AnalysisStartRequest,
    background_tasks: BackgroundTasks
):
    """Start a new startup analysis. Runs the first 5 nodes in the background."""
    project_id = request.project_id or f"project_{int(time.time())}"
    initial_state = {
        "project_id": project_id,
        "startup_idea": request.startup_idea,
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
    register_analysis(project_id, initial_state)

    # Run the graph orchestrator as a background task
    background_tasks.add_task(
        graph_runner.start_analysis,
        startup_idea=request.startup_idea,
        project_id=project_id
    )
    
    return {
        "project_id": project_id,
        "status": "running",
        "message": "Analysis workflow initiated successfully"
    }


@router.get("/status/{project_id}", response_model=models.AnalysisStatusResponse)
def get_status(project_id: str):
    """Get the current progress, step, metrics, and routing logs of an analysis."""
    status_summary = graph_runner.get_analysis_status(project_id)
    if status_summary.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return status_summary


@router.post("/workflow/{project_id}/approve", response_model=models.AnalysisStatusResponse)
def approve_workflow(
    project_id: str,
    request: models.HumanApprovalRequest,
    background_tasks: BackgroundTasks
):
    """Resume a paused workflow after human-in-the-loop review.
    
    If action is 'approve' or 'modify', execution resumes in the background.
    If action is 'reject', workflow is marked as rejected immediately.
    """
    if project_id not in _active_analyses:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
    state = _active_analyses[project_id]["state"]
    if state.get("status") != "awaiting_approval":
        raise HTTPException(
            status_code=400, 
            detail=f"Project {project_id} is not awaiting approval (status: {state.get('status')})"
        )
        
    feedback = {
        "action": request.action,
        "comments": request.comments or ""
    }
    
    if request.action == "reject":
        state["status"] = "rejected"
        state["current_step"] = "human_approval"
        state["human_feedback"] = feedback
        logger.info("Project %s rejected by user.", project_id)
    else:
        # Resume running the graph in the background
        background_tasks.add_task(
            graph_runner.resume_analysis,
            project_id=project_id,
            human_feedback=feedback
        )
        
    status_summary = graph_runner.get_analysis_status(project_id)
    if request.action != "reject":
        status_summary["status"] = "running"
    return status_summary


# ── RAG Support ────────────────────────────────────────────────────────────────

@router.post("/upload")
def upload_document(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    startup_idea: str = Form(default=""),
):
    """Upload a document (PDF/DOCX/TXT/MD) to the RAG vector store and compile wiki."""
    if project_id not in _active_analyses:
        initial_state = {
            "project_id": project_id,
            "startup_idea": startup_idea or "Uploaded Reference Documents",
            "status": "pending",
            "current_step": "upload",
            "execution_metrics": {},
            "llm_routing_log": [],
            "memory_references": [],
            "errors": [],
            "human_feedback": {},
            "wiki_compiled": False,
            "wiki_stats": {},
        }
        register_analysis(project_id, initial_state)

    # Get startup_idea from existing state if not provided
    if not startup_idea:
        startup_idea = _active_analyses[project_id]["state"].get("startup_idea", "")

    try:
        result = process_document_upload(project_id, file, startup_idea)

        # Update wiki state
        if result.get("wiki_stats"):
            _active_analyses[project_id]["state"]["wiki_compiled"] = True
            _active_analyses[project_id]["state"]["wiki_stats"] = result["wiki_stats"]
            _save_active_analyses_backup()

        return {
            "project_id": project_id,
            "filename": file.filename,
            "chunks_added": result["chunks_added"],
            "wiki_stats": result.get("wiki_stats", {}),
            "message": "Document uploaded, indexed, and compiled into wiki"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


# ── Reports & Deliverables ───────────────────────────────────────────────────

@router.get("/report/{project_id}")
def get_report(project_id: str, format: str = "json"):
    """Get the compiled startup report.
    
    Query Parameter `format`:
    - 'json' (default): Returns JSON metadata, markdown report text, and diagrams.
    - 'md': Returns raw Markdown text response.
    - 'html': Returns a styled HTML file download.
    - 'pdf': Returns a compiled PDF file download.
    """
    state = graph_runner.get_analysis_state(project_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
    report_md = state.get("report")
    if not report_md:
        if state.get("status") in ("awaiting_approval", "running"):
            from reports.generator import generate_report
            report_md = generate_report(state)
        else:
            raise HTTPException(status_code=400, detail="Report has not been generated yet.")
        
    if format == "md":
        return Response(content=report_md, media_type="text/markdown")
        
    elif format == "html":
        try:
            html_path = save_report_as_html(project_id, report_md)
            return FileResponse(
                html_path, 
                media_type="text/html", 
                filename=f"startuppilot_report_{project_id}.html"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"HTML generation failed: {str(e)}")
            
    elif format == "pdf":
        try:
            pdf_path = save_report_as_pdf(project_id, report_md)
            if pdf_path and Path(pdf_path).exists():
                return FileResponse(
                    pdf_path, 
                    media_type="application/pdf", 
                    filename=f"startuppilot_report_{project_id}.pdf"
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to compile PDF.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF compilation failed: {str(e)}")
            
    # Default JSON
    return {
        "project_id": project_id,
        "startup_idea": state.get("startup_idea"),
        "report": report_md,
        "diagrams": state.get("diagrams", {}),
        "discussion_transcript": state.get("discussion_transcript", "")
    }


@router.get("/metrics/{project_id}", response_model=models.MetricsResponse)
def get_metrics(project_id: str):
    """Retrieve execution times, model usages, costs, and routing decisions."""
    state = graph_runner.get_analysis_state(project_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
    return {
        "project_id": project_id,
        "execution_metrics": state.get("execution_metrics", {}),
        "llm_routing_log": state.get("llm_routing_log", [])
    }


# ── Demo Mode ─────────────────────────────────────────────────────────────────

@router.get("/demo/scenarios", response_model=models.DemoScenariosResponse)
def list_demo_scenarios():
    """List pre-cached demo scenarios."""
    return {"scenarios": get_demo_scenarios()}


@router.post("/demo/run/{scenario}")
def run_demo_endpoint(scenario: str):
    """Load cached analysis results for a demo scenario instantly."""
    try:
        state = run_demo(scenario)
        # Store in active analyses so status/report endpoints can query it
        _active_analyses[state["project_id"]] = {
            "state": state,
            "started_at": time.time(),
            "graph": None
        }
        return {
            "project_id": state["project_id"],
            "status": state["status"],
            "message": f"Demo scenario '{scenario}' loaded successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Knowledge Wiki ────────────────────────────────────────────────────────────

@router.get("/wiki/{project_id}", response_model=models.WikiStatsResponse)
def get_wiki_stats(project_id: str):
    """Get Knowledge Wiki statistics for a project."""
    try:
        from knowledge_wiki.compiler import KnowledgeCompiler

        compiler = KnowledgeCompiler()
        wiki = compiler.get_wiki(project_id)

        if not wiki:
            raise HTTPException(
                status_code=404,
                detail=f"No wiki compiled for project {project_id}",
            )

        return wiki.get_stats()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wiki/{project_id}/pages", response_model=models.WikiPageListResponse)
def list_wiki_pages(project_id: str):
    """List all topic and entity pages in the Knowledge Wiki."""
    try:
        from knowledge_wiki.compiler import KnowledgeCompiler

        compiler = KnowledgeCompiler()
        wiki = compiler.get_wiki(project_id)

        if not wiki:
            raise HTTPException(
                status_code=404,
                detail=f"No wiki compiled for project {project_id}",
            )

        topic_pages = [
            models.WikiPageResponse(
                page_id=p.page_id,
                page_type="topic",
                title=p.title,
                category_or_type=p.category.value,
                summary=p.summary,
                content=p.content,
                key_facts=p.key_facts,
                related_pages=p.related_entities + p.related_topics,
                source_type=p.source_type.value,
                version=p.version,
                confidence=p.confidence,
            )
            for p in wiki.topic_pages.values()
        ]

        entity_pages = [
            models.WikiPageResponse(
                page_id=p.page_id,
                page_type="entity",
                title=p.name,
                category_or_type=p.entity_type.value,
                summary=p.summary,
                attributes=p.attributes,
                related_pages=p.related_entities + p.related_topics,
                source_type=p.source_type.value,
                version=p.version,
                confidence=p.confidence,
            )
            for p in wiki.entity_pages.values()
        ]

        return models.WikiPageListResponse(
            project_id=project_id,
            topic_pages=topic_pages,
            entity_pages=entity_pages,
            stats=models.WikiStatsResponse(**wiki.get_stats()),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wiki/{project_id}/page/{page_id}", response_model=models.WikiPageResponse)
def get_wiki_page(project_id: str, page_id: str):
    """Get a specific wiki page by ID."""
    try:
        from knowledge_wiki.compiler import KnowledgeCompiler

        compiler = KnowledgeCompiler()
        wiki = compiler.get_wiki(project_id)

        if not wiki:
            raise HTTPException(
                status_code=404,
                detail=f"No wiki compiled for project {project_id}",
            )

        page = wiki.get_page(page_id)
        if not page:
            raise HTTPException(
                status_code=404,
                detail=f"Page '{page_id}' not found in wiki",
            )

        from knowledge_wiki.models import TopicPage

        if isinstance(page, TopicPage):
            return models.WikiPageResponse(
                page_id=page.page_id,
                page_type="topic",
                title=page.title,
                category_or_type=page.category.value,
                summary=page.summary,
                content=page.content,
                key_facts=page.key_facts,
                related_pages=page.related_entities + page.related_topics,
                source_type=page.source_type.value,
                version=page.version,
                confidence=page.confidence,
            )
        else:
            return models.WikiPageResponse(
                page_id=page.page_id,
                page_type="entity",
                title=page.name,
                category_or_type=page.entity_type.value,
                summary=page.summary,
                attributes=page.attributes,
                related_pages=page.related_entities + page.related_topics,
                source_type=page.source_type.value,
                version=page.version,
                confidence=page.confidence,
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Research Platform ─────────────────────────────────────────────────────────

@router.get("/research/{project_id}", response_model=models.ProjectResearchResponse)
def get_project_research(project_id: str):
    """Retrieve all research plans, traces, and metrics for a project."""
    from workflows import graph_runner

    state = graph_runner.get_analysis_state(project_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    plans = state.get("research_plans", {})
    traces = state.get("research_traces", {})
    metrics = state.get("research_metrics", {})

    return {
        "project_id": project_id,
        "plans": plans,
        "traces": traces,
        "metrics": metrics
    }


@router.get("/research/{project_id}/agent/{agent_type}", response_model=models.ResearchTraceResponse)
def get_agent_research_trace(project_id: str, agent_type: str):
    """Retrieve the research plan and trace for a specific agent step."""
    from workflows import graph_runner

    state = graph_runner.get_analysis_state(project_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    traces = state.get("research_traces", {})
    if agent_type not in traces:
        raise HTTPException(
            status_code=404,
            detail=f"No research trace found for agent '{agent_type}' in project {project_id}"
        )

    return traces[agent_type]
