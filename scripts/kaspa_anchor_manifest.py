from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

from dotenv import load_dotenv

from policy_impact_sandbox.phase4.kaspa_anchor import build_kaspa_anchor_record, verify_kaspa_anchor_record


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Prepare a Kaspa payload anchor for an audit manifest.")
    parser.add_argument("--manifest", default="runs/ulez_2023_phase2_deepseek/audit_manifest.json")
    parser.add_argument("--output", default=None)
    parser.add_argument("--web-copy", default="web/src/data/kaspa_anchor.json")
    parser.add_argument("--network", default="testnet-10")
    parser.add_argument("--tx-id", default=None, help="Record a manually submitted Kaspa transaction id.")
    parser.add_argument("--send", action="store_true", help="Reserved for funded-wallet broadcast; fails closed by default.")
    parser.add_argument("--human-approved", action="store_true", help="Required before any future broadcast path is allowed.")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    audit_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_path = Path(args.output) if args.output else manifest_path.with_name("kaspa_anchor.json")

    if args.send and not args.human_approved:
        print("Refusing to broadcast: --send requires --human-approved from checkpoint 4.", file=sys.stderr)
        return 2

    send_attempted = False
    send_reason = None
    if args.send:
        send_attempted = True
        send_reason = (
            "Broadcast path intentionally not executed in this MVP because no funded Kaspa testnet "
            "wallet is configured in environment variables. Use the prepared payload with the "
            "official Wallet API accountsSend payload field."
        )

    anchor_record = build_kaspa_anchor_record(
        audit_manifest,
        str(manifest_path),
        network=args.network,
        tx_id=args.tx_id,
        send_attempted=send_attempted,
        send_reason=send_reason,
    )
    verification = verify_kaspa_anchor_record(audit_manifest, anchor_record)
    if not all(verification.values()):
        print(json.dumps(verification, indent=2), file=sys.stderr)
        return 1
    anchor_record["verification"] = verification

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(anchor_record, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.web_copy:
        web_copy = Path(args.web_copy)
        web_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output_path, web_copy)

    print(f"Wrote Kaspa anchor record: {output_path}")
    print(f"Status: {anchor_record['status']}")
    print(f"Manifest hash: {anchor_record['manifest_hash']}")
    print(f"Payload hash: {anchor_record['payload_hash']}")
    print(f"Payload bytes: {anchor_record['payload_size_bytes']}/{anchor_record['payload_practical_limit_bytes']}")
    if anchor_record.get("explorer_url"):
        print(f"Explorer: {anchor_record['explorer_url']}")
    else:
        print("Explorer: not available until a transaction id is recorded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
