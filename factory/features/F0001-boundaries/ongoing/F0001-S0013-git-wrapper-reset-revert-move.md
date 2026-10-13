---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The git wrapper: reset, revert and move

## Assignment (as of log entry 1)

Finish the writing half of the git wrapper (R9): reset the work tree to a ref and clean it, revert chosen paths to their content at a commit, and move a file. These are the steps that later features build on: a stall or a crash reverts or resets (F0004, F0005, F0008), the tick resets the checkout to the remote (F0006), a merge or a discard moves the story file (F0007). With this story the `Git` protocol has the nineteen operations R9 asks for, and a test proves that `GitCli` has each of them and the protocol no other. This story and S0012 were split from one story to keep each within 26 criteria. Covers R9; keeps kept thing 13 (recover by construction: reset and clean make the checkout disposable) and kept thing 5 (the undo's revert is the wrapper's, the rules for what to revert are F0004's). The closing criterion needs the operations of S0011, which comes before this story in id order.

## Interface

`src/factory/application/git.py` (adds three operations to `Git`, which now has nineteen)

```python
    def reset_to(self, ref: str) -> None: ...
    def revert_paths(self, commit: str, paths: Sequence[str]) -> None: ...
    def move(self, source: str, destination: str) -> None: ...
```

The rules, each with a criterion below:

- `reset_to(ref)` runs `git reset --hard <ref>` and then `git clean -fd`: tracked files, staged or not, go back to `ref`, the current branch points at `ref`, and untracked files and directories are removed; ignored paths stay. An unknown `ref` is a `GitError` and changes nothing.
- `revert_paths(commit, paths)` brings each path to its content at `commit` in the work tree and in the index when the file exists there, and deletes it from the work tree and the index when it does not exist at `commit` (a tracked or an untracked file); other paths are not touched; a path that is not there at either place is skipped. Each path is repository-relative with forward slashes; an absolute path, or one with a `..` segment, raises `ValueError` before any path is changed. An unknown `commit` is a `GitError`.
- `move(source, destination)` runs `git mv`, creating the destination's parent directories; the move is staged as a rename. A `source` that is not tracked, or a `destination` that exists, is a `GitError`.
- `Git` has exactly nineteen public operations: `fetch`, `remote_branches`, `resolve`, `show_file`, `list_files`, `is_ancestor`, `log`, `changed_paths`, `status`, `clone`, `checkout`, `commit`, `push`, `delete_remote_branch`, `delete_branch`, `merge`, `reset_to`, `revert_paths` and `move`; `GitCli` has each of them.

Tests: `tests/adapters/test_git_cli_restoring.py`, `tests/application/test_git_protocol.py`. The tests set up and verify with plain `git` through `run_git` (which starts git through `run_process`), and use the fixtures `remote`, `checkout` and `human`.

## Acceptance criteria

1. `reset_to(ref)` discards staged and unstaged changes of tracked files and points the current branch at `ref`.
2. `reset_to` removes untracked files and untracked directories and keeps a file named in `.gitignore`.
3. `reset_to("nope")` raises `GitError`, and an uncommitted change is still there.
4. `revert_paths(commit, ["a.txt", "b.txt"])` restores the content `a.txt` and `b.txt` had at `commit` (one edited, one deleted in the work tree), in the work tree and in the index.
5. `revert_paths` deletes a path that does not exist at `commit`: a file added and committed later, a file only staged, and an untracked file; a path that exists nowhere is skipped without an error.
6. `revert_paths` leaves the changes of paths it was not given as they are.
7. `revert_paths` raises `ValueError` for `../x`, for `a/../../x` and for an absolute path, and no path is changed, not even a valid one in the same call; `docs/a.txt` is accepted.
8. `revert_paths("nope", ["a.txt"])` raises `GitError`.
9. `move("a.txt", "docs/new/a.txt")` creates the folders, the file is at the new path, and `git status` shows a rename; the content is unchanged.
10. `move` raises `GitError` for a source that is not tracked and for a destination that already exists.
11. `Git` has exactly the nineteen operations named in the rules, and `GitCli` has each of them (a test compares the public names of the protocol with that list and checks `hasattr` on `GitCli`).
12. make check stays green.
13. docs: `docs/project-guide.md` describes the operations of this story (reset and clean, revert of paths and the path rule, move) and lists the nineteen operations of the `Git` protocol with the feature that uses each.

## Demo

```bash
uv run python -c "
import tempfile
from pathlib import Path
from factory.adapters.git_cli import GitCli
from factory.adapters.process import ProcessRequest, run_process

def git(directory, *args):
    argv = ['git', '-c', 'user.name=demo', '-c', 'user.email=demo@example.invalid', *args]
    return run_process(ProcessRequest(argv=argv, cwd=directory)).stdout.strip()

root = Path(tempfile.mkdtemp())
git(root, 'init', '-q', '--initial-branch=main', 'work')
work = root / 'work'
(work / 'a.txt').write_text('base\n')
git(work, 'add', '-A')
git(work, 'commit', '-q', '-m', 'base')
cli = GitCli(work)
(work / 'junk.txt').write_text('x\n')
(work / 'a.txt').write_text('edited\n')
cli.reset_to('HEAD')
print((work / 'junk.txt').exists(), (work / 'a.txt').read_text().strip())
(work / 'a.txt').write_text('edited again\n')
cli.revert_paths('HEAD', ['a.txt'])
print((work / 'a.txt').read_text().strip())
cli.move('a.txt', 'docs/a.txt')
print((work / 'docs' / 'a.txt').exists(), (work / 'a.txt').exists())
"
```
Expect: three lines: `False base`, then `base`, then `True False`: the reset removed the untracked file and the edit, the revert restored the committed text, the move renamed the file.

## Log (append only)

1. 2026-10-12 human: created.
