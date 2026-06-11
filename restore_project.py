import json
import re
from pathlib import Path

report_path = Path("data/reports/project_1780937060.md")
backup_path = Path("data/memory/active_analyses_backup.json")

if not report_path.exists():
    print("Report file not found!")
    exit(1)

report_text = report_path.read_text(encoding="utf-8")

# Parse sections using regular expressions
def extract_section(text, start_header, next_header=None):
    try:
        start_idx = text.index(start_header) + len(start_header)
        if next_header:
            end_idx = text.index(next_header)
            return text[start_idx:end_idx].strip()
        else:
            return text[start_idx:].strip()
    except ValueError:
        return ""

research = extract_section(report_text, "## 🔬 Industry Analysis", "---")
market = extract_section(report_text, "## 📊 Market Analysis", "---")
competitors = extract_section(report_text, "## 🎯 Competitor Analysis", "---")
swot = extract_section(report_text, "## ⚡ SWOT Analysis", "---")
strategy = extract_section(report_text, "## 💡 Business Strategy & Recommendations", "---")

# Load existing backup
if backup_path.exists():
    with open(backup_path, "r", encoding="utf-8") as f:
        backup_data = json.load(f)
else:
    backup_data = {}

# Reconstruct state
state = {
    "project_id": "project_1780937060",
    "startup_idea": "Saas application for hotel booking",
    "research": research,
    "market_analysis": market,
    "competitors": competitors,
    "swot": swot,
    "business_strategy": strategy,
    "human_feedback": {},
    "research_plans": {},
    "research_traces": {},
    "research_metrics": {},
    "status": "awaiting_approval",
    "current_step": "human_approval",
    "execution_metrics": {
        "research": {"time_ms": 9832, "model_used": "poolside/laguna-xs.2:free"},
        "market_analysis": {"time_ms": 32622, "model_used": "poolside/laguna-xs.2:free"},
        "competitor_analysis": {"time_ms": 18273, "model_used": "poolside/laguna-xs.2:free"},
        "swot_analysis": {"time_ms": 10601, "model_used": "poolside/laguna-xs.2:free"}
    },
    "llm_routing_log": [
        {"task": "research", "provider": "openrouter", "model": "poolside/laguna-xs.2:free"},
        {"task": "market_analysis", "provider": "openrouter", "model": "poolside/laguna-xs.2:free"},
        {"task": "competitor_analysis", "provider": "openrouter", "model": "poolside/laguna-xs.2:free"},
        {"task": "swot_analysis", "provider": "openrouter", "model": "poolside/laguna-xs.2:free"}
    ],
    "memory_references": [],
    "errors": [],
    "report": report_text
}

backup_data["project_1780937060"] = {
    "state": state,
    "started_at": 1780937060
}

# Write back
with open(backup_path, "w", encoding="utf-8") as f:
    json.dump(backup_data, f, indent=2, ensure_ascii=False)

print("Project project_1780937060 reconstructed and saved to active_analyses_backup.json successfully!")
