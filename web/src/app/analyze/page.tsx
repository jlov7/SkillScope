"use client";

import { useMemo, useState } from "react";

import EmptyState from "@/components/EmptyState";
import Shell from "@/components/Shell";
import { normalizeEvents, parseInput, summarizeEvents } from "@/lib/analyze";

const MAX_BYTES = 8 * 1024 * 1024;

export default function AnalyzePage() {
  const [content, setContent] = useState("");
  const [manualError, setManualError] = useState<string | null>(null);

  const analysis = useMemo(() => {
    if (!content) return { summary: null, error: null };
    try {
      const parsed = parseInput(content, "auto");
      const normalized = normalizeEvents(parsed);
      return { summary: summarizeEvents(normalized), error: null };
    } catch (err) {
      return { summary: null, error: (err as Error).message };
    }
  }, [content]);

  const error = manualError ?? analysis.error;
  const summary = analysis.summary;

  const handleFile = async (file: File | null) => {
    if (!file) return;
    if (file.size > MAX_BYTES) {
      setManualError("File too large. Please upload 8MB or smaller.");
      return;
    }
    setManualError(null);
    setContent(await file.text());
  };

  return (
    <Shell>
      <div className="space-y-6">
        <h1 className="text-3xl font-semibold">Analyze your events</h1>
        <p className="text-[var(--muted)]">Client-side analysis only. No data leaves your browser.</p>
        <input
          type="file"
          accept=".json,.jsonl,.ndjson"
          onChange={(event) => handleFile(event.target.files?.[0] ?? null)}
          aria-label="Upload SkillScope events"
        />
        {error && (
          <div role="alert" className="text-red-600">
            {error}
          </div>
        )}
        {!summary ? (
          <EmptyState
            title="No data yet"
            body="Upload JSON or JSONL from skillscope emit/ingest to see summaries."
          />
        ) : (
          <div className="space-y-6">
            <section className="grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl bg-white border border-[var(--border)] p-4">
                <p className="text-sm text-[var(--muted)]">Total events</p>
                <p className="text-2xl font-semibold">{summary.total_events}</p>
              </div>
              <div className="rounded-2xl bg-white border border-[var(--border)] p-4">
                <p className="text-sm text-[var(--muted)]">Skills observed</p>
                <p className="text-2xl font-semibold">{summary.total_skills}</p>
              </div>
              <div className="rounded-2xl bg-white border border-[var(--border)] p-4">
                <p className="text-sm text-[var(--muted)]">Total tokens</p>
                <p className="text-2xl font-semibold">{summary.total_tokens}</p>
              </div>
            </section>
            <section className="rounded-3xl bg-white border border-[var(--border)] p-6">
              <h2 className="text-xl font-semibold mb-4">Skills</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[var(--muted)]">
                      <th className="py-2">Skill</th>
                      <th className="py-2">Calls</th>
                      <th className="py-2">Avg tokens</th>
                      <th className="py-2">Policy %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(summary.skills).map(([skill, data]) => (
                      <tr key={skill} className="border-t border-[var(--border)]">
                        <td className="py-2 font-medium">{skill}</td>
                        <td className="py-2">{data.calls}</td>
                        <td className="py-2">{data.tokens_average.toFixed(1)}</td>
                        <td className="py-2">{(data.policy_rate * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}
      </div>
    </Shell>
  );
}
