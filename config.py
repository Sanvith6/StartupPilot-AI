"""
StartupPilot AI — Central Configuration

All application settings loaded from environment variables with sensible defaults.
Supports Groq (free), OpenAI, and DeepSeek as LLM providers with automatic fallback.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


# ── Project root ──────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
REPORTS_DIR = DATA_DIR / "reports"
CHROMA_DIR = DATA_DIR / "chroma"
MEMORY_DIR = DATA_DIR / "memory"
WIKI_DIR = DATA_DIR / "wiki"


# ── LLM Model Pricing (USD per 1K tokens) ────────────────────────────────────

MODEL_PRICING: dict[str, dict[str, float]] = {
    # Groq (free tier)
    "llama-3.3-70b-versatile": {"input": 0.0, "output": 0.0},
    "llama-3.1-8b-instant": {"input": 0.0, "output": 0.0},
    "mixtral-8x7b-32768": {"input": 0.0, "output": 0.0},
    # OpenAI
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    # DeepSeek
    "deepseek-chat": {"input": 0.00014, "output": 0.00028},
    # OpenRouter
    "nvidia/nemotron-3-ultra-550b-a55b:free": {"input": 0.0, "output": 0.0},
    "nex-agi/nex-n2-pro:free": {"input": 0.0, "output": 0.0},
    # APIFreeLLM
    "apifreellm": {"input": 0.0, "output": 0.0},
    # DashScope / Alibaba Cloud Model Studio
    "qwen3.7-plus-2026-05-26": {"input": 0.00028, "output": 0.0011},
    "qwen-plus": {"input": 0.0004, "output": 0.0012},
}


# ── LLM Routing Rules ────────────────────────────────────────────────────────
# Maps task types to preferred (provider, model) pairs.
# The router tries these in order and falls back if a provider is unavailable.

DEFAULT_ROUTING_RULES: dict[str, list[dict[str, str]]] = {
    "research": [
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        {"provider": "openai", "model": "gpt-4o-mini"},
    ],
    "market_analysis": [
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        {"provider": "openai", "model": "gpt-4o-mini"},
    ],
    "competitor_analysis": [
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        {"provider": "openai", "model": "gpt-4o-mini"},
    ],
    "swot_analysis": [
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        {"provider": "openai", "model": "gpt-4o-mini"},
    ],
    "business_strategy": [
        {"provider": "openai", "model": "gpt-4o"},
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
    ],
    "architecture_design": [
        {"provider": "openai", "model": "gpt-4o"},
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
    ],
    "cost_estimation": [
        {"provider": "openai", "model": "gpt-4o-mini"},
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
    ],
    "report_writing": [
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        {"provider": "openai", "model": "gpt-4o-mini"},
    ],
    "evaluation": [
        {"provider": "groq", "model": "llama-3.1-8b-instant"},
        {"provider": "openai", "model": "gpt-4o-mini"},
    ],
    "discussion": [
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        {"provider": "openai", "model": "gpt-4o-mini"},
    ],
    "default": [
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        {"provider": "openai", "model": "gpt-4o-mini"},
        {"provider": "deepseek", "model": "deepseek-chat"},
    ],
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── LLM Provider API Keys ─────────────────────────────────────────────
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    apifreellm_api_key: Optional[str] = Field(default=None, alias="APIFREELLM_API_KEY")
    dashscope_api_key: Optional[str] = Field(default=None, alias="DASHSCOPE_API_KEY")

    # ── Default LLM Settings ─────────────────────────────────────────────
    default_provider: str = Field(default="groq", alias="LLM_PROVIDER")
    default_model: str = Field(
        default="llama-3.3-70b-versatile", alias="DEFAULT_MODEL"
    )
    fallback_provider: str = Field(default="openai", alias="FALLBACK_PROVIDER")
    fallback_model: str = Field(default="gpt-4o-mini", alias="FALLBACK_MODEL")
    temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    max_tokens: int = Field(default=4096, alias="LLM_MAX_TOKENS")

    # ── RAG Settings ─────────────────────────────────────────────────────
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL"
    )
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    retrieval_top_k: int = Field(default=5, alias="RETRIEVAL_TOP_K")

    # ── File Paths ────────────────────────────────────────────────────────
    upload_dir: str = Field(default=str(UPLOAD_DIR), alias="UPLOAD_DIR")
    reports_dir: str = Field(default=str(REPORTS_DIR), alias="REPORTS_DIR")
    chroma_persist_dir: str = Field(default=str(CHROMA_DIR), alias="CHROMA_PERSIST_DIR")
    memory_dir: str = Field(default=str(MEMORY_DIR), alias="MEMORY_DIR")
    wiki_dir: str = Field(default=str(WIKI_DIR), alias="WIKI_DIR")

    # ── Knowledge Wiki Settings ──────────────────────────────────────────
    wiki_auto_compile: bool = Field(
        default=True,
        alias="WIKI_AUTO_COMPILE",
        description="Auto-compile wiki on document upload",
    )
    wiki_max_topic_pages: int = Field(default=20, alias="WIKI_MAX_TOPIC_PAGES")
    wiki_max_entity_pages: int = Field(default=50, alias="WIKI_MAX_ENTITY_PAGES")

    # ── Backend Settings ──────────────────────────────────────────────────
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    frontend_port: int = Field(default=8501, alias="FRONTEND_PORT")

    # ── Retry / Failure Recovery ──────────────────────────────────────────
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    retry_delay_seconds: float = Field(default=2.0, alias="RETRY_DELAY_SECONDS")
    request_timeout_seconds: int = Field(default=120, alias="REQUEST_TIMEOUT_SECONDS")

    # ── AutoGen Settings ──────────────────────────────────────────────────
    autogen_max_rounds: int = Field(default=6, alias="AUTOGEN_MAX_ROUNDS")

    # ── LangSmith (Optional) ─────────────────────────────────────────────
    langsmith_api_key: Optional[str] = Field(
        default=None, alias="LANGSMITH_API_KEY"
    )
    langsmith_project: str = Field(
        default="startuppilot-ai", alias="LANGSMITH_PROJECT"
    )

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "populate_by_name": True,
    }

    # ── Derived Properties ────────────────────────────────────────────────

    @property
    def available_providers(self) -> list[str]:
        """Return list of providers that have API keys configured."""
        providers = []
        if self.groq_api_key:
            providers.append("groq")
        if self.openai_api_key:
            providers.append("openai")
        if self.deepseek_api_key:
            providers.append("deepseek")
        if self.openrouter_api_key:
            providers.append("openrouter")
        if self.apifreellm_api_key:
            providers.append("apifreellm")
        if self.dashscope_api_key:
            providers.append("dashscope")
        return providers

    @property
    def has_any_llm_key(self) -> bool:
        """Check if at least one LLM provider is configured."""
        return len(self.available_providers) > 0

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get the API key for a specific provider."""
        key_map = {
            "groq": self.groq_api_key,
            "openai": self.openai_api_key,
            "deepseek": self.deepseek_api_key,
            "openrouter": self.openrouter_api_key,
            "apifreellm": self.apifreellm_api_key,
            "dashscope": self.dashscope_api_key,
        }
        return key_map.get(provider)


def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def ensure_directories() -> None:
    """Create all required data directories."""
    for directory in [UPLOAD_DIR, REPORTS_DIR, CHROMA_DIR, MEMORY_DIR, WIKI_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
