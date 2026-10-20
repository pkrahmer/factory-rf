"""The interface through which the factory reaches git."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from factory.domain.git import (
    ChangedPath,
    CommitId,
    CommitInfo,
    MergeOutcome,
    PushOutcome,
    RemoteBranch,
    TreeId,
    WorkTreeStatus,
)


class Git(ABC):
    """One working copy and its remote; every failing call raises `GitError`."""

    @abstractmethod
    def fetch(self) -> None:
        """Fetch from the remote and drop the remote-tracking branches it deleted.

        Raises `FetchFailed` on any failure.
        """

    @abstractmethod
    def remote_branches(self) -> list[RemoteBranch]:
        """The remote-tracking branches, sorted by name; local branches never appear."""

    @abstractmethod
    def resolve(self, ref: str) -> CommitId | None:
        """The commit `ref` points to, or `None` when there is no such ref."""

    @abstractmethod
    def show_file(self, ref: str, path: str) -> str | None:
        """The text of the file `path` at `ref`, or `None` when it is not a file there."""

    @abstractmethod
    def list_files(self, ref: str, directory: str) -> list[str]:
        """The paths of all files under `directory` at `ref`, recursive and sorted."""

    @abstractmethod
    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """Whether `ancestor` is reachable from `descendant`, a commit being its own ancestor."""

    @abstractmethod
    def log(
        self, ref: str, *, since: str | None = None, path: str | None = None
    ) -> list[CommitInfo]:
        """The commits reachable from `ref`, newest first and each before its parents.

        With `since`, only those not reachable from `since`; with `path`, only those that
        changed it or anything under it.
        """

    @abstractmethod
    def changed_paths(self, since: str) -> list[ChangedPath]:
        """The paths whose content differs between the commit `since` and the work tree.

        Committed, staged, unstaged and untracked changes count, ignored files do not; a
        rename is a deletion plus an addition. Sorted by path.
        """

    @abstractmethod
    def status(self) -> WorkTreeStatus:
        """The checked-out branch, `HEAD`, and every path that differs from `HEAD`, sorted."""

    @abstractmethod
    def clone(self, url: str) -> None:
        """Clone `url` into the working copy's directory, which must be missing or empty."""

    @abstractmethod
    def checkout(self, branch: str, *, start_point: str | None = None) -> None:
        """Switch to `branch`; with `start_point`, create it there or reset it to it.

        A branch that exists only on the remote is created at the remote's commit.
        """

    @abstractmethod
    def commit(self, message: str) -> CommitId:
        """Stage every change, commit it with `message` as given and return the new commit.

        Raises `NothingToCommit` when there is no change to commit.
        """

    @abstractmethod
    def push(self, branch: str) -> PushOutcome:
        """Push `branch` to the remote, never forced, and say how the remote took it."""

    @abstractmethod
    def delete_remote_branch(self, branch: str) -> PushOutcome:
        """Delete `branch` on the remote and its remote-tracking ref, and say how that went.

        A branch already gone from the remote counts as `"pushed"`.
        """

    @abstractmethod
    def delete_branch(self, branch: str) -> None:
        """Delete the local `branch`, merged or not; a missing branch is no error."""

    @abstractmethod
    def merge(self, ref: str, *, fast_forward_only: bool = False) -> MergeOutcome:
        """Merge `ref` into the checked-out branch, fast-forwarding where it can.

        A conflict is aborted before `"conflict"` is returned, so nothing is left half done.
        """

    @abstractmethod
    def reset_to(self, ref: str) -> None:
        """Point the current branch at `ref`, discard every tracked change and clean the tree.

        Untracked files and directories are removed, ignored ones stay.
        """

    @abstractmethod
    def revert_paths(self, commit: str, paths: Sequence[str]) -> None:
        """Bring each of `paths` to its content at `commit`, in the work tree and the index.

        A path missing at `commit` is deleted; one that is nowhere is skipped. Paths are
        repository-relative with forward slashes: an absolute path or a `..` segment raises
        `ValueError` before any path is changed.
        """

    @abstractmethod
    def move(self, source: str, destination: str) -> None:
        """Move the tracked file `source` to `destination`, staged as a rename.

        The destination's parent directories are created; an existing destination is refused.
        Both paths follow the rule of `revert_paths`: an absolute path or a `..` segment in
        either raises `ValueError` before anything is created.
        """

    @abstractmethod
    def seal(self) -> None:
        """Take the group's and others' write permission from the repository folder and its entries.

        Raises `RepositoryUnsealed` when the folder is missing, is a symbolic link, is not a
        directory, holds no regular file `HEAD` or belongs to another user, or when an entry
        cannot be read or changed.
        """

    @abstractmethod
    def check_seal(self) -> None:
        """Raise `RepositoryUnsealed` unless the repository folder is the factory's alone.

        That is a directory, not a symbolic link, of the factory's own user, that neither its
        group nor others may write and that holds a regular file `HEAD`. Changes nothing.
        """

    @abstractmethod
    def remove_nested_repositories(self) -> list[str]:
        """Remove every entry named `.git` below the working copy other than its own repository.

        A folder, a file or a symbolic link counts. Returns their paths relative to the working
        copy, `/`-separated and sorted; `[]` when there is none. Raises `RepositoryUnsealed`
        when one cannot be removed.
        """

    @abstractmethod
    def discard(self) -> None:
        """Remove the working copy and its repository; a missing working copy is no error."""

    @abstractmethod
    def work_tree_id(self, left_out: Sequence[str] = ()) -> TreeId:
        """The tree a commit of the work tree would record now, less the paths matching `left_out`.

        Tracked files count with their content in the work tree, untracked files that are
        not ignored count, deleted and ignored files do not. A path is left out when
        `matches_any(path, left_out)`. The index, `HEAD`, the refs and the work tree stay
        as they are.
        """

    @abstractmethod
    def remove_ignored(self) -> None:
        """Remove every untracked path the ignore rules match, a folder with all it holds.

        Tracked files, untracked paths no rule matches and the repository stay. A path that
        cannot be removed raises `GitError`.
        """
