from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .semconv import (
    AGENT_OPERATION,
    GENAI_MODEL,
    GENAI_TOKEN_USAGE,
    SKILL_FILES,
    SKILL_NAME,
    SKILL_POLICY_REQUIRED,
    SKILL_PROGRESSIVE_LEVEL,
    SKILL_VERSION,
    skill_attrs,
)

MODULE_ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = MODULE_ROOT / "examples" / "skills" / "brand_voice" / "SKILL.md"
STYLE_GUIDE_PATH = MODULE_ROOT / "examples" / "skills" / "brand_voice" / "style-guide" / "brand-voice.md"


def demo_skill_attrs() -> Dict[str, str]:
    return skill_attrs(
        name="Brand Voice Editor (Safe Demo)",
        version="1.0.0",
        files=["examples/skills/brand_voice/style-guide/brand-voice.md"],
        policy_required=False,
        progressive_level="referenced",
        model="claude-3-5-sonnet",
        token_usage=321,
        agent_operation="tool",
    )


def demo_skill_events() -> List[Dict]:
    attrs = demo_skill_attrs()
    return [
        {"ts": 1718695200.0, "event": "start", "attrs": dict(attrs)},
        {
            "ts": 1718695201.2,
            "event": "end",
            "attrs": {**attrs, GENAI_TOKEN_USAGE: attrs[GENAI_TOKEN_USAGE]},
        },
    ]


def load_demo_skill_summary() -> str:
    skill_doc = SKILL_PATH.read_text(encoding="utf-8")
    style_doc = STYLE_GUIDE_PATH.read_text(encoding="utf-8")
    return json.dumps(
        {
            "skill": skill_doc.splitlines()[:10],
            "style_guide": style_doc.splitlines()[:10],
        },
        ensure_ascii=False,
        indent=2,
    )


def attrs_to_summary(attrs: Dict) -> Dict[str, str]:
    return {
        "name": attrs.get(SKILL_NAME),
        "version": attrs.get(SKILL_VERSION),
        "files": attrs.get(SKILL_FILES),
        "policy_required": attrs.get(SKILL_POLICY_REQUIRED),
        "progressive_level": attrs.get(SKILL_PROGRESSIVE_LEVEL),
        "model": attrs.get(GENAI_MODEL),
        "agent_operation": attrs.get(AGENT_OPERATION),
    }
