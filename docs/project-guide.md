# Project guide

The guide for agents working on `factory-rf`: how the code is laid out, where a change belongs, which conventions the checks do not catch, and what to read first. It is filled in story by story. The documenter stage fills this in from the stories' docs criteria; until then `CLAUDE.md` holds the rules.

## Errors

`factory.domain.errors.FactoryError` is the root of every error the factory raises on purpose. Later stories add their error types under it. `InjectedKill` (below) is deliberately not one.

`BoundaryError` (a `FactoryError`) is the root of the errors for an outside party that failed. `HostingServiceError(operation, detail)` is its first subtype: every implementation of the hosting-service interface raises it for every failing call, and its message is `hosting service <operation> failed: <detail>`. `operation` and `detail` are attributes.

`GitError(command, exit_status, output_tail)` is its second subtype, for the git wrapper. `command` is `git ` and the arguments (`git fetch --prune origin`); `exit_status` is `None` when git could not be started or hit its time limit; `output_tail` is the last 30 lines of the output, stdout and stderr merged (all of it when shorter). The message is `<command> failed (exit <status>): <tail>`, or `failed (no exit status)` when the status is `None`. `FetchFailed` is a `GitError` that `fetch` raises for every failure.

`ProjectCommandError(command, detail)` is its third subtype, for the project commands: it is raised only when a command cannot be started (an invalid name, or an executable the operating system cannot start). The message is `project command <command> failed: <detail>`; `command` and `detail` are attributes. A red command is a result, not this error.

## The hosting service

The factory reaches the hosting service (pull requests and their comments) only through the `HostingService` protocol in `factory.application.hosting`. Nothing else may call it, and the application layer knows no concrete client. `PyGithubHostingService` (`factory.adapters.pygithub_hosting`) is the one client; the one fake follows in a later story. Build comments from the service's data with `PullRequestComment.from_body`, so that `by_factory` and `key` always agree with the body.

The ten operations:

| Operation | Returns | Purpose |
|---|---|---|
| `create_pull_request(branch, title, body, *, draft)` | `PullRequestView` | open a pull request, as draft or ready |
| `find_open_pull_request(branch)` | `PullRequestView \| None` | the open pull request of a branch |
| `get_pull_request(number)` | `PullRequestView` | read state, draft flag and merge state |
| `list_comments(number)` | `list[PullRequestComment]` | comments with id and author |
| `post_comment(number, text, key)` | `PostOutcome` | post with the marker; `"already_posted"` if the key is already there |
| `close(number)`, `reopen(number)` | `None` | change the state |
| `set_draft(number, draft)` | `None` | mark draft or ready |
| `set_description(number, body)` | `None` | replace the description (the one projection of the work item) |
| `set_labels(number, labels)` | `None` | write the labels |

Labels are a projection of the stage: they are written and never read back, so no operation returns them and `PullRequestView` has no label field. `LABEL_PREFIX` (`"stage:"`) in `factory.domain.paths` is the prefix of those labels, and `MAIN_BRANCH` is `"main"`.

### The PyGithub client

`PyGithubHostingService(repository, kill_points=None)` implements the ten operations on a PyGithub `Repository`. It satisfies `HostingService` structurally and does not inherit it. The constructor reads nothing from the repository. Wiring that builds the `Repository` from the token comes with `factory.entry.wiring` (F0002 onward, token in F0010).

- Every failing call raises `HostingServiceError(operation, detail)`: a `github.GithubException` or an `OSError` (a connection error is one) inside any of the ten operations is re-raised with the operation's name and `str(error)` as detail, chained to the original. Any other exception, and `InjectedKill`, passes through unchanged.
- `post_comment` lists the comments first and returns `"already_posted"` without posting when one has the same key; otherwise it posts `render_post(text, key)`, reaches `KillPoint.AFTER_POST` and returns `"posted"`.
- `find_open_pull_request` asks for open pull requests with head `<owner login>:<branch>`. A view's `state` is `merged` when PyGithub says merged, else `open` or `closed`; `merge_commit` is set only for a merged pull request, even though GitHub reports a test-merge commit for an open one.
- `list_comments` sorts by id, oldest first, and reads a naive `created_at` as UTC.
- `set_labels` keeps the labels that do not start with `LABEL_PREFIX` and adds the given ones; the names it read are never returned.
- `github` is imported by this module only. No module in `src/factory` imports another route to the hosting service (`requests`, `httpx`, `aiohttp`, `urllib3`, `urllib.request`, `http.client`, `socket`, `git`, `pygit2`, `dulwich`, `githubkit`) or contains the string `"gh"`; `tests/test_hosting_search.py` checks it.

Tests do not call PyGithub. `tests/adapters/test_pygithub_hosting.py` uses the recording stand-ins of PyGithub's objects in `tests/adapters/pygithub_stand_ins.py`, passed in with `typing.cast`; the fake hosting service follows in a later story. A real call is first seen by the baseline run. Use a low-entropy literal such as `"a" * 40` for a commit id in a test, so that `make secrets` stays green.

### Data

The models in `factory.domain.hosting` are frozen, forbid unknown keys, and hold aware datetimes converted to UTC.

- `PullRequestView`: `number`, `branch`, `title`, `state` (`open`, `closed` or `merged`), `draft`, `merge_commit`, `url`. `merge_commit` is a 40-character lowercase hex commit id exactly when the state is `merged`, otherwise `None`.
- `PullRequestComment`: `id`, `author`, `body`, `created_at`, `by_factory`, `key`.

### The marker and the post key

Every post the factory makes ends with two lines: the marker `<!-- factory -->` and a key comment `<!-- factory key=<work item>:<kind>:<n> -->`, for example `<!-- factory key=F0001-S0001:question:7 -->`. `n` is lowercase hex and not empty; `kind` is one of `question`, `attempts_cap`, `round_cap`, `crash_cap`, `send_back`, `stall`, `expiry`, `correction`, `error`, `cost_table`.

- `render_post(text, key)` gives `text` without trailing whitespace, a blank line, the marker, and the key comment. Nothing follows.
- `parse_post_key(body)` reads only the last non-blank line, which must be exactly a valid key comment (trailing whitespace and `\r` are ignored). Anything else gives `None`.
- `PullRequestComment.from_body` sets `by_factory` when the body contains the marker, whoever the author is, and `key` to the parsed key when it is by the factory.

Why: see `docs/decisions.md`.

## The git wrapper

Git is reached only through the `Git` protocol (`factory.application.git`) and its one implementation `GitCli` (`factory.adapters.git_cli`), which satisfies the protocol structurally and does not inherit it. Every command goes through `run_process`; no other module starts git. It reads, and it writes the first things: clone, checkout, commit and push. Deleting branches and merging, then reset, revert and move, follow in later stories.

`GitCli(directory, options=None)` works in `directory`. `options` is a `GitOptions` (`factory.domain.git`; frozen, unknown keys forbidden), and `None` means `GitOptions()`:

| Field | Default | Meaning |
|---|---|---|
| `identity` | `GitIdentity(name="factory", email="factory@noreply.invalid")` | author and committer of the factory's commits; non-empty name and email. The default is only what an unset instance setting falls back to |
| `environment` | `{}` | extra environment for git; each `GitOptions` has its own dict |
| `kill_points` | `None` | reached by `push` (see below) |
| `executable` | `"git"` | the program to run (tests give a stand-in) |
| `time_limit` | `GIT_TIME_LIMIT` (5 minutes) | per command |

F0010's wiring fills `identity` from the instance settings `GIT_USER_NAME` and `GIT_USER_EMAIL`, and `environment` with the token for the factory's own pushes, so that the agent run never receives it.

The ten operations, six reading and four writing:

| Operation | Returns |
|---|---|
| `fetch()` | `None`; runs `git fetch --prune origin`, so branches the remote deleted disappear; any failure is `FetchFailed` |
| `remote_branches()` | `list[RemoteBranch(name, commit)]` from `refs/remotes/origin/`, name without `origin/`, sorted by name, without `HEAD`; local branches are never listed |
| `resolve(ref)` | the 40-character commit id, or `None` when there is no such ref (also `HEAD` without commits) |
| `show_file(ref, path)` | the text exactly as committed, or `None` when `path` is absent or a directory; an unknown `ref` is a `GitError` |
| `list_files(ref, directory)` | full paths of all files under `directory` (no trailing slash), recursive, in string order; `[]` when the directory is absent; an unknown `ref` is a `GitError` |
| `is_ancestor(ancestor, descendant)` | whether `ancestor` is reachable from `descendant` (a commit is its own ancestor); an unknown ref is a `GitError` |
| `clone(url)` | `None`; runs `git clone <url> <directory>` from the parent of the bound directory and creates missing parents. The directory must be missing or empty, otherwise `GitError`. Afterwards the checkout is on the remote's default branch with `origin` set |
| `checkout(branch, *, start_point=None)` | `None`; switches to the local branch, or creates it at `origin/<branch>` when only the remote has it. With `start_point` it creates the branch there or resets an existing one to it (`git switch --force-create`, the same as `checkout -B`). An unknown branch or start point, or changes that stand in the way, is a `GitError` and leaves the branch and the changes as they were |
| `commit(message)` | the new commit id; stages every change (`add --all`, ignored paths stay out) and commits `message` verbatim, unsigned. Nothing staged raises `NothingToCommit` (a `GitError`) and commits nothing |
| `push(branch)` | `PushOutcome`: `"pushed"`, `"rejected"` or `"unreachable"` (below) |

Any other failure of a command (non-zero exit, cannot be started, `time_limit` reached) is a `GitError`. A missing ref or path is told apart from a failure by exit status and by `ls-tree -z` listings, never by git's wording.

Push never forces: it runs `git push --porcelain --set-upstream origin <branch>`. The outcome is a value, because the caller decides what a refusal means:

- `"pushed"`: git exited 0; afterwards `origin/<branch>` in the checkout is the pushed commit.
- `"rejected"`: the remote refused the update, a non-fast-forward or a remote hook that declined it (git marks the ref with `!`).
- `"unreachable"`: exit 128 with `Could not read from remote repository`, `does not appear to be a git repository`, `unable to access` or `Could not resolve host` in the output.
- Any other failure, such as an unknown local branch, is a `GitError`.

The push kill points: `KillPoint.BEFORE_PUSH` is reached once per call, before git runs (between a commit and its push, so nothing reaches the remote); `KillPoint.AFTER_PUSH` is reached only after a push that returned `"pushed"`. A rejected or unreachable push reaches only the first. A `GitCli` without kill points pushes normally.

Identity: every call also sets `GIT_AUTHOR_NAME`, `GIT_COMMITTER_NAME`, `GIT_AUTHOR_EMAIL` and `GIT_COMMITTER_EMAIL` from `options.identity`, over the process environment and `options.environment`. No user or system configuration can change it, and `commit.gpgsign` is ignored. F0010 fills `identity` from `GIT_USER_NAME` and `GIT_USER_EMAIL`; a `GitCli` built without options commits as `factory <factory@noreply.invalid>`.

Configuration is isolated: each call runs with the process environment, then `options.environment`, then the identity, then `GIT_CONFIG_NOSYSTEM=1` and `GIT_CONFIG_GLOBAL` set to the null device. The isolation and the identity come last, so `options.environment` cannot lift them. Credentials therefore reach git only through the environment (for example `GIT_ASKPASS`, or `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_<n>`, `GIT_CONFIG_VALUE_<n>`), never through global or system configuration, and never inside a URL, because git may print a URL. Why: see `docs/decisions.md`.

Tests use real git. The `remote` fixture is a bare repository in `tmp_path` with the pipeline definition, the story form and one feature with one story on `main`, and `checkout` is a `GitCli` on a clone of it (identity `TEST_IDENTITY`). `tests/git_support.py` has the helpers: `run_git` (through `run_process`, same isolation, author `Test Author`) and `write_executable` for a stand-in `executable`, and `remote_commit(remote, branch)`, which reads a branch of the bare remote with plain git and gives `None` when it is absent. Git is not faked. Tests check results with plain git through `run_git`, not through other `GitCli` methods.

The `human` fixture (`HumanClone` in `tests/human_clone.py`) is a second clone of `remote`, the writer a push test needs besides `checkout`; it is built with `TEST_IDENTITY` and drives `GitCli`. `start(path)` moves a story file from `backlog/` to `in-progress/` on `main`, commits and pushes. `push_file(branch, path, text)` writes the file on that branch (created from `origin/main` if the remote has none), commits and pushes. `merge(branch, method)` brings `origin/<branch>` into `main` and pushes it: `"merge"` as a merge commit, `"squash"` as one ordinary commit that leaves the branch tip outside the history of `main`, `"rebase"` as the branch's commits replayed with no merge commit. Every push it makes must return `"pushed"`.

## Project commands

The factory reaches a project's build only through the `ProjectCommands` protocol (`factory.application.project_commands`). It has one operation, `run(command, *, time_limit) -> CheckResult`. `MakeProjectCommands(directory, kill_points=None, *, executable="make")` (`factory.adapters.make_commands`) is the first implementation. It satisfies the protocol structurally and does not inherit it. The string `"make"` appears in no other module under `src/factory`; `tests/test_make_search.py` checks it. The pipeline uses the results from F0005, the preflight's probe from F0010.

`run` starts `<executable> --no-print-directory <command>` in `directory` through `run_process`, with stderr merged into stdout. The environment is the current one less `MAKELEVEL`, `MAKEFLAGS` and `MFLAGS`. Without that, a run inside `make check` (where `MAKELEVEL` is set) would print `make[N]: Entering directory` lines that a run on its own does not. `directory` is where make finds the project's Makefile.

Rules of `run`:

- `time_limit` of zero or less raises `ValueError`.
- `command` must match `^[a-z][a-z0-9-]*$`, checked with a full match. Otherwise `ProjectCommandError` is raised before anything is started. So is an `executable` that cannot be started; the detail is the operating system's message.
- The exit status is the only judgment. 0 is `"passed"`, any other is `"failed"`, and a command ended by the `time_limit` is `"time_limit"` with `exit_status` `None`; the process group is killed. GNU make, not the recipe, sets the status: it exits 2 whenever a recipe fails, whatever status the recipe's command had, and when the target is missing. A missing target is therefore a failed command, not an error.
- `output_tail` is the last 30 lines (`OUTPUT_TAIL_LINES`) of the merged output, in the order written; all of it when shorter.
- `last_line` is the last line that is not blank and does not start with `make:` or `make[` (make's own messages); `""` when there is none.
- `duration` is the time the command ran.
- `kill_points` is accepted so that wiring builds every wrapper the same way; this wrapper reaches no kill point.

`CheckResult` (`factory.domain.checks`) is frozen, forbids unknown keys, and has the fields `command`, `status`, `exit_status`, `duration`, `last_line` and `output_tail`. `status` and `exit_status` must agree (`status_of(exit_status)` is the one mapping), or validation fails. `passed` is true only for `"passed"`. The result is generic: it carries no layer names (R8), and no identifier in the three modules contains `layer`.

A project declares its own layers and checks them with a project command of its own. To add the layers check, the project adds a make target (for example `layers`, which calls its tool through uv) to its Makefile and, where it belongs in the gate, makes `check` depend on it. The factory sees only that target's `CheckResult`: its status, `last_line` and `output_tail`.

```python
result = MakeProjectCommands(Path(".")).run("check", time_limit=timedelta(minutes=10))
if not result.passed:
    print(result.status, result.exit_status, result.last_line)
```

Tests write a Makefile into `tmp_path` and run the class against it; nothing is faked.

## Starting a process

`subprocess` is imported, and a process started, in `factory.adapters.process` only (R5). The git wrapper, the make class and the `claude -p` runtime each reach their tool through `run_process(request) -> ProcessResult`; no other module calls a command-line tool.

`ProcessRequest` (frozen, unknown keys forbidden) holds:

- `argv`: the program and its arguments, at least one element, passed as given. There is never a shell, so `$HOME; echo x` reaches the child as that text.
- `cwd`: the working directory.
- `env`: `None` lets the child inherit the current environment; a mapping is the child's whole environment, nothing is added.
- `time_limit`: `None` for no limit, otherwise greater than zero (a zero or negative value is a `ValidationError`).
- `merge_stderr`: the child's stderr goes into the same pipe as its stdout, in the order written, and `ProcessResult.stderr` is empty.

The child runs in its own session, with stdin closed. At the `time_limit` the whole process group is killed with SIGKILL, so what the command started ends too, and `run_process` returns with `exit_status=None`, `timed_out=True` and the output written so far. A child that ends in time gives its real exit status and `timed_out=False`; a non-zero status is returned, not raised. Output is decoded as UTF-8 with undecodable bytes replaced. A failure to start, such as `FileNotFoundError`, is an `OSError` and is not caught: the wrapper above decides what it means.

```python
result = run_process(ProcessRequest(argv=["git", "status"], cwd=repo, time_limit=timedelta(seconds=30)))
```

Known limits: after the kill, the output is read without a limit, so a descendant that left the group (by calling `setsid`) and still holds the pipe would block the call; and a child that exits normally but leaves a background process holding its stdout open makes the call wait for that process (bounded by `time_limit` if one is set).

`tests/test_process_search.py` keeps the boundary: only `process.py` imports `subprocess`; `shell=True`, `os.system`, `os.popen`, `os.exec*`, `os.spawn*`, `os.posix_spawn*` and `asyncio.create_subprocess_*` are used nowhere under `src/factory`; and the only suppression markers there are the four in `process.py` (`noqa: S404` and `nosec B404` on `import subprocess`, `noqa: S603` and `nosec B603` on the `subprocess.Popen(` line). Do not write those marker words in a comment or docstring in `src/factory`. Why: see `docs/decisions.md`. Tests run real child processes (Python one-liners through `sys.executable`) in `tmp_path`; nothing is faked.

## Kill points: testing a crash

A test that must show the factory survives its own death arms a kill point. The seam is `factory.domain.kill_points`; the tests that use it to prove recovery come with the recovery features (F0008, F0011).

There are four points, the members of `KillPoint`:

| Point | Value | Reached by |
|---|---|---|
| `AGENT_RUN` | `agent-run` | the two agent runtimes, while an agent runs |
| `BEFORE_PUSH` | `before-push` | the git wrapper, before a push |
| `AFTER_PUSH` | `after-push` | the git wrapper, after a push |
| `AFTER_POST` | `after-post` | the fake hosting service and the PyGithub client, after posting |

This story built only the seam. A wrapper calls `kill_points.reach(point)` at its point in its own story; until then nothing reaches a point.

A new `KillPoints` is inert. In a test, use the `kill_points` fixture from `tests/conftest.py`, which returns a new `KillPoints()` for each test, and hand it to the wrapper under test:

```python
def test_push_dies_after_the_second_try(kill_points: KillPoints) -> None:
    kill_points.arm(KillPoint.BEFORE_PUSH, after=1)
    with pytest.raises(InjectedKill):
        ...  # code that reaches BEFORE_PUSH twice
    assert kill_points.reached(KillPoint.BEFORE_PUSH) == 2
```

- `arm(point)` makes the next `reach(point)` raise `InjectedKill`. `arm(point, after=n)` lets `n` reaches pass first and raises on the next; `after` counts from the arming. A negative `after` raises `ValueError` and changes nothing.
- A point fires once and is then inert again. Arming an armed point replaces the earlier arming. Arming one point never changes another, armed or not.
- `reached(point)` counts every reach, the one that raises included, armed or not.
- Each `KillPoints` instance has its own state.
- `str(InjectedKill(point))` is `injected kill at <point value>`, and `.point` is the point that fired.

`InjectedKill` is a `BaseException`; see `docs/decisions.md`.
