"""
StartupPilot AI — Research Explorer Page

Visualizes the Research Plan, step-by-step Multi-Hop Navigation path,
internal agent reasoning chain, and gathered Evidence Vault for each agent phase.
"""

from __future__ import annotations

import streamlit as st
import requests
from pathlib import Path
from datetime import datetime

from app import apply_custom_css

# Apply styling
apply_custom_css()

# Header
st.markdown("## 🔬 Agentic Research Explorer")
st.markdown(
    "Observe how the AI agents behave like real researchers. "
    "This page displays their sub-question plans, step-by-step multi-hop wiki traversal trails, "
    "reasoning chains, and gathered facts."
)

backend_url = st.session_state.backend_url
active_pid = st.session_state.current_project_id

# ── Project Discovery ─────────────────────────────────────────────────────────

from config import get_settings
try:
    settings = get_settings()
    wiki_root = Path(settings.wiki_dir)
except Exception:
    wiki_root = Path("data/wiki")

# Always include demo project
available_projects = ["demo-healthcare"]
if wiki_root.exists():
    for p in wiki_root.iterdir():
        if p.is_dir() and (p / "wiki.json").exists() and p.name not in available_projects:
            available_projects.append(p.name)

# ── Sidebar Selector ──────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🗂️ Select Workspace")
    
    # Pre-select active project if possible
    default_idx = 0
    if active_pid in available_projects:
        default_idx = available_projects.index(active_pid)
        
    selected_project = st.selectbox(
        "Active Project:",
        options=available_projects,
        index=default_idx,
        format_func=lambda x: "🏥 AI Healthcare (Demo)" if x == "demo-healthcare" else f"📁 {x}"
    )
    
    st.markdown("---")
    st.markdown("### 💡 Interview Talking Point")
    st.markdown("""
    <div class="premium-card" style="padding: 15px; font-size: 0.85rem; line-height: 1.4;">
        <strong>Multi-Hop Agentic Navigation:</strong><br/>
        "Instead of throwing the entire vector store at the agent (which dilutes prompt context and leads to hallucinations), 
        my agents decompose the prompt into sub-questions and navigate the wiki step-by-step. 
        They read a page, extract evidence, and evaluate which related page to hop to next based on links. 
        This models a human research methodology and creates a completely auditable research trace."
    </div>
    """, unsafe_allow_html=True)

# ── Fetch Research Data ───────────────────────────────────────────────────────

def get_research_data(project_id: str) -> dict:
    """Fetch research traces from API, falling back to direct state/scenario query if offline."""
    try:
        res = requests.get(f"{backend_url}/research/{project_id}", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
        
    # Offline fallback
    try:
        from workflows import graph_runner
        state = graph_runner.get_analysis_state(project_id)
        if state:
            return {
                "project_id": project_id,
                "plans": state.get("research_plans", {}),
                "traces": state.get("research_traces", {}),
                "metrics": state.get("research_metrics", {})
            }
    except Exception:
        pass
    return {}

with st.spinner("Fetching Research Trace..."):
    research_data = get_research_data(selected_project)

if not research_data or not research_data.get("plans"):
    st.info("ℹ️ No active research traces recorded for this workspace. Select the Demo scenario or launch an analysis to see traces.")
    st.stop()

plans = research_data.get("plans", {})
traces = research_data.get("traces", {})
metrics = research_data.get("metrics", {})

# ── Select Agent Phase ────────────────────────────────────────────────────────

agent_labels = {
    "research": "🔍 Research Analyst",
    "market_analysis": "📈 Market Analyst",
    "competitor_analysis": "🏢 Competitor Analyst",
    "swot_analysis": "⚖️ SWOT Strategist",
    "business_strategy": "⚡ Business Consultant",
    "architecture_design": "🏗️ Cloud Architect",
    "cost_estimation": "💰 Financial Analyst"
}

available_agents = [k for k in plans.keys()]
if not available_agents:
    st.warning("No agent research steps found.")
    st.stop()

# Render horizontal selector
selected_agent = st.radio(
    "Select Agent Phase to Audit:",
    options=available_agents,
    format_func=lambda x: agent_labels.get(x, x.upper()),
    horizontal=True
)

st.markdown("---")

# ── Render Research Plan ──────────────────────────────────────────────────────

agent_plan = plans.get(selected_agent, {})
agent_trace = traces.get(selected_agent, {})
agent_metrics = metrics.get(selected_agent, {})

col_plan, col_metrics = st.columns([2, 1], gap="large")

with col_plan:
    st.markdown("### 📋 1. Research Plan & Sub-questions")
    st.markdown(
        f"Before beginning execution, the **Research Planner** analyzed the startup concept "
        f"and formulated these sub-questions to guide the traversal."
    )
    
    for sq in agent_plan.get("sub_questions", []):
        status_color = "green" if sq.get("status") == "completed" else "orange"
        st.markdown(f"""
        <div style="background: rgba(22, 25, 32, 0.5); border-left: 4px solid #7f5af0; border-radius: 6px; padding: 15px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 600; color: #f8fafc;">{sq.get('question_id').upper()}: {sq.get('text')}</span>
                <span style="font-size: 0.75rem; background: rgba(44, 182, 125, 0.1); color: #2cb67d; border: 1px solid rgba(44, 182, 125, 0.2); padding: 2px 8px; border-radius: 4px;">{sq.get('status').upper()}</span>
            </div>
            <div style="margin-top: 8px; font-size: 0.8rem; color: #94a3b8;">
                Target Entry-point Pages: {', '.join([f"<code>{p}</code>" for p in sq.get('target_pages', [])]) or 'None (dynamic seed)'}
            </div>
        </div>
        """, unsafe_allow_html=True)

with col_metrics:
    st.markdown("### 📊 Observability Metrics")
    st.markdown("Traversal cost and complexity statistics.")
    
    m_depth = agent_metrics.get("max_depth", agent_trace.get("depth", 0))
    m_explored = agent_metrics.get("pages_explored", len(agent_trace.get("navigation_path", [])))
    m_evidence = agent_metrics.get("evidence_count", len(agent_trace.get("evidence_gathered", [])))
    m_success = "SUCCESSFUL" if agent_metrics.get("success", m_evidence > 0) else "NO EVIDENCE"
    
    st.markdown(f"""
    <div style="background: #141722; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
        <span style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase;">Traversal Depth</span>
        <div style="font-size: 1.8rem; font-weight: 700; color: #7f5af0;">{m_depth} Hops</div>
    </div>
    <div style="background: #141722; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
        <span style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase;">Pages Explored</span>
        <div style="font-size: 1.8rem; font-weight: 700; color: #2cb67d;">{m_explored} Pages</div>
    </div>
    <div style="background: #141722; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
        <span style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase;">Evidence Extracted</span>
        <div style="font-size: 1.8rem; font-weight: 700; color: #ff9f43;">{m_evidence} Items</div>
    </div>
    """, unsafe_allow_html=True)

# ── Render Multi-Hop Navigation Trail ─────────────────────────────────────────

st.markdown("<br/>", unsafe_allow_html=True)
st.markdown("### 🔀 2. Multi-Hop Traversal Trail")
st.markdown(
    "Chronological step-by-step path taken by the navigator across the Knowledge Wiki network."
)

path = agent_trace.get("navigation_path", [])
if path:
    # Render a beautiful arrow-linked pathway
    path_html = []
    path_html.append('<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 10px; background: rgba(255,255,255,0.02); padding: 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 25px;">')
    path_html.append('<div style="font-size: 0.8rem; background: #7f5af0; color: white; padding: 5px 12px; border-radius: 4px; font-weight: 600;">START</div>')
    
    for idx, pid in enumerate(path):
        # Determine icon based on page id
        icon = "📈" if "market" in pid else "⚖️" if "regulatory" in pid or "hipaa" in pid else "🏢" if "entity" in pid else "📄"
        
        path_html.append('<div style="font-size: 1.2rem; color: #94a3b8;">➔</div>')
        path_html.append(f"""
        <div style="background: rgba(22, 25, 32, 0.8); border: 1px solid rgba(127, 90, 240, 0.3); padding: 8px 15px; border-radius: 6px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="font-size: 0.65rem; color: #94a3b8; text-transform: uppercase;">Hop {idx + 1}</div>
            <div style="font-size: 0.85rem; font-weight: 600; color: #f1f5f9;">{icon} {pid}</div>
        </div>
        """)
        
    path_html.append('<div style="font-size: 1.2rem; color: #94a3b8;">➔</div>')
    path_html.append('<div style="font-size: 0.8rem; background: #2cb67d; color: white; padding: 5px 12px; border-radius: 4px; font-weight: 600;">END</div>')
    path_html.append('</div>')
    
    st.markdown("".join(path_html), unsafe_allow_html=True)
else:
    st.caption("No traversal path recorded.")

# ── Render Reasoning Chain & Evidence ─────────────────────────────────────────

col_reasoning, col_evidence = st.columns([1, 1], gap="large")

with col_reasoning:
    st.markdown("### 🧠 3. Reasoning Chain")
    st.markdown("Internal agent monologue explaining the decision behind each hop.")
    
    reasons = agent_trace.get("reasoning_chain", [])
    if reasons:
        for idx, r in enumerate(reasons):
            # Parse prefix "[page_id]" from monologue
            match = re.match(r'^\[([^\]]+)\]\s*(.*)$', r)
            if match:
                pid = match.group(1)
                text = match.group(2)
                st.markdown(f"""
                <div style="margin-bottom: 15px; padding-left: 10px; border-left: 2px solid #7f5af0;">
                    <div style="font-size: 0.75rem; color: #94a3b8; font-family: monospace;">STEP {idx + 1} | {pid.upper()}</div>
                    <div style="font-size: 0.85rem; color: #cbd5e1; font-style: italic;">"{text}"</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"- *Step {idx + 1}*: {r}")
    else:
        st.caption("No reasoning monologues recorded.")

with col_evidence:
    st.markdown("### 🏆 4. Evidence Vault")
    st.markdown("Extracted claims and facts backed by source documentation.")
    
    evidence = agent_trace.get("evidence_gathered", [])
    if evidence:
        for ev in evidence:
            st.markdown(f"""
            <div style="background: rgba(44, 182, 125, 0.03); border: 1px solid rgba(44, 182, 125, 0.15); border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 6px; margin-bottom: 8px;">
                    <span style="font-size: 0.75rem; color: #2cb67d; font-weight: 600;">ID: {ev.get('evidence_id')}</span>
                    <span style="font-size: 0.75rem; color: #94a3b8;">Source: {ev.get('title_or_name')} ({ev.get('page_id')})</span>
                </div>
                <div style="font-size: 0.9rem; font-weight: 500; color: #f1f5f9; line-height: 1.4; margin-bottom: 8px;">
                    "{ev.get('fact')}"
                </div>
                <div style="font-size: 0.8rem; color: #94a3b8; background: rgba(255,255,255,0.02); padding: 6px 10px; border-radius: 4px;">
                    <strong>Relevance Reasoning:</strong> {ev.get('relevance_reasoning')}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No evidence items gathered.")
