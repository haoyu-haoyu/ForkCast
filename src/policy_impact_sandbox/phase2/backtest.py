from __future__ import annotations

from typing import Any

from policy_impact_sandbox.simulation.mock import DECISION_SUPPORT_DISCLAIMER


RULE_FACTS = {
    "R1": ["C1_public_opinion_distribution"],
    "R2": ["D1_six_month_compliance_rate_change"],
    "R3": ["B1_uxbridge_by_election_result", "B2_ulez_as_key_by_election_issue"],
    "R4": ["C2_camera_vandalism_and_enforcement_resistance"],
    "R5": ["D1_six_month_compliance_rate_change", "D2_non_compliant_vehicle_count_change"],
    "R6": ["D3_air_quality_and_emissions_changes", "A2_daily_charge", "C1_public_opinion_distribution"],
}


def evaluate_backtest(report: dict[str, Any], truth_set: dict[str, Any]) -> dict[str, Any]:
    signals = report.get("system_signals", {})
    facts = {fact["id"]: fact for fact in truth_set.get("facts", [])}
    rules = [
        _rule("R1", facts, signals, "HIT" if "R1" in signals else "MISS", "Direction only: checks outer > inner opposition split."),
        _rule("R2", facts, signals, "HIT" if "R2" in signals else "MISS", "Requires van/tradespeople/small business group to be singled out."),
        _rule(
            "R3",
            facts,
            signals,
            "HIT" if "R3" in signals else "MISS",
            "Counts political salience/electoral risk only; not causal proof and not an election result prediction.",
        ),
        _rule("R4", facts, signals, "HIT" if "R4" in signals else "MISS", "Checks enforcement backlash or sabotage-risk signal."),
        _rule("R5", facts, signals, "HIT" if "R5" in signals else "MISS", "Checks short-term opposition plus longer-term adaptation direction."),
        _rule("R6", facts, signals, _r6_verdict(signals), "BALANCED HIT requires both air-quality benefit and distributional burden."),
    ]
    return {
        "case_id": truth_set["case_id"],
        "backtest_mode": "mock_demo_signals",
        "disclaimer": DECISION_SUPPORT_DISCLAIMER,
        "rubric_path": "backtest_rubric.md",
        "rules": rules,
    }


def evaluate_blind_prediction_backtest(blind_prediction: dict[str, Any], truth_set: dict[str, Any]) -> dict[str, Any]:
    prediction = blind_prediction.get("prediction", {})
    signals = _blind_prediction_signals(prediction)
    if truth_set.get("headline_excluded") is True:
        return _draft_not_scored_result(truth_set, signals)
    facts = {fact["id"]: fact for fact in truth_set.get("facts", [])}
    rules = [
        _rule("R1", facts, signals, _verdict_for(signals, "R1"), "Blind prediction is checked for outer-London opposition stronger than inner-London support."),
        _rule("R2", facts, signals, _verdict_for(signals, "R2"), "Blind prediction must single out van drivers/tradespeople/small businesses; generic vehicle cost pressure is only partial."),
        _rule(
            "R3",
            facts,
            signals,
            _verdict_for(signals, "R3"),
            "Counts political salience/electoral risk only; not causal proof and not an election result prediction.",
        ),
        _rule("R4", facts, signals, _verdict_for(signals, "R4"), "Blind prediction is checked for enforcement resistance, sabotage, or camera backlash."),
        _rule("R5", facts, signals, _verdict_for(signals, "R5"), "Blind prediction is checked for short-term opposition plus longer-term adaptation/compliance direction."),
        _rule("R6", facts, signals, _r6_blind_verdict(signals), "BALANCED HIT requires both air-quality/health benefit and fairness/distributional burden."),
    ]
    return {
        "case_id": truth_set["case_id"],
        "backtest_mode": "blind_prediction",
        "prediction_artifact": "blind_prediction.json",
        "disclaimer": DECISION_SUPPORT_DISCLAIMER,
        "rubric_path": "backtest_rubric.md",
        "rules": rules,
    }


def _draft_not_scored_result(truth_set: dict[str, Any], signals: dict[str, str]) -> dict[str, Any]:
    note = "Draft truth set pending human verification; excluded from headline numbers."
    rules = [
        {
            "rule_id": rule_id,
            "real_outcome": note,
            "system_signal": "",
            "verdict": "NOT_SCORED",
            "note": note,
        }
        for rule_id in RULE_FACTS
    ]
    return {
        "case_id": truth_set["case_id"],
        "backtest_mode": "blind_prediction_draft_not_scored",
        "prediction_artifact": "blind_prediction.json",
        "disclaimer": DECISION_SUPPORT_DISCLAIMER,
        "rubric_path": "backtest_rubric.md",
        "headline_excluded": True,
        "verification_policy": truth_set.get("verification_policy", "DRAFT — PENDING HUMAN VERIFICATION"),
        "rules": rules,
    }


def render_backtest_markdown(result: dict[str, Any]) -> str:
    title = (
        "Draft Blind Prediction Plumbing Check"
        if result.get("backtest_mode") == "blind_prediction_draft_not_scored"
        else "Blind Prediction Backtest"
        if result.get("backtest_mode") == "blind_prediction"
        else "Backtest"
    )
    lines = [
        f"# {title}: {result['case_id']}",
        "",
        result["disclaimer"],
        "",
        f"Backtest mode: `{result.get('backtest_mode', 'unknown')}`",
        "",
        "| Rule | Verdict | System signal | Real outcome | Note |",
        "|---|---|---|---|---|",
    ]
    for item in result["rules"]:
        lines.append(
            "| {rule_id} | {verdict} | {system_signal} | {real_outcome} | {note} |".format(
                rule_id=item["rule_id"],
                verdict=item["verdict"],
                system_signal=_escape_table(item["system_signal"]),
                real_outcome=_escape_table(item["real_outcome"]),
                note=_escape_table(item["note"]),
            )
        )
    lines.extend(
        [
            "",
            "This table compares qualitative blind-prediction signals against verified historical outcomes.",
            "It does not claim to predict exact numbers.",
        ]
    )
    return "\n".join(lines) + "\n"


def _rule(
    rule_id: str,
    facts: dict[str, dict[str, Any]],
    signals: dict[str, str],
    verdict: str,
    note: str,
) -> dict[str, str]:
    return {
        "rule_id": rule_id,
        "real_outcome": " | ".join(facts[fact_id]["fact"] for fact_id in RULE_FACTS[rule_id] if fact_id in facts),
        "system_signal": signals.get(rule_id, ""),
        "verdict": verdict,
        "note": note,
    }


def _blind_prediction_signals(prediction: dict[str, Any]) -> dict[str, str]:
    text = _prediction_text(prediction)
    group_reactions = prediction.get("group_reactions", [])
    outer_hit = _group_direction(group_reactions, "outer_london", {"oppose", "opposed", "opposition"}, {"high", "very_high", "strong"})
    inner_support = _group_direction(group_reactions, "inner_london", {"support", "supported"}, {"medium", "high", "strong"})
    van_hit = "van" in text and any(term in text for term in ["trades", "tradespeople", "small business", "small businesses"]) and _has_high_opposition_text(text)
    political_hit = any(term in text for term in ["political salience", "electoral risk", "political risk", "election salience"])
    enforcement_hit = any(term in text for term in ["enforcement resistance", "sabotage", "camera", "vandal"])
    adaptation_hit = any(term in text for term in ["adaptation", "adapt", "compliance", "behavioural change", "behavioral change"]) and any(
        term in text for term in ["over time", "longer-term", "long term", "gradual"]
    )
    benefit_hit = any(term in text for term in ["air quality", "health benefit", "public health", "emissions"])
    burden_hit = any(term in text for term in ["distributional", "fairness", "low-income", "low income", "affordability", "burden"])

    signals: dict[str, str] = {}
    if outer_hit and inner_support:
        signals["R1"] = "Blind prediction identifies stronger outer-London/vehicle-dependent opposition than inner-London support groups."
    elif outer_hit:
        signals["R1"] = "Blind prediction identifies outer-London opposition but inner-London contrast is weak."
        signals["_R1_partial"] = "true"
    if van_hit:
        signals["R2"] = "Blind prediction singles out van drivers, tradespeople or small businesses as high-opposition/high-impact groups."
    elif "business" in text or "vehicle-dependent" in text:
        signals["R2"] = "Blind prediction mentions business or vehicle-dependent burden but does not clearly single out vans/tradespeople."
        signals["_R2_partial"] = "true"
    if political_hit:
        signals["R3"] = "Blind prediction flags political salience/electoral risk without claiming a specific election result."
    if enforcement_hit:
        signals["R4"] = "Blind prediction flags enforcement resistance, sabotage, camera backlash or vandalism risk."
    if adaptation_hit:
        signals["R5"] = "Blind prediction flags short-term backlash with longer-term adaptation/compliance improvement."
    if benefit_hit and burden_hit:
        signals["R6"] = "Blind prediction captures both air-quality/health benefits and distributional fairness burden."
    elif benefit_hit or burden_hit:
        signals["R6"] = "Blind prediction captures only one side of benefit/burden balance."
        signals["_R6_partial"] = "true"
    return signals


def _prediction_text(prediction: dict[str, Any]) -> str:
    return str(prediction).lower().replace("_", " ")


def _group_direction(
    reactions: list[Any],
    group_token: str,
    directions: set[str],
    intensities: set[str],
) -> bool:
    token = group_token.replace("_", " ")
    for reaction in reactions:
        if not isinstance(reaction, dict):
            continue
        group_id = str(reaction.get("group_id") or reaction.get("group") or "").lower().replace("_", " ")
        if token not in group_id:
            continue
        direction = str(reaction.get("direction", "")).lower().replace("_", " ")
        intensity = str(reaction.get("intensity", "")).lower().replace(" ", "_")
        if any(item in direction for item in directions) and intensity in intensities:
            return True
    return False


def _has_high_opposition_text(text: str) -> bool:
    return any(term in text for term in ["very high", "high", "strong", "strongest", "oppose", "opposition"])


def _verdict_for(signals: dict[str, str], rule_id: str) -> str:
    if rule_id in signals and signals.get(f"_{rule_id}_partial") == "true":
        return "PARTIAL"
    if rule_id in signals:
        return "HIT"
    return "MISS"


def _r6_verdict(signals: dict[str, str]) -> str:
    if "R6" in signals:
        return "BALANCED HIT"
    return "MISS"


def _r6_blind_verdict(signals: dict[str, str]) -> str:
    if "R6" in signals and signals.get("_R6_partial") == "true":
        return "PARTIAL"
    if "R6" in signals:
        return "BALANCED HIT"
    return "MISS"


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
