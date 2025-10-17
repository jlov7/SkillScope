from __future__ import annotations

import asyncio
import json

import pytest

from skillscope.instrumentation import (
    AnthropicInstrumented,
    RECORDER,
    default_token_estimator,
    gather_with_skill,
    use_skill,
    use_skill_async,
    with_skill,
)
from skillscope.semconv import GENAI_MODEL, GENAI_TOKEN_USAGE, SKILL_NAME


def setup_function(_) -> None:
    RECORDER.clear()


def test_use_skill_records_start_and_end_events():
    with use_skill(name="Telemetry Skill", files=["guide.md"]):
        pass

    assert len(RECORDER.events) == 2
    start_event, end_event = RECORDER.events
    assert start_event["event"] == "start"
    assert start_event["attrs"][SKILL_NAME] == "Telemetry Skill"
    assert end_event["event"] == "end"


def test_anthropic_wrapper_attaches_skill_metadata(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("SKILLSCOPE_CAPTURE", "1")
    client = AnthropicInstrumented()

    with use_skill(name="Capture Skill", files=["demo.txt"], extra_attrs={"env": "test"}):
        response = client.messages_create(model="claude-3-opus", max_tokens=16, messages=[])

    captured = capsys.readouterr().out.strip()
    payload = json.loads(captured)
    assert payload["attrs"][SKILL_NAME] == "Capture Skill"
    assert response["mock"] is True
    assert response["kwargs"]["metadata"]["skill.name"] == "Capture Skill"
    assert response["kwargs"]["metadata"]["skillscope.env"] == "test"


def test_anthropic_updates_span_model_attribute(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = AnthropicInstrumented()

    with use_skill(name="Model Skill") as attrs:
        client.messages_create(model="claude-3-sonnet", max_tokens=8, messages=[])
        assert attrs[GENAI_MODEL] == "claude-3-sonnet"
        assert attrs[GENAI_TOKEN_USAGE] > 0


def test_with_skill_decorator_applies_context():
    calls = []

    @with_skill(name="Decorated Skill")
    def decorated(x: int) -> int:
        calls.append(x)
        span_attrs = RECORDER.events[-1]["attrs"]
        assert span_attrs[SKILL_NAME] == "Decorated Skill"
        return x * 2

    result = decorated(3)
    assert result == 6
    assert calls == [3]


@pytest.mark.asyncio
async def test_use_skill_async():
    async with use_skill_async(name="Async Skill"):
        await asyncio.sleep(0)
    events = [event for event in RECORDER.events if event["attrs"][SKILL_NAME] == "Async Skill"]
    assert len(events) == 2


def test_default_token_estimator_counts_text():
    request = {
        "messages": [
            {"role": "user", "content": "This is a fairly long message about our brand voice."},
        ],
        "max_tokens": 32,
    }
    estimated = default_token_estimator(request)
    assert estimated and estimated > 32


@pytest.mark.asyncio
async def test_gather_with_skill_adds_span():
    RECORDER.clear()
    async def noop():
        return "ok"

    results = await gather_with_skill({"name": "Gather Skill"}, [noop()])
    assert results == ["ok"]
    span_events = [event for event in RECORDER.events if event["attrs"][SKILL_NAME] == "Gather Skill"]
    assert len(span_events) == 2
