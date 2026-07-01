export interface Stakeholder {
  id: string;
  name: string;
  archetype_group: string;
  stance_prior: string;
  interests: string[];
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
