# SkillScope Overview

SkillScope is an Apache-2.0 research project that instruments Agent Skills with OpenTelemetry semantics. This document introduces the concepts, vocabulary, and data produced by SkillScope so stakeholders across product, engineering, and operations have a shared frame of reference.

## What is a Skill?

Agent Skills (the open standard) bundle procedural knowledge into a folder that contains:

- `SKILL.md` with YAML frontmatter (`name`, `description`, optional metadata). The canonical format is defined in the [Agent Skills specification](https://agentskills.io/specification).
- Instructions describing purpose, inputs, outputs, and policy constraints.
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
| `skill.description` | Short summary from SKILL.md frontmatter |
| `skill.version` | Semantic or git-style version string |
| `skill.files_loaded_count` | Number of files presented to the Skill |
| `skill.files` | Comma-separated list of file paths bundled with the Skill |
| `skill.policy_required` | Boolean flag for policy/approval gating |
| `skill.progressive_level` | Progressive disclosure level (`metadata`, `referenced`, `eager`) |
| `skill.license` | License identifier from SKILL.md frontmatter (optional) |
| `skill.compatibility` | Environment requirements from SKILL.md (optional) |
| `skill.allowed_tools` | Pre-approved tool patterns (optional) |
| `gen_ai.request.model` | Model family used in the request |
| `gen_ai.usage.input_tokens` | Input tokens used (estimated when not provided) |
| `gen_ai.usage.output_tokens` | Output tokens used (estimated when not provided) |
| `gen_ai.client.token.usage` | Total tokens for metrics compatibility |

These attributes integrate with any OpenTelemetry-compatible backend (Prometheus, Grafana, Honeycomb, Lightstep, etc.).

## Semantic mapping

SkillScope attributes complement the OpenTelemetry GenAI & Agent semantic conventions.

| SkillScope attribute | Related OTEL attribute(s) | Purpose |
| --- | --- | --- |
| `skill.name` | `gen_ai.operation.name` / `gen_ai.tool.name` (when used) | Human-friendly Skill identifier for spans/logs. |
| `skill.version` | — | Tracks Skill revisions across deployments. |
| `skill.files` / `skill.files_loaded_count` | — | Describes referenced resources so teams can audit file usage. |
| `skill.policy_required` | — | Flags workflows that require human approval. |
| `skill.progressive_level` | — | Clarifies disclosure level (`metadata`, `referenced`, `eager`). |
| `skillscope.*` (extra attrs) | `gen_ai.*` | Custom dimensions that avoid collisions with official keys while specs stabilize. |

> Tip: export `OTEL_SEMCONV_STABILITY_OPT_IN=gen-ai` to opt into the evolving GenAI/Agent conventions.

## Data products

SkillScope emits information in three primary forms:

1. **Spans and metrics** — OpenTelemetry-structured events for live observability pipelines.
1. **NDJSON event streams** — Lightweight line-delimited JSON for local analysis or ad-hoc scripting.
1. **Human-readable summaries** — `skillscope analyze` converts raw events into tables/JSON for status reports.
1. **Dashboards** — Grafana JSON plus a visual preview (`docs/assets/grafana-dashboard.png`) so stakeholders know what to expect.

## Skill discovery and prompts

SkillScope can scan skill directories, extract frontmatter, and generate prompt metadata:

```bash
skillscope discover ./skills --format xml
```

This emits `<available_skills>` XML blocks suitable for agent system prompts, aligned with the Agent Skills guidance.

## Project structure

```
skillscope/
  instrumentation.py   # context managers, decorators, tool wrappers
  exporters.py         # NDJSON, OTLP, OpenTelemetry SDK exporters
  cli.py               # emit | ingest | analyze | demo | discover | validate
  example_data.py      # synthetic sample payloads
  skills.py            # Agent Skills frontmatter parsing/validation
dashboards/
  grafana_skillscope.json
ops/
  docker-compose.yaml  # collector + Prometheus + Grafana bundle
```

## Safe demo content

The repository ships with a safe "Brand Voice" Skill (markdown only) to keep demonstrations deterministic and free of proprietary data. Running `python examples/run_with_skill.py` exercises the instrumentation without making external API calls when a provider key is not configured.

## Next steps

- Read [docs/workflows.md](workflows.md) to integrate SkillScope into engineering projects.
- Share [docs/reporting.md](reporting.md) with non-technical partners who need to interpret SkillScope output.
- Import the Grafana dashboard and experiment with the bundled docker-compose stack for a complete observability loop.
