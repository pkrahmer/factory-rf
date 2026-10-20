"""The write paths: matching, placeholders, the protected paths and the one refusal verdict."""

from pathlib import Path

import pytest

from factory.domain.agent_runs import GuardSettings
from factory.domain.write_paths import (
    PROTECTED_PATHS,
    expand_write_paths,
    is_writable,
    matches_any,
    refusal,
)

WORK_ITEM = "factory/features/F0004-x/in-progress/F0004-S0001-y.md"
FEATURE = "factory/features/F0004-x"


def _guard(write_paths: list[str]) -> GuardSettings:
    return GuardSettings(
        root=Path("/work"), write_paths=write_paths, protected_paths=list(PROTECTED_PATHS)
    )


@pytest.mark.parametrize(
    ("path", "patterns", "expected"),
    [
        ("src/factory/domain/x.py", ["src/*"], True),
        ("tests/a.py", ["tests/*"], True),
        ("tests/a.py", ["src/*", "tests/*"], True),
        ("SRC/a.py", ["src/*"], False),
    ],
)
def test_a_path_matching_a_write_path_is_writable_and_star_crosses_slashes(
    path: str, patterns: list[str], expected: bool
) -> None:
    assert is_writable(path, patterns) is expected


@pytest.mark.parametrize(
    ("path", "patterns"),
    [
        ("docs/a.md", ["src/*", "tests/*"]),
        ("src/a.py", []),
        ("README.md", []),
    ],
)
def test_a_path_matching_no_write_path_is_not_writable(path: str, patterns: list[str]) -> None:
    assert is_writable(path, patterns) is False


@pytest.mark.parametrize(
    ("path", "patterns", "expected"),
    [
        ("", ["*"], False),
        ("/src/a.py", ["*"], False),
        ("/src/a.py", ["/src/*"], False),
        ("src/../factory/pipeline.yml", ["src/*"], False),
        ("../a.py", ["*"], False),
        ("src/..", ["src/*"], False),
        ("src/..x/a.py", ["src/*"], True),
        ("src/x../a.py", ["src/*"], True),
        ("..x/a.py", ["*"], True),
    ],
)
def test_an_unsafe_path_is_never_writable_and_a_dotted_segment_name_is_safe(
    path: str, patterns: list[str], expected: bool
) -> None:
    assert is_writable(path, patterns) is expected


def test_both_placeholders_are_expanded_in_order() -> None:
    expanded = expand_write_paths(
        ["{work_item}", "{feature}/backlog/*", "tests/*"],
        work_item_path=WORK_ITEM,
        feature_path=FEATURE,
    )

    assert expanded == [WORK_ITEM, f"{FEATURE}/backlog/*", "tests/*"]


@pytest.mark.parametrize("placeholder", ["{stage}", "{other_name}"])
def test_an_unknown_placeholder_is_refused_by_name(placeholder: str) -> None:
    with pytest.raises(ValueError, match=placeholder.replace("{", r"\{").replace("}", r"\}")):
        expand_write_paths([f"{placeholder}/*"], work_item_path=WORK_ITEM, feature_path=FEATURE)


def test_a_brace_that_is_no_placeholder_name_is_kept() -> None:
    patterns = ["{Feature}/a", "{1}/b"]

    assert expand_write_paths(patterns, work_item_path=WORK_ITEM, feature_path=FEATURE) == patterns


def test_the_protected_paths_are_the_engines_twelve_patterns() -> None:
    assert PROTECTED_PATHS == (
        ".claude/*",
        "*/.claude/*",
        "CLAUDE.md",
        "Makefile",
        "pyproject.toml",
        "uv.lock",
        "factory/pipeline.yml",
        "factory/story-form.md",
        "factory/feature-form.md",
        "feature.md",
        "*/feature.md",
        "factory/agents/*",
    )


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (".claude/settings.json", True),
        ("CLAUDE.md", True),
        ("Makefile", True),
        ("pyproject.toml", True),
        ("uv.lock", True),
        ("factory/pipeline.yml", True),
        ("factory/story-form.md", True),
        ("factory/feature-form.md", True),
        ("feature.md", True),
        ("factory/features/F0004-x/feature.md", True),
        ("docs/feature.md", True),
        ("docs/CLAUDE.md", False),
        ("src/pyproject.toml", False),
        (".claudex/a", False),
        ("docs/myfeature.md", False),
        ("src/feature.md.bak", False),
    ],
)
def test_each_protected_pattern_protects_its_path(path: str, expected: bool) -> None:
    assert matches_any(path, PROTECTED_PATHS) is expected


def test_a_writable_unprotected_path_is_not_refused() -> None:
    assert refusal("src/factory/x.py", _guard(["src/*"])) is None


def test_a_path_outside_the_write_paths_is_refused() -> None:
    assert refusal("docs/a.md", _guard(["src/*"])) == (
        "docs/a.md is outside the write paths of this stage."
    )


@pytest.mark.parametrize(
    "path", ["pyproject.toml", ".claude/settings.json", "factory/features/F0004-x/feature.md"]
)
def test_a_protected_path_is_refused_even_under_a_matching_write_path(path: str) -> None:
    assert (
        refusal(path, _guard(["*"]))
        == f"{path} is owned by the human; a change there is a question."
    )


@pytest.mark.parametrize(
    ("path", "write_paths"),
    [
        ("src/../factory/pipeline.yml", ["src/*"]),
        ("src/../pyproject.toml", ["*"]),
        ("/pyproject.toml", ["*"]),
        ("../CLAUDE.md", []),
        ("", ["*"]),
        ("src/../feature.md", ["*"]),
        (".claude/../a.py", ["*"]),
    ],
)
def test_an_unsafe_path_is_refused_before_anything_else(path: str, write_paths: list[str]) -> None:
    assert refusal(path, _guard(write_paths)) == f"{path} is not a path inside the checkout."
