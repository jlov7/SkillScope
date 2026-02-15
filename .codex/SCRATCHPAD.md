## Current Task

Build and ship Replay + Compare Studio in the web UI with production-grade quality gates.

## Status

Completed

## Plan

1. [x] Create exhaustive execution tracker and TODO ledger
2. [x] Implement replay/compare core analysis library and tests
3. [x] Build Studio UI with onboarding, replay controls, and diff insights
4. [x] Add/expand e2e coverage for critical Studio flow
5. [x] Update docs/help/README
6. [x] Run full quality gates and fix regressions
7. [x] Commit milestones, push, verify CI and deployment

## Files Expected To Change

- `PLANS.md`
- `.codex/PLANS.md`
- `.codex/SCRATCHPAD.md`
- `web/src/lib/analyze.ts`
- `web/src/lib/demo-data.ts`
- `web/src/lib/analyze.test.ts`
- `web/src/app/studio/page.tsx`
- `web/src/components/Shell.tsx`
- `web/src/app/page.tsx`
- `web/src/app/help/page.tsx`
- `web/tests/home.spec.ts`
- `README.md`
- `docs/help.md`
- `docs/faq.md`

## Decisions Made

- Keep the feature fully client-side and static-export-compatible.
- Reuse existing parser/summarizer primitives and extend with run comparison APIs.

## Open Questions

- None blocking implementation.
