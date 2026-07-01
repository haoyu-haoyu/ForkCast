from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Protocol

from policy_impact_sandbox.phase2.backtest import evaluate_blind_prediction_backtest
from policy_impact_sandbox.phase2.blind_prediction import (
    DeterministicBlindLLMClient,
    generate_blind_prediction,
)
from policy_impact_sandbox.phase2.json_utils import parse_json_object


class RobustnessLLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


PERTURBATION_TARGETS = [
    ("stakeholder_van_drivers_tradespeople", 0.8),
    ("stakeholder_low_income_households", 0.8),
    ("stakeholder_outer_london_residents", 0.8),
    ("stakeholder_inner_london_residents", 0.8),
    ("stakeholder_van_drivers_tradespeople", 1.2),
    ("stakeholder_low_income_households", 1.2),
]


class DeterministicRobustnessLLMClient:
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        payload = parse_json_object(DeterministicBlindLLMClient().complete_json(system_prompt, user_prompt))
        if "stakeholder_van_drivers_tradespeople" in user_prompt and '"weight": 0.8' in user_prompt:
            payload["group_reactions"] = [
                item for item in payload["group_reactions"] if item["group_id"] != "stakeholder_van_drivers_tradespeople"
            ]
            payload["ranked_opposition_groups"] = ["stakeholder_low_income_households", "stakeholder_outer_london_residents"]
        if "stakeholder_low_income_households" in user_prompt and '"weight": 0.8' in user_prompt:
            payload["benefit_burden_balance"] = ["air-quality and public-health benefits are likely"]
        return json.dumps(payload, ensure_ascii=False)


def run_robustness(
    *,
    case_graph_path: Path,
    truth_set_path: Path,
    run_dir: Path,
    k: int,
    perturbations: int = 6,
    mock_llm: bool,
    llm_client: RobustnessLLMClient | None = None,
    llm_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    case_graph = _read_json(case_graph_path)
    truth_set = _read_json(truth_set_path)
    run_dir.mkdir(parents=True, exist_ok=True)
    client = llm_client or DeterministicRobustnessLLMClient()
    metadata = llm_metadata or {"provider": "mock", "model": "deterministic_robustness"}
    if mock_llm:
        client = DeterministicRobustnessLLMClient()
        metadata = {"provider": "mock", "model": "deterministic_robustness"}

    repeat_runs = []
    for iteration in range(1, k + 1):
        prediction = generate_blind_prediction(case_graph=case_graph, llm_client=client, llm_metadata=metadata)
        backtest = evaluate_blind_prediction_backtest(blind_prediction=prediction, truth_set=truth_set)
        repeat_runs.append(
            {
                "iteration": iteration,
                "verdicts": _verdicts(backtest),
                "backtest_result": backtest,
            }
        )
    repeat_stability = _stability([run["verdicts"] for run in repeat_runs])
    baseline_verdicts = {rule_id: item["majority_verdict"] for rule_id, item in repeat_stability.items()}

    sensitivity_runs = []
    for index, (stakeholder_id, factor) in enumerate(_perturbation_plan(perturbations), start=1):
        perturbed_case_graph = _perturb_case_graph(case_graph, stakeholder_id, factor)
        prediction = generate_blind_prediction(case_graph=perturbed_case_graph, llm_client=client, llm_metadata=metadata)
        backtest = evaluate_blind_prediction_backtest(blind_prediction=prediction, truth_set=truth_set)
        verdicts = _verdicts(backtest)
        sensitivity_runs.append(
            {
                "perturbation_id": f"p{index}",
                "stakeholder_id": stakeholder_id,
                "weight_factor": factor,
                "verdicts": verdicts,
                "flips": {
                    rule_id: {"baseline": baseline, "perturbed": verdicts[rule_id]}
                    for rule_id, baseline in baseline_verdicts.items()
                    if verdicts[rule_id] != baseline
                },
            }
        )

    sensitivity = _sensitivity_summary(sensitivity_runs, baseline_verdicts)
    result = {
        "case_id": case_graph["case_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "mock" if mock_llm else "real_llm",
        "repeat_k": k,
        "judgment_stage_only": True,
        "extraction_rerun": False,
        "repeat_runs": repeat_runs,
        "repeat_stability": repeat_stability,
        "sensitivity": sensitivity,
    }
    _write_json(run_dir / "robustness.json", result)
    _upsert_robustness_section(run_dir / "impact_report.md", render_robustness_markdown(result))
    return result


def render_robustness_markdown(result: dict[str, Any]) -> str:
    lines = [
        "## Robustness",
        "",
        f"Mode: `{result['mode']}`. Extraction rerun: `{result['extraction_rerun']}`.",
        "",
        "### Repeat Stability",
        "",
    ]
    for rule_id, stats in result["repeat_stability"].items():
        status = "UNSTABLE" if stats["unstable"] else "stable"
        lines.append(f"- {rule_id}: {stats['agreement_label']} ({status}); majority `{stats['majority_verdict']}`")
    lines.extend(["", "### Weight Sensitivity", ""])
    for rule_id, stats in result["sensitivity"]["rules"].items():
        lines.append(
            f"- {rule_id}: {stats['classification']} ({stats['flip_count']} flips across {result['sensitivity']['perturbation_count']} perturbations)"
        )
    return "\n".join(lines) + "\n"


def _stability(matrices: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    total = len(matrices)
    for rule_id in ["R1", "R2", "R3", "R4", "R5", "R6"]:
        counts = Counter(matrix[rule_id] for matrix in matrices)
        majority_verdict, majority_count = counts.most_common(1)[0]
        output[rule_id] = {
            "majority_verdict": majority_verdict,
            "agreement_count": majority_count,
            "run_count": total,
            "agreement_label": f"{majority_count}/{total} runs agree",
            "unstable": majority_count != total,
            "counts": dict(sorted(counts.items())),
        }
    return output


def _sensitivity_summary(runs: list[dict[str, Any]], baseline_verdicts: dict[str, str]) -> dict[str, Any]:
    rules = {}
    for rule_id in ["R1", "R2", "R3", "R4", "R5", "R6"]:
        flips = [run for run in runs if rule_id in run["flips"]]
        rules[rule_id] = {
            "baseline": baseline_verdicts[rule_id],
            "flip_count": len(flips),
            "classification": "assumption_sensitive" if flips else "robust",
            "flipped_by": [
                {
                    "perturbation_id": run["perturbation_id"],
                    "stakeholder_id": run["stakeholder_id"],
                    "weight_factor": run["weight_factor"],
                    "perturbed": run["verdicts"][rule_id],
                }
                for run in flips
            ],
        }
    return {
        "perturbation_count": len(runs),
        "runs": runs,
        "rules": rules,
    }


def _perturbation_plan(count: int) -> list[tuple[str, float]]:
    if count <= len(PERTURBATION_TARGETS):
        return PERTURBATION_TARGETS[:count]
    output = list(PERTURBATION_TARGETS)
    while len(output) < count:
        output.extend(PERTURBATION_TARGETS)
    return output[:count]


def _perturb_case_graph(case_graph: dict[str, Any], stakeholder_id: str, factor: float) -> dict[str, Any]:
    perturbed = deepcopy(case_graph)
    for stakeholder in perturbed.get("stakeholders", []):
        stakeholder.pop("weight", None)
        if stakeholder.get("id") == stakeholder_id:
            stakeholder["weight"] = factor
    return perturbed


def _verdicts(backtest: dict[str, Any]) -> dict[str, str]:
    return {rule["rule_id"]: rule["verdict"] for rule in backtest["rules"]}


def _upsert_robustness_section(path: Path, section: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    marker = "\n## Robustness\n"
    if marker in existing:
        existing = existing.split(marker, 1)[0].rstrip() + "\n"
    path.write_text(existing.rstrip() + "\n\n" + section, encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
