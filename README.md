# SkillScope — OpenTelemetry for Agent Skills (research-only)

SkillScope adds observability to the open Agent Skills standard so you can see which Skill was intended, which files were referenced, whether policy approval was required, and how tokens or latency shifted. Everything here is non-commercial, vendor-neutral, and driven by the Agent Skills specification plus OpenTelemetry conventions.

## At a glance

- **Audience** — Product & operations leads, engineering teams, and observability practitioners who need transparent Skill usage.
- **Signals** — `skill.*` attributes layered on top of the OpenTelemetry GenAI & Agent conventions.
- **Outputs** — NDJSON events, OTLP traces/metrics, Grafana dashboards, and human-readable summaries (`skillscope analyze`).

## Audience quick links

- Product/Ops teams: start with [docs/reporting.md](docs/reporting.md).
- Engineers / platform owners: see [docs/workflows.md](docs/workflows.md).
- Observability background + glossary: read [docs/overview.md](docs/overview.md).
- Browse everything: [docs/index.md](docs/index.md).

## Quickstart (2 minutes)

```bash
git clone https://github.com/skillscope/skillscope.git
cd skillscope
python -m pip install -e .[dev]
export SKILLSCOPE_CAPTURE=1     # optional JSON capture per provider call
python examples/run_with_skill.py
skillscope emit --demo          # emits synthetic spans/events to stdout
```

You can then import `dashboards/grafana_skillscope.json` into Grafana (backed by Prometheus/OTLP) or run the bundled collector stack (see below). CI parity lives in `.github/workflows/ci.yml`, which runs ruff, mypy, pytest, and demo artefact generation.

### Semantic conventions

GenAI and Agent semantic conventions continue to evolve. To opt into the current stable set, export:

```bash
export OTEL_SEMCONV_STABILITY_OPT_IN=gen-ai
```

See the OpenTelemetry GenAI & Agent specs for details.

## Core features

- **Instrumentation helpers**
  - `use_skill`, `use_skill_async`, `use_skill_from_path`, and `with_skill` wrap Skill-aware sections while handling context propagation.
  - `gather_with_skill` keeps spans intact across concurrent `asyncio.gather`.
  - `use_tool` and `run_skill_script` record tool/script executions with GenAI tool attributes.
  - Provider wrappers (for example, `AnthropicInstrumented`) attach `skill.*` and `skillscope.*` metadata, record JSON events when `SKILLSCOPE_CAPTURE=1`, and estimate token usage if the SDK is unavailable.
- **CLI workflows**
  - `skillscope emit` normalizes JSON/JSONL/provider conversation logs (including Anthropic) into OpenTelemetry-style events and forwards them through exporters.
  - `skillscope ingest` batches and re-exports existing logs to NDJSON or OTLP.
  - `skillscope analyze` produces human-friendly tables or JSON summaries (great for product reviews or weekly reports).
  - `skillscope demo` previews the bundled Brand Voice Skill content.
  - `skillscope discover` emits Skill metadata or `<available_skills>` XML for prompts.
  - `skillscope validate` checks SKILL.md frontmatter against the Agent Skills spec.
- **Exporters**
  - NDJSON for quick inspection (stdout or file).
  - OTLP via a lightweight HTTP client or the real OpenTelemetry SDK when optional extras are installed.
- **Dashboards & operations**
  - Grafana starter board with calls, approval rates, token throughput, latency p95, and file usage.
  - `ops/docker-compose.yaml` boots an OpenTelemetry Collector + Prometheus + Grafana loop for local experimentation (see `docs/assets/grafana-dashboard.png` for a preview).
  - `ops/sample_metrics.prom` seeds Prometheus with realistic demo data.

## Sample artefacts

- `artifacts/skillscope_demo_summary.json` — output of `skillscope analyze --demo --format json`.
- `docs/assets/grafana-dashboard.png` — dashboard preview.

## Telemetry scope

- When provider SDKs do not expose token metrics, SkillScope uses a heuristic estimator. Prefer native provider token usage fields whenever they are available.
- SkillScope emits `gen_ai.usage.input_tokens` and `gen_ai.usage.output_tokens` when available, plus `gen_ai.client.token.usage` for metrics compatibility.
- The auxiliary `skillscope.*` attributes intentionally avoid collisions with `gen_ai.*` keys while semantic conventions continue to stabilize.

## CLI cheatsheet

| Command | Purpose | Notes |
| --- | --- | --- |
| `skillscope emit --demo` | Emit synthetic spans/events | Add `--stdout/--no-stdout`, `--input`, `--input-format` for custom logs |
| `skillscope ingest path/to/logs --to otlp` | Re-export JSON/JSONL logs to OTLP or NDJSON | Works with files or directories |
| `skillscope analyze path/to/logs` | Summarize Skill activity for stakeholders | `--format json` for automation; add `--demo` to preview |
| `skillscope demo` | Show bundled Skill documentation | Uses safe synthetic content |
| `skillscope discover ./skills` | List skills or emit `<available_skills>` XML | Use `--format xml` for prompt blocks |
| `skillscope validate ./skills` | Validate SKILL.md frontmatter | `--format json` for automation |

## Environment variables

| Variable | Meaning |
| --- | --- |
| `SKILLSCOPE_CAPTURE` | When set to `1`, print compact JSON events for every provider client call |
| `SKILLSCOPE_EXPORT_NDJSON` | `0` disables NDJSON output; `SKILLSCOPE_EXPORT_NDJSON_PATH` writes to a file |
| `SKILLSCOPE_EXPORT_OTLP` | `1` enables OTLP exporters; respects `SKILLSCOPE_OTLP_ENDPOINT` / `OTEL_EXPORTER_OTLP_ENDPOINT` |
| `SKILLSCOPE_EXPORT_NDJSON_PATH` | File path for persisted NDJSON lines |

## Observability stack demo

```bash
cd ops
docker compose up
# Collector listens on 4317/4318, Prometheus on 9090, Grafana on 3000 (password: skillscope)
```

Import the Grafana dashboard (`dashboards/grafana_skillscope.json`) and point it to the Prometheus data source to explore Skill KPIs such as calls, approval rate, token flow, file usage, and p95 latency. Use `docs/assets/grafana-dashboard.png` for a quick preview of the layout. The Prometheus sample dataset at `ops/sample_metrics.prom` can be ingested inside the Prometheus container using `promtool tsdb create-blocks-from openmetrics /etc/prometheus/sample_metrics.prom /tmp/skillscope-demo` followed by `mv /tmp/skillscope-demo/* /prometheus` for an instant demo.

## Non-technical reporting flow

1. Ask an engineer to export Skill events (`skillscope emit` or `skillscope ingest`) into a JSONL file.
1. Run `skillscope analyze exported-events.jsonl` to print a table showing calls, policy rate, token averages, and referenced files per Skill.
1. Share the table output directly in status updates, or use `--format json` to feed your own dashboards/spreadsheets.
1. Want a dry run? `skillscope analyze --demo` prints a sample summary without needing data.
1. For live dashboards, point your telemetry stack (OTLP/Prometheus) at the collector and import the Grafana JSON.

## For engineers

- Add instrumentation by wrapping Skill-bound sections with `use_skill`/`with_skill` or `use_skill_from_path`. See concrete examples in [docs/workflows.md](docs/workflows.md).
- When the Anthropic Python SDK is available, `AnthropicInstrumented` will forward requests while injecting metadata; otherwise, it returns a mock preview plus estimated token usage so tests stay deterministic.
- Configure exporters using environment variables (`SKILLSCOPE_EXPORT_OTLP=1`) and optional extras (`pip install skillscope[otlp]`) to stream spans straight into your collector.

## Limitations

Provider-native Skill telemetry is not generally exposed today; SkillScope annotates your own calls and harnesses. Treat it as developer-side instrumentation, not a reverse-engineering tool. For canonical behavior, always refer to the Agent Skills spec and provider documentation.

## References

- Agent Skills specification ([Agent Skills][4])
- Agent Skills reference library (`skills-ref`) ([GitHub][6])
- Anthropic announcement & engineering deep-dive on Skills ([Anthropic][1])
- Anthropic public Skills examples and templates ([GitHub][5])
- OpenTelemetry GenAI & Agent semantic conventions ([OpenTelemetry][2])

## Contributing

Interested in improving SkillScope? Review [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow, testing checklist, and code of conduct.

## Security

For vulnerability disclosures, follow the guidance in [SECURITY.md](SECURITY.md).

[1]: https://www.anthropic.com/news/claude-team-skills
[2]: https://opentelemetry.io/docs/specs/semconv/gen-ai/
[5]: https://github.com/anthropics/skills
[4]: https://agentskills.io/specification
[6]: https://github.com/agentskills/agentskills/tree/main/skills-ref
