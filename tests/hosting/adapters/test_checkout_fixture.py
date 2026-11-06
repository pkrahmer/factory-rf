"""The fixture `checkout`: the tracked files at the checked commit, in an empty folder."""

from pathlib import Path

import pytest

from factory.hosting.adapters.checkout_fixture import CheckoutFixture
from factory.hosting.adapters.git_cli import GitCli
from factory.shared.domain.errors import FixtureError
from support.git_support import CHECKOUT


def test_the_checkout_fixture_copies_the_tracked_files_and_not_the_untracked_ones(
    tmp_path: Path, checkout: GitCli
) -> None:
    directory = tmp_path / CHECKOUT
    (directory / "tracked.md").write_text("tracked\n", encoding="utf-8")
    checkout.commit("Add a tracked file")
    (directory / "untracked.md").write_text("untracked\n", encoding="utf-8")
    folder = tmp_path / "example"
    folder.mkdir()

    CheckoutFixture(checkout).prepare(folder)

    assert (folder / "tracked.md").read_text(encoding="utf-8") == "tracked\n"
    assert not (folder / "untracked.md").exists()


def test_the_checkout_fixture_outside_a_git_repository_raises_a_fixture_error(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "not-a-repository"
    outside.mkdir()
    folder = tmp_path / "example"
    folder.mkdir()

    with pytest.raises(FixtureError):
        CheckoutFixture(GitCli(outside)).prepare(folder)
