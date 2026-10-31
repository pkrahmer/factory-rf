"""The preflight item of the copy snapshots: the workspace and the base are directories."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.application.preflight import snapshots_item


def _directory(path: Path) -> None:
    path.mkdir()


def _file(path: Path) -> None:
    path.write_text("x\n", encoding="utf-8")


def _missing(_path: Path) -> None:
    pass


def _workspace_not_a_directory(workspace: Path, _base: Path) -> str:
    return f"the workspace {workspace} is not a directory"


def _base_missing(_workspace: Path, base: Path) -> str:
    return f"the base {base} does not exist; make it empty with mkdir, the first advance fills it"


def _base_not_a_directory(_workspace: Path, base: Path) -> str:
    return f"the base {base} is not a directory"


def _both(workspace: Path, base: Path) -> str:
    return f"workspace {workspace}, base {base}"


@pytest.mark.parametrize(
    ("make_workspace", "make_base", "passed", "detail"),
    [
        pytest.param(_directory, _directory, True, _both, id="two-directories"),
        pytest.param(_file, _directory, False, _workspace_not_a_directory, id="workspace-a-file"),
        pytest.param(
            _missing, _directory, False, _workspace_not_a_directory, id="workspace-missing"
        ),
        pytest.param(_directory, _missing, False, _base_missing, id="base-missing"),
        pytest.param(_directory, _file, False, _base_not_a_directory, id="base-a-file"),
    ],
)
def test_the_snapshots_item_passes_only_when_the_workspace_and_the_base_are_directories(
    tmp_path: Path,
    make_workspace: Callable[[Path], None],
    make_base: Callable[[Path], None],
    *,
    passed: bool,
    detail: Callable[[Path, Path], str],
) -> None:
    workspace = tmp_path / "work"
    base = tmp_path / "base"
    make_workspace(workspace)
    make_base(base)

    item = snapshots_item(workspace, base)

    assert (item.name, item.passed, item.detail) == ("snapshots", passed, detail(workspace, base))
