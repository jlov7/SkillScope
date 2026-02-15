# Demo Funnel Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship a world-class, public-facing demo and explanation funnel that makes SkillScope easy to try, understand, and present.

**Architecture:** Extend the existing static Next.js UI with guided Studio behavior and dedicated narrative pages (`/start`, `/why`, `/demo-kit`), then align repo docs for technical and non-technical audiences. Keep everything client-side and static-export compatible.

**Tech Stack:** Next.js App Router, TypeScript, Tailwind CSS, Playwright, Markdown docs, Vercel static deployment.

______________________________________________________________________

## Tasks

### Task 1: Guided Studio demo mode

**Files:**

- Modify: `web/src/app/studio/page.tsx`

Steps:

1. Add support for `?demo=1&guide=1` deep link behavior.
1. Add a guided walkthrough panel with clear presenter-oriented steps and actions.
1. Add direct “copy/share demo link” affordance.
1. Ensure replay controls and insights sections are addressable targets.

### Task 2: Funnel routes and navigation

**Files:**

- Create: `web/src/app/start/page.tsx`
- Create: `web/src/app/why/page.tsx`
- Create: `web/src/app/demo-kit/page.tsx`
- Modify: `web/src/components/Shell.tsx`
- Modify: `web/src/app/page.tsx`
- Modify: `web/src/app/help/page.tsx`

Steps:

1. Add the three new routes with focused UX for trial, explanation, and presenting.
1. Update nav and homepage CTAs to funnel users through these routes.
1. Keep copy concise, explicit, and research-only positioned.

### Task 3: Documentation upgrade

**Files:**

- Create: `docs/demo-kit.md`
- Create: `docs/explainers.md`
- Modify: `docs/index.md`
- Modify: `README.md`

Steps:

1. Add non-technical and technical articulation guidance.
1. Add short/medium/deep demo scripts with backup plan.
1. Wire docs index and README to the new pathways.

### Task 4: Journey tests and validation

**Files:**

- Modify: `web/tests/home.spec.ts`

Steps:

1. Add route checks for new pages.
1. Add guided deep-link test for Studio.
1. Run full quality gates and fix issues.

### Task 5: Release verification

Steps:

1. Run local verification commands (python + web + docs formatting).
1. Commit in small logical steps.
1. Push and verify GitHub CI and Vercel production status.
