from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Render CC 2003 human verification checklist.")
    parser.add_argument("--truth-set", default="data/cases/congestion_charge_2003/truth_set.json")
    parser.add_argument("--output", default="docs/evaluation/cc2003_verification_checklist.md")
    args = parser.parse_args()

    truth_set = json.loads(Path(args.truth_set).read_text(encoding="utf-8"))
    output = render_checklist(truth_set)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")
    print(f"Wrote {output_path}")
    print(f"facts={len(truth_set.get('facts', []))}")
    print(f"headline_excluded={truth_set.get('headline_excluded')}")
    return 0


def render_checklist(truth_set: dict[str, Any]) -> str:
    lines = [
        "# CC 2003 Truth-Set Human Verification Checklist",
        "",
        f"Case: `{truth_set['case_id']}` - {truth_set.get('case_name', '')}",
        f"Current verification policy: `{truth_set.get('verification_policy', '')}`",
        f"Current headline_excluded: `{truth_set.get('headline_excluded')}`",
        "",
        "Instructions for the human reviewer:",
        "",
        "- Use only the linked source URL and quoted text for each item.",
        "- Mark exactly one decision per fact: CONFIRM, REJECT, or EDIT.",
        "- Do not promote any `待核实` fact to `已确认` unless the reviewer explicitly marks CONFIRM.",
        "- If any scored fact remains unconfirmed, keep `headline_excluded=true` and exclude this case from headline metrics.",
        "",
        "Decision key: `[ ] CONFIRM   [ ] REJECT   [ ] EDIT: <write corrected fact/status>`",
        "",
    ]
    for index, fact in enumerate(truth_set.get("facts", []), start=1):
        lines.extend(
            [
                f"## {index}. {fact['id']}",
                "",
                f"- Category: {fact.get('category', '')}",
                f"- Requested item: {fact.get('requested_item', '')}",
                f"- Current status: `{fact.get('confidence_status', '')}`",
                f"- Headline excluded: `{fact.get('headline_excluded')}`",
                f"- Fact: {fact.get('fact', '')}",
                f"- Value JSON: `{json.dumps(fact.get('value', {}), ensure_ascii=False, sort_keys=True)}`",
                f"- Notes: {fact.get('notes', '')}",
                "",
                "Sources:",
            ]
        )
        for source_number, source in enumerate(fact.get("sources", []), start=1):
            lines.extend(
                [
                    f"- Source {source_number} name: {source.get('source_name', '')}",
                    f"  - Type: {source.get('source_type', '')}",
                    f"  - URL: {source.get('url', '')}",
                    f"  - Quote: {source.get('quote', '')}",
                ]
            )
        lines.extend(
            [
                "",
                "Human decision: [ ] CONFIRM   [ ] REJECT   [ ] EDIT: ________________________________",
                "",
                "Reviewer notes:",
                "",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
