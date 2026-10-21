---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-21T06:30:23.105074Z'
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
