import type { LivePolicyReviewDiff, LivePolicyRunStatus } from "./types";

type CaseGraph = NonNullable<LivePolicyRunStatus["case_graph_ai"]>;

export function diffCaseGraphReview(before: CaseGraph | null | undefined, after: CaseGraph | null | undefined) {
  if (!before || !after) return [];
  return diffJson(before, after);
}

export function hasUnsavedReviewDiff(before: CaseGraph | null | undefined, after: CaseGraph | null | undefined) {
  return diffCaseGraphReview(before, after).length > 0;
}

function diffJson(before: unknown, after: unknown, path = ""): LivePolicyReviewDiff[] {
  if (typeTag(before) !== typeTag(after)) {
    return [{ path: path || "/", before: normalizeMissing(before), after: normalizeMissing(after) }];
  }
  if (isRecord(before) && isRecord(after)) {
    return Array.from(new Set([...Object.keys(before), ...Object.keys(after)]))
      .sort()
      .flatMap((key) => {
        const childPath = `${path}/${escapePath(key)}`;
        if (!(key in before)) return [{ path: childPath, before: null, after: after[key] }];
        if (!(key in after)) return [{ path: childPath, before: before[key], after: null }];
        return diffJson(before[key], after[key], childPath);
      });
  }
  if (Array.isArray(before) && Array.isArray(after)) {
    return Array.from({ length: Math.max(before.length, after.length) }).flatMap((_, index) => {
      const childPath = `${path}/${index}`;
      if (index >= before.length) return [{ path: childPath, before: null, after: after[index] }];
      if (index >= after.length) return [{ path: childPath, before: before[index], after: null }];
      return diffJson(before[index], after[index], childPath);
    });
  }
  return before === after ? [] : [{ path: path || "/", before: normalizeMissing(before), after: normalizeMissing(after) }];
}

function typeTag(value: unknown) {
  if (Array.isArray(value)) return "array";
  if (value === null || value === undefined) return "nullish";
  return typeof value;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function normalizeMissing(value: unknown) {
  return value === undefined ? null : value;
}

function escapePath(value: string) {
  return value.replace(/~/g, "~0").replace(/\//g, "~1");
}
