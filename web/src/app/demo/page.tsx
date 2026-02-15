"use client";

import { useMemo } from "react";

import Shell from "@/components/Shell";
import { normalizeEvents, parseInput, summarizeEvents } from "@/lib/analyze";
import demoData from "@/lib/demo-data";

export default function DemoPage() {
  const summary = useMemo(() => summarizeEvents(normalizeEvents(parseInput(demoData, "jsonl"))), []);

  return (
    <Shell>
      <div className="space-y-6">
        <h1 className="text-3xl font-semibold">Demo</h1>
        <p className="text-[var(--muted)]">Sample dataset, analyzed locally in your browser.</p>
        <pre className="rounded-2xl bg-white border border-[var(--border)] p-4 text-sm overflow-x-auto">
          {JSON.stringify(summary, null, 2)}
        </pre>
      </div>
    </Shell>
  );
}
