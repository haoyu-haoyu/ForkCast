from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from dotenv import load_dotenv
from jsonschema import Draft202012Validator

from policy_impact_sandbox.llm import LLMConfig, MissingLLMConfig, OpenAICompatibleLLMClient
from policy_impact_sandbox.phase1.extract import (
    DeterministicMockLLMClient,
    build_seed_policy_from_truth_set,
    extract_case_graph,
)


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run Phase 1 ULEZ truth_set to case_graph pipeline.")
    parser.add_argument("--truth-set", default="data/cases/ulez_2023/truth_set.json")
    parser.add_argument("--policy-doc", default="data/cases/ulez_2023/seed_policy.md")
    parser.add_argument("--output", default="data/cases/ulez_2023/case_graph.json")
    parser.add_argument("--graph-output", default="data/cases/ulez_2023/case_graph_networkx.json")
    parser.add_argument("--mock-llm", action="store_true", help="Use deterministic local mock LLM for tests only.")
    args = parser.parse_args()

    truth_set = _read_json(Path(args.truth_set))
    seed_policy = _read_seed_policy(Path(args.policy_doc), truth_set)

    if args.mock_llm:
        llm_client = DeterministicMockLLMClient(truth_set)
        llm_metadata = {
            "provider": "mock",
            "base_url": None,
            "model": "deterministic_mock",
        }
    else:
        try:
            llm_config = LLMConfig.from_env()
            llm_client = OpenAICompatibleLLMClient(llm_config)
            llm_metadata = {
                "provider": llm_config.provider,
                "base_url": llm_config.base_url,
                "model": llm_config.model,
            }
        except MissingLLMConfig as exc:
            print(str(exc), file=sys.stderr)
            return 2

    case_graph = extract_case_graph(seed_policy=seed_policy, truth_set=truth_set, llm_client=llm_client)
    case_graph["llm"] = llm_metadata
    _validate("schemas/case_graph.schema.json", case_graph)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(case_graph, ensure_ascii=False, indent=2), encoding="utf-8")

    graph_path = Path(args.graph_output)
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(json.dumps(case_graph["graph"], ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote case graph: {output_path}")
    print(f"Wrote NetworkX fallback graph: {graph_path}")
    print(f"Entities: {len(case_graph['entities'])}")
    print(f"Stakeholders: {len(case_graph['stakeholders'])}")
    print(f"Evidence facts: {len(case_graph['evidence'])}")
    return 0


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_seed_policy(path: Path, truth_set: dict) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return build_seed_policy_from_truth_set(truth_set)


def _validate(schema_path: str, payload: dict) -> None:
    schema = _read_json(Path(schema_path))
    Draft202012Validator(schema).validate(payload)


if __name__ == "__main__":
    raise SystemExit(main())
