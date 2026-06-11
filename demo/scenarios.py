"""
StartupPilot AI — Demo Scenarios

Pre-cached demo scenarios that work WITHOUT an API key.
This is the highest-ROI feature: recruiters can click one button
and see the full system in action.

5 scenarios: AI Healthcare, FinTech, EdTech, SaaS, E-Commerce
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Quick Demo State Generator (must be before DEMO_SCENARIOS)
# ══════════════════════════════════════════════════════════════════════════════


def _quick_demo_state(project_id: str, startup_idea: str) -> dict[str, Any]:
    """Generate a simplified demo state for secondary scenarios."""
    return {
        "project_id": project_id,
        "startup_idea": startup_idea,
        "status": "completed",
        "current_step": "completed",
        "research": f"Industry research for '{startup_idea}' indicates a growing market with significant AI adoption opportunities. Key trends include digital transformation, increasing automation demand, and favorable regulatory environment.",
        "market_analysis": f"TAM: $25-50B globally. SAM: $5-10B in target markets. SOM: $50-100M achievable in 3-5 years. Growth rate: 12-18% CAGR. Primary segments: SMBs and mid-market enterprises.",
        "competitors": f"5-8 direct competitors identified with varying strengths. Key differentiation opportunity through AI-first approach and superior user experience. Most competitors lack advanced AI capabilities.",
        "swot": "**Strengths**: AI-native architecture, modern UX, agile team. **Weaknesses**: New brand, limited resources. **Opportunities**: Growing market, AI adoption wave. **Threats**: Large incumbents, regulatory changes.",
        "business_strategy": "SaaS subscription model with freemium tier. GTM: product-led growth + targeted outreach. MVP in 3 months, V1 in 6 months. Seed funding: $500K-1M.",
        "discussion_transcript": "Agents reached consensus: viability 7/10. Strong market opportunity with manageable technical risks. Recommended starting lean and validating with early customers.",
        "architecture": "Cloud-native architecture on AWS: ECS Fargate, RDS PostgreSQL, ElastiCache Redis, S3, CloudFront. Microservices pattern with API Gateway.",
        "cost_estimates": "MVP: $500-800/month. Growth: $2,000-4,000/month. Scale: $8,000-15,000/month. First year total: $10,000-20,000.",
        "execution_metrics": {
            "research": {"time_ms": 3500, "model_used": "llama-3.3-70b-versatile", "provider": "groq"},
            "market_analysis": {"time_ms": 3200, "model_used": "llama-3.3-70b-versatile", "provider": "groq"},
            "business_strategy": {"time_ms": 4800, "model_used": "gpt-4o", "provider": "openai"},
        },
        "llm_routing_log": [
            {"task": "research", "provider": "groq", "model": "llama-3.3-70b-versatile"},
            {"task": "business_strategy", "provider": "openai", "model": "gpt-4o"},
        ],
        "human_feedback": {"action": "approve", "comments": ""},
        "errors": [],
        "memory_references": [],
        "diagrams": {},
        "report": "",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Demo Scenario Definitions
# ══════════════════════════════════════════════════════════════════════════════

DEMO_SCENARIOS: dict[str, dict[str, Any]] = {
    "ai-healthcare": {
        "id": "demo-healthcare",
        "name": "AI Healthcare Scheduling",
        "startup_idea": "AI-powered healthcare appointment scheduling platform",
        "icon": "🏥",
        "description": "An AI platform that optimizes healthcare appointment scheduling using NLP and predictive analytics.",
        "state": {
            "project_id": "demo-healthcare",
            "startup_idea": "AI-powered healthcare appointment scheduling platform",
            "status": "completed",
            "current_step": "completed",
            "research": (
                "## Industry Overview\n\n"
                "The healthcare scheduling market is experiencing rapid digital transformation. "
                "The global healthcare IT market is projected to reach $390.7 billion by 2028, "
                "growing at a CAGR of 13.3% (Grand View Research, 2023).\n\n"
                "### Key Trends\n"
                "- **AI adoption in healthcare**: 86% of healthcare organizations use AI (Accenture)\n"
                "- **Patient experience focus**: 70% of patients prefer digital scheduling (MGMA)\n"
                "- **No-show reduction**: AI reduces no-shows by 25-30% (Journal of Medical Internet Research)\n"
                "- **Telehealth integration**: 37% of visits remain virtual post-pandemic\n"
                "- **Value-based care**: Shift from fee-for-service to outcomes-based models\n\n"
                "### Regulatory Landscape\n"
                "- HIPAA compliance is mandatory for patient data\n"
                "- ONC interoperability rules require open APIs\n"
                "- FDA guidance on Clinical Decision Support software\n\n"
                "### Technology Enablers\n"
                "- NLP for patient intake and triage\n"
                "- Predictive analytics for demand forecasting\n"
                "- EHR integration via FHIR/HL7 standards\n"
                "- Real-time calendar synchronization"
            ),
            "market_analysis": (
                "## Market Opportunity\n\n"
                "### TAM (Total Addressable Market)\n"
                "$45.2 billion — Global healthcare scheduling and workflow optimization market\n\n"
                "### SAM (Serviceable Addressable Market)\n"
                "$8.5 billion — US & Europe AI-powered scheduling specifically\n\n"
                "### SOM (Serviceable Obtainable Market)\n"
                "$85 million — Achievable in 3-5 years targeting mid-size practices\n\n"
                "### Growth Rate\n"
                "15.8% CAGR (2024-2030)\n\n"
                "### Customer Segments\n"
                "1. **Mid-size medical practices** (10-50 providers) — Primary target\n"
                "2. **Hospital outpatient departments** — Enterprise segment\n"
                "3. **Multi-location dental/vision chains** — Niche segment\n"
                "4. **Telehealth platforms** — Partnership opportunity\n\n"
                "### Pricing Benchmarks\n"
                "- Per-provider per month: $200-500\n"
                "- Enterprise: $5,000-20,000/month\n"
                "- Industry average: $350/provider/month\n\n"
                "### Revenue Model\n"
                "SaaS subscription (per-provider pricing) + premium AI features tier"
            ),
            "competitors": (
                "## Competitive Landscape\n\n"
                "### Direct Competitors\n\n"
                "| Company | Funding | Strengths | Weaknesses |\n"
                "|---------|---------|-----------|------------|\n"
                "| Zocdoc | $375M | Brand recognition, patient marketplace | High CAC, limited AI |\n"
                "| Doctolib | $560M (EU) | European market leader | Limited US presence |\n"
                "| Nexhealth | $42M | API-first, modern UI | Small market share |\n"
                "| Luma Health | $36M | Patient engagement focus | Limited AI scheduling |\n"
                "| Qventus | $95M | AI-powered operations | Enterprise-only, expensive |\n\n"
                "### Competitive Advantages\n"
                "- **AI-first approach**: Purpose-built AI vs. bolted-on features\n"
                "- **Predictive no-show prevention**: Unique ML model\n"
                "- **Mid-market focus**: Underserved by enterprise solutions\n"
                "- **Modern API-first architecture**: Faster EHR integration"
            ),
            "swot": (
                "## SWOT Analysis\n\n"
                "### Strengths\n"
                "- AI-native architecture with predictive capabilities\n"
                "- Focus on underserved mid-market segment\n"
                "- Modern tech stack enabling rapid iteration\n"
                "- Lower CAC than marketplace models\n"
                "- FHIR-compliant API-first design\n\n"
                "### Weaknesses\n"
                "- No existing customer base or brand\n"
                "- Healthcare sales cycles are long (6-12 months)\n"
                "- HIPAA compliance adds development overhead\n"
                "- Requires EHR integration for each customer\n"
                "- Limited training data initially\n\n"
                "### Opportunities\n"
                "- Growing AI adoption in healthcare\n"
                "- Post-pandemic digital health acceleration\n"
                "- Value-based care driving efficiency demand\n"
                "- Potential for international expansion\n"
                "- Adjacent features: patient engagement, analytics\n\n"
                "### Threats\n"
                "- EHR vendors adding scheduling features\n"
                "- Regulatory changes (HIPAA, state laws)\n"
                "- Economic downturn reducing IT budgets\n"
                "- Large competitors acquiring AI capabilities\n"
                "- Data privacy concerns limiting AI adoption\n\n"
                "### Key Recommendations\n"
                "1. **Start with 3-5 pilot clinics** to build case studies\n"
                "2. **Focus on no-show reduction ROI** as primary selling point\n"
                "3. **Build HIPAA compliance from day one** — don't retrofit"
            ),
            "business_strategy": (
                "## Business Strategy\n\n"
                "### Value Proposition\n"
                "Reduce patient no-shows by 30% and increase scheduling efficiency by 40% "
                "through AI-powered predictive scheduling.\n\n"
                "### Business Model\n"
                "- **Starter**: $199/provider/month (basic AI scheduling)\n"
                "- **Professional**: $349/provider/month (predictive + analytics)\n"
                "- **Enterprise**: Custom pricing (full platform + integrations)\n\n"
                "### Go-to-Market Strategy\n"
                "1. Phase 1 (Months 1-6): 10 pilot clinics via direct sales\n"
                "2. Phase 2 (Months 6-12): 50 customers via channel partnerships\n"
                "3. Phase 3 (Year 2): 200 customers, launch self-serve tier\n\n"
                "### Product Roadmap\n"
                "- **MVP (Month 1-3)**: AI scheduling, EHR integration, patient reminders\n"
                "- **V1 (Month 4-6)**: Predictive no-shows, analytics dashboard\n"
                "- **V2 (Month 7-12)**: Multi-location, telehealth integration, API marketplace\n\n"
                "### Key Metrics\n"
                "- North Star: Monthly scheduled appointments per provider\n"
                "- No-show reduction rate\n"
                "- Monthly recurring revenue (MRR)\n"
                "- Net Revenue Retention (NRR)\n"
                "- Time to integrate (onboarding velocity)"
            ),
            "discussion_transcript": (
                "**Discussion_Moderator**: Let's evaluate: 'AI-powered healthcare appointment scheduling platform'\n\n---\n\n"
                "**Business_Consultant**: This is a strong opportunity. The healthcare scheduling market "
                "is fragmented with no dominant AI-first player in the mid-market. The $85M SOM is "
                "achievable with focused execution. Key risk: long sales cycles. Recommendation: start "
                "with dental/vision chains (shorter sales cycles) then expand to medical practices. "
                "Overall viability: 8/10.\n\n---\n\n"
                "**Cloud_Architect**: Technically feasible with modern cloud architecture. "
                "I recommend starting with AWS ECS Fargate for the API layer, RDS PostgreSQL for data, "
                "and SageMaker for ML models. HIPAA compliance requires dedicated infrastructure — "
                "expect $3,000-5,000/month baseline. The main technical risk is EHR integration "
                "complexity — each EHR system has different APIs. Suggest partnering with an integration "
                "platform like Redox or Health Gorilla.\n\n---\n\n"
                "**Financial_Analyst**: Unit economics look favorable. At $349/provider/month with "
                "50 providers, MRR = $17,450. Infrastructure costs of $5,000/month means 71% gross "
                "margin. Break-even at approximately 15 providers (assuming 2 FTEs). First-year "
                "infrastructure: $60,000-80,000. Recommend raising a $500K pre-seed to fund 12 months "
                "of runway. Cost optimization: use reserved instances and spot for ML training.\n\n---\n\n"
                "**Business_Consultant**: Agreed on unit economics. I'd add: focus on proving 30% "
                "no-show reduction in pilots — that's the ROI story that sells. Each no-show costs "
                "a practice $200 on average. For a 10-provider clinic with 5% no-show rate, that's "
                "$100K/year in lost revenue. Our solution paying for itself 2-3x over.\n\n---\n\n"
                "**Consensus**: Viability 8/10. Strengths: clear ROI, growing market, feasible tech. "
                "Risks: sales cycle length, EHR integration. Next steps: build MVP, sign 3-5 pilots, "
                "prove no-show reduction metric."
            ),
            "architecture": (
                "## Cloud Architecture\n\n"
                "### Technology Stack\n"
                "- **Frontend**: React + Next.js (HIPAA-compliant hosting on Vercel or AWS Amplify)\n"
                "- **Backend**: Python FastAPI (async, high-performance)\n"
                "- **Database**: PostgreSQL (RDS) + Redis (ElastiCache)\n"
                "- **ML/AI**: AWS SageMaker for scheduling models, OpenAI API for NLP\n"
                "- **Integration**: Redox for EHR connectivity (FHIR/HL7)\n"
                "- **Queue**: SQS for async processing\n"
                "- **Storage**: S3 for documents, CloudWatch for monitoring\n\n"
                "### Security\n"
                "- AWS HIPAA-eligible services only\n"
                "- End-to-end encryption (TLS 1.3 + AES-256 at rest)\n"
                "- BAA with all cloud providers\n"
                "- SOC 2 Type II compliance roadmap"
            ),
            "cost_estimates": (
                "## Infrastructure Cost Estimates\n\n"
                "### MVP Stage (0-1K users)\n"
                "| Service | Monthly Cost |\n|---|---|\n"
                "| ECS Fargate (2 services) | $150 |\n"
                "| RDS PostgreSQL (db.t3.medium) | $130 |\n"
                "| ElastiCache Redis (cache.t3.micro) | $25 |\n"
                "| S3 + CloudFront | $20 |\n"
                "| SageMaker (inference) | $200 |\n"
                "| OpenAI API | $100 |\n"
                "| Monitoring & Logging | $50 |\n"
                "| **Total** | **$675/month** |\n\n"
                "### Growth Stage (1K-10K users)\n"
                "| Service | Monthly Cost |\n|---|---|\n"
                "| ECS Fargate (auto-scaling) | $500 |\n"
                "| RDS PostgreSQL (db.r5.large) | $350 |\n"
                "| ElastiCache Redis (cache.r5.large) | $180 |\n"
                "| SageMaker (dedicated endpoint) | $600 |\n"
                "| OpenAI API | $400 |\n"
                "| Other | $200 |\n"
                "| **Total** | **$2,230/month** |\n\n"
                "### First Year Total: ~$15,000-25,000\n\n"
                "### Optimization Tips\n"
                "- Use reserved instances for RDS (save 30-40%)\n"
                "- Implement caching aggressively to reduce AI API calls\n"
                "- Use SageMaker Serverless for intermittent inference"
            ),
            "execution_metrics": {
                "research": {"time_ms": 4200, "model_used": "llama-3.3-70b-versatile", "provider": "groq"},
                "market_analysis": {"time_ms": 3800, "model_used": "llama-3.3-70b-versatile", "provider": "groq"},
                "competitor_analysis": {"time_ms": 4500, "model_used": "llama-3.3-70b-versatile", "provider": "groq"},
                "swot_analysis": {"time_ms": 3200, "model_used": "llama-3.3-70b-versatile", "provider": "groq"},
                "business_strategy": {"time_ms": 5100, "model_used": "gpt-4o", "provider": "openai"},
                "autogen_discussion": {"time_ms": 12000, "rounds": 5},
                "architecture_design": {"time_ms": 4800, "model_used": "gpt-4o", "provider": "openai"},
                "cost_estimation": {"time_ms": 3500, "model_used": "gpt-4o-mini", "provider": "openai"},
                "report_generation": {"time_ms": 1200},
            },
            "llm_routing_log": [
                {"task": "research", "provider": "groq", "model": "llama-3.3-70b-versatile"},
                {"task": "market_analysis", "provider": "groq", "model": "llama-3.3-70b-versatile"},
                {"task": "competitor_analysis", "provider": "groq", "model": "llama-3.3-70b-versatile"},
                {"task": "swot_analysis", "provider": "groq", "model": "llama-3.3-70b-versatile"},
                {"task": "business_strategy", "provider": "openai", "model": "gpt-4o"},
                {"task": "architecture_design", "provider": "openai", "model": "gpt-4o"},
                {"task": "cost_estimation", "provider": "openai", "model": "gpt-4o-mini"},
            ],
            "human_feedback": {"action": "approve", "comments": "Looks good, proceed."},
            "errors": [],
            "memory_references": [],
            "diagrams": {},
            "report": "",
            "research_plans": {
                "research": {
                    "project_id": "demo-healthcare",
                    "startup_idea": "AI-powered healthcare appointment scheduling platform",
                    "agent_type": "research",
                    "sub_questions": [
                        {"question_id": "q1", "text": "What are the core industry dynamics and growth drivers?", "target_pages": ["topic_industry_overview"], "status": "completed"},
                        {"question_id": "q2", "text": "What is the regulatory and compliance landscape?", "target_pages": ["topic_regulatory_landscape"], "status": "completed"}
                    ],
                    "created_at": "2026-06-04T07:00:00Z"
                },
                "market_analysis": {
                    "project_id": "demo-healthcare",
                    "startup_idea": "AI-powered healthcare appointment scheduling platform",
                    "agent_type": "market_analysis",
                    "sub_questions": [
                        {"question_id": "q1", "text": "What is the addressable market size (TAM/SAM/SOM)?", "target_pages": ["topic_market_opportunity"], "status": "completed"}
                    ],
                    "created_at": "2026-06-04T07:00:00Z"
                },
                "competitor_analysis": {
                    "project_id": "demo-healthcare",
                    "startup_idea": "AI-powered healthcare appointment scheduling platform",
                    "agent_type": "competitor_analysis",
                    "sub_questions": [
                        {"question_id": "q1", "text": "Who are the direct and indirect competitors?", "target_pages": ["entity_zocdoc", "entity_doctolib", "entity_nexhealth"], "status": "completed"}
                    ],
                    "created_at": "2026-06-04T07:00:00Z"
                }
            },
            "research_traces": {
                "research": {
                    "project_id": "demo-healthcare",
                    "agent_type": "research",
                    "navigation_path": ["topic_industry_overview", "topic_regulatory_landscape", "entity_hipaa"],
                    "evidence_gathered": [
                        {
                            "evidence_id": "ev-r1",
                            "page_id": "topic_industry_overview",
                            "title_or_name": "Healthcare Scheduling Industry Overview",
                            "fact": "Healthcare IT market projected to reach $390.7B by 2028, growing at a CAGR of 13.3%.",
                            "relevance_reasoning": "Establishes macro industry tailwinds.",
                            "timestamp": "2026-06-04T07:00:05Z"
                        },
                        {
                            "evidence_id": "ev-r2",
                            "page_id": "topic_regulatory_landscape",
                            "title_or_name": "HIPAA Regulatory Compliance",
                            "fact": "Compliance with the Health Insurance Portability and Accountability Act (HIPAA) is mandatory for patient data handling.",
                            "relevance_reasoning": "Identifies legal compliance constraint.",
                            "timestamp": "2026-06-04T07:00:10Z"
                        },
                        {
                            "evidence_id": "ev-r3",
                            "page_id": "entity_hipaa",
                            "title_or_name": "HIPAA",
                            "fact": "HIPAA requires end-to-end encryption of Protected Health Information (PHI) and signing BAAs with cloud hosts.",
                            "relevance_reasoning": "Provides operational rules for architecture design.",
                            "timestamp": "2026-06-04T07:00:15Z"
                        }
                    ],
                    "reasoning_chain": [
                        "[topic_industry_overview] Starting research. Analyzing general healthcare scheduling industry trends.",
                        "[topic_regulatory_landscape] Identified PHI encryption and BAA requirements. Hopping to regulatory landscape.",
                        "[entity_hipaa] Regulatory landscape references HIPAA compliance requirements. Traversing to HIPAA entity page."
                    ],
                    "depth": 3,
                    "metrics": {"pages_explored": 3, "evidence_count": 3, "success": True, "max_depth": 3}
                },
                "market_analysis": {
                    "project_id": "demo-healthcare",
                    "agent_type": "market_analysis",
                    "navigation_path": ["topic_market_opportunity"],
                    "evidence_gathered": [
                        {
                            "evidence_id": "ev-m1",
                            "page_id": "topic_market_opportunity",
                            "title_or_name": "AI Healthcare Market Opportunity",
                            "fact": "TAM is $45.2 Billion globally, SAM is $8.5 Billion in US & Europe, and SOM is $85 Million targeting mid-size practices.",
                            "relevance_reasoning": "Establishes addressable market boundaries.",
                            "timestamp": "2026-06-04T07:00:20Z"
                        }
                    ],
                    "reasoning_chain": [
                        "[topic_market_opportunity] Analyzing market sizing and opportunities for AI scheduling."
                    ],
                    "depth": 1,
                    "metrics": {"pages_explored": 1, "evidence_count": 1, "success": True, "max_depth": 1}
                },
                "competitor_analysis": {
                    "project_id": "demo-healthcare",
                    "agent_type": "competitor_analysis",
                    "navigation_path": ["entity_zocdoc", "entity_doctolib", "entity_nexhealth"],
                    "evidence_gathered": [
                        {
                            "evidence_id": "ev-c1",
                            "page_id": "entity_zocdoc",
                            "title_or_name": "Zocdoc",
                            "fact": "Zocdoc raised $375M, has high brand recognition but suffers from high CAC and limited AI.",
                            "relevance_reasoning": "Evaluates incumbent market leader.",
                            "timestamp": "2026-06-04T07:00:25Z"
                        },
                        {
                            "evidence_id": "ev-c2",
                            "page_id": "entity_doctolib",
                            "title_or_name": "Doctolib",
                            "fact": "Doctolib is the European leader with $560M funding, but has very limited US presence.",
                            "relevance_reasoning": "Identifies geographic competitor boundaries.",
                            "timestamp": "2026-06-04T07:00:30Z"
                        },
                        {
                            "evidence_id": "ev-c3",
                            "page_id": "entity_nexhealth",
                            "title_or_name": "Nexhealth",
                            "fact": "Nexhealth is API-first with $42M funding, but has a small market share compared to incumbents.",
                            "relevance_reasoning": "Evaluates developer-friendly niche threat.",
                            "timestamp": "2026-06-04T07:00:35Z"
                        }
                    ],
                    "reasoning_chain": [
                        "[entity_zocdoc] Analyzing first competitor Zocdoc, checking funding and strengths.",
                        "[entity_doctolib] Hopping to Doctolib to evaluate European competitor.",
                        "[entity_nexhealth] Hopping to Nexhealth to evaluate developer-friendly API-first competitor."
                    ],
                    "depth": 3,
                    "metrics": {"pages_explored": 3, "evidence_count": 3, "success": True, "max_depth": 3}
                }
            },
            "research_metrics": {
                "research": {"pages_explored": 3, "evidence_count": 3, "success": True, "max_depth": 3},
                "market_analysis": {"pages_explored": 1, "evidence_count": 1, "success": True, "max_depth": 1},
                "competitor_analysis": {"pages_explored": 3, "evidence_count": 3, "success": True, "max_depth": 3}
            },
            "report": "",
        },
    },

    "fintech": {
        "id": "demo-fintech",
        "name": "FinTech Micro-Lending",
        "startup_idea": "Blockchain-based micro-lending platform for small businesses",
        "icon": "💳",
        "description": "A decentralized lending platform connecting small business borrowers with individual lenders.",
        "state": _quick_demo_state(
            "demo-fintech",
            "Blockchain-based micro-lending platform for small businesses",
        ),
    },

    "edtech": {
        "id": "demo-edtech",
        "name": "AI Tutoring Platform",
        "startup_idea": "AI tutor for personalized K-12 education",
        "icon": "📚",
        "description": "Personalized AI tutoring system that adapts to each student's learning style.",
        "state": _quick_demo_state(
            "demo-edtech",
            "AI tutor for personalized K-12 education",
        ),
    },

    "saas": {
        "id": "demo-saas",
        "name": "No-Code Workflow Automation",
        "startup_idea": "No-code workflow automation platform for enterprises",
        "icon": "⚙️",
        "description": "Enterprise workflow automation platform with drag-and-drop AI-powered builders.",
        "state": _quick_demo_state(
            "demo-saas",
            "No-code workflow automation platform for enterprises",
        ),
    },

    "ecommerce": {
        "id": "demo-ecommerce",
        "name": "AI Visual Product Search",
        "startup_idea": "AI-powered visual product search engine for e-commerce",
        "icon": "🛒",
        "description": "Image-based product search that lets shoppers find products by taking photos.",
        "state": _quick_demo_state(
            "demo-ecommerce",
            "AI-powered visual product search engine for e-commerce",
        ),
    },
}



# ══════════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════════


def get_demo_scenarios() -> list[dict]:
    """List all available demo scenarios."""
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "startup_idea": s["startup_idea"],
            "icon": s["icon"],
            "description": s["description"],
        }
        for s in DEMO_SCENARIOS.values()
    ]


def get_demo_result(project_id: str) -> Optional[dict[str, Any]]:
    """Get a demo result by project_id.

    Returns the full demo state if found, None otherwise.
    """
    for scenario in DEMO_SCENARIOS.values():
        if scenario["id"] == project_id:
            return dict(scenario["state"])
    return None


def ensure_demo_wiki(project_id: str) -> None:
    """Ensure that the pre-compiled wiki exists for the demo project."""
    if project_id != "demo-healthcare":
        return

    import json
    from pathlib import Path
    from config import get_settings

    settings = get_settings()
    wiki_dir = Path(settings.wiki_dir) / project_id
    wiki_dir.mkdir(parents=True, exist_ok=True)

    wiki_file = wiki_dir / "wiki.json"
    if wiki_file.exists():
        return

    demo_wiki_data = {
      "project_id": "demo-healthcare",
      "topic_pages": {
        "topic_industry_overview": {
          "page_id": "topic_industry_overview",
          "title": "Healthcare Scheduling Industry Overview",
          "category": "industry",
          "summary": "Overview of the digital transformation in the healthcare scheduling sector.",
          "content": "## Healthcare Scheduling Industry\\n\\nThe healthcare scheduling market is experiencing rapid digital transformation. The global healthcare IT market is projected to reach $390.7 billion by 2028, growing at a CAGR of 13.3%. Key drivers include the need for operational efficiency, reducing patient no-shows, and improving patient engagement.",
          "key_facts": [
            "Healthcare IT market projected to reach $390.7B by 2028",
            "Growing at a CAGR of 13.3%",
            "86% of healthcare organizations use AI in some form"
          ],
          "related_entities": ["entity_zocdoc", "entity_doctolib", "entity_nexhealth"],
          "related_topics": ["topic_market_opportunity"],
          "source_chunks": ["agent:research"],
          "source_type": "agent",
          "confidence": 0.95,
          "version": 1
        },
        "topic_regulatory_landscape": {
          "page_id": "topic_regulatory_landscape",
          "title": "HIPAA Regulatory Compliance",
          "category": "regulation",
          "summary": "Mandatory regulatory requirements for handling Protected Health Information (PHI) in scheduling platforms.",
          "content": "## Regulatory Compliance in Healthcare IT\\n\\nCompliance with the Health Insurance Portability and Accountability Act (HIPAA) is mandatory for any patient data handling in the US. This requires end-to-end encryption of PHI, signing Business Associate Agreements (BAAs) with cloud providers, and maintaining detailed audit logs.",
          "key_facts": [
            "HIPAA compliance is mandatory for PHI",
            "Requires BAAs with all cloud hosts",
            "Requires end-to-end encryption (AES-256 and TLS 1.3)"
          ],
          "related_entities": ["entity_hipaa"],
          "related_topics": ["topic_industry_overview"],
          "source_chunks": ["agent:research"],
          "source_type": "agent",
          "confidence": 0.95,
          "version": 1
        },
        "topic_market_opportunity": {
          "page_id": "topic_market_opportunity",
          "title": "AI Healthcare Market Opportunity",
          "category": "market",
          "summary": "Financial and market sizing analysis for AI-powered scheduling platforms.",
          "content": "## Market Sizing and Segments\\n\\n- **TAM (Total Addressable Market)**: $45.2 Billion globally for healthcare scheduling and workflow optimization.\\n- **SAM (Serviceable Addressable Market)**: $8.5 Billion in US & Europe for AI-specific scheduling.\\n- **SOM (Serviceable Obtainable Market)**: $85 Million targeting mid-size practices within 3-5 years.",
          "key_facts": [
            "TAM: $45.2B globally",
            "SAM: $8.5B in US & Europe",
            "SOM: $85M within 3-5 years",
            "15.8% CAGR (2024-2030)"
          ],
          "related_entities": ["entity_zocdoc", "entity_doctolib", "entity_nexhealth"],
          "related_topics": ["topic_industry_overview"],
          "source_chunks": ["agent:market_analysis"],
          "source_type": "agent",
          "confidence": 0.95,
          "version": 1
        }
      },
      "entity_pages": {
        "entity_zocdoc": {
          "page_id": "entity_zocdoc",
          "name": "Zocdoc",
          "entity_type": "company",
          "summary": "A major patient scheduling marketplace with strong brand recognition.",
          "attributes": {
            "funding": "$375M",
            "founded": "2007",
            "strength": "High brand awareness, active patient marketplace",
            "weakness": "High customer acquisition costs (CAC), limited AI capabilities"
          },
          "mentions": [
            {"source": "agent:competitor_analysis", "context_snippet": "Zocdoc has raised $375M and has high brand recognition but suffers from high CAC."}
          ],
          "related_entities": ["entity_doctolib", "entity_nexhealth"],
          "related_topics": ["topic_market_opportunity"],
          "source_chunks": ["agent:competitor_analysis"],
          "source_type": "agent",
          "confidence": 0.95,
          "version": 1
        },
        "entity_doctolib": {
          "page_id": "entity_doctolib",
          "name": "Doctolib",
          "entity_type": "company",
          "summary": "The dominant healthcare scheduling and teleconsultation platform in Europe.",
          "attributes": {
            "funding": "$560M",
            "hq": "Paris, France",
            "strength": "Market leader in Europe, strong hospital integrations",
            "weakness": "Very limited US presence"
          },
          "mentions": [
            {"source": "agent:competitor_analysis", "context_snippet": "Doctolib is the European market leader with over $560M in funding."}
          ],
          "related_entities": ["entity_zocdoc"],
          "related_topics": ["topic_market_opportunity"],
          "source_chunks": ["agent:competitor_analysis"],
          "source_type": "agent",
          "confidence": 0.95,
          "version": 1
        },
        "entity_nexhealth": {
          "page_id": "entity_nexhealth",
          "name": "Nexhealth",
          "entity_type": "company",
          "summary": "An API-first patient experience platform for EHR integration.",
          "attributes": {
            "funding": "$42M",
            "strength": "API-first developer-friendly, modern UI components",
            "weakness": "Small market share compared to incumbents"
          },
          "mentions": [
            {"source": "agent:competitor_analysis", "context_snippet": "Nexhealth focuses on API-first EHR integration with $42M funding."}
          ],
          "related_entities": ["entity_zocdoc"],
          "related_topics": ["topic_market_opportunity"],
          "source_chunks": ["agent:competitor_analysis"],
          "source_type": "agent",
          "confidence": 0.95,
          "version": 1
        },
        "entity_hipaa": {
          "page_id": "entity_hipaa",
          "name": "HIPAA",
          "entity_type": "regulation",
          "summary": "Health Insurance Portability and Accountability Act of 1996.",
          "attributes": {
            "jurisdiction": "United States",
            "requirements": "PHI encryption, BAA agreements, access controls"
          },
          "mentions": [
            {"source": "agent:research", "context_snippet": "HIPAA compliance is mandatory for protecting patient data."}
          ],
          "related_entities": [],
          "related_topics": ["topic_regulatory_landscape"],
          "source_chunks": ["agent:research"],
          "source_type": "agent",
          "confidence": 0.98,
          "version": 1
        }
      },
      "index": {
        "topic_index": {
          "industry": ["topic_industry_overview"],
          "regulation": ["topic_regulatory_landscape"],
          "market": ["topic_market_opportunity"]
        },
        "entity_index": {
          "company": ["entity_zocdoc", "entity_doctolib", "entity_nexhealth"],
          "regulation": ["entity_hipaa"]
        },
        "keyword_index": {
          "healthcare": ["topic_industry_overview", "topic_market_opportunity", "entity_doctolib"],
          "scheduling": ["topic_industry_overview", "topic_market_opportunity"],
          "market": ["topic_industry_overview", "topic_market_opportunity", "entity_zocdoc", "entity_doctolib", "entity_nexhealth"],
          "compliance": ["topic_regulatory_landscape", "entity_hipaa"],
          "hipaa": ["topic_regulatory_landscape", "entity_hipaa"],
          "funding": ["entity_zocdoc", "entity_doctolib", "entity_nexhealth"]
        },
        "cross_references": {
          "topic_industry_overview": ["entity_zocdoc", "entity_doctolib", "entity_nexhealth", "topic_market_opportunity", "topic_regulatory_landscape"],
          "topic_regulatory_landscape": ["entity_hipaa", "topic_industry_overview"],
          "topic_market_opportunity": ["entity_zocdoc", "entity_doctolib", "topic_industry_overview"],
          "entity_zocdoc": ["entity_doctolib", "entity_nexhealth", "topic_market_opportunity", "topic_industry_overview"],
          "entity_doctolib": ["entity_zocdoc", "topic_market_opportunity", "topic_industry_overview"],
          "entity_nexhealth": ["entity_zocdoc", "topic_market_opportunity", "topic_industry_overview"],
          "entity_hipaa": ["topic_regulatory_landscape"]
        }
      },
      "compilation_count": 1
    }

    try:
        wiki_file.write_text(json.dumps(demo_wiki_data, indent=2), encoding="utf-8")
        logger.info("Pre-compiled demo wiki written for %s", project_id)
    except Exception as e:
        logger.error("Failed to write demo wiki: %s", e)


def run_demo(scenario_key: str) -> dict[str, Any]:
    """Run a demo scenario (returns cached results instantly).

    Args:
        scenario_key: One of "ai-healthcare", "fintech", "edtech", "saas", "ecommerce"

    Returns:
        The complete demo state.
    """
    if scenario_key not in DEMO_SCENARIOS:
        raise ValueError(
            f"Unknown demo scenario: {scenario_key}. "
            f"Available: {list(DEMO_SCENARIOS.keys())}"
        )

    scenario = DEMO_SCENARIOS[scenario_key]
    state = dict(scenario["state"])

    # Generate report if not cached
    if not state.get("report"):
        from reports.generator import generate_report
        state["report"] = generate_report(state)

    # Generate diagrams if not cached
    if not state.get("diagrams"):
        from reports.diagrams import generate_diagrams
        state["diagrams"] = generate_diagrams(state)

    # Ensure pre-compiled wiki is written
    ensure_demo_wiki(state["project_id"])

    logger.info("Demo scenario '%s' loaded.", scenario_key)
    return state
