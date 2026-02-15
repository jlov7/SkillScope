# Release Checklist (v1)

## Product & UX

- [x] Core user journeys are coherent end-to-end (happy path + key failure states) with clear UX and copy.
- [x] Onboarding is implemented (first-run, empty states, progressive disclosure).
- [x] Help is implemented (in-app help/tooltips + a minimal docs/help page).

## Quality Gates

- [x] Tests exist for critical logic and key UI flows.
- [x] Lint, typecheck, and build pass.
- [x] CI is green.

## Accessibility

- [x] Keyboard navigation for primary flows.
- [x] Sensible focus states.
- [x] Labels/aria where needed.

## Performance

- [x] No obvious slow pages.
- [x] Avoid unnecessary re-renders.
- [x] Reasonable bundle size for the stack.

## Security Hygiene

- [x] No secrets in repo.
- [x] Inputs validated.
- [x] Safe error handling.
- [x] Auth boundaries respected (if applicable).

## Docs

- [x] README includes local setup + run + test + deploy notes + env vars.
