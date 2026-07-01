import caseGraphJson from "./data/case_graph.json";
import agentsJson from "./data/agents.json";
import simulationJson from "./data/simulation_events.json";
import blindPredictionJson from "./data/blind_prediction.json";
import backtestJson from "./data/backtest_result.json";
import impactReportJson from "./data/impact_report.json";
import auditManifestJson from "./data/audit_manifest.json";
import kaspaAnchorJson from "./data/kaspa_anchor.json";

import type { AgentProfile, AuditEntry, BacktestRule, KaspaAnchor, SimulationEvent, Stakeholder } from "./types";

export const caseGraph = caseGraphJson as {
  case_id: string;
  stakeholders: Stakeholder[];
  assumptions: Array<{ id: string; statement: string; status: string }>;
};

export const agents = (agentsJson as { agents: AgentProfile[] }).agents;
export const simulation = simulationJson as {
  events: SimulationEvent[];
  signals: Record<string, string>;
  metadata: { agent_count: number; rounds: number; disclaimer: string };
};
export const blindPrediction = blindPredictionJson as {
  prompt: { system_prompt: string; user_prompt: string };
  leakage_guard: {
    truth_set_loaded_into_prompt: boolean;
    truth_set_file_read_by_prediction_step: boolean;
    excluded_case_graph_fields: string[];
  };
  prediction: {
    summary: string;
    group_reactions: Array<{ group_id: string; direction: string; intensity: string; rationale: string }>;
  };
};
export const backtest = backtestJson as {
  backtest_mode: string;
  rules: BacktestRule[];
  disclaimer: string;
};
export const impactReport = impactReportJson as {
  report_mode: string;
  backtest_evidence: string;
  method_note: string;
  stakeholder_impact_matrix: Array<{
    stakeholder_id: string;
    name: string;
    impact_level: string;
    opposition_intensity: string;
    qualitative_signal: string;
  }>;
  risk_timeline: Array<{ stage: string; signal: string; risk_level: string }>;
  mitigation_options: Array<{ option: string; rationale: string }>;
  confidence_notes: string[];
};
export const auditManifest = auditManifestJson as {
  chain_status: string;
  entries: AuditEntry[];
};
export const kaspaAnchor = kaspaAnchorJson as KaspaAnchor;
