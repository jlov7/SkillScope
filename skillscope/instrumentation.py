from __future__ import annotations

import asyncio
import contextlib
import json
import os
import subprocess
import threading
import time
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, Optional, TypeVar

from .example_data import attrs_to_summary
from .semconv import (
    DEFAULT_PROGRESSIVE_LEVEL,
    GENAI_OPERATION,
    GENAI_MODEL,
    GENAI_TOKEN_USAGE,
    GENAI_USAGE_INPUT,
    GENAI_USAGE_OUTPUT,
    GENAI_TOOL_CALL_ARGUMENTS,
    GENAI_TOOL_CALL_ID,
    GENAI_TOOL_CALL_RESULT,
    GENAI_TOOL_DESCRIPTION,
    GENAI_TOOL_NAME,
    GENAI_TOOL_TYPE,
    skill_attrs,
)
from .skills import read_skill_metadata


class SpanRecorder:
    """Minimal span-like recorder (keeps us vendor-neutral)."""

    def __init__(self) -> None:
        self.events: list[dict] = []
        self._lock = threading.Lock()

    def start(self, attrs: Dict) -> Dict:
        evt = {"ts": time.time(), "event": "start", "attrs": dict(attrs)}
        with self._lock:
            self.events.append(evt)
        return {"attrs": dict(attrs), "start_ts": evt["ts"]}

    def end(self, attrs: Dict) -> Dict:
        evt = {"ts": time.time(), "event": "end", "attrs": dict(attrs)}
        with self._lock:
            self.events.append(evt)
        return evt

    def clear(self) -> None:
        with self._lock:
            self.events.clear()


RECORDER = SpanRecorder()

_CURRENT_SPAN: ContextVar[Optional[Dict]] = ContextVar("_CURRENT_SPAN", default=None)


@contextlib.contextmanager
def use_skill(
    name: str,
    version: Optional[str] = None,
    description: Optional[str] = None,
    files: Optional[Iterable[str]] = None,
    policy_required: bool = False,
    progressive_level: str = DEFAULT_PROGRESSIVE_LEVEL,
    model: Optional[str] = None,
    operation: Optional[str] = None,
    agent_operation: Optional[str] = None,
    license: Optional[str] = None,
    compatibility: Optional[str] = None,
    allowed_tools: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    extra_attrs: Optional[Dict[str, Any]] = None,
) -> Iterator[Dict]:
    """Context manager that records a span representing intended skill usage.

    Parameters mirror the semantic convention and permit caller-provided
    ``extra_attrs`` for custom tagging (e.g. team/environment).
    """

    attrs = skill_attrs(
        name=name,
        version=version,
        description=description,
        files=files,
        policy_required=policy_required,
        progressive_level=progressive_level,
        model=model,
        operation=operation,
        agent_operation=agent_operation,
        license=license,
        compatibility=compatibility,
        allowed_tools=allowed_tools,
        metadata=metadata,
    )
    if extra_attrs:
        for key, value in extra_attrs.items():
            attr_key = key if "." in key else f"skillscope.{key}"
            attrs[attr_key] = value

    span_handle = RECORDER.start(attrs)
    token = _CURRENT_SPAN.set(span_handle)
    try:
        yield span_handle["attrs"]
    finally:
        _CURRENT_SPAN.reset(token)
        RECORDER.end(span_handle["attrs"])


@contextlib.asynccontextmanager
async def use_skill_async(
    *args,
    **kwargs,
):
    """Async variant of :func:`use_skill` for coroutine workflows."""

    with use_skill(*args, **kwargs) as attrs:
        yield attrs


F = TypeVar("F", bound=Callable[..., Any])


def with_skill(
    name: str,
    *,
    version: Optional[str] = None,
    description: Optional[str] = None,
    files: Optional[Iterable[str]] = None,
    policy_required: bool = False,
    progressive_level: str = DEFAULT_PROGRESSIVE_LEVEL,
    model: Optional[str] = None,
    operation: Optional[str] = None,
    agent_operation: Optional[str] = None,
    license: Optional[str] = None,
    compatibility: Optional[str] = None,
    allowed_tools: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    extra_attrs: Optional[Dict[str, Any]] = None,
) -> Callable[[F], F]:
    """Decorator that wraps a function within :func:`use_skill`."""

    def decorator(func: F) -> F:
        def wrapper(*func_args, **func_kwargs):
            with use_skill(
                name=name,
                version=version,
                description=description,
                files=files,
                policy_required=policy_required,
                progressive_level=progressive_level,
                model=model,
                operation=operation,
                agent_operation=agent_operation,
                license=license,
                compatibility=compatibility,
                allowed_tools=allowed_tools,
                metadata=metadata,
                extra_attrs=extra_attrs,
            ):
                return func(*func_args, **func_kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


class AnthropicInstrumented:
    """Optional Anthropic wrapper that adds skill attributes when called inside use_skill()."""

    def __init__(
        self,
        *,
        token_estimator: Optional[Callable[[dict], Any]] = None,
        recorder: SpanRecorder | None = None,
    ) -> None:
        try:
            import anthropic  # type: ignore

            self._client = anthropic.Anthropic()
        except Exception:
            self._client = None
        self._token_estimator = token_estimator or default_token_estimator
        self._recorder = recorder or RECORDER

    def messages_create(self, **kwargs):
        span_handle = _CURRENT_SPAN.get()
        skill_context = dict(span_handle["attrs"]) if span_handle else {}
        metadata = kwargs.setdefault("metadata", {})
        for key, value in skill_context.items():
            if key.startswith("skill.") or key.startswith("skillscope."):
                metadata.setdefault(key, value)

        if os.getenv("SKILLSCOPE_CAPTURE") == "1":
            payload = {
                "ts": time.time(),
                "event": "anthropic_call",
                "attrs": skill_context,
                "request": attrs_to_summary(skill_context) | {
                    "model": kwargs.get("model"),
                    "max_tokens": kwargs.get("max_tokens"),
                },
            }
            print(json.dumps(payload, ensure_ascii=False))

        if span_handle:
            span_handle["attrs"][GENAI_MODEL] = kwargs.get("model", span_handle["attrs"].get(GENAI_MODEL, ""))

        if self._client and os.getenv("ANTHROPIC_API_KEY"):
            response = self._client.messages.create(**kwargs)
            usage = getattr(response, "usage", None)
            if isinstance(usage, dict) and span_handle:
                input_tokens = int(usage.get("input_tokens", 0))
                output_tokens = int(usage.get("output_tokens", 0))
                span_handle["attrs"][GENAI_USAGE_INPUT] = input_tokens
                span_handle["attrs"][GENAI_USAGE_OUTPUT] = output_tokens
                span_handle["attrs"][GENAI_TOKEN_USAGE] = input_tokens + output_tokens
            return response

        mock_response = {
            "mock": True,
            "kwargs": kwargs,
            "note": "Anthropic SDK or key not available",
        }
        if span_handle:
            span_handle["attrs"][GENAI_MODEL] = kwargs.get("model", "")
            input_tokens, output_tokens, total_tokens = _normalize_token_estimate(
                self._token_estimator(kwargs),
                kwargs,
            )
            span_handle["attrs"][GENAI_USAGE_INPUT] = input_tokens
            span_handle["attrs"][GENAI_USAGE_OUTPUT] = output_tokens
            span_handle["attrs"][GENAI_TOKEN_USAGE] = total_tokens
        return mock_response


def default_token_estimator(request: dict) -> int | None:
    """Very rough token heuristic: ~4 characters per token on text payloads."""
    input_tokens, output_tokens = estimate_token_usage(request)
    estimated = input_tokens + output_tokens
    return estimated if estimated > 0 else None


def estimate_token_usage(request: dict) -> tuple[int, int]:
    """Estimate input/output tokens for a request."""
    messages = request.get("messages") or []
    text_length = 0
    for message in messages:
        if isinstance(message, dict):
            content = message.get("content", "")
            if isinstance(content, str):
                text_length += len(content)
            elif isinstance(content, list):
                for chunk in content:
                    if isinstance(chunk, dict) and isinstance(chunk.get("text"), str):
                        text_length += len(chunk["text"])
        elif isinstance(message, str):
            text_length += len(message)

    max_tokens = request.get("max_tokens") or 0
    input_tokens = round(text_length / 4)
    output_tokens = int(max_tokens)
    return max(input_tokens, 0), max(output_tokens, 0)


def _normalize_token_estimate(estimate: Any, request: dict) -> tuple[int, int, int]:
    input_est, output_est = estimate_token_usage(request)
    if estimate is None:
        total = input_est + output_est
        return input_est, output_est, total
    if isinstance(estimate, dict):
        input_tokens = int(estimate.get("input_tokens") or estimate.get("input") or input_est)
        output_tokens = int(estimate.get("output_tokens") or estimate.get("output") or output_est)
        total = int(estimate.get("total_tokens") or (input_tokens + output_tokens))
        return input_tokens, output_tokens, total
    if isinstance(estimate, (tuple, list)) and len(estimate) >= 2:
        input_tokens = int(estimate[0])
        output_tokens = int(estimate[1])
        total = input_tokens + output_tokens
        return input_tokens, output_tokens, total
    if isinstance(estimate, (int, float)):
        total = int(estimate)
        input_tokens = min(total, input_est)
        output_tokens = max(0, total - input_tokens)
        return input_tokens, output_tokens, total
    total = input_est + output_est
    return input_est, output_est, total


@contextlib.contextmanager
def use_tool(
    name: str,
    *,
    tool_type: Optional[str] = None,
    call_id: Optional[str] = None,
    description: Optional[str] = None,
    arguments: Any = None,
    result: Any = None,
    operation: str = "execute_tool",
    include_skill_context: bool = True,
    extra_attrs: Optional[Dict[str, Any]] = None,
) -> Iterator[Dict]:
    """Context manager that records a tool execution span."""
    attrs: Dict[str, Any] = {
        GENAI_OPERATION: operation,
        GENAI_TOOL_NAME: name,
    }
    if tool_type:
        attrs[GENAI_TOOL_TYPE] = tool_type
    if call_id:
        attrs[GENAI_TOOL_CALL_ID] = call_id
    if description:
        attrs[GENAI_TOOL_DESCRIPTION] = description
    if arguments is not None:
        attrs[GENAI_TOOL_CALL_ARGUMENTS] = arguments
    if result is not None:
        attrs[GENAI_TOOL_CALL_RESULT] = result

    if include_skill_context:
        span_handle = _CURRENT_SPAN.get()
        if span_handle:
            for key, value in span_handle["attrs"].items():
                if key.startswith("skill.") or key.startswith("skillscope."):
                    attrs.setdefault(key, value)

    if extra_attrs:
        for key, value in extra_attrs.items():
            attr_key = key if "." in key else f"skillscope.{key}"
            attrs[attr_key] = value

    span_handle = RECORDER.start(attrs)
    try:
        yield span_handle["attrs"]
    finally:
        RECORDER.end(span_handle["attrs"])


def run_skill_script(
    script_path: str,
    *,
    args: Optional[Iterable[str]] = None,
    tool_name: Optional[str] = None,
    tool_type: str = "extension",
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    """Execute a skill script while recording a tool span."""
    path = Path(script_path)
    command = [str(path)]
    if args:
        command.extend(args)
    tool_label = tool_name or path.name
    with use_tool(
        name=tool_label,
        tool_type=tool_type,
        extra_attrs={"tool.path": str(path)},
    ):
        return subprocess.run(command, **kwargs)


@contextlib.contextmanager
def use_skill_from_path(
    skill_path: str,
    *,
    files: Optional[Iterable[str]] = None,
    policy_required: bool = False,
    progressive_level: str = DEFAULT_PROGRESSIVE_LEVEL,
    model: Optional[str] = None,
    operation: Optional[str] = None,
    agent_operation: Optional[str] = None,
    extra_attrs: Optional[Dict[str, Any]] = None,
) -> Iterator[Dict]:
    """Load SKILL.md frontmatter and record a skill span."""
    metadata = read_skill_metadata(skill_path)
    with use_skill(
        name=metadata.name,
        version=metadata.metadata.get("version"),
        description=metadata.description,
        files=files,
        policy_required=policy_required,
        progressive_level=progressive_level,
        model=model,
        operation=operation,
        agent_operation=agent_operation,
        license=metadata.license,
        compatibility=metadata.compatibility,
        allowed_tools=metadata.allowed_tools,
        metadata=metadata.metadata,
        extra_attrs=extra_attrs,
    ) as attrs:
        yield attrs


async def gather_with_skill(skill_kwargs: dict, coroutines: Iterable[asyncio.Future]) -> list[Any]:
    """Helper to wrap ``asyncio.gather`` with a shared skill span."""

    async with use_skill_async(**skill_kwargs):
        return await asyncio.gather(*coroutines)
