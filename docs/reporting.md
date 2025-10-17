# Reporting With SkillScope

This guide is written for product managers, operations partners, and policy teams who want answers without diving into code.

## What you get

SkillScope creates a short record every time your team intends to use a Claude Skill. Each record captures:
- The Skill name and version
- How many files were loaded
- Whether policy approval was required
- Estimated tokens for the request
- Which Claude model was involved

You can turn those records into clear summaries with a single command.

## Step-by-step: Weekly summary

1. **Ask an engineer** to export the week’s SkillScope events (JSONL file). They can run `skillscope emit --input ... --stdout > week.jsonl`.
2. **Run the analyzer**:

   ```bash
   skillscope analyze week.jsonl
   ```

   You’ll see a table like:

   ```
   SkillScope Summary
   ==================
   Total events: 42
   Skills observed: 3
   Recorded tokens: 18540

   Skill                             Calls  Avg Tokens   Policy % Top Files                      Models
   Brand Voice Editor (Safe Demo)        9       312.0        0.0 examples/skills/...            claude-3-5-sonnet
   Contract Analyzer                     7       421.5       57.1 contracts/nda.md               claude-3-opus
   ```

3. **Share the table** in docs, email, or chat. It reads like a status update—no engineering jargon required.

4. **Need spreadsheets?** Use JSON output:

   ```bash
   skillscope analyze week.jsonl --format json > week-summary.json
   ```

   Upload the JSON into your favorite BI tool or add it to Google Sheets with an importer.

5. **No data yet?** Try `skillscope analyze --demo` to see a sample summary line-up.

## Live dashboards (optional)

If your organization already runs Grafana or another telemetry tool:
1. Ask the platform team to set `SKILLSCOPE_EXPORT_OTLP=1` on workloads that use Skills.
2. Point the endpoint to a collector (the repo ships with `ops/docker-compose.yaml` if you want to try it locally).
3. Import `dashboards/grafana_skillscope.json` into Grafana. Preview the layout via `docs/assets/grafana-dashboard.png`.
4. (Optional) After `cd ops`, run:

   ```bash
   docker exec ops-prometheus-1 promtool tsdb create-blocks-from openmetrics /etc/prometheus/sample_metrics.prom /tmp/skillscope-demo
   docker exec ops-prometheus-1 sh -c 'mv /tmp/skillscope-demo/* /prometheus'
   ```

   This seeds Prometheus with example data so panels populate immediately.

## Glossary

- **Skill**: curated folder of instructions + resources for Claude to follow.
- **Policy required**: does the Skill require human approval before execution?
- **Progressive level**: how much of the Skill has been revealed (`metadata`, `referenced`, `eager`).
- **Tokens**: billing unit for how much text is processed; think approximate word pieces.

## Tips

- Look at `Avg Tokens` to spot expensive Skills. Large averages may indicate extra-long prompts or output.
- `Policy %` helps you monitor approval-heavy Skills so you can staff reviews appropriately.
- `Top Files` shows which guides, style sheets, or resources the Skill actually touched.

Still need help? Share this guide with your engineering partner—they can adjust instrumentation or exporters without restructuring your workflow.
