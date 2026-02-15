# Questions

## Resolved Decisions

- Vercel deployment target: `web/` project root with static export output (`out/`).
- Visual system: continue the current tokenized palette and typography in the web UI.
- Upload constraints: keep 8MB max file size and support `json`, `jsonl`, `ndjson`, and Anthropic JSON payloads.
- Demo publishing: plan for a public demo URL, with no user-upload persistence.
- Next.js warning handling: set `turbopack.root` to `process.cwd()` in `web/next.config.ts`.

## Notes

- Python verification requires `uv sync --all-extras` because `pytest` is in optional `dev` extras.
