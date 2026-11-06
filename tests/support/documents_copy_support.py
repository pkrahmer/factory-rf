"""The copy of the repository's tracked files that the document check tests run on."""

import shutil
from pathlib import Path

from support.git_support import commit_all, run_git


def tracked_files_repository(source: Path, target: Path) -> Path:
    """A git repository at `target` with every file git tracks in `source`, in one commit."""
    target.mkdir(parents=True)
    for name in run_git(source, "ls-files", "-z").split("\0"):
        path = source / name
        if not name or not (path.is_file() or path.is_symlink()):
            continue
        copied = target / name
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copied, follow_symlinks=False)
    run_git(target, "init", "-q")
    commit_all(target, "The copied tracked files")
    return target
