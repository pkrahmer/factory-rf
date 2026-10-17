---
stage: accept
pr: 192
blocked: null
comments_seen: 4
round: 0
attempts: 0
---
# The factory alone writes the checkout's git folder

## Assignment (as of log entry 1)

The agent can write the shared checkout's git folder. While F0014 was drafted (2026-10-17, `planning/overnight/first-start-checklist.md`, "Results", fault 5), a `core.fsmonitor` line written into `/work/checkout/.git/config` as `agent` made the factory's own `git status` run a command as `factory`, the user who can read the hosting token. The folder is `drwxrwsr-x` and its files `-rw-rw-r--`, because the factory's git runs with `core.sharedRepository=group` (`git_environment` in `src/factory/entry/wiring.py`) under the entrypoint's `umask 002`. S0001's `core.hooksPath` does not cover this: git also runs commands named in the configuration (`core.fsmonitor`, a filter or diff driver, `core.sshCommand`) and in `.git/info/attributes`. The human's word (2026-10-17): the factory alone writes the checkout's `.git`. The agent user can read it but cannot create, change, rename or remove anything in it, so no repository configuration, hook or attribute file an agent writes there can make the factory's git run a command. The work tree stays group-writable for the agent, as today.

Nothing an agent does needs to write `.git`. Agents never commit. The shipped `claude/settings.json` allows only `git status`, `git diff`, `git log`, `git show` and `git rev-parse` and denies `git add`, `git commit`, `git checkout`, `git switch`, `git reset` and the rest. The guard (`src/factory/adapters/claude_guard.py`) judges file paths, not git. A `git status` that cannot write the index skips the write and still prints the status.

How (FEATURE decisions 20 and 21):

- **What git writes.** `core.sharedRepository` becomes `0640`, git's documented setting for a repository the group can read but not write. The mode overrides the umask for what git creates in `.git`; directories get the group's execute bit, so they are `750` (`2750` under the setgid `/work`). Git writes the work tree under the umask alone, so the files and folders it checks out stay group-writable, as the entrypoint's `umask 002` makes them today. `group` never served the work tree.
- **The seal.** Git leaves some files outside that setting (`FETCH_HEAD` and `COMMIT_EDITMSG`, and during a conflict `MERGE_MSG`, `MERGE_HEAD`, `MERGE_MODE` and `AUTO_MERGE`, are written under the umask; checked with git 2.39.5 at the pre-check), so the factory makes sure itself. A new `Git.seal()` takes the group's and others' write permission from `.git` and from every entry in it. A new `Git.check_seal()` refuses a `.git` that is not a directory of the factory's own user, closed to the group's and others' writes, holding a `HEAD` file.
- **The swap.** The agent can still rename `.git` itself, because the work tree's root is group-writable, and put a folder of its own, or one of the factory's group-writable work-tree folders, in its place. The agent cannot take the group's write bit from a folder of the factory's, so such a `.git` fails `check_seal()`. That is why a `.git` that is not closed is refused, never repaired, wherever an agent may have run since the last check.
- **No repository above.** A folder of the factory's that the group cannot write, renamed into `.git`, would pass a check of the root alone, and git would look for a repository further up, in `/work`, where the agent can place one. So `check_seal()` also wants a `HEAD` file in `.git`, and the factory's git runs with `GIT_CEILING_DIRECTORIES` at the checkout's parent and never looks above the checkout.
- **Where the seal runs.** At the start of every iteration: `CheckoutPreparer.prepare` checks an existing checkout and then seals it. A checkout that fails the check is removed and cloned again; this also repairs every instance cloned before this story, whose `.git` is group-writable. F0014-S0009, built right after it, seals around every agent run and lets the dispatcher pass `RepositoryUnsealed`; until it is merged the seal holds at the start of each iteration only.

S0001's hooks fix stays as defence in depth.

The tests use real repositories, and git's own modes under the entrypoint's umask `002`. `make test` has no second user (no root, no `sudo`, and a skipped test is counted), so a mode bit stands in for what the agent could write, and a changed effective user id stands in for a folder of another user (FEATURE decision 22). The real check as `agent` is plan step 4's, with the command in the docs criterion. Four tests of earlier stories change by the human's leave (FEATURE decision 23). Built right after S0001, which it extends.

## Interface

`src/factory/entry/wiring.py`: `git_environment(helper: str = CREDENTIAL_HELPER) -> dict[str, str]`, signature unchanged. It returns the seven entries of S0001's table with one change: `GIT_CONFIG_VALUE_1` is `0640` (was `group`). Its comment says why: git creates what it writes in `.git` readable and not writable by the group, so the agent's git can read the repository and cannot change it. The work tree is not touched by this setting and stays group-writable through the umask.

`src/factory/domain/errors.py`: `class RepositoryUnsealed(GitError)`, "The checkout's git folder is not the factory's alone." Its constructor is `__init__(self, detail: str)`. It calls `GitError.__init__("seal", None, detail)`, so its message is `seal failed (no exit status): <detail>`.

`src/factory/application/git.py`, the `Git` interface, gains three abstract operations (twenty-two in all):

- `seal() -> None`: take the group's and others' write permission from the repository folder and from every entry in it. Raises `RepositoryUnsealed` when the folder is missing, is a symbolic link, is not a directory or holds no regular file `HEAD`, when it belongs to another user, or when an entry cannot be read or changed.
- `check_seal() -> None`: raise `RepositoryUnsealed` unless the repository folder is a directory, not a symbolic link, that belongs to the factory's own user, that neither its group nor others may write, and that holds a regular file `HEAD`. Changes nothing.
- `discard() -> None`: remove the working copy and its repository entirely. A missing working copy is no error; any other failure is a `GitError`.

`src/factory/adapters/git_cli.py`, `GitCli` (the repository folder is `<directory>/.git`), with no git process for any of the three:

- `seal()`:
  - Checks the folder and its `HEAD` with `os.lstat`, and reads the effective user with `os.geteuid()` at each call. The folder's own owner is checked before anything is changed.
  - Then walks the folder without following symbolic links and, for the folder and every entry whose mode has `0o022`, sets the mode to `stat.S_IMODE(mode) & ~0o022`. That keeps the setgid bit and the read and execute bits.
  - Leaves a symbolic link inside the folder alone, not following it, and does not check its owner.
  - A folder it cannot list or an entry it cannot change raises `RepositoryUnsealed` naming it (the walk's `onerror` raises; `os.walk` would skip it otherwise).
- `check_seal()`: `os.lstat` of the folder and of its `HEAD`.
- `discard()`: `shutil.rmtree` of the working copy; an `OSError` other than a missing directory becomes `GitError("discard", None, <error>)`.
- The details, each naming the path:
  - `<folder> does not exist`
  - `<folder> is a symbolic link`
  - `<folder> is not a directory`
  - `<folder> holds no HEAD file`
  - `<folder> belongs to the user <uid>, not to <effective uid>`
  - `<folder> is writable by its group or by others` (`check_seal()` only)
  - `<path>: <error>`
- Every git command `GitCli` runs gets `GIT_CEILING_DIRECTORIES` = the working copy's parent, set beside `GIT_CONFIG_NOSYSTEM` among the entries no `GitOptions.environment` can lift. So git never looks for a repository above the working copy: a `.git` that is not a repository is an error, never a way to a repository an agent placed in the checkout's parent. Its comment says why.

`src/factory/application/scheduler.py`: `CheckoutPreparer.__init__(self, git, settings, log: FactoryLog | None = None)`. `prepare()` still returns `True` and raises `GitError` as before:

- When `checkout/.git` does not exist in any form (`os.path.lexists`), it clones, as now, and then calls `seal()`.
- When it exists, it calls `check_seal()`. On `RepositoryUnsealed` it writes the log line `cloning the checkout again: <error>` (when a log is given), calls `discard()` and `clone(url)`. It then calls `seal()`.
- A folder with files and no `.git` is still refused by the clone, unchanged.

`src/factory/entry/run.py`: `CheckoutPreparer(boundaries.git, settings, log=boundaries.log)`.

Tests:

- New modules:
  - `tests/entry/test_git_repository_modes.py`: `GitCli` with `git_environment()` on the `remote` fixture, under umask `0o002`. A fixture sets the umask and restores the previous one, as `tests/adapters/test_claude_runtime_file_modes.py` does.
  - `tests/adapters/test_git_cli_seal.py`: clones from `clone` of `tests/git_support.py`, with the modes set by the test.
  - `tests/application/test_checkout_preparer_seal.py`, with the preparer's and the repository waiter's criteria.
- Another user is a monkeypatched `os.geteuid` that returns the real id plus one. A group-writable `.git` is a `Path.chmod` by the test (ruff's `S103` flags `os.chmod` with such a mode, not `Path.chmod`).
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
6. `seal()` raises `RepositoryUnsealed`, and no row changes a mode. Rows of one parametrized test, each naming its detail:
   - `.git` is missing: `does not exist`.
   - `.git` is a symbolic link to another clone's `.git`: `is a symbolic link`.
   - `.git` is a file: `is not a directory`.
   - `os.geteuid()` names another user: `belongs to the user`, with a file inside at `0o666` that stays `0o666`.

   A second test: a folder inside `.git` at `0o300` (it cannot be listed) makes `seal()` raise `RepositoryUnsealed` whose message holds that folder's path. It is skipped for root, as `tests/application/test_tick.py` does, and the test restores the mode afterwards.
7. `check_seal()` passes for a `.git` at `0o2750` and at `0o750`, and raises `RepositoryUnsealed` in these cases, rows of one parametrized test, each naming its detail:
   - `0o2770`: `is writable by its group or by others`; for this row `str(error)` is exactly `seal failed (no exit status): <folder> is writable by its group or by others`.
   - `0o757`: `is writable by its group or by others`.
   - a symbolic link: `is a symbolic link`.
   - a file: `is not a directory`.
   - a missing folder: `does not exist`.
   - another user (monkeypatched `os.geteuid`): `belongs to the user`.

   No row changes a mode.
8. A `.git` that is an empty directory of the factory's user at `0o755` fails `check_seal()` and `seal()` with the detail `holds no HEAD file`, and changes no mode. With such a `.git` in the working copy and a repository whose `main` holds a commit at the working copy's parent's `.git` (made by the test), `GitCli.status()` raises `GitError` and `resolve("HEAD")` does not return that repository's commit.
9. `discard()` removes the working copy with its `.git` and its files. A missing working copy raises nothing. A working copy holding a folder at `0o555` that holds a file raises `GitError` whose message holds `discard` (skipped for root, as `tests/application/test_tick.py` does); the test restores the mode afterwards.
10. `CheckoutPreparer.prepare` without a checkout clones and seals: under umask `0o002`, with `GitOptions()` (git's modes `0o775` for `.git`), `.git` afterwards has no group or others' write bit and `origin/main` resolves.
11. `prepare` on an existing checkout whose `.git` passes `check_seal()` keeps it: a file the test put in the work tree is still there. An entry the test made writable inside `.git` (`.git/config` at `0o664`) is `0o644` afterwards, and no line is logged.
12. `prepare` on an existing checkout whose `.git` fails `check_seal()` removes it and clones again. Afterwards a file the test put in the old work tree is gone, `origin/main` resolves, `.git` is a directory with no group or others' write bit, and the log, where one is given, holds exactly one line, `cloning the checkout again: ` followed by the error's message. Rows of one parametrized test:
    - `.git` at `0o2775`
    - `.git` a symbolic link to a clone elsewhere
    - `.git` at `0o2775`, with the preparer built without a log: the same new clone, and no error
13. `RepositoryWaiter.prepare` over a checkout whose `.git` fails `check_seal()` and whose work tree holds a folder at `0o555` that holds a file returns `False` and raises the stop `repository_unavailable` whose detail starts with `cannot prepare the checkout: discard failed`. Skipped for root, as `tests/application/test_tick.py` does; the test restores the mode afterwards.
14. What must still hold: the existing tests of the preparer, the repository waiter, the scheduler, the tick and the git wrapper pass. In particular, a checkout with files and no `.git` is refused unchanged (`tests/application/test_scheduler.py`), an existing clone is kept without starting git, the tick's restore removes an agent-made folder, the hooks of a bare remote still run on a push to it, and the factory's git reads no system configuration.
15. `GitCli` built with `GitOptions(environment={"GIT_CEILING_DIRECTORIES": <other folder>})` still refuses the repository at the working copy's parent's `.git`, as in criterion 8: `status()` raises `GitError` and `resolve("HEAD")` does not return that repository's commit. Rows of one parametrized test: the entry set to the working copy's parent's parent, and set to the empty string.
16. `make check` stays green.
17. docs: The operator guide:
    - *Users and directories* gets a row for `/work/checkout/.git`: `2750`, `factory:factory-work`, its files `0640`. It is git's repository of the checkout; the factory alone writes it; the agent's git reads it (`git status`, `git diff`, `git log`) and cannot create, change, rename or remove anything in it. The work tree around it stays group-writable.
    - The morning observations in *The agent runs as a second user* get this row, made once F0014-S0002 is in the image (without its `safe.directory` the agent's git refuses the checkout before it tries to write) and after the instance's second iteration (right after a new clone, `FETCH_HEAD` stays group-writable until the next iteration seals it): `docker exec -u agent <container> sh -c 'cd /work/checkout && stat -c "%a %U:%G %n" .git .git/config && find .git -perm /022 | wc -l && git config --local factory.sealcheck agent; touch .git/agent-file; mv .git/hooks .git/hooks-moved'`. Expected, line by line: `2750 factory:factory-work .git`, `640 factory:factory-work .git/config`, `0`, `error: could not lock config file .git/config: Permission denied`, `touch: cannot touch '.git/agent-file': Permission denied`, `mv: cannot move '.git/hooks' to '.git/hooks-moved': Permission denied`.
    - The section *The checkout is recloned only when it is missing* becomes *The checkout is cloned again when it is missing or its `.git` is not the factory's alone*. It says that a missing checkout is cloned. A checkout whose `.git` is not the factory's alone (one cloned before this change, one an agent replaced, or one without `HEAD`) is removed on the next iteration and cloned again, with the line `cloning the checkout again: ...` in `/state/factory.log`. The instance's local state is lost, which the restore discards anyway. A folder with files and no `.git` is still refused. A checkout the factory cannot remove is the stop `repository_unavailable`. The cross-reference in *The low disk* takes the new title.
    - *The hosting-service token*'s "Left for v2" paragraph no longer names the checkout's `.git` as a route: neither its configuration nor its hooks nor `.git/info/attributes`.

    The project guide:
    - `git_environment` gives `core.sharedRepository` = `0640`.
    - `Git` has twenty-two operations, with `seal`, `check_seal` and `discard` described, the `HEAD` check among them; `GitCli` sets `GIT_CEILING_DIRECTORIES`.
    - `CheckoutPreparer.prepare`'s check, removal and new clone are described.

    The decision log:
    - A new entry, "The factory alone writes the checkout's `.git`". It gives fault 5, the human's word, `0640` and why the work tree keeps its modes, why the seal and why a `.git` that is not closed is refused and not repaired, why the `HEAD` check and the ceiling, and where the seal runs (at the start of every iteration; S0009 adds every agent run). It names what was rejected: a sticky bit on the checkout's root, which would stop the agent from renaming, removing or replacing by rename any of the factory's files there, such as `uv.lock` and `.venv`; a git folder outside the work tree under `GIT_DIR`; a volume mounted at `.git`; a umask of `022` for git, which would close the work tree too; and a check before every git command.
    - The entry "Git gets its credential helper and shared group through `GitOptions.environment`" says that the shared setting is now `0640` and points to the new entry.
    - The entry "A checkout whose clone was killed half-way is not recognised" says that the factory now removes a checkout whose `.git` fails the check, and still refuses a folder without `.git`.
    - The open point of the entry "The token is a bind mount into a folder only the factory can enter" is marked closed by "The factory's git runs no hooks" and the new entry.

    No other document changes; the decision-log entry names as left for v2 the clone's working folder (the checkout's parent) and the process environment that `GitCli` passes on first. `python -m factory.entry.check_documents` still prints `documents ok`.

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
uv run pytest --no-header -p no:cacheprovider tests/entry/test_git_repository_modes.py tests/adapters/test_git_cli_seal.py tests/application/test_checkout_preparer_seal.py tests/entry/test_wiring_boundaries.py tests/application/test_git_interface.py tests/application/test_interfaces.py tests/application/test_scheduler.py tests/application/test_repository_waiter.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: Two rules in `## Interface` have no criterion that tests them. The format check passed. The Interface, the Demo, the architecture and the scope are otherwise fine.

   1. The Interface says `GIT_CEILING_DIRECTORIES` is set "among the entries no `GitOptions.environment` can lift". Criterion 8 only tests that git refuses to look above a broken `.git`. Nothing tests that a `GitOptions.environment` entry named `GIT_CEILING_DIRECTORIES`, or one set to another folder, is overridden by the wrapper. That is the refused side of the rule, and without a test a later story will drop it unnoticed.
      - Options: (a) add a criterion: `GitCli` built with `GitOptions(environment={"GIT_CEILING_DIRECTORIES": <other>})` still refuses the repository at the working copy's parent's `.git`, as in criterion 8. (b) Drop "no ... can lift" from the Interface.
      - I would choose (a).

   2. `seal()` "refuses an entry of another user when it reaches it" with the detail `<path> belongs to the user <uid>, not to <effective uid>`. Criterion 6's monkeypatched `os.geteuid` row only tests the folder's own owner, because the owner check comes first. No criterion covers the owner check on an entry inside `.git`. A single user cannot own an entry that differs from the folder, so the monkeypatch cannot tell the two checks apart.
      - Options: (a) drop the entry-owner rule from the Interface, because the folder's owner and the "cannot change" rule cover it. (b) Keep the rule and name how one test reaches it. For example the test could monkeypatch `os.lstat` for one entry, but that fakes a system call inside the code under test, which `CLAUDE.md` forbids ("Never mock the code under test"). (c) Accept it as untested, stated in the ticket.
      - I would choose (a).

   Neither answer changes the Assignment. Under (a) for question 1, the new criterion goes before the two closing ones.
3. human (pull request comment, 2026-10-17): 1: (a), add the criterion before the two closing ones. 2: (a), drop the entry-owner rule from the Interface; the folder's owner and the "cannot change" rule cover it.
4. intake: accepted. The human's answers (log entry 3) are carried into the story. The Assignment's meaning is unchanged, so it stays as of log entry 1.
   - From answer 1 (a): new criterion 15 before the two closing ones. A `GitCli` built with a `GIT_CEILING_DIRECTORIES` entry in `GitOptions.environment` still refuses the repository at the working copy's parent's `.git`. Rows: the entry set to the parent's parent, and the empty string. `make check` is now 16 and docs 17.
   - From answer 2 (a): the entry-owner rule is dropped from the Interface. The `seal()` raises-list names only the folder's owner. The walk bullet "Refuses an entry of another user" is removed. The detail `<folder> belongs to the user <uid>, not to <effective uid>` now names the folder. The "cannot change" rule still covers an entry.
   - Interface: concrete modules and signatures are named for wiring, errors, `Git`, `GitCli`, `CheckoutPreparer` and run.py. The detail strings are exact.
   - Criteria: each is testable by one parametrized test. Each rule has its failing side: seal and check_seal refusals in 6 to 8, the unremovable discard in 9, a failing check in 12 and 13, and the ceiling override in 15.
   - Demo: the commands are runnable. Each Expect line is checkable.
   - Architecture: the changes sit in the right layers: the error in the domain, the interface and preparer in the application, `GitCli` in the adapters, the wiring in the entry layer.
   - Scope: the story is within F0014's S0006 scope. Nothing in "Out of scope" is touched.
5. tester: I wrote red tests for criteria 1 to 15 and made the four earlier-test changes the human allowed (FEATURE decision 23). Nothing else in an earlier story's tests changed. `make lint` is green. One `make test` run gave the expected red: the three changed tests in `tests/entry/test_wiring_boundaries.py` fail on `"group" != "0640"`, and `tests/adapters/test_git_cli_seal.py` does not collect, because `RepositoryUnsealed` is not in `factory.domain.errors` yet. The new modes and preparer tests fail on code that does not exist yet: `seal`, `check_seal`, `discard`, the `log=` keyword of `CheckoutPreparer`, `0640` and `GIT_CEILING_DIRECTORIES`.

   - criterion 1: tests/entry/test_wiring_boundaries.py::test_git_environment_gives_the_credential_helper_the_shared_group_and_no_hooks and ::test_the_built_git_runs_with_the_git_options_of_the_settings. Each now expects `GIT_CONFIG_VALUE_1` = `0640`; their names are unchanged.
   - criteria 2 and 3: tests/entry/test_git_repository_modes.py::test_a_clone_closes_the_git_folder_to_the_group_and_leaves_the_work_tree_writable. One row each for `.git`, `.git/config`, `PIPELINE_DEFINITION_FILE` and that file's folder.
   - criterion 4: tests/entry/test_git_repository_modes.py::test_after_git_work_and_a_seal_nothing_in_the_git_folder_is_writable_but_by_its_owner
   - criterion 5: tests/adapters/test_git_cli_seal.py::test_seal_takes_the_group_and_others_write_bits_and_keeps_every_other_bit. Five rows; the last is a symbolic link to `tmp_path/outside.txt`.
   - criterion 6: tests/adapters/test_git_cli_seal.py::test_seal_refuses_a_git_folder_that_is_not_the_factorys_and_changes_nothing (four rows) and ::test_seal_refuses_a_folder_inside_that_it_cannot_list_and_names_it (skipped for root).
   - criterion 7: tests/adapters/test_git_cli_seal.py::test_check_seal_passes_only_a_closed_git_folder_of_the_factorys_user_and_changes_nothing (eight rows, two of them passing) and ::test_check_seal_names_a_group_writable_folder_in_its_message, which checks the exact `str(error)` for `0o2770`.
   - criterion 8: tests/adapters/test_git_cli_seal.py::test_a_git_folder_without_head_is_refused_and_changes_nothing (one row each for `seal` and `check_seal`) and the `no-entry` row of ::test_git_never_reaches_a_repository_above_a_working_copy_whose_git_folder_is_broken.
   - criterion 9: tests/adapters/test_git_cli_seal.py::test_discard_removes_the_working_copy_and_a_missing_one_is_no_error and ::test_discard_that_cannot_remove_a_file_is_a_git_error (skipped for root).
   - criterion 10: tests/application/test_checkout_preparer_seal.py::test_a_missing_checkout_is_cloned_and_sealed
   - criterion 11: tests/application/test_checkout_preparer_seal.py::test_a_sealed_checkout_is_kept_and_sealed_again_without_a_log_line
   - criterion 12: tests/application/test_checkout_preparer_seal.py::test_a_checkout_whose_git_folder_fails_the_check_is_removed_and_cloned_again (three rows)
   - criterion 13: tests/application/test_checkout_preparer_seal.py::test_a_checkout_that_cannot_be_discarded_is_the_repository_unavailable_stop (skipped for root)
   - criterion 14: no new test. The existing preparer, repository-waiter, scheduler, tick and git-wrapper tests cover it.
   - criterion 15: the `parent-of-parent` and `empty` rows of tests/adapters/test_git_cli_seal.py::test_git_never_reaches_a_repository_above_a_working_copy_whose_git_folder_is_broken
   - Interface count: in tests/application/test_git_interface.py, `OPERATIONS` gains `seal`, `check_seal` and `discard`, and the test is renamed `test_git_has_exactly_the_twenty_two_operations_and_git_cli_has_each`. In tests/application/test_interfaces.py the test is renamed `test_git_abstract_methods_are_exactly_its_twenty_two_operations`; its body is unchanged.

   Files created: tests/entry/test_git_repository_modes.py, tests/adapters/test_git_cli_seal.py, tests/application/test_checkout_preparer_seal.py. Files changed: tests/conftest.py, which gains the fixture `group_umask` (umask `0o002`, the previous one restored), used by the modes tests and criterion 10; and the three earlier test files named above.

   Module the test runner could not import: `RepositoryUnsealed` from `factory.domain.errors`, which stops tests/adapters/test_git_cli_seal.py from collecting.

   Notes for the coder:
   - `resolve("HEAD")` above a broken `.git` may return `None` or raise `GitError`. The tests accept either; they only require that it does not return the commit of the repository above.
   - The "another user" rows set `.git` to `0o755` first, so the owner detail is the one that fires.
   - This shell's umask is `0022`, so clones made by the existing tests' fixtures get a `.git` at `0o755`, which passes `check_seal()`. Those tests should keep their checkouts once the preparer checks the seal.

   Open: nothing.

   `make lint`: lint: green (0.0 s)
   `make test`: ERROR tests/adapters/test_git_cli_seal.py - ImportError while importing test ...
6. coder: The code is built and committed (cacf17ea feat, 085a3783 refactor). Every check passes except two rows of one test, and the fault is in the test's fixture order, not in the code. I need the human's word before the tester changes that test.

   **The contradiction.** Two rows of tests/entry/test_git_repository_modes.py::test_a_clone_closes_the_git_folder_to_the_group_and_leaves_the_work_tree_writable fail: `work-tree-file` and `work-tree-folder` (criterion 3). The test asks for the clone through `@pytest.mark.usefixtures("cloned")` on the function, and for the umask through the module's `pytestmark = pytest.mark.usefixtures("group_umask")`. pytest applies the function's marks first, so `cloned` runs before `group_umask` (`pytest --setup-show` shows `SETUP F cloned` before `SETUP F group_umask`). The clone therefore runs under the shell's umask `0022`, and git checks the work tree out at `0644`, which is correct. The `.git` rows pass anyway, because `core.sharedRepository=0640` sets those modes whatever the umask.

   **The code is right on criterion 3.** I cloned through `GitCli` with `git_environment()` under umask `0o002`: `.git` is `0o2750`, `.git/config` is `0o640`, and the work-tree file and folder are `0o664` and `0o775`. That is exactly what the criterion wants. No change to the code can make the rows pass without the code forcing a umask on the work tree, which the story rules out.

   **Options:**
   - (a) The `cloned` fixture takes `group_umask` as a parameter: `def cloned(tmp_path: Path, remote: Path, group_umask: None) -> GitCli:`. It then always runs under `0002`, and the module's `pytestmark` can stay.
   - (b) Request `group_umask` before `cloned` in the function's own mark: `@pytest.mark.usefixtures("group_umask", "cloned")`.

   I would choose (a): the fixture states its own precondition. After the answer I end with `tests`, naming that change.

   **What is built:**
   - `RepositoryUnsealed(GitError)` in src/factory/domain/errors.py.
   - `seal`, `check_seal` and `discard` on the `Git` interface (src/factory/application/git.py).
   - In `GitCli` (src/factory/adapters/git_cli.py):
     - the three operations, with no git process;
     - one `_check_git_folder` shared by `seal` and `check_seal`: it checks that the folder exists, is not a symbolic link, is a directory, belongs to the effective user and holds a regular `HEAD` file;
     - `seal` closes `.git`, then walks it with an `onerror` that raises, leaving symbolic links alone;
     - `GIT_CEILING_DIRECTORIES` set to the working copy's absolute parent, among the entries no option can lift.
   - `CheckoutPreparer` takes an optional `log`. With `os.path.lexists` it either clones, or checks the seal and, on `RepositoryUnsealed`, logs, discards and clones again. Then it always seals.
   - run.py passes `boundaries.log` to the preparer, and wiring.py sets the shared mode to `0640`, with its comment rewritten.

   **Design decision:** a `.git` that fails the check is never repaired in place, only discarded and cloned again (the story's reason: an agent cannot close a folder of the factory's). I rejected checking `HEAD` before the owner in a separate helper per operation, because one shared check keeps `seal` and `check_seal` refusing the same set of cases.

   **Refactor:** the folder's `lstat` is read once, and `.git` is closed before the walk instead of inside it.

   **Open:** criterion 3's two rows, above. Not touched: nothing else noticed.
7. human (pull request comment, 2026-10-17): (a): `cloned` takes `group_umask` as a parameter, so it always runs under `0002`; the module's `pytestmark` stays. The criterion is unchanged.
8. coder: The human's answer (log entry 7, option (a)) needs a change to a test, so I am handing the story back to the tester. I did not touch the test and did not change any code.

   The change: in `tests/entry/test_git_repository_modes.py`, the `cloned` fixture (line 19) takes `group_umask` as a parameter, so its signature becomes `def cloned(tmp_path: Path, remote: Path, group_umask: None) -> GitCli:`. The clone then always runs under umask `0002`. The module's `pytestmark = pytest.mark.usefixtures("group_umask")` stays, and nothing else in the test changes.

   This fixes the order problem behind criterion 3. Today `cloned` runs before `group_umask`, so the clone runs under the shell's umask `0022`. That is why the `work-tree-file` and `work-tree-folder` rows of `test_a_clone_closes_the_git_folder_to_the_group_and_leaves_the_work_tree_writable` fail. With the change, they should pass against the code already committed (cacf17ea feat, 085a3783 refactor). I checked those modes by hand in my last entry: `0o664` for the file and `0o775` for the folder.

   Open: once the tester has made the change, the story comes back to doing to confirm that `make check` is green. Every other check was green after my last entry; only these two rows failed.
9. tester: I made the test change the human approved (log entry 7, option (a)), as the coder's entry 8 named it. The test change is in, and `make test` and `make lint` are both green.

   - Change: in `tests/entry/test_git_repository_modes.py`, the `cloned` fixture now takes `group_umask` as a parameter: `def cloned(tmp_path: Path, remote: Path, group_umask: None) -> GitCli:`. pytest therefore sets the umask `0002` before the clone. The module's `pytestmark = pytest.mark.usefixtures("group_umask")` stays, and the criterion is unchanged.
   - One line more than entry 8 named: ruff's ARG001 flagged the new parameter as unused, so `make lint` failed. I added `del group_umask` as the first line of the fixture body, with a comment saying the fixture is requested for its umask alone. I chose this over a `# noqa: ARG001` marker and over removing the parameter. It does not change what the test does.
   - Why: before the change, `cloned` ran before `group_umask`, so the clone ran under the shell's umask `0022`. That made the `work-tree-file` and `work-tree-folder` rows of `test_a_clone_closes_the_git_folder_to_the_group_and_leaves_the_work_tree_writable` fail.

   `make test`: test: green (29.5 s), with total coverage at 99.48 %.
   `make lint`: lint: green (0.0 s).

   Open: the coder still needs to confirm that `make check` is green; I did not run it in this stage.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (29.9 s)
10. coder: This round was a confirmation only. The code was already committed (cacf17ea feat, 085a3783 refactor). The tester has made the fixture change the human approved (log entries 7 and 9). I changed no code and no test in this run, and the working tree was clean.

    - `make check`: check: green. `make test` passes with total coverage at 99.48 %. `make duplicates`: 0 new, 39 known, 0 gone.

    What is built (details in entry 6):
    - `RepositoryUnsealed(GitError)` in `src/factory/domain/errors.py`.
    - `seal`, `check_seal` and `discard` on the `Git` interface in `src/factory/application/git.py`.
    - In `GitCli` (`src/factory/adapters/git_cli.py`):
      - The three operations, which start no git process.
      - One `_check_git_folder` that both `seal` and `check_seal` use. It checks, in order: the folder exists, is not a symbolic link, is a directory, belongs to the effective user and holds a regular `HEAD` file.
      - `seal` closes `.git` and then walks it with an `onerror` that raises. It leaves symbolic links alone.
      - `GIT_CEILING_DIRECTORIES` is set to the working copy's absolute parent, among the entries no option can lift.
    - `CheckoutPreparer` in `src/factory/application/scheduler.py` takes an optional `log`:
      - If `.git` does not exist in any form, it clones.
      - Otherwise it calls `check_seal`. On `RepositoryUnsealed` it logs, discards and clones again.
      - In both cases it then calls `seal`.
    - `src/factory/entry/run.py` passes `boundaries.log` to the preparer. `src/factory/entry/wiring.py` sets the shared mode to `0640` and its comment says why.

    Main design decision: a `.git` that fails the check is never repaired in place, only discarded and cloned again, because an agent cannot close a folder of the factory's. I rejected separate checks for each operation, because one shared check keeps `seal` and `check_seal` refusing exactly the same cases.

    Refactor: already done in 085a3783, where the folder's status is read once and `.git` is closed before the walk. Nothing more needed changing on this reading of the diff.

    Noticed, not touched: `scheduler.py` (application layer) now imports `os` for `os.path.lexists`. The layer already did file-system checks through `Path.exists`, and `lexists` is needed so that a dangling symbolic link at `.git` counts as existing.

    Open: nothing.

    `make check`: check: green
    `make duplicates`: duplicates: 0 new, 39 known, 0 gone
11. reviewer: no findings.

    I read the diff (`git diff main...HEAD -- . ':!factory'`, 13 files) against the Interface and criteria 1 to 17. I did not trust the log's own account.

    - Acceptance criteria: each of criteria 1 to 15 has a test that checks what the criterion says. Criteria 2 and 3 are rows of one parametrized test. The four rows of criterion 6 and the eight of criterion 7 compare every mode under `tmp_path` before and after the call. The exact `str(error)` is tested for `0o2770`. Criterion 8 covers both `seal` and `check_seal`, plus the repository above. The `parent-of-parent` and `empty` rows of criterion 15 would fail if `GitOptions.environment` could lift the ceiling: git would then find `tmp_path/.git`. The `0o022` limit of `check_seal()` is tested on both sides: `2750`/`750` pass, while `2770` (group) and `757` (others) are refused. The failing sides of the Interface's rules are tested: missing, symbolic link, file, another user, no `HEAD`, a folder that cannot be listed, a discard that cannot remove, and a failed check that leads to a new clone or to the `repository_unavailable` stop. Root-only cases are skipped for root as `test_tick.py` does, and their modes are restored. The four changes to earlier tests are exactly the ones FEATURE decision 23 allows. The coder's entry 10 records `check: green` and `duplicates: 0 new`.
    - Architecture: `RepositoryUnsealed` is in the domain. The three abstract operations on `Git` have docstring-only bodies. The implementations are in `GitCli` and start no process. The preparer stays in the application layer. Its `os.path.lexists` is a file-system check like the `Path.exists` it replaces, not a tool. `run.py` does the wiring. No `dict[str, Any]` crosses a boundary.
    - Security: there are no suppression markers. `_close` uses `lstat` and skips symbolic links, and `os.walk` does not follow them. The folder's owner is checked before any change, which the another-user row with a `0o666` file confirms. `onerror` raises, so a folder that cannot be listed is not silently skipped. The ceiling comes after `**self._options.environment`. A `.git` that is not closed is discarded, never repaired.
    - Quality: `seal` and `check_seal` share one `_check_git_folder`, so they refuse the same cases. The comments say why: the ceiling, the walk's `onerror`, and why the preparer never repairs. The public names have docstrings.
    - Ticket hygiene: the log gives the main decision (discard and clone again, never repair) and what was rejected. The Assignment matches what was built, including that until S0009 the seal holds only at the start of each iteration. The docs criterion still describes what the operator guide, the project guide and the decision log must say.

    Considered and not raised:
    - Criterion 8 tests a missing `HEAD` but not a `HEAD` that exists and is not a regular file. I count the empty folder as the failing side the story names.
    - The test-local `RecordingLog` follows the pattern of three existing test modules.

    Open: nothing.
12. documenter: Docs written from the docs criterion. `python -m factory.entry.check_documents` prints `documents ok`. I did not run `make check`, since I changed only docs. I did not run the `docker exec` observation either, because it needs a real image.

    Files changed:
    - `docs/operator-guide.md`:
      - "Users and directories" has the new `/work/checkout/.git` row.
      - The morning observations table has the `.git` row. A note after the table says to make it after the second iteration and that the agent's git needs `safe.directory`.
      - The section is renamed "The checkout is cloned again when it is missing or its `.git` is not the factory's alone". It now describes the seal, the check, the `cloning the checkout again: ...` log line, the never-repair rule and the `repository_unavailable` stop. The cross-reference in "The low disk" takes the new title.
      - "Left for v2" no longer names the checkout's `.git` as a route.
    - `docs/project-guide.md`:
      - The `Git` interface now has twenty-two operations, with `seal`, `check_seal` (including the `HEAD` check) and `discard` described.
      - `GIT_CEILING_DIRECTORIES` is added to the `GitOptions` table row for `environment`.
      - `git_environment` gives `core.sharedRepository` = `0640`.
      - A new paragraph covers `RepositoryUnsealed` and `CheckoutPreparer.prepare` (check, removal, new clone, seal).
    - `docs/decisions.md`:
      - New entry "The factory alone writes the checkout's `.git`", with the rejected options.
      - The "credential helper and shared group" entry now says `0640`.
      - The "clone killed half-way" entry has an update note.
      - The open point in the token bind-mount entry is marked closed.

    Cross-read and found current: README, and the rest of the operator guide. The project guide already named the three new operations only in the count, which I fixed.

    Not touched: nothing stale that is unrelated. I found no code that contradicts the Interface or the criteria, so there are no findings for the coder.

    `make check`: check: green
    `make documents`: documents ok
13. demo: Demo run from the repository root: all three commands, exactly as written and in order. Every command exited 0 and met its `Expect:` line.

    1. `git_environment()['GIT_CONFIG_VALUE_1']`
    ```
    0640
    ```
    Met: one line, `0640`.

    2. Clone under umask `0o002` with `git_environment()`, then fetch and `seal()`
    ```
    0o750 0o640
    0
    0o664
    ```
    Met: `.git` is `0o750` and `.git/config` is `0o640`. No entry under `.git` (symbolic links excepted) is writable by its group or by others. The work-tree file `a.txt` stays group-writable at `0o664`.

    3. The pytest selection (the mode, seal and preparer tests, wiring boundaries, the git interface, interfaces, scheduler and repository waiter)
    ```
    ........................................................................ [ 55%]
    .........................................................                [100%]
    129 passed in 1.73s
    ```
    Met: `129 passed`, with no failed, error or skipped count. The root-only skips in criteria 6, 9 and 13 did not trigger, so those tests ran.

    Judgement against the acceptance criteria:
    - The demo agrees with criterion 1 (`0640`).
    - It agrees with criteria 2 and 3: git's own mode for the config is `0o640` and the work tree stays group-writable.
    - It agrees with criterion 4: after `seal()`, nothing under `.git` is writable by its group or by others.
    - Criteria 5 to 15 are covered by the tests that passed. The demo contradicts none of them.
    - I did not run `make check` (criterion 16). The factory runs it as the gate after this stage.
    - I did not check the docs criterion (17) in this demo.

    No findings.
