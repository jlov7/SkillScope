# AGENTS

## Working Agreements

- Keep public-facing copy research-only while meeting production-grade quality internally.
- Use `uv` for Python workflows and `pnpm` for the web UI.
- Make small, reviewable changes and commit frequently with conventional commits.
- Do not commit generated artifacts, `.venv/`, `node_modules/`, or secrets.
- Validate inputs and handle errors safely at boundaries.

## Commands

### Python (from repo root)

- Setup: `uv sync --all-extras`
- Tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Typecheck: `uv run mypy skillscope`

### Web UI (from `web/`)

- Install: `pnpm install`
- Dev server: `pnpm dev`
- Tests: `pnpm test`
- Lint: `pnpm lint`
- Typecheck: `pnpm typecheck`
- Build: `pnpm build`

## Quality Bar

- Tests, lint, typecheck, and build must pass for both Python and Web UI.
- Core flows must be keyboard accessible with visible focus states and labeled controls.
- Performance: avoid unnecessary re-renders; keep bundle size reasonable.
- Update docs and help content whenever behavior or UX changes.
