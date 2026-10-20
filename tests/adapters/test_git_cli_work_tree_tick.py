"""The work tree's id sees a change made in the timestamp tick of the last index write."""

import os
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from git_support import CHECKOUT, run_git, write_files

PAST_NS = 1_600_000_000_000_000_000


def _set_past_time(*paths: Path) -> None:
    for path in paths:
        os.utime(path, ns=(PAST_NS, PAST_NS))


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("two\n", id="same-size"),
        pytest.param("three\n", id="other-size"),
    ],
)
def test_a_change_in_the_tick_of_the_last_index_write_is_seen(
    tmp_path: Path, checkout: GitCli, text: str
) -> None:
    directory = tmp_path / CHECKOUT
    run_git(directory, "config", "core.trustctime", "false")
    write_files(directory, {"kept.log": "one\n"})
    _set_past_time(directory / "kept.log")
    checkout.commit("kept")
    write_files(directory, {"kept.log": text})
    _set_past_time(directory / "kept.log", directory / ".git" / "index")

    seen = checkout.work_tree_id()
    checkout.commit("edit")

    assert seen == run_git(directory, "rev-parse", "HEAD^{tree}").strip()
