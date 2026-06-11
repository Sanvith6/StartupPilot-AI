from __future__ import annotations

import logging
import time
import requests
from typing import Any, Dict, List, Optional

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field

logger = logging.getLogger(__name__)


class APIFreeLLMChat(BaseChatModel):
    """Custom LangChain ChatModel for APIFreeLLM.

    Wraps the POST https://apifreellm.com/api/v1/chat endpoint.
    Handles rate limit failures (HTTP 429) automatically by sleeping for 21 seconds and retrying.
    """

    api_key: str
    model_name: str = "apifreellm"
    api_url: str = "https://apifreellm.com/api/v1/chat"
    timeout: int = 120

    @property
    def _llm_type(self) -> str:
        return "apifreellm"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name, "api_url": self.api_url}

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # 1. Compile message list into a unified message string
        message_parts = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                message_parts.append(f"System: {msg.content}")
            elif isinstance(msg, HumanMessage):
                message_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                message_parts.append(f"Assistant: {msg.content}")
            else:
                message_parts.append(f"{msg.content}")
        prompt_str = "\n\n".join(message_parts)

        # 2. Setup headers and body
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "message": prompt_str,
            "model": self.model_name
        }

        # 3. Call endpoint with rate limit handling (1 request every 20 seconds)
        max_retries = 3
        backoff_seconds = 21
        response = None
        text = ""

        for attempt in range(max_retries):
            try:
                logger.info(
                    "Sending request to APIFreeLLM (attempt %d/%d)",
                    attempt + 1,
                    max_retries,
                )
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                # Check for rate limit
                if response.status_code == 429:
                    logger.warning(
                        "APIFreeLLM rate limit (429) hit. Waiting %d seconds before retry...",
                        backoff_seconds
                    )
                    time.sleep(backoff_seconds)
                    continue

                response.raise_for_status()
                res_json = response.json()
                
                if not res_json.get("success"):
                    # API returns success: false
                    raise ValueError(f"APIFreeLLM API returned error: {res_json.get('response') or res_json}")
                
                text = res_json.get("response", "")
                break

            except requests.exceptions.RequestException as e:
                # If we hit an HTTP error or connection issue
                if response is not None and response.status_code == 429:
                    # Already handled above, but just in case
                    time.sleep(backoff_seconds)
                    continue
                
                logger.warning("Request to APIFreeLLM failed: %s", e)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise RuntimeError(f"APIFreeLLM connection failed after {max_retries} attempts: {e}") from e

        else:
            raise RuntimeError(f"APIFreeLLM request failed due to rate limits after {max_retries} retries.")

        # 4. Return result conforming to LangChain expectations
        ai_message = AIMessage(content=text)
        generation = ChatGeneration(message=ai_message)
        return ChatResult(generations=[generation])
