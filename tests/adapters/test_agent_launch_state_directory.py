"""The runtimes' shared helper makes the state directory, and a failed `mkdir` is an error."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.agent_launch import make_state_directory
from factory.domain.errors import AgentRuntimeError


def _nothing(root: Path) -> None:
    pass


def _runs_with_a_file(root: Path) -> None:
    (root / "runs").mkdir()
    (root / "runs" / "keep.txt").write_text("kept", encoding="utf-8")


def _a_file_named_state(root: Path) -> None:
    (root / "state").write_text("kept", encoding="utf-8")


def _tree(root: Path) -> dict[str, str | None]:
    """Every path under `root`, relative: a file's text, or `None` for a folder."""
    return {
        path.relative_to(root).as_posix(): (
            path.read_text(encoding="utf-8") if path.is_file() else None
        )
        for path in root.rglob("*")
    }


@pytest.mark.parametrize(
    ("prepare", "target", "fails", "tree"),
    [
        pytest.param(
            _nothing, "a/runs", False, {"a": None, "a/runs": None}, id="missing-with-parent"
        ),
        pytest.param(
            _runs_with_a_file,
            "runs",
            False,
            {"runs": None, "runs/keep.txt": "kept"},
            id="existing-with-a-file",
        ),
        pytest.param(_a_file_named_state, "state", True, {"state": "kept"}, id="a-file"),
    ],
)
def test_make_state_directory_makes_a_missing_folder_keeps_an_existing_one_and_refuses_a_file(
    tmp_path: Path,
    prepare: Callable[[Path], None],
    target: str,
    fails: bool,  # noqa: FBT001 - a column of the table
    tree: dict[str, str | None],
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    prepare(root)
    state = root / target

    detail: str | None = None
    try:
        make_state_directory(state)
    except AgentRuntimeError as error:
        detail = error.detail

    if fails:
        assert detail is not None
        assert detail.startswith(f"cannot write the state directory {state}: ")
    else:
        assert detail is None
    assert _tree(root) == tree
