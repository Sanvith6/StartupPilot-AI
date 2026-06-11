"""
StartupPilot AI — Multi-LLM Router

Intelligent model selection with automatic fallback.
Routes tasks to the best available model based on task type,
provider availability, and cost/quality tradeoffs.

Interview talking point:
    "I built an intelligent model router that selects Groq for fast research tasks,
     GPT-4o for complex architecture design, and automatically falls back when a
     provider is unavailable — with full routing decision logging."
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel

from config import Settings, get_settings, DEFAULT_ROUTING_RULES, MODEL_PRICING

logger = logging.getLogger(__name__)


# ── Data Models ───────────────────────────────────────────────────────────────


@dataclass
class LLMConfig:
    """Configuration for a specific LLM instance."""

    provider: str
    model: str
    temperature: float = 0.3
    max_tokens: int = 4096
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0

    @property
    def display_name(self) -> str:
        return f"{self.provider}/{self.model}"


@dataclass
class RoutingDecision:
    """Record of a routing decision for observability."""

    task_type: str
    selected_provider: str
    selected_model: str
    reasoning: str
    alternatives_tried: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "task_type": self.task_type,
            "selected_provider": self.selected_provider,
            "selected_model": self.selected_model,
            "reasoning": self.reasoning,
            "alternatives_tried": self.alternatives_tried,
            "timestamp": self.timestamp,
        }


# ── Provider Factory ──────────────────────────────────────────────────────────



def _create_chat_model(
    provider: str,
    model: str,
    api_key: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> BaseChatModel:
    """Create a LangChain chat model for the given provider.

    Supports Groq, OpenAI, and DeepSeek (OpenAI-compatible API).
    """
    from config import get_settings
    timeout = get_settings().request_timeout_seconds or 60

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    elif provider == "deepseek":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            base_url="https://api.deepseek.com/v1",
            timeout=timeout,
        )
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            base_url="https://openrouter.ai/api/v1",
            timeout=timeout,
        )
    elif provider == "apifreellm":
        from llm_router.apifreellm import APIFreeLLMChat

        return APIFreeLLMChat(
            api_key=api_key,
            model_name=model,
            timeout=timeout,
        )
    elif provider == "dashscope":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            timeout=timeout,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


# ── LLM Router ────────────────────────────────────────────────────────────────


class LLMRouter:
    """Intelligent multi-LLM router with automatic fallback.

    Routes each task type to the best available model based on:
    1. Task-specific routing rules (research → Groq, architecture → GPT-4o)
    2. Provider availability (has API key?)
    3. Fallback chain (if primary fails, try next provider)

    Usage:
        router = LLMRouter()
        llm = router.get_llm("research")  # Returns best model for research
        decision = router.routing_log[-1]  # See why this model was chosen
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._routing_rules = DEFAULT_ROUTING_RULES
        self._routing_log: list[RoutingDecision] = []
        self._model_cache: dict[str, BaseChatModel] = {}

        logger.info(
            "LLMRouter initialized. Available providers: %s",
            self._settings.available_providers,
        )

    @property
    def routing_log(self) -> list[RoutingDecision]:
        """Get the full routing decision log."""
        return self._routing_log

    def get_available_providers(self) -> list[str]:
        """Return providers that have API keys configured."""
        return self._settings.available_providers

    def get_llm(
        self,
        task_type: str = "default",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> BaseChatModel:
        """Get the best available LLM for a given task type.

        Args:
            task_type: The type of task (e.g., "research", "architecture_design").
            temperature: Override the default temperature.
            max_tokens: Override the default max tokens.

        Returns:
            A LangChain chat model instance.

        Raises:
            RuntimeError: If no LLM provider is available.
        """
        temp = temperature or self._settings.temperature
        tokens = max_tokens or self._settings.max_tokens

        # Get routing rules for this task type (fall back to "default")
        rules = self._routing_rules.get(
            task_type, self._routing_rules["default"]
        )

        # Prioritize default provider/model if configured
        if self._settings.default_provider and self._settings.get_api_key(self._settings.default_provider):
            rules = [{"provider": self._settings.default_provider, "model": self._settings.default_model}] + list(rules)

        alternatives_tried: list[str] = []

        for rule in rules:
            provider = rule["provider"]
            model = rule["model"]

            # Check if this provider has an API key
            api_key = self._settings.get_api_key(provider)
            if not api_key:
                alternatives_tried.append(f"{provider}/{model} (no API key)")
                continue

            try:
                # Create cache key
                cache_key = f"{provider}:{model}:{temp}:{tokens}"

                if cache_key not in self._model_cache:
                    self._model_cache[cache_key] = _create_chat_model(
                        provider=provider,
                        model=model,
                        api_key=api_key,
                        temperature=temp,
                        max_tokens=tokens,
                    )

                # Log the routing decision
                pricing = MODEL_PRICING.get(model, {"input": 0, "output": 0})
                decision = RoutingDecision(
                    task_type=task_type,
                    selected_provider=provider,
                    selected_model=model,
                    reasoning=self._get_reasoning(task_type, provider, model),
                    alternatives_tried=alternatives_tried,
                )
                self._routing_log.append(decision)

                logger.info(
                    "Routed task '%s' → %s/%s (%s)",
                    task_type,
                    provider,
                    model,
                    decision.reasoning,
                )

                return self._model_cache[cache_key]

            except Exception as e:
                alternatives_tried.append(f"{provider}/{model} (error: {e})")
                logger.warning(
                    "Failed to create %s/%s: %s. Trying next provider...",
                    provider,
                    model,
                    e,
                )
                continue

        raise RuntimeError(
            f"No LLM provider available for task '{task_type}'. "
            f"Tried: {alternatives_tried}. "
            f"Set at least one API key in .env (GROQ_API_KEY is free)."
        )

    def get_llm_config(self, task_type: str = "default") -> LLMConfig:
        """Get the LLM configuration that would be selected for a task.

        Does not create the model — useful for displaying routing info.
        """
        rules = self._routing_rules.get(
            task_type, self._routing_rules["default"]
        )

        # Prioritize default provider/model if configured
        if self._settings.default_provider and self._settings.get_api_key(self._settings.default_provider):
            rules = [{"provider": self._settings.default_provider, "model": self._settings.default_model}] + list(rules)

        for rule in rules:
            provider = rule["provider"]
            model = rule["model"]
            api_key = self._settings.get_api_key(provider)

            if api_key:
                pricing = MODEL_PRICING.get(model, {"input": 0, "output": 0})
                return LLMConfig(
                    provider=provider,
                    model=model,
                    temperature=self._settings.temperature,
                    max_tokens=self._settings.max_tokens,
                    cost_per_1k_input=pricing["input"],
                    cost_per_1k_output=pricing["output"],
                )

        return LLMConfig(provider="none", model="none")

    def _get_reasoning(
        self, task_type: str, provider: str, model: str
    ) -> str:
        """Generate human-readable reasoning for a routing decision."""
        reasons = {
            "research": "Fast inference for broad research queries",
            "market_analysis": "Fast inference for analytical tasks",
            "competitor_analysis": "Fast inference for data gathering",
            "swot_analysis": "Fast inference for structured analysis",
            "business_strategy": "High-quality reasoning for strategic decisions",
            "architecture_design": "High-quality reasoning for complex design",
            "cost_estimation": "Good balance of quality and cost for financial analysis",
            "report_writing": "Fast inference for text generation",
            "evaluation": "Fast, cheap model for quality scoring",
            "discussion": "Fast inference for multi-turn conversation",
        }
        base_reason = reasons.get(task_type, "Default routing rule")
        return f"{base_reason} → {provider}/{model}"

    def get_routing_summary(self) -> list[dict]:
        """Get a summary of all routing decisions made so far."""
        return [d.to_dict() for d in self._routing_log]

    def clear_cache(self) -> None:
        """Clear the model cache (useful for testing)."""
        self._model_cache.clear()
        logger.info("LLM model cache cleared.")
