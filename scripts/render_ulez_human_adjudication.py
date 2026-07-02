from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from policy_impact_sandbox.phase2 import backtest as backtest_module


RULE_QUESTIONS = {
    "R1": "Did the blind prediction identify stronger outer-London opposition than inner-London support?",
    "R2": "Did the blind prediction single out van drivers, tradespeople, or small businesses as highly affected?",
    "R3": "Did the blind prediction identify political salience/electoral risk without claiming to predict the election result?",
    "R4": "Did the blind prediction identify enforcement resistance, camera backlash, sabotage, or vandalism risk?",
    "R5": "Did the blind prediction identify short-term backlash plus longer-term adaptation or compliance improvement?",
    "R6": "Did the blind prediction capture both air-quality/health benefits and distributional burden?",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Render ULEZ human adjudication sheet.")
    parser.add_argument("--blind-prediction", default="runs/ulez_2023_phase2_deepseek/blind_prediction.json")
    parser.add_argument("--truth-set", default="data/cases/ulez_2023/truth_set.json")
    parser.add_argument("--output", default="docs/evaluation/ulez_human_adjudication.md")
    args = parser.parse_args()

    blind_prediction = json.loads(Path(args.blind_prediction).read_text(encoding="utf-8"))
    truth_set = json.loads(Path(args.truth_set).read_text(encoding="utf-8"))
    output = render_adjudication(blind_prediction=blind_prediction, truth_set=truth_set)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")
    print(f"Wrote {output_path}")
    print(f"rules={len(RULE_QUESTIONS)}")
    return 0


def render_adjudication(blind_prediction: dict[str, Any], truth_set: dict[str, Any]) -> str:
    facts = {fact["id"]: fact for fact in truth_set.get("facts", [])}
    prediction = blind_prediction.get("prediction", {})
    lines = [
        "# ULEZ Human Adjudication Sheet",
        "",
        f"Case: `{truth_set['case_id']}`",
        "Purpose: human grading of the cached blind prediction against source-backed truth-set evidence.",
        "",
        "Instructions:",
        "",
        "- Read the cached blind prediction excerpt and the linked truth-set evidence for each rule.",
        "- Mark exactly one decision per rule: HIT, PARTIAL, or MISS.",
        "- Do not use the automated scorer verdicts while completing this sheet.",
        "- The excerpts below are copied from `blind_prediction.json`; no post-hoc prediction text is added here.",
        "",
        "Decision key: `[ ] HIT   [ ] PARTIAL   [ ] MISS`",
        "",
    ]
    for rule_id, question in RULE_QUESTIONS.items():
        lines.extend(
            [
                f"## {rule_id}",
                "",
                f"Question: {question}",
                "",
                "Cached blind prediction excerpt:",
                "",
                "```json",
                _json_excerpt(_prediction_excerpt(rule_id, prediction)),
                "```",
                "",
                "Relevant truth-set facts and evidence:",
                "",
            ]
        )
        for fact_id in backtest_module.RULE_FACTS[rule_id]:
            fact = facts[fact_id]
            lines.extend(
                [
                    f"### {fact_id}",
                    "",
                    f"- Fact: {fact['fact']}",
                    f"- Current confidence status: `{fact.get('confidence_status', '')}`",
                    "",
                    "Sources:",
                ]
            )
            for source_index, source in enumerate(fact.get("sources", []), start=1):
                lines.extend(
                    [
                        f"- Source {source_index}: {source.get('source_name', '')}",
                        f"  - URL: {source.get('url', '')}",
                        f"  - Quote: {source.get('quote', '')}",
                    ]
                )
            lines.append("")
        lines.extend(
            [
                "Human decision: [ ] HIT   [ ] PARTIAL   [ ] MISS",
                "",
                "Reviewer notes:",
                "",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _prediction_excerpt(rule_id: str, prediction: dict[str, Any]) -> Any:
    if rule_id == "R1":
        return {
            "group_reactions": _matching_reactions(prediction, ["outer_london", "inner_london"]),
        }
    if rule_id == "R2":
        return {
            "group_reactions": _matching_reactions(prediction, ["van", "trades", "small_business"]),
            "ranked_opposition_groups": prediction.get("ranked_opposition_groups", []),
        }
    if rule_id == "R3":
        return {"political_consequences": prediction.get("political_consequences", [])}
    if rule_id == "R4":
        return {"secondary_reactions": prediction.get("secondary_reactions", [])}
    if rule_id == "R5":
        return {"time_dynamics": prediction.get("time_dynamics", [])}
    if rule_id == "R6":
        return {"benefit_burden_balance": prediction.get("benefit_burden_balance", [])}
    return {}


def _matching_reactions(prediction: dict[str, Any], tokens: list[str]) -> list[Any]:
    output = []
    for reaction in prediction.get("group_reactions", []):
        text = json.dumps(reaction, ensure_ascii=False).lower().replace("_", " ")
        if any(token.replace("_", " ") in text for token in tokens):
            output.append(reaction)
    return output


def _json_excerpt(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
