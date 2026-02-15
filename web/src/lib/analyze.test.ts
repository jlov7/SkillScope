import { describe, expect, it } from "vitest";

import { parseInput, summarizeEvents } from "./analyze";

const demoJsonl =
  "{\"event\":\"end\",\"attrs\":{\"skill.name\":\"Brand Voice\",\"gen_ai.usage.input_tokens\":10,\"gen_ai.usage.output_tokens\":5}}\n";

describe("parseInput", () => {
  it("parses JSONL into events", () => {
    const events = parseInput(demoJsonl, "jsonl");
    expect(events).toHaveLength(1);
    expect(events[0].attrs["skill.name"]).toBe("Brand Voice");
  });
});

describe("summarizeEvents", () => {
  it("summarizes tokens and calls", () => {
    const events = parseInput(demoJsonl, "jsonl");
    const summary = summarizeEvents(events);
    expect(summary.total_events).toBe(1);
    expect(summary.skills["Brand Voice"].calls).toBe(1);
    expect(summary.total_tokens).toBe(15);
  });
});
