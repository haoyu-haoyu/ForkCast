from __future__ import annotations

from fastapi.testclient import TestClient

from policy_impact_sandbox.api import create_app
from test_policy_run_pipeline import RecordingLLMClient


def test_policy_run_api_returns_impact_analysis_without_backtest() -> None:
    app = create_app(llm_client_factory=RecordingLLMClient)
    client = TestClient(app)

    response = client.post(
        "/api/policy-runs",
        json={
            "policy_text": "Create a low-traffic neighbourhood trial with camera enforcement and exemptions.",
            "agent_count": 4,
            "rounds": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["truth_set_status"]["message"] == "无历史回测数据，仅提供影响分析"
    assert payload["backtest_result"] is None
    assert payload["case_graph"]["stakeholders"]
    assert payload["impact_report"]["stakeholder_impact_matrix"]


def test_policy_run_api_rejects_empty_policy_text() -> None:
    app = create_app(llm_client_factory=RecordingLLMClient)
    client = TestClient(app)

    response = client.post("/api/policy-runs", json={"policy_text": "   "})

    assert response.status_code == 400
    assert "policy_text is required" in response.json()["detail"]
