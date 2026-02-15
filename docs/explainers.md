# Explainers

Use this page to explain SkillScope to different audiences without changing the core narrative.

## One-liner

SkillScope compares baseline and current agent runs, replays behavior changes, and surfaces likely root causes with actionable next steps.

## Non-technical explainer

### What it does

- Shows where an agent workflow changed between “good” and “current.”
- Highlights likely reasons for regressions in plain language.
- Gives teams a fast path from issue detection to next action.

### Why it was built

- Agent behavior can drift quietly.
- Raw logs are too noisy for quick stakeholder understanding.
- Teams need a clear “what changed and what to do next” workflow.

### Why this matters

- Faster triage.
- Better communication across product, engineering, and operations.
- More confidence when demonstrating AI systems externally.

## Technical explainer

### How it works

1. Parse and normalize JSON/JSONL/NDJSON/Anthropic payloads.
1. Build deterministic replay timeline with timestamp coercion.
1. Compute run-level and skill-level metrics (calls, tokens, errors, latency, policy rate).
1. Diff baseline vs current and classify material changes.
1. Generate rule-based root-cause insights and recommendations.

### Architecture choices

- Client-side analysis by default (privacy and low operational overhead).
- Static export deployment (simple distribution and low risk).
- OpenTelemetry/Agent Skills aligned attributes for interoperability.

### Demo recommendation

Use <https://skillscope-amber.vercel.app/studio?demo=1&guide=1> for the most consistent first-run and presentation experience.
