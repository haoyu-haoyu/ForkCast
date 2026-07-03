from __future__ import annotations

import argparse
import asyncio
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

KASPA_API_BASE = {"testnet-10": "https://api-tn10.kaspa.org"}
KASPA_EXPLORER_BASE = {"testnet-10": "https://explorer-tn10.kaspa.org"}


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Broadcast the prepared Kaspa audit-anchor payload.")
    parser.add_argument("--anchor", default="runs/ulez_2023_phase2_deepseek/kaspa_anchor.json")
    parser.add_argument("--human-approved", action="store_true")
    parser.add_argument("--amount-kas", default="1")
    parser.add_argument(
        "--allow-duplicate",
        action="store_true",
        help="Required if the anchor already has a tx id or the same payload was recently broadcast.",
    )
    args = parser.parse_args()
    return asyncio.run(_main(args.anchor, args.human_approved, args.amount_kas, args.allow_duplicate))


async def _main(anchor_path: str, human_approved: bool, amount_kas: str, allow_duplicate: bool = False) -> int:
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
    warnings: list[str] = []
    recent_matches: list[dict] = []
    try:
        recent_matches = _fetch_recent_payload_matches(recipient, payload, network)
    except Exception as exc:  # pragma: no cover - network diagnostics only
        warnings.append(f"Could not check recent payload matches before broadcast: {exc}")
    _enforce_duplicate_guard(anchor, recent_matches, allow_duplicate)

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

    recovered_matches: list[dict] = []
    if not _extract_transaction_ids(result):
        await asyncio.sleep(3)
        try:
            recovered_matches = _fetch_recent_payload_matches(recipient, payload, network)
        except Exception as exc:  # pragma: no cover - network diagnostics only
            warnings.append(f"Could not recover transaction id from explorer API after broadcast: {exc}")

    print(
        _format_success_output(
            sdk_result=result,
            network=network,
            recovered_matches=recovered_matches,
            warnings=warnings,
        )
    )
    return 0


def _enforce_duplicate_guard(anchor: dict, recent_matches: list[dict], allow_duplicate: bool) -> None:
    recorded_tx_id = anchor.get("tx_id")
    if allow_duplicate:
        return
    if recorded_tx_id:
        raise SystemExit(
            "Refusing to broadcast: anchor already records tx_id "
            f"{recorded_tx_id}. Re-run with --allow-duplicate only if intentional."
        )
    if recent_matches:
        txids = ", ".join(match["tx_id"] for match in recent_matches if match.get("tx_id"))
        raise SystemExit(
            "Refusing to broadcast: this payload was already broadcast recently "
            f"({txids}). Re-run with --allow-duplicate only if intentional."
        )


def _format_success_output(
    sdk_result,
    network: str,
    recovered_matches: list[dict],
    warnings: list[str],
) -> str:
    txids = _extract_transaction_ids(sdk_result)
    if not txids and recovered_matches:
        latest = _sort_matches(recovered_matches)[-1]
        if latest.get("tx_id"):
            txids = [latest["tx_id"]]
    final_transaction_id = txids[-1] if txids else None
    lines = ["SUCCESS: Kaspa anchor broadcast accepted"]
    if final_transaction_id:
        lines.append(f"final_transaction_id={final_transaction_id}")
        lines.append(f"explorer_url={_explorer_url(final_transaction_id, network)}")
    else:
        lines.append("final_transaction_id=UNRECOVERED")
        lines.append("explorer_url=UNRECOVERED")
        warnings = [
            *warnings,
            "The Kaspa SDK returned from accounts_send, but no transaction id was exposed or recovered.",
        ]
    for warning in warnings:
        lines.append(f"WARNING: {warning}")
    lines.append("sdk_result=" + json.dumps(_serialize(sdk_result), ensure_ascii=False, sort_keys=True))
    if recovered_matches:
        lines.append(
            "recovered_payload_matches="
            + json.dumps(_sort_matches(recovered_matches), ensure_ascii=False, sort_keys=True)
        )
    return "\n".join(lines)


def _fetch_recent_payload_matches(address: str, payload: bytes, network: str, limit: int = 100) -> list[dict]:
    api_base = KASPA_API_BASE.get(network)
    if not api_base:
        raise ValueError(f"Unsupported Kaspa API network: {network}")
    address_path = urllib.parse.quote(address, safe=":")
    url = f"{api_base}/addresses/{address_path}/full-transactions?limit={limit}&offset=0"
    with urllib.request.urlopen(url, timeout=20) as response:
        transactions = json.loads(response.read().decode("utf-8"))
    return _payload_matches(transactions, payload)


def _payload_matches(transactions: list[dict], payload: bytes) -> list[dict]:
    payload_hex = payload.hex().lower()
    matches = []
    for tx in transactions:
        if str(tx.get("payload", "")).lower() != payload_hex:
            continue
        tx_id = tx.get("transaction_id") or tx.get("tx_id") or tx.get("id") or tx.get("hash")
        if not tx_id:
            continue
        matches.append(
            {
                "tx_id": tx_id,
                "hash": tx.get("hash"),
                "block_time": tx.get("block_time"),
                "accepting_block_time": tx.get("accepting_block_time"),
                "mass": tx.get("mass"),
            }
        )
    return _sort_matches(matches)


def _sort_matches(matches: list[dict]) -> list[dict]:
    def sort_key(match: dict):
        return (
            match.get("block_time") if match.get("block_time") is not None else -1,
            match.get("accepting_block_time") if match.get("accepting_block_time") is not None else -1,
            match.get("tx_id") or "",
        )

    return sorted(matches, key=sort_key)


def _extract_transaction_ids(value) -> list[str]:
    candidates: list[str] = []
    _collect_transaction_ids(value, candidates)
    return candidates


def _collect_transaction_ids(value, candidates: list[str]) -> None:
    tx_keys = {"final_transaction_id", "transaction_id", "tx_id", "txid"}
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in tx_keys and item:
                candidates.append(str(item))
            else:
                _collect_transaction_ids(item, candidates)
        return
    if isinstance(value, list):
        for item in value:
            _collect_transaction_ids(item, candidates)
        return
    if hasattr(value, "__dict__"):
        _collect_transaction_ids(value.__dict__, candidates)


def _explorer_url(tx_id: str, network: str) -> str:
    explorer_base = KASPA_EXPLORER_BASE.get(network, "https://explorer-tn10.kaspa.org")
    return f"{explorer_base}/txs/{tx_id}"


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
