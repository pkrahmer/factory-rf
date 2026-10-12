# The git wrapper: clone, checkout, commit and push

## Assignment (as of log entry 1)

Add the first writing operations to `GitCli`: clone into the bound directory, check out a branch (creating or resetting it at a start point), commit every change, and push with its outcome as a value (`pushed`, `rejected`, `unreachable`), never forced. The factory's commits carry the identity that `GitCli` is given at construction (it comes from the instance's settings, R25), and no user or system git configuration can change it; a `GitCli` built without an identity cannot commit. `push` is where two of the four kill points of R36 live: `before-push` is reached between a commit and its push, `after-push` right after a successful push, so that later tests can kill the tick at either place. Covers R9 and R36 (the two push kill points); keeps kept thing 13 (a push is the only way the remote learns anything, and a rejected or unreachable push is a result the caller decides on) and kept thing 18 (the identity is set, from settings, not fixed in code). The test fixture `human`, a second clone that acts as the human, is built here because the push tests need a second writer; F0006 uses its `merge` for the three merge methods. Deleting branches and merging follow in S0012; reset, revert and move in S0013.

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

- When the `GitCli` has an `identity` (S0005), the environment of every call also sets `GIT_AUTHOR_NAME` and `GIT_COMMITTER_NAME` to `identity.name` and `GIT_AUTHOR_EMAIL` and `GIT_COMMITTER_EMAIL` to `identity.email`, over whatever the process or `environment` has; the isolation from the user and system configuration of S0005 stays.
- `clone(url)` runs `git clone <url> <directory>` from the parent of the bound directory, creating missing parents. The directory must be missing or empty; otherwise `GitError`. After a clone the checkout is on the remote's default branch with `origin` set.
- `checkout(branch)` switches to the existing local branch; when the branch exists only as `origin/<branch>`, it creates the local branch at the remote's commit. `checkout(branch, start_point=ref)` creates the branch at `ref` or resets an existing branch to `ref` (`git checkout -B`). An unknown branch or start point, or uncommitted changes that stand in the way, is a `GitError` and leaves the current branch and the changes as they were.
- `commit(message)` stages every change (`git add -A`; ignored paths stay out), commits with `message` as given, and returns the new commit's id. When nothing is staged it raises `NothingToCommit` and commits nothing. On a `GitCli` without an `identity` it raises `GitError` with `exit_status` `None` and the output tail `no commit identity`, before it runs git.
- `push(branch)` runs `git push --porcelain --set-upstream origin <branch>`, never with force. It reaches `KillPoint.BEFORE_PUSH` before running git, and `KillPoint.AFTER_PUSH` only after a push that succeeded (when the `GitCli` has kill points). It returns `"pushed"` when git exits 0; `"rejected"` when the remote refused the update (a non-fast-forward, or a hook of the remote declined it: git reports the ref with `!`); `"unreachable"` when git could not reach the remote (exit 128 with `Could not read from remote repository`, `does not appear to be a git repository`, `unable to access` or `Could not resolve host` in the output); any other failure, such as an unknown local branch, is a `GitError`. After `"pushed"`, `origin/<branch>` in the checkout is the pushed commit.

The test fixture `human` in `tests/conftest.py`, with the class in `tests/human_clone.py`, driven through `GitCli` and `run_git`:

```python
class HumanClone:
    def __init__(self, directory: Path, remote: Path) -> None: ...
    def start(self, path: str) -> None: ...
    def push_file(self, branch: str, path: str, text: str) -> None: ...
    def merge(self, branch: str, method: Literal["merge", "squash", "rebase"]) -> None: ...
```

`HumanClone` is a second clone of the `remote` fixture, built with `identity=TEST_IDENTITY`. `start(path)` moves a story file from `backlog/` to `in-progress/` in the same feature folder on `main`, commits and pushes. `push_file(branch, path, text)` writes the file on that branch (created from `origin/main` when the remote has no such branch), commits and pushes. `merge(branch, method)` brings `origin/<branch>` into `main` and pushes `main`: with `"merge"` as a merge commit, with `"squash"` as one ordinary commit that leaves the branch tip outside the history of `main`, with `"rebase"` as the branch's commits replayed on `main` with no merge commit.

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
11. A commit has the author and the committer given as `identity` at construction, also when the test process sets `GIT_AUTHOR_NAME`, and when `GIT_CONFIG_GLOBAL` points to a file with another `user.name` and `commit.gpgsign = true`.
12. `commit` on a `GitCli` built without an `identity` raises `GitError` with `exit_status` `None` and `no commit identity` in `output_tail`, and `HEAD` is unchanged.
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
25. docs: `docs/project-guide.md` explains the writing operations of the git wrapper (the identity from settings, push outcomes as values, never forced) and the two push kill points, and the fixtures `remote`, `checkout` and `human` for tests; `docs/operator-guide.md` names `GIT_USER_NAME` and `GIT_USER_EMAIL` as the commit identity; `docs/decisions.md` records why a push is never forced and a rejection is a value, not an error (WE6.3).

## Demo

```bash
uv run python -c "
import tempfile
from pathlib import Path
from factory.adapters.git_cli import GitCli
from factory.adapters.process import ProcessRequest, run_process
from factory.domain.errors import NothingToCommit
from factory.domain.git import GitIdentity

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
first = GitCli(root / 'first', identity=identity)
second = GitCli(root / 'second', identity=identity)
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
