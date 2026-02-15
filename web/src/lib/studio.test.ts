import { describe, expect, it } from "vitest";

import { buildReplaySteps, compareRunContents, compareRuns } from "./studio";
import type { EventRecord } from "./analyze";

describe("buildReplaySteps", () => {
  it("orders replay steps by timestamp with stable fallback ordering", () => {
    const events: EventRecord[] = [
      {
        ts: "2026-02-15T11:00:02.000Z",
        event: "end",
        attrs: { "skill.name": "Writer", "gen_ai.usage.input_tokens": 80, "gen_ai.usage.output_tokens": 50 },
      },
      {
        ts: "2026-02-15T11:00:01.000Z",
        event: "start",
        attrs: { "skill.name": "Writer", "gen_ai.usage.input_tokens": 0, "gen_ai.usage.output_tokens": 0 },
      },
      {
        event: "tool.call",
        attrs: { "skill.name": "Writer", "gen_ai.usage.input_tokens": 10, "gen_ai.usage.output_tokens": 5 },
      },
    ];

    const steps = buildReplaySteps(events);
    expect(steps).toHaveLength(3);
    expect(steps[0].event).toBe("start");
    expect(steps[1].event).toBe("end");
    expect(steps[2].event).toBe("tool.call");
    expect(steps[2].tsMs).toBeNull();
  });
});

describe("compareRuns", () => {
  it("detects high-severity regressions for missing skills and error growth", () => {
    const baseline: EventRecord[] = [
      {
        ts: 1739617201,
        event: "end",
        attrs: {
          "skill.name": "Planner",
          "gen_ai.usage.input_tokens": 100,
          "gen_ai.usage.output_tokens": 40,
          "skill.policy_required": false,
          latency_ms: 120,
        },
      },
      {
        ts: 1739617202,
        event: "end",
        attrs: {
          "skill.name": "Writer",
          "gen_ai.usage.input_tokens": 150,
          "gen_ai.usage.output_tokens": 80,
          "skill.policy_required": false,
          latency_ms: 180,
        },
      },
    ];

    const current: EventRecord[] = [
      {
        ts: 1739617301,
        event: "error",
        attrs: {
          "skill.name": "Writer",
          "gen_ai.usage.input_tokens": 420,
          "gen_ai.usage.output_tokens": 260,
          "skill.policy_required": true,
          latency_ms: 380,
          status: "error",
        },
      },
    ];

    const result = compareRuns(baseline, current);
    expect(result.regressions.length).toBeGreaterThan(0);
    expect(result.insights.some((insight) => insight.id === "missing-skills")).toBe(true);
    expect(result.insights.some((insight) => insight.id === "error-spike")).toBe(true);
    expect(result.deltas.totalTokens.absolute).toBeGreaterThan(0);
  });
});

describe("compareRunContents", () => {
  it("returns a stable insight when runs are equivalent", () => {
    const payload =
      "{\"event\":\"end\",\"attrs\":{\"skill.name\":\"Brand Voice\",\"gen_ai.usage.input_tokens\":10,\"gen_ai.usage.output_tokens\":5,\"latency_ms\":90}}\n";
    const result = compareRunContents(payload, payload);
    expect(result.insights[0].id).toBe("stable");
    expect(result.deltas.totalTokens.absolute).toBe(0);
  });
});
