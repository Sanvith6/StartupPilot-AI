"""
StartupPilot AI — RAG Retrieval (Wiki-Enhanced)

Context retrieval that uses the Knowledge Wiki as the PRIMARY source
and falls back to raw ChromaDB chunks only when no wiki exists.

Pipeline:
    1. Check if a compiled wiki exists for this project
    2. If yes → use ContextAssembler to build agent-specific context
    3. If no  → fall back to raw top-K chunk retrieval from ChromaDB

LangChain component: Retrieval chain integration

Interview talking point:
    "My retrieval layer is wiki-first. Instead of raw chunks, agents get
     structured topic pages and entity pages with cross-references.
     Raw chunks are only used as a fallback when no wiki is compiled."
"""

from __future__ import annotations

import logging
from typing import Optional

from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Module-level singletons (lazy initialized)
_vector_store: Optional[VectorStore] = None


def get_store() -> VectorStore:
    """Get or create the singleton VectorStore instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def retrieve_context(
    query: str,
    project_id: str,
    top_k: int = 5,
    agent_type: Optional[str] = None,
) -> str:
    """Retrieve relevant context — wiki-first, raw chunks as fallback.

    Strategy:
    1. Try wiki-based context (structured, agent-aware)
    2. Fall back to raw ChromaDB chunks if no wiki exists

    Args:
        query: The search query (e.g., "AI healthcare market size").
        project_id: The project ID to search within.
        top_k: Number of results for raw chunk fallback.
        agent_type: The agent requesting context (for wiki assembly).

    Returns:
        Formatted context string with source attribution.
        Returns empty string if no relevant documents found.
    """
    # ── Strategy 1: Wiki-based context (primary) ──────────────────────────
    wiki_context = _try_wiki_context(project_id, query, agent_type)
    if wiki_context:
        logger.info(
            "Wiki context retrieved for project %s (%d chars)",
            project_id,
            len(wiki_context),
        )
        return wiki_context

    # ── Strategy 2: Raw chunk retrieval (fallback) ────────────────────────
    return _raw_chunk_retrieval(query, project_id, top_k)


def _try_wiki_context(
    project_id: str,
    query: str,
    agent_type: Optional[str] = None,
) -> str:
    """Try to assemble context from the Knowledge Wiki.

    Checks if a research trace exists for this agent first.
    If yes → uses research trace evidence and reasoning.
    If no  → falls back to normal flat ContextAssembler.
    """
    if project_id and agent_type:
        try:
            from workflows.graph_runner import get_analysis_state
            state = get_analysis_state(project_id)
            if state and state.get("research_traces") and agent_type in state["research_traces"]:
                trace = state["research_traces"][agent_type]
                evidence_items = trace.get("evidence_gathered", [])
                path = trace.get("navigation_path", [])
                reasons = trace.get("reasoning_chain", [])
                
                if evidence_items or path:
                    parts = []
                    parts.append("### 🔬 AGENTIC MULTI-HOP RESEARCH TRACE")
                    if path:
                        parts.append(f"**Navigation Path:** {' → '.join(path)}")
                    
                    if reasons:
                        parts.append("\n**Reasoning Steps:**")
                        for r in reasons:
                            parts.append(f"- {r}")
                    
                    if evidence_items:
                        parts.append("\n**Collected Evidence & Facts:**")
                        for item in evidence_items:
                            parts.append(f"- [{item.get('title_or_name')}]: {item.get('fact')} *(Reasoning: {item.get('relevance_reasoning')})*")
                    else:
                        parts.append("\n*(No direct evidence claims extracted from these pages)*")
                    
                    return "\n".join(parts)
        except Exception as e:
            logger.debug("Research trace check failed: %s. Continuing with flat assembly.", e)

    # Standard flat context assembler fallback
    try:
        from knowledge_wiki.compiler import KnowledgeCompiler
        from knowledge_wiki.context_assembler import ContextAssembler

        compiler = KnowledgeCompiler()
        wiki = compiler.get_wiki(project_id)

        if wiki is None:
            return ""

        assembler = ContextAssembler(wiki)

        if agent_type:
            return assembler.assemble(
                agent_type=agent_type,
                query=query,
                max_chars=4000,
            )
        else:
            return assembler.assemble_for_query(query=query, max_chars=3000)

    except Exception as e:
        logger.debug("Wiki context assembly failed: %s. Using raw chunks.", e)
        return ""


def _raw_chunk_retrieval(query: str, project_id: str, top_k: int) -> str:
    """Original raw chunk retrieval from ChromaDB (fallback)."""
    store = get_store()

    try:
        results = store.query(project_id, query, top_k=top_k)

        if not results:
            return ""

        # Format results as context
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result.get("metadata", {}).get("source_file", "unknown")
            content = result["content"]
            distance = result.get("distance", 0)

            context_parts.append(
                f"[Source {i}: {source} (relevance: {1 - distance:.2f})]\n{content}"
            )

        context = "\n\n---\n\n".join(context_parts)

        logger.info(
            "Retrieved %d raw chunks for query '%s...' in project %s",
            len(results),
            query[:50],
            project_id,
        )

        return context

    except Exception as e:
        logger.warning("RAG retrieval failed: %s. Returning empty context.", e)
        return ""


def ingest_document(
    file_path: str,
    project_id: str,
) -> int:
    """Ingest a document into the RAG pipeline.

    Full pipeline: Load → Chunk → Embed → Store in ChromaDB.
    Wiki compilation is triggered separately (by the caller).

    Args:
        file_path: Path to the document file.
        project_id: The project to associate the document with.

    Returns:
        Number of chunks stored.
    """
    from rag.loaders import load_and_chunk

    # Load and chunk the document
    chunks = load_and_chunk(file_path)

    # Store in vector store
    store = get_store()
    count = store.add_documents(project_id, chunks)

    logger.info(
        "Ingested %s → %d chunks stored for project %s",
        file_path,
        count,
        project_id,
    )

    return count


def ingest_and_compile(
    file_path: str,
    project_id: str,
    startup_idea: str = "",
) -> dict:
    """Ingest a document AND compile it into the Knowledge Wiki.

    This is the recommended entry point for document uploads.
    Performs both chunk storage and wiki compilation in one call.

    Args:
        file_path: Path to the document file.
        project_id: The project ID.
        startup_idea: The startup idea for context.

    Returns:
        Dict with {chunks_stored, wiki_stats}.
    """
    from rag.loaders import load_and_chunk
    from knowledge_wiki.compiler import KnowledgeCompiler

    # Step 1: Load and chunk
    chunks = load_and_chunk(file_path)

    # Step 2: Store in vector store
    store = get_store()
    chunks_stored = store.add_documents(project_id, chunks)

    # Step 3: Compile into wiki
    compiler = KnowledgeCompiler()
    wiki = compiler.compile_documents(
        project_id=project_id,
        chunks=chunks,
        startup_idea=startup_idea or f"Project {project_id}",
    )

    logger.info(
        "Ingested + compiled %s → %d chunks, %d topics, %d entities",
        file_path,
        chunks_stored,
        len(wiki.topic_pages),
        len(wiki.entity_pages),
    )

    return {
        "chunks_stored": chunks_stored,
        "wiki_stats": wiki.get_stats(),
    }


def get_project_stats(project_id: str) -> dict:
    """Get RAG statistics for a project (including wiki stats)."""
    store = get_store()
    stats = store.get_collection_stats(project_id)

    # Add wiki stats if available
    try:
        from knowledge_wiki.compiler import KnowledgeCompiler
        compiler = KnowledgeCompiler()
        wiki = compiler.get_wiki(project_id)
        if wiki:
            stats["wiki"] = wiki.get_stats()
    except Exception:
        pass

    return stats
