# Replay + Compare Studio (Execution Plan)

Date: 2026-02-15
Owner: Product Engineering Lead (Codex)
Status: In Progress

## Objective

Deliver a world-class, research-positioned but production-grade Studio experience for:

1. Replay of a single run timeline
1. Baseline vs current run comparison
1. Root-cause guidance with actionable recommendations

## Scope

- In scope:
  - Client-side timeline reconstruction from uploaded JSON/JSONL/NDJSON/Anthropic payloads
  - Side-by-side metric diffs and skill-level deltas
  - Heuristic root-cause analysis (token, latency, policy, failure, missing/new skill)
  - Guided UI states, accessibility labels/focus, and keyboard-friendly controls
  - Test coverage for core logic and critical UI flow
  - Docs updates for Studio usage
- Out of scope:
  - Server-side persistence
  - Auth/user accounts
  - Multi-user collaboration backend

## Milestones

- [x] M0: Tracking and execution ledger setup
- [x] M1: Core replay/compare library implementation
- [x] M2: Studio UI and UX implementation
- [x] M3: Test expansion (unit + e2e)
- [x] M4: Documentation and release verification

## Exhaustive Task Checklist

### M1 Core logic

- [x] Define run-step and comparison data contracts
- [x] Implement timestamp coercion and deterministic ordering
- [x] Implement replay timeline generation
- [x] Implement metrics aggregation per run
- [x] Implement skill-level rollups
- [x] Implement baseline/current diff calculations
- [x] Implement root-cause heuristic engine
- [x] Implement recommendation text generator
- [x] Add unit tests for all above

### M2 UI/UX

- [x] Add `Studio` route and navigation entrypoint
- [x] Add dual upload input with file-size validation
- [x] Add demo dataset prefill action
- [x] Add replay controls: play, pause, next/prev, scrubber, speed
- [x] Add live step detail card
- [x] Add overall delta summary cards
- [x] Add skill delta/regression table
- [x] Add root-cause insight panel
- [x] Add failure/empty/help states for each panel
- [x] Validate keyboard navigation and focus visibility

### M3 Tests

- [x] Extend unit tests for comparison heuristics and edge cases
- [x] Add Playwright test for Studio happy path
- [x] Add Playwright assertion for compare output visibility

### M4 Docs and release checks

- [x] Update README with Studio workflow
- [x] Update `docs/help.md` with step-by-step Studio usage
- [x] Update `docs/faq.md` with comparison/replay FAQs
- [x] Run `pnpm lint`
- [x] Run `pnpm test`
- [x] Run `pnpm build`
- [x] Run `pnpm e2e`
- [x] Run `uv run pytest`
- [x] Run `uv run ruff check .`
- [x] Run `uv run mypy skillscope`

## Risks and Mitigations

- Risk: Timestamp quality in arbitrary logs can be inconsistent.
  Mitigation: Strong fallback ordering and explicit confidence labels.
- Risk: Large files may degrade responsiveness.
  Mitigation: Keep 8MB cap and compute in memoized passes.
- Risk: False-positive root-cause heuristics.
  Mitigation: Rule explanations and conservative thresholds.

## Verification Gate

Work is complete only when:

1. All checklist items are checked.
1. CI is green on `master`.
1. Vercel production deployment is `Ready`.
