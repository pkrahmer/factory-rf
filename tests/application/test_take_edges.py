"""The take's edges: the shared copying, the paths it drops and a stage start it cannot read."""

import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from factory.application.boundaries import Boundaries
from factory.application.claims import StageStart
from factory.application.take import copy_changed
from factory.domain.errors import WorkItemFormatError
from factory.domain.git import ChangedPath
from git_support import write_files
from human_clone import HumanClone
from take_support import AGENT_TEXT, changes, make_dataset, run_take, tree, write_dataset
from undo_support import PATH, start_stage

BROKEN_FRONT_MATTER = "---\nstage: [unclosed\n  : :\n---\n# First story\n"
OUTSIDE_TEXT = "outside\n"
SOURCE_TEXT = "from the source\n"
TARGET_TEXT = "on the target\n"


@dataclass(frozen=True)
class Trees:
    """The source and target trees of a copy, and a folder outside both."""

    source: Path
    target: Path
    outside: Path


Prepare = Callable[[Trees], list[ChangedPath]]
Verify = Callable[[Trees], None]


@pytest.fixture
def trees(tmp_path: Path) -> Trees:
    """Empty source and target trees, and a folder outside them holding `file.txt`."""
    found = Trees(tmp_path / "source", tmp_path / "target", tmp_path / "outside")
    for folder in (found.source, found.target, found.outside):
        folder.mkdir()
    (found.outside / "file.txt").write_text(OUTSIDE_TEXT, encoding="utf-8")
    return found


def _file(path: Path, text: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(mode)


def _mode(path: Path) -> int:
    return path.lstat().st_mode & 0o777


def _added(mode: int) -> Prepare:
    def prepare(trees: Trees) -> list[ChangedPath]:
        _file(trees.source / "a" / "b" / "run.sh", SOURCE_TEXT, mode)
        return changes(("a/b/run.sh", "added"))

    return prepare


def _arrived(mode: int) -> Verify:
    def verify(trees: Trees) -> None:
        target = trees.target / "a" / "b" / "run.sh"
        assert target.read_text(encoding="utf-8") == SOURCE_TEXT
        assert _mode(target) == mode

    return verify


def _modified(trees: Trees) -> list[ChangedPath]:
    _file(trees.source / "src" / "kept.py", SOURCE_TEXT, 0o644)
    _file(trees.target / "src" / "kept.py", TARGET_TEXT, 0o755)
    return changes(("src/kept.py", "modified"))


def _replaced(trees: Trees) -> None:
    target = trees.target / "src" / "kept.py"
    assert target.read_text(encoding="utf-8") == SOURCE_TEXT
    assert _mode(target) == 0o644


def _deleted(trees: Trees) -> list[ChangedPath]:
    _file(trees.target / "src" / "old.py", TARGET_TEXT)
    return changes(("src/old.py", "deleted"))


def _deleted_missing(trees: Trees) -> list[ChangedPath]:
    del trees
    return changes(("src/never.py", "deleted"))


def _gone(trees: Trees) -> None:
    for name in ("src/old.py", "src/never.py", "src/link"):
        assert not (trees.target / name).is_symlink()
        assert not (trees.target / name).exists()


def _added_link(trees: Trees) -> list[ChangedPath]:
    # A dangling target: a copy that followed the link would find nothing to read.
    (trees.source / "src").mkdir()
    os.symlink("missing.txt", trees.source / "src" / "link")
    return changes(("src/link", "added"))


def _link_arrived(trees: Trees) -> None:
    target = trees.target / "src" / "link"
    assert target.is_symlink()
    assert os.readlink(target) == "missing.txt"


def _modified_over_link(trees: Trees) -> list[ChangedPath]:
    _file(trees.source / "src" / "kept.py", SOURCE_TEXT)
    (trees.target / "src").mkdir()
    (trees.target / "src" / "kept.py").symlink_to(trees.outside / "file.txt")
    return changes(("src/kept.py", "modified"))


def _link_replaced(trees: Trees) -> None:
    target = trees.target / "src" / "kept.py"
    assert not target.is_symlink()
    assert target.read_text(encoding="utf-8") == SOURCE_TEXT
    assert (trees.outside / "file.txt").read_text(encoding="utf-8") == OUTSIDE_TEXT


def _added_over_folder(trees: Trees) -> list[ChangedPath]:
    _file(trees.source / "src" / "entry", SOURCE_TEXT)
    _file(trees.target / "src" / "entry" / "inside.txt", TARGET_TEXT)
    return changes(("src/entry", "added"))


def _folder_replaced(trees: Trees) -> None:
    target = trees.target / "src" / "entry"
    assert target.is_file()
    assert not target.is_symlink()
    assert target.read_text(encoding="utf-8") == SOURCE_TEXT


def _deleted_folder_link(trees: Trees) -> list[ChangedPath]:
    (trees.target / "src").mkdir()
    (trees.target / "src" / "link").symlink_to(trees.outside, target_is_directory=True)
    return changes(("src/link", "deleted"))


def _deleted_dangling_link(trees: Trees) -> list[ChangedPath]:
    (trees.target / "src").mkdir()
    (trees.target / "src" / "link").symlink_to(trees.outside / "missing.txt")
    return changes(("src/link", "deleted"))


def _outside_kept(trees: Trees) -> None:
    _gone(trees)
    assert (trees.outside / "file.txt").read_text(encoding="utf-8") == OUTSIDE_TEXT


def _refused(path: str) -> Prepare:
    def prepare(trees: Trees) -> list[ChangedPath]:
        _file(trees.source / "src" / "first.py", SOURCE_TEXT)
        return changes(("src/first.py", "added"), (path, "added"))

    return prepare


@pytest.mark.parametrize(
    ("prepare", "verify", "refused"),
    [
        pytest.param(_added(0o755), _arrived(0o755), None, id="added-executable"),
        pytest.param(_added(0o644), _arrived(0o644), None, id="added-plain"),
        pytest.param(_modified, _replaced, None, id="modified"),
        pytest.param(_deleted, _gone, None, id="deleted"),
        pytest.param(_deleted_missing, _gone, None, id="deleted-missing"),
        pytest.param(_added_link, _link_arrived, None, id="added-link"),
        pytest.param(_modified_over_link, _link_replaced, None, id="modified-over-a-link"),
        pytest.param(_added_over_folder, _folder_replaced, None, id="added-over-a-folder"),
        pytest.param(_deleted_folder_link, _outside_kept, None, id="deleted-folder-link"),
        pytest.param(_deleted_dangling_link, _outside_kept, None, id="deleted-dangling-link"),
        pytest.param(_refused("/abs"), None, "/abs", id="absolute"),
        pytest.param(_refused("a/../b"), None, "a/../b", id="dot-dot"),
    ],
)
def test_copy_changed_mirrors_each_changed_path_into_the_target(
    trees: Trees, prepare: Prepare, verify: Verify | None, refused: str | None
) -> None:
    changed = prepare(trees)

    if refused is None:
        copy_changed(trees.source, trees.target, changed)
    else:
        before = tree(trees.target)
        with pytest.raises(ValueError, match=re.escape(refused)):
            copy_changed(trees.source, trees.target, changed)
        assert tree(trees.target) == before

    if verify is not None:
        verify(trees)


@pytest.mark.parametrize(
    ("path", "change"),
    [
        pytest.param("checkout/.venv/bin/python", "added", id="ignored"),
        pytest.param("checkout/.git/config", "modified", id="git-folder"),
        pytest.param("checkout/src/.git/HEAD", "added", id="nested-git-folder"),
        pytest.param("home/.claude.json", "added", id="home"),
        pytest.param("caches/uv/x", "added", id="elsewhere"),
        pytest.param("checkout", "added", id="the-checkout-itself"),
    ],
)
def test_a_dropped_path_is_neither_taken_nor_left(
    boundaries: Boundaries, human: HumanClone, tmp_path: Path, path: str, change: str
) -> None:
    human.push_file("main", ".gitignore", ".venv/\n")
    start = start_stage(boundaries, human)
    mount_point = make_dataset(boundaries, tmp_path)
    if path != "checkout":
        write_dataset(mount_point, {path: AGENT_TEXT})
    host = tree(boundaries.checkout, skip_git=True)
    git_config = (boundaries.checkout / ".git" / "config").read_bytes()

    report = run_take(boundaries, start, mount_point, changes((path, change)))

    assert report.left == []
    assert tree(boundaries.checkout, skip_git=True) == host
    assert (boundaries.checkout / ".git" / "config").read_bytes() == git_config


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
    tmp_path: Path,
    baseline: Callable[[Boundaries, StageStart], StageStart],
) -> None:
    start = baseline(boundaries, start_stage(boundaries, human, write_paths=["src/*"]))
    mount_point = make_dataset(boundaries, tmp_path)
    write_dataset(mount_point, {"checkout/src/new.py": AGENT_TEXT})
    host = tree(boundaries.checkout, skip_git=True)

    with pytest.raises(WorkItemFormatError, match=re.escape(PATH)):
        run_take(boundaries, start, mount_point, changes(("checkout/src/new.py", "added")))

    assert not (boundaries.checkout / "src" / "new.py").exists()
    assert tree(boundaries.checkout, skip_git=True) == host
