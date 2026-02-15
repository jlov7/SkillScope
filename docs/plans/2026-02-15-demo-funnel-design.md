# Demo-First Adoption Funnel Design

Date: 2026-02-15
Status: Implemented

## Problem

SkillScope has strong technical capability, but first-time users and stakeholders need a clearer path to:

1. Try the product immediately
1. Understand value at non-technical and technical levels
1. Present results confidently in live demos

## Design goals

- Zero-friction first run from public URL.
- Cohesive “try -> understand -> present” journey.
- Preserve research-only positioning while showcasing production-quality UX.

## UX structure

- `/start`: 60-second first-run path with direct guided demo launch.
- `/studio?demo=1&guide=1`: guided presenter mode with sequenced walkthrough actions.
- `/why`: audience-mode explanation (non-technical vs technical).
- `/demo-kit`: scripts for 90-second, 5-minute, and 15-minute demos plus fallback plan.

## Documentation structure

- `docs/explainers.md`: reusable articulation for multiple audiences.
- `docs/demo-kit.md`: repeatable scripts and backup guidance.
- `docs/index.md` and `README.md`: direct links to demo and explanation pathways.

## Quality and risk controls

- Keep logic client-side and static-export friendly.
- Extend Playwright route and deep-link coverage.
- Verify full Python + web + docs quality gates before release.
