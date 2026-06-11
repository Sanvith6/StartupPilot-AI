"""
StartupPilot AI — Home Page

The landing page of the platform. Showcases the system architecture,
describes the 8 specialized agents, and hosts the Demo Mode selector.
"""

from __future__ import annotations

import streamlit as st
import requests

from app import apply_custom_css

# Apply page styling
apply_custom_css()

# Header Section with stunning gradient text
st.markdown("""
<div style="text-align: center; padding: 30px 0 20px 0;">
    <h1 style="font-size: 3.5rem; background: linear-gradient(135deg, #7f5af0 0%, #2cb67d 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        🚀 StartupPilot AI
    </h1>
    <p style="font-size: 1.25rem; color: #94a3b8; max-width: 800px; margin: 0 auto; line-height: 1.6;">
        An Enterprise-Grade Multi-Agent Startup Intelligence Platform. 
        Input your startup idea and let a team of 8 specialized autonomous agents research, analyze, 
        design cloud architectures, estimate costs, and debate viability.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Layout: Split page into two columns (Intro & Architecture / Demo Scenarios)
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.markdown("### 🤖 Meet the Autonomous Crew")
    st.markdown(
        "The system deploys 8 specialized agents built on **CrewAI** and **AutoGen**, "
        "collaborating through a stateful **LangGraph** orchestration workflow."
    )
    
    # Grid of agents (using cards)
    agents_data = [
        {"icon": "🔬", "role": "Senior Research Analyst", "goal": "Industry trends, regulatory factors, and growth drivers"},
        {"icon": "📊", "role": "Senior Market Analyst", "goal": "TAM/SAM/SOM sizing and customer segmentation"},
        {"icon": "🎯", "role": "Competitive Intelligence Analyst", "goal": "Competitor mapping and differentiation strategy"},
        {"icon": "⚡", "role": "SWOT Strategist", "goal": "Detailed SWOT mapping and actionable recommendations"},
        {"icon": "💡", "role": "Senior Business Consultant", "goal": "Business models, GTM planning, and roadmap design"},
        {"icon": "🏗️", "role": "Principal Cloud Architect", "goal": "Scalable, secure, HIPAA-ready AWS/GCP system design"},
        {"icon": "💰", "role": "Cloud Financial Analyst", "goal": "Unit economics, multi-stage monthly cost estimations"},
        {"icon": "✍️", "role": "Senior Technical Writer", "goal": "Investor-ready report compilation (PDF/HTML/MD)"}
    ]
    
    # 2x4 Grid
    cols = st.columns(2)
    for index, agent in enumerate(agents_data):
        col = cols[index % 2]
        with col:
            st.markdown(f"""
            <div class="premium-card" style="padding: 18px; margin-bottom: 12px; height: 160px;">
                <div style="font-size: 1.5rem; margin-bottom: 6px;">{agent['icon']}</div>
                <div style="font-weight: 600; color: #f8fafc; font-size: 1rem; margin-bottom: 4px;">{agent['role']}</div>
                <div style="font-size: 0.85rem; color: #94a3b8; line-height: 1.4;">{agent['goal']}</div>
            </div>
            """, unsafe_allow_html=True)

with col_right:
    st.markdown("### ⚡ Demo Mode (Secret Weapon)")
    st.markdown(
        "Recruiters and reviewers: try the full platform with **one click — no API keys required**. "
        "Select a pre-cached scenario below to instantly load a production-grade multi-agent analysis."
    )
    
    # Fetch demo scenarios from backend or fallback to hardcoded list
    backend_url = st.session_state.backend_url
    scenarios = []
    
    try:
        response = requests.get(f"{backend_url}/demo/scenarios", timeout=5)
        if response.status_code == 200:
            scenarios = response.json().get("scenarios", [])
    except Exception:
        # Fallback if backend is not started yet or offline
        scenarios = [
            {"id": "ai-healthcare", "name": "AI Healthcare Scheduling", "icon": "🏥", "description": "AI-powered appointment scheduling platform"},
            {"id": "fintech", "name": "FinTech Micro-Lending", "icon": "💳", "description": "Blockchain-based micro-lending platform for small businesses"},
            {"id": "edtech", "name": "AI Tutoring Platform", "icon": "📚", "description": "AI tutor for personalized K-12 education"},
            {"id": "saas", "name": "No-Code Workflow Automation", "icon": "⚙️", "description": "No-code workflow automation for enterprises"},
            {"id": "ecommerce", "name": "AI Visual Product Search", "icon": "🛒", "description": "AI-powered visual product search engine for e-commerce"}
        ]
        
    for s in scenarios:
        # Create a container with custom styling for each demo
        with st.container():
            st.markdown(f"""
            <div style="margin-top: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 12px;">
                <span style="font-size: 1.25rem;">{s['icon']}</span>
                <strong style="color: #f8fafc; font-size: 1.05rem; margin-left: 8px;">{s['name']}</strong>
                <p style="font-size: 0.85rem; color: #94a3b8; margin: 4px 0 8px 30px;">{s['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Button to load demo
            button_key = f"demo_btn_{s['id']}"
            if st.button(f"Load {s['name']} Demo", key=button_key):
                with st.spinner("Loading cached demo analysis..."):
                    # Call run demo endpoint
                    demo_key = s["id"]
                    # Map frontend id if it doesn't match backend keys
                    if demo_key.startswith("demo-"):
                        demo_key = demo_key.replace("demo-", "")
                    # Direct lookup mapping
                    key_map = {
                        "demo-healthcare": "ai-healthcare",
                        "healthcare": "ai-healthcare",
                        "ai-healthcare": "ai-healthcare",
                        "fintech": "fintech",
                        "edtech": "edtech",
                        "saas": "saas",
                        "ecommerce": "ecommerce"
                    }
                    scenario_arg = key_map.get(demo_key, demo_key)
                    
                    try:
                        res = requests.post(f"{backend_url}/demo/run/{scenario_arg}", timeout=10)
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.current_project_id = data["project_id"]
                            st.session_state.current_status = data["status"]
                            st.session_state.current_startup_idea = s["description"]
                            
                            st.success(f"Successfully loaded '{s['name']}' demo scenario!")
                            time_delay = st.empty()
                            st.switch_page("pages/2_🚀_Analysis.py")
                        else:
                            st.error(f"Error loading demo: {res.text}")
                    except Exception as e:
                        # Fallback for standalone frontend demonstration
                        st.warning("Backend API offline. Simulating local demo state...")
                        st.session_state.current_project_id = f"demo-{scenario_arg}"
                        st.session_state.current_status = "completed"
                        st.session_state.current_startup_idea = s["description"]
                        st.switch_page("pages/2_🚀_Analysis.py")

st.markdown("---")

# Architectural Showcase (StateGraph)
st.markdown("### 🔄 Orchestration Flow (10-Node StateGraph)")
st.markdown(
    "Unlike basic linear pipelines, StartupPilot AI uses **LangGraph** to manage state, "
    "loops, and a human approval gateway. Here is the visual flow of the system:"
)

# Render Mermaid diagram via Streamlit markdown (with mermaid html wrapper or code block)
st.markdown("""
```mermaid
graph TD
    START([START]) --> R["1. Research Node"]
    R --> MA["2. Market Analysis"]
    MA --> CA["3. Competitor Analysis"]
    CA --> SW["4. SWOT Analysis"]
    SW --> BS["5. Business Strategy"]
    BS --> HA{"6. Human Approval"}
    HA -->|Approve| AG["7. AutoGen Debate"]
    HA -->|Modify| BS
    HA -->|Reject| END2([END: Rejected])
    AG --> ARCH["8. Architecture & Cost"]
    ARCH --> RPT["9. Report Generation"]
    RPT --> MEM["10. Memory Storage"]
    MEM --> END([END: Complete])
    
    style START fill:#0b0d11,stroke:#7f5af0,stroke-width:2px;
    style HA fill:#1f1b3d,stroke:#7f5af0,stroke-width:2px;
    style END fill:#0b0d11,stroke:#2cb67d,stroke-width:2px;
    style END2 fill:#0b0d11,stroke:#cf6679,stroke-width:2px;
```
""", unsafe_allow_html=True)
