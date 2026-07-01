from policy_impact_sandbox.simulation.oasis_probe import evaluate_oasis_probe


def test_oasis_probe_requires_importable_package() -> None:
    decision = evaluate_oasis_probe(import_ok=False, has_api_key=True, live_enabled=True)

    assert decision.status == "dependency_failed"
    assert decision.can_run_live is False
    assert "mock simulation mode" in decision.message


def test_oasis_probe_does_not_run_without_api_key() -> None:
    decision = evaluate_oasis_probe(import_ok=True, has_api_key=False, live_enabled=True)

    assert decision.status == "missing_api_key"
    assert decision.can_run_live is False


def test_oasis_probe_does_not_run_paid_llm_calls_by_default() -> None:
    decision = evaluate_oasis_probe(import_ok=True, has_api_key=True, live_enabled=False)

    assert decision.status == "live_disabled"
    assert decision.can_run_live is False
