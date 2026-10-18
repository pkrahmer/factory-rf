"""The kernel's targets of a run's write paths and tool paths."""

from pathlib import Path

import pytest

from factory.domain.agent_runs import GuardSettings
from factory.domain.confinement import WriteTarget, write_targets

ROOT = Path("/work/checkout")
HOME = Path("/home/agent")
WORK_ITEM = "factory/features/F0001-x/in-progress/F0001-S0001-y.md"


def _guard(write_paths: list[str], tool_paths: list[str]) -> GuardSettings:
    return GuardSettings(
        root=ROOT, write_paths=write_paths, protected_paths=[], tool_paths=tool_paths
    )


def _folder(path: Path) -> WriteTarget:
    return WriteTarget(path=path, kind="folder")


def _file(path: Path) -> WriteTarget:
    return WriteTarget(path=path, kind="file")


@pytest.mark.parametrize(
    ("write_path", "expected"),
    [
        ("src/*", [_folder(ROOT / "src")]),
        ("a/b/*", [_folder(ROOT / "a/b")]),
        ("README.md", [_file(ROOT / "README.md")]),
        (WORK_ITEM, [_file(ROOT / WORK_ITEM)]),
        ("docs/*.md", [_folder(ROOT / "docs")]),
        ("a/b*/c", [_folder(ROOT / "a")]),
        ("a/b?/c", [_folder(ROOT / "a")]),
        ("a/[bc]/d", [_folder(ROOT / "a")]),
        ("*.md", []),
        ("*", []),
        ("", []),
        ("/etc/*", []),
        ("../x/*", []),
        ("src/../x", []),
    ],
)
def test_a_write_path_becomes_the_folder_or_file_the_kernel_can_name(
    write_path: str, expected: list[WriteTarget]
) -> None:
    assert write_targets(_guard([write_path], []), home=HOME) == expected


@pytest.mark.parametrize(
    ("tool_path", "home", "expected"),
    [
        (".venv/*", HOME, [_folder(ROOT / ".venv")]),
        ("~/.cache/*", HOME, [_folder(HOME / ".cache")]),
        ("~/.cache/*", None, []),
        ("*.log", HOME, []),
    ],
)
def test_a_tool_path_becomes_a_folder_in_the_checkout_or_the_home(
    tool_path: str, home: Path | None, expected: list[WriteTarget]
) -> None:
    assert write_targets(_guard([], [tool_path]), home=home) == expected


def test_the_write_paths_come_first_and_a_repeated_target_is_left_out() -> None:
    guard = _guard(["src/*", "docs/*", "src/*"], [".venv/*", "src/*"])

    assert write_targets(guard, home=HOME) == [
        _folder(ROOT / "src"),
        _folder(ROOT / "docs"),
        _folder(ROOT / ".venv"),
    ]
