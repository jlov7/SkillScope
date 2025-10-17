# Contributing to SkillScope

Thanks for your interest in improving SkillScope! This project is a research toolkit, and contributions that improve instrumentation, exporters, documentation, or demos are welcome.

## Getting started

1. **Fork** the repository and clone your fork.
2. **Install dependencies** in editable mode:

   ```bash
   python -m pip install -e .[otlp]
   ```

3. **Run tests and demos** before making changes:

   ```bash
   pytest -q
   python -m skillscope.cli emit --demo
   python -m skillscope.cli analyze --demo
   ```

## Development guidelines

- **Code style**: follow PEP 8. Keep dependencies minimal and standard-library first.
- **Tests**: add or update tests under `tests/` for new behavior. Every PR must keep `pytest` green.
- **Documentation**: update relevant files in `README.md` and `docs/` when you add new features or flags. Screenshots or diagrams should live under `docs/assets/`.
- **CLI compatibility**: maintain backward compatibility for existing commands whenever possible. Document breaking changes clearly.
- **Semantic conventions**: changes to the `skill.*` attribute set should be discussed via issues before implementation to stay aligned with OpenTelemetry guidelines.

## Pull request checklist

- [ ] Tests added/updated
- [ ] `pytest -q` passes
- [ ] `python -m skillscope.cli emit --demo` succeeds
- [ ] `python -m skillscope.cli analyze --demo` succeeds
- [ ] Docs updated (README and/or `docs/`)
- [ ] GitHub Actions workflow passes (see `.github/workflows/ci.yml`)

## Issue reporting

Use GitHub issues to report bugs or propose enhancements. Include:
- Description of the problem or idea
- Steps to reproduce (if applicable)
- Environment details (`python --version`, OS, relevant env vars)

## Code of conduct

Be respectful and constructive. This project values collaboration across disciplines (engineering, policy, ops). Harassment or discriminatory behavior is not tolerated.

By contributing, you agree that your contributions will be licensed under the Apache-2.0 license.
