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
    stakeholder_impact_matrix = _list(parsed.get("stakeholder_impact_matrix"))
    risk_timeline = _list(parsed.get("risk_timeline"))
    mitigation_options = _list(parsed.get("mitigation_options"))
    claims_audit_table = _normalize_claim_rows(
        _list(parsed.get("claims_audit_table")),
        stakeholder_impact_matrix=stakeholder_impact_matrix,
        risk_timeline=risk_timeline,
        mitigation_options=mitigation_options,
    )
    return {
        "case_id": case_graph["case_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": DECISION_SUPPORT_DISCLAIMER,
        "report_mode": "llm_policy_analysis_no_truth_set",
        "backtest_evidence": None,
        "method_note": "No historical truth_set was supplied; this report provides impact analysis only, not backtest validation.",
        "stakeholder_impact_matrix": stakeholder_impact_matrix,
        "risk_timeline": risk_timeline,
        "mitigation_options": mitigation_options,
        "confidence_notes": _string_list(parsed.get("confidence_notes"))
        or ["无历史回测数据，仅提供影响分析。"],
        "system_signals": {},
        "claims_audit_table": claims_audit_table,
    }


def _list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _normalize_claim_rows(
    rows: list[dict[str, Any]],
    stakeholder_impact_matrix: list[dict[str, Any]],
    risk_timeline: list[dict[str, Any]],
    mitigation_options: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalized = []
    allowed = {"DOCUMENT-CITED", "INFERRED-FROM-DOCUMENT", "MODEL-PRIOR"}
    for index, row in enumerate(rows, start=1):
        claim = str(row.get("claim") or row.get("statement") or "").strip()
        if not claim:
            continue
        provenance_class = str(row.get("provenance_class") or "INFERRED-FROM-DOCUMENT")
        if provenance_class not in allowed:
            provenance_class = "INFERRED-FROM-DOCUMENT"
        normalized.append(
            {
                "id": str(row.get("id") or f"claim_{index}"),
                "claim": claim,
                "provenance_class": provenance_class,
                "evidence_pointer": str(row.get("evidence_pointer") or "llm_report_context"),
                "evidence_fact_ids": [str(item) for item in row.get("evidence_fact_ids", [])],
                "source_artifact": str(row.get("source_artifact") or "impact_report_generation_context"),
                "confidence": str(row.get("confidence") or "medium"),
            }
        )
    return normalized or _fallback_claim_rows(stakeholder_impact_matrix, risk_timeline, mitigation_options)


def _fallback_claim_rows(
    stakeholder_impact_matrix: list[dict[str, Any]],
    risk_timeline: list[dict[str, Any]],
    mitigation_options: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in stakeholder_impact_matrix:
        if item.get("qualitative_signal"):
            rows.append(
                {
                    "id": f"stakeholder_{item.get('stakeholder_id', len(rows) + 1)}",
                    "claim": str(item["qualitative_signal"]),
                    "provenance_class": "INFERRED-FROM-DOCUMENT",
                    "evidence_pointer": f"case_graph.stakeholders.{item.get('stakeholder_id', 'unknown')}; simulation_events.signals",
                    "evidence_fact_ids": [],
                    "source_artifact": "case_graph.json + simulation_events.json",
                    "confidence": "medium",
                }
            )
    for item in risk_timeline:
        if item.get("signal"):
            rows.append(
                {
                    "id": f"risk_{item.get('stage', len(rows) + 1)}",
                    "claim": str(item["signal"]),
                    "provenance_class": "INFERRED-FROM-DOCUMENT",
                    "evidence_pointer": f"risk_timeline.{item.get('stage', 'unknown')}",
                    "evidence_fact_ids": [],
                    "source_artifact": "impact_report.json",
                    "confidence": "medium",
                }
            )
    for index, item in enumerate(mitigation_options, start=1):
        if item.get("rationale"):
            rows.append(
                {
                    "id": f"mitigation_{index}",
                    "claim": str(item["rationale"]),
                    "provenance_class": "MODEL-PRIOR",
                    "evidence_pointer": f"mitigation_options[{index - 1}]",
                    "evidence_fact_ids": [],
                    "source_artifact": "impact_report_generation_prompt",
                    "confidence": "low",
                }
            )
    return rows
