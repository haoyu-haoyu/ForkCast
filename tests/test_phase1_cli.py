from __future__ import annotations

import json
import subprocess
import sys


def test_phase1_cli_can_run_with_mock_llm(tmp_path) -> None:
    output = tmp_path / "case_graph.json"
    graph_output = tmp_path / "case_graph_networkx.json"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_phase1_case_graph.py",
            "--mock-llm",
            "--output",
            str(output),
            "--graph-output",
            str(graph_output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    case_graph = json.loads(output.read_text(encoding="utf-8"))
    graph = json.loads(graph_output.read_text(encoding="utf-8"))
    assert case_graph["case_id"] == "ulez_2023_expansion"
    assert case_graph["llm"] == {
        "provider": "mock",
        "base_url": None,
        "model": "deterministic_mock",
    }
    assert graph["nodes"]
    assert graph["edges"]
