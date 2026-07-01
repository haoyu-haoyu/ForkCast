import type { LivePolicyRunResult, LivePolicyRunStart, LivePolicyRunStatus } from "./types";

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
  const started = await startPolicyRun(input, fetcher);
  return getPolicyRun(started.run_id, fetcher) as Promise<LivePolicyRunResult>;
}

export async function startPolicyRun(
  input: SubmitPolicyRunInput,
  fetcher: FetchLike = fetch,
): Promise<LivePolicyRunStart> {
  const response = await fetcher("/api/policy-runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      policy_text: input.policyText,
      agent_count: input.agentCount,
      rounds: input.rounds,
    }),
  });
  return parseJsonResponse<LivePolicyRunStart>(response);
}

export async function getPolicyRun(runId: string, fetcher: FetchLike = fetch): Promise<LivePolicyRunStatus> {
  const response = await fetcher(`/api/policy-runs/${encodeURIComponent(runId)}`);
  return parseJsonResponse<LivePolicyRunStatus>(response);
}

export async function patchPolicyRunCaseGraph(
  runId: string,
  caseGraph: LivePolicyRunStatus["case_graph_ai"],
  fetcher: FetchLike = fetch,
): Promise<{ run_id: string; status: string; review_diff: LivePolicyRunStatus["review_diff"] }> {
  const response = await fetcher(`/api/policy-runs/${encodeURIComponent(runId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ case_graph: caseGraph }),
  });
  return parseJsonResponse(response);
}

export async function approvePolicyRun(
  runId: string,
  fetcher: FetchLike = fetch,
): Promise<LivePolicyRunStart> {
  const response = await fetcher(`/api/policy-runs/${encodeURIComponent(runId)}/approve`, {
    method: "POST",
  });
  return parseJsonResponse<LivePolicyRunStart>(response);
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : `Policy run failed with HTTP ${response.status}`;
    throw new Error(detail);
  }
  return payload as T;
}
