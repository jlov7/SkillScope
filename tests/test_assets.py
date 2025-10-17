from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_grafana_dashboard_exists():
    path = ROOT / "docs" / "assets" / "grafana-dashboard.png"
    assert path.exists(), "Grafana preview image is missing"
    assert path.stat().st_size > 0, "Grafana preview image is empty"


def test_sample_metrics_has_expected_metrics():
    path = ROOT / "ops" / "sample_metrics.prom"
    assert path.exists(), "Sample Prometheus metrics file missing"
    text = path.read_text(encoding="utf-8")
    required_metrics = [
        "gen_ai_client_operation_duration_count",
        "skill_policy_required",
        "skill_files_loaded_count",
        "gen_ai_client_token_usage",
    ]
    for metric in required_metrics:
        assert metric in text


@pytest.mark.parametrize("doc_path", ["docs/index.md", "docs/faq.md", "CONTRIBUTING.md"])
def test_markdown_files_exist(doc_path):
    path = ROOT / doc_path
    assert path.exists(), f"Expected documentation file missing: {doc_path}"
