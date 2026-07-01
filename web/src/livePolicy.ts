import type { LivePolicyRunResult } from "./types";

export interface SubmitPolicyRunInput {
  policyText: string;
  agentCount: number;
  rounds: number;
}

type FetchLike = typeof fetch;

export async function submitPolicyRun(
  input: SubmitPolicyRunInput,
  fetcher: FetchLike = fetch,
): Promise<LivePolicyRunResult> {
  const response = await fetcher("/api/policy-runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      policy_text: input.policyText,
      agent_count: input.agentCount,
      rounds: input.rounds,
    }),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : `Policy run failed with HTTP ${response.status}`;
    throw new Error(detail);
  }

  return payload as LivePolicyRunResult;
}
