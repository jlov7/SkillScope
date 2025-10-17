# Frequently Asked Questions

**Is SkillScope an official Anthropic product?**  
No. SkillScope is a community research project that builds on publicly documented behavior. It never inspects or modifies Anthropic internals.

**Does it require an Anthropic API key?**  
Only when you want to forward real API calls through the `AnthropicInstrumented` wrapper. All demos and tests run without a key.

**What exactly is recorded?**  
SkillScope captures *intent*—which Skill you meant to use, which files were referenced, whether policy approvals were required, and model/tokens metadata. It does not store raw prompts or outputs unless you choose to log them yourself.

**How are tokens estimated when the SDK is absent?**  
The default estimator assumes ~4 characters per token and adds the requested `max_tokens`. It’s conservative: real usage will usually be lower. Replace `default_token_estimator` with a custom callback if you have more precise heuristics.

**Can we send telemetry to our existing observability stack?**  
Yes. SkillScope emits standard OpenTelemetry spans/logs/metrics. Enable `SKILLSCOPE_EXPORT_OTLP=1`, install the `skillscope[otlp]` extras for a full SDK exporter, and point to an OTLP collector.

**What about policy-sensitive Skills?**  
The `skill.policy_required` attribute is a simple boolean flag set by the developer. The CLI’s `analyze` command reports policy rates, and the Grafana dashboard visualizes them for monitoring.

**Is there a quick way to demo the dashboards?**  
Launch the bundled stack in `ops/` and import the Grafana JSON. A sample metrics file (`ops/sample_metrics.prom`) can be loaded into Prometheus for instant visuals.

**How should we contribute improvements?**  
See `CONTRIBUTING.md` for development workflow, code style, and testing requirements. We welcome extensions to the semantic conventions and exporters.

**What’s the license?**  
Apache-2.0. Feel free to experiment and adapt for research and internal tooling.
