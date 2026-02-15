# Release-ready v1

## Purpose / Big Picture

- Ship a production-quality MVP while keeping public positioning research-only.
- Deliver a minimal, polished web UI with in-browser analysis to complement the CLI.
- Ensure quality gates (tests, lint, typecheck, build) and documentation are complete for v1.

## Progress

- [x] Milestone 0: Repo steering files + release checklist + ExecPlan
- [x] Milestone 1: Web UI foundation (Next.js + Tailwind) and app shell
- [x] Milestone 2: Client-side analysis engine + unit tests
- [x] Milestone 3: Onboarding, demo flow, help page, and accessibility polish
- [ ] Milestone 4: CI updates, docs updates, and release validation

## Surprises & Discoveries

- Date: 2026-02-15
  Discovery: `uv run pytest` failed because `pytest` is only in `dev` extras.
  Impact: Need `uv sync --all-extras` before baseline test verification.

## Decision Log

- Date: 2026-02-15
  Decision: Web UI is static and client-side only, deployed to Vercel, with in-browser analysis.
  Rationale: Lower scope and security risk while delivering a polished UX and demo experience.
  Alternatives considered: Hosted backend or local API companion.

## Outcomes & Retrospective

- Completed:
- Deferred:
- Risks left:
- Follow-ups:

## Verification Evidence

- Commands run:
  - `uv sync --all-extras`
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run mypy skillscope`
  - `pnpm lint`
  - `pnpm test`
  - `pnpm build` (warning about Next.js workspace root)
  - `pnpm e2e`
- Tests run:
  - Python: 36 passed
  - Web: Vitest (2), Playwright (2)
- Manual checks: Not run
