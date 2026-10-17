# The factory alone writes the checkout's git folder

## Assignment (as of log entry 1)

The agent can write the shared checkout's git folder. While F0014 was drafted (2026-10-17, `planning/overnight/first-start-checklist.md`, "Results", fault 5), a `core.fsmonitor` line written into `/work/checkout/.git/config` as `agent` made the factory's own `git status` run a command as `factory`, the user who can read the hosting token. The folder is `drwxrwsr-x` and its files `-rw-rw-r--`, because the factory's git runs with `core.sharedRepository=group` (`git_environment` in `src/factory/entry/wiring.py`) under the entrypoint's `umask 002`. S0001's `core.hooksPath` does not cover this: git also runs commands named in the configuration (`core.fsmonitor`, a filter or diff driver, `core.sshCommand`) and in `.git/info/attributes`. The human's word (2026-10-17): the factory alone writes the checkout's `.git`. The agent user can read it but cannot create, change, rename or remove anything in it, so no repository configuration, hook or attribute file an agent writes there can make the factory's git run a command. The work tree stays group-writable for the agent, as today.

Nothing an agent does needs to write `.git`. Agents never commit. The shipped `claude/settings.json` allows only `git status`, `git diff`, `git log`, `git show` and `git rev-parse` and denies `git add`, `git commit`, `git checkout`, `git switch`, `git reset` and the rest. The guard (`src/factory/adapters/claude_guard.py`) judges file paths, not git. A `git status` that cannot write the index skips the write and still prints the status.

How (FEATURE decisions 20 and 21):

- **What git writes.** `core.sharedRepository` becomes `0640`, git's documented setting for a repository the group can read but not write. The mode overrides the umask for what git creates in `.git`; directories get the group's execute bit, so they are `750` (`2750` under the setgid `/work`). Git writes the work tree under the umask alone, so the files and folders it checks out stay group-writable, as the entrypoint's `umask 002` makes them today. `group` never served the work tree.
- **The seal.** Git leaves some files outside that setting (to this session's reading, `FETCH_HEAD` and `COMMIT_EDITMSG` are written under the umask), so the factory makes sure itself. A new `Git.seal()` takes the group's and others' write permission from `.git` and from every entry in it. A new `Git.check_seal()` refuses a `.git` that is not a directory of the factory's own user, closed to the group's and others' writes.
- **The swap.** The agent can still rename `.git` itself, because the work tree's root is group-writable, and put a folder of its own, or one of the factory's group-writable work-tree folders, in its place. The agent cannot take the group's write bit from a folder of the factory's, so such a `.git` fails `check_seal()`. That is why a `.git` that is not closed is refused, never repaired, wherever an agent may have run since the last check.
- **Where the seal runs.** It runs in three places:
  - At the start of every iteration: `CheckoutPreparer.prepare` checks an existing checkout and then seals it. A checkout that fails the check is removed and cloned again; this also repairs every instance cloned before this story, whose `.git` is group-writable.
  - Around every agent run: a new `run_sealed` seals before the run and checks after it. `StageLauncher.launch` and the preflight's probe use it.
  - In the dispatcher: `RepositoryUnsealed` passes through uncounted, so no later handler of the tick runs git in that checkout. The scheduler logs the failed iteration, and the next iteration clones afresh.

S0001's hooks fix stays as defence in depth.

The tests use real repositories, and git's own modes under the entrypoint's umask `002`. `make test` has no second user (no root, no `sudo`, and a skipped test is counted), so a mode bit stands in for what the agent could write, and a changed effective user id stands in for a folder of another user (FEATURE decision 22). The real check as `agent` is plan step 4's, with the command in the docs criterion. Four tests of earlier stories change by the human's leave (FEATURE decision 23). Built right after S0001, which it extends.

## Interface

`src/factory/entry/wiring.py`: `git_environment(helper: str = CREDENTIAL_HELPER) -> dict[str, str]`, signature unchanged. It returns the seven entries of S0001's table with one change: `GIT_CONFIG_VALUE_1` is `0640` (was `group`). Its comment says why: git creates what it writes in `.git` readable and not writable by the group, so the agent's git can read the repository and cannot change it. The work tree is not touched by this setting and stays group-writable through the umask.

`src/factory/domain/errors.py`: `class RepositoryUnsealed(GitError)`, "The checkout's git folder is not the factory's alone." Its constructor is `__init__(self, detail: str)`. It calls `GitError.__init__("seal", None, detail)`, so its message is `seal failed (no exit status): <detail>`.

`src/factory/application/git.py`, the `Git` interface, gains three abstract operations (twenty-two in all):

- `seal() -> None`: take the group's and others' write permission from the repository folder and from every entry in it. Raises `RepositoryUnsealed` when the folder is missing, is a symbolic link or is not a directory, or when it or an entry in it belongs to another user.
- `check_seal() -> None`: raise `RepositoryUnsealed` unless the repository folder is a directory, not a symbolic link, that belongs to the factory's own user and that neither its group nor others may write. Changes nothing.
- `discard() -> None`: remove the working copy and its repository entirely. A missing working copy is no error; any other failure is a `GitError`.

`src/factory/adapters/git_cli.py`, `GitCli` (the repository folder is `<directory>/.git`), with no git process for any of the three:

- `seal()`:
  - Checks the folder with `os.lstat` and reads the effective user with `os.geteuid()` at each call.
  - Then walks the folder without following symbolic links and, for the folder and every entry whose mode has `0o022`, sets the mode to `stat.S_IMODE(mode) & ~0o022`. That keeps the setgid bit and the read and execute bits.
  - Leaves a symbolic link inside the folder alone, not following it, and does not check its owner.
  - Refuses an entry of another user before changing anything further.
  - An entry it cannot read or change raises `RepositoryUnsealed` naming it.
- `check_seal()`: one `os.lstat` of the folder.
- `discard()`: `shutil.rmtree` of the working copy; an `OSError` other than a missing directory becomes `GitError("discard", None, <error>)`.
- The details, each naming the path:
  - `<folder> does not exist`
  - `<folder> is a symbolic link`
  - `<folder> is not a directory`
  - `<path> belongs to the user <uid>, not to <effective uid>`
  - `<folder> is writable by its group or by others` (`check_seal()` only)
  - `<path>: <error>`

`src/factory/application/scheduler.py`: `CheckoutPreparer.__init__(self, git, settings, log: FactoryLog | None = None)`. `prepare()` still returns `True` and raises `GitError` as before:

- When `checkout/.git` does not exist in any form (`os.path.lexists`), it clones, as now, and then calls `seal()`.
- When it exists, it calls `check_seal()`. On `RepositoryUnsealed` it writes the log line `cloning the checkout again: <error>` (when a log is given), calls `discard()` and `clone(url)`. It then calls `seal()`.
- A folder with files and no `.git` is still refused by the clone, unchanged.

`src/factory/entry/run.py`: `CheckoutPreparer(boundaries.git, settings, log=boundaries.log)`.

A new module `src/factory/application/sealed_runs.py`: `run_sealed(boundaries: Boundaries, request: AgentRunRequest) -> AgentRunResult`. It calls `boundaries.git.seal()`, then `boundaries.agent_runtime.run(request)`, and in a `finally` `boundaries.git.check_seal()`. So a `RepositoryUnsealed` after the run wins over an error of the run, which becomes its context. `StageLauncher.launch` (`src/factory/application/stage.py`) and `agent_run_probe_item` (`src/factory/application/preflight.py`) call `run_sealed` in place of `agent_runtime.run`. The probe still catches only `AgentDefinitionError` and `AgentRuntimeError`, so a `RepositoryUnsealed` leaves the item as an exception. `launch`'s docstring adds `RepositoryUnsealed` to what propagates.

`src/factory/application/dispatcher.py`: `Dispatcher.dispatch` re-raises `RepositoryUnsealed` from a handler before its `except Exception`, without counting an error. Every other handler error is counted as now.

Tests:

- New modules:
  - `tests/entry/test_git_repository_modes.py`: `GitCli` with `git_environment()` on the `remote` fixture, under umask `0o002`. A fixture sets the umask and restores the previous one, as `tests/adapters/test_claude_runtime_file_modes.py` does.
  - `tests/adapters/test_git_cli_seal.py`: clones from `clone` of `tests/git_support.py`, with the modes set by the test.
  - `tests/application/test_checkout_preparer_seal.py`.
  - `tests/application/test_sealed_runs.py`: the runtimes that swap `.git` or record modes are implementations of `AgentRuntime` written in the test, wrapping `FakeAgentRuntime`.
- Another user is a monkeypatched `os.geteuid` that returns the real id plus one. A group-writable `.git` is a `chmod` by the test.
- By the human's leave (FEATURE decision 23), and no other change to an earlier story's test:
  - In `tests/entry/test_wiring_boundaries.py` (F0010-S0003, as F0014-S0001 leaves it): `test_git_environment_gives_the_credential_helper_the_shared_group_and_no_hooks` expects `GIT_CONFIG_VALUE_1` = `0640`, and `test_the_built_git_runs_with_the_git_options_of_the_settings` asserts `GIT_CONFIG_VALUE_1` = `0640`. Both keep their names.
  - In `tests/application/test_git_interface.py` (F0001, renamed by F0001-S0022): `OPERATIONS` gains `seal`, `check_seal` and `discard`, and the test becomes `test_git_has_exactly_the_twenty_two_operations_and_git_cli_has_each`.
  - In `tests/application/test_interfaces.py` (F0001-S0019): `test_git_abstract_methods_are_exactly_its_nineteen_operations` becomes `test_git_abstract_methods_are_exactly_its_twenty_two_operations`, its body unchanged.

## Acceptance criteria

1. `git_environment()` returns S0001's seven entries with `GIT_CONFIG_VALUE_1` = `0640`, for the default helper and for `/opt/other-helper` (the changed test of `tests/entry/test_wiring_boundaries.py`). The built boundaries' git runs with `GIT_CONFIG_VALUE_1` = `0640` (the other changed test).
2. Under umask `0o002`, after a clone by `GitCli` with `git_environment()`, the group of `.git` may read and enter it and not write it (`mode & 0o070 == 0o050`), and `.git/config` has the mode `0o640`. These are git's own modes, before any `seal()`.
3. Under umask `0o002`, after that clone, the file `PIPELINE_DEFINITION_FILE` (`factory.domain.paths`) and its folder, both checked out by git from the `remote` fixture's `main`, are writable by the group (`mode & 0o020`). The agent's work tree stays as today. Criteria 2 and 3 are rows of one parametrized test, one row per path and its expected bits.
4. After that clone, a fetch, a switch to a new branch from `origin/main`, a commit of a new file, a `reset_to("HEAD")` and then `seal()`, no entry under `.git` (`.git` included, symbolic links excepted) is writable by its group or by others. Every directory there can be read and entered by the group (`mode & 0o050 == 0o050`), and every file read by it (`mode & 0o040`).
5. `seal()` takes the group's and others' write bits and keeps every other bit, rows of one parametrized test:
   - `.git` at `0o2775` becomes `0o2755`.
   - A folder inside it at `0o777` becomes `0o755`.
   - A file inside it at `0o666` becomes `0o644`.
   - A file at `0o640` stays `0o640`.
   - A symbolic link inside `.git` to a file outside the checkout at `0o666` is left, and that file stays `0o666`.
6. `seal()` raises `RepositoryUnsealed` and changes no mode, rows of one parametrized test:
   - `.git` is missing (detail `does not exist`).
   - `.git` is a symbolic link to another clone's `.git` (`is a symbolic link`).
   - `.git` is a file (`is not a directory`).
   - `os.geteuid()` names another user (`belongs to the user`), with a file inside at `0o666` that stays `0o666`.
7. `check_seal()` passes for a `.git` at `0o2750` and at `0o750`, and raises `RepositoryUnsealed` in these cases, rows of one parametrized test:
   - `0o2770` (group write)
   - `0o757` (others' write)
   - a symbolic link
   - a file
   - a missing folder
   - another user (monkeypatched `os.geteuid`)

   No row changes a mode.
8. `discard()` removes the working copy with its `.git` and its files. A missing working copy raises nothing. A working copy holding a folder at `0o555` that holds a file raises `GitError` whose message holds `discard` (skipped for root, as `tests/application/test_tick.py` does); the test restores the mode afterwards.
9. `CheckoutPreparer.prepare` without a checkout clones and seals: under umask `0o002`, with `GitOptions()` (git's modes `0o775` for `.git`), `.git` afterwards has no group or others' write bit and `origin/main` resolves.
10. `prepare` on an existing checkout whose `.git` passes `check_seal()` keeps it: a file the test put in the work tree is still there. An entry the test made writable inside `.git` (`.git/config` at `0o664`) is `0o644` afterwards, and no line is logged.
11. `prepare` on an existing checkout whose `.git` fails `check_seal()` removes it and clones again. Afterwards a file the test put in the old work tree is gone, `origin/main` resolves, `.git` is a directory with no group or others' write bit, and the log holds exactly one line, `cloning the checkout again: ` followed by the error's message. Rows of one parametrized test:
    - `.git` at `0o2775`
    - `.git` a symbolic link to a clone elsewhere
12. `run_sealed` seals before the run: a runtime that records, during its run, the modes of `.git` (set to `0o2775` by the test) and of `.git/config` (`0o666`) sees `0o2755` and `0o644`. `run_sealed` returns the runtime's result.
13. `run_sealed` raises `RepositoryUnsealed` in these cases, rows of one parametrized test:
    - after a run that renames `.git` to `.git-moved` and puts a folder at `0o2775` in its place
    - after a run that puts a symbolic link to `.git-moved` in its place
    - when the run makes that swap and then raises `AgentRuntimeError`; the `AgentRuntimeError` is the `__context__` of the `RepositoryUnsealed`
14. `StageLauncher.launch` and `agent_run_probe_item` run the agent through `run_sealed`. With a runtime that swaps `.git` as in criterion 13, `launch` raises `RepositoryUnsealed`, and the probe item raises it instead of returning a failed item (rows of one parametrized test).
15. `Dispatcher.dispatch` lets a handler's `RepositoryUnsealed` pass and counts no error for the event, while a handler's other `GitError` is counted as before (rows of one parametrized test).
16. What must still hold: the existing tests of the preparer, the repository waiter, the scheduler, the tick, the stage, the probe, the dispatcher and the git wrapper pass. In particular, a checkout with files and no `.git` is refused unchanged (`tests/application/test_scheduler.py`), an existing clone is kept without starting git, the tick's restore removes an agent-made folder, the hooks of a bare remote still run on a push to it, and the factory's git reads no system configuration.
17. `make check` stays green.
18. docs: The operator guide:
    - *Users and directories* gets a row for `/work/checkout/.git`: `2750`, `factory:factory-work`, its files `0640`. It is git's repository of the checkout; the factory alone writes it; the agent's git reads it (`git status`, `git diff`, `git log`) and cannot create, change, rename or remove anything in it. The work tree around it stays group-writable.
    - The morning observations in *The agent runs as a second user* get this row: `docker exec -u agent <container> sh -c 'cd /work/checkout && stat -c "%a %U:%G %n" .git .git/config && find .git -perm /022 | wc -l && git config --local factory.sealcheck agent; touch .git/agent-file; mv .git/hooks .git/hooks-moved'`. Expected, line by line: `2750 factory:factory-work .git`, `640 factory:factory-work .git/config`, `0`, `error: could not lock config file .git/config: Permission denied`, `touch: cannot touch '.git/agent-file': Permission denied`, `mv: cannot move '.git/hooks' to '.git/hooks-moved': Permission denied`.
    - A paragraph says what happens to a checkout whose `.git` is not the factory's alone, as one cloned before this change or one an agent replaced: on the next iteration the factory removes the checkout and clones it again, with the line `cloning the checkout again: ...` in `/state/factory.log`. The instance's local state is lost, which the restore discards anyway. A checkout the factory cannot remove is the stop `repository_unavailable`.
    - *The hosting-service token*'s "Left for v2" paragraph no longer names the checkout's `.git` as a route: neither its configuration nor its hooks nor `.git/info/attributes`.

    The project guide:
    - `git_environment` gives `core.sharedRepository` = `0640`.
    - `Git` has twenty-two operations, with `seal`, `check_seal` and `discard` described.
    - `CheckoutPreparer.prepare`'s check, removal and new clone are described.
    - `run_sealed` and its two callers are described.
    - The dispatcher passes `RepositoryUnsealed` through.

    The decision log:
    - A new entry, "The factory alone writes the checkout's `.git`". It gives fault 5, the human's word, `0640` and why the work tree keeps its modes, why the seal and why a `.git` that is not closed is refused and not repaired, and where the seal runs. It names what was rejected: a sticky bit on the checkout's root, which would stop the agent from renaming, removing or replacing by rename any of the factory's files there, such as `uv.lock` and `.venv`; a git folder outside the work tree under `GIT_DIR`; a volume mounted at `.git`; a umask of `022` for git, which would close the work tree too; and a check before every git command.
    - The entry "Git gets its credential helper and shared group through `GitOptions.environment`" says that the shared setting is now `0640` and points to the new entry.
    - The entry "A checkout whose clone was killed half-way is not recognised" says that the factory now removes a checkout whose `.git` fails the check, and still refuses a folder without `.git`.
    - The open point of the entry "The token is a bind mount into a folder only the factory can enter" is marked closed by "The factory's git runs no hooks" and the new entry.

    No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "from factory.entry.wiring import git_environment; print(git_environment()['GIT_CONFIG_VALUE_1'])"
```
Expect: one line: `0640`.

```bash
uv run python -c "
import os, stat, subprocess, tempfile
from pathlib import Path
from factory.adapters.git_cli import GitCli
from factory.domain.git import GitOptions
from factory.entry.wiring import git_environment
os.umask(0o002)
root = Path(tempfile.mkdtemp())
source = root / 'source'
subprocess.run(['git', 'init', '-q', '-b', 'main', str(source)], check=True)
(source / 'a.txt').write_text('a\n', encoding='utf-8')
subprocess.run(['git', '-C', str(source), 'add', 'a.txt'], check=True)
subprocess.run(['git', '-C', str(source), '-c', 'user.name=demo', '-c', 'user.email=demo@example.invalid', 'commit', '-q', '-m', 'a'], check=True)
git = GitCli(root / 'checkout', GitOptions(environment=git_environment()))
git.clone(str(source))
git.fetch()
git.seal()
folder = root / 'checkout' / '.git'
print(oct(folder.stat().st_mode & 0o777), oct(stat.S_IMODE((folder / 'config').stat().st_mode)))
print(sum(1 for path in [folder, *folder.rglob('*')] if not path.is_symlink() and path.lstat().st_mode & 0o022))
print(oct(stat.S_IMODE((root / 'checkout' / 'a.txt').stat().st_mode)))
"
```
Expect: three lines: `0o750 0o640`, then `0`, then `0o664`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/entry/test_git_repository_modes.py tests/adapters/test_git_cli_seal.py tests/application/test_checkout_preparer_seal.py tests/application/test_sealed_runs.py tests/entry/test_wiring_boundaries.py tests/application/test_git_interface.py tests/application/test_interfaces.py tests/application/test_scheduler.py tests/application/test_repository_waiter.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
