from __future__ import annotations

from skillscope.semconv import (
    AGENT_OPERATION,
    GENAI_MODEL,
    GENAI_OPERATION,
    GENAI_TOKEN_USAGE,
    GENAI_USAGE_INPUT,
    GENAI_USAGE_OUTPUT,
    SKILL_DESCRIPTION,
    SKILL_FILES,
    SKILL_FILES_COUNT,
    SKILL_LICENSE,
    SKILL_METADATA,
    SKILL_NAME,
    SKILL_POLICY_REQUIRED,
    SKILL_PROGRESSIVE_LEVEL,
    SKILL_VERSION,
    apply_skill_attrs,
    end_span,
    skill_attrs,
    start_span,
)


class DummyRecorder:
    def __init__(self) -> None:
        self.started = None
        self.ended = None

    def start(self, attrs):
        self.started = attrs
        return {"attrs": attrs}

    def end(self, attrs):
        self.ended = attrs
        return attrs


def test_skill_attrs_sets_expected_keys():
    attrs = skill_attrs(
        name="Demo Skill",
        version="1.2.3",
        description="Demo description",
        files=("a.txt", "b.txt"),
        policy_required=True,
        progressive_level="eager",
        model="claude-3",
        input_tokens=100,
        output_tokens=23,
        token_usage=123,
        operation="invoke_agent",
        agent_operation="act",
        license="Apache-2.0",
        metadata={"owner": "qa"},
    )

    assert attrs[SKILL_NAME] == "Demo Skill"
    assert attrs[SKILL_VERSION] == "1.2.3"
    assert attrs[SKILL_DESCRIPTION] == "Demo description"
    assert attrs[SKILL_FILES] == "a.txt,b.txt"
    assert attrs[SKILL_FILES_COUNT] == 2
    assert attrs[SKILL_POLICY_REQUIRED] is True
    assert attrs[SKILL_PROGRESSIVE_LEVEL] == "eager"
    assert attrs[GENAI_MODEL] == "claude-3"
    assert attrs[GENAI_USAGE_INPUT] == 100
    assert attrs[GENAI_USAGE_OUTPUT] == 23
    assert attrs[GENAI_TOKEN_USAGE] == 123
    assert attrs[GENAI_OPERATION] == "invoke_agent"
    assert attrs[AGENT_OPERATION] == "act"
    assert attrs[SKILL_LICENSE] == "Apache-2.0"
    assert "owner" in attrs[SKILL_METADATA]


def test_apply_skill_attrs_handles_generators():
    generator = (item for item in ["guide.md"])
    attrs = skill_attrs(name="Generator Skill", files=generator)
    target = {}
    apply_skill_attrs(target, attrs)
    assert target[SKILL_FILES] == "guide.md"
    assert target[SKILL_FILES_COUNT] == 1


def test_span_helpers_delegate_to_recorder():
    attrs = skill_attrs(name="Span Skill")
    recorder = DummyRecorder()
    handle = start_span(recorder, attrs)
    assert recorder.started[SKILL_NAME] == "Span Skill"
    end_span(recorder, handle, {GENAI_MODEL: "claude"})
    assert recorder.ended[GENAI_MODEL] == "claude"
