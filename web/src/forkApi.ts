/// <reference types="vite/client" />
import cachedCompareJson from "./data/fork_compare_showcase.json";
import cachedVerifyJson from "./data/verify_transcript.json";

// Client for the Fork API (docs/FORK_API.md). The static gh-pages build has no
// backend: callers catch fetch failures and fall back to the cached showcase
// payloads below, which were recorded against the real endpoints (the verify
// transcript against live Kaspa testnet-10).

export interface JsonPatchOp {
  op: "add" | "replace" | "remove";
  path: string;
  value?: unknown;
}

export interface ForkApprovalDiffEntry {
  path: string;
  before: unknown;
  after: unknown;
}

export interface ForkApprovalEvent {
  stage: string;
  editor?: string;
  actor?: string;
  diff: ForkApprovalDiffEntry[];
  patches: JsonPatchOp[];
  approved_hash?: string;
}

export interface ForkCreateResponse {
  parent_run_id: string;
  fork_id: string;
  name: string;
  status: string;
  approval_event?: ForkApprovalEvent;
}

export type ForkRowStatus = "changed" | "unchanged" | "new" | "removed";

export interface ForkCompareRow {
  key: string;
  status: ForkRowStatus;
  changed_fields?: string[];
  a: Record<string, unknown> | null;
  b: Record<string, unknown> | null;
}

export interface ForkComparison {
  parent_run_id: string;
  a: { fork_id: string; name: string };
  b: { fork_id: string; name: string };
  dimensions: {
    risk_timeline: ForkCompareRow[];
    claims: ForkCompareRow[];
    stakeholder_pressure: ForkCompareRow[];
  };
  summary: { changed: number; unchanged: number; new: number; removed: number };
}

export interface VerifyCheck {
  status: string;
  note: string;
}

export interface VerifyLink {
  id: string;
  stage: string;
  status: string;
}

export interface VerifyResult {
  overall: string;
  mode: string;
  network: string;
  txid: string;
  checks: Record<string, VerifyCheck>;
  links: VerifyLink[];
}

export const CACHED_FORK_COMPARISON = cachedCompareJson as unknown as ForkComparison;
export const CACHED_VERIFY_TRANSCRIPT = cachedVerifyJson as unknown as VerifyResult;

// Builds produced with DEMO_BASE (the deployed static showcase) have no
// backend: skip network calls entirely and serve the cached payloads, so the
// buttons degrade gracefully without dead requests.
export const STATIC_SHOWCASE = import.meta.env.BASE_URL !== "/";

type FetchLike = typeof fetch;

export async function createFork(
  runId: string,
  name: string,
  patches: JsonPatchOp[],
  fetcher: FetchLike = fetch,
): Promise<ForkCreateResponse> {
  const response = await fetcher(`/api/policy-runs/${encodeURIComponent(runId)}/forks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, case_graph_patches: patches }),
  });
  return parseJsonResponse<ForkCreateResponse>(response);
}

export async function compareForks(
  runId: string,
  forkIdA: string,
  forkIdB: string,
  fetcher: FetchLike = fetch,
): Promise<ForkComparison> {
  const query = `a=${encodeURIComponent(forkIdA)}&b=${encodeURIComponent(forkIdB)}`;
  const response = await fetcher(`/api/policy-runs/${encodeURIComponent(runId)}/forks/compare?${query}`);
  return parseJsonResponse<ForkComparison>(response);
}

export async function verifyAnchor(runId: string, fetcher: FetchLike = fetch): Promise<VerifyResult> {
  const response = await fetcher(`/api/anchors/${encodeURIComponent(runId)}/verify`);
  return parseJsonResponse<VerifyResult>(response);
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail =
      typeof (payload as { detail?: unknown }).detail === "string"
        ? (payload as { detail: string }).detail
        : `Fork API request failed with HTTP ${response.status}`;
    throw new Error(detail);
  }
  return payload as T;
}
