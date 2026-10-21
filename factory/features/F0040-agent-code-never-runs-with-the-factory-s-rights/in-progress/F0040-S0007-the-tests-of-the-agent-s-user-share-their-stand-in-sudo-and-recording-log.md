---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 387
comments_read: []
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-21T06:35:45.732125Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T06:30:23.099674Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T06:30:23.105074Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T06:30:47.813969Z'
  stage: intake
  run: 140c7603b4584a24857f88960c9d5ad6
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T06:31:08.192096Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T06:35:24.066313Z'
  stage: tests
  run: 03288458aaad44faabe503698029c3ea
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T06:35:45.732125Z'
  stage: doing
---

# The tests of the agent's user share their stand-in sudo and their recording log

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

The reviewers of F0040 left notes on its tests that were not findings and that nobody acted on. F0040 added two more local stand-in `sudo` scripts: `SUDO_SCRIPT` and `_write_sudo` in `tests/adapters/test_make_commands_user.py` (S0001), and the same pair in `tests/adapters/test_sudo_agent_home.py` (S0004). Each one records the arguments, the environment and the working directory of a call. Then it either exits with a planned status and standard error, or runs what follows `--`. The two use different field names for the same thing (`working_directory` and `cwd`) and different plan files. Three test modules import `RecordingLog` from another test module, `tests/application/test_checkout_preparer_seal.py`: `test_nested_repositories.py`, and F0040's `test_sealed_project_commands.py` and `test_agent_home_resets.py`. The S0002 reviewer named it as a candidate for the standing leave to move a shared helper. Three other modules there keep a class of their own by that name and import nothing across modules (`test_dispatcher.py`, `test_scheduler.py`, and `test_repository_waiter.py` with one method more); they stay as they are. Three smaller notes change what an assertion checks, so the standing leave does not cover them: `tests/adapters/test_make_commands_user.py` restates `LEFTOVERS_FAULT` instead of importing it from `factory.adapters.agent_launch`; its criterion-8 test compares `.user` with `==` where the criterion says "is"; and `tests/domain/test_agent_home.py` passes the refusal text to `pytest.raises(match=...)` as a regular expression, so `../x` matches more than the exact text. This story moves the two helpers to one shared place each and makes the three assertions exact. It is the tester's alone: the coder changes nothing, and every test keeps its name. The older stand-in `sudo` scripts (`tests/leftovers_runtime_support.py`, `tests/adapters/test_claude_runtime_os_user.py`, `tests/adapters/test_claude_runtime_confinement.py`, `tests/confine_support.py`) stay as they are.

## Interface

No module under `src/factory/` changes. The tester changes these test files:

- New `tests/recording_log.py`: `RecordingLog(FactoryLog)`, moved unchanged from `tests/application/test_checkout_preparer_seal.py`. That module, `tests/application/test_nested_repositories.py`, `tests/application/test_sealed_project_commands.py` and `tests/application/test_agent_home_resets.py` import it from there. This is under the standing leave of `CLAUDE.md` (*Tests*).
- New `tests/sudo_support.py`: one stand-in `sudo` for both F0040 modules.

```python
class SudoCall(BaseModel):
    """One call the stand-in `sudo` saw."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    arguments: list[str]
    environment: dict[str, str]
    working_directory: Path


@dataclass(frozen=True)
class Sudo:
    """The stand-in `sudo` and the folder that holds its plan and its record."""

    path: Path
    folder: Path

    def calls(self) -> list[SudoCall]:
        """The calls it recorded, in order."""


def write_sudo(
    folder: Path,
    *,
    exit_status: int | None = None,
    stderr: str = "",
    warning: str = "",
    program: Path | None = None,
    wait_seconds: float = 0,
) -> Sudo:
    """Write the stand-in into `folder`: it records each call, then runs `program` or what follows `--`, or exits as planned."""
```

- Rules of the stand-in: it records every call first. A call whose first word after `--` is `program` runs that program, whatever the plan. Any other call writes `warning` to standard error. Then, when `exit_status` is set, it writes `stderr`, waits `wait_seconds` and exits with `exit_status`; when it is not set, it runs what follows `--`. These are the behaviours of the two scripts it replaces, together.
- `tests/adapters/test_make_commands_user.py` and `tests/adapters/test_sudo_agent_home.py` drop their stand-in (both: `SUDO_SCRIPT`, `_write_sudo` and `SudoCall`; the first also `Sudo`; the second also `_sudo_calls`, `CALLS` and `PLANNED`) and use `tests/sudo_support.py`. Every test keeps its name and its rows, and checks the same calls. In the second module, a test reads the shared record's `working_directory` where it read `cwd` (`call.cwd == "/"` becomes `call.working_directory == Path("/")`, the same check), a planned row `(exit_status, stderr)` is passed as `exit_status=` and `stderr=`, and the stand-in's path is `Sudo.path`. Under the standing leave.
- Beyond the standing leave, and only with the leave the human writes into the feature's `feature.md` when refining this story (decision 18): in `tests/adapters/test_make_commands_user.py`, `LEFTOVERS_FAULT` is imported from `factory.adapters.agent_launch` (the source's constant ends in `:` without the test's trailing space, so the two expected details of `LEFTOVERS_ROWS` become `f"{LEFTOVERS_FAULT} ..."`, the same text), and `test_the_user_property_returns_what_the_constructor_was_given` asserts `MakeProjectCommands(tmp_path, user=user).user is user`. In `tests/domain/test_agent_home.py`, `test_kept_paths_are_the_logins_inside_the_home_then_state_files_then_folders` uses `match=re.escape(refused)`.

## Acceptance criteria

1. `tests/recording_log.py` holds `RecordingLog`. `tests/application/test_checkout_preparer_seal.py` no longer defines it, and the four modules named in the Interface import it from `recording_log`. The classes of that name in `test_dispatcher.py`, `test_scheduler.py` and `test_repository_waiter.py` stay.
2. `tests/sudo_support.py` holds `write_sudo`, `Sudo` and `SudoCall`. Neither `tests/adapters/test_make_commands_user.py` nor `tests/adapters/test_sudo_agent_home.py` defines `SUDO_SCRIPT` or `_write_sudo`.
3. The test ids that `uv run pytest --collect-only` lists for the changed test modules (the six of the Interface's standing-leave bullets, and `tests/domain/test_agent_home.py` with criterion 4's leave) are the same before and after the change, and every one of them passes.
4. With the human's leave (Interface, last bullet): `LEFTOVERS_FAULT` is not assigned in `tests/adapters/test_make_commands_user.py`; the criterion-8 test of that module uses `is`; and `tests/domain/test_agent_home.py` passes `re.escape(refused)` to `match`. Without that leave, this criterion is dropped when the story is refined.
5. Nothing under `src/` changes. The coder ends with an entry saying so.
6. `make check` stays green.
7. docs: `docs/project-guide/README.md`, *Shared test helpers*, the list of the modules under `tests/` whose name does not start with `test_`, gains two entries in its alphabetical order: `recording_log.py`: `RecordingLog`, a factory log that keeps the lines written to it; and `sudo_support.py`: a stand-in `sudo` that records each call's arguments, environment and working directory and runs the call or exits as planned (`write_sudo`, `Sudo`, `SudoCall`). No other document changes, because no behaviour changes.

## Smoke test

```bash
grep -c "^SUDO_SCRIPT\|^def _write_sudo\|^class RecordingLog" tests/adapters/test_make_commands_user.py tests/adapters/test_sudo_agent_home.py tests/application/test_checkout_preparer_seal.py
```
Expect: three lines, each ending in `:0`

```bash
uv run pytest tests/adapters/test_make_commands_user.py tests/adapters/test_sudo_agent_home.py tests/application/test_checkout_preparer_seal.py tests/application/test_nested_repositories.py tests/application/test_sealed_project_commands.py tests/application/test_agent_home_resets.py 2>&1 | tail -n 1
```
Expect: one summary line with a count of `passed`, and no `failed` and no `error` in it

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: concrete. It names `tests/recording_log.py` (`RecordingLog`) and `tests/sudo_support.py` (`SudoCall`, `Sudo`, `write_sudo` with full signatures). It lists the stand-in's rules and which names each of the two adapter test modules drops. No `src/` change.
   - Criteria: each is testable by one check. These are the moved definitions and imports (1, 2), identical collected ids with all passing (3), the three exact assertions (4), nothing under `src/` (5), `make check` (6) and the docs entry (7). The stand-in's rules (record first, `program` runs whatever the plan, `warning`, `exit_status`/`stderr`/`wait_seconds`, otherwise run what follows `--`) are the behaviours of the two scripts being replaced. The unchanged tests of the two modules (criterion 3) exercise them. The story adds no new behaviour, so no failing side lacks a criterion. Criterion 4's leave is in the feature's `feature.md`, decision 18 ("granted", the human, 2026-10-21).
   - Smoke test: both commands are runnable. The `grep -c` over three files prints `path:count` lines, so "each ending in `:0`" is checkable. The pytest command passes no `-q`, and `pyproject.toml` `addopts` already sets `-q`, so the last line is a summary with a `passed` count.
   - Architecture: test-only changes, in the places `CLAUDE.md` gives. The shared helpers are modules at the `tests/` root, which the standing leave allows. The tester makes the move, and the coder changes nothing.
   - Scope: it is inside F0040 (the S0001 and S0004 test modules and the reviewers' notes). Nothing in the feature's "Out of scope" is touched; the older stand-in scripts stay as they are.
4. factory: started tests as self.
5. tester: This story is only about tests, and all of it is the tester's job. So I made the changes themselves (moving the helpers and making three checks exact) instead of writing new red tests. The work is done and `make test` is green. Nothing under `src/` changed, so the coder has nothing to implement. The coder only needs to confirm that (criterion 5) and run `make check` (criterion 6).

   Criterion → where it is met:
   - criterion 1: `tests/recording_log.py::RecordingLog` was moved unchanged from `tests/application/test_checkout_preparer_seal.py`. That module, `test_nested_repositories.py`, `test_sealed_project_commands.py` and `test_agent_home_resets.py` now import it with `from recording_log import RecordingLog`. The unused `FactoryLog` import was dropped from the seal module. The classes in `test_dispatcher.py`, `test_scheduler.py` and `test_repository_waiter.py` were not touched.
   - criterion 2: `tests/sudo_support.py` holds `SudoCall`, `Sudo` and `write_sudo` with the signatures in the Interface. Its script combines the two old ones: it records the call, then the planned `program` runs; any other call writes `warning`, then either exits after `stderr` and `wait_seconds` or runs what follows `--`. An unset `program` is stored as null. `tests/adapters/test_make_commands_user.py` dropped `SUDO_SCRIPT`, `_write_sudo`, `SudoCall` and `Sudo`. `tests/adapters/test_sudo_agent_home.py` dropped `SUDO_SCRIPT`, `_write_sudo`, `SudoCall`, `_sudo_calls`, `CALLS` and `PLANNED`. In that module, `call.cwd == "/"` became `call.working_directory == Path("/")`. A planned `(exit_status, stderr)` is now passed as keyword arguments, and the stand-in's path is `Sudo.path`.
   - criterion 3: I listed the test ids with `uv run pytest --collect-only` (with `-o addopts=""`) for the seven modules before and after the change. Both lists have the same 109 ids (no diff). `make test` passed: `test: green (61.0 s)`, coverage 99.14 %.
   - criterion 4: the leave is decision 18 in the feature's `feature.md`, which intake cited; I did not read the file myself. `LEFTOVERS_FAULT` is now imported from `factory.adapters.agent_launch`, and the two expected details are `f"{LEFTOVERS_FAULT} ..."`, the same text as before. `test_the_user_property_returns_what_the_constructor_was_given` now checks with `is user`. In `tests/domain/test_agent_home.py`, `test_kept_paths_are_the_logins_inside_the_home_then_state_files_then_folders` uses `match=re.escape(refused)` and adds an `import re`.
   - criteria 5–7: for the coder (nothing under `src/`), for `make check`, and for the docs stage (two entries under *Shared test helpers* in `docs/project-guide/README.md`).

   Files created: `tests/recording_log.py`, `tests/sudo_support.py`.
   Earlier test files changed:
   - Under the standing leave (*Tests* in `CLAUDE.md`): `tests/application/test_checkout_preparer_seal.py`, `tests/application/test_nested_repositories.py`, `tests/application/test_sealed_project_commands.py`, `tests/application/test_agent_home_resets.py`, `tests/adapters/test_make_commands_user.py`, `tests/adapters/test_sudo_agent_home.py`.
   - Under the human's leave (decision 18): the three assertions in criterion 4, in `tests/adapters/test_make_commands_user.py` and `tests/domain/test_agent_home.py`.

   Every test kept its name and its rows. The older stand-in `sudo` scripts were left as they are; this includes `_write_sudo` in `tests/adapters/test_claude_runtime_os_user.py`, which `tests/test_test_children.py` uses.

   Modules the test run could not import: none. There are no red tests, because the story adds no behaviour. `make lint` and `make types` were both green.

   Smoke test: the `grep -c` prints three lines, each ending in `:0`.

   `lint`: lint: green (0.6 s)
   `test`: test: green (60.9 s)
6. factory: started doing as self.
