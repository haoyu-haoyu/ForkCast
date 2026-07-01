from __future__ import annotations

import argparse
from pathlib import Path
import sys

from dotenv import load_dotenv

from policy_impact_sandbox.evaluation.ablation import run_ablation
from policy_impact_sandbox.llm import LLMConfig, MissingLLMConfig, OpenAICompatibleLLMClient


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run ULEZ blind-backtest ablation baselines.")
    parser.add_argument("--case-graph", default="data/cases/ulez_2023/case_graph.json")
    parser.add_argument("--policy-text", default="data/cases/ulez_2023/seed_policy.md")
    parser.add_argument("--truth-set", default="data/cases/ulez_2023/truth_set.json")
    parser.add_argument("--output-dir", default="docs/evaluation")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--mock-llm", action="store_true")
    args = parser.parse_args()

    mock_llm = args.mock_llm
    llm_client = None
    llm_metadata = None
    if not mock_llm:
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

    result = run_ablation(
        case_graph_path=Path(args.case_graph),
        policy_text_path=Path(args.policy_text),
        truth_set_path=Path(args.truth_set),
        k=args.k,
        mock_llm=mock_llm,
        output_dir=Path(args.output_dir),
        llm_client=llm_client,
        llm_metadata=llm_metadata,
    )
    print(f"Wrote ablation artifacts to {args.output_dir}")
    for condition_id, condition in result["conditions"].items():
        print(f"{condition_id}: mean_hit_rate={condition['mean_hit_rate']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
