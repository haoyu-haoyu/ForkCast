from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from policy_impact_sandbox.evaluation.adversarial_inputs import FIXTURE_ORDER, run_adversarial_inputs


def test_adversarial_mock_extraction_records_graceful_behavior(tmp_path: Path) -> None:
    result = run_adversarial_inputs(
        fixture_dir=Path("tests/fixtures/adversarial"),
        output_dir=tmp_path,
        include_real_llm=False,
    )

    assert [item["fixture"] for item in result["results"]] == FIXTURE_ORDER
    assert result["summary"]["fixture_count"] == 5
    assert result["summary"]["mock_crashes"] == 0
    assert result["summary"]["mock_schema_valid_count"] == 5
    assert result["summary"]["real_llm_status_counts"] == {"skipped_by_flag": 5}
    long_fixture = next(item for item in result["results"] if item["fixture"] == "long_public_consultation.txt")
    assert long_fixture["input_characters"] > 50_000
    assert long_fixture["source_url"].startswith("https://www.gov.uk/")
    near_empty = next(item for item in result["results"] if item["fixture"] == "near_empty.txt")
    assert near_empty["mock"]["confidence_flags"]
    assert (tmp_path / "adversarial_inputs.json").exists()
    assert "Observed Behavior" in (tmp_path / "adversarial_inputs.md").read_text(encoding="utf-8")


def test_adversarial_inputs_cli_writes_artifacts(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_adversarial_inputs.py",
            "--output-dir",
            str(tmp_path),
            "--skip-real-llm",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "fixtures=5" in result.stdout
    artifact = json.loads((tmp_path / "adversarial_inputs.json").read_text(encoding="utf-8"))
    assert artifact["summary"]["mock_schema_valid_count"] == 5
