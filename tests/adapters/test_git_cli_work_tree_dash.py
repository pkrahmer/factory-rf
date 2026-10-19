"""The work tree's id leaves out a path that starts with a dash as a literal path."""

from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from git_support import CHECKOUT, write_files

DASH_TREE = {"a.md": "a\n", "-x.md": "x\n", "--y.md": "y\n"}


@pytest.mark.parametrize(
    ("left_out", "removed"),
    [
        pytest.param(["-x.md", "--y.md"], ["-x.md", "--y.md"], id="both-dash-files"),
        pytest.param(["-x.md"], ["-x.md"], id="single-dash-file-only"),
        pytest.param(["-*"], ["-x.md", "--y.md"], id="dash-pattern"),
        pytest.param(["a.md"], ["a.md"], id="plain-file-only"),
    ],
)
def test_a_left_out_path_that_starts_with_a_dash_is_removed_as_a_literal_path(
    tmp_path: Path, checkout: GitCli, left_out: list[str], removed: list[str]
) -> None:
    directory = tmp_path / CHECKOUT
    write_files(directory, DASH_TREE)

    actual = checkout.work_tree_id(left_out)
    for name in removed:
        (directory / name).unlink()

    assert actual == checkout.work_tree_id()
