from __future__ import annotations

import argparse
import json

from policy_impact_sandbox.live_policy.anchoring import record_anchor_transaction


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a human-broadcast Kaspa tx id into a live policy run.")
    parser.add_argument("--run-dir", required=True, help="Run directory containing audit_manifest.json and status.json.")
    parser.add_argument("--tx-id", required=True, help="Kaspa transaction id produced after human-approved broadcast.")
    parser.add_argument("--network", default="testnet-10")
    args = parser.parse_args()

    anchor = record_anchor_transaction(run_dir=args.run_dir, tx_id=args.tx_id, network=args.network)
    print(json.dumps({"status": anchor["status"], "tx_id": anchor["tx_id"], "explorer_url": anchor["explorer_url"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
