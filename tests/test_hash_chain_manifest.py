from __future__ import annotations

from policy_impact_sandbox.phase2.audit import build_chained_audit_manifest, compute_hash_chain


def test_hash_chain_head_changes_when_approval_event_is_tampered() -> None:
    policy_input = {"policy_text": "Create a school street trial.", "agent_count": 12, "rounds": 2}
    case_graph_ai = {
        "case_id": "school_street_trial",
        "stakeholders": [{"id": "parents", "name": "Parents", "weight": 1.0}],
    }
    approval_event = {
        "timestamp": "2026-07-02T00:00:00+00:00",
        "stage": "case_graph_review",
        "editor": "human",
        "diff": [{"path": "/stakeholders/0/weight", "before": None, "after": 1.2}],
        "approved_hash": "approved-hash",
    }
    simulation_outputs = {"events": [{"event_id": "e1"}]}
    report = {"risk_timeline": [{"stage": "implementation", "risk_level": "medium"}]}

    original = compute_hash_chain(
        policy_input=policy_input,
        case_graph_ai=case_graph_ai,
        approval_event=approval_event,
        simulation_outputs=simulation_outputs,
        report=report,
    )
    tampered = compute_hash_chain(
        policy_input=policy_input,
        case_graph_ai=case_graph_ai,
        approval_event={**approval_event, "editor": "robot"},
        simulation_outputs=simulation_outputs,
        report=report,
    )

    assert original["head_hash"] != tampered["head_hash"]
    assert [link["id"] for link in original["links"]] == ["h0", "h1", "h2", "h3", "h4"]
    assert original["links"][2]["stage"] == "approval_event"


def test_chained_manifest_contains_approval_diff_and_head_hash() -> None:
    manifest = build_chained_audit_manifest(
        case_id="school_street_trial",
        run_id="policy_run_test",
        artifacts={
            "policy_input": ("runs/policy_run_test/input.json", {"policy_text": "Create a school street trial."}),
            "case_graph_ai": ("runs/policy_run_test/case_graph_ai.json", {"case_id": "school_street_trial"}),
            "approval_event": (
                "runs/policy_run_test/approval_event.json",
                {
                    "timestamp": "2026-07-02T00:00:00+00:00",
                    "stage": "case_graph_review",
                    "editor": "human",
                    "diff": [{"path": "/stakeholders/0/weight", "before": None, "after": 1.2}],
                    "approved_hash": "approved-hash",
                },
            ),
            "simulation_outputs": ("runs/policy_run_test/simulation_outputs.json", {"events": []}),
            "report": ("runs/policy_run_test/impact_report.json", {"risk_timeline": []}),
        },
    )

    assert manifest["chain_status"] == "hash_chained"
    assert manifest["hash_chain"]["head_hash"] == manifest["head_hash"]
    assert manifest["approval_event"]["diff"][0]["path"] == "/stakeholders/0/weight"
    assert manifest["entries"][-1]["stage"] == "report"
