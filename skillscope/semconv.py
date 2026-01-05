# OpenTelemetry helpers for Skills — extends GenAI + Agent semconv
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Mapping, MutableMapping

# Core GenAI/Agent attribute keys (subset; see OTel specs)
GENAI_MODEL = "gen_ai.request.model"  # string
GENAI_TOKEN_USAGE = "gen_ai.client.token.usage"  # int (metrics compatibility)
GENAI_USAGE_INPUT = "gen_ai.usage.input_tokens"  # int
GENAI_USAGE_OUTPUT = "gen_ai.usage.output_tokens"  # int
GENAI_OPERATION = "gen_ai.operation.name"  # string
AGENT_OPERATION = "gen_ai.agent.operation"  # legacy string, e.g., "plan"|"act"|"tool"
GENAI_TOOL_NAME = "gen_ai.tool.name"
GENAI_TOOL_TYPE = "gen_ai.tool.type"
GENAI_TOOL_CALL_ID = "gen_ai.tool.call.id"
GENAI_TOOL_DESCRIPTION = "gen_ai.tool.description"
GENAI_TOOL_CALL_ARGUMENTS = "gen_ai.tool.call.arguments"
GENAI_TOOL_CALL_RESULT = "gen_ai.tool.call.result"

# Skill-specific attributes (proposed extension)
SKILL_NAME = "skill.name"
SKILL_VERSION = "skill.version"
SKILL_DESCRIPTION = "skill.description"
SKILL_FILES = "skill.files"  # comma-joined string for portability
SKILL_FILES_COUNT = "skill.files_loaded_count"
SKILL_POLICY_REQUIRED = "skill.policy_required"  # bool
SKILL_PROGRESSIVE_LEVEL = "skill.progressive_level"  # "metadata"|"referenced"|"eager"
SKILL_LICENSE = "skill.license"
SKILL_COMPATIBILITY = "skill.compatibility"
SKILL_ALLOWED_TOOLS = "skill.allowed_tools"
SKILL_METADATA = "skill.metadata"

DEFAULT_PROGRESSIVE_LEVEL = "referenced"


def _normalize_files(files: Iterable[str] | None) -> list[str]:
    if not files:
        return []
    if isinstance(files, list):
        return files
    return [str(item) for item in files]


def skill_attrs(
    name: str,
    version: str | None = None,
    description: str | None = None,
    files: Iterable[str] | None = None,
    policy_required: bool = False,
    progressive_level: str = DEFAULT_PROGRESSIVE_LEVEL,
    model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    token_usage: int | None = None,
    operation: str | None = None,
    agent_operation: str | None = None,
    license: str | None = None,
    compatibility: str | None = None,
    allowed_tools: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Return a dictionary of semantic-convention attributes for a skill span."""
    normalized_files = _normalize_files(files)
    input_value = int(input_tokens or 0)
    output_value = int(output_tokens or 0)
    legacy_total = int(token_usage) if token_usage is not None else input_value + output_value
    metadata_value = ""
    if metadata:
        metadata_value = json.dumps(
            {str(key): str(value) for key, value in metadata.items()},
            ensure_ascii=False,
            sort_keys=True,
        )
    return {
        SKILL_NAME: name,
        SKILL_VERSION: version or "",
        SKILL_DESCRIPTION: description or "",
        SKILL_FILES: ",".join(normalized_files),
        SKILL_FILES_COUNT: len(normalized_files),
        SKILL_POLICY_REQUIRED: bool(policy_required),
        SKILL_PROGRESSIVE_LEVEL: progressive_level,
        GENAI_MODEL: model or "",
        GENAI_USAGE_INPUT: input_value,
        GENAI_USAGE_OUTPUT: output_value,
        GENAI_TOKEN_USAGE: legacy_total,
        GENAI_OPERATION: operation or agent_operation or "",
        AGENT_OPERATION: agent_operation or "",
        SKILL_LICENSE: license or "",
        SKILL_COMPATIBILITY: compatibility or "",
        SKILL_ALLOWED_TOOLS: allowed_tools or "",
        SKILL_METADATA: metadata_value,
    }


def apply_skill_attrs(
    target: MutableMapping[str, Any],
    attrs: Mapping[str, Any],
) -> MutableMapping[str, Any]:
    """Mutate *target* to include skill semantic attributes."""
    for key, value in attrs.items():
        target[key] = value
    return target


def start_span(recorder, attrs: Mapping[str, Any]) -> Any:
    """Helper to start a span on a recorder-like object."""
    return recorder.start(dict(attrs))


def end_span(recorder, span_handle: Any, attrs: Mapping[str, Any] | None = None) -> Any:
    """Helper to finish a span, optionally updating attributes."""
    if attrs is None:
        attrs = {}
    if hasattr(span_handle, "update"):
        span_handle.update(attrs)
    payload = dict(getattr(span_handle, "attrs", {}))
    payload.update(attrs)
    return recorder.end(payload)
