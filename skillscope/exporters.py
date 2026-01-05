from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, MutableMapping, Optional, Sequence

from .semconv import GENAI_OPERATION, GENAI_TOOL_NAME, SKILL_NAME

try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
    from opentelemetry.sdk.trace.export import SpanExporter as _SpanExporter  # type: ignore

    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,  # type: ignore
        )
    except Exception:
        OTLPSpanExporter = None  # type: ignore

    HAS_OTEL = True
except Exception:  # pragma: no cover - executed when otel missing
    trace = None  # type: ignore
    Resource = None  # type: ignore
    TracerProvider = None  # type: ignore
    BatchSpanProcessor = None  # type: ignore
    SimpleSpanProcessor = None  # type: ignore
    OTLPSpanExporter = None  # type: ignore
    _SpanExporter = object  # type: ignore
    HAS_OTEL = False


class ExportResult(dict):
    """Simple result container for exporter operations."""


class BaseExporter:
    """Common exporter interface."""

    kind = "base"

    def export(self, events: Sequence[MutableMapping]) -> ExportResult:
        raise NotImplementedError


class NDJSONExporter(BaseExporter):
    """Append events as NDJSON lines to stdout or a file."""

    kind = "ndjson"

    def __init__(self, path: str | None = None, stream=None) -> None:
        self.path = Path(path).expanduser() if path else None
        self.stream = stream or sys.stdout

    def export(self, events: Sequence[MutableMapping]) -> ExportResult:
        if not events:
            return ExportResult(status="skipped", reason="no-events")

        output = self.stream
        close_stream = False

        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            output = self.path.open("a", encoding="utf-8")
            close_stream = True

        try:
            for event in events:
                output.write(json.dumps(event, ensure_ascii=False) + "\n")
            if hasattr(output, "flush"):
                output.flush()
        finally:
            if close_stream:
                output.close()
        return ExportResult(status="ok", count=len(events))


def _attr_value(value):
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, (int, float)):
        if isinstance(value, bool):
            return {"boolValue": value}
        if isinstance(value, int):
            return {"intValue": str(value)}
        return {"doubleValue": float(value)}
    return {"stringValue": str(value)}


class HTTPOTLPExporter(BaseExporter):
    """Lightweight OTLP HTTP exporter for SkillScope events (log-based)."""

    kind = "otlp"

    def __init__(
        self,
        endpoint: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        self.endpoint = (
            endpoint
            or os.getenv("SKILLSCOPE_OTLP_ENDPOINT")
            or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            or "http://localhost:4318/v1/logs"
        )
        self.timeout = timeout

    def export(self, events: Sequence[MutableMapping]) -> ExportResult:
        if not events:
            return ExportResult(status="skipped", reason="no-events")

        payload = {
            "resourceLogs": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "skillscope"}},
                            {"key": "telemetry.sdk.name", "value": {"stringValue": "skillscope-research"}},
                        ]
                    },
                    "scopeLogs": [
                        {
                            "scope": {"name": "skillscope.events", "version": "0.1.0"},
                            "logRecords": [
                                {
                                    "timeUnixNano": str(int(evt.get("ts", time.time()) * 1_000_000_000)),
                                    "body": {"stringValue": json.dumps(evt, ensure_ascii=False)},
                                    "attributes": [
                                        {"key": key, "value": _attr_value(value)}
                                        for key, value in evt.get("attrs", {}).items()
                                    ],
                                }
                                for evt in events
                            ],
                        }
                    ],
                }
            ]
        }

        try:
            req = urllib.request.Request(
                self.endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"content-type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp.read()
            return ExportResult(status="ok", count=len(events), endpoint=self.endpoint)
        except urllib.error.URLError as exc:
            return ExportResult(status="error", reason=str(exc), endpoint=self.endpoint)


@dataclass
class CoalescedSpan:
    name: str
    start_ts: float
    end_ts: float
    attrs: MutableMapping


def coalesce_spans(events: Sequence[MutableMapping]) -> List[CoalescedSpan]:
    """Pair start/end events into spans based on insertion order."""

    active: list[MutableMapping] = []
    spans: List[CoalescedSpan] = []
    for event in events:
        attrs = event.get("attrs", {})
        name = _span_name(attrs)
        ts = float(event.get("ts") or time.time())
        if event.get("event") == "start":
            active.append({"name": name, "start": ts, "attrs": dict(attrs)})
        elif event.get("event") == "end":
            if active:
                span = active.pop()
                spans.append(
                    CoalescedSpan(
                        name=span["name"],
                        start_ts=span["start"],
                        end_ts=ts,
                        attrs=span["attrs"],
                    )
                )
            else:
                spans.append(CoalescedSpan(name=name, start_ts=ts, end_ts=ts, attrs=dict(attrs)))
        else:
            spans.append(CoalescedSpan(name=name, start_ts=ts, end_ts=ts, attrs=dict(attrs)))
    # flush remaining active
    for span in active:
        spans.append(
            CoalescedSpan(
                name=span["name"],
                start_ts=span["start"],
                end_ts=span["start"],
                attrs=span["attrs"],
            )
        )
    return spans


def _span_name(attrs: MutableMapping) -> str:
    operation = attrs.get(GENAI_OPERATION)
    tool = attrs.get(GENAI_TOOL_NAME)
    if operation == "execute_tool" and tool:
        return f"{operation} {tool}"
    skill_name = attrs.get(SKILL_NAME) or attrs.get("skill")
    if skill_name:
        return str(skill_name)
    if operation:
        return str(operation)
    return "skill"


class OTelSDKTraceExporter(BaseExporter):
    """Export events as real spans via the OpenTelemetry SDK."""

    kind = "otel-sdk"

    def __init__(
        self,
        endpoint: Optional[str] = None,
        insecure: Optional[bool] = None,
    ) -> None:
        if not HAS_OTEL or OTLPSpanExporter is None:
            raise RuntimeError("OpenTelemetry SDK not available")
        self.endpoint = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if not self.endpoint:
            self.endpoint = "http://localhost:4317"
        if insecure is None:
            insecure = self.endpoint.startswith("http://")
        self.insecure = insecure
        self._tracer = self._create_tracer()

    def _create_tracer(self):
        provider = trace.get_tracer_provider()
        if not isinstance(provider, TracerProvider):
            resource = Resource.create({"service.name": "skillscope"})
            provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(provider)

        span_exporter: _SpanExporter
        span_exporter = OTLPSpanExporter(endpoint=self.endpoint, insecure=self.insecure)  # type: ignore

        # Avoid adding duplicate processors if already configured
        existing_processors = getattr(provider, "_active_span_processors", [])  # type: ignore[attr-defined]
        processor_types = {type(proc) for proc in existing_processors}
        if BatchSpanProcessor and BatchSpanProcessor not in processor_types:
            provider.add_span_processor(BatchSpanProcessor(span_exporter))  # type: ignore[arg-type]
        elif SimpleSpanProcessor and SimpleSpanProcessor not in processor_types:
            provider.add_span_processor(SimpleSpanProcessor(span_exporter))  # type: ignore[arg-type]
        return trace.get_tracer("skillscope.exporter")

    def export(self, events: Sequence[MutableMapping]) -> ExportResult:
        spans = coalesce_spans(events)
        for span in spans:
            with self._tracer.start_as_current_span(
                span.name,
                start_time=int(span.start_ts * 1_000_000_000),
                end_on_exit=False,
            ) as otel_span:
                for key, value in span.attrs.items():
                    otel_span.set_attribute(key, value)
                otel_span.end(end_time=int(span.end_ts * 1_000_000_000))
        return ExportResult(status="ok", count=len(spans), exporter="otel-sdk")


def configure_exporters(stream=None) -> List[BaseExporter]:
    """Instantiate exporters based on environment configuration."""
    exporters: List[BaseExporter] = []

    disable_default_stream = stream is False
    actual_stream = None if disable_default_stream else stream

    if os.getenv("SKILLSCOPE_EXPORT_NDJSON", "1") != "0":
        path = os.getenv("SKILLSCOPE_EXPORT_NDJSON_PATH")
        if path:
            exporters.append(NDJSONExporter(path=path, stream=actual_stream))
        elif actual_stream is not None:
            exporters.append(NDJSONExporter(stream=actual_stream))
        elif not disable_default_stream:
            exporters.append(NDJSONExporter(stream=sys.stdout))

    if os.getenv("SKILLSCOPE_EXPORT_OTLP", "0") == "1":
        if HAS_OTEL and OTLPSpanExporter is not None:
            exporters.append(OTelSDKTraceExporter())
        else:
            exporters.append(HTTPOTLPExporter())

    return exporters


def export_events(events: Sequence[MutableMapping], exporters: Iterable[BaseExporter]) -> List[ExportResult]:
    """Send *events* through each configured exporter."""
    results: List[ExportResult] = []
    for exporter in exporters:
        results.append(exporter.export(events))
    return results
