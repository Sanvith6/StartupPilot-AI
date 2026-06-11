"""
StartupPilot AI — Document Upload & RAG Page

Allows users to upload reference documents (PDF, DOCX, TXT, MD) to the vector store.
Explains the RAG architecture and its value in multi-agent intelligence systems.
"""

from __future__ import annotations

import streamlit as st
import requests

from app import apply_custom_css

# Apply styling
apply_custom_css()

# Header
st.markdown("## 📤 RAG Document Upload Center")
st.markdown(
    "Enhance the intelligence of your startup analysis by uploading proprietary reference files, "
    "market studies, financial sheets, or pitch drafts. Our RAG system parses and index them into "
    "ChromaDB for agents to reference during their tasks."
)

backend_url = st.session_state.backend_url
active_pid = st.session_state.current_project_id

# ── Sidebar details ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📚 RAG Architecture")
    st.markdown(
        "**Retrieval-Augmented Generation (RAG)** provides context-aware agent actions without fine-tuning."
    )
    st.markdown("""
    **Core Pipeline:**
    1. **Load**: PyPDF, Docx2txt, or UTF-8 Text Loaders
    2. **Chunk**: Recursive Character splitting (size=1000, overlap=200)
    3. **Embed**: Sentence Transformers `all-MiniLM-L6-v2` (384-dim, local)
    4. **Store**: Scoped ChromaDB collection
    5. **Query**: Semantic similarity search injected into CrewAI agent prompts
    """)

# ── Main Content Area ─────────────────────────────────────────────────────────

col_form, col_help = st.columns([3, 2], gap="large")

with col_form:
    st.markdown("### 📂 Upload Reference Files")
    
    # Target project ID input
    proj_id_input = st.text_input(
        "Associate with Project ID:",
        value=active_pid or f"project_{int(time_delay := 123456789)}", # Fallback placeholder
        help="Documents will be indexed under this project scope. Agents working on this project will retrieve context from these files."
    )
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose file (PDF, DOCX, TXT, MD):",
        type=["pdf", "docx", "txt", "md"],
        help="Supported file types: .pdf, .docx, .txt, .md. Max size: 200MB."
    )
    
    if st.button("🚀 Upload & Index Document"):
        if not proj_id_input.strip():
            st.error("Please specify a Project ID.")
        elif not uploaded_file:
            st.error("Please select a file to upload.")
        else:
            with st.spinner("Processing document (parsing, chunking, embedding, indexing)..."):
                # Prepare multipart request
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"project_id": proj_id_input.strip()}
                
                try:
                    res = requests.post(
                        f"{backend_url}/upload",
                        files=files,
                        data=data,
                        timeout=30
                    )
                    if res.status_code == 200:
                        res_data = res.json()
                        st.success(
                            f"🎉 Successfully indexed '{uploaded_file.name}'!\n\n"
                            f"Added **{res_data.get('chunks_added', 0)} chunks** to project vector space `{proj_id_input.strip()}`."
                        )
                        # Set active project ID if not set
                        if not active_pid:
                            st.session_state.current_project_id = proj_id_input.strip()
                            st.session_state.current_status = "pending"
                    else:
                        st.error(f"Upload failed: {res.text}")
                except Exception as e:
                    # Mock/simulation for frontend offline demo
                    st.warning("Backend API offline. Simulating indexing local mock document...")
                    mock_chunks = 14
                    st.success(
                        f"🎉 Successfully indexed '{uploaded_file.name}' (Simulated)!\n\n"
                        f"Added **{mock_chunks} chunks** to project vector space `{proj_id_input.strip()}`."
                    )
                    if not active_pid:
                        st.session_state.current_project_id = proj_id_input.strip()
                        st.session_state.current_status = "pending"

with col_help:
    st.markdown("### 💡 Why RAG matters in Interviews")
    st.markdown(
        "Retrieval-Augmented Generation is a top-3 interview topic for AI roles. "
        "Explain to your interviewer:"
    )
    
    st.markdown("""
    <div class="premium-card" style="margin-top: 15px;">
        <strong>"I implemented project-scoped RAG:</strong><br/>
        Each project has a dedicated ChromaDB collection. 
        When Research or Competitor agents start their task, they perform a semantic query 
        against the project collection, fetch the top-5 most relevant chunks, and inject them 
        directly into the LLM system prompt. This ensures my agents have access to proprietary data 
        without leaking documents between projects."
    </div>
    """, unsafe_allow_html=True)
