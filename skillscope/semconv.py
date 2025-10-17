# OpenTelemetry helpers for Skills — extends GenAI + Agent semconv
from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, MutableMapping

# Core GenAI/Agent attribute keys (subset; see OTel specs)
GENAI_MODEL = "gen_ai.request.model"  # string
GENAI_TOKEN_USAGE = "gen_ai.client.token.usage"  # int
AGENT_OPERATION = "gen_ai.agent.operation"  # string, e.g., "plan"|"act"|"tool"

# Skill-specific attributes (proposed extension)
SKILL_NAME = "skill.name"
SKILL_VERSION = "skill.version"
SKILL_FILES = "skill.files"  # comma-joined string for portability
SKILL_FILES_COUNT = "skill.files_loaded_count"
SKILL_POLICY_REQUIRED = "skill.policy_required"  # bool
SKILL_PROGRESSIVE_LEVEL = "skill.progressive_level"  # "metadata"|"referenced"|"eager"

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
    files: Iterable[str] | None = None,
    policy_required: bool = False,
    progressive_level: str = DEFAULT_PROGRESSIVE_LEVEL,
    model: str | None = None,
    token_usage: int | None = None,
    agent_operation: str | None = None,
) -> Dict[str, Any]:
    """Return a dictionary of semantic-convention attributes for a skill span."""
    normalized_files = _normalize_files(files)
    return {
        SKILL_NAME: name,
        SKILL_VERSION: version or "",
        SKILL_FILES: ",".join(normalized_files),
        SKILL_FILES_COUNT: len(normalized_files),
        SKILL_POLICY_REQUIRED: bool(policy_required),
        SKILL_PROGRESSIVE_LEVEL: progressive_level,
        GENAI_MODEL: model or "",
        GENAI_TOKEN_USAGE: int(token_usage or 0),
        AGENT_OPERATION: agent_operation or "",
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

