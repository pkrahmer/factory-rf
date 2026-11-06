"""The fixture `checkout`: a copy of the repository's tracked files at the checked commit."""

from pathlib import Path

from factory.hosting.adapters.git_cli import GitCli
from factory.shared.application.document_examples import Fixture

CHECKED_COMMIT = "HEAD"


class CheckoutFixture(Fixture):
    """Copies the files tracked at `HEAD` of the working copy `git` stands for."""

    def __init__(self, git: GitCli) -> None:
        """Copy from the working copy of `git`."""
        self._git = git

    def prepare(self, folder: Path) -> dict[str, str]:
        """Write the tracked files at the checked commit into `folder`; no extra environment."""
        self._git.export(CHECKED_COMMIT, folder)
        return {}
