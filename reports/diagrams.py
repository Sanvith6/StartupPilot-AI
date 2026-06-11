"""
StartupPilot AI — Diagram Generation

Generates Mermaid diagrams for the analysis report:
- System architecture diagram (based on agent output)
- Workflow diagram (the LangGraph pipeline)
- Agent interaction diagram
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def generate_diagrams(state: dict[str, Any]) -> dict[str, str]:
    """Generate all diagrams from the analysis state.

    Returns:
        Dict mapping diagram name to Mermaid code.
    """
    diagrams = {}

    diagrams["workflow"] = _workflow_diagram(state)
    diagrams["agent_interaction"] = _agent_interaction_diagram()
    diagrams["architecture"] = _architecture_diagram(state)

    logger.info("Generated %d diagrams", len(diagrams))
    return diagrams


def _workflow_diagram(state: dict[str, Any]) -> str:
    """Generate the LangGraph workflow diagram showing node status."""
    current = state.get("current_step", "completed")
    status = state.get("status", "completed")

    def node_style(node_name: str) -> str:
        steps_order = [
            "research", "market_analysis", "competitor_analysis",
            "swot_analysis", "business_strategy", "human_approval",
            "autogen_discussion", "architecture_cost",
            "report_generation", "memory_storage", "completed",
        ]
        try:
            current_idx = steps_order.index(current)
            node_idx = steps_order.index(node_name)
            if node_idx < current_idx:
                return "✅ "
            elif node_idx == current_idx:
                return "▶️ "
            else:
                return "⏳ "
        except ValueError:
            return ""

    return f"""graph TD
    START([🚀 START]) --> R["{node_style('research')}Research Agent"]
    R --> MA["{node_style('market_analysis')}Market Analysis"]
    MA --> CA["{node_style('competitor_analysis')}Competitor Analysis"]
    CA --> SW["{node_style('swot_analysis')}SWOT Analysis"]
    SW --> BS["{node_style('business_strategy')}Business Strategy"]
    BS --> HA{{"{node_style('human_approval')}Human Approval"}}
    HA -->|Approve| AG["{node_style('autogen_discussion')}AutoGen Discussion"]
    HA -->|Modify| BS
    HA -->|Reject| END2([❌ Rejected])
    AG --> AC["{node_style('architecture_cost')}Architecture & Cost"]
    AC --> RPT["{node_style('report_generation')}Report Generation"]
    RPT --> MEM["{node_style('memory_storage')}Memory Storage"]
    MEM --> END([✅ Complete])

    style HA fill:#f9a825,stroke:#f57f17,color:#000
    style AG fill:#42a5f5,stroke:#1565c0,color:#fff
    style END fill:#66bb6a,stroke:#2e7d32,color:#fff
    style END2 fill:#ef5350,stroke:#c62828,color:#fff"""


def _agent_interaction_diagram() -> str:
    """Generate the agent interaction diagram."""
    return """graph LR
    User([👤 User]) --> API[⚡ FastAPI]
    API --> LG[🔄 LangGraph]
    LG --> RA[🔬 Research Analyst]
    LG --> MA[📊 Market Analyst]
    LG --> CA[🎯 Competitor Analyst]
    LG --> SW[⚡ SWOT Strategist]
    LG --> BC[💡 Business Consultant]
    LG --> HITL{👤 Human Approval}
    HITL --> AG[💬 AutoGen GroupChat]
    AG --> BC2[💡 Business Consultant]
    AG --> ARCH[🏗️ Cloud Architect]
    AG --> FA[💰 Financial Analyst]
    LG --> ARCH2[🏗️ Cloud Architect]
    LG --> FA2[💰 Financial Analyst]
    LG --> TW[✍️ Report Writer]
    TW --> Report([📄 Final Report])

    RA & MA & CA & SW & BC --> RAG[(📚 ChromaDB RAG)]
    RA & MA & CA & SW & BC --> Router[🔀 LLM Router]
    Router --> Groq[Groq]
    Router --> OpenAI[OpenAI]

    style LG fill:#7c4dff,stroke:#6200ea,color:#fff
    style AG fill:#42a5f5,stroke:#1565c0,color:#fff
    style HITL fill:#f9a825,stroke:#f57f17,color:#000
    style Report fill:#66bb6a,stroke:#2e7d32,color:#fff"""


def _architecture_diagram(state: dict[str, Any]) -> str:
    """Generate a cloud architecture diagram based on the analysis."""
    startup_idea = state.get("startup_idea", "Startup Platform")

    return f"""graph TD
    subgraph "Client Layer"
        WEB[🌐 Web App<br/>React / Next.js]
        MOB[📱 Mobile App<br/>React Native]
    end

    subgraph "API Layer"
        ALB[⚖️ Load Balancer<br/>AWS ALB]
        API[⚡ API Gateway<br/>FastAPI / Express]
        AUTH[🔐 Auth Service<br/>JWT / OAuth2]
    end

    subgraph "Application Layer"
        SVC1[📦 Core Service]
        SVC2[🤖 AI Service]
        QUEUE[📫 Message Queue<br/>SQS / Redis]
    end

    subgraph "Data Layer"
        DB[(🗄️ Database<br/>PostgreSQL)]
        CACHE[(⚡ Cache<br/>Redis)]
        S3[(📁 Storage<br/>S3)]
    end

    subgraph "AI/ML Layer"
        LLM[🧠 LLM API<br/>OpenAI / Groq]
        VEC[(📚 Vector DB<br/>ChromaDB)]
    end

    WEB & MOB --> ALB
    ALB --> API
    API --> AUTH
    API --> SVC1
    API --> SVC2
    SVC1 --> DB
    SVC1 --> CACHE
    SVC2 --> LLM
    SVC2 --> VEC
    SVC1 --> QUEUE
    QUEUE --> SVC2
    SVC1 --> S3

    style API fill:#42a5f5,stroke:#1565c0,color:#fff
    style DB fill:#66bb6a,stroke:#2e7d32,color:#fff
    style LLM fill:#ab47bc,stroke:#7b1fa2,color:#fff"""
