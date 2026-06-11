"""
StartupPilot AI — Reports Page

Enables users to read the compiled markdown report, render the diagrams,
and download the final deliverable in Markdown, HTML, and PDF formats.
"""

from __future__ import annotations

import streamlit as st
import requests

from app import apply_custom_css

# Apply styling
apply_custom_css()

# Header
st.markdown("## 📄 Startup intelligence Reports")
st.markdown(
    "Review and download the final, investor-ready startup reports and cloud architecture "
    "recommendations. You can download the reports in multiple professional formats."
)

backend_url = st.session_state.backend_url
active_pid = st.session_state.current_project_id

# ── Main Content Area ─────────────────────────────────────────────────────────

if not active_pid:
    st.info("👈 Load a demo scenario from the Home page or submit a startup idea in the Analysis tab to view and download reports.")
else:
    report_data = {}
    
    # Fetch report from backend
    try:
        res = requests.get(f"{backend_url}/report/{active_pid}", timeout=5)
        if res.status_code == 200:
            report_data = res.json()
        elif res.status_code == 400:
            st.warning("⏳ The final report is compiled at the very end of the workflow. Please approve the strategy step on the Analysis page first.")
            st.stop()
        else:
            st.error(f"Failed to fetch report: {res.text}")
            st.stop()
    except Exception:
        # Simulation fallback for offline demo
        if active_pid.startswith("demo-") or active_pid.startswith("local-"):
            # Load simulated report from demo
            from demo.scenarios import get_demo_result
            demo = get_demo_result(active_pid)
            if demo:
                # We can generate report locally if we need to, but let's check
                from reports.generator import generate_report
                report_md = generate_report(demo)
                report_data = {
                    "project_id": active_pid,
                    "startup_idea": demo.get("startup_idea"),
                    "report": report_md,
                    "diagrams": {}
                }
            else:
                st.error("Could not load simulation report.")
                st.stop()
        else:
            st.error("Could not connect to the backend server.")
            st.stop()

    report_md = report_data.get("report", "")
    diagrams = report_data.get("diagrams", {})

    # ── Sidebar Downloads ─────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 📥 Download Deliverable")
        st.markdown("Generate and download the report in your preferred layout:")
        
        # Download buttons fetching directly from backend or local fallback
        
        # 1. PDF Download
        pdf_ready = False
        pdf_bytes = b""
        try:
            res_pdf = requests.get(f"{backend_url}/report/{active_pid}?format=pdf", timeout=10)
            if res_pdf.status_code == 200:
                pdf_bytes = res_pdf.content
                pdf_ready = True
        except Exception:
            # Local fallback generation
            try:
                from reports.generator import save_report_as_pdf
                pdf_path = save_report_as_pdf(active_pid, report_md)
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                pdf_ready = True
            except Exception:
                pass
                
        if pdf_ready:
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"startuppilot_report_{active_pid}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("PDF generator unavailable")
            
        # 2. HTML Download
        html_ready = False
        html_bytes = b""
        try:
            res_html = requests.get(f"{backend_url}/report/{active_pid}?format=html", timeout=10)
            if res_html.status_code == 200:
                html_bytes = res_html.content
                html_ready = True
        except Exception:
            # Local fallback generation
            try:
                from reports.generator import save_report_as_html
                html_path = save_report_as_html(active_pid, report_md)
                with open(html_path, "rb") as f:
                    html_bytes = f.read()
                html_ready = True
            except Exception:
                pass
                
        if html_ready:
            st.download_button(
                label="🌐 Download HTML Report",
                data=html_bytes,
                file_name=f"startuppilot_report_{active_pid}.html",
                mime="text/html"
            )
            
        # 3. Markdown Download
        st.download_button(
            label="📝 Download Markdown",
            data=report_md,
            file_name=f"startuppilot_report_{active_pid}.md",
            mime="text/markdown"
        )

    # ── Main report tabs ──────────────────────────────────────────────────────
    tab_report, tab_architecture = st.tabs(["📄 Completed Report", "🏗️ Cloud Architecture Diagram"])
    
    with tab_report:
        st.markdown("### Final Report Summary")
        st.markdown(report_md)
        
    with tab_architecture:
        st.markdown("### Cloud Architecture Recommendation")
        
        # Display the architecture Mermaid diagram if generated
        arch_diagram = diagrams.get("architecture")
        if not arch_diagram:
            # Fallback/default architecture diagram if not in report_data
            arch_diagram = """
graph TD
    User([User]) --> Route53[AWS Route 53]
    Route53 --> CF[Amazon CloudFront]
    CF --> S3[Amazon S3 Static Bucket]
    CF --> ALB[Application Load Balancer]
    ALB --> ECS[AWS ECS Fargate API]
    ECS --> RDS[(Amazon RDS PostgreSQL)]
    ECS --> ElastiCache[(Amazon ElastiCache Redis)]
    ECS --> SageMaker[AWS SageMaker ML Platform]
    ECS --> OpenAI[OpenAI API Gateway]
    
    style User fill:#0d0f12,stroke:#7f5af0,stroke-width:2px;
    style ECS fill:#1b2a47,stroke:#2cb67d,stroke-width:2px;
    style RDS fill:#162521,stroke:#cf6679,stroke-width:2px;
            """
            
        st.markdown(f"```mermaid\n{arch_diagram}\n```", unsafe_allow_html=True)
        st.markdown(
            "This diagram represents the recommended secure, multi-stage cloud architecture "
            "designed by the Cloud Architect agent based on your startup idea."
        )
