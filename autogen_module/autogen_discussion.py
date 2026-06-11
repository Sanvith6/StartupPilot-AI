"""
StartupPilot AI — AutoGen Multi-Agent Discussion

Implements a GroupChat with 3 agents who debate startup viability:
- Business Consultant: evaluates business value and market fit
- Cloud Architect: evaluates technical feasibility and scalability
- Financial Analyst: evaluates cost impact and financial viability

The agents discuss for multiple rounds and produce a consensus recommendation.

Interview talking point:
    "I used AutoGen for autonomous multi-agent discussions. Three specialized
     agents debate startup viability from business, technical, and financial
     perspectives — producing a consensus recommendation after several rounds."
"""

from __future__ import annotations

import logging
from typing import Optional

from config import get_settings

logger = logging.getLogger(__name__)


def run_discussion(
    startup_idea: str,
    business_context: str = "",
    architecture_context: str = "",
    max_rounds: Optional[int] = None,
) -> dict:
    """Run an AutoGen GroupChat discussion about startup viability.

    Three agents discuss the startup idea from different perspectives
    and reach a consensus recommendation.

    Args:
        startup_idea: The startup idea being evaluated.
        business_context: Prior business strategy analysis.
        architecture_context: Prior architecture analysis (if available).
        max_rounds: Maximum discussion rounds (default from config).

    Returns:
        Dict with keys:
            - transcript: Full discussion transcript (str)
            - consensus: Final consensus recommendation (str)
            - rounds: Number of discussion rounds
    """
    settings = get_settings()
    rounds = max_rounds or settings.autogen_max_rounds

    # Determine which LLM to use
    llm_config = _build_llm_config(settings)

    if llm_config is None:
        logger.warning("No LLM provider available. Returning mock discussion.")
        return _mock_discussion(startup_idea)

    try:
        import autogen

        # ── Create the three discussion agents ────────────────────────────

        business_consultant = autogen.AssistantAgent(
            name="Business_Consultant",
            system_message=(
                "You are a Senior Business Consultant evaluating startup viability. "
                "Focus on: market opportunity, business model strength, go-to-market "
                "feasibility, competitive positioning, and revenue potential. "
                "Be specific and data-driven in your assessments. "
                "Challenge other agents' assumptions constructively."
            ),
            llm_config=llm_config,
        )

        cloud_architect = autogen.AssistantAgent(
            name="Cloud_Architect",
            system_message=(
                "You are a Principal Cloud Architect evaluating technical feasibility. "
                "Focus on: technology stack choices, scalability challenges, "
                "infrastructure complexity, security concerns, and development timeline. "
                "Provide realistic assessments of what can be built and at what cost. "
                "Challenge overly optimistic technical assumptions."
            ),
            llm_config=llm_config,
        )

        financial_analyst = autogen.AssistantAgent(
            name="Financial_Analyst",
            system_message=(
                "You are a Cloud Financial Analyst evaluating cost impact. "
                "Focus on: infrastructure costs, burn rate, unit economics, "
                "cost optimization opportunities, and financial sustainability. "
                "Challenge expensive technical decisions and suggest cost-effective "
                "alternatives. Be specific with numbers."
            ),
            llm_config=llm_config,
        )

        if settings.apifreellm_api_key:
            for agent in [business_consultant, cloud_architect, financial_analyst]:
                agent.register_model_client(model_client_cls=APIFreeLLMModelClient)

        # ── User proxy (orchestrator) ────────────────────────────────────

        user_proxy = autogen.UserProxyAgent(
            name="Discussion_Moderator",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config=False,
            system_message=(
                "You are a discussion moderator. Start the discussion by presenting "
                "the startup idea and asking each expert to share their perspective."
            ),
        )

        # ── GroupChat setup ───────────────────────────────────────────────

        group_chat = autogen.GroupChat(
            agents=[user_proxy, business_consultant, cloud_architect, financial_analyst],
            messages=[],
            max_round=rounds,
            speaker_selection_method="round_robin",
        )

        manager = autogen.GroupChatManager(
            groupchat=group_chat,
            llm_config=llm_config,
        )
        if settings.apifreellm_api_key:
            manager.register_model_client(model_client_cls=APIFreeLLMModelClient)

        # ── Run the discussion ────────────────────────────────────────────

        discussion_prompt = (
            f"Let's evaluate this startup idea: '{startup_idea}'\n\n"
        )

        if business_context:
            discussion_prompt += (
                f"Business analysis so far:\n{business_context[:500]}\n\n"
            )

        if architecture_context:
            discussion_prompt += (
                f"Architecture considerations:\n{architecture_context[:500]}\n\n"
            )

        discussion_prompt += (
            "Each expert should provide their assessment from their specialty area. "
            "After the discussion, reach a consensus recommendation on:\n"
            "1. Overall viability (1-10 score)\n"
            "2. Key strengths\n"
            "3. Critical risks\n"
            "4. Recommended next steps\n\n"
            "Business Consultant, please start."
        )

        logger.info("Starting AutoGen discussion for '%s' (max %d rounds)", startup_idea[:50], rounds)

        user_proxy.initiate_chat(
            manager,
            message=discussion_prompt,
        )

        # ── Extract transcript ────────────────────────────────────────────

        transcript_parts = []
        for msg in group_chat.messages:
            sender = msg.get("name", msg.get("role", "Unknown"))
            content = msg.get("content", "")
            if content:
                transcript_parts.append(f"**{sender}**: {content}")

        transcript = "\n\n---\n\n".join(transcript_parts)

        # Extract consensus (last message is typically the summary)
        consensus = ""
        if group_chat.messages:
            last_messages = group_chat.messages[-2:]
            consensus = "\n\n".join(
                msg.get("content", "") for msg in last_messages if msg.get("content")
            )

        logger.info(
            "AutoGen discussion completed. %d messages exchanged.",
            len(group_chat.messages),
        )

        return {
            "transcript": transcript,
            "consensus": consensus,
            "rounds": len(group_chat.messages),
        }

    except Exception as e:
        logger.error("AutoGen discussion failed: %s", e)
        return {
            "transcript": f"Discussion failed: {str(e)}",
            "consensus": "Unable to reach consensus due to technical error.",
            "rounds": 0,
            "error": str(e),
        }


class APIFreeLLMModelClient:
    """Custom AutoGen ModelClient for APIFreeLLM (free tier)."""

    def __init__(self, config, **kwargs):
        self.api_key = config.get("api_key")
        self.model = config.get("model", "apifreellm")
        self.api_url = config.get("api_url", "https://apifreellm.com/api/v1/chat")
        self.timeout = config.get("timeout", 120)

    def create(self, params):
        messages = params.get("messages", [])
        
        message_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                message_parts.append(f"System: {content}")
            elif role == "assistant":
                message_parts.append(f"Assistant: {content}")
            else:
                message_parts.append(f"User: {content}")
        prompt_str = "\n\n".join(message_parts)

        import requests
        import time
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "message": prompt_str,
            "model": self.model
        }
        
        max_retries = 3
        backoff_seconds = 21
        res_json = None
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 429:
                    time.sleep(backoff_seconds)
                    continue

                response.raise_for_status()
                res_json = response.json()
                
                if not res_json.get("success"):
                    raise ValueError(f"APIFreeLLM API error: {res_json.get('response') or res_json}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise RuntimeError(f"APIFreeLLM request failed: {e}") from e
        else:
            raise RuntimeError("APIFreeLLM request failed due to rate limits.")

        text = res_json.get("response", "")
        
        class Response:
            class Choice:
                class Message:
                    def __init__(self, content):
                        self.content = content
                        self.role = "assistant"
                        self.function_call = None
                        self.tool_calls = None
                def __init__(self, content):
                    self.message = Response.Choice.Message(content)
                    self.finish_reason = "stop"
            
            def __init__(self, content):
                self.choices = [Response.Choice(content)]
                self.model = "apifreellm"
                class Usage:
                    def __init__(self):
                        self.prompt_tokens = 0
                        self.completion_tokens = 0
                        self.total_tokens = 0
                self.usage = Usage()
        
        return Response(text)

    def message_retrieval(self, response):
        return [choice.message.content for choice in response.choices]

    def cost(self, response):
        return 0.0

    @staticmethod
    def get_usage(response):
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost": 0.0
        }


def _build_llm_config(settings: Settings) -> Optional[dict]:
    """Build AutoGen LLM config from available providers."""
    configs = []

    if settings.apifreellm_api_key:
        configs.append({
            "model": settings.default_model if settings.default_provider == "apifreellm"
                     else "apifreellm",
            "api_key": settings.apifreellm_api_key,
            "model_client_cls": "APIFreeLLMModelClient",
            "api_url": "https://apifreellm.com/api/v1/chat",
        })

    if settings.openrouter_api_key:
        configs.append({
            "model": settings.default_model if settings.default_provider == "openrouter"
                     else "nvidia/nemotron-3-ultra-550b-a55b:free",
            "api_key": settings.openrouter_api_key,
            "base_url": "https://openrouter.ai/api/v1",
            "api_type": "openai",
        })

    if settings.groq_api_key:
        configs.append({
            "model": settings.default_model if settings.default_provider == "groq"
                     else "llama-3.3-70b-versatile",
            "api_key": settings.groq_api_key,
            "base_url": "https://api.groq.com/openai/v1",
            "api_type": "openai",
        })

    if settings.openai_api_key:
        configs.append({
            "model": "gpt-4o-mini",
            "api_key": settings.openai_api_key,
        })

    if not configs:
        return None

    return {
        "config_list": configs,
        "temperature": settings.temperature,
        "timeout": settings.request_timeout_seconds,
    }


def _mock_discussion(startup_idea: str) -> dict:
    """Return a mock discussion when no LLM is available (demo mode)."""
    return {
        "transcript": (
            f"**Discussion_Moderator**: Let's evaluate: '{startup_idea}'\n\n---\n\n"
            "**Business_Consultant**: This startup idea targets a growing market. "
            "The key strength is the clear problem-solution fit. However, customer "
            "acquisition costs could be high in this space. I recommend starting with "
            "a focused niche and expanding.\n\n---\n\n"
            "**Cloud_Architect**: From a technical perspective, this is feasible with "
            "modern cloud-native architecture. I recommend starting with a serverless "
            "approach to minimize initial costs. The main technical risk is data "
            "integration complexity.\n\n---\n\n"
            "**Financial_Analyst**: Infrastructure costs for MVP would be approximately "
            "$500-1,500/month using serverless. This is sustainable for an early-stage "
            "startup. The unit economics look favorable if customer acquisition costs "
            "stay below $50.\n\n---\n\n"
            "**Business_Consultant**: Agreed. My recommendation: start lean, validate "
            "with 10-20 pilot customers, then scale. Overall viability: 7/10."
        ),
        "consensus": (
            "**Consensus Recommendation**\n\n"
            "- Overall Viability: 7/10\n"
            "- Key Strengths: Clear problem-solution fit, growing market, feasible technology\n"
            "- Critical Risks: Customer acquisition costs, data integration complexity\n"
            "- Recommended Next Steps: Build MVP with serverless architecture, "
            "acquire 10-20 pilot customers, validate unit economics"
        ),
        "rounds": 4,
    }
