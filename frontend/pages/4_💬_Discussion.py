"""
StartupPilot AI — AutoGen Discussion Page

Parses the AutoGen multi-agent debate transcript and renders it
as an interactive, premium chat conversation using Streamlit chat components.
"""

from __future__ import annotations

import streamlit as st
import requests
import re

from app import apply_custom_css

# Apply styling
apply_custom_css()

# Header
st.markdown("## 💬 AutoGen Multi-Agent Debate")
st.markdown(
    "After the business strategy is approved, a group of 3 AutoGen agents (Business Consultant, "
    "Cloud Architect, and Financial Analyst) hold an autonomous debate to stress-test viability "
    "and align technology requirements. Read the chat log below."
)

backend_url = st.session_state.backend_url
active_pid = st.session_state.current_project_id

# Speaker settings for avatars and colors
SPEAKER_CONFIG = {
    "Discussion_Moderator": {"name": "Discussion Moderator", "avatar": "🤖"},
    "Business_Consultant": {"name": "Senior Business Consultant", "avatar": "💡"},
    "Cloud_Architect": {"name": "Principal Cloud Architect", "avatar": "🏗️"},
    "Financial_Analyst": {"name": "Cloud Financial Analyst", "avatar": "💰"},
    "Consensus": {"name": "Consensus & Next Steps", "avatar": "🤝"},
    "System": {"name": "Workflow System", "avatar": "⚙️"}
}


def parse_transcript(transcript_text: str) -> list[dict]:
    """Parse the raw debate transcript into structured messages."""
    if not transcript_text:
        return []
        
    # Split by the markdown horizontal rule separators used in transcripts
    parts = re.split(r'\n*(?:---)\n*', transcript_text)
    messages = []
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        # Match "**SpeakerName**: Content" pattern
        match = re.match(r'^\*\*([A-Za-z0-9_]+)\*\*:\s*(.*)$', part, re.DOTALL)
        if match:
            speaker = match.group(1)
            content = match.group(2).strip()
            messages.append({"speaker": speaker, "content": content})
        else:
            # Check if it starts with **Consensus** without colon
            if part.startswith("**Consensus**"):
                match_consensus = re.match(r'^\*\*(Consensus)\*\*:\?\s*(.*)$', part, re.DOTALL)
                # Just general fallback
                content = part.replace("**Consensus**:", "").replace("**Consensus**", "").strip()
                messages.append({"speaker": "Consensus", "content": content})
            else:
                messages.append({"speaker": "System", "content": part})
                
    return messages


# ── Main Content Area ─────────────────────────────────────────────────────────

if not active_pid:
    st.info("👈 Load a demo scenario from the Home page or submit a startup idea in the Analysis tab to view the agent debate transcript.")
else:
    # Fetch report JSON which contains the discussion transcript
    transcript = ""
    try:
        res = requests.get(f"{backend_url}/report/{active_pid}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            transcript = data.get("discussion_transcript", "")
        else:
            st.error(f"Failed to fetch discussion: {res.text}")
    except Exception:
        # Simulation mode fallback
        if active_pid.startswith("demo-") or active_pid.startswith("local-"):
            transcript = (
                "**Discussion_Moderator**: Let's evaluate: 'AI-powered healthcare appointment scheduling platform'\n\n---\n\n"
                "**Business_Consultant**: This is a strong opportunity. The healthcare scheduling market "
                "is fragmented with no dominant AI-first player in the mid-market. The $85M SOM is "
                "achievable with focused execution. Key risk: long sales cycles. Recommendation: start "
                "with dental/vision chains (shorter sales cycles) then expand to medical practices. "
                "Overall viability: 8/10.\n\n---\n\n"
                "**Cloud_Architect**: Technically feasible with modern cloud architecture. "
                "I recommend starting with AWS ECS Fargate for the API layer, RDS PostgreSQL for data, "
                "and SageMaker for ML models. HIPAA compliance requires dedicated infrastructure — "
                "expect $3,000-5,000/month baseline. The main technical risk is EHR integration "
                "complexity — each EHR system has different APIs. Suggest partnering with an integration "
                "platform like Redox or Health Gorilla.\n\n---\n\n"
                "**Financial_Analyst**: Unit economics look favorable. At $349/provider/month with "
                "50 providers, MRR = $17,450. Infrastructure costs of $5,000/month means 71% gross "
                "margin. Break-even at approximately 15 providers (assuming 2 FTEs). First-year "
                "infrastructure: $60,000-80,000. Recommend raising a $500K pre-seed to fund 12 months "
                "of runway. Cost optimization: use reserved instances and spot for ML training.\n\n---\n\n"
                "**Business_Consultant**: Agreed on unit economics. I'd add: focus on proving 30% "
                "no-show reduction in pilots — that's the ROI story that sells. Each no-show costs "
                "a practice $200 on average. For a 10-provider clinic with 5% no-show rate, that's "
                "$100K/year in lost revenue. Our solution paying for itself 2-3x over.\n\n---\n\n"
                "**Consensus**: Viability 8/10. Strengths: clear ROI, growing market, feasible tech. "
                "Risks: sales cycle length, EHR integration. Next steps: build MVP, sign 3-5 pilots, "
                "prove no-show reduction metric."
            )
        else:
            st.error("Could not connect to backend server.")
            st.stop()

    if not transcript:
        st.warning("⏳ The AutoGen debate runs *after* business strategy approval. Please complete the approval step in the Analysis tab.")
    else:
        parsed_msgs = parse_transcript(transcript)
        
        # Render the messages in chat style
        st.markdown("### 💬 Chat Log")
        
        for msg in parsed_msgs:
            speaker_key = msg["speaker"]
            content = msg["content"]
            
            # Get speaker configuration
            config = SPEAKER_CONFIG.get(speaker_key, {"name": speaker_key, "avatar": "💬"})
            
            # Display using Streamlit chat message component
            with st.chat_message(name=speaker_key, avatar=config["avatar"]):
                # Render speaker display name
                st.markdown(f"**{config['name']}**")
                st.write(content)
                
        # Key takeaways box
        st.markdown("---")
        st.markdown("""
        <div class="premium-card" style="border-left: 4px solid #ffb900; background: rgba(255, 185, 0, 0.03);">
            <strong>💡 Interview Insight:</strong><br/>
            This debate showcases <strong>AutoGen</strong> GroupChat capabilities where agents with divergent interests 
            (Tech, Finance, Strategy) challenge each other to align on system requirements and financial feasibility.
        </div>
        """, unsafe_allow_html=True)
