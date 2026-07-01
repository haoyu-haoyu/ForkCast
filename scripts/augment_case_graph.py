from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from policy_impact_sandbox.phase1.augment import augment_missing_stakeholders


def main() -> int:
    parser = argparse.ArgumentParser(description="Add required Phase 2 stakeholders to an existing case_graph.json.")
    parser.add_argument("--case-graph", default="data/cases/ulez_2023/case_graph.json")
    parser.add_argument("--schema", default="schemas/case_graph.schema.json")
    args = parser.parse_args()

    case_graph_path = Path(args.case_graph)
    case_graph = json.loads(case_graph_path.read_text(encoding="utf-8"))
    augmented = augment_missing_stakeholders(case_graph)

    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(augmented)

    case_graph_path.write_text(json.dumps(augmented, ensure_ascii=False, indent=2), encoding="utf-8")
    graph_path = case_graph_path.with_name("case_graph_networkx.json")
    graph_path.write_text(json.dumps(augmented["graph"], ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote augmented case graph: {case_graph_path}")
    print(f"Stakeholders: {len(augmented['stakeholders'])}")
    print(f"Wrote NetworkX fallback graph: {graph_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
