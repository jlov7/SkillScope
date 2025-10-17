# SkillScope Overview

SkillScope is an Apache-2.0 research project that instruments Anthropic *Skills* with OpenTelemetry semantics. This document introduces the concepts, vocabulary, and data produced by SkillScope so stakeholders across product, engineering, and operations have a shared frame of reference.

## What is a Skill?

Anthropic Skills bundle procedural knowledge into a folder that contains:
- `SKILL.md` describing purpose, inputs, outputs, and policy constraints.
- Optional supporting files (style guides, scripts, resources).
- Progressive disclosure levels letting agents load metadata first, then referenced files, then higher-privilege execution.

SkillScope does **not** alter Skill behavior. It only records intent: *which Skill did we mean to use, what resources were referenced, and how did that choice affect the request?*

## Why observability?

- Product leads want to know whether a new Skill is actually used.
- Policy and trust teams need to flag Skills that require approval.
- Engineering teams want to trace Skill usage through logs, metrics, and dashboards.

SkillScope extends the [OpenTelemetry GenAI & Agent semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) with additional attributes:

| Attribute | Description |
| --- | --- |
| `skill.name` | Human-readable Skill descriptor (e.g., "Brand Voice Editor") |
| `skill.version` | Semantic or git-style version string |
| `skill.files_loaded_count` | Number of files presented to the Skill |
| `skill.files` | Comma-separated list of file paths bundled with the Skill |
| `skill.policy_required` | Boolean flag for policy/approval gating |
| `skill.progressive_level` | Progressive disclosure level (`metadata`, `referenced`, `eager`) |
| `gen_ai.request.model` | Claude model family used in the request |
| `gen_ai.client.token.usage` | Total input + output tokens (estimated when not provided) |

These attributes integrate with any OpenTelemetry-compatible backend (Prometheus, Grafana, Honeycomb, Lightstep, etc.).

## Data products

SkillScope emits information in three primary forms:
1. **Spans and metrics** — OpenTelemetry-structured events for live observability pipelines.
2. **NDJSON event streams** — Lightweight line-delimited JSON for local analysis or ad-hoc scripting.
3. **Human-readable summaries** — `skillscope analyze` converts raw events into tables/JSON for status reports.
4. **Dashboards** — Grafana JSON plus a visual preview (`docs/assets/grafana-dashboard.png`) so stakeholders know what to expect.

## Project structure

```
skillscope/
  instrumentation.py   # context managers, decorators, Anthropic wrapper
  exporters.py         # NDJSON, OTLP, OpenTelemetry SDK exporters
  cli.py               # emit | ingest | analyze | demo commands
  example_data.py      # synthetic sample payloads
dashboards/
  grafana_skillscope.json
ops/
  docker-compose.yaml  # collector + Prometheus + Grafana bundle
```

## Safe demo content

The repository ships with a safe "Brand Voice" Skill (markdown only) to keep demonstrations deterministic and free of proprietary data. Running `python examples/run_with_skill.py` exercises the instrumentation without making external API calls when an Anthropic key is not configured.

## Next steps

- Read [docs/workflows.md](workflows.md) to integrate SkillScope into engineering projects.
- Share [docs/reporting.md](reporting.md) with non-technical partners who need to interpret SkillScope output.
- Import the Grafana dashboard and experiment with the bundled docker-compose stack for a complete observability loop.
