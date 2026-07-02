from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import random
from statistics import mean
from typing import Any

from policy_impact_sandbox.phase2.backtest import RULE_FACTS, evaluate_blind_prediction_backtest


HIT_VERDICTS = {"HIT", "BALANCED HIT"}

INVERTED_RULE_OUTCOMES = {
    "R1": "Inverted control: outer London does not show stronger opposition than inner London.",
    "R2": "Inverted control: van drivers, tradespeople and small businesses are not singled out as a high-impact group.",
    "R3": "Inverted control: the policy is not politically salient and is not linked to Uxbridge electoral risk.",
    "R4": "Inverted control: no enforcement resistance, camera vandalism or sabotage signal occurs.",
    "R5": "Inverted control: compliance does not improve over time and no adaptation signal is observed.",
    "R6": "Inverted control: neither air-quality benefit nor distributional burden is observed.",
}


def run_negative_controls(
    *,
    blind_prediction_path: Path,
    truth_set_path: Path,
    ablation_path: Path | None,
    output_dir: Path,
    permutations: int = 20,
    seed: int = 20260703,
) -> dict[str, Any]:
    blind_prediction = _read_json(blind_prediction_path)
    truth_set = _read_json(truth_set_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline = _score(blind_prediction, truth_set)
    inverted_truth = make_inverted_truth_set(truth_set)
    inverted = _score(blind_prediction, inverted_truth)

    shuffled_runs = []
    rng = random.Random(seed)
    for index in range(1, permutations + 1):
        shuffled_truth, mapping = make_shuffled_truth_set(truth_set, rng=rng)
        scored = _score(blind_prediction, shuffled_truth)
        shuffled_runs.append(
            {
                "permutation": index,
                "mapping": mapping,
                "hit_rate": scored["hit_rate"],
                "verdicts": scored["verdicts"],
            }
        )

    shuffled_rates = [item["hit_rate"] for item in shuffled_runs]
    ablation_reference_rate = _ablation_full_pipeline_rate(ablation_path) if ablation_path else None
    real_rate_for_position = ablation_reference_rate if ablation_reference_rate is not None else baseline["hit_rate"]
    controls_collapse = inverted["hit_rate"] < baseline["hit_rate"] and mean(shuffled_rates) < baseline["hit_rate"]
    scorer_leniency_finding = not controls_collapse

    result = {
        "case_id": truth_set["case_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scorer": "evaluate_blind_prediction_backtest",
        "prediction_artifact": str(blind_prediction_path),
        "truth_set_artifact": str(truth_set_path),
        "controls": {
            "baseline_cached_prediction": baseline,
            "inverted_truth": {
                **inverted,
                "control_description": "Same blind prediction scored against direction-inverted truth facts.",
            },
            "shuffled_alignment": {
                "control_description": "Same blind prediction scored against truth facts permuted across R1-R6 alignments.",
                "seed": seed,
                "permutations": permutations,
                "runs": shuffled_runs,
                "distribution": {
                    "min": min(shuffled_rates),
                    "max": max(shuffled_rates),
                    "mean": round(mean(shuffled_rates), 4),
                    "values": shuffled_rates,
                },
                "real_ablation_full_pipeline_mean_hit_rate": ablation_reference_rate,
                "real_rate_position": _position(real_rate_for_position, shuffled_rates),
            },
            "cross_case": {
                "status": "not_run",
                "reason": "CC 2003 cross-case control is gated on human verification of the draft truth set.",
            },
        },
        "finding": {
            "scorer_leniency_found": scorer_leniency_finding,
            "controls_collapse_toward_chance": controls_collapse,
            "summary": (
                "Negative controls did not reduce hit rate; current scorer verdicts are driven by prediction text "
                "signals and not by semantic comparison against truth-set content."
                if scorer_leniency_finding
                else "Negative controls reduced hit rate as expected."
            ),
            "scorer_modified": False,
        },
    }
    _write_json(output_dir / "negative_controls.json", result)
    (output_dir / "negative_controls.md").write_text(render_negative_controls_markdown(result), encoding="utf-8")
    return result


def make_inverted_truth_set(truth_set: dict[str, Any]) -> dict[str, Any]:
    inverted = deepcopy(truth_set)
    fact_to_rules = _fact_to_rules()
    for fact in inverted.get("facts", []):
        rules = fact_to_rules.get(fact.get("id"), [])
        if not rules:
            continue
        inverted_text = " ".join(INVERTED_RULE_OUTCOMES[rule_id] for rule_id in rules)
        fact["fact"] = inverted_text
        fact["value"] = {"negative_control": "direction_inverted", "source_rules": rules}
        fact["notes"] = "Generated only for negative-control scoring; not a real historical claim."
    inverted["case_id"] = f"{truth_set['case_id']}__negative_control_inverted"
    inverted["negative_control"] = "direction_inverted"
    return inverted


def make_shuffled_truth_set(truth_set: dict[str, Any], *, rng: random.Random) -> tuple[dict[str, Any], dict[str, str]]:
    shuffled = deepcopy(truth_set)
    rule_ids = list(RULE_FACTS)
    source_rules = list(rule_ids)
    rng.shuffle(source_rules)
    if source_rules == rule_ids and len(source_rules) > 1:
        source_rules = source_rules[1:] + source_rules[:1]
    mapping = dict(zip(rule_ids, source_rules, strict=True))
    source_facts = {rule_id: _joined_rule_facts(truth_set, rule_id) for rule_id in rule_ids}
    fact_to_rules = _fact_to_rules()
    for fact in shuffled.get("facts", []):
        rules = fact_to_rules.get(fact.get("id"), [])
        if not rules:
            continue
        assigned = [mapping[rule_id] for rule_id in rules]
        fact["fact"] = " | ".join(
            f"Shuffled control: {rule_id} receives facts from {source_rule}: {source_facts[source_rule]}"
            for rule_id, source_rule in zip(rules, assigned, strict=True)
        )
        fact["value"] = {"negative_control": "shuffled_alignment", "source_rules": assigned}
        fact["notes"] = "Generated only for negative-control scoring; not a real historical claim."
    shuffled["case_id"] = f"{truth_set['case_id']}__negative_control_shuffled"
    shuffled["negative_control"] = "shuffled_alignment"
    return shuffled, mapping


def render_negative_controls_markdown(result: dict[str, Any]) -> str:
    baseline = result["controls"]["baseline_cached_prediction"]
    inverted = result["controls"]["inverted_truth"]
    shuffled = result["controls"]["shuffled_alignment"]
    distribution = shuffled["distribution"]
    finding = result["finding"]
    lines = [
        "# ULEZ Negative Controls",
        "",
        "All controls reuse `evaluate_blind_prediction_backtest` and the existing cached `blind_prediction.json` unchanged.",
        "No scorer code was modified.",
        "",
        "## Headline Finding",
        "",
        f"- Scorer leniency found: `{finding['scorer_leniency_found']}`",
        f"- Controls collapse toward chance: `{finding['controls_collapse_toward_chance']}`",
        f"- Summary: {finding['summary']}",
        "",
        "## Hit Rates",
        "",
        "| Condition | Hit rate | Verdicts |",
        "|---|---:|---|",
        f"| Real truth set, cached blind prediction | {baseline['hit_rate']:.4f} | {_format_verdicts(baseline['verdicts'])} |",
        f"| Inverted-truth control | {inverted['hit_rate']:.4f} | {_format_verdicts(inverted['verdicts'])} |",
        f"| Shuffled-alignment controls, mean of {shuffled['permutations']} | {distribution['mean']:.4f} | min={distribution['min']:.4f}; max={distribution['max']:.4f} |",
        "",
        "## Shuffled Distribution",
        "",
        f"- Seed: `{shuffled['seed']}`",
        f"- Values: `{json.dumps(distribution['values'])}`",
        f"- Real ablation full-pipeline mean hit rate: `{shuffled['real_ablation_full_pipeline_mean_hit_rate']}`",
        f"- Position of real rate in permutation distribution: `{json.dumps(shuffled['real_rate_position'], sort_keys=True)}`",
        "",
        "## Interpretation",
        "",
        "These controls are intentionally adversarial. They show that the current R1-R6 scorer is useful as a signal-extraction checklist, but not yet a semantic truth-comparison evaluator: changing or shuffling the truth-set content does not change verdicts because verdicts are derived from blind-prediction text signals. This is an evidence-hardening finding, not a product claim.",
        "",
        "Cross-case control status: `{status}` — {reason}".format(**result["controls"]["cross_case"]),
    ]
    return "\n".join(lines) + "\n"


def _score(blind_prediction: dict[str, Any], truth_set: dict[str, Any]) -> dict[str, Any]:
    backtest = evaluate_blind_prediction_backtest(blind_prediction=blind_prediction, truth_set=truth_set)
    verdicts = {rule["rule_id"]: rule["verdict"] for rule in backtest["rules"]}
    return {
        "case_id": backtest["case_id"],
        "hit_rate": round(_hit_rate(verdicts), 4),
        "verdicts": verdicts,
        "backtest_result": backtest,
    }


def _hit_rate(verdicts: dict[str, str]) -> float:
    return sum(1 for verdict in verdicts.values() if verdict in HIT_VERDICTS) / len(verdicts)


def _position(real_rate: float, distribution: list[float]) -> dict[str, Any]:
    below_or_equal = sum(1 for value in distribution if value <= real_rate)
    above_or_equal = sum(1 for value in distribution if value >= real_rate)
    return {
        "real_rate": round(real_rate, 4),
        "permutation_count": len(distribution),
        "count_less_or_equal": below_or_equal,
        "count_greater_or_equal": above_or_equal,
        "percentile_less_or_equal": round(below_or_equal / len(distribution), 4),
    }


def _ablation_full_pipeline_rate(path: Path | None) -> float | None:
    if path is None or not path.exists():
        return None
    payload = _read_json(path)
    rate = payload.get("conditions", {}).get("full_pipeline", {}).get("mean_hit_rate")
    return float(rate) if rate is not None else None


def _fact_to_rules() -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for rule_id, fact_ids in RULE_FACTS.items():
        for fact_id in fact_ids:
            output.setdefault(fact_id, []).append(rule_id)
    return output


def _joined_rule_facts(truth_set: dict[str, Any], rule_id: str) -> str:
    facts = {fact["id"]: fact for fact in truth_set.get("facts", [])}
    return " | ".join(facts[fact_id]["fact"] for fact_id in RULE_FACTS[rule_id] if fact_id in facts)


def _format_verdicts(verdicts: dict[str, str]) -> str:
    return ", ".join(f"{rule_id}={verdict}" for rule_id, verdict in sorted(verdicts.items()))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
