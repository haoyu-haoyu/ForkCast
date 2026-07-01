from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import secrets

from dotenv import dotenv_values


ENV_PATH = Path(".env")
DEFAULT_WALLET_FILE = ".kaspa-wallet/policy-impact-sandbox-testnet10.wallet"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a local Kaspa testnet-10 wallet for audit anchoring.")
    parser.add_argument("--wallet-file", default=DEFAULT_WALLET_FILE)
    parser.add_argument("--network", default="testnet-10")
    args = parser.parse_args()
    return asyncio.run(_main(args.wallet_file, args.network))


async def _main(wallet_file: str, network: str) -> int:
    if network != "testnet-10":
        raise SystemExit("Refusing to create wallet: only KASPA_NETWORK=testnet-10 is allowed for this demo.")

    from kaspa import AccountKind, Mnemonic, NewAddressKind, Resolver, Wallet

    existing = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    wallet_secret = existing.get("KASPA_WALLET_SECRET") or secrets.token_urlsafe(32)
    mnemonic_phrase = existing.get("KASPA_MNEMONIC") or Mnemonic.random(12).phrase
    wallet_path = Path(wallet_file)
    wallet_path.parent.mkdir(parents=True, exist_ok=True)

    wallet = Wallet(network_id=network, resolver=Resolver())
    try:
        await wallet.wallet_create(
            wallet_secret=wallet_secret,
            filename=str(wallet_path),
            overwrite_wallet_storage=False,
            title="Policy Impact Sandbox TN10",
            user_hint="testnet-only",
        )
    except Exception as exc:
        message = str(exc).lower()
        if "exist" not in message and "already" not in message:
            raise

    try:
        await wallet.wallet_open(wallet_secret=wallet_secret, filename=str(wallet_path), account_descriptors=False)
        await wallet.accounts_ensure_default(
            wallet_secret=wallet_secret,
            account_kind=AccountKind("bip32"),
            mnemonic_phrase=mnemonic_phrase,
        )
        accounts = await wallet.accounts_enumerate()
        if not accounts:
            raise RuntimeError("Wallet did not return an account descriptor.")
        account = accounts[0]
        address = await wallet.accounts_create_new_address(account_id=account.account_id, address_kind=NewAddressKind.Receive)
    finally:
        try:
            await wallet.wallet_close()
        except Exception:
            pass

    _merge_env(
        {
            "KASPA_NETWORK": network,
            "KASPA_WALLET_FILENAME": str(wallet_path),
            "KASPA_WALLET_SECRET": wallet_secret,
            "KASPA_MNEMONIC": mnemonic_phrase,
            "KASPA_RECIPIENT_ADDRESS": str(address),
        }
    )

    print(f"Kaspa testnet wallet ready: {address}")
    print("Secrets were written only to .env.")
    return 0


def _merge_env(updates: dict[str, str]) -> None:
    current: dict[str, str] = {}
    if ENV_PATH.exists():
        current = {key: value for key, value in dotenv_values(ENV_PATH).items() if value is not None}
    current.update(updates)
    lines = ["# Local secrets for Policy Impact Sandbox. Do not commit.\n"]
    for key in sorted(current):
        value = current[key].replace("\n", "\\n")
        lines.append(f"{key}={value}\n")
    ENV_PATH.write_text("".join(lines), encoding="utf-8")
    ENV_PATH.chmod(0o600)


if __name__ == "__main__":
    raise SystemExit(main())
