from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import random
from statistics import mean
from typing import Any

from policy_impact_sandbox.phase2 import backtest as backtest_module


HIT_VERDICTS = {"HIT", "BALANCED HIT"}

INVERTED_RULE_OUTCOMES = {
    "R1": "Inverted control: outer London does not show stronger opposition than inner London.",
    "R2": "Inverted control: van drivers, tradespeople and small businesses are not singled out as a high-impact group.",
    "R3": "Inverted control: the policy is not politically salient and is not linked to Uxbridge electoral risk.",
    "R4": "Inverted control: no enforcement resistance, camera vandalism or sabotage signal occurs.",
    "R5": "Inverted control: compliance does not improve over time and no adaptation signal is observed.",
    "R6": "Inverted control: neither air-quality benefit nor distributional burden is observed.",
}

MECHANISM_BY_RULE = {
    "R1": {
        "verdict_source": "prediction text patterns alone with no comparison target",
        "rule_facts": "RULE_FACTS maps R1 to C1_public_opinion_distribution only; it contains no expected polarity.",
        "signal_source": "outer/inner stakeholder reaction text matched by _blind_prediction_signals.",
        "code_refs": ["backtest.py:8-14", "backtest.py:44-62", "backtest.py:143-147", "backtest.py:152-171", "backtest.py:219-224"],
    },
    "R2": {
        "verdict_source": "prediction text patterns alone with no comparison target",
        "rule_facts": "RULE_FACTS maps R2 to D1_six_month_compliance_rate_change only; it contains no expected polarity.",
        "signal_source": "van/tradespeople/small-business and high-opposition terms matched in prediction text.",
        "code_refs": ["backtest.py:8-14", "backtest.py:44-62", "backtest.py:143-147", "backtest.py:157", "backtest.py:172-176", "backtest.py:219-224"],
    },
    "R3": {
        "verdict_source": "prediction text patterns alone with no comparison target",
        "rule_facts": "RULE_FACTS maps R3 to Uxbridge result and ULEZ-as-key-issue facts; it contains no expected polarity.",
        "signal_source": "political salience/electoral-risk terms matched in prediction text.",
        "code_refs": ["backtest.py:8-14", "backtest.py:44-62", "backtest.py:143-147", "backtest.py:158", "backtest.py:177-178", "backtest.py:219-224"],
    },
    "R4": {
        "verdict_source": "prediction text patterns alone with no comparison target",
        "rule_facts": "RULE_FACTS maps R4 to camera vandalism/enforcement-resistance facts; it contains no expected polarity.",
        "signal_source": "enforcement resistance, sabotage, camera, or vandal terms matched in prediction text.",
        "code_refs": ["backtest.py:8-14", "backtest.py:44-62", "backtest.py:143-147", "backtest.py:159", "backtest.py:179-180", "backtest.py:219-224"],
    },
    "R5": {
        "verdict_source": "prediction text patterns alone with no comparison target",
        "rule_facts": "RULE_FACTS maps R5 to compliance and non-compliant-vehicle facts; it contains no expected polarity.",
        "signal_source": "adaptation/compliance terms plus over-time terms matched in prediction text.",
        "code_refs": ["backtest.py:8-14", "backtest.py:44-62", "backtest.py:143-147", "backtest.py:160-162", "backtest.py:181-182", "backtest.py:219-224"],
    },
    "R6": {
        "verdict_source": "prediction text patterns alone with no comparison target",
        "rule_facts": "RULE_FACTS maps R6 to air-quality, charge and public-opinion facts; it contains no expected polarity.",
        "signal_source": "air-quality/health/emissions terms plus distributional/fairness/burden terms matched in prediction text.",
        "code_refs": ["backtest.py:8-14", "backtest.py:44-62", "backtest.py:143-147", "backtest.py:163-187", "backtest.py:233-238"],
    },
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
    inverted_rule_truth, inverted_rule_facts = make_inverted_rule_facts_control(truth_set)
    with _temporary_rule_facts(inverted_rule_facts):
        inverted_rule_facts_result = _score(blind_prediction, inverted_rule_truth)

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
    controls_collapse = inverted["hit_rate"] < baseline["hit_rate"] and mean(shuffled_rates) < baseline["hit_rate"]
    rule_facts_verdicts_changed = inverted_rule_facts_result["verdicts"] != baseline["verdicts"]
    scorer_leniency_finding = not controls_collapse and not rule_facts_verdicts_changed
    mechanism = (
        "semantic_comparator_with_code_ground_truth"
        if rule_facts_verdicts_changed
        else "text_signal_checklist_no_comparison_target"
    )

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
            "inverted_rule_facts": {
                **inverted_rule_facts_result,
                "control_description": "Same blind prediction scored while negative-controls temporarily replace RULE_FACTS with inverted-polarity synthetic fact IDs.",
                "temporary_rule_facts": inverted_rule_facts,
                "verdicts_changed_from_baseline": rule_facts_verdicts_changed,
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
                "ablation_reference": {
                    "artifact": str(ablation_path) if ablation_path else None,
                    "status": "not_compared",
                    "reason": "Removed from this control: a k=5 ablation mean is a different sample from the cached-run shuffle distribution.",
                },
            },
            "cross_case": {
                "status": "not_run",
                "reason": "CC 2003 cross-case control is gated on human verification of the draft truth set.",
            },
        },
        "finding": {
            "scorer_leniency_found": scorer_leniency_finding,
            "controls_collapse_toward_chance": controls_collapse,
            "control_c_verdicts_changed_from_baseline": rule_facts_verdicts_changed,
            "mechanism": mechanism,
            "summary": (
                "Negative controls did not reduce hit rate, and Control C did not change verdicts when RULE_FACTS was temporarily inverted. Current scorer verdicts are driven by prediction text signals with no comparison target."
                if scorer_leniency_finding
                else "Control C changed verdicts; this indicates a semantic comparator with code-level ground-truth polarity, not truth_set.json as the operative source."
            ),
            "scorer_modified": False,
        },
        "mechanism_by_rule": MECHANISM_BY_RULE,
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
    rule_ids = list(backtest_module.RULE_FACTS)
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
    inverted_rule_facts = result["controls"]["inverted_rule_facts"]
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
        f"| Control C: inverted RULE_FACTS surrogate | {inverted_rule_facts['hit_rate']:.4f} | {_format_verdicts(inverted_rule_facts['verdicts'])} |",
        f"| Shuffled-alignment controls, mean of {shuffled['permutations']} | {distribution['mean']:.4f} | min={distribution['min']:.4f}; max={distribution['max']:.4f} |",
        "",
        "## Mechanism",
        "",
        "`RULE_FACTS` maps rule ids to truth-set fact ids only. It does not contain expected directions or polarity. In `evaluate_blind_prediction_backtest`, the `truth_set` argument is read into `facts`, but those facts are used by `_rule(...)` to populate `real_outcome`; the verdict itself is passed in before `_rule(...)` and is derived from `signals`.",
        "",
        "Relevant scorer lines:",
        "",
        "- `RULE_FACTS = { ... }` maps R1-R6 to fact ids only (`backtest.py:8-14`).",
        "- `prediction = blind_prediction.get(\"prediction\", {})` and `signals = _blind_prediction_signals(prediction)` (`backtest.py:45-46`).",
        "- R1-R5 verdicts call `_verdict_for(signals, \"R#\")`; R6 calls `_r6_blind_verdict(signals)` (`backtest.py:51-62`).",
        "- `_rule(...)` writes `real_outcome` from `facts[fact_id][\"fact\"]` via `RULE_FACTS`, but receives `verdict` as an already-computed argument (`backtest.py:136-148`).",
        "- `_blind_prediction_signals(...)` builds R1-R6 signals from prediction text/group-reaction terms (`backtest.py:152-188`).",
        "- `_verdict_for(...)` and `_r6_blind_verdict(...)` return verdicts from signal presence/partial flags only (`backtest.py:219-238`).",
        "",
        "| Rule | Verdict actually computed from | Truth-set role | Code refs |",
        "|---|---|---|---|",
        *[
            "| {rule_id} | {verdict_source}: {signal_source} | {rule_facts} | {code_refs} |".format(
                rule_id=rule_id,
                verdict_source=item["verdict_source"],
                signal_source=item["signal_source"],
                rule_facts=item["rule_facts"],
                code_refs=", ".join(item["code_refs"]),
            )
            for rule_id, item in result["mechanism_by_rule"].items()
        ],
        "",
        "Control C interpretation: verdicts did not change after replacing `RULE_FACTS` with inverted-polarity synthetic fact ids. Therefore the scorer is not a semantic comparator with ground truth in code; it is a text-signal checklist with no comparison target.",
        "",
        "## Shuffled Distribution",
        "",
        f"- Seed: `{shuffled['seed']}`",
        f"- Values: `{json.dumps(distribution['values'])}`",
        f"- Ablation comparison: `{shuffled['ablation_reference']['status']}` — {shuffled['ablation_reference']['reason']}",
        "",
        "## Interpretation",
        "",
        finding["summary"],
        "",
        "These controls are intentionally adversarial. They show that the current R1-R6 scorer is useful as a signal-extraction checklist, but not yet a semantic truth-comparison evaluator: changing/shuffling truth-set content and inverting the harness-level RULE_FACTS surrogate does not change verdicts because verdicts are derived from blind-prediction text signals. This is an evidence-hardening finding, not a product claim.",
        "",
        "Cross-case control status: `{status}` — {reason}".format(**result["controls"]["cross_case"]),
    ]
    return "\n".join(lines) + "\n"


def _score(blind_prediction: dict[str, Any], truth_set: dict[str, Any]) -> dict[str, Any]:
    backtest = backtest_module.evaluate_blind_prediction_backtest(blind_prediction=blind_prediction, truth_set=truth_set)
    verdicts = {rule["rule_id"]: rule["verdict"] for rule in backtest["rules"]}
    return {
        "case_id": backtest["case_id"],
        "hit_rate": round(_hit_rate(verdicts), 4),
        "verdicts": verdicts,
        "backtest_result": backtest,
    }


def _hit_rate(verdicts: dict[str, str]) -> float:
    return sum(1 for verdict in verdicts.values() if verdict in HIT_VERDICTS) / len(verdicts)


def _fact_to_rules() -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for rule_id, fact_ids in backtest_module.RULE_FACTS.items():
        for fact_id in fact_ids:
            output.setdefault(fact_id, []).append(rule_id)
    return output


def _joined_rule_facts(truth_set: dict[str, Any], rule_id: str) -> str:
    facts = {fact["id"]: fact for fact in truth_set.get("facts", [])}
    return " | ".join(facts[fact_id]["fact"] for fact_id in backtest_module.RULE_FACTS[rule_id] if fact_id in facts)


def make_inverted_rule_facts_control(truth_set: dict[str, Any]) -> tuple[dict[str, Any], dict[str, list[str]]]:
    control_truth = deepcopy(truth_set)
    control_truth["case_id"] = f"{truth_set['case_id']}__negative_control_inverted_rule_facts"
    control_truth["negative_control"] = "inverted_rule_facts"
    inverted_rule_facts: dict[str, list[str]] = {}
    synthetic_facts = []
    for rule_id, original_fact_ids in backtest_module.RULE_FACTS.items():
        synthetic_ids = [f"CONTROL_C_{rule_id}_{index}" for index, _ in enumerate(original_fact_ids, start=1)]
        inverted_rule_facts[rule_id] = synthetic_ids
        for fact_id in synthetic_ids:
            synthetic_facts.append(
                {
                    "id": fact_id,
                    "fact": INVERTED_RULE_OUTCOMES[rule_id],
                    "value": {"negative_control": "inverted_rule_facts", "source_rule": rule_id},
                    "sources": [],
                    "notes": "Generated only for Control C; not a real historical claim.",
                }
            )
    control_truth["facts"] = synthetic_facts
    return control_truth, inverted_rule_facts


@contextmanager
def _temporary_rule_facts(rule_facts: dict[str, list[str]]):
    original = backtest_module.RULE_FACTS
    try:
        backtest_module.RULE_FACTS = rule_facts
        yield
    finally:
        backtest_module.RULE_FACTS = original


def _format_verdicts(verdicts: dict[str, str]) -> str:
    return ", ".join(f"{rule_id}={verdict}" for rule_id, verdict in sorted(verdicts.items()))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
