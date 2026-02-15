# Replay + Compare Studio (Execution Plan)

Date: 2026-02-15
Owner: Product Engineering Lead (Codex)
Status: In Progress

## Objective

Deliver a world-class, research-positioned but production-grade Studio experience for:

1. Replay of a single run timeline
2. Baseline vs current run comparison
3. Root-cause guidance with actionable recommendations

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
- [ ] M2: Studio UI and UX implementation
- [ ] M3: Test expansion (unit + e2e)
- [ ] M4: Documentation and release verification

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

- [ ] Add `Studio` route and navigation entrypoint
- [ ] Add dual upload input with file-size validation
- [ ] Add demo dataset prefill action
- [ ] Add replay controls: play, pause, next/prev, scrubber, speed
- [ ] Add live step detail card
- [ ] Add overall delta summary cards
- [ ] Add skill delta/regression table
- [ ] Add root-cause insight panel
- [ ] Add failure/empty/help states for each panel
- [ ] Validate keyboard navigation and focus visibility

### M3 Tests

- [ ] Extend unit tests for comparison heuristics and edge cases
- [ ] Add Playwright test for Studio happy path
- [ ] Add Playwright assertion for compare output visibility

### M4 Docs and release checks

- [ ] Update README with Studio workflow
- [ ] Update `docs/help.md` with step-by-step Studio usage
- [ ] Update `docs/faq.md` with comparison/replay FAQs
- [ ] Run `pnpm lint`
- [ ] Run `pnpm test`
- [ ] Run `pnpm build`
- [ ] Run `pnpm e2e`
- [ ] Run `uv run pytest`
- [ ] Run `uv run ruff check .`
- [ ] Run `uv run mypy skillscope`

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
2. CI is green on `master`.
3. Vercel production deployment is `Ready`.
