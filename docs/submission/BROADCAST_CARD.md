# Broadcast Card: Live Showcase Anchor

Use this card only for a public showcase document and Kaspa `testnet-10`. Do not paste secrets into the terminal. The showcase run's input policy text will be committed to a public repo, so use public documents only.

## 0. Pre-Flight

Check local env presence without printing secret values:

```bash
python3 - <<'PY'
from dotenv import dotenv_values
required = [
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "KASPA_NETWORK",
    "KASPA_WALLET_FILENAME",
    "KASPA_WALLET_SECRET",
    "KASPA_RECIPIENT_ADDRESS",
]
vals = dotenv_values(".env")
for name in required:
    print(f"{name}: {'present' if vals.get(name) else 'MISSING'}")
print(f"KASPA_NETWORK_IS_TESTNET_10: {vals.get('KASPA_NETWORK') == 'testnet-10'}")
PY
```

Expected output: every variable is `present`; `KASPA_NETWORK_IS_TESTNET_10: True`.

Failure playbook: if any variable is missing or the network is not `testnet-10`, stop and fix `.env`. Do not broadcast.

Check public wallet balance:

```bash
ADDR=$(python3 - <<'PY'
from dotenv import dotenv_values
print(dotenv_values(".env").get("KASPA_RECIPIENT_ADDRESS", ""))
PY
)
curl -fsSL "https://api-tn10.kaspa.org/addresses/${ADDR}/balance"
```

Expected output: JSON with the public `address` and `balance` in sompi.

Recommended primary path for the current wallet: use the lower-amount broadcast command in step 6 (`--amount-kas 0.2`). The helper converts `0.2` KAS to `20000000` sompi via the Kaspa SDK, so the current `1.0` KAS balance covers amount plus the observed f553-style fee estimate (`349800` sompi). Practical minimum for this path: `20349800` sompi (`0.20349800` KAS).

Dust/minimum-output check: Kaspa dust depends on output value, serialized output size and minimum relay fee. `0.2` KAS is `20000000` sompi, far above the dust threshold for a normal wallet `PaymentOutput` on TN-10, so this fallback is safe from a dust/minimum-output perspective.

Faucet path if you want to keep `--amount-kas 1`: use at least `100349800` sompi (`1.00349800` KAS) as a practical minimum. Open the canonical TN-10 faucet `https://faucet-tn10.kaspanet.io`, paste the `kaspatest:` address, request funds, wait 1-3 minutes, then rerun the balance command. Backup if the faucet is unavailable: Kaspa Discord `#testnet`.

Failure playbook: if balance is below `20349800` sompi, fund the testnet wallet first and stop if the faucet requires CAPTCHA/login or does not send funds. Do not switch to mainnet.

## 1. Start Servers

Terminal A, API:

```bash
uv run python scripts/run_api.py --host 127.0.0.1 --port 8000
```

Expected output: Uvicorn starts and keeps running on `http://127.0.0.1:8000`.

Failure playbook: if it exits immediately, check `.env` exists and rerun `uv run pytest -q`. Stop and report the first traceback.

Terminal B, dashboard:

```bash
cd web
npm run dev -- --host 127.0.0.1 --port 5173
```

Expected output: Vite serves `http://127.0.0.1:5173/`.

Failure playbook: if Vite fails, run `npm test` and `npm run build`; stop and report the failing command.

## 2. Submit The Chosen Public Document

Open `http://127.0.0.1:5173/`, paste or upload the chosen GOV.UK document text in **Run a new policy document**, then click **Run real analysis**.

Expected output: the live run card moves from `running` to `awaiting_review`, and the UI shows extracted stakeholders.

Failure playbook: if the card shows `failed`, copy only the non-secret error message and stop. Do not retry blindly.

## 3. Open Review Screen And Make A Mandatory Human Edit

In the review card, change at least one stakeholder weight. Example: change the first stakeholder weight from `1.0` to `1.2`.

Then click **Save review edits**.

Expected output: **Visible diff** contains a non-empty path such as `/stakeholders/0/weight`.

Failure playbook: if the diff is empty, do not approve. Change a stakeholder weight again and save. A non-empty approval diff is mandatory for the showcase.

## 4. Approve The Run

Click **Approve and continue**.

Expected output: the run reaches `AWAITING_ANCHOR_APPROVAL`; the result panel shows an audit hash-chain head.

Failure playbook: if status becomes `FAILED`, stop and report the failed stage. Do not broadcast.

Copy the run id shown in the result panel:

```bash
export RUN_ID=policy_run_YYYYMMDDTHHMMSSZ
```

## 5. Prepare The Anchor Package

Terminal C:

```bash
uv run python scripts/kaspa_anchor_manifest.py \
  --manifest "runs/${RUN_ID}/audit_manifest.json" \
  --output "runs/${RUN_ID}/kaspa_anchor.json" \
  --web-copy "" \
  --network testnet-10
```

Expected output:

```text
Wrote Kaspa anchor record: runs/${RUN_ID}/kaspa_anchor.json
Status: pending_broadcast
Hash-chain head: <hash>
Payload bytes: <n>/25000
Explorer: not available until a transaction id is recorded.
```

Failure playbook: if verification fails or the manifest path is missing, stop and check that the run is `AWAITING_ANCHOR_APPROVAL`.

Inspect the payload before broadcasting:

```bash
jq '.payload.commitment_type, .payload.head_hash, .payload_size_bytes, .human_approval_required_for_chain_anchor' \
  "runs/${RUN_ID}/kaspa_anchor.json"
```

Expected output: commitment type is hash-chain based, `human_approval_required_for_chain_anchor` is true, and payload bytes are below `25000`.

Failure playbook: if the payload is missing `head_hash`, stop. Do not broadcast a malformed anchor.

## 6. Broadcast With Human Approval

Recommended primary command for the currently funded wallet:

```bash
uv run --with kaspa python scripts/kaspa_broadcast_anchor.py \
  --anchor "runs/${RUN_ID}/kaspa_anchor.json" \
  --human-approved \
  --amount-kas 0.2
```

Optional command if the faucet has topped the wallet above `1.00349800` KAS:

```bash
uv run --with kaspa python scripts/kaspa_broadcast_anchor.py \
  --anchor "runs/${RUN_ID}/kaspa_anchor.json" \
  --human-approved \
  --amount-kas 1
```

Expected output: JSON containing a transaction id from the Kaspa wallet SDK result.

Failure playbook: if balance is insufficient, fund the testnet wallet and retry once. If the SDK reports wallet/open/connect/signing errors, stop and report the first error. Never switch to mainnet.

## 7. Record The Transaction And Report The Txid

Set the transaction id from the broadcast output:

```bash
export TX_ID=<kaspa_testnet_transaction_id>
```

Record it back into the run:

```bash
uv run python scripts/record_anchor_tx.py \
  --run-dir "runs/${RUN_ID}" \
  --tx-id "${TX_ID}" \
  --network testnet-10
```

Expected output:

```json
{"status":"anchored","tx_id":"...","explorer_url":"https://explorer-tn10.kaspa.org/txs/..."}
```

Failure playbook: if this fails, do not edit JSON manually. Report the error and preserve `runs/${RUN_ID}/`.

Verify local status:

```bash
jq '.status, .anchor.tx_id, .anchor.explorer_url' "runs/${RUN_ID}/status.json"
jq '.status, .payload.commitment_type, .payload.head_hash, .explorer_url' "runs/${RUN_ID}/kaspa_anchor.json"
```

Expected output: `status.json` is `DONE`; `kaspa_anchor.json` is `anchored`; explorer URL starts with `https://explorer-tn10.kaspa.org/txs/`.

Send the human-reported values back to Codex:

```text
RUN_ID=<run id>
TX_ID=<tx id>
EXPLORER=https://explorer-tn10.kaspa.org/txs/<tx id>
```
