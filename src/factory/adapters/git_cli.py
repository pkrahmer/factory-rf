"""The git wrapper: the one class that runs the git command-line tool."""

import os
from datetime import UTC, datetime
from pathlib import Path

from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from factory.domain.errors import FetchFailed, GitError, NothingToCommit
from factory.domain.git import (
    ChangedPath,
    ChangeKind,
    CommitId,
    CommitInfo,
    GitOptions,
    PushOutcome,
    RemoteBranch,
    WorkTreeStatus,
)
from factory.domain.kill_points import KillPoint
from factory.domain.paths import REMOTE

OUTPUT_TAIL_LINES = 30
REMOTE_PREFIX = f"refs/remotes/{REMOTE}/"
# The exit status by which `rev-parse --verify --quiet` and `merge-base --is-ancestor` say "no".
ANSWER_NO = 1
# The exit status by which git says it could not talk to the remote at all.
FATAL = 128
# One log record is id, parents, author, committer timestamp and message, each ended by NUL.
LOG_FORMAT = "%H%x00%P%x00%an%x00%ct%x00%B"
LOG_FIELDS = 5
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


def _sorted_changes(changes: dict[str, ChangeKind]) -> list[ChangedPath]:
    return [ChangedPath(path=path, change=changes[path]) for path in sorted(changes)]


def _is_rejected(porcelain: str) -> bool:
    # A `push --porcelain` ref line is "<flag>\t<from>:<to>\t<summary>"; `!` marks a refusal.
    return any(line.startswith("!\t") for line in porcelain.splitlines())


def _is_unreachable(result: ProcessResult) -> bool:
    if result.exit_status != FATAL:
        return False
    return any(marker in result.stdout for marker in UNREACHABLE_MARKERS)


class GitCli:
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
        result = self._run(
            ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], accepted=(0, ANSWER_NO)
        )
        if result.exit_status == ANSWER_NO:
            return None
        return result.stdout.strip()

    def show_file(self, ref: str, path: str) -> str | None:
        """The text of `path` at `ref`, or `None` when it is absent or not a file."""
        listing = self._run(["ls-tree", "-z", ref, "--", path]).stdout
        blob = _blob_in_listing(listing, path)
        if blob is None:
            return None
        return self._run(["cat-file", "blob", blob]).stdout

    def list_files(self, ref: str, directory: str) -> list[str]:
        """The repository-relative paths of all files under `directory` at `ref`, sorted."""
        listing = self._run(["ls-tree", "-r", "-z", "--name-only", ref, "--", directory]).stdout
        prefix = f"{directory}/"
        return sorted(path for path in listing.split("\0") if path.startswith(prefix))

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """Whether `ancestor` is reachable from `descendant`."""
        result = self._run(
            ["merge-base", "--is-ancestor", ancestor, descendant], accepted=(0, ANSWER_NO)
        )
        return result.exit_status == 0

    def log(
        self, ref: str, *, since: str | None = None, path: str | None = None
    ) -> list[CommitInfo]:
        """The commits reachable from `ref` and not from `since`, touching `path` if given."""
        revisions = [ref] if since is None else [ref, f"^{since}"]
        paths = [] if path is None else [path]
        arguments = ["log", "-z", "--date-order", f"--format={LOG_FORMAT}", "--end-of-options"]
        listing = self._run([*arguments, *revisions, "--", *paths]).stdout
        return _commits_in_log(listing)

    def changed_paths(self, since: str) -> list[ChangedPath]:
        """The tracked paths that differ from `since`, and the untracked ones as added."""
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
        branch: str | None = None
        head: str | None = None
        changes: dict[str, ChangeKind] = {}
        for entry in filter(None, listing.split("\0")):
            if entry.startswith("# branch.oid "):
                oid = entry.removeprefix("# branch.oid ")
                head = None if oid == "(initial)" else oid
            elif entry.startswith("# branch.head "):
                name = entry.removeprefix("# branch.head ")
                branch = None if name == "(detached)" else name
            else:
                change = _status_entry(entry)
                if change is not None:
                    changes[change.path] = change.change
        return WorkTreeStatus(branch=branch, head=head, changes=_sorted_changes(changes))

    def clone(self, url: str) -> None:
        """Clone `url` into the bound directory, creating its missing parents."""
        parent = self._directory.parent
        parent.mkdir(parents=True, exist_ok=True)
        self._run(["clone", "--quiet", url, str(self._directory)], cwd=parent)

    def checkout(self, branch: str, *, start_point: str | None = None) -> None:
        """Switch to `branch`; with `start_point`, create or reset it there first."""
        if start_point is None:
            # `switch` takes no paths, so a branch name is never read as a file.
            self._run(["switch", "--quiet", branch])
        else:
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
        self._reach(KillPoint.BEFORE_PUSH)
        arguments = ["push", "--porcelain", "--set-upstream", REMOTE, branch]
        result = self._execute(arguments)
        if result.exit_status == 0:
            self._reach(KillPoint.AFTER_PUSH)
            return "pushed"
        if _is_rejected(result.stdout):
            return "rejected"
        if _is_unreachable(result):
            return "unreachable"
        raise GitError(_command(arguments), result.exit_status, _tail(result.stdout))

    def _untracked_paths(self) -> list[str]:
        listing = self._run(["ls-files", "--others", "--exclude-standard", "-z"]).stdout
        return [path for path in listing.split("\0") if path]

    def _reach(self, point: KillPoint) -> None:
        if self._options.kill_points is not None:
            self._options.kill_points.reach(point)

    def _environment(self) -> dict[str, str]:
        # The identity and the isolation come last, so that no extra environment can lift them.
        return {
            **os.environ,
            **self._options.environment,
            "GIT_AUTHOR_NAME": self._identity.name,
            "GIT_AUTHOR_EMAIL": self._identity.email,
            "GIT_COMMITTER_NAME": self._identity.name,
            "GIT_COMMITTER_EMAIL": self._identity.email,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
        }

    def _run(
        self,
        arguments: list[str],
        *,
        accepted: tuple[int, ...] = (0,),
        error: type[GitError] = GitError,
        cwd: Path | None = None,
    ) -> ProcessResult:
        result = self._execute(arguments, error=error, cwd=cwd)
        if result.exit_status not in accepted:
            raise error(_command(arguments), result.exit_status, _tail(result.stdout))
        return result

    def _execute(
        self,
        arguments: list[str],
        *,
        error: type[GitError] = GitError,
        cwd: Path | None = None,
    ) -> ProcessResult:
        # Runs git and leaves the exit status to the caller; only a git that never finished fails.
        request = ProcessRequest(
            argv=[self._options.executable, *arguments],
            cwd=self._directory if cwd is None else cwd,
            env=self._environment(),
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
