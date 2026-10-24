"""The take's edges: the copying of changed paths, the dropped paths and the faults."""

import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

import pytest

from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.take import copy_changed
from factory.domain.errors import WorkItemFormatError
from factory.domain.git import ChangedPath, ChangeKind
from git_support import write_files
from human_clone import HumanClone
from take_support import (
    AGENT_TEXT,
    changed,
    dataset_of,
    dataset_text,
    take_stage,
    write_dataset,
)
from undo_support import GUIDE, PATH, start_stage
from work_item_support import checkout_text

SOURCE_TEXT = "source\n"
TARGET_TEXT = "target\n"
OUTSIDE_TEXT = "outside\n"
BROKEN_FRONT_MATTER = "---\nstage: [unclosed\n  : :\n---\n# First story\n"


class Trees(NamedTuple):
    """The source and target trees of a copy, and a folder outside both."""

    source: Path
    target: Path
    outside: Path


Setup = Callable[[Trees], list[ChangedPath]]
Check = Callable[[Trees], None]


@pytest.fixture
def trees(tmp_path: Path) -> Trees:
    """Empty source and target trees, and an outside folder holding `file.txt`."""
    found = Trees(tmp_path / "source", tmp_path / "target", tmp_path / "outside")
    found.source.mkdir()
    found.target.mkdir()
    write_files(found.outside, {"file.txt": OUTSIDE_TEXT})
    return found


def _file(root: Path, path: str, text: str, mode: int) -> None:
    write_files(root, {path: text})
    (root / path).chmod(mode)


def _mode(path: Path) -> int:
    return path.stat().st_mode & 0o777


def _change(path: str, kind: ChangeKind) -> ChangedPath:
    return ChangedPath(path=path, change=kind)


def _added_file(mode: int) -> Setup:
    def setup(trees: Trees) -> list[ChangedPath]:
        _file(trees.source, "src/deep/run.sh", SOURCE_TEXT, mode)
        return [_change("src/deep/run.sh", "added")]

    return setup


def _arrived_with(mode: int) -> Check:
    def check(trees: Trees) -> None:
        target = trees.target / "src/deep/run.sh"
        assert target.read_text(encoding="utf-8") == SOURCE_TEXT
        assert _mode(target) == mode

    return check


def _modified_file(trees: Trees) -> list[ChangedPath]:
    _file(trees.source, "src/a.py", SOURCE_TEXT, 0o644)
    _file(trees.target, "src/a.py", TARGET_TEXT, 0o755)
    return [_change("src/a.py", "modified")]


def _replaced(trees: Trees) -> None:
    target = trees.target / "src/a.py"
    assert not target.is_symlink()
    assert target.read_text(encoding="utf-8") == SOURCE_TEXT
    assert _mode(target) == 0o644


def _deleted_file(trees: Trees) -> list[ChangedPath]:
    _file(trees.target, "src/a.py", TARGET_TEXT, 0o644)
    return [_change("src/a.py", "deleted")]


def _deleted_missing(trees: Trees) -> list[ChangedPath]:
    del trees
    return [_change("src/a.py", "deleted")]


def _gone(trees: Trees) -> None:
    assert not (trees.target / "src/a.py").exists()
    assert not (trees.target / "src/a.py").is_symlink()


def _added_link(trees: Trees) -> list[ChangedPath]:
    (trees.source / "src").mkdir()
    (trees.source / "src/link").symlink_to(trees.outside / "file.txt")
    return [_change("src/link", "added")]


def _link_arrived(trees: Trees) -> None:
    target = trees.target / "src/link"
    assert target.is_symlink()
    assert os.readlink(target) == str(trees.outside / "file.txt")


def _modified_over_link(trees: Trees) -> list[ChangedPath]:
    _file(trees.source, "src/a.py", SOURCE_TEXT, 0o644)
    (trees.target / "src").mkdir()
    (trees.target / "src/a.py").symlink_to(trees.outside / "file.txt")
    return [_change("src/a.py", "modified")]


def _link_replaced(trees: Trees) -> None:
    target = trees.target / "src/a.py"
    assert not target.is_symlink()
    assert target.read_text(encoding="utf-8") == SOURCE_TEXT
    assert (trees.outside / "file.txt").read_text(encoding="utf-8") == OUTSIDE_TEXT


def _added_over_folder(trees: Trees) -> list[ChangedPath]:
    _file(trees.source, "src/a.py", SOURCE_TEXT, 0o644)
    write_files(trees.target, {"src/a.py/inner.txt": TARGET_TEXT})
    return [_change("src/a.py", "added")]


def _folder_replaced(trees: Trees) -> None:
    target = trees.target / "src/a.py"
    assert target.is_file()
    assert not target.is_symlink()
    assert target.read_text(encoding="utf-8") == SOURCE_TEXT


def _deleted_folder_link(trees: Trees) -> list[ChangedPath]:
    (trees.target / "src").mkdir()
    (trees.target / "src/a.py").symlink_to(trees.outside, target_is_directory=True)
    return [_change("src/a.py", "deleted")]


def _folder_link_gone(trees: Trees) -> None:
    _gone(trees)
    assert (trees.outside / "file.txt").read_text(encoding="utf-8") == OUTSIDE_TEXT


def _deleted_dangling_link(trees: Trees) -> list[ChangedPath]:
    (trees.target / "src").mkdir()
    (trees.target / "src/a.py").symlink_to(trees.outside / "missing.txt")
    return [_change("src/a.py", "deleted")]


@pytest.mark.parametrize(
    ("setup", "check"),
    [
        pytest.param(_added_file(0o755), _arrived_with(0o755), id="added-executable"),
        pytest.param(_added_file(0o644), _arrived_with(0o644), id="added-plain"),
        pytest.param(_modified_file, _replaced, id="modified"),
        pytest.param(_deleted_file, _gone, id="deleted"),
        pytest.param(_deleted_missing, _gone, id="deleted-missing"),
        pytest.param(_added_link, _link_arrived, id="added-link"),
        pytest.param(_modified_over_link, _link_replaced, id="modified-over-link"),
        pytest.param(_added_over_folder, _folder_replaced, id="added-over-folder"),
        pytest.param(_deleted_folder_link, _folder_link_gone, id="deleted-folder-link"),
        pytest.param(_deleted_dangling_link, _gone, id="deleted-dangling-link"),
    ],
)
def test_copy_changed_mirrors_each_change_without_following_a_link(
    trees: Trees, setup: Setup, check: Check
) -> None:
    changes = setup(trees)

    copy_changed(trees.source, trees.target, changes)

    check(trees)


def _listing(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


@pytest.mark.parametrize("path", ["/abs", "a/../b"])
def test_copy_changed_refuses_a_path_outside_the_tree_before_copying_anything(
    trees: Trees, path: str
) -> None:
    _file(trees.source, "src/new.py", SOURCE_TEXT, 0o644)
    listing = _listing(trees.target)

    with pytest.raises(ValueError, match=re.escape(path)):
        copy_changed(
            trees.source, trees.target, [_change("src/new.py", "added"), _change(path, "added")]
        )

    assert _listing(trees.target) == listing


@pytest.mark.parametrize(
    ("change", "host"),
    [
        pytest.param(
            ChangedPath(path="checkout/.venv/bin/python", change="added"),
            ".venv/bin/python",
            id="ignored",
        ),
        pytest.param(
            ChangedPath(path="checkout/.git/config", change="modified"),
            ".git/config",
            id="git-folder",
        ),
        pytest.param(
            ChangedPath(path="checkout/src/.git/HEAD", change="added"),
            "src/.git/HEAD",
            id="nested-git",
        ),
        pytest.param(
            ChangedPath(path="home/.claude.json", change="added"), ".claude.json", id="home"
        ),
        pytest.param(ChangedPath(path="caches/uv/x", change="added"), "uv/x", id="elsewhere"),
        pytest.param(
            ChangedPath(path="checkout", change="added"), "checkout", id="checkout-itself"
        ),
    ],
)
def test_dropped_paths_are_neither_taken_nor_left(
    boundaries: Boundaries, human: HumanClone, change: ChangedPath, host: str
) -> None:
    start = start_stage(boundaries, human, write_paths=["*"])
    write_files(boundaries.checkout, {".gitignore": ".venv/\n"})
    if change.path != "checkout":
        write_files(dataset_of(boundaries), {change.path: AGENT_TEXT})

    report = take_stage(boundaries, start, [change])

    assert checkout_text(boundaries, host) != AGENT_TEXT
    assert report.left == []


def _without_work_item(boundaries: Boundaries, start: StageStart) -> StageStart:
    commit = boundaries.git.resolve("origin/main")
    assert commit is not None
    return StageStart(commit=commit, claim=start.claim)


def _with_broken_work_item(boundaries: Boundaries, start: StageStart) -> StageStart:
    write_files(boundaries.checkout, {PATH: BROKEN_FRONT_MATTER})
    commit = boundaries.git.commit("break the work item")
    return StageStart(commit=commit, claim=start.claim)


@pytest.mark.parametrize("baseline", [_without_work_item, _with_broken_work_item])
def test_a_missing_or_unreadable_baseline_raises_before_anything_is_taken(
    boundaries: Boundaries,
    human: HumanClone,
    baseline: Callable[[Boundaries, StageStart], StageStart],
) -> None:
    start = baseline(boundaries, start_stage(boundaries, human, write_paths=["*"]))
    write_dataset(boundaries, {"src/new.py": AGENT_TEXT})

    with pytest.raises(WorkItemFormatError, match=re.escape(PATH)):
        take_stage(boundaries, start, [changed("src/new.py", "added")])

    assert checkout_text(boundaries, "src/new.py") is None


def test_left_ascends_without_repeats(boundaries: Boundaries, human: HumanClone) -> None:
    start = start_stage(boundaries, human)
    write_dataset(boundaries, {"docs/z.md": AGENT_TEXT, GUIDE: AGENT_TEXT, "a.txt": AGENT_TEXT})
    changes = [
        changed("docs/z.md", "added"),
        changed(GUIDE, "modified"),
        changed("a.txt", "added"),
        changed(GUIDE, "modified"),
    ]

    report = take_stage(boundaries, start, changes)

    assert report.left == ["a.txt", GUIDE, "docs/z.md"]
    assert dataset_text(boundaries, GUIDE) == AGENT_TEXT
