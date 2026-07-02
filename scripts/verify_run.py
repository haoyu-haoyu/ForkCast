from __future__ import annotations

import argparse
import json
from pathlib import Path

from policy_impact_sandbox.verify_run import verify_run


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a policy run against a Kaspa transaction payload.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--txid", required=True)
    parser.add_argument("--network", default="testnet-10")
    parser.add_argument("--json", action="store_true", help="Print machine-readable verification JSON.")
    args = parser.parse_args()

    result = verify_run(run_dir=Path(args.run_dir), txid=args.txid, network=args.network)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_human(result)
    return 0 if result["overall"] == "PASS" else 1


def _print_human(result: dict) -> None:
    print(f"Overall: {result['overall']}")
    print(f"Mode: {result['mode']}")
    print(f"Network: {result['network']}")
    print(f"Txid: {result['txid']}")
    print("Checks:")
    for name, check in result["checks"].items():
        print(f"- {name}: {check['status']} — {check['note']}")
    print("Links:")
    for link in result["links"]:
        print(f"- {link['id']} {link['stage']}: {link['status']}")


if __name__ == "__main__":
    raise SystemExit(main())
