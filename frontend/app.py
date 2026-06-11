"""
StartupPilot AI — Frontend Entrypoint

Configures the Streamlit page, applies the master premium dark theme CSS,
initializes the session state variables, and redirects to the Home page.
"""

from __future__ import annotations

import streamlit as st

# Configure the Streamlit page layout and title
st.set_page_config(
    page_title="StartupPilot AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)


def apply_custom_css():
    """Apply premium dark-mode, glassmorphism, and responsive styling to the Streamlit app.
    
    Includes Google Fonts, gradient buttons, custom cards, and hover micro-animations.
    """
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Outfit:wght@400;600;700;800&display=swap');
        
        /* Apply fonts globally */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #e2e8f0;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }
        
        /* Master background */
        .stApp {
            background-color: #0b0d11;
            background-image: 
                radial-gradient(at 0% 0%, rgba(127, 90, 240, 0.04) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(44, 182, 125, 0.03) 0px, transparent 50%);
            background-attachment: fixed;
        }
        
        /* Premium Sidebar */
        [data-testid="stSidebar"] {
            background-color: #0f1219;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* Glassmorphic cards */
        .premium-card {
            background: rgba(22, 25, 32, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .premium-card:hover {
            border-color: rgba(127, 90, 240, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 12px 40px 0 rgba(127, 90, 240, 0.1);
        }
        
        /* Glowing badges */
        .glow-badge {
            background: linear-gradient(135deg, rgba(127, 90, 240, 0.15) 0%, rgba(79, 70, 229, 0.15) 100%);
            border: 1px solid rgba(127, 90, 240, 0.4);
            color: #bf5af2;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
            box-shadow: 0 0 15px rgba(127, 90, 240, 0.1);
        }
        
        .glow-badge-teal {
            background: linear-gradient(135deg, rgba(44, 182, 125, 0.15) 0%, rgba(20, 110, 80, 0.15) 100%);
            border: 1px solid rgba(44, 182, 125, 0.4);
            color: #2cb67d;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
            box-shadow: 0 0 15px rgba(44, 182, 125, 0.1);
        }
        
        /* Gradient buttons */
        .stButton > button {
            background: linear-gradient(135deg, #7f5af0 0%, #4f46e5 100%);
            color: #ffffff !important;
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            font-weight: 600;
            font-size: 1rem;
            box-shadow: 0 4px 14px rgba(127, 90, 240, 0.3);
            transition: all 0.25s ease;
            width: 100%;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(127, 90, 240, 0.5);
            background: linear-gradient(135deg, #8c67ff 0%, #5d54ff 100%);
        }
        
        .stButton > button:active {
            transform: translateY(1px);
        }
        
        /* Text input customization */
        .stTextInput input, .stTextArea textarea {
            background-color: #12161f !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            color: #f1f5f9 !important;
            transition: border-color 0.2s ease;
        }
        
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #7f5af0 !important;
            box-shadow: 0 0 0 2px rgba(127, 90, 240, 0.2) !important;
        }
        
        /* Metric dashboard style */
        .metric-card {
            background: #141722;
            border-left: 4px solid #7f5af0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
        }
        
        .metric-title {
            font-size: 0.85rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }
        
        .metric-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #f8fafc;
        }
        
        /* Highlight boxes */
        .highlight-box {
            background: rgba(127, 90, 240, 0.05);
            border: 1px solid rgba(127, 90, 240, 0.15);
            border-radius: 12px;
            padding: 18px;
            margin-top: 15px;
        }
        
    </style>
    """, unsafe_allow_html=True)


def init_session_state():
    """Initialize global session state variables if they do not exist."""
    if "backend_url" not in st.session_state:
        # Default local backend URL
        st.session_state.backend_url = "http://localhost:8000"
        
    if "current_project_id" not in st.session_state:
        st.session_state.current_project_id = None
        
    if "current_startup_idea" not in st.session_state:
        st.session_state.current_startup_idea = None
        
    if "current_status" not in st.session_state:
        st.session_state.current_status = None


if __name__ == "__main__":
    # Run initialization
    init_session_state()
    apply_custom_css()

    # Redirect to the Home page
    try:
        st.switch_page("pages/1_🏠_Home.py")
    except Exception as e:
        # Safe fallback if switch_page fails (e.g. running for the first time before file write)
        st.info("Directing you to StartupPilot AI Home... Please wait.")
        st.markdown("### 🚀 Welcome to StartupPilot AI")
        st.markdown("Use the sidebar navigation to visit the **Home** page.")
