---
stage: tests
pr: 12
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The git wrapper: branches and merge

## Assignment (as of log entry 1)

Add the branch operations of the git wrapper (R9): delete a branch on the remote and locally, and merge a ref (the main branch into a work item's branch) with the merge aborted on a conflict. Every operation returns a value for what the caller must decide on (a push outcome, a merge outcome) and raises `GitError` for the rest. These are the steps that later features build on: preparing a stage merges the main branch (F0005), a merge or a discard deletes branches (F0007). Reset, revert and move follow in S0013. This story and S0013 were split from one story to keep each within 26 criteria. Covers R9; keeps kept thing 13 (recover by construction: a conflict never leaves a merge half done). The merge commit uses the identity in the options that `GitCli` is given (S0005, S0006), `factory <factory@noreply.invalid>` when it is built without options, so a `GitCli` never depends on an identity that git detects on its own; the tests use the `checkout` fixture, which has `TEST_IDENTITY`.

## Interface

`src/factory/domain/git.py` (adds one name)

```python
MergeOutcome = Literal["merged", "fast_forwarded", "up_to_date", "conflict", "not_fast_forward"]
```

`src/factory/application/git.py` (adds three operations to `Git`)

```python
    def delete_remote_branch(self, branch: str) -> PushOutcome: ...
    def delete_branch(self, branch: str) -> None: ...
    def merge(self, ref: str, *, fast_forward_only: bool = False) -> MergeOutcome: ...
```

The rules, each with a criterion below:

- `delete_remote_branch(branch)` runs `git push origin --delete <branch>`. It returns `"pushed"` when the branch no longer exists on the remote afterwards, also when it was already gone (git's `remote ref does not exist` is not an error); `"rejected"` when the remote refuses the deletion (for example a hook); `"unreachable"` under the same conditions as `push` (S0006); any other failure, such as an invalid ref name, is a `GitError`. After `"pushed"` the remote-tracking ref `origin/<branch>` is gone from the checkout too, also when the branch was already gone from the remote and the checkout still held a stale `origin/<branch>`; the remote itself is then unchanged. It reaches no kill point.
- `delete_branch(branch)` deletes the local branch even when it is not merged. Deleting the branch that is checked out is a `GitError` and leaves the branch. A branch that does not exist is not an error and changes nothing.
- `merge(ref, fast_forward_only=False)`: when `ref` is already contained in `HEAD` it changes nothing and returns `"up_to_date"` (also with `fast_forward_only`); when `HEAD` is contained in `ref` it moves the branch to `ref` without a merge commit and returns `"fast_forwarded"` (also with `fast_forward_only`); when the two have diverged it returns `"not_fast_forward"` and changes nothing if `fast_forward_only` is true, and otherwise merges with git's default message (no editor) and returns `"merged"`, the merge commit having `HEAD` and `ref` as parents and the identity of the options as its author and committer. When the merge conflicts it is aborted before returning `"conflict"`: `HEAD`, the index and the work tree are as they were and no merge is left in progress. An unknown `ref`, and any other refusal by git that leaves no merge in progress (for example local changes that the merge would overwrite), is a `GitError` and changes nothing.

Tests: `tests/adapters/test_git_cli_branches.py`. The tests set up and verify with plain `git` through `run_git` (which starts git through `run_process`), and use the fixtures `remote`, `checkout` and `human`.

## Acceptance criteria

1. `delete_remote_branch` of a branch that exists on the remote returns `"pushed"`; the branch is gone from the remote and `origin/<branch>` is gone from the checkout's refs.
2. `delete_remote_branch` of a branch that is already gone from the remote returns `"pushed"`, the remote is unchanged, and a stale `origin/<branch>` that the checkout still held is gone afterwards.
3. `delete_remote_branch` returns `"rejected"` when a `pre-receive` hook of the remote exits non-zero, and the remote's branch is still there.
4. `delete_remote_branch` returns `"unreachable"` when the remote's directory has been removed.
5. `delete_remote_branch` of an invalid ref name such as `a..b` raises `GitError`.
6. With `BEFORE_PUSH` and `AFTER_PUSH` armed, `delete_remote_branch` returns `"pushed"` and `reached` is 0 for both points.
7. `delete_branch` removes a local branch that has a commit the main branch does not have.
8. `delete_branch` of the checked-out branch raises `GitError`, and the branch still exists.
9. `delete_branch` of a branch that does not exist raises nothing and changes nothing.
10. `merge("origin/main")` when `HEAD` already contains it returns `"up_to_date"` and `HEAD` is unchanged; the same with `fast_forward_only=True`.
11. `merge` returns `"fast_forwarded"` when `HEAD` is an ancestor of `ref`: `HEAD` is then the commit of `ref` and no merge commit was made; the same result with `fast_forward_only=True`.
12. `merge("other")` of a diverged branch without conflict returns `"merged"`: `HEAD` has two parents, the old `HEAD` and the commit of `other`, the files of both sides are in the work tree, and, with `main` checked out, the merge commit's subject is git's default `Merge branch 'other'` (on another branch git appends ` into <branch>`).
13. `merge(ref, fast_forward_only=True)` of a diverged ref returns `"not_fast_forward"`, and `HEAD` and the work tree are unchanged.
14. `merge` of a diverged ref whose changes conflict returns `"conflict"`, `HEAD` is unchanged, the work tree is clean and no merge is in progress (`MERGE_HEAD` does not exist).
15. `merge("origin/nope")` raises `GitError`.
16. `merge` of a ref whose merge would overwrite an uncommitted local change raises `GitError`, leaves that change in place and leaves no merge in progress.
17. The merge commit of criterion 12 has `TEST_IDENTITY` as its author and as its committer (name and email), also when the test process sets `GIT_COMMITTER_NAME`; for a `GitCli` built without options (`GitCli(directory)`) they are `factory` and `factory@noreply.invalid`.
18. make check stays green.
19. docs: `docs/project-guide.md` describes the branch operations of this story (the push outcomes of the remote deletion, the merge outcomes and the abort on a conflict) and says which feature uses which.

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
cli.delete_branch('other')
print(repr(git(work, 'branch', '--list', 'other')))
cli.delete_branch('other')
print(cli.merge('main'))
"
```
Expect: three lines: `conflict []`, then `''`, then `up_to_date`: the conflicting merge was aborted and left a clean tree, the branch is gone, deleting it again is no error, and a merge of the branch into itself changes nothing.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`factory.domain.git.MergeOutcome`; `delete_remote_branch`, `delete_branch` and `merge` on `Git` in `factory.application.git`). The rules are stated per outcome, including the stale `origin/<branch>` and the kill-point rule.
   - Criteria: 17 behavioural criteria plus the two closing ones. Each is testable with setup through plain git. Every rule has its failing side: rejected (3), unreachable (4), invalid ref (5), checked-out branch (8), missing branch (9), not_fast_forward (13), conflict (14), unknown ref (15) and local-change overwrite (16). Every behaviour in the Interface text has a criterion: the default message (12), the identity (17), and the no-kill-point rule (6). Criterion 17 covers two scenarios (options identity, and the default identity); I take it as two test functions, which needs no further decision.
   - Demo: runnable. It relies on `GitCli.status().changes` from S0011, which is in this feature. The three expected lines (`conflict []`, `''`, `up_to_date`) can be checked against the output.
   - Architecture: the DTO name goes in the domain layer, the operations on the application `Git` interface, and the implementation in the adapter `GitCli`. This matches R9 and the layer rules.
   - Scope: within F0001's scope ("delete branches, merge with abort on a conflict"). Reset, revert and move are left to S0013, which is not in the Out of scope list.
