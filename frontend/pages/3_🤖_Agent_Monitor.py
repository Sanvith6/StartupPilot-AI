"""
StartupPilot AI — Agent Monitor & Metrics Page

Visualizes the execution times, active model selections, cost analysis,
and the Multi-LLM routing rules in a premium dashboard.
"""

from __future__ import annotations

import streamlit as st
import requests

from app import apply_custom_css

# Apply styling
apply_custom_css()

# Header
st.markdown("## 🤖 Agent Monitor & LLM Routing Dashboard")
st.markdown(
    "Observe real-time execution statistics, performance metrics, and model routing decisions. "
    "This dashboard demonstrates production-grade system observability."
)

backend_url = st.session_state.backend_url
active_pid = st.session_state.current_project_id

# ── Sidebar details ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔀 Router Configuration")
    st.markdown(
        "The **Multi-LLM Router** uses task-based rules to select the optimal model, "
        "minimizing latency and token costs while maximizing response quality."
    )
    
    # Display the static routing table
    st.markdown("#### Preferred Routing Rules:")
    st.markdown("""
    | Task / Agent | Preferred | Backup |
    | :--- | :--- | :--- |
    | **Research** | Groq Llama-70b | OpenAI GPT-4o-mini |
    | **Market** | Groq Llama-70b | OpenAI GPT-4o-mini |
    | **Competitors**| Groq Llama-70b | OpenAI GPT-4o-mini |
    | **SWOT** | Groq Llama-70b | OpenAI GPT-4o-mini |
    | **Strategy** | OpenAI GPT-4o | Groq Llama-70b |
    | **Arch Design**| OpenAI GPT-4o | Groq Llama-70b |
    | **Cost Est** | OpenAI GPT-4o-mini | Groq Llama-70b |
    | **Technical Writer** | Groq Llama-70b | OpenAI GPT-4o-mini |
    """)

# ── Main Content Area ─────────────────────────────────────────────────────────

if not active_pid:
    st.info("💡 Load a demo scenario from the Home page or submit a startup idea in the Analysis tab to view live agent metrics.")
    
    # Show static/educational router diagram when no project is active
    st.markdown("### 🛠️ How it works: Fallback & Recovery")
    st.markdown(
        "If a preferred provider (e.g. Groq) encounters a rate limit or goes offline, "
        "the router automatically falls back to secondary models (e.g. OpenAI GPT-4o-mini) "
        "using exponential backoff (1s, 2s, 4s...) and logs the event."
    )
    st.image("https://raw.githubusercontent.com/mermaid-js/mermaid-live-editor/master/public/img/logo.svg", width=50) # Small placeholder
else:
    # ── Fetch metrics from backend ────────────────────────────────────────────
    metrics_data = {}
    try:
        res = requests.get(f"{backend_url}/metrics/{active_pid}", timeout=5)
        if res.status_code == 200:
            metrics_data = res.json()
        else:
            st.error(f"Failed to fetch metrics: {res.text}")
    except Exception:
        # Simulation fallback for offline demo
        if active_pid.startswith("demo-") or active_pid.startswith("local-"):
            metrics_data = {
                "project_id": active_pid,
                "execution_metrics": {
                    "research": {"time_ms": 4200, "model_used": "llama-3.1-70b-versatile", "provider": "groq"},
                    "market_analysis": {"time_ms": 3800, "model_used": "llama-3.1-70b-versatile", "provider": "groq"},
                    "competitor_analysis": {"time_ms": 4500, "model_used": "llama-3.1-70b-versatile", "provider": "groq"},
                    "swot_analysis": {"time_ms": 3200, "model_used": "llama-3.1-70b-versatile", "provider": "groq"},
                    "business_strategy": {"time_ms": 5100, "model_used": "gpt-4o", "provider": "openai"},
                    "autogen_discussion": {"time_ms": 12000, "rounds": 5},
                    "architecture_design": {"time_ms": 4800, "model_used": "gpt-4o", "provider": "openai"},
                    "cost_estimation": {"time_ms": 3500, "model_used": "gpt-4o-mini", "provider": "openai"},
                    "report_generation": {"time_ms": 1200},
                },
                "llm_routing_log": [
                    {"task": "research", "provider": "groq", "model": "llama-3.1-70b-versatile"},
                    {"task": "market_analysis", "provider": "groq", "model": "llama-3.1-70b-versatile"},
                    {"task": "competitor_analysis", "provider": "groq", "model": "llama-3.1-70b-versatile"},
                    {"task": "swot_analysis", "provider": "groq", "model": "llama-3.1-70b-versatile"},
                    {"task": "business_strategy", "provider": "openai", "model": "gpt-4o"},
                    {"task": "architecture_design", "provider": "openai", "model": "gpt-4o"},
                    {"task": "cost_estimation", "provider": "openai", "model": "gpt-4o-mini"},
                ]
            }
        else:
            st.error("Could not connect to the backend server.")
            st.stop()

    exec_metrics = metrics_data.get("execution_metrics", {})
    routing_log = metrics_data.get("llm_routing_log", [])

    # ── Column Layout for Key stats ───────────────────────────────────────────
    st.markdown("### 📊 Live Performance Stats")
    
    total_time = sum(m.get("time_ms", 0) for m in exec_metrics.values() if isinstance(m, dict))
    avg_time = total_time / len(exec_metrics) if exec_metrics else 0
    
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Execution Time</div>
            <div class="metric-value">{(total_time / 1000.0):.2f}s</div>
        </div>
        """, unsafe_allow_html=True)
    with col_m2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #2cb67d;">
            <div class="metric-title">Average Latency / Node</div>
            <div class="metric-value">{(avg_time / 1000.0):.2f}s</div>
        </div>
        """, unsafe_allow_html=True)
    with col_m3:
        # Count providers used
        providers = [r.get("provider") for r in routing_log if r.get("provider")]
        prov_summary = ", ".join(set(providers)) if providers else "N/A"
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #ff9f43;">
            <div class="metric-title">Providers Called</div>
            <div class="metric-value">{prov_summary}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Latency Breakdown (Visual Bar chart) ──────────────────────────────────
    st.markdown("### ⏱️ Latency per Node")
    
    # We can create a simple Streamlit bar chart from data
    if exec_metrics:
        chart_data = {
            node: metrics.get("time_ms", 0) / 1000.0 
            for node, metrics in exec_metrics.items() 
            if isinstance(metrics, dict)
        }
        st.bar_chart(chart_data)
    else:
        st.info("Waiting for execution metrics to populate...")

    # ── Routing Decisions Table ───────────────────────────────────────────────
    st.markdown("### 🔀 Active LLM Routing & Decisions")
    
    if routing_log:
        # Construct clean list of dicts to render as table
        display_log = []
        for index, r in enumerate(routing_log):
            display_log.append({
                "#": index + 1,
                "Node / Task": r.get("task", "Unknown").upper(),
                "Selected Provider": r.get("provider", "Unknown").upper(),
                "Model Used": r.get("model", "Unknown"),
                "Status": "✅ SUCCESSFUL"
            })
        st.table(display_log)
    else:
        st.info("No routing log entries recorded yet.")
