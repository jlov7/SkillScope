from __future__ import annotations

import json
import urllib.error

from skillscope.exporters import (
    HTTPOTLPExporter,
    NDJSONExporter,
    coalesce_spans,
    configure_exporters,
    export_events,
)


def test_ndjson_exporter_writes_lines(tmp_path):
    output = tmp_path / "events.jsonl"
    exporter = NDJSONExporter(path=str(output))
    events = [{"event": "start", "attrs": {"skill.name": "Test"}}]
    result = exporter.export(events)
    assert result["status"] == "ok"
    written = output.read_text(encoding="utf-8").strip().splitlines()
    assert len(written) == len(events)
    record = json.loads(written[0])
    assert record["attrs"]["skill.name"] == "Test"


def test_otlp_exporter_posts_payload(monkeypatch):
    captured = {}

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b"ok"

    def fake_urlopen(request, timeout=None):
        captured["timeout"] = timeout
        captured["data"] = json.loads(request.data.decode("utf-8"))
        return DummyResponse()

    monkeypatch.setenv("SKILLSCOPE_OTLP_ENDPOINT", "http://collector.test/v1/logs")
    monkeypatch.setenv("SKILLSCOPE_EXPORT_OTLP", "1")
    monkeypatch.setenv("SKILLSCOPE_EXPORT_NDJSON", "0")
    monkeypatch.setitem(captured, "data", None)
    monkeypatch.setattr("skillscope.exporters.HAS_OTEL", False)
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    exporters = configure_exporters(stream=False)
    events = [{"ts": 123.0, "event": "end", "attrs": {"skill.name": "Telemetry"}}]
    results = export_events(events, exporters)

    assert results[0]["status"] == "ok"
    payload = captured["data"]
    log_record = payload["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]
    assert json.loads(log_record["body"]["stringValue"])["attrs"]["skill.name"] == "Telemetry"


def test_http_otlp_exporter_handles_error(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(urllib.error.URLError("boom")))
    exporter = HTTPOTLPExporter(endpoint="http://collector.test/v1/logs")
    result = exporter.export([{"ts": 1, "attrs": {}}])
    assert result["status"] == "error"


def test_coalesce_spans_pairs_events():
    events = [
        {"event": "start", "ts": 1.0, "attrs": {"skill.name": "Demo"}},
        {"event": "end", "ts": 2.5, "attrs": {"skill.name": "Demo"}},
    ]
    spans = coalesce_spans(events)
    assert len(spans) == 1
    assert spans[0].name == "Demo"
    assert spans[0].start_ts == 1.0
    assert spans[0].end_ts == 2.5
