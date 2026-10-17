---
stage: tests
pr: 194
blocked: null
comments_seen: 2
round: 0
attempts: 0
---
# No nested repository in the work tree

## Assignment (as of log entry 3)

S0006 and S0009 keep the checkout's own `.git` the factory's alone, but the agent can still make a git repository anywhere in the work tree it may write, for example with `uv run ...`, which `claude/settings.json` allows. The pre-check of 2026-10-17 found the route with git 2.39.5, the image's version, and S0001's environment. The factory's own commit (`git add --all`) adds such a repository as a gitlink, with only a warning. From then on the factory's `git status` and `git diff` start a child `git status` inside it, and the child reads that repository's own configuration: its `core.fsmonitor` ran as `factory`, the user who can read the hosting token. Even a nested `.git` the agent makes itself may pass git's ownership check, since the agent can rename one of the factory's group-writable folders into place. `git clean -f -d`, the restore, keeps a nested repository (`-ff` would remove it), and `diff.ignoreSubmodules=all` did not stop the child.

The human's answer after the pre-check (2026-10-17, FEATURE decision 30) closes the route structurally:

- After every agent run, where S0009 checks the seal, the factory looks for any entry named `.git` (a folder, a file or a symbolic link) below the work tree's root, other than the root's own. Each one it finds, it removes, as the undo removes a write outside the write paths, and the stage stalls with a note naming the paths. No factory git command runs between the agent run and the removal, so git never sees the repository.
- `core.fsmonitor=false` joins the factory's git environment pairs as a second line of defence, beside S0001's `core.hooksPath`. The child git of a nested repository inherits the `GIT_CONFIG_*` pairs, so even a nested repository the search missed cannot start its `core.fsmonitor` (tested at the pre-check). Other keys of a nested configuration were not tried there; the removal is what covers them.

The same search runs at the start of every iteration, on an existing checkout that passed S0006's check, so that a nested repository left by an older checkout, or one the factory could not remove after a run, never meets a git command. One the factory cannot remove there makes the preparer remove the whole checkout and clone it again (S0006), and when that fails too, the stop `repository_unavailable` follows (FEATURE decision 31). The probe of the agent run, which has no stage, fails its item with the paths instead of stalling.

The tests use a real nested repository in a real checkout: its `core.fsmonitor` must not run, its path must be gone, and the stall must name it. Five tests of earlier stories change by the human's leave (FEATURE decision 32). Built right after S0009, whose `run_sealed` it extends.

## Interface

`src/factory/entry/wiring.py`: `git_environment(helper: str = CREDENTIAL_HELPER) -> dict[str, str]`, signature unchanged, returns exactly these nine entries: S0001's table as S0006 leaves it, with a fourth pair.

| Name | Value |
|---|---|
| `GIT_CONFIG_COUNT` | `4` |
| `GIT_CONFIG_KEY_0` | `credential.helper` |
| `GIT_CONFIG_VALUE_0` | `helper` |
| `GIT_CONFIG_KEY_1` | `core.sharedRepository` |
| `GIT_CONFIG_VALUE_1` | `0640` |
| `GIT_CONFIG_KEY_2` | `core.hooksPath` |
| `GIT_CONFIG_VALUE_2` | `os.devnull` (`/dev/null`) |
| `GIT_CONFIG_KEY_3` | `core.fsmonitor` |
| `GIT_CONFIG_VALUE_3` | `false` |

Its comment says why the fourth pair is there: a child git started for a nested repository inherits the pairs, so that repository's `core.fsmonitor` never runs as the factory's user.

`src/factory/application/git.py`, the `Git` interface, gains one abstract operation (twenty-three in all): `remove_nested_repositories() -> list[str]`: remove every entry named `.git` below the working copy's root other than the root's own repository folder, and return their paths relative to the working copy, `/`-separated and sorted; `[]` when there is none. One it cannot remove raises `RepositoryUnsealed`.

`src/factory/adapters/git_cli.py`, `GitCli.remove_nested_repositories()`, with no git process:

- Walks the working copy top-down with `os.walk(..., followlinks=False)`. At the root it leaves out the root's own `.git`: not entered, not reported. In every other folder, an entry named exactly `.git` among the folders or the files (a folder, a file, or a symbolic link, dangling or not) is a nested repository; the walk does not enter it. Every other folder is entered, `.venv` included. A folder the walk cannot list is skipped, as `os.walk` does: the factory's git cannot look into it either.
- Removes each one it finds: a folder that is not a symbolic link (`os.lstat`) with `shutil.rmtree`, anything else with `os.unlink`. Its parent folder and everything else in it stay, so the nested work tree's files become ordinary files of the work tree, which the undo and the write paths then judge as any other.
- An `OSError` while removing one raises `RepositoryUnsealed(f"{path}: {error}")`, the path absolute, S0006's detail form.

`src/factory/application/sealed_runs.py`:

- A new model `SealedRun`, frozen, with unknown keys refused: `result: AgentRunResult` and `nested_repositories: list[str]`.
- `run_sealed(boundaries, request) -> SealedRun`. It seals, runs and, in the `finally`, calls `check_seal()` and then `remove_nested_repositories()`, and returns the run's result with the removed paths. When the run raises, the removal still runs and the run's error propagates (a `RepositoryUnsealed` of the check or the removal wins, as in S0009); the paths are then not reported. When `check_seal()` raises, no search runs: the next iteration clones the checkout again.

`src/factory/application/stage.py`:

- `LaunchedStage` gains `nested_repositories: list[str] = []`. `StageLauncher.launch` takes `result` and `nested_repositories` from `run_sealed`'s `SealedRun`.
- `AfterAgent.process`, as its first step, before the branch check: when `launched.nested_repositories` is not empty, the stage stalls with the reason `nested_repository` and the detail the paths joined by `, `, as any other stall of `process` (one attempt counted, the undo, the stall entry, the note). Its docstring names it.

`src/factory/domain/decisions.py`: `StallReason` gains `nested_repository`, after `merge_conflict`. `src/factory/domain/post_texts.py`: its sentence is `the agent left a git repository in the work tree, which the factory removed`. So the note reads, for example, `Stalled (attempt 1 of 3): the agent left a git repository in the work tree, which the factory removed: notes/sub/.git. Retrying on the next tick.`

`src/factory/application/preflight.py`: `agent_run_probe_item` takes the result from `run_sealed(...).result`. When the `SealedRun` names nested repositories, the item fails with the detail `the probe run left a git repository in the work tree, which the factory removed: <paths joined by ", ">`, before the end reason is looked at.

`src/factory/application/scheduler.py`: `CheckoutPreparer.prepare`, on an existing checkout that passes `check_seal()`, calls `remove_nested_repositories()` before `seal()`. When it removed any, it writes the log line `removed nested repositories: <paths joined by ", ">` (when a log is given). A `RepositoryUnsealed` from it is handled as a failed check: the log line `cloning the checkout again: <error>`, `discard()`, `clone(url)`, then `seal()`. A fresh clone is not searched.

Tests:

- New modules:
  - `tests/entry/test_git_nested_repositories.py`: the `remote` fixture, `clone` and `run_git` of `tests/git_support.py`, `GitCli` with `git_environment()` and with `GitOptions()`. The `core.fsmonitor` of the nested repository is an executable shell script that appends a line to a marker file under `tmp_path`, outside the checkout.
  - `tests/adapters/test_git_cli_nested.py`: clones from `clone` of `tests/git_support.py`; nested repositories made with `run_git(<folder>, "init", "-q")`.
  - `tests/application/test_nested_repositories.py`: `run_sealed`, the stall, the probe and the preparer, on the `boundaries` fixture. The runtimes that make a nested repository are implementations of `AgentRuntime` written in the test, wrapping `FakeAgentRuntime`, which run `run_git(<folder>, "init", "-q")` during the run. The stall's test imports `_launch`, `_stalled`, `_note` and `_completed` from `application.test_after_agent` (not copied) and hands `_launch` a `Boundaries` whose `agent_runtime` is that wrapper (`dataclasses.replace`), with the `FakeAgentRuntime` as `agent_runtime=` for the queue.
- By the human's leave (FEATURE decision 32), and no other change to an earlier story's test:
  - In `tests/entry/test_wiring_boundaries.py` (F0010-S0003, as F0014-S0006 leaves it): `test_git_environment_gives_the_credential_helper_the_shared_group_and_no_hooks` expects the nine entries of the table above, for both rows, and `test_the_built_git_runs_with_the_git_options_of_the_settings` also asserts `GIT_CONFIG_KEY_3` = `core.fsmonitor` and `GIT_CONFIG_VALUE_3` = `false`. Both keep their names.
  - In `tests/application/test_git_interface.py` (as F0014-S0006 leaves it): `OPERATIONS` gains `remove_nested_repositories`, and the test becomes `test_git_has_exactly_the_twenty_three_operations_and_git_cli_has_each`.
  - In `tests/application/test_interfaces.py` (as F0014-S0006 leaves it): `test_git_abstract_methods_are_exactly_its_twenty_two_operations` becomes `test_git_abstract_methods_are_exactly_its_twenty_three_operations`, its body unchanged.
  - In `tests/domain/test_stall_texts.py` (F0001): `SENTENCES` gains the row `("nested_repository", "the agent left a git repository in the work tree, which the factory removed")`, after the row of `merge_conflict`.
  - In `tests/application/test_sealed_runs.py` (F0014-S0009): the test of S0009's criterion 1 compares the runtime's result with `run_sealed(...).result` in place of `run_sealed(...)`; its name and every other assertion stay.

## Acceptance criteria

1. `git_environment()` returns exactly the nine entries of the Interface with the helper `/usr/local/bin/git-credential-factory`, and `git_environment("/opt/other-helper")` the same nine with `/opt/other-helper` as `GIT_CONFIG_VALUE_0`; the built boundaries' git runs with `GIT_CONFIG_KEY_3` = `core.fsmonitor` and `GIT_CONFIG_VALUE_3` = `false` (the changed tests of `tests/entry/test_wiring_boundaries.py`).
2. A nested repository's `core.fsmonitor` does not run under the factory's git. In a checkout cloned from the `remote` fixture, a nested repository at `notes/sub` holds one commit and a `core.fsmonitor` that appends to the marker file. `GitCli` with `GitOptions()` commits it into the checkout as a gitlink, and the marker is emptied afterwards. Then `status()` and `changed_paths("HEAD")` with `git_environment()` leave the marker empty, while the same two with `GitOptions()` write it, which shows the command is real. Four rows of one parametrized test.
3. `remove_nested_repositories()` in a checkout cloned from the `remote` fixture, rows of one parametrized test; in every row the root's `.git` stays and `resolve("HEAD")` still gives the clone's commit:
   - nothing nested: returns `[]`, nothing changes;
   - a repository made by `git init` at `notes/sub`, with a file `notes/sub/a.txt`: returns `["notes/sub/.git"]`; `notes/sub/.git` is gone, `notes/sub/a.txt` stays;
   - a file `other/.git` holding `gitdir: ` and a path outside the checkout: returns `["other/.git"]`, and the file is gone;
   - a symbolic link `link/.git` to a folder outside the checkout: returns `["link/.git"]`; the link is gone, its target and the target's files stay;
   - a repository at `a` and another at `a/b`: returns `["a/.git", "a/b/.git"]`, and both are gone;
   - a folder `.github`, a file `x.git` and a folder `sub.git`: returns `[]`, and all three stay;
   - a repository made by `git init` at `.venv/lib/x`: returns `[".venv/lib/x/.git"]`, and it is gone;
   - a folder `closed` at `0o000`: returns `[]` with no error, and the folder stays; skipped for root, as `tests/application/test_tick.py` does; the test restores the mode afterwards.
4. A nested repository the factory cannot remove: a folder `locked` at `0o555` that holds a repository made by `git init` makes `remove_nested_repositories()` raise `RepositoryUnsealed` whose message holds the path of `locked/.git`. Skipped for root, as `tests/application/test_tick.py` does; the test restores the mode afterwards.
5. `run_sealed` reports and removes, rows of one parametrized test:
   - a run that makes a repository at `notes/sub` and completes: the `SealedRun`'s `result` is the runtime's result, its `nested_repositories` is `["notes/sub/.git"]`, and `notes/sub/.git` is gone when `run_sealed` returns;
   - a run that makes none: `nested_repositories` is `[]`;
   - a run that makes a repository at `notes/sub` and then raises `AgentRuntimeError`: that error propagates, and `notes/sub/.git` is gone;
   - a run that makes a repository at `notes/sub` while `check_seal()` fails: `RepositoryUnsealed` propagates and `notes/sub/.git` stays, since no search runs;
   - a run that raises `AgentRuntimeError` while the removal fails (the `locked` folder of criterion 4): `RepositoryUnsealed` propagates, not the run's error; skipped for root, the mode restored afterwards.
6. A stage whose agent makes a nested repository stalls. With a run that completes with an allowed decision and makes a repository at `notes/sub`, whose `core.fsmonitor` appends to the marker file: `launch` gives `nested_repositories` = `["notes/sub/.git"]`, and `notes/sub/.git` is gone. `AfterAgent.process` returns a `StallResult` with the reason `nested_repository` and one attempt more. The note posted on the pull request is `stall_note("nested_repository", 1, <attempts cap>, detail="notes/sub/.git")`, and the journal's last record is the factory's `stall`, whose text names `notes/sub/.git`. The marker is still empty after the stall's commit and push. A second row: the branch check would also fail (the agent's commits leave the ticket's branch as the earlier tests of `tests/application/test_after_agent.py` make it fail), and the reason is still `nested_repository`.
7. `stall_cause("nested_repository")` is `the agent left a git repository in the work tree, which the factory removed` (the changed row of `tests/domain/test_stall_texts.py`).
8. The probe, rows of one parametrized test: a probe run that completes and makes a repository at `notes/sub` fails the item with exactly the detail `the probe run left a git repository in the work tree, which the factory removed: notes/sub/.git`, and `notes/sub/.git` is gone; a probe run that completes and makes none passes; a probe run that ends with a reason other than complete and makes a repository at `notes/sub` fails with the same exact nested-repository detail.
9. `CheckoutPreparer.prepare` on an existing checkout that passes `check_seal()` and holds a repository at `notes/sub` keeps the checkout (a file the test put in the work tree is still there) and removes `notes/sub/.git`. The log holds exactly one line, `removed nested repositories: notes/sub/.git`. Built without a log, the preparer does the same without an error. A row for an existing checkout with nothing nested keeps the checkout and writes no `removed nested repositories` line (rows of one parametrized test).
10. `CheckoutPreparer.prepare` on an existing checkout that passes `check_seal()` and holds the `locked` folder of criterion 4 writes the log line `cloning the checkout again: ` followed by the error's message and raises `GitError` whose message holds `discard`, since the whole checkout cannot be removed either. Skipped for root, as `tests/application/test_tick.py` does; the test restores the mode afterwards.
11. What must still hold: the tests of the factory's git hooks (`tests/entry/test_git_hooks.py`), of the seal (`tests/adapters/test_git_cli_seal.py`, `tests/application/test_checkout_preparer_seal.py`, `tests/application/test_sealed_runs.py`), of the stage launch and its aftermath (`tests/application/test_stage_launch.py`, `tests/application/test_after_agent.py`), of the stalls and their texts, of the probe and of the tick pass.
12. `CheckoutPreparer.prepare` on a missing checkout clones it without a call to `remove_nested_repositories`.
13. `make check` stays green.
14. docs: The operator guide:
    - A paragraph beside S0006's *The checkout is cloned again when it is missing or its `.git` is not the factory's alone* says that after every agent run the factory removes any `.git` below the work tree's root (a folder, a file or a link) and stalls the stage with the reason `nested_repository` and the paths. At the start of every iteration it removes one an older checkout holds, with the line `removed nested repositories: ...` in `/state/factory.log`. One it cannot remove makes it clone the checkout again, and when that fails, the stop `repository_unavailable` follows. A project whose tools keep a git repository inside the work tree, even in an ignored folder, therefore stalls every stage: keep such clones outside `/work/checkout`. A probe run that leaves one fails the item `agent-run-probe` with the paths.
    - Where the guide lists the stall reasons, `nested_repository` is added.

    The project guide:
    - `git_environment` returns nine entries, `GIT_CONFIG_COUNT=4`, with `core.fsmonitor` = `false`.
    - `Git` has twenty-three operations, with `remove_nested_repositories` described.
    - `run_sealed` returns a `SealedRun`, and its `finally` checks the seal and then removes nested repositories.
    - `StallReason` gains `nested_repository`, and `AfterAgent.process`'s first step is that stall.
    - The probe's detail for a nested repository, and the preparer's search, are described.

    The decision log gets an entry "No nested repository in the work tree". It gives the route found at the pre-check (a gitlink makes the factory's `status` and `diff` start a child git that reads the nested repository's configuration), and the human's answer. It says why the removal comes right after the run, before any git command, and why the stage stalls rather than keeping the agent's work silently. It says why `-ff` and not the restore's `-f`, and why `core.fsmonitor=false` is a second line: other keys were not tried, and the removal covers them. It names what is left: an index entry of mode `160000` without a repository behind it is not refused, since no child git starts for it; and a folder the factory cannot list is not searched, since its git cannot read it either.

    No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "from factory.entry.wiring import git_environment; print(sorted(git_environment().items()))"
```
Expect: one line: `[('GIT_CONFIG_COUNT', '4'), ('GIT_CONFIG_KEY_0', 'credential.helper'), ('GIT_CONFIG_KEY_1', 'core.sharedRepository'), ('GIT_CONFIG_KEY_2', 'core.hooksPath'), ('GIT_CONFIG_KEY_3', 'core.fsmonitor'), ('GIT_CONFIG_VALUE_0', '/usr/local/bin/git-credential-factory'), ('GIT_CONFIG_VALUE_1', '0640'), ('GIT_CONFIG_VALUE_2', '/dev/null'), ('GIT_CONFIG_VALUE_3', 'false')]`.

```bash
uv run python -c "
import subprocess, tempfile
from pathlib import Path
from factory.adapters.git_cli import GitCli
root = Path(tempfile.mkdtemp())
checkout = root / 'checkout'
subprocess.run(['git', 'init', '-q', str(checkout)], check=True)
subprocess.run(['git', 'init', '-q', str(checkout / 'notes' / 'sub')], check=True)
(checkout / 'notes' / 'sub' / 'a.txt').write_text('a\n', encoding='utf-8')
(checkout / 'other').mkdir()
(checkout / 'other' / '.git').write_text('gitdir: ' + str(root / 'elsewhere') + '\n', encoding='utf-8')
print(GitCli(checkout).remove_nested_repositories())
print((checkout / 'notes' / 'sub' / 'a.txt').is_file(), (checkout / 'notes' / 'sub' / '.git').exists(), (checkout / 'other' / '.git').exists(), (checkout / '.git').is_dir())
"
```
Expect: two lines: `['notes/sub/.git', 'other/.git']`, then `True False False True`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/entry/test_git_nested_repositories.py tests/adapters/test_git_cli_nested.py tests/application/test_nested_repositories.py tests/entry/test_wiring_boundaries.py tests/application/test_git_interface.py tests/application/test_interfaces.py tests/domain/test_stall_texts.py tests/application/test_sealed_runs.py tests/application/test_after_agent.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: 1. Several behaviours stated in `## Interface` have no criterion, so a coder could implement them in two ways and still pass the tests. The format check passed. The rest of the story looks complete: the Interface names modules and signatures, the Demo runs, and the architecture and scope fit `FEATURE.md`. Each gap below needs a criterion, or a statement that it is deliberately untested.
      a. `GitCli.remove_nested_repositories`: "Every other folder is entered, `.venv` included". Criterion 3 has no row with a nested `.git` inside `.venv` or another ordinary hidden folder. Option: add a row `.venv/lib/x/.git` that returns `[".venv/lib/x/.git"]`.
      b. `GitCli.remove_nested_repositories`: "A folder the walk cannot list is skipped". No criterion covers it. Option: add a row with a `0o000` folder, skipped for root and restored afterwards, that returns `[]` with no error.
      c. `run_sealed`: "When `check_seal()` raises, no search runs". Criterion 5 has no row for it. Option: add a row in which `check_seal()` fails, `RepositoryUnsealed` propagates and the nested `.git` stays.
      d. `run_sealed`: "A `RepositoryUnsealed` of the check or the removal wins" over the run's error. No criterion covers it. Option: add a row in which the run raises `AgentRuntimeError` and the removal raises `RepositoryUnsealed` (the `locked` folder), and `RepositoryUnsealed` propagates.
      e. `agent_run_probe_item`: the nested-repository failure comes "before the end reason is looked at". Criterion 8 covers only runs that complete. Option: add a row in which the run ends with a non-complete reason and makes a repository, and the detail is still the nested-repository text.
      f. `CheckoutPreparer.prepare`: "A fresh clone is not searched". No criterion covers it. Option: add a criterion that a missing checkout is cloned without a call to `remove_nested_repositories`, or drop the sentence.
      g. `CheckoutPreparer.prepare`: the log line is written only when it removed any. Criterion 9 tests only the case where something was removed. Option: add a row for an existing checkout with nothing nested, which writes no `removed nested repositories` line and keeps the checkout.
      h. `AfterAgent.process`: the stall is "as its first step, before the branch check". Criterion 6 does not show the order. Option: add a row in which the branch check would also fail and the reason is still `nested_repository`.
   I would choose to add all eight as rows of the existing parametrized criteria (3, 5, 8, 9 and 6), and criterion f as a new criterion before the two closing ones.
3. human (pull request comment, 2026-10-17): 1: yes, all eight as you propose: a, b, c, d, e, g and h as rows of the existing parametrized criteria (3, 5, 8, 9 and 6), and f as a new criterion before the two closing ones (a missing checkout is cloned without a call to `remove_nested_repositories`). For b, the `0o000` folder row is skipped when the tests run as root and its mode is restored afterwards.
4. intake: accepted, with the human's answer (log entry 3) carried into the story; the Assignment heading now reads "as of log entry 3", its meaning unchanged.
   - Carried in from entry 3, and nothing else: criterion 3 gained rows `.venv/lib/x` (a, `[".venv/lib/x/.git"]`) and an unlistable `0o000` folder (b, `[]`, skipped for root, mode restored). Criterion 5 gained a row where `check_seal()` fails and the nested `.git` stays (c), and a row where the run raises and the removal fails, so `RepositoryUnsealed` wins (d). Criterion 6 gained a row where the branch check would also fail (h). Criterion 8 gained a row where the probe run does not complete (e). Criterion 9 gained a row with nothing nested (g). A new criterion 12 says a missing checkout is cloned without a call to `remove_nested_repositories` (f). `make check` is now 13 and `docs:` is 14, still last.
   - Interface: concrete modules, signatures and the nine-entry table; every behaviour stated there (paths relative, `/`-separated and sorted, the log line, the detail texts, the order in `run_sealed`) now has a criterion.
   - Criteria: each is testable by one parametrized test function. Each rule has its failing side: unremovable folder (4, 10), removal failure and seal failure in `run_sealed` (5), non-nested lookalikes (3).
   - Demo: three runnable commands, and each `Expect:` line can be checked against the output.
   - Architecture: the walk and the removal sit in the `GitCli` wrapper behind the `Git` interface, the stall in `application`, the stall reason and its text in `domain`, and the wiring in `entry`. This fits the four layers.
   - Scope: within F0014's scope, which lists S0010 and its modules. It touches nothing in "Out of scope". The five earlier tests it changes are covered by FEATURE decision 32.
