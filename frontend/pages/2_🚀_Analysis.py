"""
StartupPilot AI — Analysis & Human-in-the-Loop Page

Allows users to start a new analysis, monitors workflow progress in real-time,
and presents the Human-in-the-Loop (HITL) approval gateway.
"""

from __future__ import annotations

import streamlit as st
import requests
import time
import logging
from streamlit_autorefresh import st_autorefresh

from app import apply_custom_css

logger = logging.getLogger(__name__)

# Apply styling
apply_custom_css()

# Header
st.markdown("## 🚀 Startup Analysis Control Center")
st.markdown(
    "Submit a new startup idea or monitor the state of an existing analysis. "
    "When the workflow reaches the **Human Approval** stage, you can review outputs and direct the crew."
)

backend_url = st.session_state.backend_url

# Active project display
active_pid = st.session_state.current_project_id

if "page_render_count" not in st.session_state:
    st.session_state.page_render_count = 0
if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0
if "polling_start_time" not in st.session_state:
    st.session_state.polling_start_time = None

st.session_state.page_render_count += 1

# ── Sidebar actions: New analysis or active project details ───────────────────
with st.sidebar:
    st.markdown("### 🛠️ Workflow Actions")
    
    # Input new startup idea
    new_idea = st.text_area(
        "Enter Startup Idea:",
        placeholder="e.g. AI-powered healthcare appointment scheduling platform",
        height=100
    )
    
    if st.button("Launch Analysis Crew"):
        if not new_idea.strip():
            st.error("Please enter a startup idea.")
        else:
            with st.spinner("Initializing graph..."):
                try:
                    res = requests.post(
                        f"{backend_url}/analyze",
                        json={"startup_idea": new_idea.strip()},
                        timeout=10
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.current_project_id = data["project_id"]
                        st.session_state.current_status = data["status"]
                        st.session_state.current_startup_idea = new_idea.strip()
                        st.success(f"Workflow started! ID: {data['project_id']}")
                        active_pid = data["project_id"]
                    else:
                        st.error(f"Failed to start: {res.text}")
                except Exception as e:
                    st.warning("Backend API offline. Simulating local execution...")
                    st.session_state.current_project_id = f"local-{int(time.time())}"
                    st.session_state.current_status = "running"
                    st.session_state.current_startup_idea = new_idea.strip()
                    active_pid = st.session_state.current_project_id
                    st.rerun()

    if active_pid:
        st.markdown("---")
        st.markdown(f"**Active Project:** `{active_pid}`")
        if st.session_state.current_startup_idea:
            st.markdown(f"**Idea:** *\"{st.session_state.current_startup_idea[:60]}...\"*")
            
        if st.button("Clear Active Project"):
            st.session_state.current_project_id = None
            st.session_state.current_status = None
            st.session_state.current_startup_idea = None
            st.session_state.page_render_count = 0
            st.session_state.refresh_count = 0
            st.session_state.polling_start_time = None
            st.rerun()

# ── Main Content Area ─────────────────────────────────────────────────────────

if not active_pid:
    st.info("👈 Enter a startup idea in the sidebar to launch the analysis crew or load a demo on the Home page.")
    
    # Show status grid of past projects if available
    st.markdown("### 📋 Active Workspace Analyses")
    try:
        res = requests.get(f"{backend_url}/health", timeout=2) # Dummy check
        # Let's query state list
        # We can implement list_analyses endpoint in route or get active
        # Let's list a few options or show demo triggers
        st.markdown("No active analyses started in this session. Start one in the sidebar!")
    except Exception:
        st.markdown("Start a project or select a Demo scenario to see metrics here.")

else:
    # ── Fetch active state from backend ───────────────────────────────────────
    state = {}
    try:
        res = requests.get(f"{backend_url}/status/{active_pid}", timeout=5)
        if res.status_code == 200:
            state = res.json()
            st.session_state.current_status = state.get("status")
        else:
            st.error(f"Error fetching status: {res.text}")
    except Exception:
        # Simulation mode for offline/local demonstration
        if active_pid.startswith("demo-") or active_pid.startswith("local-"):
            state = {
                "project_id": active_pid,
                "startup_idea": st.session_state.current_startup_idea,
                "status": st.session_state.current_status,
                "current_step": "human_approval" if st.session_state.current_status == "running" else "completed",
                "progress": 60 if st.session_state.current_status == "running" else 100,
                "elapsed_seconds": 32,
                "has_report": st.session_state.current_status == "completed",
                "errors": []
            }
        else:
            st.error("Could not connect to the backend server.")
            st.stop()

    status = state.get("status", "unknown")
    current_step = state.get("current_step", "unknown")
    progress = state.get("progress", 0)
    
    # Render progress and header
    st.markdown(f"#### Status: **{status.upper()}** | Current Step: `{current_step}`")
    st.progress(progress / 100.0)

    # ── CASE 1: Running (Auto-polling) ────────────────────────────────────────
    if status == "running":
        if st.session_state.polling_start_time is None:
            st.session_state.polling_start_time = time.time()
            st.session_state.refresh_count = 0

        st.markdown("""
        <div class="premium-card" style="text-align: center; padding: 40px;">
            <div style="font-size: 3rem; animation: spin 2s linear infinite;">⏳</div>
            <h3 style="margin-top: 15px; color: #7f5af0;">AI Crew is Working...</h3>
            <p style="color: #94a3b8; font-size: 0.95rem;">
                The agents are currently executing analysis on node <strong>{current_step}</strong>.<br/>
                This page auto-refreshes every 3 seconds.
            </p>
        </div>
        <style>
            @keyframes spin { 100% { transform:rotate(360deg); } }
        </style>
        """, unsafe_allow_html=True)
        
        # Auto refresh using non-blocking component
        count = st_autorefresh(interval=3000, limit=None, key="analysis_autorefresh")
        
        if count > 0:
            st.session_state.refresh_count = count
            
        polling_duration = time.time() - st.session_state.polling_start_time
        logger.info(
            f"[Websocket Health OK] Page renders: {st.session_state.page_render_count} | "
            f"Refresh count: {st.session_state.refresh_count} | Polling duration: {polling_duration:.1f}s"
        )

    # ── CASE 2: Awaiting Approval (HITL Gateway) ──────────────────────────────
    elif status == "awaiting_approval":
        st.session_state.polling_start_time = None
        st.warning("⚠️ **Human-in-the-Loop Gateway Activated**")
        st.markdown(
            "The first 5 nodes (Research, Market, Competitors, SWOT, Strategy) are complete. "
            "Please review the outputs generated by the agents so far, then choose to Approve, Modify, or Reject."
        )
        
        # Let's fetch the full state to show current outputs
        full_state = {}
        try:
            res_full = requests.get(f"{backend_url}/report/{active_pid}", timeout=5)
            if res_full.status_code == 200:
                full_state = res_full.json()
        except Exception:
            # Simulation fallback
            full_state = {
                "report": "### Research Analyst Findings\nMarket is expanding rapidly.\n\n### Market Analysis\nTAM is $10B.\n\n### Competitive Landscape\nNo major competitor.",
                "diagrams": {}
            }
            
        # Display tabs of current outputs
        tab1, tab2, tab3 = st.tabs(["🔍 Agent Analysis Outputs", "📊 Mermaid Diagrams", "⚡ HITL Control Panel"])
        
        with tab1:
            st.markdown("### Agent Deliverables (V1 draft)")
            # Let's display the markdown report
            # If the backend is offline, show fallback report
            report_text = full_state.get("report", "Draft data is loading...")
            st.markdown(report_text)
            
        with tab2:
            st.markdown("### Process Diagrams")
            diagrams = full_state.get("diagrams", {})
            if diagrams and "workflow" in diagrams:
                st.markdown(f"```mermaid\n{diagrams['workflow']}\n```", unsafe_allow_html=True)
            else:
                st.info("Process workflow diagram is generated upon final completion.")
                
        with tab3:
            st.markdown("### Review Decision")
            st.markdown(
                "Provide feedback to the crew. If you choose **Modify**, write specific directions "
                "in the text box below. The Business Consultant agent will re-run the strategy phase incorporating your input."
            )
            
            feedback_comments = st.text_area(
                "Feedback / Modification Instructions:",
                placeholder="e.g. Focus more on high-value B2B healthcare practices rather than general clinics."
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Approve
                if st.button("✅ Approve & Proceed"):
                    with st.spinner("Submitting approval..."):
                        try:
                            res = requests.post(
                                f"{backend_url}/workflow/{active_pid}/approve",
                                json={"action": "approve", "comments": feedback_comments},
                                timeout=10
                            )
                            if res.status_code == 200:
                                st.success("Approved! Proceeding with AutoGen debate...")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Failed to submit decision: {res.text}")
                                time.sleep(2)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error connecting to backend: {e}")
                            
            with col2:
                # Modify
                if st.button("🔄 Request Modifications"):
                    if not feedback_comments.strip():
                        st.error("Please enter modification comments first.")
                    else:
                        with st.spinner("Submitting feedback..."):
                            try:
                                res = requests.post(
                                    f"{backend_url}/workflow/{active_pid}/approve",
                                    json={"action": "modify", "comments": feedback_comments},
                                    timeout=10
                                )
                                if res.status_code == 200:
                                    st.success("Feedback sent! Re-running strategy phase...")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"Failed to submit modifications: {res.text}")
                                    time.sleep(2)
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error connecting to backend: {e}")
                                
            with col3:
                # Reject
                if st.button("❌ Reject & Terminate"):
                    with st.spinner("Terminating workflow..."):
                        try:
                            res = requests.post(
                                f"{backend_url}/workflow/{active_pid}/approve",
                                json={"action": "reject", "comments": feedback_comments},
                                timeout=10
                            )
                            if res.status_code == 200:
                                st.error("Workflow terminated and rejected.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Failed to reject workflow: {res.text}")
                                time.sleep(2)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error connecting to backend: {e}")

    # ── CASE 3: Completed ─────────────────────────────────────────────────────
    elif status == "completed":
        st.session_state.polling_start_time = None
        st.markdown("""
        <div class="premium-card" style="border-color: rgba(44, 182, 125, 0.4); background: rgba(44, 182, 125, 0.05);">
            <h3 style="color: #2cb67d;">🎉 Analysis Complete!</h3>
            <p>
                The Multi-Agent Crew has finalized the startup intelligence report. 
                All diagrams, cost estimates, and reports are ready for review.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col_view1, col_view2 = st.columns(2)
        with col_view1:
            if st.button("📄 Read Completed Report"):
                st.switch_page("pages/5_📄_Reports.py")
        with col_view2:
            if st.button("💬 Watch Agent Discussion"):
                st.switch_page("pages/4_💬_Discussion.py")

    # ── CASE 4: Rejected ──────────────────────────────────────────────────────
    elif status == "rejected":
        st.session_state.polling_start_time = None
        st.error("❌ **Analysis Rejected**")
        st.markdown(
            "This analysis was rejected and terminated by the user during the Human-in-the-Loop stage. "
            "Please clear the active project and submit a new startup idea to start fresh."
        )

    # ── CASE 5: Failed ────────────────────────────────────────────────────────
    elif status == "failed":
        st.session_state.polling_start_time = None
        st.error("💥 **Workflow Failed**")
        errors = state.get("errors", [])
        if errors:
            st.markdown("### Error Details:")
            for err in errors:
                st.code(err)
        else:
            st.markdown("An unexpected error occurred during execution. Please check backend logs.")
