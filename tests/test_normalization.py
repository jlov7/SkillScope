from __future__ import annotations

import json

from skillscope.normalization import (
    GENAI_AGENT_INVOKE,
    GENAI_TOOL_EXECUTE,
    SKILLSCOPE_SOURCE_FORMAT,
    load_events_from_source,
    normalize_event,
)
from skillscope.semconv import (
    GENAI_OPERATION,
    GENAI_TOKEN_USAGE,
    GENAI_TOOL_NAME,
    GENAI_USAGE_INPUT,
    GENAI_USAGE_OUTPUT,
)


def test_normalizes_branchlab_tool_and_memory_events(tmp_path):
    source = tmp_path / "branchlab.jsonl"
    source.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "schema": "branchlab.trace.v1",
                        "run_id": "run_1",
                        "event_id": "e1",
                        "ts": "2026-02-27T18:00:06Z",
                        "type": "tool.request",
                        "data": {"call_id": "c1", "tool": "pricing.lookup", "args": {"sku": "A"}},
                        "meta": {"tool": "pricing.lookup"},
                    }
                ),
                json.dumps(
                    {
                        "schema": "branchlab.trace.v1",
                        "run_id": "run_1",
                        "event_id": "e2",
                        "ts": "2026-02-27T18:00:08Z",
                        "type": "memory.read",
                        "data": {"items": [{"id": "m1"}]},
                        "meta": {"count": 1},
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    events = load_events_from_source(source, "auto")

    assert events[0]["attrs"][GENAI_OPERATION] == GENAI_TOOL_EXECUTE
    assert events[0]["attrs"][GENAI_TOOL_NAME] == "pricing.lookup"
    assert events[0]["attrs"][SKILLSCOPE_SOURCE_FORMAT] == "branchlab.trace"
    assert events[1]["attrs"]["skillscope.resources"] == "memory"


def test_normalizes_overhearops_otel_spans():
    event = normalize_event(
        {
            "span_id": 1,
            "trace_id": 2,
            "name": "exec",
            "start_time": 1772561277796510000,
            "attributes": {
                "agent.role": "exec",
                "overhearops.thread_id": "ci_flake",
                "token.approx_in": 442,
                "token.approx_out": 828,
            },
        }
    )

    attrs = event["attrs"]
    assert attrs[GENAI_OPERATION] == "exec"
    assert attrs["gen_ai.agent.operation"] == "exec"
    assert attrs[GENAI_USAGE_INPUT] == 442
    assert attrs[GENAI_USAGE_OUTPUT] == 828
    assert attrs[GENAI_TOKEN_USAGE] == 1270
    assert attrs[SKILLSCOPE_SOURCE_FORMAT] == "otel.span"


def test_normalizes_skillchain_trace_steps(tmp_path):
    source = tmp_path / "skillchain.jsonl"
    source.write_text(
        json.dumps(
            {
                "type": "step",
                "trace_id": "trc_1",
                "episode_id": "ep_1",
                "step_idx": 1,
                "kind": "tool",
                "tool_name": "http.request",
                "input": {"url": "https://example.com"},
                "output": {"status": 200},
            }
        ),
        encoding="utf-8",
    )

    events = load_events_from_source(source, "auto")

    assert events[0]["attrs"][GENAI_OPERATION] == GENAI_TOOL_EXECUTE
    assert events[0]["attrs"][GENAI_TOOL_NAME] == "http.request"
    assert events[0]["attrs"][SKILLSCOPE_SOURCE_FORMAT] == "skillchain.trace"


def test_normalizes_current_genai_agent_and_tool_shapes():
    agent = normalize_event(
        {
            "name": "gen_ai.agent.invoke",
            "attributes": {
                "gen_ai.request.model": "gpt-5.3-codex",
                "gen_ai.usage.input_tokens": 10,
                "gen_ai.usage.output_tokens": 4,
            },
        }
    )
    tool = normalize_event(
        {
            "name": "gen_ai.tool.execute",
            "attributes": {
                "gen_ai.tool.name": "github.create_issue",
                "tool.scopes": "issues:write,repo:read",
                "files.touched": "src/app.ts",
            },
        }
    )

    assert agent["attrs"][GENAI_OPERATION] == GENAI_AGENT_INVOKE
    assert agent["attrs"][GENAI_TOKEN_USAGE] == 14
    assert tool["attrs"][GENAI_OPERATION] == GENAI_TOOL_EXECUTE
    assert tool["attrs"][GENAI_TOOL_NAME] == "github.create_issue"
    assert tool["attrs"]["skillscope.scopes"] == "issues:write,repo:read"
    assert tool["attrs"]["skillscope.files_touched"] == "src/app.ts"
