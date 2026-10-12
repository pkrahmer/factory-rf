# The git wrapper: branches, merge, reset and revert

## Assignment (as of log entry 1)

Finish the writing half of the git wrapper (R9): delete a branch on the remote and locally, merge a ref (the main branch into a work item's branch) with the merge aborted on a conflict, reset the work tree to a ref and clean it, revert chosen paths to their content at a commit, and move a file. Every operation returns a value for what the caller must decide on (a push outcome, a merge outcome) and raises `GitError` for the rest. These are the steps that later features build on: preparing a stage merges the main branch (F0005), a stall or a crash reverts or resets (F0004, F0005, F0008), the tick resets the checkout to the remote (F0006), a merge or a discard deletes branches and moves the story file (F0007). With this story the `Git` protocol has the nineteen operations R9 asks for. Covers R9; keeps kept thing 13 (recover by construction: reset and clean make the checkout disposable) and kept thing 5 (the undo's revert is the wrapper's, the rules for what to revert are F0004's).

## Interface

`src/factory/domain/git.py` (adds one name)

```python
MergeOutcome = Literal["merged", "fast_forwarded", "up_to_date", "conflict", "not_fast_forward"]
```

`src/factory/application/git.py` (adds six operations to `Git`, which now has nineteen)

```python
    def delete_remote_branch(self, branch: str) -> PushOutcome: ...
    def delete_branch(self, branch: str) -> None: ...
    def merge(self, ref: str, *, fast_forward_only: bool = False) -> MergeOutcome: ...
    def reset_to(self, ref: str) -> None: ...
    def revert_paths(self, commit: str, paths: Sequence[str]) -> None: ...
    def move(self, source: str, destination: str) -> None: ...
```

The rules, each with a criterion below:

- `delete_remote_branch(branch)` runs `git push origin --delete <branch>`. It returns `"pushed"` when the branch no longer exists on the remote afterwards, also when it was already gone (git's `remote ref does not exist` is not an error); `"rejected"` when the remote refuses the deletion (for example a hook); `"unreachable"` under the same conditions as `push`; any other failure is a `GitError`. The remote-tracking ref `origin/<branch>` is gone as well after `"pushed"`. It reaches no kill point.
- `delete_branch(branch)` deletes the local branch even when it is not merged. Deleting the branch that is checked out is a `GitError` and leaves the branch. A branch that does not exist is not an error and changes nothing.
- `merge(ref, fast_forward_only=False)`: when `ref` is already contained in `HEAD` it changes nothing and returns `"up_to_date"` (also with `fast_forward_only`); when `HEAD` is contained in `ref` it moves the branch to `ref` without a merge commit and returns `"fast_forwarded"`; when the two have diverged it returns `"not_fast_forward"` and changes nothing if `fast_forward_only` is true, and otherwise merges with git's default message (no editor) and returns `"merged"`, the merge commit having `HEAD` and `ref` as parents. When the merge conflicts it is aborted before returning `"conflict"`: `HEAD`, the index and the work tree are as they were and no merge is left in progress. An unknown `ref`, and any other refusal by git that leaves no merge in progress (for example local changes that the merge would overwrite), is a `GitError` and changes nothing.
- `reset_to(ref)` runs `git reset --hard <ref>` and then `git clean -fd`: tracked files, staged or not, go back to `ref`, the current branch points at `ref`, and untracked files and directories are removed; ignored paths stay. An unknown `ref` is a `GitError` and changes nothing.
- `revert_paths(commit, paths)` brings each path to its content at `commit` in the work tree and in the index when the file exists there, and deletes it from the work tree and the index when it does not exist at `commit` (a tracked or an untracked file); other paths are not touched; a path that is not there at either place is skipped. Each path is repository-relative with forward slashes; an absolute path, or one with a `..` segment, raises `ValueError` before any path is changed. An unknown `commit` is a `GitError`.
- `move(source, destination)` runs `git mv`, creating the destination's parent directories; the move is staged as a rename. A `source` that is not tracked, or a `destination` that exists, is a `GitError`.

Tests: `tests/adapters/test_git_cli_branches.py`, `tests/application/test_git_protocol.py`. The tests set up and verify with plain `git` through `run_git`, and use the fixtures `remote`, `checkout` and `human`.

## Acceptance criteria

1. `delete_remote_branch` of a branch that exists on the remote returns `"pushed"`; the branch is gone from the remote and `origin/<branch>` is gone from the checkout's refs.
2. `delete_remote_branch` of a branch that is already gone from the remote returns `"pushed"` and changes nothing.
3. `delete_remote_branch` returns `"rejected"` when a `pre-receive` hook of the remote exits non-zero, and the remote's branch is still there.
4. `delete_remote_branch` returns `"unreachable"` when the remote's directory has been removed.
5. `delete_branch` removes a local branch that has a commit the main branch does not have.
6. `delete_branch` of the checked-out branch raises `GitError`, and the branch still exists.
7. `delete_branch` of a branch that does not exist raises nothing and changes nothing.
8. `merge("origin/main")` when `HEAD` already contains it returns `"up_to_date"` and `HEAD` is unchanged; the same with `fast_forward_only=True`.
9. `merge` returns `"fast_forwarded"` when `HEAD` is an ancestor of `ref`: `HEAD` is then the commit of `ref` and no merge commit was made.
10. `merge` of a diverged ref without conflict returns `"merged"`: `HEAD` has two parents, the old `HEAD` and the commit of `ref`, and the files of both sides are in the work tree.
11. `merge(ref, fast_forward_only=True)` of a diverged ref returns `"not_fast_forward"`, and `HEAD` and the work tree are unchanged.
12. `merge` of a diverged ref whose changes conflict returns `"conflict"`, `HEAD` is unchanged, the work tree is clean and no merge is in progress (`MERGE_HEAD` does not exist).
13. `merge("origin/nope")` raises `GitError`; and `merge` of a ref whose merge would overwrite an uncommitted local change raises `GitError`, leaves that change in place and leaves no merge in progress.
14. `reset_to(ref)` discards staged and unstaged changes of tracked files and points the current branch at `ref`.
15. `reset_to` removes untracked files and untracked directories and keeps a file named in `.gitignore`.
16. `reset_to("nope")` raises `GitError`, and an uncommitted change is still there.
17. `revert_paths(commit, ["a.txt", "b.txt"])` restores the content `a.txt` and `b.txt` had at `commit` (one edited, one deleted in the work tree), in the work tree and in the index.
18. `revert_paths` deletes a path that does not exist at `commit`: a file added and committed later, a file only staged, and an untracked file; a path that exists nowhere is skipped without an error.
19. `revert_paths` leaves the changes of paths it was not given as they are.
20. `revert_paths` raises `ValueError` for `../x`, for `a/../../x` and for an absolute path, and no path is changed, not even a valid one in the same call; `docs/a.txt` is accepted.
21. `revert_paths("nope", ["a.txt"])` raises `GitError`.
22. `move("a.txt", "docs/new/a.txt")` creates the folders, the file is at the new path, and `git status` shows a rename; the content is unchanged.
23. `move` raises `GitError` for a source that is not tracked and for a destination that already exists.
24. `GitCli` implements exactly these nineteen operations of `Git`: `fetch`, `remote_branches`, `resolve`, `show_file`, `list_files`, `is_ancestor`, `log`, `changed_paths`, `status`, `clone`, `checkout`, `commit`, `push`, `delete_remote_branch`, `delete_branch`, `merge`, `reset_to`, `revert_paths` and `move`; the protocol has no other.
25. make check stays green.
26. docs: `docs/project-guide.md` describes the writing operations of this story (the merge outcomes and the abort on a conflict, reset and clean, revert of paths, the path rule) and says which feature uses which.

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
git(work, 'checkout', '-q', '-b', 'other')
(work / 'a.txt').write_text('other side\n')
git(work, 'commit', '-q', '-a', '-m', 'other')
git(work, 'checkout', '-q', 'main')
(work / 'a.txt').write_text('main side\n')
git(work, 'commit', '-q', '-a', '-m', 'main')
cli = GitCli(work)
print(cli.merge('other'), cli.status().changes)
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
Expect: four lines: `conflict []`, then `False main side`, then `main side`, then `True False`: the conflicting merge was aborted and left a clean tree, the reset removed the untracked file and the edit, the revert restored the committed text, the move renamed the file.

## Log (append only)

1. 2026-10-12 human: created.
