"""
StartupPilot AI — Agent Tools

Custom tools for CrewAI agents: RAG search and web search.
Each tool is a LangChain-compatible tool that agents can invoke.

LangChain components: Tool, BaseTool
"""

from __future__ import annotations

import logging
from typing import Optional

from langchain_core.tools import Tool

logger = logging.getLogger(__name__)


def get_search_tool() -> Optional[Tool]:
    """Create a web search tool using DuckDuckGo.

    Returns None if the search library is not available.
    """
    try:
        from duckduckgo_search import DDGS

        def search_web(query: str) -> str:
            """Search the web for information about a topic."""
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=5))

                if not results:
                    return "No search results found."

                formatted = []
                for r in results:
                    formatted.append(
                        f"**{r.get('title', 'N/A')}**\n"
                        f"{r.get('body', 'No description')}\n"
                        f"Source: {r.get('href', 'N/A')}"
                    )

                return "\n\n---\n\n".join(formatted)

            except Exception as e:
                logger.warning("Web search failed: %s", e)
                return f"Search failed: {str(e)}"

        return Tool(
            name="web_search",
            description=(
                "Search the web for current information about industries, "
                "companies, markets, technologies, and trends. "
                "Use this when you need up-to-date data or want to verify facts."
            ),
            func=search_web,
        )

    except ImportError:
        logger.warning("duckduckgo-search not installed. Web search tool unavailable.")
        return None


def get_rag_tool(project_id: Optional[str] = None) -> Optional[Tool]:
    """Create a RAG search tool that queries the project's vector store.

    Args:
        project_id: The project ID to scope RAG searches.

    Returns:
        A Tool instance, or None if no project_id provided.
    """
    if not project_id:
        return None

    def search_documents(query: str) -> str:
        """Search uploaded documents for relevant information."""
        try:
            from rag.retrieval import retrieve_context

            context = retrieve_context(
                query=query,
                project_id=project_id,
                top_k=3,
            )

            if not context:
                return "No relevant documents found in the project's knowledge base."

            return context

        except Exception as e:
            logger.warning("RAG search failed: %s", e)
            return f"Document search failed: {str(e)}"

    return Tool(
        name="document_search",
        description=(
            "Search through uploaded documents (PDFs, DOCX, TXT files) "
            "for relevant information. Use this when you need specific data "
            "from the user's uploaded research reports and documents."
        ),
        func=search_documents,
    )
