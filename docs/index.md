# SkillScope Documentation

Welcome! SkillScope is a research-grade observability toolkit that brings OpenTelemetry semantics to Agent Skills. Choose the path that matches your role:

- **Just getting oriented?** Read the [Overview](overview.md) for terminology, context, and project structure.
- **Shipping instrumentation or wiring telemetry?** Head to [Engineering Workflows](workflows.md) for code examples, exporter configuration, and collector recipes.
- **Preparing reports or stakeholder updates?** See [Reporting Playbook](reporting.md) for step-by-step summaries and dashboard tips.
- **Have a question?** Check the [FAQ](faq.md) for common topics such as token estimation, policy flagging, and safety posture.
- **Need messaging support?** Use [Explainers](explainers.md) for technical and non-technical articulation.
- **Preparing a live demo?** Use [Demo Kit](demo-kit.md) for scripts and backup plan.
- **Need a preview?** View the Grafana layout at [assets/grafana-dashboard.png](assets/grafana-dashboard.png).

## Quick links

- [README](../README.md) — high-level pitch, quickstart, and CLI cheatsheet.
- [Web UI Help](help.md) — local UI setup and demo flow.
- [Explainers](explainers.md) — audience-specific messaging guide.
- [Demo Kit](demo-kit.md) — presenter scripts and fallback strategy.
- [Grafana Dashboard](../dashboards/grafana_skillscope.json) — import into your observability stack.
- [Ops Stack](../ops/docker-compose.yaml) — collector + Prometheus + Grafana bundle.
- [Sample Metrics](../ops/sample_metrics.prom) — seed Prometheus for instant dashboards.
- [Agent Skills Spec](https://agentskills.io/specification) — format and metadata rules for SKILL.md.
- [Contributing](../CONTRIBUTING.md) — guidelines if you want to extend SkillScope.
- [Security Policy](../SECURITY.md) — how to report vulnerabilities.

If you’re evaluating SkillScope, start with the demo workflows:

```bash
python -m pip install -e .
skillscope emit --demo
skillscope analyze --demo
```

This produces synthetic telemetry and a human-readable summary so you can experience the output before touching production data.
