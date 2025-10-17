from __future__ import annotations

import asyncio
import contextlib
import json
import os
import threading
import time
from contextvars import ContextVar
from typing import Any, Callable, Dict, Iterable, Iterator, Optional, TypeVar

from .example_data import attrs_to_summary

from .semconv import (
    DEFAULT_PROGRESSIVE_LEVEL,
    GENAI_MODEL,
    GENAI_TOKEN_USAGE,
    SKILL_NAME,
    SKILL_PROGRESSIVE_LEVEL,
    skill_attrs,
)


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
    files: Optional[Iterable[str]] = None,
    policy_required: bool = False,
    progressive_level: str = DEFAULT_PROGRESSIVE_LEVEL,
    model: Optional[str] = None,
    agent_operation: Optional[str] = None,
    extra_attrs: Optional[Dict[str, Any]] = None,
) -> Iterator[Dict]:
    """Context manager that records a span representing intended skill usage.

    Parameters mirror the semantic convention and permit caller-provided
    ``extra_attrs`` for custom tagging (e.g. team/environment).
    """

    attrs = skill_attrs(
        name=name,
        version=version,
        files=files,
        policy_required=policy_required,
        progressive_level=progressive_level,
        model=model,
        agent_operation=agent_operation,
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
    files: Optional[Iterable[str]] = None,
    policy_required: bool = False,
    progressive_level: str = DEFAULT_PROGRESSIVE_LEVEL,
    model: Optional[str] = None,
    agent_operation: Optional[str] = None,
    extra_attrs: Optional[Dict[str, Any]] = None,
) -> Callable[[F], F]:
    """Decorator that wraps a function within :func:`use_skill`."""

    def decorator(func: F) -> F:
        def wrapper(*func_args, **func_kwargs):
            with use_skill(
                name=name,
                version=version,
                files=files,
                policy_required=policy_required,
                progressive_level=progressive_level,
                model=model,
                agent_operation=agent_operation,
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
        token_estimator: Optional[Callable[[dict], int]] = None,
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
                span_handle["attrs"][GENAI_TOKEN_USAGE] = (
                    usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                )
            return response

        mock_response = {
            "mock": True,
            "kwargs": kwargs,
            "note": "Anthropic SDK or key not available",
        }
        if span_handle:
            span_handle["attrs"][GENAI_MODEL] = kwargs.get("model", "")
            estimated = self._token_estimator(kwargs)
            if estimated is not None:
                span_handle["attrs"][GENAI_TOKEN_USAGE] = estimated
        return mock_response


def default_token_estimator(request: dict) -> int:
    """Very rough token heuristic: ~4 characters per token on text payloads."""

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
    estimated = round(text_length / 4) + int(max_tokens)
    return estimated if estimated > 0 else None


async def gather_with_skill(skill_kwargs: dict, coroutines: Iterable[asyncio.Future]) -> list[Any]:
    """Helper to wrap ``asyncio.gather`` with a shared skill span."""

    async with use_skill_async(**skill_kwargs):
        return await asyncio.gather(*coroutines)
