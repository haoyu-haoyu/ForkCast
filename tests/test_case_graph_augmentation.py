from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from policy_impact_sandbox.phase1.augment import MISSING_STAKEHOLDERS, augment_missing_stakeholders


def test_augment_missing_stakeholders_adds_van_and_low_income_groups() -> None:
    case_graph = json.loads(Path("data/cases/ulez_2023/case_graph.json").read_text(encoding="utf-8"))
    missing_ids = {stakeholder["id"] for stakeholder in MISSING_STAKEHOLDERS}
    case_graph["stakeholders"] = [
        stakeholder for stakeholder in case_graph["stakeholders"] if stakeholder["id"] not in missing_ids
    ]
    case_graph["graph"] = {"nodes": [], "edges": []}
    original_count = len(case_graph["stakeholders"])

    augmented = augment_missing_stakeholders(case_graph)

    stakeholders = {item["id"]: item for item in augmented["stakeholders"]}
    assert len(stakeholders) == original_count + 2
    assert stakeholders["stakeholder_van_drivers_tradespeople"]["archetype_group"] == "affected_business"
    assert stakeholders["stakeholder_van_drivers_tradespeople"]["stance_prior"] == "oppose"
    assert "D1_six_month_compliance_rate_change" in stakeholders["stakeholder_van_drivers_tradespeople"]["evidence_fact_ids"]
    assert stakeholders["stakeholder_low_income_households"]["archetype_group"] == "affected_public"
    assert stakeholders["stakeholder_low_income_households"]["stance_prior"] == "oppose"
    assert "A2_daily_charge" in stakeholders["stakeholder_low_income_households"]["evidence_fact_ids"]

    node_ids = {node["id"] for node in augmented["graph"]["nodes"]}
    assert "stakeholder:stakeholder_van_drivers_tradespeople" in node_ids
    assert "stakeholder:stakeholder_low_income_households" in node_ids
    assert len(augmented["stakeholders"]) == 9


def test_augmented_case_graph_validates_against_schema() -> None:
    case_graph = json.loads(Path("data/cases/ulez_2023/case_graph.json").read_text(encoding="utf-8"))
    augmented = augment_missing_stakeholders(case_graph)
    schema = json.loads(Path("schemas/case_graph.schema.json").read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(augmented)
