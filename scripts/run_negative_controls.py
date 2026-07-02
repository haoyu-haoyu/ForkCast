from __future__ import annotations

import argparse
from pathlib import Path

from policy_impact_sandbox.evaluation.negative_controls import run_negative_controls


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ULEZ negative controls for the blind-backtest scorer.")
    parser.add_argument("--blind-prediction", default="runs/ulez_2023_phase2_deepseek/blind_prediction.json")
    parser.add_argument("--truth-set", default="data/cases/ulez_2023/truth_set.json")
    parser.add_argument("--ablation", default="docs/evaluation/ablation_ulez.json")
    parser.add_argument("--output-dir", default="docs/evaluation")
    parser.add_argument("--permutations", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260703)
    args = parser.parse_args()

    result = run_negative_controls(
        blind_prediction_path=Path(args.blind_prediction),
        truth_set_path=Path(args.truth_set),
        ablation_path=Path(args.ablation) if args.ablation else None,
        output_dir=Path(args.output_dir),
        permutations=args.permutations,
        seed=args.seed,
    )
    baseline = result["controls"]["baseline_cached_prediction"]["hit_rate"]
    inverted = result["controls"]["inverted_truth"]["hit_rate"]
    inverted_rule_facts = result["controls"]["inverted_rule_facts"]["hit_rate"]
    shuffled = result["controls"]["shuffled_alignment"]["distribution"]["mean"]
    finding = result["finding"]["scorer_leniency_found"]
    print(f"Wrote negative-control artifacts to {args.output_dir}")
    print(f"baseline_cached_prediction={baseline:.4f}")
    print(f"inverted_truth={inverted:.4f}")
    print(f"inverted_rule_facts={inverted_rule_facts:.4f}")
    print(f"shuffled_alignment_mean={shuffled:.4f}")
    print(f"mechanism={result['finding']['mechanism']}")
    print(f"scorer_leniency_found={finding}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
