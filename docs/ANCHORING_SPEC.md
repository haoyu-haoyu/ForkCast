# Anchoring Specification

## Scope

Policy Impact Sandbox anchors an audit commitment, not AI reasoning. Policy text, source documents, prompts, persona content, simulation events, reports and other large artifacts stay off-chain. Kaspa stores only a compact payload containing case/run metadata plus either a legacy manifest hash or a new hash-chain head.

## Canonical Serialization

All artifact hashes are computed over parsed JSON objects, not raw file bytes:

```python
json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
```

This makes pretty-printed JSON and compact JSON hash identically after parse/write/read round trips, including floats and non-ASCII text.

## Legacy Demo Commitment

The existing ULEZ demo transaction was broadcast before live-run hash chaining was added. It commits to the canonical SHA-256 hash of:

```text
runs/ulez_2023_phase2_deepseek/audit_manifest.json
```

The committed payload is stored locally in:

```text
runs/ulez_2023_phase2_deepseek/kaspa_anchor.json
```

The verifier supports this legacy mode by:

1. Loading each artifact listed in `audit_manifest.entries`.
2. Recomputing each artifact hash from parsed JSON.
3. Recomputing the canonical manifest hash.
4. Fetching the Kaspa transaction payload from `https://api-tn10.kaspa.org/transactions/{txid}`.
5. Checking that the on-chain payload equals the approved local anchor payload and contains the same manifest-hash commitment.

## New Live-Run Commitment

New live runs use a hash chain:

```text
h0 = H(policy_input)
h1 = H(h0 || canonical_json(case_graph_ai))
h2 = H(h1 || canonical_json(approval_event))
h3 = H(h2 || canonical_json(simulation_outputs))
h4 = H(h3 || canonical_json(report))
```

`audit_manifest.json` stores all link hashes and the final `head_hash`. The Kaspa payload commits to `sha256:{head_hash}`. One on-chain transaction therefore covers the input, AI extraction, human approval diff, simulation outputs and final report.

## Verifier Usage

Verify the existing ULEZ TN-10 transaction:

```bash
uv run python scripts/verify_run.py \
  --run-dir runs/ulez_2023_phase2_deepseek \
  --txid f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123 \
  --network testnet-10
```

Expected result:

```text
Overall: PASS
Mode: legacy_manifest_hash
```

For a new live run after `scripts/record_anchor_tx.py` has written `runs/{run_id}/kaspa_anchor.json`:

```bash
uv run python scripts/verify_run.py \
  --run-dir "runs/${RUN_ID}" \
  --txid "${TX_ID}" \
  --network testnet-10
```

Expected mode:

```text
Mode: hash_chain_head
```

## Tamper Demo

For a disposable copy of a run directory:

```bash
cp -R runs/ulez_2023_phase2_deepseek /tmp/ulez_tamper_demo
python - <<'PY'
from pathlib import Path
p = Path("/tmp/ulez_tamper_demo/impact_report.json")
p.write_text(p.read_text(encoding="utf-8").replace("mock_demo_visualization", "tampered"), encoding="utf-8")
PY

uv run python scripts/verify_run.py \
  --run-dir /tmp/ulez_tamper_demo \
  --txid f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123 \
  --network testnet-10
```

Expected result:

```text
Overall: FAIL
```

The automated tamper test in `tests/test_verify_run.py` performs the same check for a chained live-run manifest.

## Public API Basis

- Kaspa explorer list and API docs: `https://kaspa.aspectron.org/explorers.html`
- TN-10 explorer: `https://explorer-tn10.kaspa.org`
- TN-10 REST API docs: `https://api-tn10.kaspa.org/docs`
- Transaction payload endpoint used by the verifier: `https://api-tn10.kaspa.org/transactions/{txid}`
