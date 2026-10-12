# The git wrapper: fetch and refs

## Assignment (as of log entry 1)

Start the git wrapper (R9): the git error types and the first half of the reading operations of `GitCli`: fetch with prune, the remote-tracking branches, resolving a ref, a file at a commit, the files under a directory at a commit, and ancestry. The commit identity is a constructor argument that comes from the instance's settings (`GIT_USER_NAME` and `GIT_USER_EMAIL`, R25; F0010's preflight checks that it is set, kept thing 18); `commit` uses it in S0006. Every command runs through `run_process` (S0004) with the user's and the system's git configuration ignored, so that nothing but the factory decides what git does. Git gets its credentials only from the factory process's environment, never from global or system configuration: `GitCli` inherits the process environment and takes an optional extra environment, which is how the factory's own pushes get the token while the agent run never receives it (WE3.5, R33). History, changed paths and status follow in S0011; everything that writes follows in S0006, S0012 and S0013. Every operation takes and returns factory-shaped DTOs or plain types (R7), never git's text. Covers R9; keeps kept thing 3 (the remote is the truth: the wrapper reads remote-tracking refs and never local branches for `remote_branches`). The shared fixtures `remote` and `checkout` are built here, because the first tests of a git operation need them. Tests use a real bare repository in `tmp_path` and do not fake git. Test helpers start git through `factory.adapters.process.run_process`, never through `subprocess`.

## Interface

`src/factory/domain/errors.py` (adds to the module from S0001 and S0002)

```python
class GitError(BoundaryError):
    command: str
    exit_status: int | None
    output_tail: str
    def __init__(self, command: str, exit_status: int | None, output_tail: str) -> None: ...

class FetchFailed(GitError): ...
```

`src/factory/domain/paths.py` (adds one name)

```python
REMOTE = "origin"
```

`src/factory/domain/git.py` (adds to the module from S0002)

```python
class RemoteBranch(BaseModel):
    name: str
    commit: CommitId

class GitIdentity(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    email: Annotated[str, Field(min_length=1)]
```

`src/factory/application/git.py`

```python
class Git(Protocol):
    def fetch(self) -> None: ...
    def remote_branches(self) -> list[RemoteBranch]: ...
    def resolve(self, ref: str) -> CommitId | None: ...
    def show_file(self, ref: str, path: str) -> str | None: ...
    def list_files(self, ref: str, directory: str) -> list[str]: ...
    def is_ancestor(self, ancestor: str, descendant: str) -> bool: ...
```

`src/factory/adapters/git_cli.py`

```python
GIT_TIME_LIMIT = timedelta(minutes=5)

class GitCli:      # satisfies Git structurally, no inheritance
    def __init__(
        self,
        directory: Path,
        kill_points: KillPoints | None = None,
        *,
        executable: str = "git",
        time_limit: timedelta = GIT_TIME_LIMIT,
        environment: Mapping[str, str] | None = None,
        identity: GitIdentity | None = None,
    ) -> None: ...
```

The rules, each with a criterion below:

- `GitIdentity` is frozen, forbids unknown keys and has a non-empty `name` and a non-empty `email`; `GitCli` keeps the `identity` it is given for S0006's `commit` and does nothing else with it here.
- `GitError.command` is `git ` followed by the arguments, for example `git fetch --prune origin`; its message is `<command> failed (exit <exit_status>): <output_tail>`, or `<command> failed (no exit status): <output_tail>` when `exit_status` is `None`. `output_tail` is the last 30 lines of the command's output, stdout and stderr merged in the order written (all of it when it has fewer lines).
- Every `GitCli` method runs `<executable> <arguments>` in `directory` through `run_process` with `merge_stderr=True` and `time_limit`. The environment of the call is the current environment of the process, then the entries of `environment`, then `GIT_CONFIG_NOSYSTEM=1` and `GIT_CONFIG_GLOBAL` set to the null device (`os.devnull`), so that no user or system configuration changes what the wrapper does and `environment` cannot lift this.
- Credentials reach git only through the environment: the process environment and `environment` pass unchanged to git (for example `GIT_ASKPASS`, or a credential setting given as `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_<n>` and `GIT_CONFIG_VALUE_<n>`), and global or system configuration is never read.
- A command that exits non-zero, cannot be started, or reaches its `time_limit` raises `GitError` (exit status `None` and, for the time limit, the output tail `time limit reached`; for a command that cannot be started, the `OSError` text); `fetch` raises `FetchFailed` for every one of these.
- `fetch` runs `git fetch --prune origin`, so remote-tracking branches that the remote deleted are removed.
- `remote_branches` lists the branches under `refs/remotes/origin/` as `RemoteBranch(name, commit)`, with `name` without the `origin/` prefix, sorted by name in plain string order, without `HEAD`. Local branches are never listed.
- `resolve(ref)` returns the 40-character commit id the ref points to, or `None` when there is no such ref (also for `HEAD` in a repository without commits); any other failure is a `GitError`.
- `show_file(ref, path)` returns the file's text exactly as committed (UTF-8, trailing newline kept), or `None` when `path` is not a file at `ref` (absent, or a directory); an unknown `ref` is a `GitError`.
- `list_files(ref, directory)` returns the full repository-relative paths of all files under `directory` (given without a trailing slash) at `ref`, recursive, in plain string order; `[]` when the directory does not exist at `ref`; an unknown `ref` is a `GitError`. Names with spaces and non-ASCII characters come back exactly.
- `is_ancestor(ancestor, descendant)` is true when `ancestor` is reachable from `descendant`, a commit counting as its own ancestor; an unknown ref is a `GitError`.

The shared test fixtures, created here in `tests/conftest.py` with the helpers in `tests/git_support.py` (`run_git` runs real `git` through `run_process` with the same configuration isolation and the author `Test Author <test@example.invalid>`; `write_executable(directory, body)` writes a script whose first line is `#!` and `sys.executable`, for a stand-in `executable`; `TEST_IDENTITY` is `GitIdentity(name="Test Author", email="test@example.invalid")`): `remote` is a bare repository in `tmp_path` whose `main` holds `factory/pipeline.yml` with the text below, `factory/story-form.md` (the five headings `## Description`, `## Interface`, `## Acceptance criteria`, `## Smoke test`, `## Journal` under a title line), `factory/features/F0001-example/feature.md` (the line `# Example feature`) and `factory/features/F0001-example/backlog/F0001-S0001-first.md` (the line `# First story`); `checkout` is a `GitCli` on a clone of `remote`, built with `kill_points` and `identity=TEST_IDENTITY`.

```yaml
contract: "1.0"
attempts_cap: 2
crash_cap: 2
acceptance_stage: acceptance
project_commands:
  check: {time_limit: 10}
  lint: {time_limit: 5}
  test: {time_limit: 10}
roles:
  intake: {write_paths: ["{work_item}"]}
  tester: {write_paths: ["tests/*"]}
  coder: {write_paths: ["src/*"]}
  reviewer: {write_paths: ["{work_item}"]}
  documenter: {write_paths: ["README.md", "docs/*"]}
  smoke-tester: {write_paths: ["{work_item}"]}
  acceptance-reviewer: {write_paths: ["{work_item}", "{feature}/backlog/*"]}
stages:
  intake: {role: intake, next: [tests]}
  tests: {role: tester, next: [doing], checks: [lint], reports: [test]}
  doing: {role: coder, next: [review, tests], checks: [check]}
  review: {role: reviewer, next: [docs, doing], round_cap: 3}
  docs: {role: documenter, next: [smoke-test, doing], checks: [check], round_cap: 3}
  smoke-test: {role: smoke-tester, next: [approval, doing], round_cap: 3}
  acceptance: {role: acceptance-reviewer, next: [approval]}
  approval: {approval: true, next: [done, doing]}
  done: {}
```

Tests: `tests/adapters/test_git_cli_reading.py`, `tests/domain/test_git.py` (also the `GitIdentity` cases), `tests/domain/test_errors.py` (extended: it gains new tests only, no existing test is changed); `tests/conftest.py` (extended in the same way) gains `remote` and `checkout`; `tests/git_support.py` is new. A test module assigns `GitCli` to a variable annotated `Git`, so that mypy checks the fit. A test that needs a commit id as a literal uses a low-entropy one such as `"a" * 40`, so that `make secrets` stays green. The only waiting in the tests is for a stand-in git that the `time_limit` kills.

## Acceptance criteria

1. `GitError("git fetch --prune origin", 128, "fatal: x")` carries the three attributes and has the message `git fetch --prune origin failed (exit 128): fatal: x`; with `exit_status` `None` the message reads `failed (no exit status)`; `FetchFailed` is a subclass of `GitError`, and `GitError` is a subclass of `BoundaryError`.
2. With a stand-in `executable` that prints 40 numbered lines to stderr and exits 1, a `GitCli` method raises `GitError` whose `output_tail` holds exactly the lines 11 to 40; with a stand-in that prints 3 lines, the tail holds all 3.
3. `GitCli(directory, executable="/no/such/git").resolve("HEAD")` raises `GitError` with `exit_status` `None` and a non-empty `output_tail`, and `fetch()` raises `FetchFailed`.
4. `GIT_TIME_LIMIT` is `timedelta(minutes=5)`; with a stand-in `executable` that sleeps 60 seconds and `time_limit=timedelta(seconds=1)`, `resolve("HEAD")` raises `GitError` with `exit_status` `None` and `time limit reached` in `output_tail` within 6 seconds, and `fetch()` raises `FetchFailed`.
5. After another clone pushes a new branch to the remote, `remote_branches()` of the `checkout` does not list it; after `fetch()` it does, with the commit that was pushed.
6. After the remote deletes a branch, `fetch()` removes it from `remote_branches()`.
7. `fetch()` in a directory that is not a repository, and on a clone whose remote was removed, raises `FetchFailed` with `command == "git fetch --prune origin"`, `exit_status == 128` and an `output_tail` that is not empty; for the first case it contains git's own text `not a git repository`.
8. With `GIT_CONFIG_GLOBAL` in the test process pointing to a file that rewrites the remote's URL to a missing path (`url.<missing>.insteadOf`), `fetch()` still succeeds; the same when the file is named by `GIT_CONFIG_GLOBAL` in the `environment` argument.
9. With `GIT_CONFIG_SYSTEM` in the test process pointing to a file that rewrites the remote's URL to a missing path, `fetch()` still succeeds.
10. On a clone whose `origin` is a URL that does not exist, `fetch()` raises `FetchFailed`; with `GitCli(..., environment=...)` holding `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=url.<the real remote>.insteadOf` and `GIT_CONFIG_VALUE_0=<that URL>`, the same `fetch()` succeeds.
11. The same entries in the environment of the test process, with no `environment` argument, make that `fetch()` succeed as well.
12. `remote_branches()` returns `RemoteBranch(name, commit)` for each branch of the remote with `name` free of the `origin/` prefix (a name with a slash such as `work-item/F0001-S0001` included), sorted by name, without `HEAD`, and a branch that exists only locally is not in the list.
13. `resolve` returns the 40-character commit id for `HEAD`, for `origin/main` and for a full commit id.
14. `resolve` returns `None` for `origin/nope` and for `HEAD` in a repository without commits.
15. `show_file("origin/main", path)` returns the text exactly as committed, trailing newline and non-ASCII characters included, and `show_file` at an older commit returns that commit's text.
16. `show_file` returns `None` for a path that does not exist at the ref and for a directory, and raises `GitError` for a ref that does not exist.
17. `list_files("origin/main", "factory/features")` returns the full paths of all files under it, sorted in plain string order, and a file named `read me é.txt` comes back as written.
18. `list_files` returns `[]` for a directory that does not exist at the ref and raises `GitError` for a ref that does not exist.
19. `is_ancestor` is true for a commit and a later commit, true for a commit and itself, and false for the later commit and the earlier one, and false for two commits on diverged branches.
20. `is_ancestor` raises `GitError` when either ref does not exist.
21. `GitIdentity(name="factory", email="factory@noreply.invalid")` is accepted; an empty `name` and an empty `email` are rejected with `ValidationError`; it rejects an unknown keyword argument and assignment to a field.
22. `GitCli` is not a subclass of `Git`, and a test module assigns a `GitCli` to a variable annotated `Git`, so that `make check` (mypy) proves the structural fit.
23. make check stays green.
24. docs: `docs/project-guide.md` describes the git wrapper (reached only through `Git` and `GitCli`, the isolated configuration, the credentials that reach git only through the process environment and `environment`, the tests against a real bare remote); `docs/operator-guide.md` says that git gets its token from the factory process's environment and from nowhere else; `docs/decisions.md` records why global and system git configuration are ignored (WE6.3).

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
(work / 'docs').mkdir()
(work / 'docs' / 'read me.txt').write_text('hello\n')
git(work, 'add', '-A')
git(work, 'commit', '-q', '-m', 'first')
git(root, 'init', '-q', '--bare', '--initial-branch=main', 'remote.git')
git(work, 'remote', 'add', 'origin', str(root / 'remote.git'))
git(work, 'push', '-q', 'origin', 'main')
cli = GitCli(work)
cli.fetch()
print([branch.name for branch in cli.remote_branches()])
print(repr(cli.show_file('origin/main', 'docs/read me.txt')))
print(cli.list_files('origin/main', 'docs'))
print(cli.show_file('origin/main', 'missing.txt'), cli.resolve('origin/nope'))
print(cli.is_ancestor('origin/main', 'main'))
"
```
Expect: five lines: `['main']`, then `'hello\n'`, then `['docs/read me.txt']`, then `None None`, then `True`.

```bash
uv run python -c "
import tempfile
from pathlib import Path
from factory.adapters.git_cli import GitCli
from factory.domain.errors import FetchFailed
try:
    GitCli(Path(tempfile.mkdtemp())).fetch()
except FetchFailed as error:
    print(type(error).__name__, error.command, error.exit_status)
"
```
Expect: one line, `FetchFailed git fetch --prune origin 128`.

## Log (append only)

1. 2026-10-12 human: created.
