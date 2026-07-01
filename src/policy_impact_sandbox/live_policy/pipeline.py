from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from policy_impact_sandbox.live_policy.generic_extract import extract_generic_case_graph
from policy_impact_sandbox.live_policy.report import generate_llm_impact_report
from policy_impact_sandbox.phase2.agents import generate_agent_profiles
from policy_impact_sandbox.phase2.audit import build_audit_manifest
from policy_impact_sandbox.phase2.simulation import run_policy_mock_simulation


class JSONLLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


NO_TRUTH_SET_STATUS = {
    "status": "unavailable",
    "message": "无历史回测数据，仅提供影响分析",
}


def run_policy_analysis(
    policy_text: str,
    llm_client: JSONLLMClient,
    run_id: str | None = None,
    agent_count: int = 12,
    rounds: int = 2,
) -> dict[str, Any]:
    if not policy_text.strip():
        raise ValueError("policy_text is required")

    run_id = run_id or "policy_run_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    case_graph = extract_generic_case_graph(policy_text=policy_text, llm_client=llm_client)
    target_count = max(agent_count, len(case_graph.get("stakeholders", [])))
    agents_payload = generate_agent_profiles(
        case_graph=case_graph,
        llm_client=llm_client,
        target_count=target_count,
    )
    simulation_result = run_policy_mock_simulation(
        agents_payload=agents_payload,
        run_id=run_id,
        rounds=rounds,
    )
    impact_report = generate_llm_impact_report(
        case_graph=case_graph,
        agents_payload=agents_payload,
        simulation_result=simulation_result,
        llm_client=llm_client,
    )
    artifacts = {
        "case_graph": ("inline:case_graph", case_graph),
        "agents": ("inline:agents", agents_payload),
        "simulation_events": ("inline:simulation_events", simulation_result),
        "impact_report": ("inline:impact_report", impact_report),
    }
    audit_manifest = build_audit_manifest(
        case_id=case_graph["case_id"],
        run_id=run_id,
        artifacts=artifacts,
    )
    return {
        "run_id": run_id,
        "mode": "live_policy_analysis",
        "truth_set_status": dict(NO_TRUTH_SET_STATUS),
        "case_graph": case_graph,
        "agents": agents_payload,
        "simulation_events": simulation_result,
        "impact_report": impact_report,
        "backtest_result": None,
        "audit_manifest": audit_manifest,
    }
