from __future__ import annotations

import json
from pathlib import Path

from policy_impact_sandbox.phase2.blind_prediction import (
    DeterministicBlindLLMClient,
    build_blind_prediction_prompts,
    generate_blind_prediction,
    make_blind_case_context,
)
from policy_impact_sandbox.phase2.backtest import evaluate_blind_prediction_backtest


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


def test_blind_context_excludes_truth_set_and_historical_outcome_fields() -> None:
    case_graph = json.loads(Path("data/cases/ulez_2023/case_graph.json").read_text(encoding="utf-8"))

    blind_context = make_blind_case_context(case_graph)
    serialized = json.dumps(blind_context, ensure_ascii=False)

    assert "stakeholder_van_drivers_tradespeople" in serialized
    assert "stakeholder_low_income_households" in serialized
    assert "evidence_fact_ids" not in serialized
    assert "evidence_note" not in serialized
    for token in FORBIDDEN_OUTCOME_TOKENS:
        assert token not in serialized


def test_blind_prediction_prompt_records_no_truth_set_or_outcome_tokens() -> None:
    case_graph = json.loads(Path("data/cases/ulez_2023/case_graph.json").read_text(encoding="utf-8"))
    blind_context = make_blind_case_context(case_graph)

    prompts = build_blind_prediction_prompts(blind_context)
    prompt_text = prompts["system_prompt"] + "\n" + prompts["user_prompt"]

    for token in FORBIDDEN_OUTCOME_TOKENS:
        assert token not in prompt_text
    assert "Do not use historical outcome data" in prompts["system_prompt"]


def test_blind_prediction_artifact_records_prompt_and_raw_prediction() -> None:
    case_graph = json.loads(Path("data/cases/ulez_2023/case_graph.json").read_text(encoding="utf-8"))

    artifact = generate_blind_prediction(
        case_graph=case_graph,
        llm_client=DeterministicBlindLLMClient(),
        llm_metadata={"provider": "mock", "base_url": None, "model": "deterministic_mock"},
    )

    assert artifact["mode"] == "blind_prediction"
    assert artifact["leakage_guard"]["truth_set_loaded_into_prompt"] is False
    assert "prompt" in artifact
    assert "raw_prediction" in artifact
    assert artifact["prediction"]["group_reactions"]


def test_blind_backtest_uses_prediction_not_mock_report() -> None:
    truth_set = json.loads(Path("data/cases/ulez_2023/truth_set.json").read_text(encoding="utf-8"))
    prediction = {
        "case_id": "ulez_2023_expansion",
        "prediction": {
            "group_reactions": [
                {"group_id": "stakeholder_outer_london_residents", "direction": "oppose", "intensity": "high"},
                {"group_id": "stakeholder_inner_london_residents", "direction": "support", "intensity": "medium"},
                {"group_id": "stakeholder_van_drivers_tradespeople", "direction": "oppose", "intensity": "very_high"},
                {"group_id": "stakeholder_low_income_households", "direction": "oppose", "intensity": "high"},
            ],
            "ranked_opposition_groups": ["stakeholder_van_drivers_tradespeople", "stakeholder_outer_london_residents"],
            "political_consequences": ["political salience and electoral risk"],
            "time_dynamics": ["short-term backlash followed by gradual adaptation and compliance"],
            "secondary_reactions": ["possible enforcement resistance and camera sabotage narratives"],
            "benefit_burden_balance": ["air quality and health benefit", "distributional burden for low-income households"],
        },
    }

    result = evaluate_blind_prediction_backtest(blind_prediction=prediction, truth_set=truth_set)

    assert result["backtest_mode"] == "blind_prediction"
    verdicts = {rule["rule_id"]: rule["verdict"] for rule in result["rules"]}
    assert verdicts["R1"] == "HIT"
    assert verdicts["R2"] == "HIT"
    assert verdicts["R3"] == "HIT"
    assert verdicts["R4"] == "HIT"
    assert verdicts["R5"] == "HIT"
    assert verdicts["R6"] == "BALANCED HIT"
