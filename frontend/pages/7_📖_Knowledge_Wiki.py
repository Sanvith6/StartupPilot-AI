"""
StartupPilot AI — Knowledge Wiki Explorer Page

Interactive interface for browsing, searching, and navigating the compiled Knowledge Wiki.
Allows recruiters and users to view structured topics, named entities, and cross-references.
"""

from __future__ import annotations

import streamlit as st
import requests
from pathlib import Path
from datetime import datetime

from app import apply_custom_css

# Apply global premium styling
apply_custom_css()

# Ensure demo wiki is compiled and ready
try:
    from demo.scenarios import ensure_demo_wiki
    ensure_demo_wiki("demo-healthcare")
except Exception:
    pass

# Header
st.markdown("## 📖 Knowledge Wiki Explorer")
st.markdown(
    "Explore the **compiled knowledge base** generated dynamically by the **Knowledge Compiler Agent**. "
    "Unlike raw document chunks, the Wiki organizes insights into structured **Topics** and **Entities** "
    "connected via cross-references."
)

backend_url = st.session_state.backend_url
active_pid = st.session_state.current_project_id

# ── Project Discovery ─────────────────────────────────────────────────────────

# Scan data/wiki directory for available compiled wikis
from config import get_settings
try:
    settings = get_settings()
    wiki_root = Path(settings.wiki_dir)
except Exception:
    wiki_root = Path("data/wiki")

available_projects = ["demo-healthcare"]
if wiki_root.exists():
    for p in wiki_root.iterdir():
        if p.is_dir() and (p / "wiki.json").exists() and p.name not in available_projects:
            available_projects.append(p.name)

# ── Sidebar Configuration ─────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🗂️ Select Workspace Wiki")
    
    # Pre-select active project if it has a wiki, else default to demo
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
        <strong>Living Wiki Architecture:</strong><br/>
        "Rather than feeding raw top-K chunks directly to the agents (which creates flat, noisy contexts), 
        I built a <strong>Knowledge Compiler Agent</strong>. It reads raw uploads and prior agent outputs, 
        extracts semantic topics and named entities, resolves links, and builds a relational Wiki. 
        Downstream agents browse this wiki using context templates to get highly relevant, curated facts."
    </div>
    """, unsafe_allow_html=True)

# ── Fetch Wiki Data ───────────────────────────────────────────────────────────

def get_wiki_data(project_id: str) -> dict:
    """Fetch wiki data from API, falling back to direct filesystem read if offline."""
    try:
        res = requests.get(f"{backend_url}/wiki/{project_id}/pages", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
        
    # Offline filesystem fallback (essential for robust local portfolio display)
    try:
        from knowledge_wiki.compiler import KnowledgeCompiler
        compiler = KnowledgeCompiler()
        wiki = compiler.get_wiki(project_id)
        if wiki:
            topic_pages = []
            for p in wiki.topic_pages.values():
                topic_pages.append({
                    "page_id": p.page_id,
                    "page_type": "topic",
                    "title": p.title,
                    "category_or_type": p.category.value,
                    "summary": p.summary,
                    "content": p.content,
                    "key_facts": p.key_facts,
                    "related_pages": p.related_entities + p.related_topics,
                    "source_type": p.source_type.value,
                    "version": p.version,
                    "confidence": p.confidence,
                })
            entity_pages = []
            for p in wiki.entity_pages.values():
                entity_pages.append({
                    "page_id": p.page_id,
                    "page_type": "entity",
                    "title": p.name,
                    "category_or_type": p.entity_type.value,
                    "summary": p.summary,
                    "attributes": p.attributes,
                    "related_pages": p.related_entities + p.related_topics,
                    "source_type": p.source_type.value,
                    "version": p.version,
                    "confidence": p.confidence,
                })
            return {
                "project_id": project_id,
                "topic_pages": topic_pages,
                "entity_pages": entity_pages,
                "stats": wiki.get_stats()
            }
    except Exception:
        pass
    return {}

with st.spinner("Loading Knowledge Wiki..."):
    wiki_data = get_wiki_data(selected_project)

if not wiki_data or (not wiki_data.get("topic_pages") and not wiki_data.get("entity_pages")):
    st.info("ℹ️ No structured knowledge compiled for this project yet. Try uploading files first or run an analysis scenario.")
    st.stop()

topic_pages = wiki_data.get("topic_pages", [])
entity_pages = wiki_data.get("entity_pages", [])
stats = wiki_data.get("stats", {})

# Build index for fast lookup
all_pages = topic_pages + entity_pages
pages_by_id = {p["page_id"]: p for p in all_pages}

# ── Initialize State ──────────────────────────────────────────────────────────

if "selected_page_id" not in st.session_state or st.session_state.get("selected_page_project") != selected_project:
    # Set default page to the first topic page
    if topic_pages:
        st.session_state.selected_page_id = topic_pages[0]["page_id"]
    elif entity_pages:
        st.session_state.selected_page_id = entity_pages[0]["page_id"]
    st.session_state.selected_page_project = selected_project

# ── Render Stats row ──────────────────────────────────────────────────────────

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
with col_s1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Topic Pages</div>
        <div class="metric-value">{stats.get("total_topic_pages", 0)}</div>
    </div>
    """, unsafe_allow_html=True)
with col_s2:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #2cb67d;">
        <div class="metric-title">Entity Pages</div>
        <div class="metric-value">{stats.get("total_entity_pages", 0)}</div>
    </div>
    """, unsafe_allow_html=True)
with col_s3:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #bf5af2;">
        <div class="metric-title">Cross-References</div>
        <div class="metric-value">{stats.get("total_cross_references", 0) // 2}</div>
    </div>
    """, unsafe_allow_html=True)
with col_s4:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #ff9f43;">
        <div class="metric-title">Incremental Commits</div>
        <div class="metric-value">{stats.get("compilation_count", 0)}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ── Main Content Columns ──────────────────────────────────────────────────────

col_nav, col_viewer = st.columns([1, 2], gap="large")

# Icon mappings
category_icons = {
    "market": "📈",
    "technology": "⚙️",
    "regulation": "⚖️",
    "industry": "🏢",
    "strategy": "⚡",
    "financial": "💰",
    "general": "📁"
}

entity_icons = {
    "company": "🏢",
    "person": "👤",
    "product": "📦",
    "technology": "⚙️",
    "regulation": "⚖️",
    "organization": "👥"
}

with col_nav:
    st.markdown("### 🔍 Search & Browse")
    
    # 1. Search input
    search_query = st.text_input(
        "Search Wiki:",
        placeholder="Type keyword, entity, or topic...",
        help="Filters the page lists below in real-time."
    ).strip().lower()
    
    # Filter function
    def matches_search(page: dict) -> bool:
        if not search_query:
            return True
        title = page["title"].lower()
        summary = page["summary"].lower()
        content = page.get("content", "").lower()
        return search_query in title or search_query in summary or search_query in content

    filtered_topics = [t for t in topic_pages if matches_search(t)]
    filtered_entities = [e for e in entity_pages if matches_search(e)]

    # 2. Browse Topics
    st.markdown("#### 📂 Topics")
    if filtered_topics:
        # Group topics by category
        categories = sorted(list(set(t["category_or_type"] for t in filtered_topics)))
        for cat in categories:
            cat_topics = [t for t in filtered_topics if t["category_or_type"] == cat]
            icon = category_icons.get(cat, "📁")
            
            with st.expander(f"{icon} {cat.capitalize()} ({len(cat_topics)})", expanded=True):
                for t in cat_topics:
                    is_selected = t["page_id"] == st.session_state.selected_page_id
                    btn_type = "primary" if is_selected else "secondary"
                    # Styled button
                    if st.button(
                        f"📄 {t['title']}", 
                        key=f"nav_t_{t['page_id']}",
                        use_container_width=True
                    ):
                        st.session_state.selected_page_id = t["page_id"]
                        st.rerun()
    else:
        st.caption("No topics match your search.")

    # 3. Browse Entities
    st.markdown("#### 🏢 Entities")
    if filtered_entities:
        types = sorted(list(set(e["category_or_type"] for e in filtered_entities)))
        for etype in types:
            etype_entities = [e for e in filtered_entities if e["category_or_type"] == etype]
            icon = entity_icons.get(etype, "👤")
            
            with st.expander(f"{icon} {etype.capitalize()} ({len(etype_entities)})", expanded=True):
                for e in etype_entities:
                    is_selected = e["page_id"] == st.session_state.selected_page_id
                    if st.button(
                        f"🔹 {e['title']}", 
                        key=f"nav_e_{e['page_id']}",
                        use_container_width=True
                    ):
                        st.session_state.selected_page_id = e["page_id"]
                        st.rerun()
    else:
        st.caption("No entities match your search.")

# ── Reader View Column ────────────────────────────────────────────────────────

with col_viewer:
    page_id = st.session_state.selected_page_id
    page = pages_by_id.get(page_id)
    
    if not page:
        # Fallback to first page if current is missing
        if all_pages:
            page = all_pages[0]
            st.session_state.selected_page_id = page["page_id"]
        else:
            st.info("Select a page on the left to start reading.")
            st.stop()
            
    # Page Header
    is_topic = page.get("page_type") == "topic"
    icon = category_icons.get(page["category_or_type"], "📄") if is_topic else entity_icons.get(page["category_or_type"], "🔹")
    
    st.markdown(f"### {icon} {page['title']}")
    
    # Badges bar
    badges_html = f"""
    <div style="margin-bottom: 20px;">
        <span class="glow-badge" style="margin-right: 8px;">{page['category_or_type'].upper()}</span>
        <span class="glow-badge-teal" style="margin-right: 8px;">CONFIDENCE: {int(page['confidence'] * 100)}%</span>
        <span style="font-size: 0.85rem; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.05);">
            Source: {page['source_type'].upper()} (v{page['version']})
        </span>
    </div>
    """
    st.markdown(badges_html, unsafe_allow_html=True)
    
    # Summary Callout
    st.info(page["summary"])
    
    # Topic specific content
    if is_topic:
        st.markdown(page.get("content", ""))
        
        if page.get("key_facts"):
            st.markdown("#### 📌 Key Facts & Claims")
            for fact in page["key_facts"]:
                st.markdown(f"- {fact}")
                
    # Entity specific content
    else:
        # Attributes grid
        attrs = page.get("attributes", {})
        if attrs:
            st.markdown("#### 📊 Entity Attributes")
            # Build nice grid layout for attributes
            cols = st.columns(2)
            for idx, (k, v) in enumerate(attrs.items()):
                with cols[idx % 2]:
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 10px 15px; margin-bottom: 10px;">
                        <span style="font-size: 0.75rem; text-transform: uppercase; color: #94a3b8; display: block; margin-bottom: 2px;">{k.replace('_', ' ')}</span>
                        <span style="font-weight: 600; color: #e2e8f0;">{v}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
        # Mentions & Snippets
        mentions = page.get("mentions", [])
        if mentions:
            st.markdown("#### 💬 Source Mentions")
            for m in mentions:
                snippet = m.get("context_snippet", "")
                src = m.get("source", "unknown")
                st.markdown(f"""
                <blockquote style="margin: 10px 0; padding-left: 15px; border-left: 3px solid #7f5af0; color: #cbd5e1; font-style: italic;">
                    "{snippet}"
                    <cite style="display: block; font-size: 0.8rem; color: #64748b; margin-top: 5px; font-style: normal;">
                        — Found in: {src.upper()}
                    </cite>
                </blockquote>
                """, unsafe_allow_html=True)
                
    # ── Related Pages (Cross-References) ──────────────────────────────────────
    
    st.markdown("---")
    st.markdown("#### 🔗 Related Knowledge Pages")
    
    related_ids = page.get("related_pages", [])
    if related_ids:
        # Deduplicate and filter out missing pages
        valid_related = [rid for rid in set(related_ids) if rid in pages_by_id and rid != page["page_id"]]
        
        if valid_related:
            cols = st.columns(min(len(valid_related), 3))
            for i, rid in enumerate(valid_related):
                rpage = pages_by_id[rid]
                is_r_topic = rpage.get("page_type") == "topic"
                ricon = category_icons.get(rpage["category_or_type"], "📄") if is_r_topic else entity_icons.get(rpage["category_or_type"], "🔹")
                
                with cols[i % 3]:
                    # Draw clickable navigation buttons
                    if st.button(
                        f"{ricon} {rpage['title']}", 
                        key=f"rel_nav_{page['page_id']}_{rid}",
                        use_container_width=True
                    ):
                        st.session_state.selected_page_id = rid
                        st.rerun()
        else:
            st.caption("No related pages linked to this page yet.")
    else:
        st.caption("No related pages linked to this page yet.")
