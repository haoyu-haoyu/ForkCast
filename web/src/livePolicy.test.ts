import { describe, expect, it, vi } from "vitest";
import { submitPolicyRun } from "./livePolicy";

describe("submitPolicyRun", () => {
  it("posts a new policy document to the backend and returns impact analysis without backtest", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        run_id: "policy_run_test",
        mode: "live_policy_analysis",
        truth_set_status: {
          status: "unavailable",
          message: "无历史回测数据，仅提供影响分析",
        },
        case_graph: {
          case_id: "school_street_trial",
          case_name: "School Street Trial",
          stakeholders: [],
          assumptions: [],
        },
        agents: { agents: [] },
        impact_report: {
          stakeholder_impact_matrix: [],
          risk_timeline: [],
          mitigation_options: [],
          confidence_notes: [],
          disclaimer: "simulation is decision support, not deterministic forecast",
        },
        backtest_result: null,
      }),
    });

    const result = await submitPolicyRun(
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
    expect(result.truth_set_status.message).toBe("无历史回测数据，仅提供影响分析");
    expect(result.backtest_result).toBeNull();
  });

  it("surfaces backend error details", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ detail: "DEEPSEEK_API_KEY or LLM_API_KEY is required" }),
    });

    await expect(
      submitPolicyRun({ policyText: "new policy", agentCount: 12, rounds: 2 }, fetchMock),
    ).rejects.toThrow("DEEPSEEK_API_KEY or LLM_API_KEY is required");
  });
});
