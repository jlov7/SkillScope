"use client";

import { useState } from "react";

import Shell from "@/components/Shell";

type ViewMode = "non-technical" | "technical";

const NON_TECHNICAL_POINTS = [
  "Agent behavior changes are hard to spot from raw logs.",
  "SkillScope compares a known-good run against a current run in minutes.",
  "You get a clear explanation of what changed and what to do next.",
  "No signup or backend is required for first value.",
];

const TECHNICAL_POINTS = [
  "Client-side pipeline: parse -> normalize -> summarize -> compare -> heuristic insights.",
  "Semantics align to `skill.*` attributes plus OpenTelemetry GenAI fields.",
  "Replay timeline is deterministic with stable ordering and timestamp coercion.",
  "Diff outputs include global deltas and per-skill regressions for fast triage.",
];

export default function WhyPage() {
  const [mode, setMode] = useState<ViewMode>("non-technical");
  const points = mode === "non-technical" ? NON_TECHNICAL_POINTS : TECHNICAL_POINTS;

  return (
    <Shell>
      <div className="space-y-8">
        <section className="space-y-4">
          <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">Why SkillScope</p>
          <h1 className="text-3xl font-semibold">Explain what it does, why it exists, and how it works</h1>
          <p className="text-[var(--muted)] max-w-3xl">
            Use this page to tailor your explanation for executives, product teams, engineers, or
            operators without changing the core story.
          </p>
          <div className="inline-flex rounded-full border border-[var(--border)] bg-white p-1">
            <button
              type="button"
              onClick={() => setMode("non-technical")}
              className={`px-3 py-1.5 rounded-full text-sm ${
                mode === "non-technical" ? "bg-[var(--accent)] text-white" : ""
              }`}
            >
              Non-technical
            </button>
            <button
              type="button"
              onClick={() => setMode("technical")}
              className={`px-3 py-1.5 rounded-full text-sm ${
                mode === "technical" ? "bg-[var(--accent)] text-white" : ""
              }`}
            >
              Technical
            </button>
          </div>
        </section>

        <section className="rounded-3xl border border-[var(--border)] bg-white p-6 space-y-4">
          <h2 className="text-2xl font-semibold">
            {mode === "non-technical" ? "Business narrative" : "Engineering narrative"}
          </h2>
          <ul className="list-disc pl-5 space-y-2 text-[var(--muted)]">
            {points.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          <article className="rounded-2xl border border-[var(--border)] bg-white p-5">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">Why it was built</p>
            <p className="mt-2 text-sm text-[var(--muted)]">
              To make agent regressions observable and explainable for real teams without requiring
              heavy infrastructure just to get started.
            </p>
          </article>
          <article className="rounded-2xl border border-[var(--border)] bg-white p-5">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">How to prove value</p>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Run the guided Studio demo, then switch to your own baseline/current logs and show how
              quickly the same workflow surfaces actionable differences.
            </p>
          </article>
        </section>
      </div>
    </Shell>
  );
}
