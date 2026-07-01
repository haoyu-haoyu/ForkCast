from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

from dotenv import load_dotenv
from jsonschema import Draft202012Validator

from policy_impact_sandbox.llm import LLMConfig, MissingLLMConfig, OpenAICompatibleLLMClient
from policy_impact_sandbox.phase2.agents import DeterministicAgentLLMClient, generate_agent_profiles
from policy_impact_sandbox.phase2.audit import build_audit_manifest
from policy_impact_sandbox.phase2.backtest import evaluate_blind_prediction_backtest, render_backtest_markdown
from policy_impact_sandbox.phase2.blind_prediction import DeterministicBlindLLMClient, generate_blind_prediction
from policy_impact_sandbox.phase2.chat import answer_persona_question
from policy_impact_sandbox.phase2.report import generate_impact_report, render_impact_report_markdown
from policy_impact_sandbox.phase2.simulation import run_policy_mock_simulation
from policy_impact_sandbox.simulation.mock import DECISION_SUPPORT_DISCLAIMER


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run Phase 2 archetypes, mock simulation, report, backtest and audit.")
    parser.add_argument("--case-graph", default="data/cases/ulez_2023/case_graph.json")
    parser.add_argument("--truth-set", default="data/cases/ulez_2023/truth_set.json")
    parser.add_argument("--run-id", default=_default_run_id())
    parser.add_argument("--run-dir", default=None)
    parser.add_argument("--agent-count", type=int, default=36)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--mock-llm", action="store_true")
    args = parser.parse_args()

    case_graph = _read_json(Path(args.case_graph))
    truth_set = _read_json(Path(args.truth_set))
    run_dir = Path(args.run_dir) if args.run_dir else Path("runs") / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if args.mock_llm:
        llm_client = DeterministicAgentLLMClient()
        blind_llm_client = DeterministicBlindLLMClient()
        llm_metadata = {"provider": "mock", "base_url": None, "model": "deterministic_mock"}
    else:
        try:
            llm_config = LLMConfig.from_env()
            llm_client = OpenAICompatibleLLMClient(llm_config)
            blind_llm_client = llm_client
            llm_metadata = {
                "provider": llm_config.provider,
                "base_url": llm_config.base_url,
                "model": llm_config.model,
            }
        except MissingLLMConfig as exc:
            print(str(exc), file=sys.stderr)
            return 2

    simulation_config = {
        "case_id": case_graph["case_id"],
        "mode": "mock",
        "agent_count": args.agent_count,
        "rounds": args.rounds,
        "random_seed": 20260701,
        "decision_support_disclaimer": DECISION_SUPPORT_DISCLAIMER,
        "oasis_live": False,
    }
    _validate("schemas/simulation_config.schema.json", simulation_config)

    agents_payload = generate_agent_profiles(
        case_graph=case_graph,
        llm_client=llm_client,
        target_count=args.agent_count,
    )
    agents_payload["llm"] = llm_metadata
    _validate("schemas/agents.schema.json", agents_payload)

    blind_prediction = generate_blind_prediction(
        case_graph=case_graph,
        llm_client=blind_llm_client,
        llm_metadata=llm_metadata,
    )
    _validate("schemas/blind_prediction.schema.json", blind_prediction)
    simulation_result = run_policy_mock_simulation(
        agents_payload=agents_payload,
        run_id=args.run_id,
        rounds=args.rounds,
    )
    impact_report = generate_impact_report(
        case_graph=case_graph,
        agents_payload=agents_payload,
        simulation_result=simulation_result,
    )
    backtest_result = evaluate_blind_prediction_backtest(blind_prediction=blind_prediction, truth_set=truth_set)
    persona_chat = answer_persona_question(
        _select_chat_agent(agents_payload["agents"]),
        "Why do you support or oppose this policy?",
    )

    artifacts: dict[str, tuple[str, Any]] = {
        "case_graph": (args.case_graph, case_graph),
        "simulation_config": (str(run_dir / "simulation_config.json"), simulation_config),
        "agents": (str(run_dir / "agents.json"), agents_payload),
        "blind_prediction": (str(run_dir / "blind_prediction.json"), blind_prediction),
        "simulation_events": (str(run_dir / "simulation_events.json"), simulation_result),
        "impact_report": (str(run_dir / "impact_report.json"), impact_report),
        "backtest_result": (str(run_dir / "backtest_result.json"), backtest_result),
        "persona_chat_sample": (str(run_dir / "persona_chat_sample.json"), persona_chat),
    }

    for _, (artifact_uri, payload) in artifacts.items():
        _write_json(Path(artifact_uri), payload)
    (run_dir / "impact_report.md").write_text(render_impact_report_markdown(impact_report), encoding="utf-8")
    (run_dir / "backtest.md").write_text(render_backtest_markdown(backtest_result), encoding="utf-8")

    audit_manifest = build_audit_manifest(
        case_id=case_graph["case_id"],
        run_id=args.run_id,
        artifacts=artifacts,
    )
    _validate("schemas/audit_manifest.schema.json", audit_manifest)
    _write_json(run_dir / "audit_manifest.json", audit_manifest)

    verdicts = ", ".join(f"{item['rule_id']}={item['verdict']}" for item in backtest_result["rules"])
    print(f"Wrote Phase 2 run: {run_dir}")
    print(f"Agents: {len(agents_payload['agents'])}")
    print(f"Simulation events: {len(simulation_result['events'])}")
    print(f"Backtest verdicts: {verdicts}")
    return 0


def _default_run_id() -> str:
    return "ulez_2023_phase2_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _validate(schema_path: str, payload: dict[str, Any]) -> None:
    schema = _read_json(Path(schema_path))
    Draft202012Validator(schema).validate(payload)


def _select_chat_agent(agents: list[dict[str, Any]]) -> dict[str, Any]:
    for agent in agents:
        if agent.get("stakeholder_id") == "stakeholder_low_income_households":
            return agent
    return agents[0]


if __name__ == "__main__":
    raise SystemExit(main())
