# Release-ready v1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship a production-quality v1 with a minimal web UI, client-side analysis, onboarding/help, and complete quality gates.

**Architecture:** Add a static Next.js web app (`web/`) that performs in-browser parsing/analysis of SkillScope event data, reusing CLI semantics. Keep Python CLI intact; augment docs and CI to validate both stacks.

**Tech Stack:** Python (uv, pytest, ruff, mypy), Next.js + React + TypeScript + Tailwind, Vitest, Playwright, pnpm, Vercel static deploy.

______________________________________________________________________

### Task 1: Scaffold Web UI (Next.js + Tailwind)

**Files:**

- Create: `web/` (Next.js app)
- Modify: `web/next.config.js`
- Modify: `web/package.json`
- Modify: `web/src/app/layout.tsx`
- Modify: `web/src/app/globals.css`

**Step 1: Create app scaffold**

Run:

```bash
pnpm create next-app@latest web --ts --tailwind --eslint --app --src-dir --import-alias "@/*"
```

Expected: Next.js app created under `web/` with `src/app` layout.

**Step 2: Configure static export**

Edit `web/next.config.js` to:

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
};

module.exports = nextConfig;
```

**Step 3: Define base layout and fonts**

Update `web/src/app/layout.tsx`:

```tsx
import './globals.css';
import type { Metadata } from 'next';
import { Space_Grotesk, IBM_Plex_Sans } from 'next/font/google';

const space = Space_Grotesk({ subsets: ['latin'], variable: '--font-display' });
const ibm = IBM_Plex_Sans({ subsets: ['latin'], weight: ['400', '500', '600'], variable: '--font-body' });

export const metadata: Metadata = {
  title: 'SkillScope Research UI',
  description: 'Research-only SkillScope UI with client-side analysis.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${space.variable} ${ibm.variable} antialiased`}>{children}</body>
    </html>
  );
}
```

**Step 4: Establish global styles**

Replace `web/src/app/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg: #f6f4ef;
  --ink: #151515;
  --muted: #6a6a6a;
  --accent: #0b6bcb;
  --accent-2: #f05d23;
  --panel: #ffffff;
  --border: #e4dfd8;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: var(--font-body), system-ui, sans-serif;
  background: radial-gradient(circle at top, #fff7ec, var(--bg));
  color: var(--ink);
}

h1, h2, h3 {
  font-family: var(--font-display), system-ui, sans-serif;
}

:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
```

**Step 5: Verify web lint**

Run:

```bash
cd web
pnpm lint
```

Expected: lint passes.

**Step 6: Commit**

```bash
git add web

git commit -m "feat: scaffold web ui" -m "Introduce Next.js app scaffold for the v1 UI." -m "" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

______________________________________________________________________

### Task 2: Implement Client-side Analysis Library (TDD)

**Files:**

- Create: `web/src/lib/analyze.ts`
- Create: `web/src/lib/analyze.test.ts`
- Modify: `web/package.json`
- Create: `web/vitest.config.ts`

**Step 1: Write failing tests**

Create `web/src/lib/analyze.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import { parseInput, summarizeEvents } from './analyze';

const demoJsonl = `{"event":"end","attrs":{"skill.name":"Brand Voice","gen_ai.usage.input_tokens":10,"gen_ai.usage.output_tokens":5}}\n`;

describe('parseInput', () => {
  it('parses JSONL into events', () => {
    const events = parseInput(demoJsonl, 'jsonl');
    expect(events).toHaveLength(1);
    expect(events[0].attrs['skill.name']).toBe('Brand Voice');
  });
});

describe('summarizeEvents', () => {
  it('summarizes tokens and calls', () => {
    const events = parseInput(demoJsonl, 'jsonl');
    const summary = summarizeEvents(events);
    expect(summary.total_events).toBe(1);
    expect(summary.skills['Brand Voice'].calls).toBe(1);
    expect(summary.total_tokens).toBe(15);
  });
});
```

**Step 2: Run tests (expect failure)**

```bash
cd web
pnpm test
```

Expected: FAIL (module not found).

**Step 3: Implement minimal analysis logic**

Create `web/src/lib/analyze.ts`:

```ts
export type EventRecord = {
  ts?: number | string;
  event?: string;
  attrs: Record<string, any>;
  metadata?: Record<string, any>;
};

const GENAI_USAGE_INPUT = 'gen_ai.usage.input_tokens';
const GENAI_USAGE_OUTPUT = 'gen_ai.usage.output_tokens';
const GENAI_TOKEN_USAGE = 'gen_ai.client.token.usage';
const GENAI_MODEL = 'gen_ai.request.model';
const SKILL_NAME = 'skill.name';

const safeInt = (value: any): number | null => {
  if (value === null || value === undefined || value === '') return null;
  const parsed = Number.parseInt(String(value), 10);
  return Number.isNaN(parsed) ? null : parsed;
};

export type InputFormat = 'auto' | 'json' | 'jsonl' | 'anthropic';

const detectFormat = (content: string): InputFormat => {
  const snippet = content.trim();
  if (!snippet) return 'jsonl';
  if (snippet.startsWith('{')) {
    try {
      const obj = JSON.parse(content);
      if (obj && typeof obj === 'object' && 'messages' in obj) return 'anthropic';
      if (Array.isArray(obj)) return 'json';
      return 'json';
    } catch {
      return 'jsonl';
    }
  }
  return 'jsonl';
};

const parseJson = (content: string): EventRecord[] => {
  const data = JSON.parse(content);
  if (Array.isArray(data)) return data as EventRecord[];
  if (data && typeof data === 'object') return [data as EventRecord];
  throw new Error('Unsupported JSON payload');
};

const parseJsonl = (content: string): EventRecord[] => {
  return content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
};

const anthropicToEvents = (payload: any): EventRecord[] => {
  const baseAttrs = Object.fromEntries(
    Object.entries(payload?.metadata ?? {}).filter(([key]) => key.startsWith('skill.'))
  );
  const events: EventRecord[] = [];
  for (const message of payload?.messages ?? []) {
    const metadata = message?.metadata ?? {};
    const perMessage = {
      ...baseAttrs,
      ...Object.fromEntries(Object.entries(metadata).filter(([key]) => key.startsWith('skill.'))),
    };
    events.push({
      ts: message?.ts ?? payload?.ts,
      event: `message.${message?.role ?? 'unknown'}`,
      attrs: perMessage,
      metadata,
    });
  }
  const usage = payload?.usage;
  if (usage && events.length > 0) {
    const inputTokens = Number(usage?.input_tokens ?? 0);
    const outputTokens = Number(usage?.output_tokens ?? 0);
    events[events.length - 1].attrs[GENAI_USAGE_INPUT] = inputTokens;
    events[events.length - 1].attrs[GENAI_USAGE_OUTPUT] = outputTokens;
    events[events.length - 1].attrs[GENAI_TOKEN_USAGE] = inputTokens + outputTokens;
  }
  return events;
};

export const parseInput = (content: string, format: InputFormat = 'auto'): EventRecord[] => {
  const detected = format === 'auto' ? detectFormat(content) : format;
  if (detected === 'anthropic') return anthropicToEvents(JSON.parse(content));
  if (detected === 'jsonl') return parseJsonl(content);
  return parseJson(content);
};

export const normalizeEvents = (events: EventRecord[]): EventRecord[] => {
  return events.map((event) => {
    const attrs = { ...(event.attrs ?? {}) };
    const metadata = event.metadata ?? {};
    for (const [key, value] of Object.entries(metadata)) {
      if (key.startsWith('skill.')) attrs[key] = value;
    }
    const inputTokens = safeInt(event?.input_tokens ?? attrs[GENAI_USAGE_INPUT]);
    const outputTokens = safeInt(event?.output_tokens ?? attrs[GENAI_USAGE_OUTPUT]);
    const legacyTokens = safeInt(event?.token_usage ?? attrs[GENAI_TOKEN_USAGE]);

    if (!attrs[SKILL_NAME]) {
      attrs[SKILL_NAME] = attrs['skill.name'] ?? event?.skill ?? 'unknown';
      attrs['skill.version'] = attrs['skill.version'] ?? event?.version ?? '';
      attrs['skill.description'] = attrs['skill.description'] ?? event?.description ?? '';
      attrs['skill.files'] = attrs['skill.files'] ?? (event?.files ? String(event.files) : '');
      attrs['skill.policy_required'] = attrs['skill.policy_required'] ?? Boolean(event?.policy_required ?? false);
      attrs['skill.progressive_level'] =
        attrs['skill.progressive_level'] ?? event?.progressive_level ?? 'referenced';
      attrs[GENAI_MODEL] = attrs[GENAI_MODEL] ?? event?.model ?? '';
    }
    if (inputTokens !== null) attrs[GENAI_USAGE_INPUT] = inputTokens;
    if (outputTokens !== null) attrs[GENAI_USAGE_OUTPUT] = outputTokens;
    if (legacyTokens !== null) attrs[GENAI_TOKEN_USAGE] = legacyTokens;

    return {
      ts: event.ts,
      event: event.event ?? 'span',
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
  skills: Record<string, any>;
};

export const summarizeEvents = (events: EventRecord[]): Summary => {
  const totals = {
    total_events: 0,
    total_tokens: 0,
    total_input_tokens: 0,
    total_output_tokens: 0,
  };
  const perSkill: Record<string, any> = {};

  for (const event of events) {
    totals.total_events += 1;
    const attrs = event.attrs ?? {};
    const skill = attrs[SKILL_NAME] ?? attrs['skill'] ?? 'unknown';
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

    const eventName = String(event.event ?? '');
    if (eventName.startsWith('end') || eventName === 'anthropic_call' || eventName === 'span') {
      entry.completions += 1;
    }
    if (attrs['skill.policy_required']) entry.policy_required += 1;
    if (attrs['skill.files']) {
      String(attrs['skill.files'])
        .split(',')
        .map((file) => file.trim())
        .filter(Boolean)
        .forEach((file) => entry.files.add(file));
    }
    if (attrs['skill.progressive_level']) entry.progressive_levels.add(String(attrs['skill.progressive_level']));

    if (eventName !== 'start') {
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

  const skills: Record<string, any> = {};
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
```

**Step 4: Add Vitest config and scripts**

Create `web/vitest.config.ts`:

```ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
  },
});
```

Update `web/package.json` scripts:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

**Step 5: Run tests (expect pass)**

```bash
cd web
pnpm test
```

Expected: PASS.

**Step 6: Commit**

```bash
git add web/src/lib web/vitest.config.ts web/package.json

git commit -m "feat: add client-side analysis engine" -m "Implement event parsing and summaries for in-browser analysis." -m "" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

______________________________________________________________________

### Task 3: Build Core UI Pages and Onboarding

**Files:**

- Create: `web/src/app/page.tsx`
- Create: `web/src/app/analyze/page.tsx`
- Create: `web/src/app/demo/page.tsx`
- Create: `web/src/app/help/page.tsx`
- Create: `web/src/components/*`

**Step 1: Create shared UI components**

Create `web/src/components/Shell.tsx`:

```tsx
import Link from 'next/link';

export default function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="px-6 py-5 border-b border-[var(--border)] bg-[var(--panel)]">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-[var(--accent)] text-white flex items-center justify-center font-semibold">S</div>
            <div>
              <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">SkillScope</p>
              <p className="text-lg font-semibold">Research UI</p>
            </div>
          </div>
          <nav className="flex gap-4 text-sm">
            <Link href="/" className="hover:underline">Home</Link>
            <Link href="/analyze" className="hover:underline">Analyze</Link>
            <Link href="/demo" className="hover:underline">Demo</Link>
            <Link href="/help" className="hover:underline">Help</Link>
          </nav>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-6 py-10">{children}</main>
      <footer className="px-6 py-6 border-t border-[var(--border)] text-sm text-[var(--muted)]">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-2">
          <span>SkillScope is research-only software. Use at your own risk.</span>
          <span>Client-side analysis. No data leaves your browser.</span>
        </div>
      </footer>
    </div>
  );
}
```

Create `web/src/components/EmptyState.tsx`:

```tsx
export default function EmptyState({ title, body, cta }: { title: string; body: string; cta?: React.ReactNode }) {
  return (
    <div className="rounded-3xl border border-dashed border-[var(--border)] p-8 bg-white">
      <h2 className="text-2xl font-semibold mb-2">{title}</h2>
      <p className="text-[var(--muted)] mb-4">{body}</p>
      {cta}
    </div>
  );
}
```

**Step 2: Home page with onboarding**

Create `web/src/app/page.tsx`:

```tsx
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Shell from '@/components/Shell';

export default function HomePage() {
  const [seen, setSeen] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem('skillscope_seen_onboarding');
    if (stored === '1') setSeen(true);
  }, []);

  const markSeen = () => {
    window.localStorage.setItem('skillscope_seen_onboarding', '1');
    setSeen(true);
  };

  return (
    <Shell>
      <section className="grid gap-8 lg:grid-cols-2">
        <div className="space-y-5">
          <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">Research-only preview</p>
          <h1 className="text-4xl font-semibold">See what your Skills are doing in minutes.</h1>
          <p className="text-lg text-[var(--muted)]">
            SkillScope adds observability to Agent Skills. This UI runs entirely in your browser—no uploads, no servers.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/analyze" className="px-4 py-2 rounded-full bg-[var(--accent)] text-white">Analyze data</Link>
            <Link href="/demo" className="px-4 py-2 rounded-full border border-[var(--border)]">Load demo</Link>
          </div>
        </div>
        <div className="rounded-3xl bg-white border border-[var(--border)] p-6 shadow-sm">
          <h2 className="text-2xl font-semibold mb-3">First run checklist</h2>
          <ol className="space-y-2 text-[var(--muted)]">
            <li>1. Export events via `skillscope emit` or `skillscope ingest`.</li>
            <li>2. Upload JSON/JSONL on the Analyze page.</li>
            <li>3. Share summaries with your team.</li>
          </ol>
          {!seen && (
            <button onClick={markSeen} className="mt-5 px-4 py-2 rounded-full bg-[var(--accent-2)] text-white">
              Mark onboarding complete
            </button>
          )}
        </div>
      </section>
    </Shell>
  );
}
```

**Step 3: Analyze page with upload and empty states**

Create `web/src/app/analyze/page.tsx`:

```tsx
'use client';

import { useMemo, useState } from 'react';
import Shell from '@/components/Shell';
import EmptyState from '@/components/EmptyState';
import { normalizeEvents, parseInput, summarizeEvents } from '@/lib/analyze';

const MAX_BYTES = 8 * 1024 * 1024;

export default function AnalyzePage() {
  const [content, setContent] = useState('');
  const [error, setError] = useState<string | null>(null);

  const summary = useMemo(() => {
    if (!content) return null;
    try {
      const parsed = parseInput(content, 'auto');
      const normalized = normalizeEvents(parsed);
      return summarizeEvents(normalized);
    } catch (err) {
      setError((err as Error).message);
      return null;
    }
  }, [content]);

  const handleFile = async (file: File | null) => {
    if (!file) return;
    if (file.size > MAX_BYTES) {
      setError('File too large. Please upload 8MB or smaller.');
      return;
    }
    setError(null);
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
        {error && <div role="alert" className="text-red-600">{error}</div>}
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
```

**Step 4: Demo and Help pages**

Create `web/src/app/demo/page.tsx`:

```tsx
'use client';

import { useMemo } from 'react';
import Shell from '@/components/Shell';
import { normalizeEvents, parseInput, summarizeEvents } from '@/lib/analyze';
import demoData from '@/lib/demo-data';

export default function DemoPage() {
  const summary = useMemo(() => summarizeEvents(normalizeEvents(parseInput(demoData, 'jsonl'))), []);

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
```

Create `web/src/app/help/page.tsx`:

```tsx
import Shell from '@/components/Shell';

export default function HelpPage() {
  return (
    <Shell>
      <div className="space-y-4">
        <h1 className="text-3xl font-semibold">Help</h1>
        <p className="text-[var(--muted)]">
          This UI analyzes SkillScope JSON/JSONL locally in your browser. For CLI workflows, see the README.
        </p>
        <ul className="list-disc pl-5 text-[var(--muted)]">
          <li>Use `skillscope emit --demo` to generate sample events.</li>
          <li>Upload JSON/JSONL files on the Analyze page.</li>
          <li>Use the Demo page for a guided preview.</li>
        </ul>
      </div>
    </Shell>
  );
}
```

Create `web/src/lib/demo-data.ts`:

```ts
const demoData = `{"event":"start","attrs":{"skill.name":"Brand Voice","gen_ai.usage.input_tokens":0,"gen_ai.usage.output_tokens":0}}\n{"event":"end","attrs":{"skill.name":"Brand Voice","gen_ai.usage.input_tokens":120,"gen_ai.usage.output_tokens":80}}`;

export default demoData;
```

**Step 5: Run dev build**

```bash
cd web
pnpm build
```

Expected: build succeeds.

**Step 6: Commit**

```bash
git add web/src/app web/src/components web/src/lib/demo-data.ts

git commit -m "feat: add core web ui" -m "Implement onboarding, analyze, demo, and help pages." -m "" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

______________________________________________________________________

### Task 4: Add UI Tests for Key Flows

**Files:**

- Create: `web/playwright.config.ts`
- Create: `web/tests/home.spec.ts`
- Modify: `web/package.json`

**Step 1: Add Playwright config**

Create `web/playwright.config.ts`:

```ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  webServer: {
    command: 'pnpm dev',
    port: 3000,
    reuseExistingServer: !process.env.CI,
  },
  use: { headless: true },
});
```

**Step 2: Add smoke tests**

Create `web/tests/home.spec.ts`:

```ts
import { test, expect } from '@playwright/test';

test('home loads', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /SkillScope/i })).toBeVisible();
});

test('demo loads', async ({ page }) => {
  await page.goto('/demo');
  await expect(page.getByText('Sample dataset')).toBeVisible();
});
```

**Step 3: Add Playwright script**

Update `web/package.json` scripts:

```json
{
  "scripts": {
    "e2e": "playwright test"
  }
}
```

**Step 4: Install Playwright**

```bash
cd web
pnpm add -D @playwright/test
pnpm exec playwright install
```

**Step 5: Run tests**

```bash
pnpm e2e
```

Expected: PASS.

**Step 6: Commit**

```bash
git add web/playwright.config.ts web/tests web/package.json

git commit -m "test: add web ui smoke tests" -m "Cover onboarding and demo flows with Playwright." -m "" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

______________________________________________________________________

### Task 5: Update Docs and README for Web UI

**Files:**

- Modify: `README.md`
- Create: `docs/help.md`
- Modify: `docs/index.md`

**Step 1: Add docs/help page**

Create `docs/help.md`:

```md
# SkillScope Help

SkillScope is research-only software. The web UI runs locally in your browser and does not upload data.

## Web UI

1. `pnpm install` in `web/`
2. `pnpm dev`
3. Visit `http://localhost:3000`

## CLI

Use `skillscope emit --demo` or `skillscope ingest` to generate events, then upload JSON/JSONL to the web UI.
```

**Step 2: Update docs index**

Add to `docs/index.md`:

```md
- Web UI quickstart: [docs/help.md](help.md)
```

**Step 3: Update README**

Add a new section “Web UI” with setup, run, test, build, and Vercel deploy notes. Include env vars (none required) and note static export.

**Step 4: Commit**

```bash
git add README.md docs/help.md docs/index.md

git commit -m "docs: add web ui help" -m "Document local usage and deployment guidance for the UI." -m "" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

______________________________________________________________________

### Task 6: Update CI for Web + Python

**Files:**

- Modify: `.github/workflows/ci.yml`

**Step 1: Add web jobs**

Add steps to install pnpm, run `pnpm install`, `pnpm lint`, `pnpm test`, `pnpm build`, and `pnpm e2e`.

**Step 2: Ensure Python uses dev extras**

Update CI to run `uv sync --all-extras` before `pytest`.

**Step 3: Commit**

```bash
git add .github/workflows/ci.yml

git commit -m "ci: add web ui quality gates" -m "Run web lint/test/build alongside Python checks." -m "" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

______________________________________________________________________

### Task 7: Release Verification

**Files:**

- Modify: `PLANS.md`
- Modify: `.codex/PLANS.md`
- Modify: `RELEASE_CHECKLIST.md`

**Step 1: Run verification**

```bash
uv sync --all-extras
uv run pytest
uv run ruff check .
uv run mypy skillscope
cd web
pnpm install
pnpm lint
pnpm test
pnpm build
pnpm e2e
```

**Step 2: Update checklist and plans**

Check off completed items in `RELEASE_CHECKLIST.md` and update progress + verification evidence in `PLANS.md` and `.codex/PLANS.md`.

**Step 3: Commit**

```bash
git add PLANS.md .codex/PLANS.md RELEASE_CHECKLIST.md

git commit -m "chore: finalize v1 release checks" -m "Capture verification evidence and checklist status." -m "" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```
