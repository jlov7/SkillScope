# Frequently Asked Questions

**Is SkillScope an official Agent Skills product?**\
No. SkillScope is a community research project built on the open Agent Skills spec and OpenTelemetry. It never inspects or modifies provider internals.

**Does it require a provider API key?**\
Only when you want to forward real API calls through a provider wrapper like `AnthropicInstrumented`. All demos and tests run without a key.

**What exactly is recorded?**\
SkillScope captures *intent*—which Skill you meant to use, which files were referenced, whether policy approvals were required, and model/tokens metadata. It does not store raw prompts or outputs unless you choose to log them yourself.

**How are tokens estimated when the SDK is absent?**\
The default estimator assumes ~4 characters per input token and uses `max_tokens` for output. It emits `gen_ai.usage.input_tokens` and `gen_ai.usage.output_tokens`, plus `gen_ai.client.token.usage` for totals. Replace `default_token_estimator` with a custom callback if you have more precise heuristics.

**Does SkillScope follow the Agent Skills spec?**\
Yes. The demo skill includes YAML frontmatter, and `skillscope discover`/`skillscope validate` read and check SKILL.md metadata. For strict validation, use the upstream `skills-ref` reference library.

**How do we generate `<available_skills>` prompt metadata?**\
Run `skillscope discover ./skills --format xml` to emit an XML block aligned with the Agent Skills guidance.

**Which YAML parser does SkillScope use for SKILL.md?**\
SkillScope prefers `strictyaml` when available for strict parsing. If it is not installed, SkillScope falls back to a minimal parser that supports basic key/value frontmatter.

**Can we send telemetry to our existing observability stack?**\
Yes. SkillScope emits standard OpenTelemetry spans/logs/metrics. Enable `SKILLSCOPE_EXPORT_OTLP=1`, install the `skillscope[otlp]` extras for a full SDK exporter, and point to an OTLP collector.

**The spec is marked experimental. Should we opt in?**\
Set `OTEL_SEMCONV_STABILITY_OPT_IN=gen-ai` to follow the latest GenAI & Agent semantic conventions while they stabilize.

**What about policy-sensitive Skills?**\
The `skill.policy_required` attribute is a simple boolean flag set by the developer. The CLI’s `analyze` command reports policy rates, and the Grafana dashboard visualizes them for monitoring.

**How do we capture tool or script execution?**\
Wrap tool calls with `use_tool` or run scripts via `run_skill_script` so SkillScope emits GenAI tool spans alongside the parent Skill.

**Is there a quick way to demo the dashboards?**\
Launch the bundled stack in `ops/` and import the Grafana JSON. A sample metrics file (`ops/sample_metrics.prom`) can be loaded into Prometheus for instant visuals.

**How should we contribute improvements?**\
See `CONTRIBUTING.md` for development workflow, code style, and testing requirements. We welcome extensions to the semantic conventions and exporters.

**What’s the license?**\
Apache-2.0. Feel free to experiment and adapt for research and internal tooling.
