from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


CASE_DIR = Path("data/cases/congestion_charge_2003")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_congestion_charge_truth_set_is_draft_and_schema_valid() -> None:
    schema = _read_json(Path("schemas/truth_set.schema.json"))
    truth_set = _read_json(CASE_DIR / "truth_set.json")

    Draft202012Validator(schema).validate(truth_set)
    assert truth_set["case_id"] == "london_congestion_charge_2003"
    assert truth_set["verification_policy"] == "DRAFT — PENDING HUMAN VERIFICATION"
    assert truth_set["headline_excluded"] is True
    assert len(truth_set["facts"]) >= 6
    assert all(fact["confidence_status"] == "待核实" for fact in truth_set["facts"])
    assert all(fact.get("headline_excluded") is True for fact in truth_set["facts"])
    assert all(fact["sources"] for fact in truth_set["facts"])
    assert all(source["url"].startswith("https://") for fact in truth_set["facts"] for source in fact["sources"])
    assert all(source["quote"] for fact in truth_set["facts"] for source in fact["sources"])


def test_congestion_charge_case_graph_is_schema_valid_and_draft_flagged() -> None:
    schema = _read_json(Path("schemas/case_graph.schema.json"))
    case_graph = _read_json(CASE_DIR / "case_graph.json")

    Draft202012Validator(schema).validate(case_graph)
    assert case_graph["case_id"] == "london_congestion_charge_2003"
    assert case_graph["verification_policy"] == "DRAFT — PENDING HUMAN VERIFICATION"
    assert case_graph["headline_excluded"] is True
    assert len(case_graph["stakeholders"]) >= 6
    assert any(stakeholder["id"] == "stakeholder_central_london_drivers" for stakeholder in case_graph["stakeholders"])
    assert any(stakeholder["id"] == "stakeholder_bus_public_transport_users" for stakeholder in case_graph["stakeholders"])


def test_congestion_charge_seed_and_sources_mark_case_as_non_headline() -> None:
    seed = (CASE_DIR / "seed_policy.md").read_text(encoding="utf-8")
    sources = (CASE_DIR / "sources.md").read_text(encoding="utf-8")

    assert "DRAFT — PENDING HUMAN VERIFICATION" in seed
    assert "DRAFT — PENDING HUMAN VERIFICATION" in sources
    assert "excluded from headline numbers" in sources


def test_congestion_charge_mock_run_exists_as_plumbing_only() -> None:
    run_dir = Path("runs/congestion_charge_2003_draft_mock")
    readme = (run_dir / "README.md").read_text(encoding="utf-8")
    blind_prediction = _read_json(run_dir / "blind_prediction.json")
    backtest_result = _read_json(run_dir / "backtest_result.json")
    audit_manifest = _read_json(run_dir / "audit_manifest.json")

    assert "DRAFT — PENDING HUMAN VERIFICATION" in readme
    assert "plumbing test only" in readme
    assert blind_prediction["case_id"] == "london_congestion_charge_2003"
    prediction_text = json.dumps(blind_prediction["prediction"], ensure_ascii=False)
    assert "stakeholder_central_london_drivers" in prediction_text
    assert "stakeholder_bus_public_transport_users" in prediction_text
    assert "stakeholder_outer_london_residents" not in prediction_text
    assert "stakeholder_van_drivers_tradespeople" not in prediction_text
    assert backtest_result["case_id"] == "london_congestion_charge_2003"
    assert backtest_result["backtest_mode"] == "blind_prediction_draft_not_scored"
    assert {item["verdict"] for item in backtest_result["rules"]} == {"NOT_SCORED"}
    assert {item["system_signal"] for item in backtest_result["rules"]} == {""}
    assert audit_manifest["case_id"] == "london_congestion_charge_2003"


def test_congestion_charge_verification_checklist_covers_all_draft_facts() -> None:
    truth_set = _read_json(CASE_DIR / "truth_set.json")
    checklist = Path("docs/evaluation/cc2003_verification_checklist.md").read_text(encoding="utf-8")

    assert "CC 2003 Truth-Set Human Verification Checklist" in checklist
    assert "Current headline_excluded: `True`" in checklist
    assert "CONFIRM" in checklist
    assert "REJECT" in checklist
    assert "EDIT" in checklist
    for fact in truth_set["facts"]:
        assert fact["id"] in checklist
        assert fact["fact"] in checklist
        for source in fact["sources"]:
            assert source["url"] in checklist
            assert source["quote"] in checklist
