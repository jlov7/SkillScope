# Engineering Workflows

This guide shows engineers how to instrument Skills, export telemetry, and integrate SkillScope with existing pipelines.

## 1. Install

```bash
python -m pip install -e .
# Optional OTLP extras for native OpenTelemetry exporters:
python -m pip install -e .[otlp]
```

## 2. Instrument code

### Context manager

```python
from skillscope.instrumentation import use_skill, AnthropicInstrumented

client = AnthropicInstrumented()

with use_skill(
    name="Brand Voice Editor (Safe Demo)",
    version="1.0.0",
    files=["examples/skills/brand-voice/style-guide/brand-voice.md"],
    policy_required=False,
    progressive_level="referenced",
    extra_attrs={"team": "marketing-ai"},
):
    response = client.messages_create(
        model="claude-3-5-sonnet",
        max_tokens=120,
        messages=[{"role": "user", "content": "Rewrite this paragraph in our brand voice."}],
    )
```

### From SKILL.md frontmatter

```python
from skillscope.instrumentation import use_skill_from_path

with use_skill_from_path(
    "examples/skills/brand-voice",
    files=["examples/skills/brand-voice/style-guide/brand-voice.md"],
    model="claude-3-5-sonnet",
    operation="invoke_agent",
):
    ...
```

### Decorator

```python
from skillscope.instrumentation import with_skill

@with_skill(
    name="Contract Analyzer",
    version="2.3.1",
    files=["skills/contract_analyzer/policy.md"],
    policy_required=True,
    progressive_level="eager",
)
def review_contract(text: str) -> str:
    ...
```

### Tool and script execution

```python
from skillscope.instrumentation import run_skill_script, use_tool

with use_tool(name="vector-search", tool_type="datastore"):
    ...

run_skill_script("skills/contract_analyzer/scripts/extract.sh", args=["--latest"], check=True)
```

### Async workflows

```python
from skillscope.instrumentation import gather_with_skill

results = await gather_with_skill(
    {"name": "QA Summarizer", "files": ["skills/qa_summarizer/guide.md"]},
    [agent.step_one(), agent.step_two()],
)
```

SkillScope uses `contextvars` to propagate spans safely across nested contexts and async tasks.

## 3. Export telemetry

### NDJSON (default)

```bash
export SKILLSCOPE_EXPORT_OTLP=0
python your_script.py | skillscope ingest - --to ndjson
```

### OTLP (HTTP fallback)

```bash
export SKILLSCOPE_EXPORT_OTLP=1
export SKILLSCOPE_OTLP_ENDPOINT=http://localhost:4318/v1/logs
python your_script.py
```

### OTLP via OpenTelemetry SDK

```bash
python -m pip install -e .[otlp]
export SKILLSCOPE_EXPORT_OTLP=1
export OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4317
python your_script.py
```

SkillScope auto-detects the SDK and sends real spans/metrics through the configured `TracerProvider`.

## 4. CLI pipelines

- **Emit**: `skillscope emit --input events.jsonl --stdout` — normalize and forward raw logs.
- **Ingest**: `skillscope ingest ./logs --to otlp` — recursively traverse a directory of JSON/JSONL logs.
- **Analyze**: `skillscope analyze ./logs --format json` — gather statistics for dashboards or automation.
- **Discover**: `skillscope discover ./skills` — list skill metadata or emit `<available_skills>` XML.
- **Validate**: `skillscope validate ./skills` — validate SKILL.md frontmatter against the spec.

All commands accept `--input-format auto|json|jsonl|anthropic`. `auto` inspects the payload and chooses the right parser.

## 5. Observability stack

Launch a local collector + Prometheus + Grafana bundle:

```bash
cd ops
docker compose up
# Seed Prometheus with sample data (optional):
docker exec ops-prometheus-1 promtool tsdb create-blocks-from openmetrics /etc/prometheus/sample_metrics.prom /tmp/skillscope-demo
docker exec ops-prometheus-1 sh -c 'mv /tmp/skillscope-demo/* /prometheus'
```

Then:

1. Point your app at `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317`.
1. Import `dashboards/grafana_skillscope.json` in Grafana (http://localhost:3000, password `skillscope`).
1. Preview the expected layout via `docs/assets/grafana-dashboard.png`.
1. Watch Skill adoption, file usage, policy rate, token trends, and latency p95 in real time.

## 6. Troubleshooting

- No spans? Ensure `SKILLSCOPE_EXPORT_OTLP` is set and the collector endpoint is reachable.
- Missing tokens? SkillScope estimates token usage when the SDK lacks usage data; set `SKILLSCOPE_CAPTURE=1` to inspect the emitted events.
- Duplicate policy counts? The summary clamps policy-required counts to the number of observed completions to avoid inflation.

Need more? File an issue or adapt the exporters. Everything here is plain Python with minimal dependencies, so it is straightforward to modify.
