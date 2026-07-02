import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { auditManifest, backtest, impactReport, kaspaAnchor } from "./data";
import { buildClaimsAuditRows, claimsAuditNotice, PROVENANCE_LABELS } from "./provenance";
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
  it("uses the cached automated rubric R1-R6 result set", () => {
    expect(backtest.backtest_mode).toBe("blind_prediction");
    expect(backtest.rules.map((rule) => rule.rule_id)).toEqual(["R1", "R2", "R3", "R4", "R5", "R6"]);
    expect(RUBRIC_LABELS.R1).toContain("Outer London");
    expect(RUBRIC_LABELS.R2).toContain("van drivers");
    expect(RUBRIC_LABELS.R3).toContain("Political salience");
    expect(RUBRIC_LABELS.R4).toContain("Enforcement resistance");
    expect(RUBRIC_LABELS.R5).toContain("Behavioural adaptation");
    expect(RUBRIC_LABELS.R6).toContain("Benefit/burden balance");
  });

  it("labels automated verdicts as rubric coverage rather than semantic verification", () => {
    const appSource = readFileSync(new URL("./App.tsx", import.meta.url), "utf-8");

    expect(appSource).toContain(
      "Automated keyword-rubric verdicts — signal coverage, not semantic verification. See negative controls & human adjudication.",
    );
    expect(appSource).toContain("Human grading");
    expect(appSource).toContain("Pending - see docs/evaluation/ulez_human_adjudication.md");
    expect(appSource).toContain("No changes were made — approve anyway?");
    expect(appSource).not.toContain("Evidence-backed validation is the blind R1-R6 backtest");
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

  it("marks anchored legacy report claims as unclassified when provenance fields are absent", () => {
    const rows = buildClaimsAuditRows(impactReport, backtest);

    expect(rows.length).toBeGreaterThanOrEqual(backtest.rules.length);
    expect(new Set(rows.map((row) => row.provenance_class))).toEqual(new Set(["UNCLASSIFIED_LEGACY"]));
    expect(PROVENANCE_LABELS.UNCLASSIFIED_LEGACY).toBe("Unclassified (legacy report)");
    expect(claimsAuditNotice(rows)).toBe(
      "This report predates provenance classification and is anchored; claims are shown unclassified.",
    );
    expect(Object.keys(PROVENANCE_LABELS).slice(0, 3)).toEqual([
      "DOCUMENT-CITED",
      "INFERRED-FROM-DOCUMENT",
      "MODEL-PRIOR",
    ]);
    expect(rows.every((row) => row.claim && row.evidence_pointer)).toBe(true);
  });

  it("preserves real provenance classes when the report contains provenance fields", () => {
    const rows = buildClaimsAuditRows(
      {
        ...impactReport,
        claims_audit_table: [
          {
            id: "claim_document",
            claim: "Document-backed statement",
            provenance_class: "DOCUMENT-CITED",
            evidence_pointer: "truth_set.C1",
            evidence_fact_ids: ["C1"],
            source_artifact: "truth_set.json",
            confidence: "high",
          },
          {
            id: "claim_model_prior",
            claim: "Mitigation design statement",
            provenance_class: "MODEL-PRIOR",
            evidence_pointer: "impact_report.mitigation_options[0]",
            evidence_fact_ids: [],
            source_artifact: "impact_report.json",
            confidence: "low",
          },
        ],
      },
      backtest,
    );

    expect(rows.map((row) => row.provenance_class)).toEqual(["DOCUMENT-CITED", "MODEL-PRIOR"]);
    expect(rows.map((row) => PROVENANCE_LABELS[row.provenance_class])).toEqual(["Document-cited", "Model prior"]);
    expect(claimsAuditNotice(rows)).toBe("");
  });
});
