# SkillScope Help

SkillScope is research-only software. The web UI runs locally in your browser and does not upload data.

## Web UI

1. `pnpm install` in `web/`
1. `pnpm dev`
1. Visit `http://localhost:3000`
1. Upload `.json`, `.jsonl`, or `.ndjson` (including Anthropic message JSON payloads)

### Limits

- Maximum upload size: `8MB` per file.
- Analysis runs in-browser only; no uploaded file is sent to a backend.

## CLI

Use `skillscope emit --demo` or `skillscope ingest` to generate events, then upload JSON/JSONL to the web UI.
