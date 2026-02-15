# Release Checklist (v1)

## Product & UX

- [ ] Core user journeys are coherent end-to-end (happy path + key failure states) with clear UX and copy.
- [ ] Onboarding is implemented (first-run, empty states, progressive disclosure).
- [ ] Help is implemented (in-app help/tooltips + a minimal docs/help page).

## Quality Gates

- [ ] Tests exist for critical logic and key UI flows.
- [ ] Lint, typecheck, and build pass.
- [ ] CI is green.

## Accessibility

- [ ] Keyboard navigation for primary flows.
- [ ] Sensible focus states.
- [ ] Labels/aria where needed.

## Performance

- [ ] No obvious slow pages.
- [ ] Avoid unnecessary re-renders.
- [ ] Reasonable bundle size for the stack.

## Security Hygiene

- [ ] No secrets in repo.
- [ ] Inputs validated.
- [ ] Safe error handling.
- [ ] Auth boundaries respected (if applicable).

## Docs

- [ ] README includes local setup + run + test + deploy notes + env vars.
