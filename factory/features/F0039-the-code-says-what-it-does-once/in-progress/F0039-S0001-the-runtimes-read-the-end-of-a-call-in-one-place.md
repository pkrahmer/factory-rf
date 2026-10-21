---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 379
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T00:24:13.450751Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T00:24:13.456802Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T00:24:30.483005Z'
  stage: intake
  run: e7c57f9cf8da45748d5ea61ca7d3f221
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T00:24:50.996821Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T00:27:51.196842Z'
  stage: tests
  run: 2f2e34890db84a9ebc294d837122c374
---

# The runtimes read the end of a call in one place

## Description

`ClaudeCodeRuntime._call` and `OpencodeRuntime._call` end in the same sequence: read a call that the runtime's own `timeout` killed at its limit as `timed_out`, then read the refusals of `sudo`, the write guard's wrapper and the login shell with that reading, and raise `AgentRuntimeError` for one. Each runtime also writes the text "cannot write the state directory ..." itself. This story moves the sequence into one function of `factory.adapters.agent_launch`, `read_call_end`, and the text into `state_directory_error`, and both runtimes call them (the feature's decision 1). The order stays: the kill is read first, so a call that printed a reply and was killed is still read for refusals. Unchanged: every result and every error of both runtimes, the runtimes' own process calls (`_start`, `_request_of`, `_remove_temporary_folder`, `version`) and `_confinement` (the feature's decision 2), and the state directory, which `ClaudeCodeRuntime` creates and `OpencodeRuntime` must find (decision 3). `agent_launch` still imports nothing of `factory.adapters.process`.

## Interface

`src/factory/adapters/agent_launch.py` (`adapters`):

```python
class CallEnd(BaseModel):
    """How a runtime's call ended, as the reading of its end needs it."""

    stderr: str
    printed: bool
    exit_status: int | None
    duration: timedelta
    timed_out: bool


def read_call_end(
    end: CallEnd, *, time_limit: timedelta, os_user: str | None, starters: Starters
) -> bool:
    """Whether a call ended at its time limit; a call that was refused is `AgentRuntimeError`."""


def state_directory_error(state_directory: Path, error: OSError) -> AgentRuntimeError:
    """The error of a run whose files cannot be written to `state_directory`."""
```

- `CallEnd` is frozen and forbids unknown keys (`tests/test_model_configuration.py`); it holds the process's fields, not a `ProcessResult`, and four parameters keep `read_call_end` within ruff's `max-args = 5`.
- `read_call_end` is `True` when `end.timed_out` is `True`, or when `killed_at_limit(os_user=os_user, exit_status=end.exit_status, duration=end.duration, time_limit=time_limit)` is `True`; otherwise `False`.
- It then reads `call_refusal(end.stderr, printed=end.printed, timed_out=<that value>, os_user=os_user, starters=starters)`; a refusal raises `AgentRuntimeError(<the refusal>)`, and no refusal returns the value.
- `state_directory_error` returns, and does not raise, `AgentRuntimeError(f"cannot write the state directory {state_directory}: {error}")`.
- `killed_at_limit` and `call_refusal` stay public with their signatures.
- `agent_launch` imports nothing of `factory.adapters.process` (`tests/test_agent_launch_search.py`, unchanged).

`src/factory/adapters/claude_runtime.py` and `src/factory/adapters/opencode_runtime.py` (`adapters`), for the reviewer:

- Each `_call` replaces its own calls of `killed_at_limit` and `call_refusal`, and the comment beside them, with one `CallEnd` of its process, its own `printed` reading in it (the reply parsed, or events read), and one call of `read_call_end` with the time limit of that call, and sets the process's `timed_out` to the value it returns.
- `ClaudeCodeRuntime._state_error` and `OpencodeRuntime._write_files` raise `state_directory_error(self._state_directory, exc)`.
- Nothing else in the two modules changes.

Tests (the tester writes them):

- `tests/adapters/test_agent_launch_call_end.py` (new): criteria 1 to 3. `STARTERS = Starters(sudo_executable="/usr/bin/sudo", confine_executable="/opt/factory/bin/factory-confine", login_files=LoginFiles())`; `LIMIT = timedelta(seconds=30)`.
- No earlier test changes.

## Acceptance criteria

1. The time-limit reading (rows of one parametrized test, each a `CallEnd` with `printed=True` and `stderr=""`, read with `time_limit=LIMIT` and `STARTERS`, none raising; `timed_out` is `False` where a row names none). `os_user=None`, `exit_status=-9`, `duration=LIMIT`: `False`. `os_user=None`, `exit_status=None`, `duration=LIMIT`, `timed_out=True`: `True`. `os_user="agent"`, `exit_status=137`, `duration=LIMIT`: `True`. `os_user="agent"`, `exit_status=-9`, `duration=timedelta(seconds=31)`: `True`. `os_user="agent"`, `exit_status=137`, `duration=timedelta(seconds=29.9)`: `False`. `os_user="agent"`, `exit_status=0`, `duration=LIMIT`: `False`.
2. The refusals, read after the time-limit reading (rows of one parametrized test, each a `CallEnd` with `timed_out=False`, read with `time_limit=LIMIT` and `STARTERS`; `os_user` is the reading's argument, the other values the `CallEnd`'s fields). `printed=False`, `os_user="agent"`, `exit_status=1`, `duration=timedelta(seconds=1)`, `stderr="sudo: a password is required\n"`: raises `AgentRuntimeError` whose `detail` is `/usr/bin/sudo refused the agent run: sudo: a password is required`. `printed=False`, `os_user=None`, `exit_status=1`, `duration=timedelta(seconds=1)`, `stderr="factory-confine: landlock is not available\n"`: raises with `detail` `/opt/factory/bin/factory-confine refused the agent run: factory-confine: landlock is not available`. `printed=True`, `os_user="agent"`, `exit_status=137`, `duration=LIMIT`, the same `factory-confine:` stderr: raises with the same `detail` (the kill is read first). `printed=True`, `os_user="agent"`, `exit_status=0`, `duration=timedelta(seconds=1)`, the same stderr: returns `False`. `printed=False`, `os_user=None`, `exit_status=0`, `duration=timedelta(seconds=1)`, `stderr=""`: returns `False`.
3. `state_directory_error(Path("/state/runs"), PermissionError(13, "Permission denied"))` returns an `AgentRuntimeError` whose `detail` is `cannot write the state directory /state/runs: [Errno 13] Permission denied`.
4. Both runtimes behave as before: `tests/adapters/test_agent_launch.py`, `tests/adapters/test_agent_launch_login.py`, every `tests/adapters/test_claude_runtime*.py`, every `tests/adapters/test_opencode*.py`, `tests/test_agent_launch_search.py` and `tests/test_opencode_runtime_search.py` pass unchanged, the row `state-missing` of `tests/adapters/test_opencode_runtime.py::test_a_run_that_cannot_start_names_the_reason` included.
5. `make check` stays green.
6. docs: `docs/project-guide/agents.md`, *The shared launch module*: it also holds the reading of a call's end, `read_call_end` (the runtime's own `timeout` kill read as the time limit first, then the refusals of `sudo`, the write guard's wrapper and the login shell with that reading, a refusal raised as `AgentRuntimeError`), and `state_directory_error`, which both runtimes call; each runtime keeps its own process calls (`_start`, `_request_of`, the removal of the temporary folder, `version`), because the module imports no process module. *The opencode runtime*, the sentence that the state directory must exist: add that the Claude Code runtime creates it, and that the difference is deliberate, because the image creates `/state/runs`. `docs/decisions.md`, the entry *What the agent runtimes share lies in one module*: one line, dated with the story, that the reading of a call's end and the state-directory error moved there too, that the process calls stay in each runtime for the entry's own reason, and that the state directory's difference between the runtimes is kept on purpose (the feature's decisions 2 and 3). `README.md` and `docs/operator-guide.md`: none, nothing an operator or a newcomer sees changes.

## Smoke test

```bash
uv run python - <<'PY'
from datetime import timedelta
from pathlib import Path
from factory.adapters.agent_launch import CallEnd, LoginFiles, Starters, read_call_end, state_directory_error
from factory.domain.errors import AgentRuntimeError
starters = Starters(sudo_executable="/usr/bin/sudo", confine_executable="/opt/factory/bin/factory-confine", login_files=LoginFiles())
limit = timedelta(seconds=30)
def end(stderr, status):
    return CallEnd(stderr=stderr, printed=True, exit_status=status, duration=limit, timed_out=False)
print(read_call_end(end("", 137), time_limit=limit, os_user="agent", starters=starters))
print(read_call_end(end("", 0), time_limit=limit, os_user="agent", starters=starters))
try:
    read_call_end(end("factory-confine: landlock is not available\n", 137), time_limit=limit, os_user="agent", starters=starters)
except AgentRuntimeError as error:
    print(error.detail)
print(state_directory_error(Path("/state/runs"), PermissionError(13, "Permission denied")).detail)
PY
```
Expect: four lines, `True`, `False`, `/opt/factory/bin/factory-confine refused the agent run: factory-confine: landlock is not available` and `cannot write the state directory /state/runs: [Errno 13] Permission denied`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: `CallEnd`, `read_call_end` and `state_directory_error` are named with full signatures in `agent_launch`. `killed_at_limit` and `call_refusal` exist with the signatures the story assumes (checked in `agent_launch.py`). The runtime changes are stated for the reviewer, and `CallEnd` keeps `read_call_end` within `max-args`.
   - Criteria: each is testable by one parametrized or single test function. 1 covers both sides of the time-limit reading: `os_user` None vs set, `timed_out` True, a kill status vs status 0, and duration at, above and below the limit. 2 covers the refusal rules from the failing side (sudo, confine, and the kill read first) and the passing side (stderr ignored when the reply was printed and the call was not killed, empty stderr). 3 covers the error text. 4 pins the runtimes' behaviour through the existing tests, 5 is `make check`, and 6 is the docs criterion.
   - Smoke test: the command is runnable and uses only names the Interface defines. The `Expect:` line gives four checkable lines. It does not run pytest, so the `-q` rule does not apply.
   - Architecture: the sequence moves within the adapters layer. `agent_launch` imports nothing of `process`, and the runtimes keep their process calls. This follows the decision log entry cited in the feature's decisions 1 to 3.
   - Scope: the story is inside the feature's scope. It does not touch the state directory difference or the process calls, which the feature's "Out of scope" lists, and it changes no earlier test.
4. factory: started tests as self.
5. tester: Tests written for criteria 1 to 3. They fail because the names they test don't exist yet. Criteria 4 to 6 are covered by the existing tests, by `make check` and by the docs stage.

   - criterion 1: tests/adapters/test_agent_launch_call_end.py::test_a_call_end_is_read_as_timed_out_when_its_own_timeout_killed_it_at_the_limit. It has six rows, one per case the criterion lists: duration at the limit (30 s), above it (31 s) and below it (29.9 s), plus `os_user` None or set, `timed_out=True`, and status 0.
   - criterion 2: tests/adapters/test_agent_launch_call_end.py::test_a_call_end_raises_the_refusal_read_after_its_time_limit. It has five rows: sudo refused, the wrapper refused, a call that printed and was killed and is still read for refusals, a call that printed before the limit, and a call with empty stderr. A row with no refusal expects `False` back; a row with one expects `AgentRuntimeError` with exactly that `detail`.
   - criterion 3: tests/adapters/test_agent_launch_call_end.py::test_the_state_directory_error_names_the_directory_and_the_cause
   - criterion 4: no new test. The existing runtime and launch tests the criterion names stay unchanged.
   - criterion 5: `make check`. criterion 6: docs, not a test.

   Files created: tests/adapters/test_agent_launch_call_end.py, using `STARTERS` and `LIMIT` as the Interface gives them. A private helper `_refused_end` builds the `CallEnd` for each criterion 2 row. I did this because ruff's PLR0917 (more than 5 positional arguments) failed with the fields as separate parameters. No earlier test file was changed.

   Module the test run could not import: tests/adapters/test_agent_launch_call_end.py fails at import because `CallEnd`, `read_call_end` and `state_directory_error` are not yet in `factory.adapters.agent_launch` (ImportError while importing the test module). I ran `make test` once, before the lint fix. That fix only restructured the criterion 2 parameters, so the module still fails at the same import. `make lint` is green. I skipped the type check, as this stage says to.

   No criterion needed interpreting. Nothing is open.

   `lint`: lint: green (0.5 s)
   `test`: ERROR tests/adapters/test_agent_launch_call_end.py - ImportError while importing test module '/work/checkout/tests/adapters/test_agent_launch_call_end.py'.
