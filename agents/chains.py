"""
StartupPilot AI — LangChain Chains

LLMChain wrappers and RetrievalQA chain integration.
Each chain combines a prompt template with the LLM router to execute
agent tasks with automatic model selection and fallback.

LangChain components: LLMChain, RunnableSequence
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from agents.prompt_templates import get_prompt
from llm_router.router import LLMRouter

logger = logging.getLogger(__name__)


class AgentChain:
    """Wraps a prompt template + LLM into an executable chain.

    Handles:
    - Model selection via LLMRouter
    - Execution with timing metrics
    - Error handling and logging

    Usage:
        router = LLMRouter()
        chain = AgentChain(router)
        result = chain.run("research", "AI healthcare scheduling", context="...")
    """

    def __init__(self, router: Optional[LLMRouter] = None) -> None:
        self._router = router or LLMRouter()

    def run(
        self,
        agent_type: str,
        startup_idea: str,
        context: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        """Execute an agent chain for a specific task.

        Args:
            agent_type: The type of agent (e.g., "research", "market_analysis").
            startup_idea: The user's startup idea.
            context: Optional RAG context or prior agent outputs.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.

        Returns:
            Dict with keys: "output", "metrics"
                output: The LLM's response text
                metrics: Dict with execution_time_ms, model_used, provider, tokens
        """
        start_time = time.time()

        try:
            # Get the appropriate LLM via the router
            llm = self._router.get_llm(
                task_type=agent_type,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Get the prompt template
            prompt = get_prompt(agent_type, startup_idea, context)

            # Build and invoke the chain
            chain = prompt | llm
            response = chain.invoke({})

            # Extract response content
            output = response.content if hasattr(response, "content") else str(response)

            # Calculate metrics
            elapsed_ms = int((time.time() - start_time) * 1000)
            routing_decision = self._router.routing_log[-1] if self._router.routing_log else None

            metrics = {
                "execution_time_ms": elapsed_ms,
                "provider": routing_decision.selected_provider if routing_decision else "unknown",
                "model_used": routing_decision.selected_model if routing_decision else "unknown",
                "task_type": agent_type,
                "input_length": len(startup_idea) + len(context),
                "output_length": len(output),
            }

            logger.info(
                "Agent '%s' completed in %dms using %s/%s (%d chars output)",
                agent_type,
                elapsed_ms,
                metrics["provider"],
                metrics["model_used"],
                len(output),
            )

            return {"output": output, "metrics": metrics}

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "Agent '%s' failed after %dms: %s",
                agent_type,
                elapsed_ms,
                str(e),
            )
            raise


class RetrievalChain:
    """Chain that retrieves context from RAG before running an agent.

    Combines document retrieval with agent execution:
    1. Query ChromaDB for relevant context
    2. Inject context into the agent prompt
    3. Execute the agent chain

    Usage:
        from rag.retrieval import retrieve_context
        chain = RetrievalChain(router)
        result = chain.run("research", "AI healthcare", project_id="abc123")
    """

    def __init__(self, router: Optional[LLMRouter] = None) -> None:
        self._agent_chain = AgentChain(router)

    def run(
        self,
        agent_type: str,
        startup_idea: str,
        project_id: Optional[str] = None,
        additional_context: str = "",
    ) -> dict[str, Any]:
        """Execute an agent chain with RAG context injection.

        Args:
            agent_type: The type of agent.
            startup_idea: The user's startup idea.
            project_id: Optional project ID for project-specific RAG.
            additional_context: Additional context from prior agents.

        Returns:
            Dict with keys: "output", "metrics", "rag_context"
        """
        rag_context = ""

        # Try to retrieve context from RAG (wiki-first, then raw chunks)
        if project_id:
            try:
                from rag.retrieval import retrieve_context

                rag_context = retrieve_context(
                    query=f"{agent_type}: {startup_idea}",
                    project_id=project_id,
                    agent_type=agent_type,
                )
                logger.info(
                    "Retrieved %d chars of context for '%s'",
                    len(rag_context),
                    agent_type,
                )
            except Exception as e:
                logger.warning("RAG retrieval failed: %s. Proceeding without context.", e)

        # Combine RAG context with additional context
        full_context = ""
        if rag_context:
            full_context += f"### Retrieved Documents\n{rag_context}\n\n"
        if additional_context:
            full_context += f"### Prior Analysis\n{additional_context}\n\n"

        # Run the agent chain
        result = self._agent_chain.run(
            agent_type=agent_type,
            startup_idea=startup_idea,
            context=full_context,
        )
        result["rag_context"] = rag_context

        return result
