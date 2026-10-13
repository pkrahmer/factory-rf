"""The interface through which the factory reaches git."""

from typing import Protocol

from factory.domain.git import (
    ChangedPath,
    CommitId,
    CommitInfo,
    PushOutcome,
    RemoteBranch,
    WorkTreeStatus,
)


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

    def log(
        self, ref: str, *, since: str | None = None, path: str | None = None
    ) -> list[CommitInfo]:
        """The commits reachable from `ref`, newest first and each before its parents.

        With `since`, only those not reachable from `since`; with `path`, only those that
        changed it or anything under it.
        """
        ...

    def changed_paths(self, since: str) -> list[ChangedPath]:
        """The paths whose content differs between the commit `since` and the work tree.

        Committed, staged, unstaged and untracked changes count, ignored files do not; a
        rename is a deletion plus an addition. Sorted by path.
        """
        ...

    def status(self) -> WorkTreeStatus:
        """The checked-out branch, `HEAD`, and every path that differs from `HEAD`, sorted."""
        ...

    def clone(self, url: str) -> None:
        """Clone `url` into the working copy's directory, which must be missing or empty."""
        ...

    def checkout(self, branch: str, *, start_point: str | None = None) -> None:
        """Switch to `branch`; with `start_point`, create it there or reset it to it.

        A branch that exists only on the remote is created at the remote's commit.
        """
        ...

    def commit(self, message: str) -> CommitId:
        """Stage every change, commit it with `message` as given and return the new commit.

        Raises `NothingToCommit` when there is no change to commit.
        """
        ...

    def push(self, branch: str) -> PushOutcome:
        """Push `branch` to the remote, never forced, and say how the remote took it."""
        ...
