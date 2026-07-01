from __future__ import annotations

import json
from pathlib import Path

from policy_impact_sandbox.phase2.audit import build_audit_manifest, canonical_sha256
from policy_impact_sandbox.phase2.backtest import evaluate_backtest, render_backtest_markdown
from policy_impact_sandbox.phase2.chat import answer_persona_question
from policy_impact_sandbox.phase2.report import generate_impact_report


def test_report_and_backtest_follow_rubric_verdicts() -> None:
    truth_set = json.loads(Path("data/cases/ulez_2023/truth_set.json").read_text(encoding="utf-8"))
    simulation_result = {
        "signals": {
            "outer_london_backlash": "strong",
            "inner_london_support": "present",
            "van_tradespeople_pressure": "high",
            "political_salience": "top_risk",
            "enforcement_backlash": "present",
            "behavioural_adaptation": "present",
            "air_quality_benefit": "present",
            "distributional_burden": "present",
        }
    }
    agents_payload = {
        "agents": [
            {
                "id": "agent_van_001",
                "stakeholder_id": "stakeholder_van_drivers_tradespeople",
                "archetype": "Self-employed van tradesperson",
                "stance": "strongly_oppose",
                "concerns": ["operating_cost"],
            }
        ]
    }

    report = generate_impact_report(
        case_graph={"case_id": "ulez_2023_expansion", "stakeholders": []},
        agents_payload=agents_payload,
        simulation_result=simulation_result,
    )
    result = evaluate_backtest(report=report, truth_set=truth_set)

    verdicts = {item["rule_id"]: item["verdict"] for item in result["rules"]}
    assert verdicts == {
        "R1": "HIT",
        "R2": "HIT",
        "R3": "HIT",
        "R4": "HIT",
        "R5": "HIT",
        "R6": "BALANCED HIT",
    }
    assert "political salience" in result["rules"][2]["note"]
    assert "495" not in result["rules"][2]["system_signal"]
    markdown = render_backtest_markdown(result)
    assert "BALANCED HIT" in markdown
    assert "decision support" in markdown


def test_persona_chat_uses_agent_persona_without_pii() -> None:
    agent = {
        "id": "agent_low_income_001",
        "persona": "Low-income outer London household relying on an older car for shift work.",
        "stance": "oppose",
        "concerns": ["vehicle_replacement_affordability", "policy_fairness"],
        "action_tendency": "raise fairness concerns and seek mitigation",
    }

    answer = answer_persona_question(agent, "Why do you oppose this?")

    assert "agent_low_income_001" in answer["agent_id"]
    assert "vehicle_replacement_affordability" in answer["answer"]
    assert "archetype" in answer["safety_note"]


def test_audit_manifest_hashes_canonical_json() -> None:
    payload = {"b": 2, "a": 1}
    digest = canonical_sha256(payload)
    assert digest == canonical_sha256({"a": 1, "b": 2})

    manifest = build_audit_manifest(
        case_id="ulez_2023_expansion",
        run_id="phase2_test",
        artifacts={"agents": ("runs/phase2_test/agents.json", payload)},
    )

    assert manifest["entries"][0]["hash"] == digest
    assert manifest["entries"][0]["approval"] == "not_on_chain"
