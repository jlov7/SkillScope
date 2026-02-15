## Current Task

Build a world-class demo and adoption funnel: guided Studio walkthrough, start/why/demo-kit pages, and polished technical + non-technical documentation.

## Status

In Progress (final release sync)

## Plan

1. [x] Set up tracking and milestones in plans
1. [x] Implement guided Studio demo mode with deep-link support
1. [x] Add Start, Why, and Demo Kit routes to the web UI
1. [x] Update navigation and onboarding calls to action
1. [x] Publish docs for explainers and presenter demo scripts
1. [x] Extend e2e tests for new user journeys
1. [ ] Run full quality gates and push
1. [ ] Verify CI + Vercel production

## Files Expected To Change

- `PLANS.md`
- `.codex/PLANS.md`
- `.codex/SCRATCHPAD.md`
- `web/src/app/studio/page.tsx`
- `web/src/components/Shell.tsx`
- `web/src/app/page.tsx`
- `web/src/app/help/page.tsx`
- `web/src/app/start/page.tsx`
- `web/src/app/why/page.tsx`
- `web/src/app/demo-kit/page.tsx`
- `web/tests/home.spec.ts`
- `README.md`
- `docs/index.md`
- `docs/demo-kit.md`
- `docs/explainers.md`

## Decisions Made

- Keep the feature fully client-side and static-export-compatible.
- Use in-app onboarding and presenter routes instead of external slide tooling.

## Open Questions

- None blocking implementation.
