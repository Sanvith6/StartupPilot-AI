"""
StartupPilot AI — Conversation Memory

Manages conversation history and agent memory across analysis sessions.
Supports both in-memory storage (for development) and file-based
persistence (for cross-session memory).

LangChain components: ConversationBufferMemory
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from config import get_settings, MEMORY_DIR

logger = logging.getLogger(__name__)


class MemoryManager:
    """Three-tier memory system for agent context.

    Tiers:
    1. Short-Term: Current analysis session state (in-memory dict)
    2. Long-Term: Past analyses persisted to JSON files
    3. Project: Per-project knowledge stored in memory dir

    Interview talking point:
        "My agents have a three-tier memory system. Short-term memory holds
         the current session state. Long-term memory lets agents reference
         past startup analyses. Project memory stores per-project knowledge
         that persists across sessions."
    """

    def __init__(self, memory_dir: Optional[str] = None) -> None:
        self._memory_dir = Path(memory_dir or get_settings().memory_dir)
        self._memory_dir.mkdir(parents=True, exist_ok=True)
        self._short_term: dict[str, dict[str, Any]] = {}

        logger.info("MemoryManager initialized. Storage: %s", self._memory_dir)

    # ── Short-Term Memory (Current Session) ───────────────────────────────

    def store_short_term(self, project_id: str, key: str, value: Any) -> None:
        """Store a value in short-term (session) memory."""
        if project_id not in self._short_term:
            self._short_term[project_id] = {}
        self._short_term[project_id][key] = value

    def recall_short_term(self, project_id: str, key: str) -> Optional[Any]:
        """Recall a value from short-term memory."""
        return self._short_term.get(project_id, {}).get(key)

    def get_session_context(self, project_id: str) -> str:
        """Get all short-term memory for a project as a context string."""
        session = self._short_term.get(project_id, {})
        if not session:
            return ""

        context_parts = []
        for key, value in session.items():
            if isinstance(value, str) and len(value) > 100:
                # Summarize long values
                context_parts.append(f"**{key}**: {value[:200]}...")
            else:
                context_parts.append(f"**{key}**: {value}")

        return "\n".join(context_parts)

    # ── Long-Term Memory (Persistent) ─────────────────────────────────────

    def store_long_term(self, project_id: str, data: dict[str, Any]) -> None:
        """Persist analysis results to long-term storage.

        Stores the full analysis state as a JSON file for future reference.
        """
        file_path = self._memory_dir / f"{project_id}.json"
        try:
            file_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
            logger.info("Stored long-term memory for project %s", project_id)
        except Exception as e:
            logger.error("Failed to store long-term memory: %s", e)

    def recall_long_term(self, project_id: str) -> Optional[dict[str, Any]]:
        """Recall past analysis results from long-term storage."""
        file_path = self._memory_dir / f"{project_id}.json"
        if file_path.exists():
            try:
                return json.loads(file_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error("Failed to recall long-term memory: %s", e)
        return None

    def search_similar_analyses(self, startup_idea: str, top_k: int = 3) -> list[dict]:
        """Search past analyses for similar startup ideas.

        Uses simple keyword matching. For production, this would use
        vector similarity search via ChromaDB.

        Returns list of {project_id, startup_idea, similarity_hint}.
        """
        results = []
        idea_words = set(startup_idea.lower().split())

        for file_path in self._memory_dir.glob("*.json"):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                past_idea = data.get("startup_idea", "")
                past_words = set(past_idea.lower().split())

                # Simple word overlap as similarity signal
                overlap = len(idea_words & past_words)
                if overlap >= 2:
                    results.append({
                        "project_id": file_path.stem,
                        "startup_idea": past_idea,
                        "overlap_words": list(idea_words & past_words),
                        "similarity_score": overlap / max(len(idea_words), 1),
                    })
            except Exception:
                continue

        # Sort by similarity and return top_k
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    def list_past_analyses(self) -> list[dict]:
        """List all past analyses in long-term memory."""
        analyses = []
        for file_path in self._memory_dir.glob("*.json"):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                analyses.append({
                    "project_id": file_path.stem,
                    "startup_idea": data.get("startup_idea", "Unknown"),
                    "status": data.get("status", "unknown"),
                    "timestamp": data.get("timestamp", ""),
                })
            except Exception:
                continue
        return analyses

    # ── Cleanup ───────────────────────────────────────────────────────────

    def clear_short_term(self, project_id: Optional[str] = None) -> None:
        """Clear short-term memory for a project or all projects."""
        if project_id:
            self._short_term.pop(project_id, None)
        else:
            self._short_term.clear()

    def clear_all(self) -> None:
        """Clear all memory (short-term and long-term). Use with caution."""
        self._short_term.clear()
        for file_path in self._memory_dir.glob("*.json"):
            file_path.unlink()
        logger.warning("All memory cleared.")
