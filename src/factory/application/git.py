"""The interface through which the factory reaches git."""

from typing import Protocol

from factory.domain.git import CommitId, RemoteBranch


class Git(Protocol):
    """One working copy and its remote; every failing call raises `GitError`."""

    def fetch(self) -> None:
        """Fetch from the remote and drop the remote-tracking branches it deleted.

        Raises `FetchFailed` on any failure.
        """
        ...

    def remote_branches(self) -> list[RemoteBranch]:
        """The remote-tracking branches, sorted by name; local branches never appear."""
        ...

    def resolve(self, ref: str) -> CommitId | None:
        """The commit `ref` points to, or `None` when there is no such ref."""
        ...

    def show_file(self, ref: str, path: str) -> str | None:
        """The text of the file `path` at `ref`, or `None` when it is not a file there."""
        ...

    def list_files(self, ref: str, directory: str) -> list[str]:
        """The paths of all files under `directory` at `ref`, recursive and sorted."""
        ...

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """Whether `ancestor` is reachable from `descendant`, a commit being its own ancestor."""
        ...
