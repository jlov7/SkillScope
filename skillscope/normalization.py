from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator, List, Optional

from .semconv import (
    AGENT_OPERATION,
    GENAI_MODEL,
    GENAI_OPERATION,
    GENAI_TOKEN_USAGE,
    GENAI_TOOL_CALL_ARGUMENTS,
    GENAI_TOOL_CALL_ID,
    GENAI_TOOL_CALL_RESULT,
    GENAI_TOOL_NAME,
    GENAI_USAGE_INPUT,
    GENAI_USAGE_OUTPUT,
    SKILL_NAME,
    skill_attrs,
)

GENAI_AGENT_INVOKE = "gen_ai.agent.invoke"
GENAI_TOOL_EXECUTE = "gen_ai.tool.execute"
SKILLSCOPE_SOURCE_FORMAT = "skillscope.source_format"
SKILLSCOPE_TRACE_ID = "skillscope.trace_id"
SKILLSCOPE_RUN_ID = "skillscope.run_id"
SKILLSCOPE_EVENT_ID = "skillscope.event_id"
SKILLSCOPE_EPISODE_ID = "skillscope.episode_id"
SKILLSCOPE_STEP_INDEX = "skillscope.step_idx"
SKILLSCOPE_SCOPE = "skillscope.scopes"
SKILLSCOPE_FILES = "skillscope.files_touched"
SKILLSCOPE_RESOURCES = "skillscope.resources"
SKILLSCOPE_POLICY = "skillscope.policy_decision"


def iter_paths(path: Path) -> Iterator[Path]:
    if path.is_dir():
        for child in sorted(path.rglob("*")):
            if child.is_file() and child.suffix in {".json", ".jsonl", ".ndjson"}:
                yield child
    else:
        yield path


def safe_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_events(events: Iterable[dict]) -> List[dict]:
    normalized: List[dict] = []
    for event in events:
        normalized.append(normalize_event(event))
    return normalized


def normalize_event(event: dict) -> dict:
    if _is_branchlab_event(event):
        return _normalize_branchlab_event(event)
    if _is_skillchain_event(event):
        return _normalize_skillchain_event(event)
    if _is_otel_span_event(event):
        return _normalize_otel_span_event(event)
    return _normalize_skillscope_event(event)


def _is_branchlab_event(event: dict) -> bool:
    return str(event.get("schema", "")).startswith("branchlab.trace.")


def _is_skillchain_event(event: dict) -> bool:
    return event.get("type") in {"metadata", "step"} and (
        "trace_id" in event or "episode_id" in event or "step_idx" in event
    )


def _is_otel_span_event(event: dict) -> bool:
    return "attributes" in event or "start_time" in event or "span_id" in event


def _base_output(event: dict, *, event_name: str, attrs: dict, metadata: dict) -> dict:
    return {
        "ts": event.get("ts") or event.get("time") or event.get("start_time"),
        "event": event_name,
        "attrs": attrs,
        "metadata": metadata,
    }


def _with_canonical_skill_attrs(
    attrs: dict[str, Any],
    event: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    for key, value in metadata.items():
        if key.startswith(("skill.", "skillscope.")) and key not in attrs:
            attrs[key] = value

    input_tokens = safe_int(
        event.get("input_tokens")
        or attrs.get(GENAI_USAGE_INPUT)
        or attrs.get("gen_ai.usage.prompt_tokens")
        or attrs.get("token.approx_in")
    )
    output_tokens = safe_int(
        event.get("output_tokens")
        or attrs.get(GENAI_USAGE_OUTPUT)
        or attrs.get("gen_ai.usage.completion_tokens")
        or attrs.get("token.approx_out")
    )
    legacy_tokens = safe_int(event.get("token_usage") or attrs.get(GENAI_TOKEN_USAGE))

    if not attrs.get(SKILL_NAME):
        attrs = skill_attrs(
            name=attrs.get("skill.name") or event.get("skill", "unknown"),
            version=attrs.get("skill.version") or event.get("version"),
            description=attrs.get("skill.description") or event.get("description"),
            files=_coerce_list(attrs.get("skill.files")) or event.get("files") or [],
            policy_required=attrs.get("skill.policy_required") or bool(event.get("policy_required", False)),
            progressive_level=attrs.get("skill.progressive_level") or event.get("progressive_level", "referenced"),
            model=event.get("model") or attrs.get(GENAI_MODEL),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            token_usage=legacy_tokens,
            operation=event.get("operation") or attrs.get(GENAI_OPERATION),
            agent_operation=event.get("agent_operation") or attrs.get(AGENT_OPERATION),
        ) | attrs
    else:
        canonical = skill_attrs(name=str(attrs.get(SKILL_NAME)))
        canonical.update(attrs)
        if input_tokens is not None:
            canonical[GENAI_USAGE_INPUT] = input_tokens
        if output_tokens is not None:
            canonical[GENAI_USAGE_OUTPUT] = output_tokens
        if legacy_tokens is not None:
            canonical[GENAI_TOKEN_USAGE] = legacy_tokens
        attrs = canonical

    if legacy_tokens is None and (input_tokens is not None or output_tokens is not None):
        attrs[GENAI_TOKEN_USAGE] = (input_tokens or 0) + (output_tokens or 0)
    return attrs


def _normalize_skillscope_event(event: dict) -> dict:
    attrs = dict(event.get("attrs", {}) or {})
    metadata = dict(event.get("metadata", {}) or {})
    attrs = _with_canonical_skill_attrs(attrs, event, metadata)
    return _base_output(event, event_name=str(event.get("event", "span")), attrs=attrs, metadata=metadata)


def _normalize_branchlab_event(event: dict) -> dict:
    data = dict(event.get("data", {}) or {})
    meta = dict(event.get("meta", {}) or {})
    event_type = str(event.get("type", "event"))
    attrs: dict[str, Any] = {
        SKILLSCOPE_SOURCE_FORMAT: "branchlab.trace",
        SKILLSCOPE_RUN_ID: event.get("run_id", ""),
        SKILLSCOPE_EVENT_ID: event.get("event_id", ""),
        GENAI_OPERATION: event_type,
        GENAI_MODEL: meta.get("model", ""),
    }
    if event_type == "tool.request":
        attrs[GENAI_OPERATION] = GENAI_TOOL_EXECUTE
        attrs[GENAI_TOOL_NAME] = data.get("tool") or meta.get("tool") or ""
        attrs[GENAI_TOOL_CALL_ID] = data.get("call_id", "")
        if "args" in data:
            attrs[GENAI_TOOL_CALL_ARGUMENTS] = json.dumps(data["args"], sort_keys=True)
    elif event_type == "tool.response":
        attrs[GENAI_OPERATION] = GENAI_TOOL_EXECUTE
        attrs[GENAI_TOOL_NAME] = data.get("tool") or meta.get("tool") or ""
        attrs[GENAI_TOOL_CALL_ID] = data.get("call_id", "")
        if "result" in data:
            attrs[GENAI_TOOL_CALL_RESULT] = json.dumps(data["result"], sort_keys=True)
    elif event_type in {"llm.request", "llm.response"}:
        attrs[GENAI_OPERATION] = GENAI_AGENT_INVOKE
        attrs[GENAI_TOOL_CALL_ID] = data.get("call_id", "")
    elif event_type.startswith("memory."):
        attrs[SKILLSCOPE_RESOURCES] = "memory"

    if meta.get("tokens_in") is not None:
        attrs[GENAI_USAGE_INPUT] = meta.get("tokens_in")
    if meta.get("tokens_out") is not None:
        attrs[GENAI_USAGE_OUTPUT] = meta.get("tokens_out")
    attrs = _with_canonical_skill_attrs(attrs, event, meta)
    return _base_output(event, event_name=event_type, attrs=attrs, metadata=meta)


def _normalize_skillchain_event(event: dict) -> dict:
    event_type = str(event.get("type", "event"))
    attrs: dict[str, Any] = {
        SKILLSCOPE_SOURCE_FORMAT: "skillchain.trace",
        SKILLSCOPE_TRACE_ID: event.get("trace_id", ""),
        SKILLSCOPE_EPISODE_ID: event.get("episode_id", ""),
        GENAI_OPERATION: event.get("kind", event_type),
    }
    if event_type == "step":
        attrs[SKILLSCOPE_STEP_INDEX] = event.get("step_idx", 0)
        if event.get("kind") == "tool" and event.get("tool_name"):
            attrs[GENAI_OPERATION] = GENAI_TOOL_EXECUTE
            attrs[GENAI_TOOL_NAME] = event.get("tool_name")
            if event.get("input") is not None:
                attrs[GENAI_TOOL_CALL_ARGUMENTS] = json.dumps(event["input"], sort_keys=True)
            if event.get("output") is not None:
                attrs[GENAI_TOOL_CALL_RESULT] = json.dumps(event["output"], sort_keys=True)
        elif event.get("kind") in {"llm", "decision"}:
            attrs[GENAI_OPERATION] = GENAI_AGENT_INVOKE
    metadata = {k: v for k, v in event.items() if k not in {"input", "output", "content"}}
    attrs = _with_canonical_skill_attrs(attrs, event, metadata)
    return _base_output(event, event_name=event_type, attrs=attrs, metadata=metadata)


def _normalize_otel_span_event(event: dict) -> dict:
    attrs = dict(event.get("attributes", {}) or event.get("attrs", {}) or {})
    name = str(event.get("name", attrs.get(GENAI_OPERATION, "span")))
    if name in {GENAI_AGENT_INVOKE, GENAI_TOOL_EXECUTE}:
        attrs[GENAI_OPERATION] = name
    elif "agent.role" in attrs:
        attrs[GENAI_OPERATION] = name
        attrs[AGENT_OPERATION] = attrs.get("agent.role")

    if event.get("trace_id") is not None:
        attrs[SKILLSCOPE_TRACE_ID] = str(event["trace_id"])
    if event.get("span_id") is not None:
        attrs[SKILLSCOPE_EVENT_ID] = str(event["span_id"])
    if attrs.get("tool.scope") or attrs.get("tool.scopes") or attrs.get("gen_ai.tool.scope"):
        attrs[SKILLSCOPE_SCOPE] = attrs.get("tool.scopes") or attrs.get("tool.scope") or attrs.get("gen_ai.tool.scope")
    if attrs.get("file.path") or attrs.get("files.touched"):
        attrs[SKILLSCOPE_FILES] = attrs.get("files.touched") or attrs.get("file.path")

    metadata = {
        SKILLSCOPE_SOURCE_FORMAT: "otel.span",
        "span.name": name,
    }
    attrs[SKILLSCOPE_SOURCE_FORMAT] = "otel.span"
    attrs = _with_canonical_skill_attrs(attrs, event, metadata)
    return _base_output(event, event_name=name, attrs=attrs, metadata=metadata)


def _coerce_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def read_input(path: Path | None) -> str:
    if path:
        return path.read_text(encoding="utf-8")
    return sys.stdin.read()


def detect_format(content: str, input_format: str) -> str:
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


def parse_json_content(content: str) -> List[dict]:
    data = json.loads(content)
    if isinstance(data, list):
        return [dict(item) for item in data]
    if isinstance(data, dict):
        return [data]
    raise ValueError("Unsupported JSON payload")


def parse_jsonl_content(content: str) -> List[dict]:
    events: List[dict] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            events.append(json.loads(stripped))
    return events


def anthropic_messages_to_events(payload: dict) -> List[dict]:
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
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        events[-1]["attrs"][GENAI_USAGE_INPUT] = input_tokens
        events[-1]["attrs"][GENAI_USAGE_OUTPUT] = output_tokens
        events[-1]["attrs"][GENAI_TOKEN_USAGE] = input_tokens + output_tokens
    return events


def load_events_from_source(path: Path | None, input_format: str) -> List[dict]:
    if path and path.is_dir():
        aggregate: List[dict] = []
        for child in iter_paths(path):
            aggregate.extend(load_events_from_source(child, input_format))
        return aggregate
    content = read_input(path)
    detected = detect_format(content, input_format)
    if detected == "anthropic":
        return anthropic_messages_to_events(json.loads(content))
    if detected == "jsonl":
        return normalize_events(parse_jsonl_content(content))
    return normalize_events(parse_json_content(content))
