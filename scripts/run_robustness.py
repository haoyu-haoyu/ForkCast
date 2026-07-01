from __future__ import annotations

import argparse
from pathlib import Path
import sys

from dotenv import load_dotenv

from policy_impact_sandbox.evaluation.robustness import run_robustness
from policy_impact_sandbox.llm import LLMConfig, MissingLLMConfig, OpenAICompatibleLLMClient


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run repeat-stability and weight-sensitivity checks.")
    parser.add_argument("--case-graph", default="data/cases/ulez_2023/case_graph.json")
    parser.add_argument("--truth-set", default="data/cases/ulez_2023/truth_set.json")
    parser.add_argument("--run-dir", default="runs/ulez_2023_phase2_deepseek")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--perturbations", type=int, default=6)
    parser.add_argument("--mock-llm", action="store_true")
    args = parser.parse_args()

    llm_client = None
    llm_metadata = None
    if not args.mock_llm:
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

    result = run_robustness(
        case_graph_path=Path(args.case_graph),
        truth_set_path=Path(args.truth_set),
        run_dir=Path(args.run_dir),
        k=args.k,
        perturbations=args.perturbations,
        mock_llm=args.mock_llm,
        llm_client=llm_client,
        llm_metadata=llm_metadata,
    )
    print(f"Wrote robustness artifact: {Path(args.run_dir) / 'robustness.json'}")
    for rule_id, stats in result["repeat_stability"].items():
        status = "UNSTABLE" if stats["unstable"] else "stable"
        print(f"{rule_id}: {stats['agreement_label']} ({status})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
