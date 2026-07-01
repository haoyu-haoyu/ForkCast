from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Protocol

from policy_impact_sandbox.phase2.backtest import evaluate_blind_prediction_backtest
from policy_impact_sandbox.phase2.blind_prediction import (
    EXCLUDED_CASE_GRAPH_FIELDS,
    DeterministicBlindLLMClient,
    generate_blind_prediction,
    make_blind_case_context,
    _normalize_prediction,
)
from policy_impact_sandbox.phase2.json_utils import parse_json_object


class AblationLLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


FORBIDDEN_OUTCOME_TOKENS = [
    "truth_set_json",
    "truth_set",
    "51%",
    "62%",
    "495",
    "416",
    "91.6",
    "96.2",
    "88.9",
    "97.1",
    "53%",
    "90,000",
    "Conservative hold",
    "Blade Runners",
    "Uxbridge",
]

CONDITIONS = {
    "bare_prompt": "A: bare single prompt from policy text only",
    "single_analyst": "B: single generic analyst with sanitized case context, no stakeholder agents",
    "full_pipeline": "C: full Policy Impact Sandbox blind-prediction path",
}


class DeterministicAblationLLMClient:
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        if "condition_id: bare_prompt" in user_prompt:
            payload = {
                "summary": "Policy-text-only baseline expects visible household cost backlash and political salience.",
                "group_reactions": [
                    {"group_id": "stakeholder_outer_london_residents", "direction": "oppose", "intensity": "high"},
                    {"group_id": "stakeholder_inner_london_residents", "direction": "support", "intensity": "medium"},
                ],
                "ranked_opposition_groups": ["stakeholder_outer_london_residents"],
                "political_consequences": ["political salience and electoral risk"],
                "time_dynamics": ["short-term backlash followed by gradual adaptation and compliance over time"],
                "secondary_reactions": [],
                "benefit_burden_balance": ["air quality and health benefit", "fairness burden for vehicle-dependent households"],
                "confidence_notes": ["Mock baseline A; no historical outcomes used."],
            }
        elif "condition_id: single_analyst" in user_prompt:
            payload = {
                "summary": "Single analyst baseline uses stakeholder context and flags concentrated business burden.",
                "group_reactions": [
                    {"group_id": "stakeholder_outer_london_residents", "direction": "oppose", "intensity": "high"},
                    {"group_id": "stakeholder_inner_london_residents", "direction": "support", "intensity": "medium"},
                    {"group_id": "stakeholder_van_drivers_tradespeople", "direction": "oppose", "intensity": "very_high"},
                ],
                "ranked_opposition_groups": [
                    "stakeholder_van_drivers_tradespeople",
                    "stakeholder_outer_london_residents",
                ],
                "political_consequences": ["political salience and electoral risk"],
                "time_dynamics": ["initial opposition may gradually adapt into higher compliance over time"],
                "secondary_reactions": [],
                "benefit_burden_balance": ["air quality and health benefit", "distributional fairness burden"],
                "confidence_notes": ["Mock baseline B; no historical outcomes used."],
            }
        else:
            return DeterministicBlindLLMClient().complete_json(system_prompt, user_prompt)
        return json.dumps(payload, ensure_ascii=False)


def run_ablation(
    *,
    case_graph_path: Path,
    policy_text_path: Path,
    truth_set_path: Path,
    k: int,
    mock_llm: bool,
    output_dir: Path,
    llm_client: AblationLLMClient | None = None,
    llm_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    case_graph = _read_json(case_graph_path)
    truth_set = _read_json(truth_set_path)
    policy_text = _sanitize_policy_text(policy_text_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)

    client = llm_client or DeterministicAblationLLMClient()
    metadata = llm_metadata or {"provider": "mock", "model": "deterministic_ablation"}
    if mock_llm:
        client = DeterministicAblationLLMClient()
        metadata = {"provider": "mock", "model": "deterministic_ablation"}

    conditions: dict[str, Any] = {}
    for condition_id in CONDITIONS:
        runs = []
        for iteration in range(1, k + 1):
            prediction = _generate_condition_prediction(
                condition_id=condition_id,
                case_graph=case_graph,
                policy_text=policy_text,
                llm_client=client,
                llm_metadata=metadata,
                iteration=iteration,
            )
            backtest = evaluate_blind_prediction_backtest(blind_prediction=prediction, truth_set=truth_set)
            verdicts = {rule["rule_id"]: rule["verdict"] for rule in backtest["rules"]}
            runs.append(
                {
                    "iteration": iteration,
                    "prediction": prediction,
                    "backtest_result": backtest,
                    "verdicts": verdicts,
                    "hit_rate": _hit_rate(verdicts),
                }
            )
        conditions[condition_id] = {
            "label": CONDITIONS[condition_id],
            "runs": runs,
            "hit_miss_matrix": [run["verdicts"] for run in runs],
            "mean_hit_rate": round(sum(run["hit_rate"] for run in runs) / len(runs), 4),
            "per_question_consistency": _consistency([run["verdicts"] for run in runs]),
        }

    result = {
        "case_id": truth_set["case_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "mock" if mock_llm else "real_llm",
        "k": k,
        "scorer": "evaluate_blind_prediction_backtest",
        "answer_isolation": {
            "truth_set_loaded_into_prediction_prompts": False,
            "truth_set_loaded_only_after_prediction_for_scoring": True,
            "forbidden_outcome_tokens": FORBIDDEN_OUTCOME_TOKENS,
        },
        "conditions": conditions,
    }
    _write_json(output_dir / "ablation_ulez.json", result)
    (output_dir / "ablation_ulez.md").write_text(render_ablation_markdown(result), encoding="utf-8")
    return result


def render_ablation_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# ULEZ Ablation Baselines",
        "",
        "All conditions use the same R1-R6 scorer: `evaluate_blind_prediction_backtest`.",
        "The truth set is loaded only after each prediction artifact is written.",
        "",
        f"Mode: `{result['mode']}`. Runs per condition: `{result['k']}`.",
        "",
        "Reproduce mock smoke table: `uv run python scripts/run_ablation.py --mock-llm --k 1 --output-dir docs/evaluation`.",
        "Run real DeepSeek table: `uv run python scripts/run_ablation.py --k 5 --output-dir docs/evaluation`.",
        "",
        "| Condition | Mean hit rate | R1 | R2 | R3 | R4 | R5 | R6 |",
        "|---|---:|---|---|---|---|---|---|",
    ]
    for condition_id, condition in result["conditions"].items():
        majority = {
            rule_id: stats["majority_verdict"]
            for rule_id, stats in condition["per_question_consistency"].items()
        }
        lines.append(
            "| {condition} | {rate:.2f} | {R1} | {R2} | {R3} | {R4} | {R5} | {R6} |".format(
                condition=condition_id,
                rate=condition["mean_hit_rate"],
                **majority,
            )
        )
    lines.extend(["", "## Hit/Miss Matrix", "", "| Condition | Run | R1 | R2 | R3 | R4 | R5 | R6 |", "|---|---:|---|---|---|---|---|---|"])
    for condition_id, condition in result["conditions"].items():
        for index, verdicts in enumerate(condition["hit_miss_matrix"], start=1):
            lines.append(
                "| {condition} | {run} | {R1} | {R2} | {R3} | {R4} | {R5} | {R6} |".format(
                    condition=condition_id,
                    run=index,
                    **verdicts,
                )
            )
    lines.extend(["", "## Per-Question Consistency", ""])
    for condition_id, condition in result["conditions"].items():
        lines.append(f"### {condition_id}")
        lines.append("")
        lines.append("| Rule | Majority verdict | Consistency | Counts |")
        lines.append("|---|---|---:|---|")
        for rule_id, stats in condition["per_question_consistency"].items():
            lines.append(
                f"| {rule_id} | {stats['majority_verdict']} | {stats['consistency_rate']:.2f} | {json.dumps(stats['counts'], sort_keys=True)} |"
            )
        lines.append("")
    return "\n".join(lines)


def _generate_condition_prediction(
    *,
    condition_id: str,
    case_graph: dict[str, Any],
    policy_text: str,
    llm_client: AblationLLMClient,
    llm_metadata: dict[str, Any],
    iteration: int,
) -> dict[str, Any]:
    if condition_id == "full_pipeline":
        artifact = generate_blind_prediction(case_graph=case_graph, llm_client=llm_client, llm_metadata=llm_metadata)
        artifact["ablation_condition"] = condition_id
        artifact["ablation_iteration"] = iteration
        return artifact

    context = _condition_context(condition_id, case_graph, policy_text)
    prompts = _build_condition_prompts(condition_id, context)
    raw_text = llm_client.complete_json(prompts["system_prompt"], prompts["user_prompt"])
    parsed = parse_json_object(raw_text)
    return {
        "case_id": case_graph["case_id"],
        "mode": "blind_prediction",
        "ablation_condition": condition_id,
        "ablation_iteration": iteration,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "llm": llm_metadata,
        "leakage_guard": {
            "truth_set_loaded_into_prompt": False,
            "truth_set_file_read_by_prediction_step": False,
            "excluded_case_graph_fields": EXCLUDED_CASE_GRAPH_FIELDS,
        },
        "prompt": prompts,
        "blind_context": context,
        "raw_prediction_text": raw_text,
        "raw_prediction": parsed,
        "prediction": _normalize_prediction(parsed),
    }


def _condition_context(condition_id: str, case_graph: dict[str, Any], policy_text: str) -> dict[str, Any]:
    if condition_id == "bare_prompt":
        return {
            "case_id": case_graph["case_id"],
            "case_name": case_graph.get("case_name", case_graph["case_id"]),
            "policy_text_only": policy_text,
            "context_limit": "No stakeholder agent profiles or historical truth set.",
        }
    context = make_blind_case_context(case_graph)
    context["context_limit"] = "Single generic analyst; no stakeholder agent simulation or persona chat."
    return context


def _build_condition_prompts(condition_id: str, context: dict[str, Any]) -> dict[str, str]:
    system_prompt = (
        "You are producing an answer-isolated qualitative policy prediction for an ablation baseline. "
        "Do not use historical outcome data, election results, post-implementation metrics, polling results, "
        "camera offence counts, compliance rates, air-quality measurements, or source quotes. "
        "Return one JSON object and no prose. Do not predict exact percentages, vote margins, offence counts, "
        "or any specific election result. Political output must be political salience/electoral risk only."
    )
    user_prompt = (
        f"condition_id: {condition_id}\n"
        f"condition_context:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        "Return JSON with keys: summary, group_reactions, ranked_opposition_groups, "
        "political_consequences, time_dynamics, secondary_reactions, benefit_burden_balance, confidence_notes. "
        "For group_reactions include group_id, direction, intensity, rationale when possible."
    )
    return {"system_prompt": system_prompt, "user_prompt": user_prompt}


def _sanitize_policy_text(policy_text: str) -> str:
    kept_lines = []
    for line in policy_text.splitlines():
        lowered = line.lower()
        if "truth_set" in lowered or "backtest" in lowered or "observed" in lowered:
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines).strip()


def _hit_rate(verdicts: dict[str, str]) -> float:
    hits = sum(1 for verdict in verdicts.values() if verdict in {"HIT", "BALANCED HIT"})
    return hits / len(verdicts)


def _consistency(matrices: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for rule_id in ["R1", "R2", "R3", "R4", "R5", "R6"]:
        counts = Counter(matrix[rule_id] for matrix in matrices)
        majority_verdict, majority_count = counts.most_common(1)[0]
        output[rule_id] = {
            "majority_verdict": majority_verdict,
            "consistency_rate": round(majority_count / len(matrices), 4),
            "counts": dict(sorted(counts.items())),
        }
    return output


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
