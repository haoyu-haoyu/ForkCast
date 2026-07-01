from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from policy_impact_sandbox.api import create_app
from test_policy_run_pipeline import RecordingLLMClient


def test_live_policy_run_pauses_for_review_records_diff_and_resumes(tmp_path: Path) -> None:
    app = create_app(
        llm_client_factory=RecordingLLMClient,
        run_root=tmp_path / "runs",
        run_background=False,
    )
    client = TestClient(app)

    response = client.post(
        "/api/policy-runs",
        json={
            "policy_text": "Create a school street trial with exemptions and camera enforcement.",
            "agent_count": 4,
            "rounds": 2,
        },
    )

    assert response.status_code == 202
    run_id = response.json()["run_id"]
    review = client.get(f"/api/policy-runs/{run_id}").json()
    assert review["status"] == "AWAITING_REVIEW"
    assert review["case_graph_ai"]["case_id"] == "school_street_trial"

    approved_case_graph = review["case_graph_ai"]
    approved_case_graph["stakeholders"][0]["weight"] = 1.2
    patch_response = client.patch(
        f"/api/policy-runs/{run_id}",
        json={"case_graph": approved_case_graph},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["review_diff"][0]["path"] == "/stakeholders/0/weight"

    approve_response = client.post(f"/api/policy-runs/{run_id}/approve")
    assert approve_response.status_code == 202
    final = client.get(f"/api/policy-runs/{run_id}").json()
    assert final["status"] == "AWAITING_ANCHOR_APPROVAL"
    assert final["impact_report"]["stakeholder_impact_matrix"]
    assert final["audit_manifest"]["approval_event"]["diff"][0]["after"] == 1.2
    assert final["audit_manifest"]["hash_chain"]["head_hash"]
    assert (tmp_path / "runs" / run_id / "approval_event.json").exists()
    assert (tmp_path / "runs" / run_id / "audit_manifest.json").exists()


def test_live_policy_run_failed_stage_is_persisted(tmp_path: Path) -> None:
    class FailingLLMClient:
        def complete_json(self, system_prompt: str, user_prompt: str) -> str:
            raise RuntimeError("forced extractor failure")

    app = create_app(
        llm_client_factory=FailingLLMClient,
        run_root=tmp_path / "runs",
        run_background=False,
    )
    client = TestClient(app)

    response = client.post("/api/policy-runs", json={"policy_text": "A new policy text."})

    assert response.status_code == 202
    run_id = response.json()["run_id"]
    status = client.get(f"/api/policy-runs/{run_id}").json()
    assert status["status"] == "FAILED"
    assert status["failed"]["stage"] == "EXTRACTING"
    assert "forced extractor failure" in status["failed"]["error"]
    assert (tmp_path / "runs" / run_id / "status.json").exists()
