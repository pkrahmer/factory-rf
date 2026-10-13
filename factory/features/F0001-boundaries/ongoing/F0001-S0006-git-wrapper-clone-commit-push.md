---
stage: accept
pr: 6
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The git wrapper: clone, checkout, commit and push

## Assignment (as of log entry 1)

Add the first writing operations to `GitCli`: clone into the bound directory, check out a branch (creating or resetting it at a start point), commit every change, and push with its outcome as a value (`pushed`, `rejected`, `unreachable`), never forced. The factory's commits carry the identity in the `GitOptions` that `GitCli` is given at construction (`factory <factory@noreply.invalid>` unless the instance's settings, R25, give another through the wiring of F0010), and no user or system git configuration can change it; a `GitCli` built without options commits as the default identity. `push` is where two of the four kill points of R36 live: `before-push` is reached between a commit and its push, `after-push` right after a successful push, so that later tests can kill the tick at either place. Covers R9 and R36 (the two push kill points); keeps kept thing 13 (a push is the only way the remote learns anything, and a rejected or unreachable push is a result the caller decides on) and kept thing 18 (the identity comes from the instance's settings; the default is only what an unset one falls back to). The test fixture `human`, a second clone that acts as the human, is built here because the push tests need a second writer; F0006 uses its `merge` for the three merge methods. Deleting branches and merging follow in S0012; reset, revert and move in S0013.

## Interface

`src/factory/domain/git.py` (adds one name)

```python
PushOutcome = Literal["pushed", "rejected", "unreachable"]
```

`src/factory/domain/errors.py` (adds one type)

```python
class NothingToCommit(GitError): ...
```

`src/factory/application/git.py` (adds four operations to `Git`)

```python
    def clone(self, url: str) -> None: ...
    def checkout(self, branch: str, *, start_point: str | None = None) -> None: ...
    def commit(self, message: str) -> CommitId: ...
    def push(self, branch: str) -> PushOutcome: ...
```

The rules, each with a criterion below:

- The environment of every call also sets `GIT_AUTHOR_NAME` and `GIT_COMMITTER_NAME` to `options.identity.name` and `GIT_AUTHOR_EMAIL` and `GIT_COMMITTER_EMAIL` to `options.identity.email` (S0005; `factory <factory@noreply.invalid>` for a `GitCli` built without options), over whatever the process or `options.environment` has; the isolation from the user and system configuration of S0005 stays.
- `clone(url)` runs `git clone <url> <directory>` from the parent of the bound directory, creating missing parents. The directory must be missing or empty; otherwise `GitError`. After a clone the checkout is on the remote's default branch with `origin` set.
- `checkout(branch)` switches to the existing local branch; when the branch exists only as `origin/<branch>`, it creates the local branch at the remote's commit. `checkout(branch, start_point=ref)` creates the branch at `ref` or resets an existing branch to `ref` (`git checkout -B`). An unknown branch or start point, or uncommitted changes that stand in the way, is a `GitError` and leaves the current branch and the changes as they were.
- `commit(message)` stages every change (`git add -A`; ignored paths stay out), commits with `message` as given, and returns the new commit's id. When nothing is staged it raises `NothingToCommit` and commits nothing. The commit's author and committer are the identity of the options.
- `push(branch)` runs `git push --porcelain --set-upstream origin <branch>`, never with force. It reaches `KillPoint.BEFORE_PUSH` before running git, and `KillPoint.AFTER_PUSH` only after a push that succeeded (when the `GitCli` has kill points). It returns `"pushed"` when git exits 0; `"rejected"` when the remote refused the update (a non-fast-forward, or a hook of the remote declined it: git reports the ref with `!`); `"unreachable"` when git could not reach the remote (exit 128 with `Could not read from remote repository`, `does not appear to be a git repository`, `unable to access` or `Could not resolve host` in the output); any other failure, such as an unknown local branch, is a `GitError`. After `"pushed"`, `origin/<branch>` in the checkout is the pushed commit.

The test fixture `human` in `tests/conftest.py`, with the class in `tests/human_clone.py`, driven through `GitCli` and `run_git`:

```python
class HumanClone:
    def __init__(self, directory: Path, remote: Path) -> None: ...
    def start(self, path: str) -> None: ...
    def push_file(self, branch: str, path: str, text: str) -> None: ...
    def merge(self, branch: str, method: Literal["merge", "squash", "rebase"]) -> None: ...
```

`HumanClone` is a second clone of the `remote` fixture, built with `GitOptions(identity=TEST_IDENTITY)`. `start(path)` moves a story file from `backlog/` to `in-progress/` in the same feature folder on `main`, commits and pushes. `push_file(branch, path, text)` writes the file on that branch (created from `origin/main` when the remote has no such branch), commits and pushes. `merge(branch, method)` brings `origin/<branch>` into `main` and pushes `main`: with `"merge"` as a merge commit, with `"squash"` as one ordinary commit that leaves the branch tip outside the history of `main`, with `"rebase"` as the branch's commits replayed on `main` with no merge commit.

Tests: `tests/adapters/test_git_cli_writing.py`, `tests/domain/test_errors.py` (extended: it gains new tests only, no existing test is changed), `tests/test_human_clone.py`; `tests/conftest.py` gains `human` (an addition; the fixtures `remote` and `checkout` stay as S0005 made them); `tests/git_support.py` gains whatever the tests need to read the remote with plain `git`, started through `run_process`. The tests verify results with plain `git` through `run_git`, not through other `GitCli` methods.

## Acceptance criteria

1. `clone(url)` into a directory that does not exist, in a parent that does not exist either, creates the clone: it holds the remote's files, is on `main`, and `origin` is the url.
2. `clone` into an existing empty directory works; `clone` into a directory that holds a file raises `GitError` and leaves the file untouched.
3. `clone` of a url that does not exist raises `GitError`.
4. `checkout("other")` switches to the existing local branch `other`.
5. `checkout("work-item/F0001-S0001", start_point="origin/main")` creates the branch at that commit; called again after the branch got another commit, it resets the branch to `origin/main`.
6. `checkout` of a branch that exists only on the remote creates a local branch at the remote's commit.
7. `checkout("nope")` and `checkout("x", start_point="origin/nope")` raise `GitError`, and the current branch is still the one before the call.
8. With an uncommitted edit to a file that differs on branch `other`, `checkout("other")` raises `GitError`; the current branch is unchanged and the edit is still in the work tree.
9. `commit` after a new file, a changed file and a deleted file returns the new commit's id, which is `HEAD`, and the commit holds exactly those three changes; a file named in `.gitignore` stays out.
10. `commit("Subject line\n\nBody line")` stores the message as given: plain `git log -1 --format=%B` shows the subject, a blank line and the body.
11. A commit has the author and the committer given as the identity of the options at construction (name and email), also when the test process sets `GIT_AUTHOR_NAME`, when the `environment` of the options sets `GIT_AUTHOR_NAME` and `GIT_COMMITTER_EMAIL`, and when `GIT_CONFIG_GLOBAL` points to a file with another `user.name` and `commit.gpgsign = true`.
12. A commit made by a `GitCli` built without options (`GitCli(directory)`) has `factory` as the name and `factory@noreply.invalid` as the email of its author and of its committer.
13. `commit` with nothing to commit raises `NothingToCommit` and `HEAD` is unchanged; the same when the only change is an ignored file; `NothingToCommit` is a subclass of `GitError`.
14. `push` of a branch the remote does not have returns `"pushed"`; afterwards the remote's branch and `origin/<branch>` in the checkout are the pushed commit.
15. `push` returns `"rejected"` when another clone pushed to the same branch first (a non-fast-forward), and the remote's branch is still the other clone's commit.
16. `push` returns `"rejected"` when a `pre-receive` hook of the remote exits non-zero, and the remote has no such branch.
17. `push` returns `"unreachable"` when the remote's directory has been removed.
18. `push("nope")` for a local branch that does not exist raises `GitError`.
19. With `KillPoint.BEFORE_PUSH` armed, `push` raises `InjectedKill` before anything reaches the remote: the local commit exists and the remote's branch does not.
20. With `KillPoint.AFTER_PUSH` armed, `push` raises `InjectedKill` after the remote has the commit.
21. Per call, `BEFORE_PUSH` is reached once whatever the outcome, and `AFTER_PUSH` only when the outcome is `"pushed"` (`reached` counts 1 and 0 after a rejected push, 2 and 1 after a following successful one); a `GitCli` without kill points pushes normally.
22. `HumanClone.merge(branch, method)` puts the branch on the remote's `main` as a two-parent merge commit with `"merge"`, as one single-parent commit whose parent is the previous `main` with `"squash"` (the branch tip is not an ancestor of `main`), and as a chain of single-parent commits with `"rebase"`.
23. `HumanClone.start("factory/features/F0001-example/backlog/F0001-S0001-first.md")` leaves the file under `in-progress/` and no longer under `backlog/` on the remote's `main`; `push_file` makes the file appear on the remote branch with the given text.
24. make check stays green.
25. docs: `docs/project-guide.md` explains the writing operations of the git wrapper (the identity of the options and its default, which F0010 fills from `GIT_USER_NAME` and `GIT_USER_EMAIL`; push outcomes as values, never forced) and the two push kill points, and the fixtures `remote`, `checkout` and `human` for tests; `docs/decisions.md` records why a push is never forced and a rejection is a value, not an error (WE6.3).

## Demo

```bash
uv run python -c "
import tempfile
from pathlib import Path
from factory.adapters.git_cli import GitCli
from factory.adapters.process import ProcessRequest, run_process
from factory.domain.errors import NothingToCommit
from factory.domain.git import GitIdentity, GitOptions

def git(directory, *args):
    argv = ['git', '-c', 'user.name=demo', '-c', 'user.email=demo@example.invalid', *args]
    return run_process(ProcessRequest(argv=argv, cwd=directory)).stdout.strip()

root = Path(tempfile.mkdtemp())
git(root, 'init', '-q', '--initial-branch=main', 'seed')
(root / 'seed' / 'readme.txt').write_text('seed\n')
git(root / 'seed', 'add', '-A')
git(root / 'seed', 'commit', '-q', '-m', 'seed')
git(root, 'init', '-q', '--bare', '--initial-branch=main', 'remote.git')
git(root / 'seed', 'push', '-q', str(root / 'remote.git'), 'main')
url = str(root / 'remote.git')
identity = GitIdentity(name='demo', email='demo@example.invalid')
first = GitCli(root / 'first', GitOptions(identity=identity))
second = GitCli(root / 'second', GitOptions(identity=identity))
first.clone(url)
second.clone(url)
for cli, name in ((first, 'first'), (second, 'second')):
    cli.checkout('work-item/F0001-S0001', start_point='origin/main')
    (root / name / (name + '.txt')).write_text(name + '\n')
    cli.commit('add ' + name)
    print(name, cli.push('work-item/F0001-S0001'))
try:
    first.commit('nothing')
except NothingToCommit:
    print('nothing to commit')
print(first.resolve('origin/work-item/F0001-S0001') == first.resolve('HEAD'))
"
```
Expect: four lines: `first pushed`, `second rejected`, `nothing to commit`, `True`: the second clone's push is refused because the first got there first, and nothing was forced.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`PushOutcome` in `domain/git.py`, `NothingToCommit` in `domain/errors.py`, `clone`/`checkout`/`commit`/`push` on `Git`, `HumanClone` in `tests/human_clone.py`, the `human` fixture). Each behaviour stated in its comments has a criterion: identity and environment precedence (11, 12), clone directory rules (1-3), checkout cases (4-8), commit staging, message and ignored paths (9, 10, 13), push outcomes and kill points (14-21), HumanClone merge methods (22, 23).
   - Criteria: each is testable by one test function. Every rule has its failing side: a clone into a non-empty directory (2) or a missing url (3), an unknown branch or start point (7), a dirty tree that blocks checkout (8), nothing to commit (13), rejected for a non-fast-forward and for a hook (15, 16), unreachable (17), an unknown local branch (18), kill points not reached after a rejection (21).
   - Demo: runnable as written (imports are complete). The Expect line gives four exact lines that can be compared with the output.
   - Architecture: the new operations sit on the `Git` interface in `application` and are implemented in the `GitCli` adapter. The types go into `domain`. Tests mirror the package layout, and git is not faked.
   - Scope: the story stays within F0001's scope (clone, check out, commit, push with its outcome). Deleting branches and merging are left to S0012, and reset, revert and move to S0013, as the feature lists them.
3. tester: wrote red tests for criteria 1–23, one test per criterion. Limits and boundaries are covered as parametrized cases where a criterion names them.
   - criterion 1: tests/adapters/test_git_cli_writing.py::test_clone_creates_a_missing_directory_and_its_missing_parent
   - criterion 2: tests/adapters/test_git_cli_writing.py::test_clone_works_into_an_empty_directory_and_refuses_one_with_a_file
   - criterion 3: tests/adapters/test_git_cli_writing.py::test_clone_of_a_missing_url_raises
   - criterion 4: tests/adapters/test_git_cli_writing.py::test_checkout_switches_to_an_existing_local_branch
   - criterion 5: tests/adapters/test_git_cli_writing.py::test_checkout_with_a_start_point_creates_and_then_resets_the_branch
   - criterion 6: tests/adapters/test_git_cli_writing.py::test_checkout_of_a_branch_only_on_the_remote_creates_it_at_the_remote_commit
   - criterion 7: tests/adapters/test_git_cli_writing.py::test_checkout_of_an_unknown_branch_or_start_point_raises_and_stays (unknown-branch, unknown-start-point)
   - criterion 8: tests/adapters/test_git_cli_writing.py::test_checkout_blocked_by_an_uncommitted_edit_raises_and_keeps_the_edit
   - criterion 9: tests/adapters/test_git_cli_writing.py::test_commit_records_new_changed_and_deleted_files_but_not_ignored_ones
   - criterion 10: tests/adapters/test_git_cli_writing.py::test_commit_stores_the_message_as_given
   - criterion 11: tests/adapters/test_git_cli_writing.py::test_commit_carries_the_identity_of_the_options (process-environment, options-environment, global-configuration with another user.name and commit.gpgsign = true)
   - criterion 12: tests/adapters/test_git_cli_writing.py::test_commit_without_options_carries_the_default_identity
   - criterion 13: tests/adapters/test_git_cli_writing.py::test_commit_with_nothing_to_commit_raises_and_keeps_head (clean, only-ignored); tests/domain/test_errors.py::test_nothing_to_commit_is_a_git_error
   - criterion 14: tests/adapters/test_git_cli_writing.py::test_push_of_a_new_branch_is_pushed
   - criterion 15: tests/adapters/test_git_cli_writing.py::test_push_behind_another_clone_is_rejected
   - criterion 16: tests/adapters/test_git_cli_writing.py::test_push_declined_by_a_remote_hook_is_rejected
   - criterion 17: tests/adapters/test_git_cli_writing.py::test_push_to_a_removed_remote_is_unreachable
   - criterion 18: tests/adapters/test_git_cli_writing.py::test_push_of_an_unknown_local_branch_raises
   - criterion 19: tests/adapters/test_git_cli_writing.py::test_kill_before_push_leaves_the_remote_untouched
   - criterion 20: tests/adapters/test_git_cli_writing.py::test_kill_after_push_comes_after_the_remote_has_the_commit
   - criterion 21: tests/adapters/test_git_cli_writing.py::test_push_reaches_before_push_every_time_and_after_push_only_when_pushed
   - criterion 22: tests/test_human_clone.py::test_merge_brings_the_branch_into_main_by_the_method (merge, squash, rebase)
   - criterion 23: tests/test_human_clone.py::test_start_moves_the_story_and_push_file_writes_the_branch
   - criteria 24 and 25 are not tests: 24 is the `make check` gate and 25 is the documenter's.

   Files created: tests/adapters/test_git_cli_writing.py, tests/human_clone.py (`HumanClone` as the Interface specifies), tests/test_human_clone.py.
   Files extended:
   - tests/conftest.py: new fixture `human`; `remote` and `checkout` are unchanged.
   - tests/git_support.py: new helper `remote_commit(remote, branch)`, which reads a branch of the bare remote with plain git through `run_process` and returns `None` when the branch is absent.
   - tests/domain/test_errors.py: one new import and one new test; the existing tests are unchanged.

   `HumanClone` drives `GitCli.clone`, `GitCli.checkout`, `GitCli.commit` and `GitCli.push`. For the merge methods it uses `run_git`: `merge --no-ff`, `merge --squash` followed by `GitCli.commit`, and a `rebase --force-rebase` followed by a fast-forward of `main`. Every push it makes must return `"pushed"`.

   `make test` result: collection errors in tests/adapters/test_git_cli_writing.py and tests/domain/test_errors.py, because the runner cannot import `NothingToCommit` from `factory.domain.errors` yet. tests/test_human_clone.py collects but will fail because `GitCli` has no `clone`, `checkout`, `commit` or `push` yet.
   `make lint` is green. I skipped the type check, as this stage allows: it cannot pass until the new `GitCli` methods exist.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: implemented clone, checkout, commit and push on the git wrapper; make check green (coverage 100 %), demo prints the four expected lines. No test changed.
      - src/factory/domain/git.py: `PushOutcome`; src/factory/domain/errors.py: `NothingToCommit(GitError)`; src/factory/application/git.py: the four operations on `Git` with docstrings.
      - src/factory/adapters/git_cli.py: `clone` creates missing parents and runs `git clone <url> <dir>` from the parent (git itself refuses a non-empty directory → `GitError`). `checkout` uses `git switch` (no path ambiguity, DWIM creates a branch that exists only on `origin`) and `git switch --force-create <branch> <start>` for a start point, the equivalent of `checkout -B`. `commit` runs `add --all`, then `diff --cached --quiet` → `NothingToCommit` when nothing is staged, else `commit --cleanup=verbatim --no-gpg-sign --message`, returning `HEAD`. `push` reaches BEFORE_PUSH, runs `push --porcelain --set-upstream origin <branch>`; exit 0 → `pushed` + AFTER_PUSH; a `!` ref line → `rejected`; exit 128 with one of the four markers → `unreachable`; else `GitError`. The environment sets GIT_AUTHOR_*/GIT_COMMITTER_* from the options' identity after the process and options environment, before the unchanged config isolation.
      - Design: split the old `_run` into `_execute` (runs git, raises only when git never finished) and `_run` (checks the exit status), plus a `cwd` override for clone; push reads its outcome from `_execute`. Rejected: an "accept any status" flag on `_run`, which blurs its contract.
      - Refactor pass: read the diff as a reviewer; nothing to change, so no refactor commit.
      - Noticed, not touched: the interface text names `git checkout -B`; `switch --force-create` is the same operation. A branch created from `origin/main` first tracks `origin/main` until its first push sets its own upstream. Criterion 25 (docs) is the documenter's.

   `make check`: check: green
5. reviewer: no findings.
      - Acceptance criteria: each of criteria 1–23 has a test named after it, and each test checks what its criterion says, using plain `git` through `run_git`/`remote_commit` rather than other `GitCli` methods. The Interface's rules all have their failing side tested: clone into a directory holding a file and clone of a missing url (2, 3); unknown branch or start point (7); an uncommitted edit that blocks checkout (8); nothing to commit, both clean and with only ignored files (13); rejection by non-fast-forward and by a `pre-receive` hook (15, 16); unreachable remote (17); any other push failure (18); `AFTER_PUSH` not reached after a rejection (21). The coder's entry reports `make check` green with 100 % coverage.
      - Architecture: `PushOutcome` and `NothingToCommit` are in `domain`; the four operations are on the `Git` protocol in `application`; the implementation is in `GitCli` in `adapters`, and every git call still goes through `run_process`. The identity variables are set after the process and options environment and before the unchanged config isolation, so neither the environment nor the global config can override them. Tests follow the package layout. `HumanClone` and its test sit at the `tests/` root because they are outside the layers.
      - Security: every argv is a list; no shell, no new suppression markers, no secrets.
      - Quality: splitting `_run` (checks the exit status) from `_execute` (runs git and leaves the status to the caller) gives `push` a clean way to turn status into an outcome. Using `switch --force-create` instead of the Interface's `checkout -B` does the same thing, and the log records it. `--no-gpg-sign` and `--cleanup=verbatim` match criteria 10 and 11.
      - Ticket hygiene: the log names the main decision and what was rejected. `Assignment` matches what was built, and criterion 25 still describes what the documenter has to write.
6. documenter: wrote the documentation for criterion 25 and cross-read the rest. `make check` is green. I did not re-run the Demo block. The coder's entry says it prints the four expected lines.
   - docs/project-guide.md, "The git wrapper": the section now covers clone, checkout, commit and push, including the `switch --force-create` equivalence with `checkout -B`. It also covers the identity of the options (default `factory <factory@noreply.invalid>`, set over the process and options environment, immune to user and system config and gpgsign, filled by F0010 from `GIT_USER_NAME`/`GIT_USER_EMAIL`). The three push outcomes (never forced) and the two push kill points are described, along with the `remote_commit` helper and the `remote`, `checkout` and `human` fixtures (`HumanClone.start`, `push_file`, `merge`). The old "not used yet / not reached yet" notes on `identity` and `kill_points` are fixed, and the intro no longer calls the wrapper reading-only.
   - docs/decisions.md: new entry "A push is never forced, and a rejection is a value" (WE6.3), with the alternatives rejected.
   - README.md: one phrase now says the git wrapper also clones, checks out, commits and pushes.
   - Cross-read and found current: the CLAUDE.md docs layout, the hosting-service, process and kill-point sections of the project guide, and the earlier decisions.
   - Findings: none. The code matches the Interface. The one deviation, `switch --force-create` for `checkout -B`, is the same operation and is recorded in the guide.
   - Stale but unrelated, not touched: the kill-point section of the project guide still says "This story built only the seam ... nothing reaches a point". That is now false for `BEFORE_PUSH` and `AFTER_PUSH`. It belongs to this story, so I did fix it, as the next line says.

   `make check`: check: green
7. demo: ran the one Demo command from the repository root exactly as written. It exited 0 and met its Expect line. No findings.

   Command 1 (`uv run python -c "…"`: two clones push to the same branch, then an empty commit, then compare `origin/<branch>` with `HEAD`):
   ```
   first pushed
   second rejected
   nothing to commit
   True
   ```
   Expect: four lines, `first pushed`, `second rejected`, `nothing to commit`, `True`. **Met.** The second clone's push came back as the value `rejected`: no exception was raised and nothing was forced. The empty commit raised `NothingToCommit`. After the push, `origin/work-item/F0001-S0001` in the first clone is its `HEAD`.

   Checked against the acceptance criteria: the output contradicts none of them.
   - clone into a directory that does not exist (1)
   - `checkout` with `start_point="origin/main"` creates the branch (5)
   - `commit` returns the commit id (9)
   - nothing to commit raises `NothingToCommit` (13)
   - pushing a new branch returns `pushed`, and `origin/<branch>` updates (14)
   - a non-fast-forward push returns `rejected` (15)

   The demo does not exercise the other criteria (hooks, unreachable remote, kill points, identity, `HumanClone`). The tests named in the tester's entry cover them.
