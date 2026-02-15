# Replay + Compare Studio

## Purpose / Big Picture

- Ship a next-level analysis experience that makes regressions obvious in minutes, not hours.
- Keep public positioning research-only while implementing production-grade UX, quality, and reliability.
- Add replay, diff, and root-cause guidance without introducing backend storage or data exfiltration.

## Progress

- [x] Milestone 0: Create exhaustive execution tracker + TODO ledger
- [x] Milestone 1: Build replay/compare analysis engine in `web/src/lib`
- [ ] Milestone 2: Build Studio UI flow (upload, replay controls, compare insights)
- [ ] Milestone 3: Add critical tests (unit + e2e) for new behavior
- [ ] Milestone 4: Update docs/help copy and run full quality gates
- [ ] Milestone 5: Final release verification + sync

## Exhaustive TODO Ledger

- [x] Define normalized replay step model with stable IDs and timestamps
- [x] Build robust timestamp coercion (unix, ISO, fallback sequence)
- [x] Build run metrics extraction (events, skills, calls, tokens, approvals, errors, latency)
- [x] Build skill-level metric rollups for side-by-side comparison
- [x] Build run diff engine for baseline vs current
- [x] Build heuristics for likely root-cause detection (latency, tokens, approvals, failures, missing skills)
- [x] Build plain-language recommendation generator
- [x] Add unit tests for timeline reconstruction
- [x] Add unit tests for diff calculations and percentage math edge cases
- [x] Add unit tests for heuristic outputs (regression and improvement paths)
- [ ] Create Studio page with dual upload and explicit error states
- [ ] Add demo seed pathway for guided exploration
- [ ] Add replay controls (play/pause, stepper, range scrubber, speed)
- [ ] Add focused step detail panel (skill/event/model/tokens/latency/status)
- [ ] Add comparison summary cards and skill delta table
- [ ] Add root-cause insights panel with severity labels
- [ ] Add empty/loading/error states for all major panels
- [ ] Wire navigation + onboarding entrypoints to Studio
- [ ] Add keyboard-accessible controls and visible focus states
- [ ] Add/extend Playwright tests for Studio happy path
- [ ] Update help docs + README flow for Studio usage
- [ ] Run lint/test/build/e2e and fix all failures
- [ ] Commit milestones in reviewable increments
- [ ] Push and verify CI green

## Surprises & Discoveries

- Date: 2026-02-15
  Discovery: Current static export routing needs clean URL handling on Vercel for extensionless paths.
  Impact: Keep `cleanUrls` in `vercel.json` for new routes (including Studio).
- Date: 2026-02-15
  Discovery: Existing summary logic can be reused safely for call/token baselines, reducing risk in the new diff engine.
  Impact: Replay + compare implementation stays additive with low regression risk.

## Decision Log

- Date: 2026-02-15
  Decision: Keep Replay + Compare fully client-side in the existing static web app.
  Rationale: Preserves privacy posture, reduces security risk, and keeps deployment simple.
  Alternatives considered: server-side comparison service.

## Outcomes & Retrospective

- In progress.

## Verification Evidence

- Pending for this plan execution.

---

# Release-ready v1 (Completed)

## Summary

- Shipped static web MVP with onboarding, analysis, demo, help, CI coverage, and release docs.
- Verified quality gates and production deployment readiness.
