from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from policy_impact_sandbox.evaluation.negative_controls import run_negative_controls


def test_negative_controls_expose_truth_content_insensitivity(tmp_path: Path) -> None:
    original_truth = Path("data/cases/ulez_2023/truth_set.json").read_text(encoding="utf-8")
    result = run_negative_controls(
        blind_prediction_path=Path("runs/ulez_2023_phase2_deepseek/blind_prediction.json"),
        truth_set_path=Path("data/cases/ulez_2023/truth_set.json"),
        ablation_path=Path("docs/evaluation/ablation_ulez.json"),
        output_dir=tmp_path,
        permutations=3,
        seed=7,
    )

    baseline = result["controls"]["baseline_cached_prediction"]
    inverted = result["controls"]["inverted_truth"]
    shuffled = result["controls"]["shuffled_alignment"]
    assert result["finding"]["scorer_leniency_found"] is True
    assert baseline["hit_rate"] == inverted["hit_rate"]
    assert shuffled["distribution"]["values"] == [baseline["hit_rate"]] * 3
    assert shuffled["real_ablation_full_pipeline_mean_hit_rate"] == 0.7333
    assert (tmp_path / "negative_controls.json").exists()
    assert "Scorer leniency found: `True`" in (tmp_path / "negative_controls.md").read_text(encoding="utf-8")
    assert Path("data/cases/ulez_2023/truth_set.json").read_text(encoding="utf-8") == original_truth


def test_negative_controls_cli_writes_artifacts(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_negative_controls.py",
            "--output-dir",
            str(tmp_path),
            "--permutations",
            "2",
            "--seed",
            "11",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "scorer_leniency_found=True" in result.stdout
    artifact = json.loads((tmp_path / "negative_controls.json").read_text(encoding="utf-8"))
    assert artifact["controls"]["shuffled_alignment"]["permutations"] == 2
    assert artifact["controls"]["cross_case"]["status"] == "not_run"
