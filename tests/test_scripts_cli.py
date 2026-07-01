from __future__ import annotations

import subprocess
import sys


def test_run_mock_simulation_script_writes_output(tmp_path) -> None:
    output = tmp_path / "mock.json"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_mock_simulation.py",
            "--output",
            str(output),
            "--rounds",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.exists()
