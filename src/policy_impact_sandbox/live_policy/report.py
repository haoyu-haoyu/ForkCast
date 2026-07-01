from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Protocol

from policy_impact_sandbox.phase2.json_utils import parse_json_object
from policy_impact_sandbox.simulation.mock import DECISION_SUPPORT_DISCLAIMER


class JSONLLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


PROMPT_PATH = Path("prompts/impact_report_generation.md")


def generate_llm_impact_report(
    case_graph: dict[str, Any],
    agents_payload: dict[str, Any],
    simulation_result: dict[str, Any],
    llm_client: JSONLLMClient,
) -> dict[str, Any]:
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    user_prompt = json.dumps(
        {
            "case_graph": case_graph,
            "agents": agents_payload.get("agents", []),
            "simulation_signals": simulation_result.get("signals", {}),
            "truth_set_available": False,
            "instruction": "Generate impact analysis only. Do not produce a historical backtest.",
        },
        ensure_ascii=False,
        indent=2,
    )
    parsed = parse_json_object(llm_client.complete_json(system_prompt=system_prompt, user_prompt=user_prompt))
    return {
        "case_id": case_graph["case_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": DECISION_SUPPORT_DISCLAIMER,
        "report_mode": "llm_policy_analysis_no_truth_set",
        "backtest_evidence": None,
        "method_note": "No historical truth_set was supplied; this report provides impact analysis only, not backtest validation.",
        "stakeholder_impact_matrix": _list(parsed.get("stakeholder_impact_matrix")),
        "risk_timeline": _list(parsed.get("risk_timeline")),
        "mitigation_options": _list(parsed.get("mitigation_options")),
        "confidence_notes": _string_list(parsed.get("confidence_notes"))
        or ["无历史回测数据，仅提供影响分析。"],
        "system_signals": {},
    }


def _list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
