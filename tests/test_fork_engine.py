from __future__ import annotations

import json
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from policy_impact_sandbox.api import create_app
from policy_impact_sandbox.phase2.audit import canonical_sha256


class ChargeAwareLLMClient:
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        if "synthetic archetype agent profiles" in system_prompt.lower():
            return json.dumps({"agents": []})
        if "impact report" in system_prompt.lower():
            high_charge = "£15.00" in user_prompt
            return json.dumps(
                {
                    "stakeholder_impact_matrix": [
                        {
                            "stakeholder_id": "stakeholder_outer_london_residents",
                            "name": "Outer London residents",
                            "impact_level": "high" if high_charge else "medium",
                            "opposition_intensity": "high" if high_charge else "medium",
                            "qualitative_signal": (
                                "Higher charge variant increases household cost pressure."
                                if high_charge
                                else "Baseline charge keeps pressure material but bounded."
                            ),
                        },
                        {
                            "stakeholder_id": "stakeholder_van_drivers_tradespeople",
                            "name": "Van drivers / tradespeople / small businesses",
                            "impact_level": "high",
                            "opposition_intensity": "very_high" if high_charge else "high",
                            "qualitative_signal": (
                                "£15.00 daily charge materially raises operating-cost backlash."
                                if high_charge
                                else "£12.50 daily charge creates strong operating-cost objections."
                            ),
                        },
                    ],
                    "risk_timeline": [
                        {
                            "stage": "implementation_period",
                            "signal": (
                                "£15.00 daily charge raises enforcement and affordability risk."
                                if high_charge
                                else "£12.50 daily charge creates baseline affordability risk."
                            ),
                            "risk_level": "high" if high_charge else "medium",
                        }
                    ],
                    "mitigation_options": [
                        {
                            "option": "targeted scrappage support",
                            "rationale": "Offset concentrated vehicle replacement pressure.",
                        }
                    ],
                    "confidence_notes": ["Mock fork comparison report for charge sensitivity."],
                    "claims_audit_table": [
                        {
                            "id": "claim_charge_pressure",
                            "claim": (
                                "Charge sensitivity increases concentrated pressure on van drivers."
                                if high_charge
                                else "Baseline charge pressure remains concentrated in cost-exposed groups."
                            ),
                            "provenance_class": "INFERRED-FROM-DOCUMENT",
                            "evidence_pointer": "scenario_variant.charge",
                            "evidence_fact_ids": [],
                            "source_artifact": "case_graph_approved.json",
                            "confidence": "medium",
                        }
                    ],
                }
            )
        raise AssertionError(system_prompt)


def _copy_cached_ulez_parent(tmp_path: Path) -> Path:
    run_root = tmp_path / "runs"
    parent = run_root / "ulez_2023_phase2_deepseek"
    parent.mkdir(parents=True)
    shutil.copyfile("runs/ulez_2023_phase2_deepseek/audit_manifest.json", parent / "audit_manifest.json")
    return run_root


def test_fork_cached_ulez_charge_variants_and_compare_returns_ui_ready_diff(tmp_path: Path) -> None:
    app = create_app(
        llm_client_factory=ChargeAwareLLMClient,
        run_root=_copy_cached_ulez_parent(tmp_path),
        run_background=False,
    )
    client = TestClient(app)

    baseline = client.post(
        "/api/policy-runs/ulez_2023_phase2_deepseek/forks",
        json={
            "name": "charge £12.50",
            "case_graph_patches": [{"op": "add", "path": "/scenario_variant", "value": {"charge": "£12.50"}}],
        },
    )
    higher = client.post(
        "/api/policy-runs/ulez_2023_phase2_deepseek/forks",
        json={
            "name": "charge £15.00",
            "case_graph_patches": [{"op": "add", "path": "/scenario_variant", "value": {"charge": "£15.00"}}],
        },
    )

    assert baseline.status_code == 202, baseline.text
    assert higher.status_code == 202, higher.text
    fork_a = baseline.json()["fork_id"]
    fork_b = higher.json()["fork_id"]
    fork_dir = tmp_path / "runs" / "ulez_2023_phase2_deepseek" / "forks" / fork_b
    manifest = json.loads((fork_dir / "audit_manifest.json").read_text(encoding="utf-8"))

    assert baseline.json()["status"] == "AWAITING_ANCHOR_APPROVAL"
    assert manifest["fork_lineage"]["parent_run_id"] == "ulez_2023_phase2_deepseek"
    assert manifest["hash_chain"]["links"][0]["id"] == "h0'"
    assert manifest["hash_chain"]["links"][0]["stage"] == "fork_lineage"
    assert manifest["hash_chain"]["links"][0]["hash"] == manifest["fork_lineage"]["fork_root_hash"]
    assert manifest["approval_event"]["actor"] == "human"
    assert (fork_dir / "case_graph_approved.json").exists()
    assert (fork_dir / "simulation_outputs.json").exists()

    compare = client.get(
        f"/api/policy-runs/ulez_2023_phase2_deepseek/forks/compare?a={fork_a}&b={fork_b}"
    )

    assert compare.status_code == 200, compare.text
    payload = compare.json()
    assert payload["parent_run_id"] == "ulez_2023_phase2_deepseek"
    assert payload["a"]["fork_id"] == fork_a
    assert payload["b"]["fork_id"] == fork_b
    assert set(payload["dimensions"]) == {"risk_timeline", "claims", "stakeholder_pressure"}
    assert payload["summary"]["changed"] >= 1
    assert payload["dimensions"]["risk_timeline"][0]["status"] == "changed"
    assert payload["dimensions"]["risk_timeline"][0]["a"]["risk_level"] == "medium"
    assert payload["dimensions"]["risk_timeline"][0]["b"]["risk_level"] == "high"
    assert payload["dimensions"]["stakeholder_pressure"][0]["changed_fields"]


def test_fork_rejects_invalid_patch_without_writing_fork(tmp_path: Path) -> None:
    app = create_app(
        llm_client_factory=ChargeAwareLLMClient,
        run_root=_copy_cached_ulez_parent(tmp_path),
        run_background=False,
    )
    client = TestClient(app)

    response = client.post(
        "/api/policy-runs/ulez_2023_phase2_deepseek/forks",
        json={
            "name": "bad patch",
            "case_graph_patches": [{"op": "replace", "path": "/stakeholders/999/name", "value": "Missing"}],
        },
    )

    assert response.status_code == 400
    assert "patch" in response.json()["detail"].lower()
    assert not (tmp_path / "runs" / "ulez_2023_phase2_deepseek" / "forks").exists()


def test_fork_lineage_hash_changes_when_patch_changes(tmp_path: Path) -> None:
    app = create_app(
        llm_client_factory=ChargeAwareLLMClient,
        run_root=_copy_cached_ulez_parent(tmp_path),
        run_background=False,
    )
    client = TestClient(app)

    first = client.post(
        "/api/policy-runs/ulez_2023_phase2_deepseek/forks",
        json={
            "name": "charge £12.50",
            "case_graph_patches": [{"op": "add", "path": "/scenario_variant", "value": {"charge": "£12.50"}}],
        },
    ).json()
    second = client.post(
        "/api/policy-runs/ulez_2023_phase2_deepseek/forks",
        json={
            "name": "charge £15.00",
            "case_graph_patches": [{"op": "add", "path": "/scenario_variant", "value": {"charge": "£15.00"}}],
        },
    ).json()

    parent = tmp_path / "runs" / "ulez_2023_phase2_deepseek" / "forks"
    first_manifest = json.loads((parent / first["fork_id"] / "audit_manifest.json").read_text(encoding="utf-8"))
    second_manifest = json.loads((parent / second["fork_id"] / "audit_manifest.json").read_text(encoding="utf-8"))

    assert first_manifest["fork_lineage"]["fork_root_hash"] != second_manifest["fork_lineage"]["fork_root_hash"]
    assert first_manifest["fork_lineage"]["parent_head"] == canonical_sha256(
        json.loads((tmp_path / "runs" / "ulez_2023_phase2_deepseek" / "audit_manifest.json").read_text())
    )
