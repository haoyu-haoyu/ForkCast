from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from policy_impact_sandbox.simulation.mock import DECISION_SUPPORT_DISCLAIMER


def generate_impact_report(
    case_graph: dict[str, Any],
    agents_payload: dict[str, Any],
    simulation_result: dict[str, Any],
) -> dict[str, Any]:
    signals = simulation_result.get("signals", {})
    risk_timeline = _risk_timeline(signals)
    mitigation_options = _mitigation_options()
    system_signals = _system_signals(signals)
    report = {
        "case_id": case_graph["case_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": DECISION_SUPPORT_DISCLAIMER,
        "report_mode": "mock_demo_visualization",
        "backtest_evidence": "blind_prediction.json",
        "method_note": "This impact report is generated from mock interaction events for dashboard demonstration. Historical backtest credibility is based on blind_prediction.json, not these mock events.",
        "stakeholder_impact_matrix": _stakeholder_matrix(case_graph, agents_payload, signals),
        "risk_timeline": risk_timeline,
        "mitigation_options": mitigation_options,
        "confidence_notes": [
            "Backtest comparison is directional only and does not score exact historical percentages.",
            "Political output is framed as political salience/electoral risk, not causal proof or election-result prediction.",
            "Mock simulation is used for the 2026-07-01 MVP path; OASIS live simulation remains a stretch validation.",
            "The R1-R6 backtest is scored from blind_prediction.json rather than mock simulation events.",
        ],
        "system_signals": system_signals,
        "claims_audit_table": _claims_audit_table(system_signals, risk_timeline, mitigation_options),
    }
    return report


def render_impact_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Impact Report: {report['case_id']}",
        "",
        report["disclaimer"],
        "",
        f"Mode: `{report.get('report_mode', 'unknown')}`",
        "",
        report.get("method_note", ""),
        "",
        "## System Signals",
    ]
    for rule_id, signal in report["system_signals"].items():
        lines.append(f"- {rule_id}: {signal}")
    lines.extend(["", "## Risk Timeline"])
    for item in report["risk_timeline"]:
        lines.append(f"- {item['stage']}: {item['signal']} ({item['risk_level']})")
    lines.extend(["", "## Mitigation Options"])
    for item in report["mitigation_options"]:
        lines.append(f"- {item['option']}: {item['rationale']}")
    lines.extend(
        [
            "",
            "## Claims Audit",
            "| Claim | Provenance | Evidence pointer |",
            "|---|---|---|",
        ]
    )
    for item in report.get("claims_audit_table", []):
        lines.append(
            f"| {item['claim']} | {item['provenance_class']} | {item['evidence_pointer']} |"
        )
    return "\n".join(lines) + "\n"


def _stakeholder_matrix(
    case_graph: dict[str, Any],
    agents_payload: dict[str, Any],
    signals: dict[str, str],
) -> list[dict[str, Any]]:
    agent_counts: dict[str, int] = {}
    for agent in agents_payload.get("agents", []):
        agent_counts[agent["stakeholder_id"]] = agent_counts.get(agent["stakeholder_id"], 0) + 1

    rows = []
    for stakeholder in case_graph.get("stakeholders", []):
        stakeholder_id = stakeholder["id"]
        rows.append(
            {
                "stakeholder_id": stakeholder_id,
                "name": stakeholder["name"],
                "agent_count": agent_counts.get(stakeholder_id, 0),
                "impact_level": _impact_level(stakeholder_id),
                "opposition_intensity": _opposition_intensity(stakeholder_id, stakeholder.get("stance_prior")),
                "primary_interests": stakeholder.get("interests", []),
                "qualitative_signal": _qualitative_signal(stakeholder_id, signals),
            }
        )
    return rows


def _impact_level(stakeholder_id: str) -> str:
    if stakeholder_id in {"stakeholder_van_drivers_tradespeople", "stakeholder_low_income_households"}:
        return "high"
    if stakeholder_id in {"stakeholder_outer_london_residents", "stakeholder_ulez_opponents_radical"}:
        return "high"
    return "medium"


def _opposition_intensity(stakeholder_id: str, stance_prior: str | None) -> str:
    if stakeholder_id == "stakeholder_van_drivers_tradespeople":
        return "very_high"
    if stakeholder_id in {"stakeholder_outer_london_residents", "stakeholder_low_income_households", "stakeholder_ulez_opponents_radical"}:
        return "high"
    if stance_prior == "support":
        return "low"
    return "medium"


def _qualitative_signal(stakeholder_id: str, signals: dict[str, str]) -> str:
    mapping = {
        "stakeholder_outer_london_residents": "outer-London backlash is stronger than inner-London support groups",
        "stakeholder_inner_london_residents": "inner-London support is visible through air-quality and health framing",
        "stakeholder_van_drivers_tradespeople": "van-dependent tradespeople are a high-pressure economic group",
        "stakeholder_low_income_households": "distributional burden and affordability concerns are visible",
        "stakeholder_ulez_opponents_radical": "enforcement backlash and sabotage narratives are visible",
    }
    return mapping.get(stakeholder_id, "policy salience and implementation risk are monitored")


def _risk_timeline(signals: dict[str, str]) -> list[dict[str, str]]:
    return [
        {
            "stage": "short_term",
            "signal": "outer-London and van-dependent groups show strong backlash",
            "risk_level": "high" if signals.get("outer_london_backlash") == "strong" else "medium",
        },
        {
            "stage": "implementation_period",
            "signal": "political salience and enforcement backlash require active management",
            "risk_level": "high" if signals.get("political_salience") == "top_risk" else "medium",
        },
        {
            "stage": "longer_term",
            "signal": "behavioural adaptation and compliance improvement emerge over time",
            "risk_level": "medium",
        },
    ]


def _mitigation_options() -> list[dict[str, str]]:
    return [
        {
            "option": "targeted support for van-dependent small businesses",
            "rationale": "reduces the highest-impact economic pressure without changing stakeholder weights automatically",
        },
        {
            "option": "low-income household transition assistance",
            "rationale": "addresses distributional burden while preserving air-quality objectives",
        },
        {
            "option": "visible enforcement legitimacy and camera-protection plan",
            "rationale": "responds to enforcement backlash without escalating automated actions",
        },
    ]


def _system_signals(signals: dict[str, str]) -> dict[str, str]:
    output = {}
    if signals.get("outer_london_backlash") == "strong" and signals.get("inner_london_support") == "present":
        output["R1"] = "outer-London and vehicle-dependent groups show clearly stronger opposition than inner-London support groups"
    if signals.get("van_tradespeople_pressure") == "high":
        output["R2"] = "van drivers, tradespeople and small businesses are singled out as high-impact, high-opposition economic groups"
    if signals.get("political_salience") == "top_risk":
        output["R3"] = "political salience and electoral risk are top risks; this is not a claim about a specific election result"
    if signals.get("enforcement_backlash") == "present":
        output["R4"] = "enforcement backlash, sabotage narratives and camera resistance risk are visible"
    if signals.get("behavioural_adaptation") == "present":
        output["R5"] = "short-term opposition coexists with longer-term behavioural adaptation and improving compliance"
    if signals.get("air_quality_benefit") == "present" and signals.get("distributional_burden") == "present":
        output["R6"] = "air-quality and health benefits coexist with distributional burden for lower-income and vehicle-dependent groups"
    return output


def _claims_audit_table(
    system_signals: dict[str, str],
    risk_timeline: list[dict[str, str]],
    mitigation_options: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rule_id, claim in system_signals.items():
        rows.append(
            {
                "id": f"claim_{rule_id}",
                "claim": claim,
                "provenance_class": "INFERRED-FROM-DOCUMENT",
                "evidence_pointer": _rule_evidence_pointer(rule_id),
                "evidence_fact_ids": _rule_fact_ids(rule_id),
                "source_artifact": "simulation_events.json + case_graph.json",
                "confidence": "medium",
            }
        )
    for risk in risk_timeline:
        rows.append(
            {
                "id": f"risk_{risk['stage']}",
                "claim": risk["signal"],
                "provenance_class": "INFERRED-FROM-DOCUMENT",
                "evidence_pointer": f"simulation_events.signals; risk_timeline.{risk['stage']}",
                "evidence_fact_ids": [],
                "source_artifact": "simulation_events.json",
                "confidence": "medium",
            }
        )
    for index, option in enumerate(mitigation_options, start=1):
        rows.append(
            {
                "id": f"mitigation_{index}",
                "claim": option["rationale"],
                "provenance_class": "MODEL-PRIOR",
                "evidence_pointer": f"impact_report.mitigation_options[{index - 1}]",
                "evidence_fact_ids": [],
                "source_artifact": "impact_report_generation_rule",
                "confidence": "low",
            }
        )
    return rows


def _rule_evidence_pointer(rule_id: str) -> str:
    mapping = {
        "R1": "case_graph.stakeholders.outer_london/inner_london; simulation_events.signals.outer_london_backlash",
        "R2": "case_graph.stakeholders.van_drivers_tradespeople; simulation_events.signals.van_tradespeople_pressure",
        "R3": "simulation_events.signals.political_salience; report note forbids election-result prediction",
        "R4": "simulation_events.signals.enforcement_backlash",
        "R5": "simulation_events.signals.behavioural_adaptation",
        "R6": "simulation_events.signals.air_quality_benefit + distributional_burden",
    }
    return mapping.get(rule_id, "impact_report.system_signals")


def _rule_fact_ids(rule_id: str) -> list[str]:
    mapping = {
        "R1": ["C1_public_opinion_distribution"],
        "R2": ["D1_six_month_compliance_rate_change", "A2_daily_charge"],
        "R3": ["B1_uxbridge_by_election_result", "B2_ulez_as_key_by_election_issue"],
        "R4": ["C2_camera_vandalism_and_enforcement_resistance"],
        "R5": ["D1_six_month_compliance_rate_change", "D2_non_compliant_vehicle_count_change"],
        "R6": ["D3_air_quality_and_emissions_changes", "A2_daily_charge", "C1_public_opinion_distribution"],
    }
    return mapping.get(rule_id, [])
