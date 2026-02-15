# Demo Kit

This guide gives you repeatable, presenter-friendly scripts for SkillScope.

Primary live URL: <https://skillscope-amber.vercel.app/studio?demo=1&guide=1>

## 90-second script

1. “SkillScope helps us diagnose agent regressions quickly by comparing a known-good run to a current run.”
1. Open the guided Studio URL and run the walkthrough.
1. Point to one root-cause card (for example, missing skill or token growth).
1. Close with one next action from skill-level deltas.

## 5-minute script

1. Introduce the problem: raw traces are noisy and hard to action quickly.
1. Run guided walkthrough in Studio.
1. Explain the replay timeline and where divergence appears.
1. Highlight overall deltas (calls/tokens/errors/latency).
1. Show root-cause insights and one concrete engineering follow-up.

## 15-minute deep dive

1. Open with 90-second narrative.
1. Show the same workflow with your own baseline/current logs.
1. Explain technical flow:
   - parse/normalize events
   - deterministic replay ordering
   - global + per-skill diffing
   - rule-based root-cause insights
1. Connect to observability stack and docs paths.
1. End with roadmap and integration options.

## Backup plan (if live demo fails)

1. Stay on the same URL and use built-in demo data only.
1. Use screenshots from the docs/assets bundle if browser behavior degrades.
1. If time is constrained, show only:
   - run summary
   - likely root causes
   - skill-level deltas
1. Always finish with an explicit next engineering action.

## Speaking points

- Non-technical: “This shows what changed and why it likely regressed.”
- Technical: “Client-side replay + deterministic diffing + heuristic triage over OpenTelemetry-aligned attributes.”
- Positioning: “Research-only project, production-grade engineering quality.”
