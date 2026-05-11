"""SkillScope package exposing skill instrumentation helpers."""

from .instrumentation import (  # noqa: F401
    RECORDER,
    AnthropicInstrumented,
    default_token_estimator,
    gather_with_skill,
    run_skill_script,
    use_skill,
    use_skill_async,
    use_skill_from_path,
    use_tool,
    with_skill,
)
from .normalization import load_events_from_source, normalize_event, normalize_events  # noqa: F401
from .semconv import skill_attrs  # noqa: F401
from .skills import read_skill_metadata, validate_skill_dir  # noqa: F401

__all__ = [
    "AnthropicInstrumented",
    "use_skill",
    "use_skill_async",
    "use_skill_from_path",
    "with_skill",
    "gather_with_skill",
    "use_tool",
    "run_skill_script",
    "default_token_estimator",
    "RECORDER",
    "skill_attrs",
    "normalize_event",
    "normalize_events",
    "load_events_from_source",
    "read_skill_metadata",
    "validate_skill_dir",
]
__version__ = "0.2.0"
