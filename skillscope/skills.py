from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Iterable, Optional
import unicodedata
from xml.sax.saxutils import escape


try:  # Prefer strict YAML parsing when available.
    import strictyaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    strictyaml = None  # type: ignore


FRONTMATTER_DELIMITER = "---"
MAX_SKILL_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500
ALLOWED_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}


class SkillParseError(ValueError):
    """Raised when SKILL.md frontmatter cannot be parsed."""


class SkillValidationError(ValueError):
    """Raised when SKILL.md frontmatter is missing required fields."""


@dataclass(frozen=True)
class SkillMetadata:
    name: str
    description: str
    path: Path
    skill_md: Path
    license: Optional[str] = None
    compatibility: Optional[str] = None
    allowed_tools: Optional[str] = None
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = {
            "name": self.name,
            "description": self.description,
            "path": str(self.path),
            "location": str(self.skill_md),
        }
        if self.license:
            payload["license"] = self.license
        if self.compatibility:
            payload["compatibility"] = self.compatibility
        if self.allowed_tools:
            payload["allowed_tools"] = self.allowed_tools
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True)
class SkillProblem:
    path: Path
    errors: list[str]


def find_skill_md(skill_dir: Path) -> Optional[Path]:
    """Return the SKILL.md file path if present in a directory."""
    for name in ("SKILL.md", "skill.md"):
        candidate = skill_dir / name
        if candidate.exists():
            return candidate
    return None


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from a SKILL.md file."""
    if not content.startswith(FRONTMATTER_DELIMITER):
        raise SkillParseError("SKILL.md must start with YAML frontmatter (---)")
    parts = content.split(FRONTMATTER_DELIMITER, 2)
    if len(parts) < 3:
        raise SkillParseError("SKILL.md frontmatter not properly closed with ---")
    frontmatter = parts[1]
    body = parts[2].lstrip()

    if strictyaml is not None:
        try:
            parsed = strictyaml.load(frontmatter)
            metadata = parsed.data
        except Exception as exc:
            raise SkillParseError(f"Invalid YAML in frontmatter: {exc}") from exc
        if not isinstance(metadata, dict):
            raise SkillParseError("SKILL.md frontmatter must be a YAML mapping")
        if isinstance(metadata.get("metadata"), dict):
            metadata["metadata"] = {str(k): str(v) for k, v in metadata["metadata"].items()}
        return metadata, body

    return _parse_frontmatter_loose(frontmatter), body


def _parse_frontmatter_loose(frontmatter: str) -> dict:
    """Parse a minimal YAML subset when strictyaml is unavailable."""
    data: dict[str, object] = {}
    current_map: Optional[dict[str, str]] = None

    for raw in frontmatter.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line.startswith((" ", "\t")):
            if current_map is None:
                continue
            key, value = _split_key_value(stripped)
            if key:
                current_map[key] = _strip_quotes(value)
            continue

        key, value = _split_key_value(stripped)
        if not key:
            continue
        if key == "metadata":
            current_map = {}
            data[key] = current_map
            if value and value not in ("{}", "{ }"):
                # Best-effort fallback if metadata is not a map.
                data[key] = {}
            continue
        current_map = None
        data[key] = _strip_quotes(value)

    return data


def _split_key_value(line: str) -> tuple[str, str]:
    if ":" not in line:
        return "", ""
    key, _, value = line.partition(":")
    return key.strip(), value.strip()


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and ((value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'"))):
        return value[1:-1]
    return value


def read_skill_metadata(path: Path | str) -> SkillMetadata:
    """Read skill metadata from a skill directory or SKILL.md path."""
    path = Path(path)
    if path.is_file():
        skill_md = path
        skill_dir = path.parent
    else:
        skill_dir = path
        skill_md = find_skill_md(skill_dir)
    if skill_md is None or not skill_md.exists():
        raise SkillParseError(f"SKILL.md not found in {skill_dir}")

    content = skill_md.read_text(encoding="utf-8")
    metadata, _ = parse_frontmatter(content)

    if "name" not in metadata:
        raise SkillValidationError("Missing required field in frontmatter: name")
    if "description" not in metadata:
        raise SkillValidationError("Missing required field in frontmatter: description")

    name = str(metadata["name"]).strip()
    description = str(metadata["description"]).strip()
    if not name:
        raise SkillValidationError("Field 'name' must be a non-empty string")
    if not description:
        raise SkillValidationError("Field 'description' must be a non-empty string")

    extra_metadata = metadata.get("metadata") or {}
    if not isinstance(extra_metadata, dict):
        extra_metadata = {}
    extra_metadata = {str(k): str(v) for k, v in extra_metadata.items()}

    return SkillMetadata(
        name=name,
        description=description,
        path=skill_dir,
        skill_md=skill_md,
        license=_coerce_optional(metadata.get("license")),
        compatibility=_coerce_optional(metadata.get("compatibility")),
        allowed_tools=_coerce_optional(metadata.get("allowed-tools")),
        metadata=extra_metadata,
    )


def _coerce_optional(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def validate_metadata(metadata: dict, skill_dir: Optional[Path] = None) -> list[str]:
    """Validate parsed metadata according to the Agent Skills spec."""
    errors: list[str] = []
    extra_fields = set(metadata.keys()) - ALLOWED_FIELDS
    if extra_fields:
        errors.append(
            "Unexpected fields in frontmatter: "
            f"{', '.join(sorted(extra_fields))}. Only {sorted(ALLOWED_FIELDS)} are allowed."
        )

    if "name" not in metadata:
        errors.append("Missing required field in frontmatter: name")
    else:
        errors.extend(_validate_name(str(metadata["name"]), skill_dir))

    if "description" not in metadata:
        errors.append("Missing required field in frontmatter: description")
    else:
        errors.extend(_validate_description(str(metadata["description"])))

    if "compatibility" in metadata:
        errors.extend(_validate_compatibility(str(metadata["compatibility"])))

    return errors


def _validate_name(name: str, skill_dir: Optional[Path]) -> list[str]:
    errors: list[str] = []
    name = name.strip()
    if not name:
        errors.append("Field 'name' must be a non-empty string")
        return errors

    name = unicodedata.normalize("NFKC", name)
    if len(name) > MAX_SKILL_NAME_LENGTH:
        errors.append(
            f"Skill name '{name}' exceeds {MAX_SKILL_NAME_LENGTH} character limit "
            f"({len(name)} chars)"
        )
    if name != name.lower():
        errors.append(f"Skill name '{name}' must be lowercase")
    if name.startswith("-") or name.endswith("-"):
        errors.append("Skill name cannot start or end with a hyphen")
    if "--" in name:
        errors.append("Skill name cannot contain consecutive hyphens")
    if not all(char.isalnum() or char == "-" for char in name):
        errors.append(
            f"Skill name '{name}' contains invalid characters. "
            "Only letters, digits, and hyphens are allowed."
        )

    if skill_dir is not None:
        dir_name = unicodedata.normalize("NFKC", skill_dir.name)
        if dir_name != name:
            errors.append(f"Directory name '{skill_dir.name}' must match skill name '{name}'")

    return errors


def _validate_description(description: str) -> list[str]:
    errors: list[str] = []
    description = description.strip()
    if not description:
        errors.append("Field 'description' must be a non-empty string")
        return errors
    if len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f"Description exceeds {MAX_DESCRIPTION_LENGTH} character limit "
            f"({len(description)} chars)"
        )
    return errors


def _validate_compatibility(compatibility: str) -> list[str]:
    errors: list[str] = []
    if len(compatibility) > MAX_COMPATIBILITY_LENGTH:
        errors.append(
            f"Compatibility exceeds {MAX_COMPATIBILITY_LENGTH} character limit "
            f"({len(compatibility)} chars)"
        )
    return errors


def validate_skill_dir(skill_dir: Path | str) -> list[str]:
    """Validate a skill directory by reading its SKILL.md frontmatter."""
    skill_dir = Path(skill_dir)
    if not skill_dir.exists():
        return [f"Path does not exist: {skill_dir}"]
    if skill_dir.is_file():
        skill_dir = skill_dir.parent
    if not skill_dir.is_dir():
        return [f"Not a directory: {skill_dir}"]

    skill_md = find_skill_md(skill_dir)
    if skill_md is None:
        return ["Missing required file: SKILL.md"]

    try:
        content = skill_md.read_text(encoding="utf-8")
        metadata, _ = parse_frontmatter(content)
    except SkillParseError as exc:
        return [str(exc)]

    return validate_metadata(metadata, skill_dir)


def discover_skills(paths: Iterable[Path | str]) -> tuple[list[SkillMetadata], list[SkillProblem]]:
    """Discover skills by scanning paths for SKILL.md files."""
    skill_dirs = collect_skill_dirs(paths)
    skills: list[SkillMetadata] = []
    problems: list[SkillProblem] = []
    for skill_dir in skill_dirs:
        try:
            metadata = read_skill_metadata(skill_dir)
            skills.append(metadata)
        except (SkillParseError, SkillValidationError) as exc:
            problems.append(SkillProblem(path=Path(skill_dir), errors=[str(exc)]))
    return skills, problems


def collect_skill_dirs(paths: Iterable[Path | str]) -> list[Path]:
    """Collect directories that contain SKILL.md files (recursive)."""
    return _collect_skill_dirs(paths)


def _collect_skill_dirs(paths: Iterable[Path | str]) -> list[Path]:
    seen: set[Path] = set()
    candidates: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file() and path.name.lower() == "skill.md":
            candidate = path.parent
            if candidate not in seen:
                seen.add(candidate)
                candidates.append(candidate)
            continue
        if path.is_dir():
            skill_md = find_skill_md(path)
            if skill_md is not None:
                if path not in seen:
                    seen.add(path)
                    candidates.append(path)
                continue
            for skill_md in path.rglob("SKILL.md"):
                candidate = skill_md.parent
                if candidate not in seen:
                    seen.add(candidate)
                    candidates.append(candidate)
            for skill_md in path.rglob("skill.md"):
                candidate = skill_md.parent
                if candidate not in seen:
                    seen.add(candidate)
                    candidates.append(candidate)
    return candidates


def skills_to_prompt_xml(skills: Iterable[SkillMetadata], include_location: bool = True) -> str:
    """Generate <available_skills> XML for agent prompts."""
    lines = ["<available_skills>"]
    for skill in skills:
        lines.append("  <skill>")
        lines.append("    <name>")
        lines.append(f"      {escape(skill.name)}")
        lines.append("    </name>")
        lines.append("    <description>")
        lines.append(f"      {escape(skill.description)}")
        lines.append("    </description>")
        if include_location:
            lines.append("    <location>")
            lines.append(f"      {escape(str(skill.skill_md))}")
            lines.append("    </location>")
        lines.append("  </skill>")
    lines.append("</available_skills>")
    return "\n".join(lines) + "\n"


def problems_to_json(problems: Iterable[SkillProblem]) -> str:
    payload = [
        {"path": str(problem.path), "errors": list(problem.errors)}
        for problem in problems
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2)
