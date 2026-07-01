export interface Stakeholder {
  id: string;
  name: string;
  archetype_group: string;
  stance_prior: string;
  interests: string[];
  weight?: number;
}

export interface AgentProfile {
  id: string;
  persona_type: string;
  stakeholder_id: string;
  stakeholder_name: string;
  archetype: string;
  persona: string;
  stance: string;
  action_tendency: string;
  concerns: string[];
  adaptation_capacity: string;
}

export interface SimulationEvent {
  event_id: string;
  round: number;
  agent_id: string;
  stakeholder_id: string;
  agent_archetype: string;
  type: "post" | "comment" | "stance_change";
  stance?: string;
  topic?: string;
  content?: string;
  from_stance?: string;
  to_stance?: string;
  reason?: string;
}

export interface BacktestRule {
  rule_id: string;
  verdict: "HIT" | "PARTIAL" | "MISS" | "BALANCED HIT";
  system_signal: string;
  real_outcome: string;
  note: string;
}

export interface AuditEntry {
  stage: string;
  hash: string;
  artifact_uri: string;
  approval: string;
  timestamp: string;
}

export interface HashChainLink {
  id: string;
  stage: string;
  payload_hash: string;
  previous_hash: string | null;
  hash: string;
}

export interface ChainedAuditManifest {
  case_id: string;
  run_id: string;
  generated_at: string;
  chain_status: string;
  head_hash: string;
  hash_chain: {
    canonicalization: string;
    links: HashChainLink[];
    head_hash: string;
  };
  approval_event: {
    timestamp: string;
    stage: string;
    editor: "human";
    diff: LivePolicyReviewDiff[];
    approved_hash: string;
  };
  entries: AuditEntry[];
}

export interface KaspaAnchor {
  status: "anchored" | "local_verification_only" | "broadcast_failed_or_not_completed";
  network: string;
  tx_id: string | null;
  explorer_url: string | null;
  explorer_base_url: string;
  manifest_uri: string;
  manifest_hash: string;
  payload_hash: string;
  payload_size_bytes: number;
  payload_practical_limit_bytes: number;
  payload_canonical_json: string;
  prepared_at: string;
  send_attempt: {
    attempted: boolean;
    reason: string;
  };
  verification: Record<string, boolean>;
}

export interface LivePolicyRunResult {
  run_id: string;
  mode: "live_policy_analysis";
  truth_set_status: {
    status: "unavailable";
    message: string;
  };
  case_graph: {
    case_id: string;
    case_name: string;
    stakeholders: Stakeholder[];
    assumptions: Array<{ id: string; statement: string; status: string }>;
  };
  agents: {
    agents: AgentProfile[];
  };
  simulation_events?: {
    events?: SimulationEvent[];
    metadata?: Record<string, unknown>;
  };
  impact_report: {
    report_mode?: string;
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
    disclaimer: string;
  };
  backtest_result: null;
}

export type LivePolicyRunStatusName =
  | "RECEIVED"
  | "EXTRACTING"
  | "AWAITING_REVIEW"
  | "SIMULATING"
  | "REPORTING"
  | "AWAITING_ANCHOR_APPROVAL"
  | "DONE"
  | "FAILED";

export interface LivePolicyRunStart {
  run_id: string;
  status: LivePolicyRunStatusName;
}

export interface LivePolicyReviewDiff {
  path: string;
  before: unknown;
  after: unknown;
}

export interface LivePolicyRunStatus extends Partial<LivePolicyRunResult> {
  run_id: string;
  status: LivePolicyRunStatusName;
  truth_set_status: {
    status: "unavailable";
    message: string;
  };
  case_graph_ai?: LivePolicyRunResult["case_graph"] | null;
  case_graph_approved?: LivePolicyRunResult["case_graph"] | null;
  review_diff: LivePolicyReviewDiff[];
  approval_event?: {
    timestamp: string;
    stage: string;
    editor: "human";
    diff: LivePolicyReviewDiff[];
    approved_hash: string;
  } | null;
  audit_manifest?: ChainedAuditManifest | null;
  failed?: {
    stage: string;
    error: string;
  };
}
