from __future__ import annotations

import time
from unittest.mock import MagicMock, patch
import pytest
import requests

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from llm_router.apifreellm import APIFreeLLMChat
from autogen_module.autogen_discussion import APIFreeLLMModelClient
from llm_router.router import _create_chat_model


def test_apifreellm_chat_success():
    """Test successful invocation of APIFreeLLMChat."""
    model = APIFreeLLMChat(api_key="test-key", timeout=10)
    
    messages = [
        SystemMessage(content="You are an AI assistant."),
        HumanMessage(content="Hello!")
    ]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "response": "Hello, how can I help you today?",
        "tier": "free"
    }

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = model.invoke(messages)
        
        # Verify post arguments
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"
        assert kwargs["json"]["model"] == "apifreellm"
        assert "System: You are an AI assistant.\n\nUser: Hello!" in kwargs["json"]["message"]
        
        # Verify result content
        assert result.content == "Hello, how can I help you today?"


def test_apifreellm_chat_rate_limit():
    """Test APIFreeLLMChat retry behavior when hitting 429 rate limits."""
    model = APIFreeLLMChat(api_key="test-key", timeout=10)
    messages = [HumanMessage(content="Hello")]

    # First response is a 429, second is 200 success
    mock_429 = MagicMock()
    mock_429.status_code = 429

    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {
        "success": True,
        "response": "Success after retry",
        "tier": "free"
    }

    with patch("requests.post", side_effect=[mock_429, mock_200]) as mock_post, \
         patch("time.sleep") as mock_sleep:  # Mock sleep to run test instantly
        result = model.invoke(messages)

        assert mock_post.call_count == 2
        mock_sleep.assert_called_once_with(21)
        assert result.content == "Success after retry"


def test_apifreellm_autogen_client_success():
    """Test successful invocation of AutoGen APIFreeLLMModelClient."""
    config = {
        "api_key": "test-autogen-key",
        "model": "apifreellm",
        "api_url": "https://apifreellm.com/api/v1/chat"
    }
    client = APIFreeLLMModelClient(config=config)

    params = {
        "messages": [
            {"role": "system", "content": "Be a helpful chatbot."},
            {"role": "user", "content": "Hi there."}
        ]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "response": "Hi user, how are you?",
        "tier": "free"
    }

    with patch("requests.post", return_value=mock_response) as mock_post:
        response = client.create(params)
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer test-autogen-key"
        assert kwargs["json"]["model"] == "apifreellm"
        assert "System: Be a helpful chatbot.\n\nUser: Hi there." in kwargs["json"]["message"]
        
        # Verify choice contents conforming to AutoGen expectations
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "Hi user, how are you?"
        assert response.choices[0].message.role == "assistant"
        
        retrieved = client.message_retrieval(response)
        assert retrieved == ["Hi user, how are you?"]
        
        assert client.cost(response) == 0.0
        assert client.get_usage(response)["total_tokens"] == 0


def test_router_creates_apifreellm_model():
    """Test that _create_chat_model returns an APIFreeLLMChat instance."""
    model = _create_chat_model(
        provider="apifreellm",
        model="apifreellm",
        api_key="dummy-key",
        temperature=0.7,
        max_tokens=2048
    )
    assert isinstance(model, APIFreeLLMChat)
    assert model.api_key == "dummy-key"
    assert model.model_name == "apifreellm"
