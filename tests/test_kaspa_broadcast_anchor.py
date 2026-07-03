from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_module():
    module_path = Path("scripts/kaspa_broadcast_anchor.py")
    spec = importlib.util.spec_from_file_location("kaspa_broadcast_anchor", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_success_output_includes_txid_explorer_and_success_line() -> None:
    module = _load_module()
    output = module._format_success_output(
        sdk_result={"final_transaction_id": "abc123"},
        network="testnet-10",
        recovered_matches=[],
        warnings=[],
    )

    assert "SUCCESS: Kaspa anchor broadcast accepted" in output
    assert "final_transaction_id=abc123" in output
    assert "explorer_url=https://explorer-tn10.kaspa.org/txs/abc123" in output


def test_success_output_recovers_txid_from_payload_match_when_sdk_omits_it() -> None:
    module = _load_module()
    output = module._format_success_output(
        sdk_result="GeneratorSummary(network_id='testnet-10', transactions=1)",
        network="testnet-10",
        recovered_matches=[{"tx_id": "def456", "block_time": 1783045243706}],
        warnings=[],
    )

    assert "SUCCESS: Kaspa anchor broadcast accepted" in output
    assert "final_transaction_id=def456" in output
    assert "explorer_url=https://explorer-tn10.kaspa.org/txs/def456" in output


def test_duplicate_guard_blocks_anchor_with_recorded_txid() -> None:
    module = _load_module()

    with pytest.raises(SystemExit, match="already records tx_id"):
        module._enforce_duplicate_guard(
            anchor={"tx_id": "abc123"},
            recent_matches=[],
            allow_duplicate=False,
        )


def test_duplicate_guard_blocks_recent_matching_payload() -> None:
    module = _load_module()

    with pytest.raises(SystemExit, match="payload was already broadcast"):
        module._enforce_duplicate_guard(
            anchor={},
            recent_matches=[{"tx_id": "def456", "block_time": 1783045243706}],
            allow_duplicate=False,
        )


def test_duplicate_guard_allows_explicit_duplicate_confirmation() -> None:
    module = _load_module()

    module._enforce_duplicate_guard(
        anchor={"tx_id": "abc123"},
        recent_matches=[{"tx_id": "def456", "block_time": 1783045243706}],
        allow_duplicate=True,
    )
