"""
StartupPilot AI — API & Workflow Lifecycle Integration Tests

Tests all FastAPI routes and verifies the complete LangGraph + HITL workflow lifecycle.
"""

from __future__ import annotations

import time
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_agents_endpoint(client: TestClient):
    """Test get agents metadata endpoint."""
    response = client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) == 8
    
    # Assert specific details are returned
    first_agent = data["agents"][0]
    assert "role" in first_agent
    assert "goal" in first_agent


def test_demo_scenarios_endpoint(client: TestClient):
    """Test list demo scenarios endpoint."""
    response = client.get("/demo/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert "scenarios" in data
    assert len(data["scenarios"]) == 5
    
    first_scenario = data["scenarios"][0]
    assert "name" in first_scenario
    assert "startup_idea" in first_scenario


def test_run_demo_scenario(client: TestClient):
    """Test running/loading a demo scenario."""
    response = client.post("/demo/run/ai-healthcare")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "demo-healthcare"
    assert data["status"] == "completed"
    assert "message" in data
    
    # Query status of loaded demo
    status_response = client.get("/status/demo-healthcare")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["status"] == "completed"
    assert status_data["progress"] == 100
    assert status_data["has_report"] is True


def test_full_analysis_workflow_lifecycle(client: TestClient):
    """Test the complete workflow lifecycle from start to approval and completion."""
    project_id = f"test_proj_{int(time.time())}"
    idea = "AI-powered healthcare appointment scheduling platform"
    
    # ── 1. Start Analysis ─────────────────────────────────────────────────────
    start_res = client.post(
        "/analyze",
        json={"startup_idea": idea, "project_id": project_id}
    )
    assert start_res.status_code == 200
    start_data = start_res.json()
    assert start_data["project_id"] == project_id
    assert start_data["status"] == "running"
    
    # Wait for the background thread to finish the first 5 nodes and reach human_approval
    # In tests, since the chains are mocked and execute instantly, it will pause almost immediately.
    # We will poll status with a short timeout.
    max_retries = 5
    status_data = {}
    for _ in range(max_retries):
        status_res = client.get(f"/status/{project_id}")
        assert status_res.status_code == 200
        status_data = status_res.json()
        if status_data["status"] == "awaiting_approval":
            break
        time.sleep(1)
        
    assert status_data["status"] == "awaiting_approval"
    assert status_data["current_step"] == "human_approval"
    assert status_data["progress"] > 0
    assert status_data["has_report"] is False
    
    # ── 2. Submit Human-in-the-Loop Approval ──────────────────────────────────
    approve_res = client.post(
        f"/workflow/{project_id}/approve",
        json={"action": "approve", "comments": "Proceed with debate."}
    )
    assert approve_res.status_code == 200
    approve_data = approve_res.json()
    # It starts executing remainder in background
    assert approve_data["status"] == "running"
    
    # ── 3. Poll Completion ────────────────────────────────────────────────────
    completed_data = {}
    for _ in range(max_retries):
        status_res = client.get(f"/status/{project_id}")
        assert status_res.status_code == 200
        completed_data = status_res.json()
        if completed_data["status"] == "completed":
            break
        time.sleep(1)
        
    assert completed_data["status"] == "completed"
    assert completed_data["current_step"] == "completed"
    assert completed_data["progress"] == 100
    assert completed_data["has_report"] is True
    
    # ── 4. Retrieve Deliverables (Report & Metrics) ───────────────────────────
    report_res = client.get(f"/report/{project_id}")
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["project_id"] == project_id
    assert report_data["startup_idea"] == idea
    assert "report" in report_data
    assert "discussion_transcript" in report_data
    
    metrics_res = client.get(f"/metrics/{project_id}")
    assert metrics_res.status_code == 200
    metrics_data = metrics_res.json()
    assert metrics_data["project_id"] == project_id
    assert "execution_metrics" in metrics_data
    assert "llm_routing_log" in metrics_data
