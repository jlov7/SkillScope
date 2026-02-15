# SkillScope Web UI

This folder contains the static Next.js web UI for SkillScope.

## Local development

```bash
pnpm install
pnpm dev
```

Open <http://localhost:3000>.

## Main routes

- `/` Home and onboarding
- `/analyze` single-run summary analysis
- `/studio` Replay + Compare Studio (baseline vs current)
- `/demo` built-in sample summary
- `/help` quick usage guidance

## Quality gates

```bash
pnpm lint
pnpm test
pnpm build
pnpm e2e
```

## Deployment

Production deployment is configured from repo root via `vercel.json` and publishes static output from `web/out`.
