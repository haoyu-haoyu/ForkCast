from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from policy_impact_sandbox.api import create_app
from policy_impact_sandbox.phase2.audit import build_chained_audit_manifest
from policy_impact_sandbox.phase4.kaspa_anchor import build_kaspa_anchor_record


class UnusedLLMClient:
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        raise AssertionError("verify API must not call the LLM")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_chained_run(run_root: Path, run_id: str = "policy_run_test") -> tuple[Path, dict]:
    run_dir = run_root / run_id
    run_dir.mkdir(parents=True)
    artifacts = {
        "policy_input": (str(run_dir / "input.json"), {"policy_text": "School street trial"}),
        "case_graph_ai": (str(run_dir / "case_graph_ai.json"), {"case_id": "school_street_trial"}),
        "approval_event": (
            str(run_dir / "approval_event.json"),
            {
                "timestamp": "2026-07-02T00:00:00+00:00",
                "stage": "case_graph_review",
                "editor": "human",
                "actor": "human",
                "diff": [{"path": "/stakeholders/0/weight", "before": 1.0, "after": 1.2}],
                "approved_hash": "approved-hash",
            },
        ),
        "simulation_outputs": (str(run_dir / "simulation_outputs.json"), {"events": []}),
        "report": (str(run_dir / "impact_report.json"), {"risk_timeline": []}),
    }
    for artifact_uri, payload in artifacts.values():
        _write_json(Path(artifact_uri), payload)
    manifest = build_chained_audit_manifest(case_id="school_street_trial", run_id=run_id, artifacts=artifacts)
    _write_json(run_dir / "audit_manifest.json", manifest)
    anchor = build_kaspa_anchor_record(manifest, str(run_dir / "audit_manifest.json"), tx_id="tx123")
    _write_json(run_dir / "kaspa_anchor.json", anchor)
    return run_dir, anchor


def test_verify_anchor_api_returns_json_and_caches_network_fetch(tmp_path: Path) -> None:
    run_dir, anchor = _write_chained_run(tmp_path / "runs")
    calls: list[tuple[str, str]] = []

    def fetch_payload_hex(txid: str, network: str) -> str:
        calls.append((txid, network))
        return anchor["payload_canonical_json"].encode("utf-8").hex()

    app = create_app(
        llm_client_factory=UnusedLLMClient,
        run_root=tmp_path / "runs",
        run_background=False,
        verify_payload_fetcher=fetch_payload_hex,
    )
    client = TestClient(app)

    first = client.get(f"/api/anchors/{run_dir.name}/verify")
    second = client.get(f"/api/anchors/{run_dir.name}/verify")

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["overall"] == "PASS"
    assert first.json()["mode"] == "hash_chain_head"
    assert first.json()["cache"]["hit"] is False
    assert second.json()["cache"]["hit"] is True
    assert calls == [("tx123", "testnet-10")]


def test_verify_anchor_api_reports_missing_anchor(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "missing_anchor_run"
    run_dir.mkdir(parents=True)
    _write_json(run_dir / "audit_manifest.json", {"entries": []})

    app = create_app(llm_client_factory=UnusedLLMClient, run_root=tmp_path / "runs", run_background=False)
    client = TestClient(app)

    response = client.get("/api/anchors/missing_anchor_run/verify")

    assert response.status_code == 404
    assert "kaspa_anchor.json" in response.json()["detail"]


def test_verify_anchor_api_supports_legacy_manifest_anchor() -> None:
    anchor = json.loads(Path("runs/ulez_2023_phase2_deepseek/kaspa_anchor.json").read_text(encoding="utf-8"))
    app = create_app(
        llm_client_factory=UnusedLLMClient,
        run_root="runs",
        run_background=False,
        verify_payload_fetcher=lambda txid, network: anchor["payload_canonical_json"].encode("utf-8").hex(),
    )
    client = TestClient(app)

    response = client.get("/api/anchors/ulez_2023_phase2_deepseek/verify")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["overall"] == "PASS"
    assert payload["mode"] == "legacy_manifest_hash"
    assert payload["txid"] == anchor["tx_id"]
