# The git wrapper: process, fetch and refs

## Assignment (as of log entry 1)

Start the git wrapper (R9): the one place that starts a subprocess for the wrappers (`run_process`), the git error types, and the first half of the reading operations of `GitCli`: fetch with prune, the remote-tracking branches, resolving a ref, a file at a commit, the files under a directory at a commit, and ancestry. History, changed paths and status follow in S0009; everything that writes follows in S0005 and S0010. Every operation takes and returns factory-shaped DTOs or plain types (R7), never git's text. Covers R9 and R5 (each command-line tool only behind a wrapper class: a search test proves that `subprocess` is started in one module only); keeps kept thing 3 (the remote is the truth: the wrapper reads remote-tracking refs and never local branches for `remote_branches`). Tests use a real bare repository in `tmp_path` and do not fake git. Precondition for the human: the one `subprocess.Popen` call needs four suppression markers (`noqa: S404`, `nosec B404`, `noqa: S603`, `nosec B603`) that CLAUDE.md lists under "Not without asking"; this story states them exactly (decision 9 of the feature), and the human adds one line to CLAUDE.md allowing exactly these four in `src/factory/adapters/process.py` before starting the story.

## Interface

`src/factory/adapters/process.py`

```python
class ProcessRequest(BaseModel):
    argv: Annotated[list[str], Field(min_length=1)]
    cwd: Path
    env: dict[str, str] | None = None
    time_limit: timedelta | None = None
    merge_stderr: bool = False

class ProcessResult(BaseModel):
    exit_status: int | None
    stdout: str
    stderr: str
    timed_out: bool
    duration: timedelta

def run_process(request: ProcessRequest) -> ProcessResult: ...
```

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
    ) -> None: ...
```

The rules, each with a criterion below:

- `run_process` never uses a shell. It starts the child in its own session; when `time_limit` is reached it kills the whole process group, so that children of the command end too, and returns with `exit_status` `None`, `timed_out` true and the output written so far. `time_limit` of `None` means no limit; otherwise it must be greater than zero. `env` of `None` makes the child inherit the current environment; a mapping is the child's whole environment. With `merge_stderr` the child's stderr goes into the same pipe as its stdout, in the order written, and `stderr` is empty. Output is decoded as UTF-8 with undecodable bytes replaced. A failure to start (`OSError`, for example `FileNotFoundError`) is not caught.
- `subprocess` is imported by `factory.adapters.process` only, and `shell=True`, `os.system` and `os.popen` are used nowhere in `src/factory`. The only suppression markers in `src/factory` are the four in `process.py`: `noqa: S404` and `nosec B404` on the line `import subprocess`, `noqa: S603` and `nosec B603` on the line that calls `subprocess.Popen`.
- `GitError.command` is `git ` followed by the arguments, for example `git fetch --prune origin`; its message is `<command> failed (exit <exit_status>): <output_tail>`, or `<command> failed (no exit status): <output_tail>` when `exit_status` is `None`. `output_tail` is the command's whole output, stdout and stderr merged.
- Every `GitCli` method runs `<executable> <arguments>` in `directory` through `run_process` with `time_limit`, with the current environment plus `GIT_CONFIG_NOSYSTEM=1` and `GIT_CONFIG_GLOBAL` set to the null device (`os.devnull`), so that no user or system configuration changes what the wrapper does.
- A command that exits non-zero, cannot be started, or reaches its `time_limit` raises `GitError` (exit status `None` and, for the time limit, the output tail `time limit reached`; for a command that cannot be started, the `OSError` text); `fetch` raises `FetchFailed` for every one of these.
- `fetch` runs `git fetch --prune origin`, so remote-tracking branches that the remote deleted are removed.
- `remote_branches` lists the branches under `refs/remotes/origin/` as `RemoteBranch(name, commit)`, with `name` without the `origin/` prefix, sorted by name in plain string order, without `HEAD`. Local branches are never listed.
- `resolve(ref)` returns the 40-character commit id the ref points to, or `None` when there is no such ref (also for `HEAD` in a repository without commits); any other failure is a `GitError`.
- `show_file(ref, path)` returns the file's text exactly as committed (UTF-8, trailing newline kept), or `None` when `path` is not a file at `ref` (absent, or a directory); an unknown `ref` is a `GitError`.
- `list_files(ref, directory)` returns the full repository-relative paths of all files under `directory` (given without a trailing slash) at `ref`, recursive, in plain string order; `[]` when the directory does not exist at `ref`; an unknown `ref` is a `GitError`. Names with spaces and non-ASCII characters come back exactly.
- `is_ancestor(ancestor, descendant)` is true when `ancestor` is reachable from `descendant`, a commit counting as its own ancestor; an unknown ref is a `GitError`.

The shared test fixtures, created here in `tests/conftest.py` with the helpers in `tests/git_support.py` (real `git` run with the same configuration isolation, author `Test Author <test@example.invalid>`): `remote` is a bare repository in `tmp_path` whose `main` holds `factory/pipeline.yml` with the text below, `factory/story-form.md` (the five headings `## Description`, `## Interface`, `## Acceptance criteria`, `## Smoke test`, `## Journal` under a title line), `factory/features/F0001-example/feature.md` (the line `# Example feature`) and `factory/features/F0001-example/backlog/F0001-S0001-first.md` (the line `# First story`); `checkout` is a `GitCli` on a clone of `remote`, built with `kill_points`.

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

Tests: `tests/adapters/test_process.py`, `tests/adapters/test_git_cli_reading.py`, `tests/domain/test_git.py`, `tests/domain/test_errors.py` (extended), `tests/test_process_search.py`, which uses `tests/source_search.py` (the helper from S0003 that parses every module under `src/factory` with `ast`). A test module assigns `GitCli` to a variable annotated `Git`, so that mypy checks the fit. The only waiting in the tests is for a child process that the `time_limit` kills.

## Acceptance criteria

1. `run_process` of a child that prints `out` to stdout and `err` to stderr and exits 0 returns `stdout == "out\n"`, `stderr == "err\n"`, `exit_status == 0`, `timed_out` false and a duration that is not negative; a child that prints its working directory prints `cwd`.
2. A child that exits with status 3 gives `exit_status == 3`; nothing is raised.
3. With `merge_stderr=True`, a child that writes `a` to stdout, `b` to stderr and `c` to stdout (flushing each) gives `stdout == "a\nb\nc\n"` and `stderr == ""`.
4. A given `env` is the child's whole environment: a variable set in the test process is absent in the child and a given variable is present; with `env=None` the child sees the test process's variable.
5. With `time_limit=timedelta(seconds=1)`, a child that sleeps 60 seconds after printing `started`, and a grandchild it started, are killed: `exit_status` is `None`, `timed_out` is true, `stdout` still holds `started`, and the call returns within 6 seconds; a child that ends within the limit gives `timed_out` false.
6. A missing executable raises `FileNotFoundError`; `ProcessRequest` rejects an empty `argv` and a `time_limit` of zero with `ValidationError`, and accepts a `time_limit` of one second.
7. Among the modules of `src/factory`, only `factory.adapters.process` imports `subprocess`, and no module under `src/factory` uses `shell=True`, `os.system` or `os.popen`.
8. The text `noqa`, `nosec`, `nosemgrep` and `pragma: allowlist secret` occurs under `src/factory` only in `process.py`, and there as exactly the four markers `noqa: S404`, `nosec B404`, `noqa: S603` and `nosec B603`, each on the line named in the Interface.
9. `GitError("git fetch --prune origin", 128, "fatal: x")` carries the three attributes and has the message `git fetch --prune origin failed (exit 128): fatal: x`; with `exit_status` `None` the message reads `failed (no exit status)`; `FetchFailed` is a subclass of `GitError`, and `GitError` is a subclass of `BoundaryError`.
10. `GitCli(directory, executable="/no/such/git").resolve("HEAD")` and `GitCli(directory, time_limit=timedelta(milliseconds=1)).resolve("HEAD")` raise `GitError` with `exit_status` `None` (the second with `time limit reached` in `output_tail`); `fetch` raises `FetchFailed` in both cases.
11. After another clone pushes a new branch to the remote, `remote_branches()` of the `checkout` does not list it; after `fetch()` it does, with the commit that was pushed.
12. After the remote deletes a branch, `fetch()` removes it from `remote_branches()`.
13. `fetch()` in a directory that is not a repository, and on a clone whose remote was removed, raises `FetchFailed` with `command == "git fetch --prune origin"`, `exit_status == 128` and a non-empty `output_tail`.
14. With `GIT_CONFIG_GLOBAL` in the test process pointing to a file that rewrites the remote's URL to a missing path (`url.<missing>.insteadOf`), `fetch()` still succeeds.
15. `remote_branches()` returns `RemoteBranch(name, commit)` for each branch of the remote with `name` free of the `origin/` prefix (a name with a slash such as `work-item/F0001-S0001` included), sorted by name, without `HEAD`, and a branch that exists only locally is not in the list.
16. `resolve` returns the 40-character commit id for `HEAD`, for `origin/main` and for a full commit id, and `None` for `origin/nope`.
17. `show_file("origin/main", path)` returns the text exactly as committed, trailing newline and non-ASCII characters included, and `show_file` at an older commit returns that commit's text.
18. `show_file` returns `None` for a path that does not exist at the ref and for a directory, and raises `GitError` for a ref that does not exist.
19. `list_files("origin/main", "factory/features")` returns the full paths of all files under it, sorted in plain string order, and a file named `read me é.txt` comes back as written.
20. `list_files` returns `[]` for a directory that does not exist at the ref and raises `GitError` for a ref that does not exist.
21. `is_ancestor` is true for a commit and a later commit, true for a commit and itself, and false for the later commit and the earlier one, and false for two commits on diverged branches.
22. `is_ancestor` raises `GitError` when either ref does not exist.
23. `GitCli` is not a subclass of `Git`, and a test module assigns a `GitCli` to a variable annotated `Git`, so that `make check` (mypy) proves the structural fit.
24. make check stays green.
25. docs: `docs/project-guide.md` describes the git wrapper (reached only through `Git` and `GitCli`, the isolated configuration, the tests against a real bare remote) and the rule that `subprocess` is started in `factory.adapters.process` only; `docs/decisions.md` records the four suppression markers in `process.py` and why there are no others (WE6.3).

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
