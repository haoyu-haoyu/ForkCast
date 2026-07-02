import { describe, expect, it } from "vitest";
import { diffCaseGraphReview, hasUnsavedReviewDiff } from "./liveReview";
import type { LivePolicyRunStatus } from "./types";

const proposed: NonNullable<LivePolicyRunStatus["case_graph_ai"]> = {
  case_id: "aps_permitting_scheme",
  case_name: "APS Permitting Scheme",
  stakeholders: [
    {
      id: "operator",
      name: "APS Operator",
      archetype_group: "industry",
      stance_prior: "supportive",
      interests: ["deployment"],
    },
    {
      id: "local_authority",
      name: "Local Authority",
      archetype_group: "regulator",
      stance_prior: "cautious",
      interests: ["local_consent"],
    },
  ],
  assumptions: [],
};

describe("live review diff helpers", () => {
  it("detects pending local edits before they are saved to the server", () => {
    const draft = structuredClone(proposed);
    draft.stakeholders[0].weight = 0.8;

    expect(diffCaseGraphReview(proposed, draft)).toEqual([
      { path: "/stakeholders/0/weight", before: null, after: 0.8 },
    ]);
    expect(hasUnsavedReviewDiff(proposed, draft)).toBe(true);
  });

  it("handles unchanged all-null extracted weights as an empty diff", () => {
    const draft = structuredClone(proposed);

    expect(diffCaseGraphReview(proposed, draft)).toEqual([]);
    expect(hasUnsavedReviewDiff(proposed, draft)).toBe(false);
  });
});
