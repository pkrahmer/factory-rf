"""The guard's path checks in the test process: each refusal comes before the first system call."""

from pathlib import Path

import pytest

from factory.adapters.landlock import restrict_writes
from factory.domain.errors import ConfinementError


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A folder A, a file P/f.txt and a link `dangling` to a missing path."""
    (tmp_path / "A").mkdir()
    (tmp_path / "P").mkdir()
    (tmp_path / "P" / "f.txt").write_text("f\n", encoding="utf-8")
    (tmp_path / "dangling").symlink_to(tmp_path / "nowhere")
    return tmp_path


@pytest.mark.parametrize(
    ("folders", "files", "detail"),
    [
        pytest.param(
            ["missing"],
            [],
            "cannot open <base>/missing: No such file or directory",
            id="missing-folder",
        ),
        pytest.param(
            [],
            ["missing.txt"],
            "cannot open <base>/missing.txt: No such file or directory",
            id="missing-file",
        ),
        pytest.param(
            ["P/f.txt", "missing"], [], "<base>/P/f.txt is not a folder", id="file-among-folders"
        ),
        pytest.param([], ["A", "missing.txt"], "<base>/A is a folder", id="folder-among-files"),
        pytest.param(["dangling"], [], "<base>/dangling is a symbolic link", id="link-folder"),
        pytest.param([], ["dangling"], "<base>/dangling is a symbolic link", id="link-file"),
        pytest.param(
            ["missing"],
            ["missing.txt"],
            "cannot open <base>/missing: No such file or directory",
            id="folders-first",
        ),
        pytest.param(
            ["missing", "absent"],
            [],
            "cannot open <base>/missing: No such file or directory",
            id="folders-in-order",
        ),
        pytest.param(
            [],
            ["missing.txt", "absent.txt"],
            "cannot open <base>/missing.txt: No such file or directory",
            id="files-in-order",
        ),
    ],
)
def test_a_path_that_cannot_be_ruled_is_refused_and_restricts_nothing(
    tree: Path, folders: list[str], files: list[str], detail: str
) -> None:
    with pytest.raises(ConfinementError) as raised:
        restrict_writes([tree / name for name in folders], [tree / name for name in files])

    assert raised.value.detail == detail.replace("<base>", str(tree))
    (tree / "A" / "after.txt").write_text("x\n", encoding="utf-8")
    assert (tree / "A" / "after.txt").read_text(encoding="utf-8") == "x\n"
