# Contributing to SkillScope

Thanks for your interest in improving SkillScope. Contributions that improve instrumentation, exporters, UI workflows, docs, and demo reliability are welcome.

## Local setup

1. Fork the repository and clone your fork.

1. Install Python and project dependencies:

   ```bash
   uv sync --all-extras
   ```

1. Install web dependencies:

   ```bash
   cd web
   pnpm install
   cd ..
   ```

## Quality gates

Run all checks before opening a PR:

```bash
uv run pytest
uv run ruff check .
uv run mypy skillscope
uv run mdformat --check README.md docs

cd web
pnpm lint
pnpm test
pnpm build
pnpm e2e
```

## Development guidelines

- Keep the product publicly positioned as research-only.
- Keep web analysis client-side by default unless a change explicitly requires backend behavior.
- Add or update tests for behavioral changes.
- Update docs (`README.md`, `docs/help.md`, `docs/faq.md`) when user-facing behavior changes.
- Keep telemetry semantics aligned with OpenTelemetry + Agent Skills conventions.

## Pull request checklist

- [ ] Tests added or updated as needed
- [ ] Python checks pass (`pytest`, `ruff`, `mypy`)
- [ ] Web checks pass (`lint`, `test`, `build`, `e2e`)
- [ ] Docs updated for any user-visible change
- [ ] CI is green

## Reporting issues

Open a GitHub issue with:

- Problem statement
- Reproduction steps
- Expected vs actual behavior
- Environment details (`python --version`, OS, browser if relevant)

## License

By contributing, you agree that your contributions are licensed under Apache-2.0.
