from __future__ import annotations

import argparse
from pathlib import Path
import sys

from dotenv import load_dotenv

from policy_impact_sandbox.evaluation.adversarial_inputs import run_adversarial_inputs
from policy_impact_sandbox.llm import LLMConfig, MissingLLMConfig, OpenAICompatibleLLMClient


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run adversarial input extraction suite.")
    parser.add_argument("--fixture-dir", default="tests/fixtures/adversarial")
    parser.add_argument("--output-dir", default="docs/evaluation")
    parser.add_argument("--skip-real-llm", action="store_true")
    args = parser.parse_args()

    include_real = not args.skip_real_llm
    real_client = None
    real_metadata = None
    if include_real:
        try:
            config = LLMConfig.from_env()
            real_client = OpenAICompatibleLLMClient(config)
            real_metadata = {
                "provider": config.provider,
                "base_url": config.base_url,
                "model": config.model,
            }
        except MissingLLMConfig:
            real_client = None
            real_metadata = None
        except Exception as exc:  # noqa: BLE001 - record setup failure without leaking secrets.
            print(f"Real LLM setup failed cleanly: {type(exc).__name__}: {str(exc)[:160]}", file=sys.stderr)
            real_client = None
            real_metadata = {"provider": "real_llm_setup_failed", "error_type": type(exc).__name__}

    result = run_adversarial_inputs(
        fixture_dir=Path(args.fixture_dir),
        output_dir=Path(args.output_dir),
        include_real_llm=include_real,
        real_llm_client=real_client,
        real_llm_metadata=real_metadata,
    )
    print(f"Wrote adversarial input artifacts to {args.output_dir}")
    print(f"fixtures={result['summary']['fixture_count']}")
    print(f"mock_schema_valid={result['summary']['mock_schema_valid_count']}")
    print(f"mock_crashes={result['summary']['mock_crashes']}")
    print(f"real_llm_status_counts={result['summary']['real_llm_status_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
