export type CheckpointKey =
  | "extraction_review"
  | "agent_review"
  | "simulation_config"
  | "report_chain_review";

export type CheckpointStatus = "pending" | "approved" | "rejected" | "superseded";

export type DemoStep =
  | "before"
  | "select_case"
  | CheckpointKey
  | "simulation_replay"
  | "impact_report"
  | "blind_backtest"
  | "audit"
  | "closing";

export interface CheckpointRecord {
  key: CheckpointKey;
  label: string;
  status: CheckpointStatus;
  artifactHash: string;
  reason: string;
  approvedAt?: string;
}

export interface ControlEvent {
  id: string;
  checkpoint: CheckpointKey;
  action: "approve" | "edit" | "reject" | "rollback";
  status: "accepted" | "blocked" | "superseded";
  note: string;
  timestamp: string;
}

export interface HardLimits {
  noAutomaticChainAction: true;
  noAutomaticWeightChanges: true;
  noRealPersonPii: true;
  archetypesOnly: true;
  decisionSupportOnly: true;
}

export interface ControlState {
  activeStep: DemoStep;
  checkpoints: Record<CheckpointKey, CheckpointRecord>;
  events: ControlEvent[];
  hardLimits: HardLimits;
}

const ORDER: CheckpointKey[] = [
  "extraction_review",
  "agent_review",
  "simulation_config",
  "report_chain_review",
];

export function createInitialControlState(): ControlState {
  return {
    activeStep: "before",
    checkpoints: {
      extraction_review: {
        key: "extraction_review",
        label: "Extraction review",
        status: "pending",
        artifactHash: "case_graph:pending",
        reason: "Review stakeholders, assumptions and missing groups before agent generation.",
      },
      agent_review: {
        key: "agent_review",
        label: "Agent review",
        status: "pending",
        artifactHash: "agents:pending",
        reason: "Inspect archetype mix, initial stances and persona constraints.",
      },
      simulation_config: {
        key: "simulation_config",
        label: "Simulation config",
        status: "pending",
        artifactHash: "simulation_config:pending",
        reason: "Approve agent count, rounds, seed and budget limits before replay/live sample.",
      },
      report_chain_review: {
        key: "report_chain_review",
        label: "Report and chain review",
        status: "pending",
        artifactHash: "audit_manifest:pending",
        reason: "Review report claims and the manifest that could be anchored in Phase 4.",
      },
    },
    events: [],
    hardLimits: {
      noAutomaticChainAction: true,
      noAutomaticWeightChanges: true,
      noRealPersonPii: true,
      archetypesOnly: true,
      decisionSupportOnly: true,
    },
  };
}

export function approveCheckpoint(state: ControlState, checkpoint: CheckpointKey): ControlState {
  if (!canApprove(state, checkpoint)) {
    return appendEvent(state, checkpoint, "approve", "blocked", "Previous checkpoint is not approved.");
  }
  const timestamp = new Date().toISOString();
  const next = cloneState(state);
  next.checkpoints[checkpoint] = {
    ...next.checkpoints[checkpoint],
    status: "approved",
    approvedAt: timestamp,
    artifactHash: `${checkpoint}:${stableHash(`${checkpoint}:${timestamp}`)}`,
  };
  next.activeStep = nextStepAfter(checkpoint);
  return appendEvent(next, checkpoint, "approve", "accepted", "Human approved checkpoint.");
}

export function rejectCheckpoint(state: ControlState, checkpoint: CheckpointKey): ControlState {
  const next = cloneState(state);
  next.checkpoints[checkpoint] = {
    ...next.checkpoints[checkpoint],
    status: "rejected",
  };
  next.activeStep = checkpoint;
  return appendEvent(next, checkpoint, "reject", "accepted", "Human rejected checkpoint; downstream work remains blocked.");
}

export function editCheckpoint(state: ControlState, checkpoint: CheckpointKey, note: string): ControlState {
  const next = cloneState(state);
  next.activeStep = checkpoint;
  return appendEvent(next, checkpoint, "edit", "accepted", note);
}

export function rollbackToPrevious(state: ControlState): ControlState {
  const approvedIndexes = [...ORDER]
    .map((key, index) => ({ key, index }))
    .filter(({ key }) => state.checkpoints[key].status === "approved");
  const latestApprovedIndex = approvedIndexes[approvedIndexes.length - 1]?.index;
  const currentIndex = latestApprovedIndex ?? activeCheckpointIndex(state.activeStep);
  const checkpoint = ORDER[Math.max(0, currentIndex)];
  const previous = ORDER[Math.max(0, currentIndex - 1)];
  const next = cloneState(state);
  if (checkpoint) {
    next.checkpoints[checkpoint] = {
      ...next.checkpoints[checkpoint],
      status: "superseded",
    };
  }
  next.activeStep = previous ?? "extraction_review";
  return appendEvent(
    next,
    checkpoint ?? "extraction_review",
    "rollback",
    "superseded",
    "Rolled back while preserving the old checkpoint in the audit trail.",
  );
}

export function canProceedTo(state: ControlState, checkpoint: CheckpointKey): boolean {
  const targetIndex = ORDER.indexOf(checkpoint);
  return ORDER.slice(0, targetIndex).every((key) => state.checkpoints[key].status === "approved");
}

function canApprove(state: ControlState, checkpoint: CheckpointKey): boolean {
  return canProceedTo(state, checkpoint) && state.checkpoints[checkpoint].status !== "superseded";
}

function nextStepAfter(checkpoint: CheckpointKey): DemoStep {
  if (checkpoint === "simulation_config") return "simulation_replay";
  if (checkpoint === "report_chain_review") return "closing";
  const index = ORDER.indexOf(checkpoint);
  return ORDER[index + 1] ?? "simulation_replay";
}

function activeCheckpointIndex(step: DemoStep): number {
  if (ORDER.includes(step as CheckpointKey)) return ORDER.indexOf(step as CheckpointKey);
  if (step === "simulation_replay" || step === "impact_report" || step === "blind_backtest" || step === "audit") return 3;
  return 0;
}

function appendEvent(
  state: ControlState,
  checkpoint: CheckpointKey,
  action: ControlEvent["action"],
  status: ControlEvent["status"],
  note: string,
): ControlState {
  return {
    ...state,
    hardLimits: state.hardLimits,
    events: [
      ...state.events,
      {
        id: `evt_${state.events.length + 1}_${stableHash(`${checkpoint}:${action}:${state.events.length}`)}`,
        checkpoint,
        action,
        status,
        note,
        timestamp: new Date().toISOString(),
      },
    ],
  };
}

function cloneState(state: ControlState): ControlState {
  return {
    ...state,
    checkpoints: structuredClone(state.checkpoints),
    events: [...state.events],
    hardLimits: state.hardLimits,
  };
}

function stableHash(value: string): string {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}
