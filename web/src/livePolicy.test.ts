import { describe, expect, it, vi } from "vitest";
import { approvePolicyRun, getPolicyRun, patchPolicyRunCaseGraph, startPolicyRun } from "./livePolicy";

describe("live policy API client", () => {
  it("starts a new async policy run", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ run_id: "policy_run_test", status: "AWAITING_REVIEW" }),
    });

    const result = await startPolicyRun(
      {
        policyText: "Restrict motor traffic near a primary school during drop-off and pick-up.",
        agentCount: 12,
        rounds: 2,
      },
      fetchMock,
    );

    expect(fetchMock).toHaveBeenCalledWith("/api/policy-runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        policy_text: "Restrict motor traffic near a primary school during drop-off and pick-up.",
        agent_count: 12,
        rounds: 2,
      }),
    });
    expect(result.run_id).toBe("policy_run_test");
  });

  it("fetches, patches and approves a paused review run", async () => {
    const caseGraph = {
      case_id: "school_street_trial",
      case_name: "School Street Trial",
      generated_at: "2026-07-02T00:00:00+00:00",
      extraction_method: "test",
      source_truth_set: { path: "", fact_count: 0 },
      entities: [],
      stakeholders: [{ id: "parents", name: "Parents", archetype_group: "affected_public", stance_prior: "mixed", interests: [], evidence_fact_ids: [], weight: 1.2 }],
      assumptions: [],
      constraints: [],
      evidence: [],
      graph: { nodes: [], edges: [] },
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          run_id: "policy_run_test",
          status: "AWAITING_REVIEW",
          case_graph_ai: caseGraph,
          review_diff: [],
          truth_set_status: { status: "unavailable", message: "无历史回测数据，仅提供影响分析" },
          backtest_result: null,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "policy_run_test", status: "AWAITING_REVIEW", review_diff: [{ path: "/stakeholders/0/weight", before: null, after: 1.2 }] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ run_id: "policy_run_test", status: "AWAITING_ANCHOR_APPROVAL" }),
      });

    const status = await getPolicyRun("policy_run_test", fetchMock);
    const patch = await patchPolicyRunCaseGraph("policy_run_test", caseGraph, fetchMock);
    const approval = await approvePolicyRun("policy_run_test", fetchMock);

    expect(status.truth_set_status.message).toBe("无历史回测数据，仅提供影响分析");
    expect(patch.review_diff[0].path).toBe("/stakeholders/0/weight");
    expect(approval.status).toBe("AWAITING_ANCHOR_APPROVAL");
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/policy-runs/policy_run_test", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_graph: caseGraph }),
    });
  });

  it("surfaces backend error details", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ detail: "DEEPSEEK_API_KEY or LLM_API_KEY is required" }),
    });

    await expect(
      startPolicyRun({ policyText: "new policy", agentCount: 12, rounds: 2 }, fetchMock),
    ).rejects.toThrow("DEEPSEEK_API_KEY or LLM_API_KEY is required");
  });
});
