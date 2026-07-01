from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Broadcast the prepared Kaspa audit-anchor payload.")
    parser.add_argument("--anchor", default="runs/ulez_2023_phase2_deepseek/kaspa_anchor.json")
    parser.add_argument("--human-approved", action="store_true")
    parser.add_argument("--amount-kas", default="1")
    args = parser.parse_args()
    return asyncio.run(_main(args.anchor, args.human_approved, args.amount_kas))


async def _main(anchor_path: str, human_approved: bool, amount_kas: str) -> int:
    if not human_approved:
        raise SystemExit("Refusing to broadcast: checkpoint-4 human approval is required.")

    network = os.getenv("KASPA_NETWORK", "testnet-10")
    if network != "testnet-10":
        raise SystemExit("Refusing to broadcast: only KASPA_NETWORK=testnet-10 is allowed.")

    wallet_file = os.getenv("KASPA_WALLET_FILENAME")
    wallet_secret = os.getenv("KASPA_WALLET_SECRET")
    recipient = os.getenv("KASPA_RECIPIENT_ADDRESS")
    if not wallet_file or not wallet_secret or not recipient:
        raise SystemExit("Missing KASPA_WALLET_FILENAME, KASPA_WALLET_SECRET or KASPA_RECIPIENT_ADDRESS in .env.")

    from kaspa import AccountKind, Fees, FeeSource, PaymentOutput, Resolver, Wallet, kaspa_to_sompi

    anchor = json.loads(Path(anchor_path).read_text(encoding="utf-8"))
    payload = anchor["payload_canonical_json"].encode("utf-8")
    amount = float(amount_kas)

    wallet = Wallet(network_id=network, resolver=Resolver())
    try:
        await wallet.wallet_open(wallet_secret=wallet_secret, filename=wallet_file, account_descriptors=False)
        await wallet.connect(block_async_connect=True)
        await wallet.start()
        await wallet.accounts_ensure_default(wallet_secret=wallet_secret, account_kind=AccountKind("bip32"))
        accounts = await wallet.accounts_enumerate()
        if not accounts:
            raise RuntimeError("Wallet has no accounts.")
        account = accounts[0]
        await wallet.accounts_activate(account_ids=[account.account_id])
        result = await wallet.accounts_send(
            wallet_secret=wallet_secret,
            account_id=account.account_id,
            priority_fee_sompi=Fees(0, FeeSource.SenderPays),
            destination=[PaymentOutput(recipient, kaspa_to_sompi(amount))],
            payload=payload,
        )
    finally:
        await wallet.stop()
        await wallet.disconnect()
        await wallet.wallet_close()

    print(json.dumps(_serialize(result), ensure_ascii=False, indent=2))
    return 0


def _serialize(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if hasattr(value, "__dict__"):
        return {str(key): _serialize(item) for key, item in value.__dict__.items()}
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
