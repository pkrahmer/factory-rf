"""The git wrapper: the one class that runs the git command-line tool."""

import os
import shutil
import stat
import tempfile
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from factory.application.git import Git
from factory.domain.errors import FetchFailed, GitError, NothingToCommit, RepositoryUnsealed
from factory.domain.git import (
    ChangedPath,
    ChangeKind,
    CommitId,
    CommitInfo,
    GitOptions,
    MergeOutcome,
    PushOutcome,
    RemoteBranch,
    TreeId,
    WorkTreeStatus,
    check_branch_name,
    check_git_argument,
    check_repository_path,
)
from factory.domain.kill_points import KillPoint
from factory.domain.paths import REMOTE
from factory.domain.write_paths import matches_any

# The argument check is exported: every public operation passes it once, at this one name.
__all__ = ["GitCli", "check_git_argument"]

OUTPUT_TAIL_LINES = 30
REMOTE_PREFIX = f"refs/remotes/{REMOTE}/"
# The exit status by which `rev-parse --verify --quiet` and `merge-base --is-ancestor` say "no".
ANSWER_NO = 1
# The exit status by which git says it could not talk to the remote at all.
FATAL = 128
# One log record is id, parents, author, committer timestamp and message, each ended by NUL.
LOG_FORMAT = "%H%x00%P%x00%an%x00%ct%x00%B"
LOG_FIELDS = 5
# The write permission of the group and of others, which the git folder must not carry.
SHARED_WRITE = 0o022
DIFF_KINDS: dict[str, ChangeKind] = {"A": "added", "D": "deleted"}
UNREACHABLE_MARKERS = (
    "Could not read from remote repository",
    "does not appear to be a git repository",
    "unable to access",
    "Could not resolve host",
)


def _tail(output: str) -> str:
    return "\n".join(output.splitlines()[-OUTPUT_TAIL_LINES:])


def _command(arguments: list[str]) -> str:
    return " ".join(["git", *arguments])


def _blob_in_listing(listing: str, path: str) -> str | None:
    # One `ls-tree -z` entry is "<mode> <type> <object>\t<path>", entries end in NUL.
    for entry in filter(None, listing.split("\0")):
        meta, entry_path = entry.split("\t", 1)
        _mode, kind, blob = meta.split(" ")
        if entry_path == path and kind == "blob":
            return blob
    return None


def _commits_in_log(listing: str) -> list[CommitInfo]:
    fields = listing.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    commits = []
    for start in range(0, len(fields), LOG_FIELDS):
        commit, parents, author, timestamp, message = fields[start : start + LOG_FIELDS]
        commits.append(
            CommitInfo(
                commit=commit,
                parents=parents.split(),
                subject=message.split("\n", 1)[0],
                author=author,
                committed_at=datetime.fromtimestamp(int(timestamp), UTC),
            )
        )
    return commits


def _changes_in_diff(listing: str) -> dict[str, ChangeKind]:
    # `diff --name-status -z` alternates a status letter and the path, each ended by NUL.
    fields = [field for field in listing.split("\0") if field]
    return {
        path: DIFF_KINDS.get(status[0], "modified")
        for status, path in zip(fields[0::2], fields[1::2], strict=True)
    }


def _status_change(staged: str, unstaged: str) -> ChangeKind:
    if "D" in (staged, unstaged):
        return "deleted"
    if staged == "A":
        return "added"
    return "modified"


def _status_entry(entry: str) -> ChangedPath | None:
    # Porcelain v2: "1 XY ... <path>" is a change, "u XY ... <path>" an unmerged path,
    # "? <path>" an untracked one; with renames off no "2" entries appear.
    kind = entry[0]
    if kind == "?":
        return ChangedPath(path=entry[2:], change="added")
    if kind == "1":
        fields = entry.split(" ", 8)
        return ChangedPath(path=fields[8], change=_status_change(fields[1][0], fields[1][1]))
    if kind == "u":
        return ChangedPath(path=entry.split(" ", 10)[10], change="modified")
    return None


def _status_header(entries: list[str], name: str, placeholder: str) -> str | None:
    # Porcelain v2 headers read "# <name> <value>"; git writes `placeholder` for no value.
    prefix = f"# {name} "
    for entry in entries:
        if entry.startswith(prefix):
            value = entry.removeprefix(prefix)
            return None if value == placeholder else value
    return None


def _sorted_changes(changes: dict[str, ChangeKind]) -> list[ChangedPath]:
    return [ChangedPath(path=path, change=changes[path]) for path in sorted(changes)]


def _raise_unsealed(error: OSError) -> None:
    # `os.walk` skips a folder it cannot list unless its `onerror` raises.
    raise RepositoryUnsealed(f"{error.filename}: {error}") from error


def _close(path: Path) -> None:
    try:
        mode = path.lstat().st_mode
        if not stat.S_ISLNK(mode) and mode & SHARED_WRITE:
            path.chmod(stat.S_IMODE(mode) & ~SHARED_WRITE)
    except OSError as error:
        raise RepositoryUnsealed(f"{path}: {error}") from error


def _nested_repositories(root: Path) -> list[Path]:
    found: list[Path] = []
    # A folder the walk cannot list is skipped: the factory's git cannot look into it either.
    for parent, folders, files in os.walk(root, followlinks=False):
        here = Path(parent)
        if here != root and (".git" in folders or ".git" in files):
            found.append(here / ".git")
        if ".git" in folders:
            folders.remove(".git")
    return found


def _remove_entry(path: Path) -> None:
    try:
        if stat.S_ISDIR(path.lstat().st_mode):
            shutil.rmtree(path)
        else:
            path.unlink()
    except OSError as error:
        raise RepositoryUnsealed(f"{path}: {error}") from error


def _is_rejected(porcelain: str) -> bool:
    # A `push --porcelain` ref line is "<flag>\t<from>:<to>\t<summary>"; `!` marks a refusal.
    return any(line.startswith("!\t") for line in porcelain.splitlines())


def _is_unreachable(result: ProcessResult) -> bool:
    if result.exit_status != FATAL:
        return False
    return any(marker in result.stdout for marker in UNREACHABLE_MARKERS)


def _failed_push(arguments: list[str], result: ProcessResult) -> PushOutcome:
    if _is_rejected(result.stdout):
        return "rejected"
    if _is_unreachable(result):
        return "unreachable"
    raise GitError(_command(arguments), result.exit_status, _tail(result.stdout))


class GitCli(Git):
    """Git in one working copy, run with the user's and the system's configuration ignored."""

    def __init__(self, directory: Path, options: GitOptions | None = None) -> None:
        """Work in `directory` with `options`, or the default options."""
        self._directory = directory
        self._options = GitOptions() if options is None else options
        self._identity = self._options.identity

    def fetch(self) -> None:
        """Fetch from the remote and prune; any failure is `FetchFailed`."""
        self._run(["fetch", "--prune", REMOTE], error=FetchFailed)

    def remote_branches(self) -> list[RemoteBranch]:
        """The branches under the remote's tracking refs, sorted by name, without `HEAD`."""
        result = self._run(["for-each-ref", "--format=%(objectname) %(refname)", REMOTE_PREFIX])
        branches = []
        for line in result.stdout.splitlines():
            commit, refname = line.split(" ", 1)
            name = refname.removeprefix(REMOTE_PREFIX)
            if name != "HEAD":
                branches.append(RemoteBranch(name=name, commit=commit))
        return sorted(branches, key=lambda branch: branch.name)

    def resolve(self, ref: str) -> CommitId | None:
        """The commit id `ref` points to, or `None` when there is no such ref."""
        check_git_argument(ref)
        return self._resolve_unchecked(ref)

    def show_file(self, ref: str, path: str) -> str | None:
        """The text of `path` at `ref`, or `None` when it is absent or not a file."""
        check_git_argument(ref)
        blob = self._blob(ref, path)
        if blob is None:
            return None
        return self._run(["cat-file", "blob", blob]).stdout

    def list_files(self, ref: str, directory: str) -> list[str]:
        """The repository-relative paths of all files under `directory` at `ref`, sorted."""
        check_git_argument(ref)
        listing = self._run(["ls-tree", "-r", "-z", "--name-only", ref, "--", directory]).stdout
        prefix = f"{directory}/"
        return sorted(path for path in listing.split("\0") if path.startswith(prefix))

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """Whether `ancestor` is reachable from `descendant`."""
        check_git_argument(ancestor)
        check_git_argument(descendant)
        return self._is_ancestor_unchecked(ancestor, descendant)

    def log(
        self, ref: str, *, since: str | None = None, path: str | None = None
    ) -> list[CommitInfo]:
        """The commits reachable from `ref` and not from `since`, touching `path` if given."""
        check_git_argument(ref)
        if since is not None:
            check_git_argument(since)
        revisions = [ref] if since is None else [ref, f"^{since}"]
        paths = [] if path is None else [path]
        arguments = ["log", "-z", "--date-order", f"--format={LOG_FORMAT}", "--end-of-options"]
        listing = self._run([*arguments, *revisions, "--", *paths]).stdout
        return _commits_in_log(listing)

    def changed_paths(self, since: str) -> list[ChangedPath]:
        """The tracked paths that differ from `since`, and the untracked ones as added."""
        check_git_argument(since)
        diff = self._run(
            ["diff", "--name-status", "-z", "--no-renames", "--end-of-options", since, "--"]
        ).stdout
        changes = _changes_in_diff(diff)
        for path in self._untracked_paths():
            # A path dropped from the index but still on disk is a change, not a deletion.
            changes[path] = "modified" if path in changes else "added"
        return _sorted_changes(changes)

    def status(self) -> WorkTreeStatus:
        """The branch (`None` when detached), `HEAD` (`None` before the first commit), changes."""
        listing = self._run(
            ["status", "--porcelain=v2", "-z", "--branch", "--untracked-files=all", "--no-renames"]
        ).stdout
        entries = [entry for entry in listing.split("\0") if entry]
        changes: dict[str, ChangeKind] = {}
        for entry in entries:
            change = _status_entry(entry)
            if change is not None:
                changes[change.path] = change.change
        return WorkTreeStatus(
            branch=_status_header(entries, "branch.head", "(detached)"),
            head=_status_header(entries, "branch.oid", "(initial)"),
            changes=_sorted_changes(changes),
        )

    def clone(self, url: str) -> None:
        """Clone `url` into the bound directory, creating its missing parents."""
        check_git_argument(url)
        parent = self._directory.parent
        parent.mkdir(parents=True, exist_ok=True)
        self._run(["clone", "--quiet", url, str(self._directory)], cwd=parent)

    def checkout(self, branch: str, *, start_point: str | None = None) -> None:
        """Switch to `branch`; with `start_point`, create or reset it there first."""
        check_git_argument(branch)
        if start_point is None:
            # `switch` takes no paths, so a branch name is never read as a file.
            self._run(["switch", "--quiet", branch])
        else:
            check_git_argument(start_point)
            self._run(["switch", "--quiet", "--force-create", branch, start_point])

    def commit(self, message: str) -> CommitId:
        """Stage every change, commit with `message` verbatim and return the new `HEAD`."""
        self._run(["add", "--all"])
        staged = self._run(["diff", "--cached", "--quiet"], accepted=(0, 1))
        if staged.exit_status == 0:
            raise NothingToCommit("git commit", None, "nothing to commit")
        self._run(
            ["commit", "--quiet", "--no-gpg-sign", "--cleanup=verbatim", "--message", message]
        )
        return self._run(["rev-parse", "HEAD"]).stdout.strip()

    def push(self, branch: str) -> PushOutcome:
        """Push `branch` without force; a refusal or an unreachable remote is a value."""
        check_branch_name(branch)
        self._reach(KillPoint.BEFORE_PUSH)
        arguments = ["push", "--porcelain", "--set-upstream", REMOTE, f"refs/heads/{branch}"]
        result = self._execute(arguments)
        if result.exit_status == 0:
            self._reach(KillPoint.AFTER_PUSH)
            return "pushed"
        return _failed_push(arguments, result)

    def delete_remote_branch(self, branch: str) -> PushOutcome:
        """Delete `branch` on the remote; already gone counts as deleted, like `push`'s values."""
        check_branch_name(branch)
        arguments = ["push", "--porcelain", REMOTE, "--delete", f"refs/heads/{branch}"]
        result = self._execute(arguments)
        if result.exit_status == 0:
            # A branch deleted elsewhere leaves a stale tracking ref that no push removes.
            self._run(["update-ref", "-d", f"{REMOTE_PREFIX}{branch}"])
            return "pushed"
        return _failed_push(arguments, result)

    def delete_branch(self, branch: str) -> None:
        """Delete the local `branch` even when unmerged; a missing branch changes nothing."""
        check_git_argument(branch)
        if self._resolve_unchecked(f"refs/heads/{branch}") is None:
            return
        self._run(["branch", "--delete", "--force", branch])

    def merge(self, ref: str, *, fast_forward_only: bool = False) -> MergeOutcome:
        """Merge `ref` into `HEAD`; a conflict is aborted, any other refusal is a `GitError`."""
        check_git_argument(ref)
        self._resolve_or_raise(ref, "merge")
        if self._is_ancestor_unchecked(ref, "HEAD"):
            return "up_to_date"
        if self._is_ancestor_unchecked("HEAD", ref):
            self._run(["merge", "--quiet", "--ff-only", "--end-of-options", ref])
            return "fast_forwarded"
        if fast_forward_only:
            return "not_fast_forward"
        return self._merge_diverged(ref)

    def reset_to(self, ref: str) -> None:
        """Hard-reset the current branch to `ref`, then remove untracked files and directories."""
        check_git_argument(ref)
        # `reset` takes no `--end-of-options`, so it only ever sees a resolved commit id.
        commit = self._resolve_or_raise(ref, "reset")
        self._run(["reset", "--quiet", "--hard", commit, "--"])
        self._run(["clean", "--quiet", "--force", "-d"])

    def revert_paths(self, commit: str, paths: Sequence[str]) -> None:
        """Restore each path from `commit`, or delete it where `commit` does not have it."""
        check_git_argument(commit)
        for path in paths:
            check_repository_path(path)
        commit_id = self._resolve_or_raise(commit, "checkout")
        for path in paths:
            if self._blob(commit_id, path) is None:
                self._delete_path(path)
            else:
                self._run(["checkout", "--quiet", commit_id, "--", path])

    def move(self, source: str, destination: str) -> None:
        """Run `git mv`, after checking both paths and creating the destination's parents."""
        check_repository_path(source)
        check_repository_path(destination)
        (self._directory / destination).parent.mkdir(parents=True, exist_ok=True)
        self._run(["mv", "--", source, destination])

    def seal(self) -> None:
        """Take the group's and others' write bits from `.git` and every entry in it."""
        folder = self._check_git_folder()
        _close(folder)
        for parent, folders, files in os.walk(folder, onerror=_raise_unsealed):
            for name in [*folders, *files]:
                _close(Path(parent) / name)

    def check_seal(self) -> None:
        """Raise `RepositoryUnsealed` unless `.git` is the factory's alone; changes nothing."""
        folder = self._check_git_folder()
        if folder.lstat().st_mode & SHARED_WRITE:
            raise RepositoryUnsealed(f"{folder} is writable by its group or by others")

    def remove_nested_repositories(self) -> list[str]:
        """Remove each `.git` below the working copy but its own, without a git process."""
        found = _nested_repositories(self._directory)
        for path in found:
            _remove_entry(path)
        return sorted(path.relative_to(self._directory).as_posix() for path in found)

    def discard(self) -> None:
        """Remove the working copy with its `.git`; a missing one is no error."""
        if not os.path.lexists(self._directory):
            return
        try:
            shutil.rmtree(self._directory)
        except OSError as error:
            raise GitError("discard", None, str(error)) from error

    def remove_ignored(self) -> None:
        """Remove every untracked path that `.gitignore` or `.git/info/exclude` matches."""
        # The second `--force` also removes an ignored folder that holds a repository.
        self._run(["clean", "--quiet", "--force", "--force", "-d", "-X"])

    def work_tree_id(self, left_out: Sequence[str] = ()) -> TreeId:
        """Stage the work tree in a temporary index, drop the paths left out, write its tree."""
        with tempfile.TemporaryDirectory() as folder:
            index = Path(folder) / "index"
            # A copy of the own index lets git rehash only changed files and keeps a tracked
            # file that `.gitignore` matches, as a commit keeps it.
            own_index = self._directory / ".git" / "index"
            if own_index.is_file():
                shutil.copyfile(own_index, index)
            self._run(["add", "--all"], index=index)
            listing = self._run(["ls-files", "-z"], index=index).stdout
            dropped = [path for path in listing.split("\0") if path and matches_any(path, left_out)]
            if dropped:
                # update-index reads its arguments as literal paths, never as pathspecs.
                self._run(["update-index", "--force-remove", "--", *dropped], index=index)
            return self._run(["write-tree"], index=index).stdout.strip()

    # The helpers below take arguments their public caller has already checked.

    def _resolve_or_raise(self, ref: str, command: str) -> CommitId:
        commit = self._resolve_unchecked(ref)
        if commit is None:
            raise GitError(_command([command, ref]), None, f"unknown ref {ref}")
        return commit

    def _resolve_unchecked(self, ref: str) -> CommitId | None:
        result = self._run(
            ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], accepted=(0, ANSWER_NO)
        )
        if result.exit_status == ANSWER_NO:
            return None
        return result.stdout.strip()

    def _is_ancestor_unchecked(self, ancestor: str, descendant: str) -> bool:
        result = self._run(
            ["merge-base", "--is-ancestor", ancestor, descendant], accepted=(0, ANSWER_NO)
        )
        return result.exit_status == 0

    def _blob(self, ref: str, path: str) -> str | None:
        listing = self._run(["ls-tree", "-z", ref, "--", path]).stdout
        return _blob_in_listing(listing, path)

    def _delete_path(self, path: str) -> None:
        self._run(["rm", "--quiet", "--cached", "--ignore-unmatch", "--", path])
        file = self._directory / path
        if file.is_file() or file.is_symlink():
            file.unlink()

    def _merge_diverged(self, ref: str) -> MergeOutcome:
        arguments = ["merge", "--quiet", "--no-edit", "--no-gpg-sign", "--end-of-options", ref]
        result = self._execute(arguments)
        if result.exit_status == 0:
            return "merged"
        if self._resolve_unchecked("MERGE_HEAD") is not None:
            self._run(["merge", "--abort"])
            return "conflict"
        raise GitError(_command(arguments), result.exit_status, _tail(result.stdout))

    def _untracked_paths(self) -> list[str]:
        listing = self._run(["ls-files", "--others", "--exclude-standard", "-z"]).stdout
        return [path for path in listing.split("\0") if path]

    def _check_git_folder(self) -> Path:
        folder = self._directory / ".git"
        try:
            folder_stat = folder.lstat()
        except FileNotFoundError:
            raise RepositoryUnsealed(f"{folder} does not exist") from None
        mode = folder_stat.st_mode
        if stat.S_ISLNK(mode):
            raise RepositoryUnsealed(f"{folder} is a symbolic link")
        if not stat.S_ISDIR(mode):
            raise RepositoryUnsealed(f"{folder} is not a directory")
        owner, effective = folder_stat.st_uid, os.geteuid()
        if owner != effective:
            raise RepositoryUnsealed(f"{folder} belongs to the user {owner}, not to {effective}")
        head = folder / "HEAD"
        if not os.path.lexists(head) or not stat.S_ISREG(head.lstat().st_mode):
            raise RepositoryUnsealed(f"{folder} holds no HEAD file")
        return folder

    def _reach(self, point: KillPoint) -> None:
        if self._options.kill_points is not None:
            self._options.kill_points.reach(point)

    def _environment(self, index: Path | None = None) -> dict[str, str]:
        # The identity, the isolation and the locale come last, so that no extra environment can
        # lift them; the C locale keeps the English messages the push outcomes are read from.
        # The ceiling keeps git from looking above the working copy: a `.git` that is not a
        # repository is an error, never a way to one an agent placed in the checkout's parent.
        return {
            **os.environ,
            **self._options.environment,
            "GIT_AUTHOR_NAME": self._identity.name,
            "GIT_AUTHOR_EMAIL": self._identity.email,
            "GIT_COMMITTER_NAME": self._identity.name,
            "GIT_COMMITTER_EMAIL": self._identity.email,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CEILING_DIRECTORIES": str(self._directory.absolute().parent),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "LC_ALL": "C",
            **({} if index is None else {"GIT_INDEX_FILE": str(index)}),
        }

    def _run(
        self,
        arguments: list[str],
        *,
        accepted: tuple[int, ...] = (0,),
        error: type[GitError] = GitError,
        cwd: Path | None = None,
        index: Path | None = None,
    ) -> ProcessResult:
        result = self._execute(arguments, error=error, cwd=cwd, index=index)
        if result.exit_status not in accepted:
            raise error(_command(arguments), result.exit_status, _tail(result.stdout))
        return result

    def _execute(
        self,
        arguments: list[str],
        *,
        error: type[GitError] = GitError,
        cwd: Path | None = None,
        index: Path | None = None,
    ) -> ProcessResult:
        # Runs git and leaves the exit status to the caller; only a git that never finished fails.
        request = ProcessRequest(
            argv=[self._options.executable, *arguments],
            cwd=self._directory if cwd is None else cwd,
            env=self._environment(index),
            time_limit=self._options.time_limit,
            merge_stderr=True,
        )
        try:
            result = run_process(request)
        except OSError as exc:
            raise error(_command(arguments), None, str(exc)) from exc
        if result.timed_out:
            raise error(_command(arguments), None, "time limit reached")
        return result
