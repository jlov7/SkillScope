from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from skillscope import __version__
from skillscope.cli import cmd_analyze, cmd_demo, cmd_discover, cmd_emit, cmd_ingest, cmd_validate, main
from skillscope.example_data import demo_skill_events
from skillscope.exporters import HTTPOTLPExporter


def test_emit_demo_to_stdout(monkeypatch, capsys):
    monkeypatch.setenv("SKILLSCOPE_EXPORT_OTLP", "0")
    monkeypatch.setenv("SKILLSCOPE_EXPORT_NDJSON", "1")
    args = SimpleNamespace(demo=True, stdout=True, input=None, input_format="auto")
    assert cmd_emit(args) == 0
    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == len(demo_skill_events())
    for line in output:
        event = json.loads(line)
        assert "attrs" in event
        assert "skill.name" in event["attrs"]


def test_ingest_to_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLSCOPE_EXPORT_OTLP", "0")
    source = tmp_path / "events.jsonl"
    source.write_text(json.dumps({"attrs": {"skill.name": "Test Skill"}}) + "\n", encoding="utf-8")

    output_file = tmp_path / "out.jsonl"
    args = SimpleNamespace(path=str(source), to="ndjson", output=str(output_file), input_format="auto")
    assert cmd_ingest(args) == 0
    written = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert written
    record = json.loads(written[0])
    assert record["attrs"]["skill.name"] == "Test Skill"


def test_demo_command_outputs_summary(capsys):
    args = SimpleNamespace()
    assert cmd_demo(args) == 0
    out = capsys.readouterr().out
    summary = json.loads(out)
    assert "skill" in summary
    assert summary["skill"]


def test_analyze_table_output(tmp_path, monkeypatch, capsys):
    events_file = tmp_path / "events.jsonl"
    events_file.write_text(
        json.dumps(
            {
                "event": "end",
                "attrs": {
                    "skill.name": "Analyze Skill",
                    "skill.files": "guide.md",
                    "skill.policy_required": False,
                    "gen_ai.usage.input_tokens": 25,
                    "gen_ai.usage.output_tokens": 15,
                    "gen_ai.request.model": "claude",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    args = SimpleNamespace(path=str(events_file), input_format="auto", format="table")
    assert cmd_analyze(args) == 0
    out = capsys.readouterr().out
    assert "Analyze Skill" in out
    assert "SkillScope Summary" in out


def test_analyze_json_output(tmp_path, capsys):
    events_file = tmp_path / "events.jsonl"
    events_file.write_text(
        json.dumps(
            {
                "event": "end",
                "attrs": {
                    "skill.name": "Analyze Skill",
                    "gen_ai.usage.input_tokens": 12,
                    "gen_ai.usage.output_tokens": 8,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    args = SimpleNamespace(path=str(events_file), input_format="auto", format="json")
    assert cmd_analyze(args) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["total_events"] == 1
    assert summary["skills"][0]["skill"] == "Analyze Skill"
    assert summary["skills"][0]["tokens_total"] == 20
    assert summary["total_input_tokens"] == 12
    assert summary["total_output_tokens"] == 8


def test_analyze_demo(monkeypatch, capsys):
    monkeypatch.setenv("SKILLSCOPE_EXPORT_OTLP", "0")
    args = SimpleNamespace(path=None, input_format="auto", format="table", demo=True)
    assert cmd_analyze(args) == 0
    out = capsys.readouterr().out
    assert "Brand Voice Editor (Safe Demo)" in out


def test_emit_from_anthropic_log(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SKILLSCOPE_EXPORT_OTLP", "0")
    monkeypatch.setenv("SKILLSCOPE_EXPORT_NDJSON", "1")
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "hello",
                "metadata": {"skill.name": "Anthropic Skill", "skill.version": "2.0.0"},
            }
        ],
        "usage": {"input_tokens": 12, "output_tokens": 4},
    }
    path = tmp_path / "conversation.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    args = SimpleNamespace(demo=False, stdout=True, input=str(path), input_format="auto")
    assert cmd_emit(args) == 0
    output_lines = capsys.readouterr().out.strip().splitlines()
    assert output_lines
    record = json.loads(output_lines[0])
    assert record["attrs"]["skill.name"] == "Anthropic Skill"
    assert record["attrs"]["gen_ai.usage.input_tokens"] == 12
    assert record["attrs"]["gen_ai.usage.output_tokens"] == 4
    assert record["attrs"]["gen_ai.client.token.usage"] == 16


def test_ingest_directory_sources(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLSCOPE_EXPORT_OTLP", "0")
    file_a = tmp_path / "a.jsonl"
    file_b = tmp_path / "nested"
    file_b.mkdir()
    (file_b / "b.json").write_text(json.dumps({"attrs": {"skill.name": "Dir Skill"}}), encoding="utf-8")
    file_a.write_text(json.dumps({"attrs": {"skill.name": "Dir Skill"}}) + "\n", encoding="utf-8")
    output_file = tmp_path / "out.jsonl"
    args = SimpleNamespace(path=str(tmp_path), to="ndjson", output=str(output_file), input_format="auto")
    assert cmd_ingest(args) == 0
    lines = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 2


def test_ingest_to_otlp(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLSCOPE_EXPORT_OTLP", "1")
    monkeypatch.setenv("SKILLSCOPE_EXPORT_NDJSON", "0")
    monkeypatch.setattr("skillscope.exporters.HAS_OTEL", False)

    called = {}

    def fake_export(self, events):
        called["events"] = events
        return {"status": "ok"}

    monkeypatch.setattr(HTTPOTLPExporter, "export", fake_export)

    source = tmp_path / "events.jsonl"
    source.write_text(json.dumps({"attrs": {"skill.name": "OTLP Skill"}}) + "\n", encoding="utf-8")

    args = SimpleNamespace(path=str(source), to="otlp", output=None, input_format="auto")
    assert cmd_ingest(args) == 0
    assert called["events"][0]["attrs"]["skill.name"] == "OTLP Skill"


def test_emit_reports_exporter_failure(monkeypatch, capsys):
    monkeypatch.setenv("SKILLSCOPE_EXPORT_OTLP", "1")
    monkeypatch.setenv("SKILLSCOPE_EXPORT_NDJSON", "0")
    monkeypatch.setattr("skillscope.exporters.HAS_OTEL", False)

    def fake_export(self, events):
        return {"status": "error", "reason": "down"}

    monkeypatch.setattr(HTTPOTLPExporter, "export", fake_export)

    args = SimpleNamespace(demo=True, stdout=False, input=None, input_format="auto")
    exit_code = cmd_emit(args)
    stderr = capsys.readouterr().err
    assert exit_code == 1
    assert "exporter failed" in stderr


def test_cli_version_flag(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    output = capsys.readouterr().out.strip()
    assert __version__ in output


def test_discover_outputs_metadata(tmp_path, capsys):
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Demo skill\n---\n",
        encoding="utf-8",
    )
    args = SimpleNamespace(paths=[str(skill_dir)], format="json", omit_location=False, strict=False)
    assert cmd_discover(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["name"] == "demo-skill"


def test_validate_reports_errors(tmp_path, capsys):
    skill_dir = tmp_path / "bad-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: bad-skill\n---\n",
        encoding="utf-8",
    )
    args = SimpleNamespace(paths=[str(skill_dir)], format="json")
    assert cmd_validate(args) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["path"].endswith("bad-skill")
