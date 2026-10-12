"""The git wrapper: the one class that runs the git command-line tool."""

import os
from pathlib import Path

from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from factory.domain.errors import FetchFailed, GitError
from factory.domain.git import CommitId, GitOptions, RemoteBranch
from factory.domain.paths import REMOTE

OUTPUT_TAIL_LINES = 30
REMOTE_PREFIX = f"refs/remotes/{REMOTE}/"
# Exit status of `rev-parse --verify --quiet` and `merge-base --is-ancestor` for "no".
NO = 1


def _tail(output: str) -> str:
    return "\n".join(output.splitlines()[-OUTPUT_TAIL_LINES:])


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
            ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], accepted=(0, NO)
        )
        if result.exit_status == NO:
            return None
        return result.stdout.strip()

    def show_file(self, ref: str, path: str) -> str | None:
        """The text of `path` at `ref`, or `None` when it is absent or not a file."""
        listing = self._run(["ls-tree", "-z", ref, "--", path]).stdout
        for entry in listing.split("\0"):
            if not entry:
                continue
            meta, entry_path = entry.split("\t", 1)
            _mode, kind, blob = meta.split(" ")
            if entry_path == path and kind == "blob":
                return self._run(["cat-file", "blob", blob]).stdout
        return None

    def list_files(self, ref: str, directory: str) -> list[str]:
        """The repository-relative paths of all files under `directory` at `ref`, sorted."""
        listing = self._run(["ls-tree", "-r", "-z", "--name-only", ref, "--", directory]).stdout
        prefix = f"{directory}/"
        return sorted(path for path in listing.split("\0") if path.startswith(prefix))

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """Whether `ancestor` is reachable from `descendant`."""
        result = self._run(["merge-base", "--is-ancestor", ancestor, descendant], accepted=(0, NO))
        return result.exit_status == 0

    def _environment(self) -> dict[str, str]:
        # The isolation comes last, so that no extra environment can lift it.
        return {
            **os.environ,
            **self._options.environment,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
        }

    def _run(
        self,
        arguments: list[str],
        *,
        accepted: tuple[int, ...] = (0,),
        error: type[GitError] = GitError,
    ) -> ProcessResult:
        command = " ".join(["git", *arguments])
        request = ProcessRequest(
            argv=[self._options.executable, *arguments],
            cwd=self._directory,
            env=self._environment(),
            time_limit=self._options.time_limit,
            merge_stderr=True,
        )
        try:
            result = run_process(request)
        except OSError as exc:
            raise error(command, None, str(exc)) from exc
        if result.timed_out:
            raise error(command, None, "time limit reached")
        if result.exit_status not in accepted:
            raise error(command, result.exit_status, _tail(result.stdout))
        return result
