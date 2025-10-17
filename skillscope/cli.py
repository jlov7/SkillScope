from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Iterator, List, Mapping, Sequence

from . import __version__
from .example_data import demo_skill_events, load_demo_skill_summary
from .exporters import configure_exporters, export_events
from .semconv import GENAI_MODEL, GENAI_TOKEN_USAGE, SKILL_NAME, skill_attrs


def _iter_paths(path: Path) -> Iterator[Path]:
    if path.is_dir():
        for child in sorted(path.rglob("*")):
            if child.is_file() and child.suffix in {".json", ".jsonl", ".ndjson"}:
                yield child
    else:
        yield path


def _normalize_events(events: Iterable[dict]) -> List[dict]:
    normalized: List[dict] = []
    for event in events:
        attrs = event.get("attrs", {}).copy()
        metadata = event.get("metadata") or {}
        if metadata:
            attrs.update({k: v for k, v in metadata.items() if k.startswith("skill.")})

        if not attrs.get(SKILL_NAME):
            attrs = skill_attrs(
                name=attrs.get("skill.name") or event.get("skill", "unknown"),
                version=attrs.get("skill.version") or event.get("version"),
                files=attrs.get("skill.files", "").split(",") if attrs.get("skill.files") else event.get("files") or [],
                policy_required=attrs.get("skill.policy_required") or bool(event.get("policy_required", False)),
                progressive_level=attrs.get("skill.progressive_level") or event.get("progressive_level", "referenced"),
                model=event.get("model"),
                token_usage=event.get("token_usage") or attrs.get(GENAI_TOKEN_USAGE),
                agent_operation=event.get("agent_operation"),
            )
        else:
            canonical = skill_attrs(name=attrs.get(SKILL_NAME))
            canonical.update(attrs)
            attrs = canonical

        normalized.append(
            {
                "ts": event.get("ts"),
                "event": event.get("event", "span"),
                "attrs": attrs,
                "metadata": metadata,
            }
        )
    return normalized


def _read_input(path: Path | None) -> str:
    if path:
        return path.read_text(encoding="utf-8")
    return sys.stdin.read()


def _detect_format(content: str, input_format: str) -> str:
    if input_format != "auto":
        return input_format
    snippet = content.lstrip()
    if not snippet:
        return "jsonl"
    if snippet.startswith("{"):
        try:
            obj = json.loads(content)
        except json.JSONDecodeError:
            return "jsonl"
        if isinstance(obj, dict) and "messages" in obj:
            return "anthropic"
        if isinstance(obj, list):
            return "json"
        return "json"
    return "jsonl"


def _parse_json_content(content: str) -> List[dict]:
    data = json.loads(content)
    if isinstance(data, list):
        return [dict(item) for item in data]
    if isinstance(data, dict):
        return [data]
    raise ValueError("Unsupported JSON payload")


def _parse_jsonl_content(content: str) -> List[dict]:
    events: List[dict] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            events.append(json.loads(stripped))
    return events


def _anthropic_messages_to_events(payload: dict) -> List[dict]:
    base_attrs = {k: v for k, v in (payload.get("metadata") or {}).items() if k.startswith("skill.")}
    events: List[dict] = []
    for message in payload.get("messages") or []:
        per_message = dict(base_attrs)
        metadata = message.get("metadata") or {}
        per_message.update({k: v for k, v in metadata.items() if k.startswith("skill.")})
        events.append(
            {
                "ts": message.get("ts") or payload.get("ts"),
                "event": f"message.{message.get('role', 'unknown')}",
                "attrs": per_message,
                "metadata": metadata,
            }
        )
    usage = payload.get("usage")
    if usage and events:
        token_usage = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        events[-1]["attrs"][GENAI_TOKEN_USAGE] = token_usage
    return events


def load_events_from_source(path: Path | None, input_format: str) -> List[dict]:
    if path and path.is_dir():
        aggregate: List[dict] = []
        for child in _iter_paths(path):
            aggregate.extend(load_events_from_source(child, input_format))
        return aggregate
    content = _read_input(path)
    detected = _detect_format(content, input_format)
    if detected == "anthropic":
        return _anthropic_messages_to_events(json.loads(content))
    if detected == "jsonl":
        return _parse_jsonl_content(content)
    return _parse_json_content(content)


def _summarize_events(events: Iterable[Mapping]) -> dict:
    totals = {"total_events": 0, "total_tokens": 0}
    per_skill: dict[str, dict] = {}
    for event in events:
        totals["total_events"] += 1
        attrs = event.get("attrs", {})
        skill = attrs.get(SKILL_NAME, "") or attrs.get("skill", "unknown")
        skill_entry = per_skill.setdefault(
            skill,
            {
                "events": 0,
                "completions": 0,
                "policy_required": 0,
                "tokens": 0,
                "token_samples": 0,
                "files": set(),
                "models": set(),
                "progressive_levels": set(),
            },
        )
        skill_entry["events"] += 1

        event_name = str(event.get("event", ""))
        if event_name.startswith("end") or event_name == "anthropic_call":
            skill_entry["completions"] += 1
        if attrs.get("skill.policy_required"):
            skill_entry["policy_required"] += 1
        if attrs.get("skill.files"):
            files = [f.strip() for f in str(attrs["skill.files"]).split(",") if f.strip()]
            skill_entry["files"].update(files)
        if attrs.get("skill.progressive_level"):
            skill_entry["progressive_levels"].add(str(attrs["skill.progressive_level"]))
        if attrs.get(GENAI_TOKEN_USAGE) is not None:
            try:
                tokens = int(attrs[GENAI_TOKEN_USAGE])
            except (TypeError, ValueError):
                tokens = 0
            skill_entry["tokens"] += tokens
            skill_entry["token_samples"] += 1
            totals["total_tokens"] += tokens
        model = attrs.get(GENAI_MODEL)
        if model:
            skill_entry["models"].add(str(model))

    skills_summary: dict[str, dict] = {}
    for skill, data in per_skill.items():
        calls = data["completions"] or data["events"]
        policy_required = min(data["policy_required"], calls)
        avg_tokens = data["tokens"] / data["token_samples"] if data["token_samples"] else 0.0
        policy_rate = (policy_required / calls) if calls else 0.0
        skills_summary[skill] = {
            "events": data["events"],
            "calls": calls,
            "policy_required": policy_required,
            "policy_rate": policy_rate,
            "tokens_total": data["tokens"],
            "tokens_average": avg_tokens,
            "files": sorted(data["files"])[:10],
            "models": sorted(data["models"]),
            "progressive_levels": sorted(data["progressive_levels"]),
        }

    totals["total_skills"] = len(skills_summary)
    totals["skills"] = skills_summary
    return totals


def _format_summary_table(summary: dict) -> str:
    if not summary.get("skills"):
        return "No skill events found."

    lines = []
    lines.append("SkillScope Summary")
    lines.append("=" * 18)
    lines.append(f"Total events: {summary['total_events']}")
    lines.append(f"Skills observed: {summary['total_skills']}")
    lines.append(f"Recorded tokens: {summary['total_tokens']}")
    lines.append("")
    header = f"{'Skill':32} {'Calls':>7} {'Avg Tokens':>11} {'Policy %':>9} {'Top Files':<30} {'Models':<20}"
    lines.append(header)
    lines.append("-" * len(header))

    for skill, data in sorted(summary["skills"].items(), key=lambda item: item[0].lower()):
        calls = data["calls"]
        avg_tokens = data["tokens_average"]
        policy_rate = data["policy_rate"] * 100
        files_preview = ", ".join(data["files"])[:30] or "—"
        models_preview = ", ".join(data["models"])[:20] or "—"
        lines.append(
            f"{skill[:32]:32} "
            f"{calls:7d} "
            f"{avg_tokens:11.1f} "
            f"{policy_rate:9.1f} "
            f"{files_preview:<30} "
            f"{models_preview:<20}"
        )

    return "\n".join(lines)


def cmd_emit(args: argparse.Namespace) -> int:
    if args.demo:
        events = demo_skill_events()
    else:
        input_path = Path(args.input) if args.input else None
        events = load_events_from_source(input_path, args.input_format)
        events = _normalize_events(events)

    exporters = configure_exporters(stream=sys.stdout if args.stdout else False)
    results = export_events(events, exporters)
    errors = [res for res in results if res.get("status") == "error"]
    if errors:
        for err in errors:
            print(f"[skillscope] exporter failed: {err}", file=sys.stderr)
        return 1
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    path = Path(args.path)
    events = load_events_from_source(path, args.input_format)
    events = _normalize_events(events)
    exporters = configure_exporters(stream=False)

    if args.to == "ndjson":
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with out_path.open("w", encoding="utf-8") as handle:
                for event in events:
                    handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        else:
            for event in events:
                print(json.dumps(event, ensure_ascii=False))
    elif args.to == "otlp":
        results = export_events(events, exporters)
        errors = [res for res in results if res.get("status") == "error"]
        if errors:
            for err in errors:
                print(f"[skillscope] exporter failed: {err}", file=sys.stderr)
            return 1
    else:
        raise ValueError(f"Unsupported export format: {args.to}")
    return 0


def cmd_demo(_: argparse.Namespace) -> int:
    summary = load_demo_skill_summary()
    print(summary)
    return 0


def _prepare_summary_for_json(summary: dict) -> dict:
    exportable = {
        "total_events": summary.get("total_events", 0),
        "total_skills": summary.get("total_skills", 0),
        "total_tokens": summary.get("total_tokens", 0),
        "skills": [],
    }
    for skill, data in sorted(summary.get("skills", {}).items(), key=lambda item: item[0].lower()):
        exportable["skills"].append({"skill": skill, **data})
    return exportable


def cmd_analyze(args: argparse.Namespace) -> int:
    if getattr(args, "demo", False):
        events = _normalize_events(demo_skill_events())
    else:
        target_path = Path(args.path) if args.path else None
        events = load_events_from_source(target_path, args.input_format)
        events = _normalize_events(events)
    summary = _summarize_events(events)
    if args.format == "json":
        print(json.dumps(_prepare_summary_for_json(summary), ensure_ascii=False, indent=2))
    else:
        print(_format_summary_table(summary))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skillscope", description="SkillScope observability toolkit.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    emit_parser = subparsers.add_parser("emit", help="Emit skill observability events.")
    emit_parser.add_argument("--demo", action="store_true", help="Emit synthetic demo events.")
    emit_parser.add_argument(
        "--stdout",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Print events to stdout (disable with --no-stdout).",
    )
    emit_parser.add_argument("--input", help="Path to an input file containing events.")
    emit_parser.add_argument(
        "--input-format",
        choices=("auto", "json", "jsonl", "anthropic"),
        default="auto",
        help="Format for --input or stdin when emitting custom events.",
    )
    emit_parser.set_defaults(func=cmd_emit)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest events and re-export in a normalized format.")
    ingest_parser.add_argument("path", help="Path to JSONL events.")
    ingest_parser.add_argument("--to", choices=("otlp", "ndjson"), default="ndjson", help="Export destination.")
    ingest_parser.add_argument("--output", help="File path for ndjson output.")
    ingest_parser.add_argument(
        "--input-format",
        choices=("auto", "json", "jsonl", "anthropic"),
        default="auto",
        help="Source format autodetection.",
    )
    ingest_parser.set_defaults(func=cmd_ingest)

    demo_parser = subparsers.add_parser("demo", help="Show demo skill documentation.")
    demo_parser.set_defaults(func=cmd_demo)

    analyze_parser = subparsers.add_parser("analyze", help="Summarize skill events for quick reports.")
    analyze_parser.add_argument("path", nargs="?", help="Path to events file or directory (defaults to stdin).")
    analyze_parser.add_argument(
        "--input-format",
        choices=("auto", "json", "jsonl", "anthropic"),
        default="auto",
        help="Format for the input events.",
    )
    analyze_parser.add_argument("--demo", action="store_true", help="Summarize bundled demo events.")
    analyze_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format for the summary.",
    )
    analyze_parser.set_defaults(func=cmd_analyze)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 1
    return func(args)


if __name__ == "__main__":
    raise SystemExit(main())
