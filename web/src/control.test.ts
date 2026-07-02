import { describe, expect, it } from "vitest";
import { approveCheckpoint, createInitialControlState, rejectCheckpoint, rollbackToPrevious } from "./control";

describe("checkpoint control layer", () => {
  it("requires ordered approvals before later checkpoints can be approved", () => {
    const state = createInitialControlState();

    const blocked = approveCheckpoint(state, "agent_review");
    expect(blocked.checkpoints.agent_review.status).toBe("pending");
    expect(blocked.events[blocked.events.length - 1]?.status).toBe("blocked");

    const approved = approveCheckpoint(state, "extraction_review");
    expect(approved.checkpoints.extraction_review.status).toBe("approved");
    expect(approved.activeStep).toBe("agent_review");
  });

  it("marks old approvals superseded on rollback instead of deleting them", () => {
    let state = createInitialControlState();
    state = approveCheckpoint(state, "extraction_review");
    state = approveCheckpoint(state, "agent_review");

    const rolledBack = rollbackToPrevious(state);

    expect(rolledBack.checkpoints.agent_review.status).toBe("superseded");
    expect(rolledBack.activeStep).toBe("extraction_review");
    expect(rolledBack.events.some((event) => event.action === "rollback")).toBe(true);
  });

  it("records rejections without changing hard limits", () => {
    const state = rejectCheckpoint(createInitialControlState(), "report_chain_review");

    expect(state.checkpoints.report_chain_review.status).toBe("rejected");
    expect(state.hardLimits.noAutomaticChainAction).toBe(true);
    expect(state.hardLimits.noAutomaticWeightChanges).toBe(true);
    expect(state.hardLimits.noRealPersonPii).toBe(true);
    expect(state.hardLimits.archetypesOnly).toBe(true);
  });

  it("moves from approved simulation config into replay, not hidden report checkpoint", () => {
    let state = createInitialControlState();
    state = approveCheckpoint(state, "extraction_review");
    state = approveCheckpoint(state, "agent_review");
    state = approveCheckpoint(state, "simulation_config");

    expect(state.activeStep).toBe("simulation_replay");
  });
});
