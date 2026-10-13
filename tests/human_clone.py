"""A second clone of the test remote that acts as the human: starts stories, pushes, merges."""

from pathlib import Path
from typing import Literal

from factory.adapters.git_cli import GitCli
from factory.domain.git import GitOptions
from git_support import TEST_IDENTITY, run_git, write_files


class HumanClone:
    """The human's own clone of `remote`, at `directory`."""

    def __init__(self, directory: Path, remote: Path) -> None:
        """Clone `remote` into `directory`."""
        self._directory = directory
        self._git = GitCli(directory, GitOptions(identity=TEST_IDENTITY))
        self._git.clone(str(remote))

    def start(self, path: str) -> None:
        """Move the story at `path` from `backlog/` to `in-progress/` on `main` and push."""
        self._on_branch("main")
        source = self._directory / path
        target = source.parent.parent / "in-progress" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
        self._git.commit(f"start {source.name}")
        self._push("main")

    def push_file(self, branch: str, path: str, text: str) -> None:
        """Write `text` to `path` on `branch`, commit and push."""
        self._on_branch(branch)
        write_files(self._directory, {path: text})
        self._git.commit(f"write {path}")
        self._push(branch)

    def merge(self, branch: str, method: Literal["merge", "squash", "rebase"]) -> None:
        """Bring `origin/<branch>` into `main` by `method` and push `main`."""
        self._on_branch("main")
        incoming = f"origin/{branch}"
        if method == "merge":
            run_git(self._directory, "merge", "-q", "--no-ff", "-m", f"merge {branch}", incoming)
        elif method == "squash":
            run_git(self._directory, "merge", "-q", "--squash", incoming)
            self._git.commit(f"squash {branch}")
        else:
            run_git(self._directory, "checkout", "-q", "-B", "rebased", incoming)
            run_git(self._directory, "rebase", "-q", "--force-rebase", "main")
            run_git(self._directory, "checkout", "-q", "main")
            run_git(self._directory, "merge", "-q", "--ff-only", "rebased")
        self._push("main")

    def _on_branch(self, branch: str) -> None:
        run_git(self._directory, "fetch", "-q", "--prune", "origin")
        exists = self._git.resolve(f"origin/{branch}") is not None
        self._git.checkout(branch, start_point=f"origin/{branch}" if exists else "origin/main")

    def _push(self, branch: str) -> None:
        outcome = self._git.push(branch)
        assert outcome == "pushed", f"the human's push of {branch} was {outcome}"
