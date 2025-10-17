"""SkillScope package exposing skill instrumentation helpers."""

from .instrumentation import (  # noqa: F401
    RECORDER,
    AnthropicInstrumented,
    default_token_estimator,
    gather_with_skill,
    use_skill,
    use_skill_async,
    with_skill,
)
from .semconv import skill_attrs  # noqa: F401

__all__ = [
    "AnthropicInstrumented",
    "use_skill",
    "use_skill_async",
    "with_skill",
    "gather_with_skill",
    "default_token_estimator",
    "RECORDER",
    "skill_attrs",
]
__version__ = "0.1.0"
