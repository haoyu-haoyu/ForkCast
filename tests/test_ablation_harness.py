from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from policy_impact_sandbox.evaluation.ablation import FORBIDDEN_OUTCOME_TOKENS, run_ablation


def test_ablation_harness_mock_outputs_three_conditions_and_consistency(tmp_path: Path) -> None:
    result = run_ablation(
        case_graph_path=Path("data/cases/ulez_2023/case_graph.json"),
        policy_text_path=Path("data/cases/ulez_2023/seed_policy.md"),
        truth_set_path=Path("data/cases/ulez_2023/truth_set.json"),
        k=1,
        mock_llm=True,
        output_dir=tmp_path,
    )

    assert result["case_id"] == "ulez_2023_expansion"
    assert result["scorer"] == "evaluate_blind_prediction_backtest"
    assert set(result["conditions"]) == {"bare_prompt", "single_analyst", "full_pipeline"}
    for condition in result["conditions"].values():
        assert len(condition["runs"]) == 1
        assert condition["mean_hit_rate"] >= 0
        assert set(condition["per_question_consistency"]) == {"R1", "R2", "R3", "R4", "R5", "R6"}
        assert condition["hit_miss_matrix"][0]["R1"] in {"HIT", "PARTIAL", "MISS", "BALANCED HIT"}


def test_ablation_prompts_exclude_truth_set_and_cli_writes_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "ablation"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_ablation.py",
            "--mock-llm",
            "--k",
            "1",
            "--output-dir",
            str(output_dir),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    artifact = json.loads((output_dir / "ablation_ulez.json").read_text(encoding="utf-8"))
    markdown = (output_dir / "ablation_ulez.md").read_text(encoding="utf-8")
    serialized_prompts = json.dumps(
        [
            run["prediction"]["prompt"]
            for condition in artifact["conditions"].values()
            for run in condition["runs"]
        ],
        ensure_ascii=False,
    )
    for token in FORBIDDEN_OUTCOME_TOKENS:
        assert token not in serialized_prompts
    assert "| Condition | Mean hit rate |" in markdown
    assert "| Condition | Run | R1 | R2 | R3 | R4 | R5 | R6 |" in markdown
    assert "bare_prompt" in markdown
    assert "full_pipeline" in markdown
