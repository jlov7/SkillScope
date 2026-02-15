export type EventRecord = {
  ts?: number | string;
  event?: string;
  attrs: Record<string, unknown>;
  metadata?: Record<string, unknown>;
};

const GENAI_USAGE_INPUT = "gen_ai.usage.input_tokens";
const GENAI_USAGE_OUTPUT = "gen_ai.usage.output_tokens";
const GENAI_TOKEN_USAGE = "gen_ai.client.token.usage";
const GENAI_MODEL = "gen_ai.request.model";
const SKILL_NAME = "skill.name";

type InputFormat = "auto" | "json" | "jsonl" | "anthropic";

const safeInt = (value: unknown): number | null => {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number.parseInt(String(value), 10);
  return Number.isNaN(parsed) ? null : parsed;
};

const detectFormat = (content: string): InputFormat => {
  const snippet = content.trim();
  if (!snippet) return "jsonl";
  if (snippet.startsWith("{")) {
    try {
      const obj = JSON.parse(content);
      if (obj && typeof obj === "object" && "messages" in obj) return "anthropic";
      if (Array.isArray(obj)) return "json";
      return "json";
    } catch {
      return "jsonl";
    }
  }
  return "jsonl";
};

const parseJson = (content: string): EventRecord[] => {
  const data = JSON.parse(content);
  if (Array.isArray(data)) return data as EventRecord[];
  if (data && typeof data === "object") return [data as EventRecord];
  throw new Error("Unsupported JSON payload");
};

const parseJsonl = (content: string): EventRecord[] => {
  return content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
};

const anthropicToEvents = (payload: Record<string, unknown>): EventRecord[] => {
  const metadata = (payload.metadata ?? {}) as Record<string, unknown>;
  const baseAttrs = Object.fromEntries(
    Object.entries(metadata).filter(([key]) => key.startsWith("skill."))
  );
  const events: EventRecord[] = [];
  const messages = (payload.messages ?? []) as Array<Record<string, unknown>>;
  for (const message of messages) {
    const messageMetadata = (message.metadata ?? {}) as Record<string, unknown>;
    const perMessage = {
      ...baseAttrs,
      ...Object.fromEntries(
        Object.entries(messageMetadata).filter(([key]) => key.startsWith("skill."))
      ),
    };
    events.push({
      ts: (message.ts as number | string) ?? (payload.ts as number | string),
      event: `message.${message.role ?? "unknown"}`,
      attrs: perMessage,
      metadata: messageMetadata,
    });
  }
  const usage = (payload.usage ?? {}) as Record<string, unknown>;
  if (Object.keys(usage).length > 0 && events.length > 0) {
    const inputTokens = Number(usage.input_tokens ?? 0);
    const outputTokens = Number(usage.output_tokens ?? 0);
    const lastAttrs = events[events.length - 1].attrs;
    lastAttrs[GENAI_USAGE_INPUT] = inputTokens;
    lastAttrs[GENAI_USAGE_OUTPUT] = outputTokens;
    lastAttrs[GENAI_TOKEN_USAGE] = inputTokens + outputTokens;
  }
  return events;
};

export const parseInput = (content: string, format: InputFormat = "auto"): EventRecord[] => {
  const detected = format === "auto" ? detectFormat(content) : format;
  if (detected === "anthropic") return anthropicToEvents(JSON.parse(content));
  if (detected === "jsonl") return parseJsonl(content);
  return parseJson(content);
};

export const normalizeEvents = (events: EventRecord[]): EventRecord[] => {
  return events.map((event) => {
    const attrs: Record<string, unknown> = { ...(event.attrs ?? {}) };
    const metadata = event.metadata ?? {};

    for (const [key, value] of Object.entries(metadata)) {
      if (key.startsWith("skill.")) attrs[key] = value;
    }

    const inputTokens = safeInt((event as Record<string, unknown>).input_tokens ?? attrs[GENAI_USAGE_INPUT]);
    const outputTokens = safeInt((event as Record<string, unknown>).output_tokens ?? attrs[GENAI_USAGE_OUTPUT]);
    const legacyTokens = safeInt((event as Record<string, unknown>).token_usage ?? attrs[GENAI_TOKEN_USAGE]);

    if (!attrs[SKILL_NAME]) {
      attrs[SKILL_NAME] = (attrs["skill.name"] as string) ?? (event as Record<string, unknown>).skill ?? "unknown";
      attrs["skill.version"] =
        (attrs["skill.version"] as string) ?? ((event as Record<string, unknown>).version as string) ?? "";
      attrs["skill.description"] =
        (attrs["skill.description"] as string) ?? ((event as Record<string, unknown>).description as string) ?? "";
      attrs["skill.files"] =
        (attrs["skill.files"] as string) ?? ((event as Record<string, unknown>).files as string) ?? "";
      attrs["skill.policy_required"] =
        attrs["skill.policy_required"] ?? Boolean((event as Record<string, unknown>).policy_required ?? false);
      attrs["skill.progressive_level"] =
        (attrs["skill.progressive_level"] as string) ??
        ((event as Record<string, unknown>).progressive_level as string) ??
        "referenced";
      attrs[GENAI_MODEL] = (attrs[GENAI_MODEL] as string) ?? ((event as Record<string, unknown>).model as string) ?? "";
    }

    if (inputTokens !== null) attrs[GENAI_USAGE_INPUT] = inputTokens;
    if (outputTokens !== null) attrs[GENAI_USAGE_OUTPUT] = outputTokens;
    if (legacyTokens !== null) attrs[GENAI_TOKEN_USAGE] = legacyTokens;

    return {
      ts: event.ts,
      event: event.event ?? "span",
      attrs,
      metadata,
    };
  });
};

export type Summary = {
  total_events: number;
  total_tokens: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_skills: number;
  skills: Record<string, {
    events: number;
    calls: number;
    policy_required: number;
    policy_rate: number;
    tokens_total: number;
    tokens_input_total: number;
    tokens_output_total: number;
    tokens_average: number;
    tokens_input_average: number;
    tokens_output_average: number;
    files: string[];
    models: string[];
    progressive_levels: string[];
  }>;
};

export const summarizeEvents = (events: EventRecord[]): Summary => {
  const totals = {
    total_events: 0,
    total_tokens: 0,
    total_input_tokens: 0,
    total_output_tokens: 0,
  };
  const perSkill: Record<string, {
    events: number;
    completions: number;
    policy_required: number;
    tokens: number;
    token_samples: number;
    tokens_input: number;
    tokens_output: number;
    tokens_input_samples: number;
    tokens_output_samples: number;
    files: Set<string>;
    models: Set<string>;
    progressive_levels: Set<string>;
  }> = {};

  for (const event of events) {
    totals.total_events += 1;
    const attrs = event.attrs ?? {};
    const skill = (attrs[SKILL_NAME] as string) ?? (attrs["skill"] as string) ?? "unknown";
    const entry = perSkill[skill] ?? {
      events: 0,
      completions: 0,
      policy_required: 0,
      tokens: 0,
      token_samples: 0,
      tokens_input: 0,
      tokens_output: 0,
      tokens_input_samples: 0,
      tokens_output_samples: 0,
      files: new Set<string>(),
      models: new Set<string>(),
      progressive_levels: new Set<string>(),
    };
    entry.events += 1;

    const eventName = String(event.event ?? "");
    if (eventName.startsWith("end") || eventName === "anthropic_call" || eventName === "span") {
      entry.completions += 1;
    }
    if (attrs["skill.policy_required"]) entry.policy_required += 1;
    if (attrs["skill.files"]) {
      String(attrs["skill.files"])
        .split(",")
        .map((file) => file.trim())
        .filter(Boolean)
        .forEach((file) => entry.files.add(file));
    }
    if (attrs["skill.progressive_level"]) entry.progressive_levels.add(String(attrs["skill.progressive_level"]));

    if (eventName !== "start") {
      const inputPresent = GENAI_USAGE_INPUT in attrs;
      const outputPresent = GENAI_USAGE_OUTPUT in attrs;
      let inputTokens = 0;
      let outputTokens = 0;
      if (inputPresent) {
        inputTokens = safeInt(attrs[GENAI_USAGE_INPUT]) ?? 0;
        entry.tokens_input += inputTokens;
        entry.tokens_input_samples += 1;
        totals.total_input_tokens += inputTokens;
      }
      if (outputPresent) {
        outputTokens = safeInt(attrs[GENAI_USAGE_OUTPUT]) ?? 0;
        entry.tokens_output += outputTokens;
        entry.tokens_output_samples += 1;
        totals.total_output_tokens += outputTokens;
      }
      if (inputPresent || outputPresent) {
        const totalTokens = (inputPresent ? inputTokens : 0) + (outputPresent ? outputTokens : 0);
        entry.tokens += totalTokens;
        entry.token_samples += 1;
        totals.total_tokens += totalTokens;
      } else if (attrs[GENAI_TOKEN_USAGE] !== undefined) {
        const legacyTokens = safeInt(attrs[GENAI_TOKEN_USAGE]) ?? 0;
        entry.tokens += legacyTokens;
        entry.token_samples += 1;
        totals.total_tokens += legacyTokens;
      }
    }

    if (attrs[GENAI_MODEL]) entry.models.add(String(attrs[GENAI_MODEL]));
    perSkill[skill] = entry;
  }

  const skills: Summary["skills"] = {};
  for (const [skill, data] of Object.entries(perSkill)) {
    const calls = data.completions || data.events;
    const policyRequired = Math.min(data.policy_required, calls);
    const avgTokens = data.token_samples ? data.tokens / data.token_samples : 0;
    const avgInput = data.tokens_input_samples ? data.tokens_input / data.tokens_input_samples : 0;
    const avgOutput = data.tokens_output_samples ? data.tokens_output / data.tokens_output_samples : 0;
    const policyRate = calls ? policyRequired / calls : 0;
    skills[skill] = {
      events: data.events,
      calls,
      policy_required: policyRequired,
      policy_rate: policyRate,
      tokens_total: data.tokens,
      tokens_input_total: data.tokens_input,
      tokens_output_total: data.tokens_output,
      tokens_average: avgTokens,
      tokens_input_average: avgInput,
      tokens_output_average: avgOutput,
      files: Array.from(data.files).sort().slice(0, 10),
      models: Array.from(data.models).sort(),
      progressive_levels: Array.from(data.progressive_levels).sort(),
    };
  }

  return {
    ...totals,
    total_skills: Object.keys(skills).length,
    skills,
  };
};

export type { InputFormat };
