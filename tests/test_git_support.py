"""Tests of the copied remote: the session's template, its copies and the fixtures on them."""

from pathlib import Path

import pytest

from git_support import REMOTE_FILES, clone, copy_remote, make_remote, remote_commit, run_git
from proof_support import build_world


@pytest.fixture
def template(tmp_path: Path) -> Path:
    """Return a folder of this test's own that `make_remote` filled."""
    return make_remote(tmp_path / "template").parent


def _push_commit(remote: Path, work: Path) -> str:
    """Clone `remote` into `work`, push one new commit to its `main` and return the commit."""
    clone(remote, work)
    (work / "pushed.txt").write_text("pushed\n", encoding="utf-8")
    run_git(work, "add", "-A")
    run_git(work, "commit", "-q", "-m", "pushed")
    run_git(work, "push", "-q", "origin", "main")
    return run_git(work, "rev-parse", "HEAD").strip()


def _files(work_tree: Path) -> dict[str, str]:
    return {
        path.relative_to(work_tree).as_posix(): path.read_text(encoding="utf-8")
        for path in work_tree.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(work_tree).parts
    }


def test_copy_is_a_bare_remote_at_the_templates_main(template: Path, tmp_path: Path) -> None:
    root = tmp_path / "copy"

    remote = copy_remote(template, root)

    assert remote == root / "remote.git"
    assert run_git(remote, "rev-parse", "--is-bare-repository").strip() == "true"
    assert remote_commit(remote, "main") is not None
    assert remote_commit(remote, "main") == remote_commit(template / "remote.git", "main")
    assert (root / "seed").is_dir()


def test_clone_of_the_copy_holds_exactly_the_remote_files(template: Path, tmp_path: Path) -> None:
    remote = copy_remote(template, tmp_path / "copy")

    work_tree = clone(remote, tmp_path / "work")

    assert _files(work_tree) == REMOTE_FILES


def test_push_to_the_copy_leaves_the_template_alone(template: Path, tmp_path: Path) -> None:
    template_remote = template / "remote.git"
    before = remote_commit(template_remote, "main")
    remote = copy_remote(template, tmp_path / "copy")

    pushed = _push_commit(remote, tmp_path / "work")

    assert remote_commit(remote, "main") == pushed
    assert remote_commit(template_remote, "main") == before


def test_push_to_the_template_leaves_the_copy_alone(template: Path, tmp_path: Path) -> None:
    template_remote = template / "remote.git"
    remote = copy_remote(template, tmp_path / "copy")
    before = remote_commit(remote, "main")

    pushed = _push_commit(template_remote, tmp_path / "work")

    assert remote_commit(template_remote, "main") == pushed
    assert remote_commit(remote, "main") == before


@pytest.mark.parametrize(
    ("relative_root", "present", "refused"),
    [
        ("missing/two-deep", None, False),
        ("empty", None, False),
        ("holds-remote", "remote.git", True),
        ("holds-seed", "seed", True),
    ],
)
def test_copy_creates_its_root_and_refuses_one_already_filled(
    template: Path, tmp_path: Path, relative_root: str, present: str | None, refused: bool
) -> None:
    root = tmp_path / relative_root
    if relative_root != "missing/two-deep":
        root.mkdir()
    if present is not None:
        (root / present).mkdir()
        (root / present / "marker.txt").write_text("before\n", encoding="utf-8")

    if refused:
        with pytest.raises(FileExistsError):
            copy_remote(template, root)
        assert present is not None
        assert sorted(path.name for path in (root / present).iterdir()) == ["marker.txt"]
        assert (root / present / "marker.txt").read_text(encoding="utf-8") == "before\n"
        other = "seed" if present == "remote.git" else "remote.git"
        assert not (root / other).exists()
    else:
        remote = copy_remote(template, root)
        assert remote == root / "remote.git"
        assert remote_commit(remote, "main") == remote_commit(template / "remote.git", "main")
        assert (root / "seed").is_dir()


def test_copy_runs_no_git(template: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    no_tools = tmp_path / "no-tools"
    no_tools.mkdir()
    with monkeypatch.context() as patch:
        patch.setenv("PATH", str(no_tools))
        remote = copy_remote(template, tmp_path / "copy")

    assert remote == tmp_path / "copy" / "remote.git"
    assert remote_commit(remote, "main") == remote_commit(template / "remote.git", "main")


def test_remote_fixture_is_a_copy_of_the_session_template(
    tmp_path: Path, remote: Path, remote_template: Path
) -> None:
    assert remote == tmp_path / "origin" / "remote.git"
    assert not remote.resolve().is_relative_to(remote_template.resolve())
    assert remote_commit(remote, "main") is not None
    assert remote_commit(remote, "main") == remote_commit(remote_template / "remote.git", "main")


def test_world_with_a_template_copies_its_remote(template: Path, tmp_path: Path) -> None:
    world = build_world(tmp_path / "world", template=template)

    assert remote_commit(world.remote, "main") == remote_commit(template / "remote.git", "main")


def test_world_without_a_template_makes_its_own_remote(tmp_path: Path) -> None:
    world = build_world(tmp_path / "world")

    assert remote_commit(world.remote, "main") is not None
    assert _files(clone(world.remote, tmp_path / "work")) == REMOTE_FILES
