from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator


def test_phase2_cli_writes_required_artifacts_with_mock_llm(tmp_path) -> None:
    run_dir = tmp_path / "phase2_run"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_phase2.py",
            "--mock-llm",
            "--run-id",
            "phase2_cli_test",
            "--run-dir",
            str(run_dir),
            "--agent-count",
            "36",
            "--rounds",
            "3",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    expected = [
        "simulation_config.json",
        "agents.json",
        "blind_prediction.json",
        "simulation_events.json",
        "impact_report.json",
        "impact_report.md",
        "backtest_result.json",
        "backtest.md",
        "persona_chat_sample.json",
        "audit_manifest.json",
    ]
    for name in expected:
        assert (run_dir / name).exists(), name
    backtest = json.loads((run_dir / "backtest_result.json").read_text(encoding="utf-8"))
    assert backtest["backtest_mode"] == "blind_prediction"
    assert [item["rule_id"] for item in backtest["rules"]] == ["R1", "R2", "R3", "R4", "R5", "R6"]
    blind_prediction = json.loads((run_dir / "blind_prediction.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/blind_prediction.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(blind_prediction)
