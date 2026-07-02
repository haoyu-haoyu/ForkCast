import type { BacktestRule, ClaimProvenanceRow } from "./types";

export const PROVENANCE_LABELS: Record<ClaimProvenanceRow["provenance_class"], string> = {
  "DOCUMENT-CITED": "Document-cited",
  "INFERRED-FROM-DOCUMENT": "Inferred from document",
  "MODEL-PRIOR": "Model prior",
  UNCLASSIFIED_LEGACY: "Unclassified (legacy report)",
};

export const LEGACY_PROVENANCE_NOTICE =
  "This report predates provenance classification and is anchored; claims are shown unclassified.";

export function buildClaimsAuditRows(
  impactReport: {
    claims_audit_table?: ClaimProvenanceRow[];
    risk_timeline: Array<{ stage: string; signal: string; risk_level: string }>;
    mitigation_options: Array<{ option: string; rationale: string }>;
  },
  backtest: { rules: BacktestRule[] },
): ClaimProvenanceRow[] {
  if (impactReport.claims_audit_table?.length) {
    return impactReport.claims_audit_table.map(normalizeRow);
  }

  const backtestRows = backtest.rules
    .filter((rule) => rule.system_signal.trim())
    .map((rule) =>
      normalizeRow({
        id: `backtest_${rule.rule_id}`,
        claim: rule.system_signal,
        provenance_class: "UNCLASSIFIED_LEGACY",
        evidence_pointer: `backtest_result.rules.${rule.rule_id}; blind_prediction.json`,
        evidence_fact_ids: [],
        source_artifact: "backtest_result.json + blind_prediction.json",
        confidence: rule.verdict === "MISS" ? "low" : "medium",
      }),
    );

  const riskRows = impactReport.risk_timeline.map((risk) =>
    normalizeRow({
      id: `risk_${risk.stage}`,
      claim: risk.signal,
      provenance_class: "UNCLASSIFIED_LEGACY",
      evidence_pointer: `impact_report.risk_timeline.${risk.stage}`,
      evidence_fact_ids: [],
      source_artifact: "impact_report.json",
      confidence: risk.risk_level === "high" ? "medium" : "low",
    }),
  );

  const mitigationRows = impactReport.mitigation_options.map((item, index) =>
    normalizeRow({
      id: `mitigation_${index + 1}`,
      claim: item.rationale,
      provenance_class: "UNCLASSIFIED_LEGACY",
      evidence_pointer: `impact_report.mitigation_options[${index}]`,
      evidence_fact_ids: [],
      source_artifact: "impact_report.json",
      confidence: "low",
    }),
  );

  return [...backtestRows, ...riskRows, ...mitigationRows];
}

export function claimsAuditNotice(rows: ClaimProvenanceRow[]): string {
  return rows.some((row) => row.provenance_class === "UNCLASSIFIED_LEGACY") ? LEGACY_PROVENANCE_NOTICE : "";
}

function normalizeRow(row: ClaimProvenanceRow): ClaimProvenanceRow {
  const provenanceClass = row.provenance_class in PROVENANCE_LABELS ? row.provenance_class : "MODEL-PRIOR";
  return {
    id: row.id,
    claim: row.claim,
    provenance_class: provenanceClass,
    evidence_pointer: row.evidence_pointer || row.source_artifact || "not specified",
    evidence_fact_ids: row.evidence_fact_ids || [],
    source_artifact: row.source_artifact || "not specified",
    confidence: row.confidence || "medium",
  };
}
