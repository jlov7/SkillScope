# Questions

## Open Decisions

- Vercel project name and deployment target (repo root vs `web/` subdirectory).
- Preferred brand assets (logo, color palette, type choices) for the web UI.
- Maximum upload size and supported formats beyond JSON/JSONL/Anthropic JSON.
- Whether to publish a public demo URL or keep the Vercel deployment private.

## Notes

- Baseline `uv run pytest` failed because `pytest` is only in `dev` extras. Will re-run after `uv sync --all-extras`.
