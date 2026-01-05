from __future__ import annotations

import asyncio
import json

import pytest

from skillscope.instrumentation import (
    RECORDER,
    AnthropicInstrumented,
    default_token_estimator,
    gather_with_skill,
    use_skill_from_path,
    use_skill,
    use_skill_async,
    use_tool,
    with_skill,
)
from skillscope.semconv import (
    GENAI_MODEL,
    GENAI_OPERATION,
    GENAI_TOKEN_USAGE,
    GENAI_TOOL_NAME,
    GENAI_USAGE_INPUT,
    GENAI_USAGE_OUTPUT,
    SKILL_DESCRIPTION,
    SKILL_NAME,
    SKILL_VERSION,
)


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


def test_use_tool_records_tool_span():
    RECORDER.clear()
    with use_skill(name="Parent Skill"):
        with use_tool(name="vector-search", tool_type="datastore") as attrs:
            assert attrs[GENAI_TOOL_NAME] == "vector-search"
            assert attrs[GENAI_OPERATION] == "execute_tool"
            assert attrs[SKILL_NAME] == "Parent Skill"
    tool_events = [event for event in RECORDER.events if event["attrs"].get(GENAI_TOOL_NAME) == "vector-search"]
    assert len(tool_events) == 2


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
        assert attrs[GENAI_USAGE_INPUT] >= 0
        assert attrs[GENAI_USAGE_OUTPUT] >= 0
        assert attrs[GENAI_TOKEN_USAGE] == attrs[GENAI_USAGE_INPUT] + attrs[GENAI_USAGE_OUTPUT]


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


def test_use_skill_from_path_reads_frontmatter(tmp_path):
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: demo-skill\n"
        "description: Demo skill\n"
        "metadata:\n"
        "  version: \"1.0.0\"\n"
        "---\n"
        "\n"
        "# Demo\n",
        encoding="utf-8",
    )
    with use_skill_from_path(skill_dir) as attrs:
        assert attrs[SKILL_NAME] == "demo-skill"
        assert attrs[SKILL_DESCRIPTION] == "Demo skill"
        assert attrs[SKILL_VERSION] == "1.0.0"


@pytest.mark.asyncio
async def test_gather_with_skill_adds_span():
    RECORDER.clear()
    async def noop():
        return "ok"

    results = await gather_with_skill({"name": "Gather Skill"}, [noop()])
    assert results == ["ok"]
    span_events = [event for event in RECORDER.events if event["attrs"][SKILL_NAME] == "Gather Skill"]
    assert len(span_events) == 2
