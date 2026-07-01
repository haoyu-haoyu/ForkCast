from __future__ import annotations

import json
from pathlib import Path

from policy_impact_sandbox.evaluation.robustness import run_robustness


def test_robustness_mock_aggregates_stability_and_sensitivity(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "ulez_robustness"
    run_dir.mkdir(parents=True)
    report_path = run_dir / "impact_report.md"
    report_path.write_text("# Impact Report\n\nExisting body.\n", encoding="utf-8")
    original_case_graph = Path("data/cases/ulez_2023/case_graph.json").read_text(encoding="utf-8")

    result = run_robustness(
        case_graph_path=Path("data/cases/ulez_2023/case_graph.json"),
        truth_set_path=Path("data/cases/ulez_2023/truth_set.json"),
        run_dir=run_dir,
        k=3,
        perturbations=4,
        mock_llm=True,
    )

    assert result["case_id"] == "ulez_2023_expansion"
    assert result["repeat_stability"]["R1"]["agreement_label"] == "3/3 runs agree"
    assert result["sensitivity"]["perturbation_count"] == 4
    assert result["sensitivity"]["rules"]["R2"]["classification"] == "assumption_sensitive"
    assert result["sensitivity"]["rules"]["R6"]["classification"] in {"robust", "assumption_sensitive"}
    assert (run_dir / "robustness.json").exists()
    assert "## Robustness" in report_path.read_text(encoding="utf-8")
    assert Path("data/cases/ulez_2023/case_graph.json").read_text(encoding="utf-8") == original_case_graph
