"""
StartupPilot AI — Test Configuration & Fixtures

Configures environment variables for testing, provides a FastAPI TestClient,
and registers mocks for the LLM providers, routers, and third-party frameworks
(like CrewAI, AutoGen, and ChromaDB) to ensure tests run offline.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

# ── Mock Out Complex Frameworks ───────────────────────────────────────────────

# Mock CrewAI
class MockAgent:
    def __init__(self, *args, **kwargs):
        pass

class MockTask:
    def __init__(self, *args, **kwargs):
        pass

class MockCrew:
    def __init__(self, *args, **kwargs):
        pass

crew_mock = MagicMock()
crew_mock.Agent = MockAgent
crew_mock.Task = MockTask
crew_mock.Crew = MockCrew
crew_mock.Process = MagicMock()
sys.modules["crewai"] = crew_mock

# Mock AutoGen
autogen_mock = MagicMock()
autogen_mock.AssistantAgent = MagicMock()
autogen_mock.UserProxyAgent = MagicMock()
autogen_mock.GroupChat = MagicMock()
autogen_mock.GroupChatManager = MagicMock()
sys.modules["autogen"] = autogen_mock

# Mock ChromaDB
chromadb_mock = MagicMock()
sys.modules["chromadb"] = chromadb_mock
sys.modules["chromadb.utils"] = MagicMock()
sys.modules["chromadb.utils.embedding_functions"] = MagicMock()

# Mock Sentence Transformers
sys.modules["sentence_transformers"] = MagicMock()


# ── Configure Test Environment Variables ──────────────────────────────────────

os.environ["GROQ_API_KEY"] = "mock-groq-key"
os.environ["OPENAI_API_KEY"] = "mock-openai-key"
os.environ["DEEPSEEK_API_KEY"] = "mock-deepseek-key"
os.environ["DASHSCOPE_API_KEY"] = "mock-dashscope-key"
os.environ["UPLOAD_DIR"] = "./data/test_uploads"
os.environ["REPORTS_DIR"] = "./data/test_reports"
os.environ["CHROMA_PERSIST_DIR"] = "./data/test_chroma"
os.environ["MEMORY_DIR"] = "./data/test_memory"
os.environ["WIKI_DIR"] = "./data/test_wiki"


# ── Pytest Fixtures ───────────────────────────────────────────────────────────

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from config import ensure_directories


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Create test directories and clean them up after testing."""
    ensure_directories()
    yield
    # Clean up test directories
    import shutil
    from pathlib import Path
    for p in ["./data/test_uploads", "./data/test_reports", "./data/test_chroma", "./data/test_memory", "./data/test_wiki"]:
        path = Path(p)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def client() -> TestClient:
    """Fixture for FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_llm_router(monkeypatch):
    """Mock the LLM Router and RetrievalChain to return static content and avoid real API calls."""
    from llm_router.router import LLMRouter
    from agents.chains import RetrievalChain
    
    # Mock LLMRouter methods
    monkeypatch.setattr(LLMRouter, "get_llm", lambda *args, **kwargs: MagicMock())
    
    # Mock RetrievalChain.run to return structured simulation content
    def mock_chain_run(self, agent_type: str, startup_idea: str, project_id: str, additional_context: str = ""):
        outputs = {
            "research": "## Research Analyst findings\nIndustry shows rapid growth in cloud-native and AI integrations.",
            "market_analysis": "## Market Analysis\nTAM is estimated at $12B with SOM at $120M in 3-5 years.",
            "competitor_analysis": "## Competitor landscape\nIdentified 3 direct competitors. Primary edge: predictive ML scheduling.",
            "swot_analysis": "## SWOT Analysis\nStrengths: AI native. Weaknesses: Brand awareness.",
            "business_strategy": "## Business Strategy\nFocus on B2B pilot clinics first. Subscription pricing tier model.",
            "architecture_design": "## Cloud Architecture\nAWS ECS Fargate, RDS PostgreSQL, and SageMaker. Security is HIPAA compliant.",
            "cost_estimation": "## Cost Estimates\nMonthly cost starting at $600 at MVP, scaling to $2500 in growth stage.",
            "report_writing": "## Final Compiled Startup Analysis\nCombined report content.",
        }
        return {
            "output": outputs.get(agent_type, f"Mocked output for {agent_type}"),
            "metrics": {
                "time_ms": 120,
                "model_used": "llama-3.3-70b-versatile",
                "provider": "groq"
            }
        }
        
    monkeypatch.setattr(RetrievalChain, "run", mock_chain_run)
