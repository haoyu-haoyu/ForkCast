# Operator Runbook: Anchor A New Live Run

This runbook is for a human operator anchoring a new live policy run after checkpoint-4 approval. Do not run these commands for mainnet. Use Kaspa `testnet-10` only.

## Preconditions

- `.env` exists locally and is not committed.
- `.env` contains:
  - `KASPA_NETWORK=testnet-10`
  - `KASPA_WALLET_FILENAME`
  - `KASPA_WALLET_SECRET`
  - `KASPA_RECIPIENT_ADDRESS`
- The wallet is funded on TN-10.
- The live run has reached `AWAITING_ANCHOR_APPROVAL`.
- The operator has reviewed and approved the report and anchor payload in checkpoint 4.

## Command Sequence

Set the run id from the dashboard:

```bash
export RUN_ID=policy_run_YYYYMMDDTHHMMSSZ
```

Prepare the anchor package. For new live runs this commits to the audit-manifest `head_hash`.

```bash
uv run python scripts/kaspa_anchor_manifest.py \
  --manifest "runs/${RUN_ID}/audit_manifest.json" \
  --output "runs/${RUN_ID}/kaspa_anchor.json" \
  --web-copy "" \
  --network testnet-10
```

Inspect the payload before broadcasting:

```bash
jq '.payload.commitment_type, .payload.head_hash, .payload_size_bytes, .human_approval_required_for_chain_anchor' \
  "runs/${RUN_ID}/kaspa_anchor.json"
```

Broadcast only after checkpoint-4 approval:

```bash
uv run --with kaspa python scripts/kaspa_broadcast_anchor.py \
  --anchor "runs/${RUN_ID}/kaspa_anchor.json" \
  --human-approved \
  --amount-kas 1
```

Copy the transaction id from the broadcast output. Then record it back into the run and mark the run `DONE`:

```bash
export TX_ID=<kaspa_testnet_transaction_id>

uv run python scripts/record_anchor_tx.py \
  --run-dir "runs/${RUN_ID}" \
  --tx-id "${TX_ID}" \
  --network testnet-10
```

Verify local status:

```bash
jq '.status, .anchor.tx_id, .anchor.explorer_url' "runs/${RUN_ID}/status.json"
jq '.status, .payload.commitment_type, .payload.head_hash, .explorer_url' "runs/${RUN_ID}/kaspa_anchor.json"
```

Expected result:

- `runs/${RUN_ID}/status.json` has `status: "DONE"`.
- `runs/${RUN_ID}/kaspa_anchor.json` has `status: "anchored"`.
- `explorer_url` points to `https://explorer-tn10.kaspa.org/txs/${TX_ID}`.

## Safety Notes

- Agents never broadcast transactions automatically.
- The dashboard approval is a human checkpoint, not an autonomous chain action.
- The on-chain payload contains only a commitment: case id, run id, manifest hash, hash-chain head, and approval policy metadata.
- Policy text, source documents, LLM prompts, personas, simulation events, and reports stay off-chain.
