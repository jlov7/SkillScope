import { normalizeEvents, parseInput, summarizeEvents, type EventRecord, type Summary } from "./analyze";

const GENAI_USAGE_INPUT = "gen_ai.usage.input_tokens";
const GENAI_USAGE_OUTPUT = "gen_ai.usage.output_tokens";
const SKILL_NAME = "skill.name";
const GENAI_MODEL = "gen_ai.request.model";
const SKILL_FILES = "skill.files";
const SKILL_POLICY = "skill.policy_required";
const SKILL_PROGRESSIVE_LEVEL = "skill.progressive_level";

type Severity = "high" | "medium" | "low" | "info";

type Classification = "regression" | "improvement" | "neutral";

export type ReplayStep = {
  id: string;
  index: number;
  tsRaw?: number | string;
  tsMs: number | null;
  event: string;
  skill: string;
  model: string;
  policyRequired: boolean;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  latencyMs: number | null;
  isError: boolean;
  files: string[];
  progressiveLevel: string;
  attrs: Record<string, unknown>;
};

export type SkillMetrics = {
  skill: string;
  events: number;
  calls: number;
  totalTokens: number;
  avgTokens: number;
  policyRate: number;
  errorCount: number;
  averageLatencyMs: number;
  p95LatencyMs: number;
  latencySamples: number;
};

export type RunMetrics = {
  totalEvents: number;
  totalSkills: number;
  totalCalls: number;
  totalTokens: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  policyRequiredCount: number;
  policyRate: number;
  errorCount: number;
  averageLatencyMs: number;
  p95LatencyMs: number;
  skillMetrics: Record<string, SkillMetrics>;
};

export type RunAnalysis = {
  steps: ReplayStep[];
  summary: Summary;
  metrics: RunMetrics;
};

export type DeltaMetric = {
  baseline: number;
  current: number;
  absolute: number;
  percent: number | null;
};

export type SkillDelta = {
  skill: string;
  baseline: SkillMetrics;
  current: SkillMetrics;
  calls: DeltaMetric;
  tokens: DeltaMetric;
  averageLatencyMs: DeltaMetric;
  errorCount: DeltaMetric;
  policyRate: DeltaMetric;
  classification: Classification;
  score: number;
  reasons: string[];
};

export type Insight = {
  id: string;
  severity: Severity;
  title: string;
  explanation: string;
  recommendation: string;
};

export type RunComparison = {
  baseline: RunAnalysis;
  current: RunAnalysis;
  deltas: {
    totalCalls: DeltaMetric;
    totalTokens: DeltaMetric;
    totalInputTokens: DeltaMetric;
    totalOutputTokens: DeltaMetric;
    policyRate: DeltaMetric;
    errorCount: DeltaMetric;
    averageLatencyMs: DeltaMetric;
    p95LatencyMs: DeltaMetric;
  };
  skillDeltas: SkillDelta[];
  regressions: SkillDelta[];
  improvements: SkillDelta[];
  insights: Insight[];
  summaryText: string;
};

const toNumber = (value: unknown): number => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return 0;
};

const toFiniteNumberOrNull = (value: unknown): number | null => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return null;
};

const coerceTimestampMs = (value: unknown): number | null => {
  if (typeof value === "number" && Number.isFinite(value)) {
    if (value > 1e12) return Math.round(value);
    if (value > 1e9) return Math.round(value * 1000);
    return Math.round(value);
  }
  if (typeof value === "string" && value.trim()) {
    const asNumber = Number(value);
    if (Number.isFinite(asNumber)) return coerceTimestampMs(asNumber);
    const parsedDate = Date.parse(value);
    if (Number.isFinite(parsedDate)) return parsedDate;
  }
  return null;
};

const percentile = (values: number[], p: number): number => {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const rank = Math.max(0, Math.min(sorted.length - 1, Math.ceil(p * sorted.length) - 1));
  return sorted[rank];
};

const average = (values: number[]): number => {
  if (values.length === 0) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
};

const parseFiles = (value: unknown): string[] => {
  if (Array.isArray(value)) {
    return value
      .map((file) => String(file).trim())
      .filter(Boolean);
  }
  if (typeof value === "string") {
    return value
      .split(",")
      .map((file) => file.trim())
      .filter(Boolean);
  }
  return [];
};

const extractLatencyMs = (attrs: Record<string, unknown>): number | null => {
  const keys = [
    "latency_ms",
    "duration_ms",
    "response_ms",
    "gen_ai.response.latency_ms",
    "gen_ai.response.duration_ms",
    "gen_ai.latency_ms",
    "skillscope.latency_ms",
  ];
  for (const key of keys) {
    const value = toFiniteNumberOrNull(attrs[key]);
    if (value !== null && value >= 0) return value;
  }
  return null;
};

const isErrorEvent = (eventName: string, attrs: Record<string, unknown>): boolean => {
  const lowered = eventName.toLowerCase();
  if (
    lowered.includes("error") ||
    lowered.includes("exception") ||
    lowered.includes("fail") ||
    lowered.includes("timeout")
  ) {
    return true;
  }

  const status = String(attrs.status ?? "").toLowerCase();
  if (status === "error" || status === "failed" || status === "timeout") return true;
  if (attrs.success === false) return true;
  return Boolean(attrs.error);
};

const buildDefaultSkillMetrics = (skill: string): SkillMetrics => ({
  skill,
  events: 0,
  calls: 0,
  totalTokens: 0,
  avgTokens: 0,
  policyRate: 0,
  errorCount: 0,
  averageLatencyMs: 0,
  p95LatencyMs: 0,
  latencySamples: 0,
});

const delta = (baseline: number, current: number): DeltaMetric => {
  const absolute = current - baseline;
  if (baseline === 0) {
    if (current === 0) return { baseline, current, absolute, percent: 0 };
    return { baseline, current, absolute, percent: null };
  }
  return {
    baseline,
    current,
    absolute,
    percent: (absolute / baseline) * 100,
  };
};

export const buildReplaySteps = (events: EventRecord[]): ReplayStep[] => {
  const normalized = normalizeEvents(events);
  const mapped = normalized.map((event, originalIndex) => {
    const attrs = event.attrs ?? {};
    const eventName = String(event.event ?? "span");
    const inputTokens = Math.max(0, toNumber(attrs[GENAI_USAGE_INPUT]));
    const outputTokens = Math.max(0, toNumber(attrs[GENAI_USAGE_OUTPUT]));
    const skill = String(attrs[SKILL_NAME] ?? "unknown");
    const tsMs = coerceTimestampMs(event.ts);
    return {
      id: "",
      index: originalIndex,
      tsRaw: event.ts,
      tsMs,
      event: eventName,
      skill,
      model: String(attrs[GENAI_MODEL] ?? ""),
      policyRequired: Boolean(attrs[SKILL_POLICY]),
      inputTokens,
      outputTokens,
      totalTokens: inputTokens + outputTokens,
      latencyMs: extractLatencyMs(attrs),
      isError: isErrorEvent(eventName, attrs),
      files: parseFiles(attrs[SKILL_FILES]),
      progressiveLevel: String(attrs[SKILL_PROGRESSIVE_LEVEL] ?? "referenced"),
      attrs,
    } satisfies ReplayStep;
  });

  const ordered = [...mapped].sort((a, b) => {
    if (a.tsMs === null && b.tsMs === null) return a.index - b.index;
    if (a.tsMs === null) return 1;
    if (b.tsMs === null) return -1;
    if (a.tsMs === b.tsMs) return a.index - b.index;
    return a.tsMs - b.tsMs;
  });

  return ordered.map((step, index) => ({
    ...step,
    id: `step-${index + 1}`,
    index,
  }));
};

export const analyzeRun = (events: EventRecord[]): RunAnalysis => {
  const normalized = normalizeEvents(events);
  const summary = summarizeEvents(normalized);
  const steps = buildReplaySteps(normalized);

  const skillNames = new Set<string>(Object.keys(summary.skills));
  for (const step of steps) skillNames.add(step.skill);

  const skillMetrics: Record<string, SkillMetrics> = {};
  for (const skill of skillNames) {
    skillMetrics[skill] = buildDefaultSkillMetrics(skill);
  }

  for (const step of steps) {
    const entry = skillMetrics[step.skill] ?? buildDefaultSkillMetrics(step.skill);
    entry.events += 1;
    entry.totalTokens += step.totalTokens;
    entry.errorCount += step.isError ? 1 : 0;
    if (step.latencyMs !== null) {
      entry.averageLatencyMs += step.latencyMs;
      entry.latencySamples += 1;
    }
    skillMetrics[step.skill] = entry;
  }

  for (const [skill, metric] of Object.entries(skillMetrics)) {
    const summarySkill = summary.skills[skill];
    const latencies = steps
      .filter((step) => step.skill === skill && step.latencyMs !== null)
      .map((step) => step.latencyMs as number);
    const calls = summarySkill?.calls ?? metric.events;
    const totalTokens = summarySkill?.tokens_total ?? metric.totalTokens;
    metric.calls = calls;
    metric.totalTokens = totalTokens;
    metric.avgTokens = calls > 0 ? totalTokens / calls : 0;
    metric.policyRate = summarySkill?.policy_rate ?? 0;
    metric.averageLatencyMs = metric.latencySamples > 0 ? metric.averageLatencyMs / metric.latencySamples : 0;
    metric.p95LatencyMs = percentile(latencies, 0.95);
  }

  const allLatencies = steps
    .filter((step) => step.latencyMs !== null)
    .map((step) => step.latencyMs as number);
  const totalCalls = Object.values(skillMetrics).reduce((sum, metric) => sum + metric.calls, 0);
  const policyRequiredCount = Math.round(
    Object.values(skillMetrics).reduce((sum, metric) => sum + metric.policyRate * metric.calls, 0)
  );

  const metrics: RunMetrics = {
    totalEvents: summary.total_events,
    totalSkills: summary.total_skills,
    totalCalls,
    totalTokens: summary.total_tokens,
    totalInputTokens: summary.total_input_tokens,
    totalOutputTokens: summary.total_output_tokens,
    policyRequiredCount,
    policyRate: totalCalls > 0 ? policyRequiredCount / totalCalls : 0,
    errorCount: steps.filter((step) => step.isError).length,
    averageLatencyMs: average(allLatencies),
    p95LatencyMs: percentile(allLatencies, 0.95),
    skillMetrics,
  };

  return { steps, summary, metrics };
};

const classifySkillDelta = (item: Omit<SkillDelta, "classification" | "score" | "reasons">): SkillDelta => {
  const reasons: string[] = [];
  let score = 0;

  if (item.baseline.calls > 0 && item.current.calls === 0) {
    reasons.push("Skill missing in current run.");
    score += 1000;
  }
  if (item.errorCount.absolute > 0) {
    reasons.push("Error count increased.");
    score += item.errorCount.absolute * 200;
  }
  if (item.tokens.absolute > 100 && (item.tokens.percent ?? 0) > 25) {
    reasons.push("Token usage increased materially.");
    score += item.tokens.absolute;
  }
  if (item.averageLatencyMs.absolute > 50 && (item.averageLatencyMs.percent ?? 0) > 20) {
    reasons.push("Latency increased materially.");
    score += item.averageLatencyMs.absolute * 2;
  }
  if (item.policyRate.absolute > 0.1) {
    reasons.push("Policy-gated calls increased.");
    score += item.policyRate.absolute * 500;
  }

  if (reasons.length > 0) {
    return { ...item, classification: "regression", score, reasons };
  }

  const improvements: string[] = [];
  let improvementScore = 0;

  if (item.errorCount.absolute < 0) {
    improvements.push("Error count decreased.");
    improvementScore += Math.abs(item.errorCount.absolute) * 200;
  }
  if (item.tokens.absolute < -100 && (item.tokens.percent ?? 0) < -20) {
    improvements.push("Token usage decreased materially.");
    improvementScore += Math.abs(item.tokens.absolute);
  }
  if (item.averageLatencyMs.absolute < -50 && (item.averageLatencyMs.percent ?? 0) < -20) {
    improvements.push("Latency improved materially.");
    improvementScore += Math.abs(item.averageLatencyMs.absolute) * 2;
  }
  if (item.policyRate.absolute < -0.1) {
    improvements.push("Policy-gated calls decreased.");
    improvementScore += Math.abs(item.policyRate.absolute) * 500;
  }

  if (improvements.length > 0) {
    return {
      ...item,
      classification: "improvement",
      score: improvementScore,
      reasons: improvements,
    };
  }

  return { ...item, classification: "neutral", score: 0, reasons: ["No material change detected."] };
};

const buildInsights = (comparison: Omit<RunComparison, "insights" | "summaryText">): Insight[] => {
  const insights: Insight[] = [];
  const missingSkills = comparison.skillDeltas.filter(
    (skillDelta) => skillDelta.baseline.calls > 0 && skillDelta.current.calls === 0
  );
  if (missingSkills.length > 0) {
    insights.push({
      id: "missing-skills",
      severity: "high",
      title: "Missing skills detected",
      explanation: `The current run skipped ${missingSkills.length} skill(s) present in baseline.`,
      recommendation: "Check routing and skill selection logic for dropped execution branches.",
    });
  }

  if (comparison.deltas.errorCount.absolute > 0) {
    insights.push({
      id: "error-spike",
      severity: "high",
      title: "Error rate regression",
      explanation: `Error events increased by ${comparison.deltas.errorCount.absolute}.`,
      recommendation: "Inspect failing steps in replay and validate tool/model boundary conditions.",
    });
  }

  if (comparison.deltas.totalTokens.absolute > 200 && (comparison.deltas.totalTokens.percent ?? 0) > 25) {
    insights.push({
      id: "token-growth",
      severity: "medium",
      title: "Token growth regression",
      explanation: `Total tokens rose by ${comparison.deltas.totalTokens.absolute} (${(comparison.deltas.totalTokens.percent ?? 0).toFixed(1)}%).`,
      recommendation: "Review prompt size and verbose tool responses in the highest-growth skills.",
    });
  }

  if (comparison.deltas.p95LatencyMs.absolute > 75 && (comparison.deltas.p95LatencyMs.percent ?? 0) > 20) {
    insights.push({
      id: "latency-growth",
      severity: "medium",
      title: "Latency regression",
      explanation: `p95 latency increased by ${comparison.deltas.p95LatencyMs.absolute.toFixed(1)}ms.`,
      recommendation: "Investigate slower models/tools and high-latency steps in timeline replay.",
    });
  }

  if (comparison.deltas.policyRate.absolute > 0.1) {
    insights.push({
      id: "policy-growth",
      severity: "low",
      title: "Policy gate increase",
      explanation: `Policy-gated call rate increased by ${(comparison.deltas.policyRate.absolute * 100).toFixed(1)} percentage points.`,
      recommendation: "Confirm whether stricter approvals are expected for this scenario.",
    });
  }

  if (insights.length === 0) {
    insights.push({
      id: "stable",
      severity: "info",
      title: "No major regressions detected",
      explanation: "Baseline and current runs are broadly stable.",
      recommendation: "Continue monitoring and use replay to inspect any subtle behavior differences.",
    });
  }

  return insights;
};

export const compareRuns = (baselineEvents: EventRecord[], currentEvents: EventRecord[]): RunComparison => {
  const baseline = analyzeRun(baselineEvents);
  const current = analyzeRun(currentEvents);

  const deltas = {
    totalCalls: delta(baseline.metrics.totalCalls, current.metrics.totalCalls),
    totalTokens: delta(baseline.metrics.totalTokens, current.metrics.totalTokens),
    totalInputTokens: delta(baseline.metrics.totalInputTokens, current.metrics.totalInputTokens),
    totalOutputTokens: delta(baseline.metrics.totalOutputTokens, current.metrics.totalOutputTokens),
    policyRate: delta(baseline.metrics.policyRate, current.metrics.policyRate),
    errorCount: delta(baseline.metrics.errorCount, current.metrics.errorCount),
    averageLatencyMs: delta(baseline.metrics.averageLatencyMs, current.metrics.averageLatencyMs),
    p95LatencyMs: delta(baseline.metrics.p95LatencyMs, current.metrics.p95LatencyMs),
  };

  const skillNames = new Set<string>([
    ...Object.keys(baseline.metrics.skillMetrics),
    ...Object.keys(current.metrics.skillMetrics),
  ]);

  const skillDeltas: SkillDelta[] = [];
  for (const skill of skillNames) {
    const baselineSkill = baseline.metrics.skillMetrics[skill] ?? buildDefaultSkillMetrics(skill);
    const currentSkill = current.metrics.skillMetrics[skill] ?? buildDefaultSkillMetrics(skill);
    skillDeltas.push(
      classifySkillDelta({
        skill,
        baseline: baselineSkill,
        current: currentSkill,
        calls: delta(baselineSkill.calls, currentSkill.calls),
        tokens: delta(baselineSkill.totalTokens, currentSkill.totalTokens),
        averageLatencyMs: delta(baselineSkill.averageLatencyMs, currentSkill.averageLatencyMs),
        errorCount: delta(baselineSkill.errorCount, currentSkill.errorCount),
        policyRate: delta(baselineSkill.policyRate, currentSkill.policyRate),
      })
    );
  }

  skillDeltas.sort((a, b) => {
    if (a.classification !== b.classification) {
      const rank: Record<Classification, number> = { regression: 0, neutral: 1, improvement: 2 };
      return rank[a.classification] - rank[b.classification];
    }
    return b.score - a.score;
  });

  const regressions = skillDeltas.filter((skillDelta) => skillDelta.classification === "regression");
  const improvements = skillDeltas.filter((skillDelta) => skillDelta.classification === "improvement");

  const baseComparison = {
    baseline,
    current,
    deltas,
    skillDeltas,
    regressions,
    improvements,
  };
  const insights = buildInsights(baseComparison);
  const topInsight = insights[0];
  const summaryText = `Current run vs baseline: ${topInsight.title}. Calls ${deltas.totalCalls.current} vs ${deltas.totalCalls.baseline}, tokens ${deltas.totalTokens.current} vs ${deltas.totalTokens.baseline}.`;

  return {
    ...baseComparison,
    insights,
    summaryText,
  };
};

export const compareRunContents = (
  baselineContent: string,
  currentContent: string
): RunComparison => {
  const baseline = parseInput(baselineContent, "auto");
  const current = parseInput(currentContent, "auto");
  return compareRuns(baseline, current);
};
