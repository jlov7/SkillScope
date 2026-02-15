"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";

import EmptyState from "@/components/EmptyState";
import Shell from "@/components/Shell";
import {
  compareRunContents,
  type DeltaMetric,
  type ReplayStep,
  type RunComparison,
} from "@/lib/studio";
import { studioBaselineData, studioCurrentData } from "@/lib/studio-demo";

const MAX_BYTES = 8 * 1024 * 1024;
const EMPTY_STEPS: ReplayStep[] = [];
const DEMO_QUERY_LINK = "/studio?demo=1&guide=1";
const PLAY_SPEEDS = [
  { label: "0.5x", value: 1600 },
  { label: "1x", value: 900 },
  { label: "1.5x", value: 600 },
  { label: "2x", value: 400 },
];

type WalkthroughStep = {
  id: string;
  title: string;
  body: string;
  target: string;
  actionLabel: string;
};

const WALKTHROUGH_STEPS: WalkthroughStep[] = [
  {
    id: "load",
    title: "Load known baseline and regression runs",
    body: "Use demo runs to recreate a realistic baseline-vs-current failure scenario in seconds.",
    target: "studio-upload",
    actionLabel: "Load demo runs",
  },
  {
    id: "replay",
    title: "Inspect the execution timeline",
    body: "Jump to replay and inspect the earliest steps before failure behavior appears.",
    target: "studio-replay",
    actionLabel: "Focus replay",
  },
  {
    id: "animate",
    title: "Animate behavior drift",
    body: "Play through the current run to make timing and sequence changes easy to explain live.",
    target: "studio-replay",
    actionLabel: "Play timeline",
  },
  {
    id: "insight",
    title: "Show likely root causes",
    body: "Use the generated root-cause cards to explain what changed and why it likely regressed.",
    target: "studio-insights",
    actionLabel: "Open root causes",
  },
  {
    id: "delta",
    title: "Land on concrete engineering action",
    body: "Finish on skill-level deltas to assign next actions with clear before/after evidence.",
    target: "studio-deltas",
    actionLabel: "Open skill deltas",
  },
];

const numberFormatter = new Intl.NumberFormat("en-US");

const formatNumber = (value: number): string => {
  return numberFormatter.format(Math.round(value));
};

const formatPercent = (value: number, digits = 1): string => {
  return `${(value * 100).toFixed(digits)}%`;
};

const formatDelta = (metric: DeltaMetric, digits = 1): string => {
  const sign = metric.absolute > 0 ? "+" : "";
  const absolute = `${sign}${metric.absolute.toFixed(digits)}`;
  if (metric.percent === null) return `${absolute} (new)`;
  return `${absolute} (${sign}${metric.percent.toFixed(digits)}%)`;
};

const deltaTone = (metric: DeltaMetric, preferLower: boolean): string => {
  if (metric.absolute === 0) return "text-[var(--muted)]";
  const regression = preferLower ? metric.absolute > 0 : metric.absolute < 0;
  return regression ? "text-red-700" : "text-emerald-700";
};

const insightTone = (severity: string): string => {
  if (severity === "high") return "border-red-200 bg-red-50";
  if (severity === "medium") return "border-amber-200 bg-amber-50";
  if (severity === "low") return "border-blue-200 bg-blue-50";
  return "border-[var(--border)] bg-white";
};

const scrollToSection = (id: string): void => {
  const target = document.getElementById(id);
  if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
};

function MetricCard({
  label,
  value,
  delta,
  preferLower,
}: {
  label: string;
  value: string;
  delta: DeltaMetric;
  preferLower: boolean;
}) {
  return (
    <div className="rounded-2xl bg-white border border-[var(--border)] p-4">
      <p className="text-sm text-[var(--muted)]">{label}</p>
      <p className="text-2xl font-semibold">{value}</p>
      <p className={`text-sm ${deltaTone(delta, preferLower)}`}>{formatDelta(delta)}</p>
    </div>
  );
}

function StepDetail({ step }: { step: ReplayStep | null }) {
  if (!step) {
    return (
      <div className="rounded-2xl border border-dashed border-[var(--border)] p-4 text-[var(--muted)]">
        Select a step to inspect details.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-[var(--border)] bg-white p-4 space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center rounded-full border border-[var(--border)] px-2.5 py-1 text-xs">
          {step.event}
        </span>
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs ${
            step.isError ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-700"
          }`}
        >
          {step.isError ? "error" : "ok"}
        </span>
      </div>
      <div className="grid gap-3 md:grid-cols-3 text-sm">
        <div>
          <p className="text-[var(--muted)]">Skill</p>
          <p className="font-medium">{step.skill}</p>
        </div>
        <div>
          <p className="text-[var(--muted)]">Model</p>
          <p className="font-medium">{step.model || "—"}</p>
        </div>
        <div>
          <p className="text-[var(--muted)]">Policy required</p>
          <p className="font-medium">{step.policyRequired ? "Yes" : "No"}</p>
        </div>
        <div>
          <p className="text-[var(--muted)]">Tokens</p>
          <p className="font-medium">{formatNumber(step.totalTokens)}</p>
        </div>
        <div>
          <p className="text-[var(--muted)]">Latency</p>
          <p className="font-medium">
            {step.latencyMs === null ? "—" : `${step.latencyMs.toFixed(1)} ms`}
          </p>
        </div>
        <div>
          <p className="text-[var(--muted)]">Files</p>
          <p className="font-medium">{step.files.length > 0 ? step.files.join(", ") : "—"}</p>
        </div>
      </div>
    </div>
  );
}

function StudioContent() {
  const searchParams = useSearchParams();
  const requestedDemo = searchParams.get("demo") === "1";
  const requestedGuide = searchParams.get("guide") === "1";

  const [baselineContent, setBaselineContent] = useState(() =>
    requestedDemo ? studioBaselineData : ""
  );
  const [currentContent, setCurrentContent] = useState(() =>
    requestedDemo ? studioCurrentData : ""
  );
  const [manualError, setManualError] = useState<string | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speedMs, setSpeedMs] = useState(900);
  const [guideIndex, setGuideIndex] = useState<number | null>(() => (requestedGuide ? 0 : null));
  const [copyNotice, setCopyNotice] = useState<string | null>(null);

  const analysis = useMemo((): { comparison: RunComparison | null; error: string | null } => {
    if (!baselineContent || !currentContent) return { comparison: null, error: null };
    try {
      return { comparison: compareRunContents(baselineContent, currentContent), error: null };
    } catch (error) {
      return { comparison: null, error: (error as Error).message };
    }
  }, [baselineContent, currentContent]);

  const comparison = analysis.comparison;
  const error = manualError ?? analysis.error;
  const replaySteps = comparison?.current.steps ?? EMPTY_STEPS;
  const maxStepIndex = Math.max(0, replaySteps.length - 1);
  const safeActiveIndex = Math.min(activeIndex, maxStepIndex);
  const activeStep = replaySteps[safeActiveIndex] ?? null;
  const currentGuideStep = guideIndex === null ? null : WALKTHROUGH_STEPS[guideIndex];
  const isGuideComplete = guideIndex !== null && guideIndex >= WALKTHROUGH_STEPS.length - 1;

  useEffect(() => {
    if (!isPlaying || replaySteps.length === 0 || safeActiveIndex >= replaySteps.length - 1) return;
    const timer = window.setTimeout(() => {
      setActiveIndex((previous) => {
        const next = Math.min(previous + 1, replaySteps.length - 1);
        if (next >= replaySteps.length - 1) setIsPlaying(false);
        return next;
      });
    }, speedMs);
    return () => window.clearTimeout(timer);
  }, [isPlaying, replaySteps.length, safeActiveIndex, speedMs]);

  const visibleSteps = useMemo(() => {
    const start = Math.max(0, safeActiveIndex - 3);
    const end = Math.min(replaySteps.length, safeActiveIndex + 4);
    return replaySteps.slice(start, end);
  }, [safeActiveIndex, replaySteps]);

  const handleUpload = async (target: "baseline" | "current", file: File | null) => {
    if (!file) return;
    if (file.size > MAX_BYTES) {
      setManualError("File too large. Please upload 8MB or smaller.");
      return;
    }
    setManualError(null);
    const content = await file.text();
    if (target === "baseline") {
      setBaselineContent(content);
      setActiveIndex(0);
      setIsPlaying(false);
      return;
    }
    setCurrentContent(content);
    setActiveIndex(0);
    setIsPlaying(false);
  };

  const loadDemo = () => {
    setManualError(null);
    setIsPlaying(false);
    setActiveIndex(0);
    setBaselineContent(studioBaselineData);
    setCurrentContent(studioCurrentData);
  };

  const clearAll = () => {
    setManualError(null);
    setBaselineContent("");
    setCurrentContent("");
    setIsPlaying(false);
    setActiveIndex(0);
    setGuideIndex(null);
  };

  const applyGuideAction = (stepIndex: number) => {
    const step = WALKTHROUGH_STEPS[stepIndex];
    if (!step) return;

    if (step.id === "load") loadDemo();
    if (step.id === "replay") {
      setIsPlaying(false);
      setActiveIndex(0);
    }
    if (step.id === "animate") {
      if (replaySteps.length > 0) setIsPlaying(true);
    }
    if (step.id === "insight") setIsPlaying(false);
    if (step.id === "delta") setIsPlaying(false);

    window.setTimeout(() => scrollToSection(step.target), 50);
  };

  const startGuide = () => {
    setGuideIndex(0);
    applyGuideAction(0);
  };

  const nextGuideStep = () => {
    if (guideIndex === null) {
      startGuide();
      return;
    }
    const next = Math.min(guideIndex + 1, WALKTHROUGH_STEPS.length - 1);
    setGuideIndex(next);
    applyGuideAction(next);
  };

  const resetGuide = () => {
    setGuideIndex(0);
    applyGuideAction(0);
  };

  const copyDemoLink = async () => {
    const absoluteUrl = `${window.location.origin}${DEMO_QUERY_LINK}`;
    try {
      await navigator.clipboard.writeText(absoluteUrl);
      setCopyNotice("Demo link copied.");
      window.setTimeout(() => setCopyNotice(null), 2500);
    } catch {
      setCopyNotice("Copy failed. Use the link shown below.");
      window.setTimeout(() => setCopyNotice(null), 4000);
    }
  };

  return (
    <Shell>
      <div className="space-y-8">
        <section className="space-y-4">
          <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">
            Replay + Compare Studio
          </p>
          <h1 className="text-3xl font-semibold">Find regressions fast with timeline replay</h1>
          <p className="text-[var(--muted)] max-w-3xl">
            Upload a baseline run and a current run. SkillScope reconstructs replay steps, highlights
            diffs, and suggests likely root causes. All analysis stays in your browser.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={loadDemo}
              className="px-4 py-2 rounded-full bg-[var(--accent)] text-white"
            >
              Load demo runs
            </button>
            <button
              type="button"
              onClick={startGuide}
              className="px-4 py-2 rounded-full border border-[var(--border)]"
            >
              Start guided walkthrough
            </button>
            <button
              type="button"
              onClick={clearAll}
              className="px-4 py-2 rounded-full border border-[var(--border)]"
            >
              Clear
            </button>
          </div>
        </section>

        <section className="rounded-3xl border border-[var(--border)] bg-white p-6 space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold">Presenter Mode</h2>
              <p className="text-sm text-[var(--muted)]">
                Use this guided sequence to demo SkillScope in a predictable, high-impact flow.
              </p>
            </div>
            <button
              type="button"
              onClick={copyDemoLink}
              className="px-3 py-1.5 rounded-full border border-[var(--border)] text-sm"
            >
              Copy shareable demo link
            </button>
          </div>
          {copyNotice && <p className="text-sm text-[var(--muted)]">{copyNotice}</p>}
          <p className="text-xs text-[var(--muted)]">
            Deep link:{" "}
            <Link href={DEMO_QUERY_LINK} className="underline hover:no-underline">
              {DEMO_QUERY_LINK}
            </Link>
          </p>
          <ol className="grid gap-3 md:grid-cols-2">
            {WALKTHROUGH_STEPS.map((step, index) => {
              const active = guideIndex === index;
              const done = guideIndex !== null && guideIndex > index;
              return (
                <li
                  key={step.id}
                  className={`rounded-2xl border p-3 ${
                    active
                      ? "border-[var(--accent)] bg-blue-50"
                      : done
                        ? "border-emerald-200 bg-emerald-50"
                        : "border-[var(--border)]"
                  }`}
                >
                  <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">
                    Step {index + 1}
                  </p>
                  <p className="font-medium">{step.title}</p>
                  <p className="text-sm text-[var(--muted)]">{step.body}</p>
                </li>
              );
            })}
          </ol>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={nextGuideStep}
              className="px-3 py-1.5 rounded-full bg-[var(--accent)] text-white text-sm"
            >
              {guideIndex === null
                ? "Begin guide"
                : isGuideComplete
                  ? "Repeat final step"
                  : `Next: ${WALKTHROUGH_STEPS[Math.min(guideIndex + 1, WALKTHROUGH_STEPS.length - 1)].actionLabel}`}
            </button>
            {guideIndex !== null && (
              <button
                type="button"
                onClick={resetGuide}
                className="px-3 py-1.5 rounded-full border border-[var(--border)] text-sm"
              >
                Restart guide
              </button>
            )}
            {guideIndex !== null && currentGuideStep && (
              <button
                type="button"
                onClick={() => applyGuideAction(guideIndex)}
                className="px-3 py-1.5 rounded-full border border-[var(--border)] text-sm"
              >
                Do current step action
              </button>
            )}
          </div>
        </section>

        <section id="studio-upload" className="grid gap-4 md:grid-cols-2">
          <label className="rounded-2xl bg-white border border-[var(--border)] p-4">
            <span className="block text-sm font-medium mb-2">Baseline run</span>
            <input
              type="file"
              accept=".json,.jsonl,.ndjson"
              onChange={(event) => handleUpload("baseline", event.target.files?.[0] ?? null)}
              aria-label="Upload baseline run"
              className="block w-full text-sm"
            />
            <span className="block text-xs text-[var(--muted)] mt-2">
              Use a known-good run as your baseline reference.
            </span>
          </label>
          <label className="rounded-2xl bg-white border border-[var(--border)] p-4">
            <span className="block text-sm font-medium mb-2">Current run</span>
            <input
              type="file"
              accept=".json,.jsonl,.ndjson"
              onChange={(event) => handleUpload("current", event.target.files?.[0] ?? null)}
              aria-label="Upload current run"
              className="block w-full text-sm"
            />
            <span className="block text-xs text-[var(--muted)] mt-2">
              Upload the run you suspect has regressions.
            </span>
          </label>
        </section>

        {error && (
          <section role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </section>
        )}

        {!comparison ? (
          <EmptyState
            title="No comparison yet"
            body="Upload both baseline and current runs, or load the demo, to start replay and diff analysis."
            cta={
              <p className="text-sm text-[var(--muted)]">
                Need context first? Visit{" "}
                <Link href="/start" className="underline hover:no-underline">
                  Start
                </Link>{" "}
                or{" "}
                <Link href="/why" className="underline hover:no-underline">
                  Why
                </Link>
                .
              </p>
            }
          />
        ) : (
          <div className="space-y-8">
            <section id="studio-summary" className="rounded-2xl border border-[var(--border)] bg-white p-4">
              <p className="text-sm text-[var(--muted)]">Run summary</p>
              <p className="text-lg font-medium">{comparison.summaryText}</p>
            </section>

            <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <MetricCard
                label="Total calls"
                value={formatNumber(comparison.deltas.totalCalls.current)}
                delta={comparison.deltas.totalCalls}
                preferLower={false}
              />
              <MetricCard
                label="Total tokens"
                value={formatNumber(comparison.deltas.totalTokens.current)}
                delta={comparison.deltas.totalTokens}
                preferLower={true}
              />
              <MetricCard
                label="Errors"
                value={formatNumber(comparison.deltas.errorCount.current)}
                delta={comparison.deltas.errorCount}
                preferLower={true}
              />
              <MetricCard
                label="p95 latency (ms)"
                value={comparison.deltas.p95LatencyMs.current.toFixed(1)}
                delta={comparison.deltas.p95LatencyMs}
                preferLower={true}
              />
            </section>

            <section id="studio-replay" className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
              <div className="rounded-3xl border border-[var(--border)] bg-white p-6 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h2 className="text-xl font-semibold">Replay current run</h2>
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setActiveIndex((index) => Math.max(index - 1, 0))}
                      className="px-3 py-1.5 rounded-full border border-[var(--border)] text-sm"
                      aria-label="Previous step"
                    >
                      Prev
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        if (isPlaying) {
                          setIsPlaying(false);
                          return;
                        }
                        if (safeActiveIndex >= replaySteps.length - 1) setActiveIndex(0);
                        setIsPlaying(true);
                      }}
                      className="px-3 py-1.5 rounded-full bg-[var(--accent)] text-white text-sm"
                      aria-label={isPlaying ? "Pause replay" : "Play replay"}
                    >
                      {isPlaying ? "Pause" : "Play"}
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        setActiveIndex((index) => Math.min(index + 1, Math.max(replaySteps.length - 1, 0)))
                      }
                      className="px-3 py-1.5 rounded-full border border-[var(--border)] text-sm"
                      aria-label="Next step"
                    >
                      Next
                    </button>
                  </div>
                </div>

                <label className="block text-sm text-[var(--muted)]">
                  Replay speed
                  <select
                    value={speedMs}
                    onChange={(event) => setSpeedMs(Number(event.target.value))}
                    className="ml-3 rounded-lg border border-[var(--border)] px-2 py-1 bg-white"
                    aria-label="Replay speed"
                  >
                    {PLAY_SPEEDS.map((speed) => (
                      <option key={speed.value} value={speed.value}>
                        {speed.label}
                      </option>
                    ))}
                  </select>
                </label>

                <div>
                  <label htmlFor="timeline-scrubber" className="text-sm text-[var(--muted)]">
                    Step {replaySteps.length === 0 ? 0 : safeActiveIndex + 1} of {replaySteps.length}
                  </label>
                  <input
                    id="timeline-scrubber"
                    type="range"
                    min={0}
                    max={Math.max(0, replaySteps.length - 1)}
                    value={safeActiveIndex}
                    onChange={(event) => setActiveIndex(Number(event.target.value))}
                    className="w-full mt-2"
                    aria-label="Timeline scrubber"
                  />
                </div>

                <StepDetail step={activeStep} />
              </div>

              <div className="rounded-3xl border border-[var(--border)] bg-white p-6 space-y-3">
                <h2 className="text-xl font-semibold">Timeline focus window</h2>
                <ul className="space-y-2">
                  {visibleSteps.map((step) => (
                    <li key={step.id}>
                      <button
                        type="button"
                        onClick={() => setActiveIndex(step.index)}
                        className={`w-full text-left rounded-xl border px-3 py-2 ${
                          step.index === safeActiveIndex
                            ? "border-[var(--accent)] bg-blue-50"
                            : "border-[var(--border)] bg-white"
                        }`}
                      >
                        <p className="text-sm font-medium">
                          {step.index + 1}. {step.skill} · {step.event}
                        </p>
                        <p className="text-xs text-[var(--muted)]">
                          tokens {formatNumber(step.totalTokens)} · latency{" "}
                          {step.latencyMs === null ? "—" : `${step.latencyMs.toFixed(1)}ms`}
                        </p>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            </section>

            <section id="studio-insights" className="rounded-3xl border border-[var(--border)] bg-white p-6 space-y-4">
              <h2 className="text-xl font-semibold">Likely root causes</h2>
              <div className="grid gap-3">
                {comparison.insights.map((insight) => (
                  <article
                    key={insight.id}
                    className={`rounded-2xl border p-4 ${insightTone(insight.severity)}`}
                  >
                    <p className="text-sm uppercase tracking-[0.16em] text-[var(--muted)]">
                      {insight.severity}
                    </p>
                    <h3 className="text-lg font-semibold">{insight.title}</h3>
                    <p className="text-sm">{insight.explanation}</p>
                    <p className="text-sm text-[var(--muted)] mt-1">Next action: {insight.recommendation}</p>
                  </article>
                ))}
              </div>
            </section>

            <section id="studio-deltas" className="rounded-3xl border border-[var(--border)] bg-white p-6">
              <h2 className="text-xl font-semibold mb-3">Skill-level deltas</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[var(--muted)] border-b border-[var(--border)]">
                      <th className="py-2">Skill</th>
                      <th className="py-2">Class</th>
                      <th className="py-2">Calls</th>
                      <th className="py-2">Tokens</th>
                      <th className="py-2">Avg latency</th>
                      <th className="py-2">Errors</th>
                      <th className="py-2">Policy rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparison.skillDeltas.map((skillDelta) => (
                      <tr key={skillDelta.skill} className="border-b border-[var(--border)]">
                        <td className="py-2 font-medium">{skillDelta.skill}</td>
                        <td className="py-2">{skillDelta.classification}</td>
                        <td className="py-2">{formatDelta(skillDelta.calls, 0)}</td>
                        <td className="py-2">{formatDelta(skillDelta.tokens, 0)}</td>
                        <td className="py-2">{formatDelta(skillDelta.averageLatencyMs, 1)}</td>
                        <td className="py-2">{formatDelta(skillDelta.errorCount, 0)}</td>
                        <td className="py-2">
                          {formatPercent(skillDelta.current.policyRate)} (
                          {formatDelta(skillDelta.policyRate, 2)})
                        </td>
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

function StudioFallback() {
  return (
    <Shell>
      <div className="rounded-3xl border border-[var(--border)] bg-white p-8">
        <h1 className="text-2xl font-semibold">Loading Studio...</h1>
        <p className="text-[var(--muted)] mt-2">Preparing replay and comparison workspace.</p>
      </div>
    </Shell>
  );
}

export default function StudioPage() {
  return (
    <Suspense fallback={<StudioFallback />}>
      <StudioContent />
    </Suspense>
  );
}
