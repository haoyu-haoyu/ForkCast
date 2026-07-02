from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def test_ulez_human_adjudication_sheet_has_unfilled_rule_decisions(tmp_path: Path) -> None:
    output = tmp_path / "ulez_human_adjudication.md"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/render_ulez_human_adjudication.py",
            "--output",
            str(output),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    markdown = output.read_text(encoding="utf-8")
    truth_set = json.loads(Path("data/cases/ulez_2023/truth_set.json").read_text(encoding="utf-8"))
    assert "ULEZ Human Adjudication Sheet" in markdown
    assert markdown.count("Human decision: [ ] HIT   [ ] PARTIAL   [ ] MISS") == 6
    assert "automated scorer verdicts" in markdown
    for rule_id in ["R1", "R2", "R3", "R4", "R5", "R6"]:
        assert f"## {rule_id}" in markdown
    for fact in truth_set["facts"]:
        for source in fact["sources"]:
            if fact["id"] in markdown:
                assert source["url"] in markdown
                assert source["quote"] in markdown
