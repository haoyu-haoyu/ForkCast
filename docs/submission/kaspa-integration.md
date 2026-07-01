# Kaspa Integration: Audit Manifest Anchoring

## What Goes On Chain

Policy Impact Sandbox keeps AI reasoning, prompts, archetype agents, mock event logs, and source evidence off-chain. The Kaspa payload commits only to the canonical SHA-256 hash of `runs/ulez_2023_phase2_deepseek/audit_manifest.json`.

The payload generated for this demo is:

- `protocol`: `policy-impact-sandbox.kaspa-anchor`
- `case_id`: `ulez_2023_expansion`
- `run_id`: `ulez_2023_phase2_deepseek`
- `stage`: `audit_manifest`
- `manifest_hash`: SHA-256 of the canonical audit manifest
- `manifest_uri`: local artifact path
- `artifact_count`: number of manifest entries
- `human_approval_gate`: checkpoint 4 is required before broadcast
- `chain_policy`: off-chain AI reasoning, on-chain commitment hash only

Generated artifact:

- Anchor record: `runs/ulez_2023_phase2_deepseek/kaspa_anchor.json`
- Dashboard copy: `web/src/data/kaspa_anchor.json`

## Official Kaspa Basis

Kaspa's official transaction payload guide says the transaction payload field is for application data inside standard mempool limits and shows the high-level Wallet API `accountsSend()` request accepting a `payload` field. It also states the practical limit is about 25 KB when payload dominates the transaction, because standard transactions are capped by transient mass.

Sources:

- Kaspa transaction payload docs: https://docs.kaspa.org/integrate/transaction-payload
- Kaspa Wallet API docs: https://docs.kaspa.org/integrate/wallet
- Kaspa TN-10 faucet/explorer docs: https://wiki.kaspa.org/en/testnets

## Network Choice

The MVP targets `testnet-10` for demo anchoring. The official Kaspa testnet page lists TN-10 as a test network with faucet `https://faucet-tn10.kaspanet.io/` and explorer `https://explorer-tn10.kaspa.org/`.

The generated anchor record includes:

- `network`: `testnet-10`
- `explorer_base_url`: `https://explorer-tn10.kaspa.org`
- `tx_id`: `f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`
- `explorer_url`: `https://explorer-tn10.kaspa.org/txs/f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`

## Human-in-the-Loop Gate

The Conduct control layer remains the authority:

1. Checkpoint 4 shows the report claims and the Kaspa payload.
2. The user may approve, refuse, or downgrade/delete unsupported claims.
3. No agent or background process broadcasts a transaction.
4. Broadcast requires explicit checkpoint-4 approval plus a funded testnet wallet configured outside source control.

The local CLI also fails closed:

```bash
uv run python scripts/kaspa_anchor_manifest.py --send
```

This exits with an error unless explicit human approval is present. The broadcast helper also refuses non-`testnet-10` networks and reads wallet material only from local environment variables.

## How to Generate the Anchor Package

```bash
uv run python scripts/kaspa_anchor_manifest.py \
  --manifest runs/ulez_2023_phase2_deepseek/audit_manifest.json \
  --network testnet-10
```

Current generated values:

- Manifest hash: `e9f71f3d18ae1f4a5226bf98f1eb48a14b94fc225e2c3cd38bb97c99fed5bf25`
- Payload hash: `93b99f9ddf63961b9382d0f74416c430d1b560861a0c44fe076d05ff6b536f07`
- Payload size: `731 / 25000` bytes
- Status: `anchored`
- Testnet transaction: `f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`
- Explorer: https://explorer-tn10.kaspa.org/txs/f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123
- Faucet funding transaction: `afe4d886bd3115ab1ce873e9e615360f205dd25fff44bd6ddb4012e13221eda9`

## How to Verify Locally

1. Recompute canonical SHA-256 of `audit_manifest.json`:

```bash
uv run python - <<'PY'
import json
from pathlib import Path
from policy_impact_sandbox.phase2.audit import canonical_sha256

manifest = json.loads(Path("runs/ulez_2023_phase2_deepseek/audit_manifest.json").read_text())
anchor = json.loads(Path("runs/ulez_2023_phase2_deepseek/kaspa_anchor.json").read_text())
print(canonical_sha256(manifest))
print(anchor["manifest_hash"])
PY
```

2. Confirm both hashes match.
3. Confirm `anchor["payload"]["manifest_hash"]` is `sha256:<manifest_hash>`.
4. Confirm `payload_hash` matches SHA-256 of `payload_canonical_json`.
5. Confirm `payload_size_bytes` is below the practical 25 KB payload limit.

Automated test coverage:

```bash
uv run pytest tests/test_phase4_kaspa_anchor.py -q
```

## True Transaction Path

To broadcast a real testnet transaction after approval, use the official Wallet API shape documented by Kaspa:

```js
await wallet.accountsSend({
  accountId: account.accountId,
  walletSecret,
  priorityFeeSompi: 0n,
  destination: [{ address: recipient, amount: kaspaToSompi("1") }],
  payload: new TextEncoder().encode(anchor.payload_canonical_json),
});
```

Secrets must come from environment variables or local wallet storage, never source code:

- `KASPA_NETWORK=testnet-10`
- `KASPA_WALLET_FILENAME`
- `KASPA_WALLET_SECRET`
- `KASPA_RECIPIENT_ADDRESS`
- optional `KASPA_RPC_URL`

For this demo, a testnet-10 wallet was created locally, funded through the official TN-10 faucet, and used to broadcast the prepared payload after the explicit `--human-approved` gate. The testnet wallet secret and mnemonic are stored only in local `.env`, which is ignored by git.

## Dashboard Surface

The `Audit + Kaspa` screen now displays:

- Anchor status
- Network
- Explorer base
- Manifest hash
- Payload hash
- Payload size against the practical limit
- Canonical payload JSON
- Human approval/refusal buttons

If a replacement transaction id is later recorded with:

```bash
uv run python scripts/kaspa_anchor_manifest.py \
  --manifest runs/ulez_2023_phase2_deepseek/audit_manifest.json \
  --network testnet-10 \
  --tx-id <kaspa_tx_id>
```

the dashboard will show an explorer link.

## SilverScript / Covenants Status

SilverScript/Covenants are not implemented as production chain rules in this MVP. They remain a design/stretch item: the current production-quality deliverable is payload hash anchoring of the approved audit manifest. This avoids overstating chain enforcement while still demonstrating verifiable AI governance and cryptographic audit tracing.
