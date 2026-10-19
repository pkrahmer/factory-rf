"""A watch on a clone without an origin/main ends with the git error the operator reads."""

import io
from dataclasses import replace
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.watcher import Watcher
from factory.domain.errors import GitError
from factory.domain.git import GitOptions
from factory.domain.pipeline_definition import PipelineDefinition
from factory.entry.watch import run_watch
from git_support import TEST_IDENTITY, run_git

UNRESOLVED = "resolve origin/main failed (no exit status): origin/main does not resolve"


@pytest.fixture
def empty_clone(boundaries: Boundaries, tmp_path: Path) -> Boundaries:
    """The boundaries on a clone of an empty bare remote."""
    run_git(tmp_path, "init", "-q", "--bare", "--initial-branch=main", "empty.git")
    run_git(tmp_path, "clone", "-q", str(tmp_path / "empty.git"), "empty-clone")
    git = GitCli(tmp_path / "empty-clone", GitOptions(identity=TEST_IDENTITY))
    return replace(boundaries, git=git)


@pytest.mark.parametrize("through", ["run_watch", "watcher"])
def test_an_unresolved_origin_main_raises_the_operators_git_error(
    empty_clone: Boundaries, definition: PipelineDefinition, through: str
) -> None:
    with pytest.raises(GitError) as raised:
        if through == "run_watch":
            run_watch(empty_clone, "factory-1", io.StringIO(), io.StringIO())
        else:
            Watcher(empty_clone, "factory-1").evaluate(definition)

    assert str(raised.value) == UNRESOLVED
