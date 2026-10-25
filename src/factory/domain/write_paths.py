"""The write paths: what an agent may write, what no agent may write, and the one verdict."""

import re
from collections.abc import Sequence
from fnmatch import fnmatchcase

from factory.domain.agent_runs import WritePathSettings
from factory.domain.paths import (
    FEATURE_FILE_NAME,
    FEATURE_FORM_FILE,
    PIPELINE_DEFINITION_FILE,
    PROJECT_AGENTS_DIRECTORY,
    STORY_FORM_FILE,
)
from factory.domain.pipeline_definition import (
    FEATURE_PLACEHOLDER,
    WORK_ITEM_PLACEHOLDER,
    is_inside_checkout,
)

PROTECTED_PATHS: tuple[str, ...] = (
    ".claude/*",
    "*/.claude/*",
    "CLAUDE.md",
    "Makefile",
    "pyproject.toml",
    "uv.lock",
    PIPELINE_DEFINITION_FILE,
    STORY_FORM_FILE,
    FEATURE_FORM_FILE,
    FEATURE_FILE_NAME,
    "*/" + FEATURE_FILE_NAME,
    f"{PROJECT_AGENTS_DIRECTORY}/*",
)

_PLACEHOLDER = re.compile(r"\{[a-z_]+\}")
_KNOWN_PLACEHOLDERS = (WORK_ITEM_PLACEHOLDER, FEATURE_PLACEHOLDER)


def matches_any(path: str, patterns: Sequence[str]) -> bool:
    """Whether `path` matches one of `patterns`, case-sensitive and with `*` crossing `/`."""
    return any(fnmatchcase(path, pattern) for pattern in patterns)


def is_writable(path: str, write_paths: Sequence[str]) -> bool:
    """Whether `path` is inside the checkout and matches one of `write_paths`."""
    return is_inside_checkout(path) and matches_any(path, write_paths)


def expand_write_paths(
    patterns: Sequence[str], *, work_item_path: str, feature_path: str
) -> list[str]:
    """The patterns with `{work_item}` and `{feature}` replaced; `ValueError` for another name."""
    return [_expand(pattern, work_item_path, feature_path) for pattern in patterns]


def refusal(path: str, settings: WritePathSettings) -> str | None:
    """The text that refuses a write to `path`, or `None` when the write is allowed."""
    if not is_inside_checkout(path):
        return f"{path} is not a path inside the checkout."
    if matches_any(path, settings.protected_paths):
        return f"{path} is owned by the human; a change there is a question."
    if not matches_any(path, settings.write_paths):
        return f"{path} is outside the write paths of this stage."
    return None


def _expand(pattern: str, work_item_path: str, feature_path: str) -> str:
    for placeholder in _PLACEHOLDER.findall(pattern):
        if placeholder not in _KNOWN_PLACEHOLDERS:
            raise ValueError(f"write path {pattern!r} holds the unknown placeholder {placeholder}")
    return pattern.replace(WORK_ITEM_PLACEHOLDER, work_item_path).replace(
        FEATURE_PLACEHOLDER, feature_path
    )
