---
stage: done
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
3. tester: wrote the red tests for the branch operations in tests/adapters/test_git_cli_branches.py (new file). All of them use the `remote`, `checkout` (TEST_IDENTITY, kill_points) and `tmp_path` fixtures, and set up and check state with plain git through `run_git`.
   - criterion 1: tests/adapters/test_git_cli_branches.py::test_delete_remote_branch_removes_it_from_the_remote_and_the_tracking_ref
   - criterion 2: ::test_delete_remote_branch_already_gone_is_pushed_and_drops_the_stale_tracking_ref (a second clone deletes the branch on the remote; the remote's refs are compared before and after)
   - criterion 3: ::test_delete_remote_branch_declined_by_a_remote_hook_is_rejected
   - criterion 4: ::test_delete_remote_branch_on_a_removed_remote_is_unreachable
   - criterion 5: ::test_delete_remote_branch_of_an_invalid_ref_name_raises
   - criterion 6: ::test_delete_remote_branch_reaches_no_kill_point
   - criterion 7: ::test_delete_branch_removes_an_unmerged_local_branch
   - criterion 8: ::test_delete_branch_of_the_checked_out_branch_raises_and_keeps_it
   - criterion 9: ::test_delete_branch_of_a_missing_branch_changes_nothing (all refs compared before and after)
   - criterion 10: ::test_merge_of_a_contained_ref_is_up_to_date_and_keeps_head (parametrized over fast_forward_only)
   - criterion 11: ::test_merge_of_a_descendant_fast_forwards_without_a_merge_commit (parametrized over fast_forward_only; HEAD's only parent is the old HEAD)
   - criterion 12: ::test_merge_of_a_diverged_branch_makes_a_merge_commit_with_both_parents (`main` checked out; subject `Merge branch 'other'`)
   - criterion 13: ::test_merge_fast_forward_only_of_a_diverged_ref_changes_nothing
   - criterion 14: ::test_merge_with_a_conflict_is_aborted_and_leaves_everything_as_it_was (clean `status --porcelain`, no .git/MERGE_HEAD)
   - criterion 15: ::test_merge_of_an_unknown_ref_raises
   - criterion 16: ::test_merge_that_would_overwrite_a_local_change_raises_and_keeps_the_change (diverged ref; the uncommitted edit is to a file that the ref changes)
   - criterion 17: ::test_merge_commit_carries_the_identity_of_the_options (with GIT_COMMITTER_NAME set through monkeypatch) and ::test_merge_commit_without_options_carries_the_default_identity
   - criteria 18 and 19: not tests (make check / documenter).
   I ran `make test` once and it fails only in the new file, with failing tests and no collection errors. All modules import. The failures come from `delete_remote_branch`, `delete_branch` and `merge` not existing yet on `GitCli`, and `MergeOutcome` is not yet in factory.domain.git (the tests do not import it). `make lint` passes. I interpreted no criterion.

   `make lint`: lint: green
   `make test`: FAILED tests/adapters/test_git_cli_branches.py::test_merge_commit_without_options_carries_the_default_identity
4. coder: implemented the branch operations. All 20 tests in tests/adapters/test_git_cli_branches.py pass, `make check` is green (coverage 98.84 %), and the demo prints `conflict []`, `''`, `up_to_date`.
      - `src/factory/domain/git.py`: `MergeOutcome`.
      - `src/factory/application/git.py`: `delete_remote_branch`, `delete_branch` and `merge` added to the `Git` protocol.
      - `src/factory/adapters/git_cli.py`:
        - `delete_remote_branch` runs `push --porcelain origin --delete`. Exit 0, or git's "remote ref does not exist", means `"pushed"`; either way it then runs `update-ref -d refs/remotes/origin/<branch>` to drop a stale tracking ref. It reaches no kill point.
        - `delete_branch` checks `refs/heads/<branch>` through `resolve`, so a missing branch is a no-op. Otherwise it runs `branch --delete --force`, and git refuses the checked-out branch, which gives the GitError.
        - `merge` decides from ancestry before git merges anything: an unknown ref is a GitError; ref contained in HEAD → `up_to_date`; HEAD contained in ref → `merge --ff-only` → `fast_forwarded`; diverged with `fast_forward_only` → `not_fast_forward`; otherwise `merge --no-edit --no-gpg-sign`. If that fails and `MERGE_HEAD` exists, it runs `merge --abort` and returns `conflict`. Any other failure (such as local changes the merge would overwrite) is a GitError. Both merge calls use `--end-of-options`. The identity comes from the existing `_environment`, which already overrides GIT_COMMITTER_*.
      - Main decision: decide the outcome from ancestry plus the presence of `MERGE_HEAD`, not by parsing git's merge messages. Rejected alternative: parsing "Already up to date" / "Fast-forward" / "CONFLICT" text, which is fragile across git versions and locales. The already-deleted case still relies on git's text "remote ref does not exist". I found no cleaner signal for it.
      - Refactor (separate commit 4366098): `push` and `delete_remote_branch` duplicated the rejected / unreachable / error classification. It is now one private `_failed_push`.
      - Open: criterion 19 (project-guide) is the documenter's. I noticed nothing outside the ticket that needs touching.

   `make check`: check: green
5. reviewer: no findings.
      - Acceptance criteria: each of criteria 1–17 has a test in tests/adapters/test_git_cli_branches.py that checks what the criterion names. The remote and the tracking ref are checked after the deletion (1, 2), with the remote's refs compared before and after (2). Criterion 3 uses a real pre-receive hook, criterion 4 a removed remote, criterion 5 `a..b`, and criterion 6 checks both kill points at 0. Criterion 10 is parametrized over both `fast_forward_only` values, as is criterion 11, where the only parent is the old HEAD. Criterion 12 checks both parents, both files and the default subject. Criteria 13, 14 and 16 check that HEAD is unchanged, the work tree is clean or the local change kept, and there is no `.git/MERGE_HEAD`. Criterion 17 has two tests: the options identity with `GIT_COMMITTER_NAME` set, and the default identity. Every failing side the Interface names has a test: rejected, unreachable, invalid ref, checked-out branch, missing branch, not_fast_forward, conflict, unknown ref, local-change overwrite. The coder's entry says the factory's `make check` was green.
      - Architecture: `MergeOutcome` is a Literal in `factory.domain.git`, the three operations are on the application `Git` protocol, and the implementation is in the adapter `GitCli`, which reaches git only through `_run`/`_execute`. No `dict[str, Any]`, and no new imports across layers.
      - Security: no new silencing markers and no secrets. All argv is lists, and both merge calls use `--end-of-options`. `merge` checks the ref with `resolve` before anything else.
      - Quality: deciding from ancestry and `MERGE_HEAD` avoids parsing merge text. Moving the push failure classification into `_failed_push` (4366098) removes duplication. The public methods have docstrings. Comments say why: the stale tracking ref and the already-deleted marker.
      - Ticket hygiene: the log records the main decision and the rejected alternative (parsing git's merge messages). It also states the remaining reliance on git's English text for "remote ref does not exist". The same applies to the existing unreachable markers. Assignment matches what was built. Criterion 19 still describes what the project guide must say.
      - Noted, not a finding: `delete_remote_branch` passes `branch` without `--end-of-options`, the same as the existing `push`. Any branch name starting with `-` still ends in a `GitError` (`--delete` without refs dies), which the Interface allows.
6. documenter: changed `docs/project-guide.md` only. In "The git wrapper" I added three rows to the method table (`delete_remote_branch`, `delete_branch`, `merge`). I added a subsection "Deleting and merging branches", placed after the push kill points, covering the remote-deletion outcomes (stale tracking ref, already-gone counts as pushed, no kill point), the five merge outcomes, the abort on a conflict, and which feature uses what (F0005 merges main into the work item's branch; F0007 deletes branches on merge or discard). I also updated the intro sentence, which said deleting and merging "follow in later stories". Cross-read: the rest of the project guide and README against the diff (the identity paragraph, the options table, the test-fixture paragraph) are current. The code matches the Interface and criteria; no findings. Nothing stale seen outside this story. `make check` is green.

   `make check`: check: green
7. demo: I ran the single `## Demo` command from the repository root exactly as written. It exited with 0.

   ```
   conflict []
   ''
   up_to_date
   ```

   - It met its `Expect:` line: there are three lines, `conflict []`, `''` and `up_to_date`.
   - Checked against the acceptance criteria, the demo contradicts none of them:
     - The conflicting merge returned `"conflict"` and left a clean work tree (criterion 14).
     - `delete_branch` removed `other`, which had a commit that `main` lacks (criterion 7).
     - Deleting `other` a second time raised nothing (criterion 9).
     - Merging `main` into itself returned `"up_to_date"` (criterion 10).
   - The demo does not exercise the remote deletion, the fast-forward, the clean merge or the identity (criteria 1–6, 11–13, 15–17). The tests cover those, as the reviewer's entry records.

   Findings: none.
8. done (pull request merged); cost: 6 runs, 6.4 min, 41 turns, 122k tokens in (657k more from cache), 24k out, $1.42
