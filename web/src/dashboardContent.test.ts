import { describe, expect, it } from "vitest";
import { auditManifest, backtest, impactReport, kaspaAnchor } from "./data";
import { buildClaimsAuditRows, PROVENANCE_LABELS } from "./provenance";
import { RUBRIC_LABELS } from "./rubric";

const FORBIDDEN_DEMO_STRINGS = [
  "Traffic Volume",
  "NO2 Concentration",
  "Public Transit Use",
  "Retail Footfall",
  "Policy Support",
  "Equity Impact",
  "Impact score +0.62",
  "Benefit £126.4M",
  "Cost £48.7M",
  "Net impact £77.7M",
  "Air Quality -15.3%",
  "May 20, 2025",
  "RUN-2025-05-20",
  "Data Freshness 2h ago",
  "Phase 4 will anchor",
  "reserved for Phase 4",
];

describe("dashboard evidence content", () => {
  it("uses the real blind backtest R1-R6 result set", () => {
    expect(backtest.backtest_mode).toBe("blind_prediction");
    expect(backtest.rules.map((rule) => rule.rule_id)).toEqual(["R1", "R2", "R3", "R4", "R5", "R6"]);
    expect(RUBRIC_LABELS.R1).toContain("Outer London");
    expect(RUBRIC_LABELS.R2).toContain("van drivers");
    expect(RUBRIC_LABELS.R3).toContain("Political salience");
    expect(RUBRIC_LABELS.R4).toContain("Enforcement resistance");
    expect(RUBRIC_LABELS.R5).toContain("Behavioural adaptation");
    expect(RUBRIC_LABELS.R6).toContain("Benefit/burden balance");
  });

  it("does not include stale generic metrics or 2025 placeholder dates in evidence text", () => {
    const evidenceText = JSON.stringify({
      backtest,
      auditManifest,
      labels: RUBRIC_LABELS,
    });

    for (const forbidden of FORBIDDEN_DEMO_STRINGS) {
      expect(evidenceText).not.toContain(forbidden);
    }
  });

  it("exposes the Phase 4 Kaspa anchor package", () => {
    expect(["anchored", "local_verification_only"]).toContain(kaspaAnchor.status);
    expect(kaspaAnchor.network).toBe("testnet-10");
    expect(kaspaAnchor.manifest_hash).toMatch(/^[a-f0-9]{64}$/);
    expect(kaspaAnchor.payload_hash).toMatch(/^[a-f0-9]{64}$/);
    expect(kaspaAnchor.payload_size_bytes).toBeLessThan(kaspaAnchor.payload_practical_limit_bytes);
    if (kaspaAnchor.status === "anchored") {
      expect(kaspaAnchor.tx_id).toMatch(/^[a-f0-9]{64}$/);
      expect(kaspaAnchor.explorer_url).toContain("explorer-tn10.kaspa.org/txs/");
      expect(kaspaAnchor.send_attempt.attempted).toBe(true);
    }
  });

  it("renders provenance labels for report claims without mutating anchored artifacts", () => {
    const rows = buildClaimsAuditRows(impactReport, backtest);

    expect(rows.length).toBeGreaterThanOrEqual(backtest.rules.length);
    expect(rows.map((row) => row.provenance_class)).toContain("INFERRED-FROM-DOCUMENT");
    expect(Object.keys(PROVENANCE_LABELS)).toEqual([
      "DOCUMENT-CITED",
      "INFERRED-FROM-DOCUMENT",
      "MODEL-PRIOR",
    ]);
    expect(rows.every((row) => row.claim && row.evidence_pointer)).toBe(true);
  });
});
