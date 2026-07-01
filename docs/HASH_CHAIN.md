# Hash Chain Commitments

Policy Impact Sandbox uses one canonical JSON hashing rule for live-run audit artifacts:

```text
json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
```

The SHA-256 hex digest of that canonical byte string is the artifact hash.

## Live Run Chain

New policy runs are chained in this order:

```text
h0 = H(policy_input)
h1 = H(h0 || canonical_json(case_graph_ai))
h2 = H(h1 || canonical_json(approval_event))
h3 = H(h2 || canonical_json(simulation_outputs))
h4 = H(h3 || canonical_json(report))
```

The manifest stores every link, each artifact hash, each link hash, and the final `head_hash`. The approval event includes the human editor, timestamp, JSON diff between the AI-proposed and human-approved case graph, and the approved case-graph hash.

## Kaspa Commitment

For new chained manifests, the Kaspa payload commits to `head_hash`. This means one on-chain transaction covers the input, AI extraction, human approval edit, simulation outputs, and report.

The original ULEZ demo transaction is a legacy path: it commits to the canonical `audit_manifest.json` hash because that transaction already exists on Kaspa TN-10 and must not be rewritten. Verification supports both paths.

## Anchoring Policy

`ANCHOR_PER_APPROVAL=false` by default. The MVP uses one checkpoint-4 human approval before preparing or broadcasting an anchor. Agents cannot broadcast automatically, cannot change stakeholder weights automatically, and cannot process real-person PII.
