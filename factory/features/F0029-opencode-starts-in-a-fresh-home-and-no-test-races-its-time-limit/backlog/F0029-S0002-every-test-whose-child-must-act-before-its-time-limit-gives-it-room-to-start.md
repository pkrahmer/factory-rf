# Every test whose child must act before its time limit gives it room to start

## Description

`tests/adapters/test_claude_runtime_confinement.py::test_the_temporary_folder_is_empty_at_each_call_and_gone_after_the_run[time-limit]` failed under a loaded `make check` on 2026-10-19 and passes alone. Its output was `assert 0 == 1` at `len(calls) == len(steps)`. Its limit of 3 s killed the probe before the probe wrote its call record: the probe starts through the real `factory-confine` and then a Python stand-in. Seventeen more tests give a child that must do something before its limit kills it (write a record or a pid file, print a line, finish a first call) one to five seconds. A loaded machine can fail each of them in the same way, or leave it checking nothing. This story gives all of them one limit with room, `ROOMY_LIMIT` (ten seconds) in a new shared module `tests/time_limits.py`, and one elapsed bound, `ROOMY_BOUND_SECONDS` (25), below what every stand-in waits that the limit must end. Each changed test keeps its name and what it checks. Two are rewritten so that what they check no longer races the clock: the resume's leftover limit is read from its request, and the one-second limit of a project command is read from the request handed to the process. Tests whose child need not start to be killed keep their short limits, and no production code changes. The rule in `CLAUDE.md` is the human's change 2 after this story.

## Interface

No module under `src/factory/` changes; the coder has nothing to build.

`tests/time_limits.py` (new, a support module at the root of `tests/`):

```python
"""Time limits for tests whose child must act before the limit ends it."""

from datetime import timedelta
from typing import Final

# Under `make check` pytest runs on every core; on 2026-10-19 a stand-in started through
# `factory-confine` needed more than three seconds to write its first record.
ROOMY_LIMIT: Final[timedelta] = timedelta(seconds=10)
# An upper bound on a run that ROOMY_LIMIT ends, with room above it; a stand-in the limit must
# end waits longer, so a missed kill fails.
ROOMY_BOUND_SECONDS: Final[int] = 25
```

- `ROOMY_BOUND_SECONDS` is at least ten seconds above `ROOMY_LIMIT`, and every stand-in wait that a changed test relies on being cut short is above `ROOMY_BOUND_SECONDS` (30 or 60 s).

The changed tests, by the feature's decision 9, by the tester only and nothing else in those modules. Each keeps its name and its assertions, with `ROOMY_LIMIT` for its limit and `ROOMY_BOUND_SECONDS` for its elapsed bound where it has one:

- `tests/adapters/test_claude_runtime_confinement.py`: the row `time-limit` of `test_the_temporary_folder_is_empty_at_each_call_and_gone_after_the_run` (and the test's bound), and `test_a_wrapper_line_of_a_call_killed_at_its_time_limit_is_a_runtime_error`. `SHORT_LIMIT` stays for `test_a_removal_that_outlasts_its_time_limit_is_ended_and_changes_no_result`, with the comment the feature gives.
- `tests/adapters/test_claude_runtime_provider_limit.py`: `test_a_call_past_its_time_limit_ends_time_limit_though_it_named_the_limit`.
- `tests/adapters/test_claude_runtime_resume.py`: `test_first_call_ended_by_the_time_limit_is_not_resumed`, both rows of `test_call_killed_by_the_time_limit_has_no_model_duration`, the row `resume ended by the time limit` of `test_model_duration_of_a_resumed_run_adds_the_known_calls` (`timedelta(seconds=5)` becomes `ROOMY_LIMIT`), and the rewrite of `test_resume_gets_what_is_left_of_the_time_limit_and_unknown_measures` (criterion 4).
- `tests/adapters/test_opencode_budget.py`: `test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`.
- `tests/adapters/test_opencode_resume_session.py`: the rows `timed-out-with-events` and `timed-out-resumed-without-events` of `test_a_run_resumes_the_named_session_and_reports_the_first_session_of_its_events`, and its last assertion; the module's `SHORT_LIMIT` goes.
- `tests/adapters/test_opencode_events.py`: `test_a_call_past_its_time_limit_ends_by_time_limit_without_measures`; the module's `SHORT_LIMIT`, `ELAPSED_BOUND` and their comment go.
- `tests/adapters/test_opencode_confinement.py`: the row `time-limit` of `test_through_the_wrapper_the_temporary_root_is_empty_after_the_run` (and the test's bound); the module's `SHORT_LIMIT`, its comment and the import of `BOUND_SECONDS` go.
- `tests/adapters/test_opencode_sudo_time_limit.py`: `test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login`, all four rows through the module's limit; `PAST_LIMIT_SECONDS` becomes `ROOMY_LIMIT.total_seconds() + 1.5`; the module's `LIMIT`, its comment and the imports of `BOUND_SECONDS` and `timedelta` go.
- `tests/adapters/test_process.py`: `test_child_is_killed_at_the_time_limit` and `test_grandchild_is_killed_with_the_child_at_the_time_limit`, with the comment the feature gives.
- `tests/adapters/test_process_streaming.py`: `test_child_is_killed_at_the_time_limit_and_no_later_line_is_passed` and `test_child_that_closed_its_streams_is_killed_at_the_time_limit`; `RETURNS_WITHIN_SECONDS` stays for its other tests.
- `tests/adapters/test_make_commands.py`: `test_command_reaching_its_time_limit_is_killed`, with the comment the feature gives, and the rewrite of `test_time_limit_of_one_second_runs` (criterion 5).

Unchanged: every other test, the shipped tester lesson (`claude/agents/tester.md`, `template/CLAUDE.md`) and its pinned texts, `tests/conftest.py`, `tests/run_process_recorder.py`, the stand-ins.

Tests (the tester writes them): `tests/time_limits.py`, `tests/test_time_limits.py`, and the changes above.

## Acceptance criteria

1. The shared limits (rows of one parametrized test in `tests/test_time_limits.py`): `ROOMY_LIMIT` is `timedelta(seconds=10)` and `ROOMY_BOUND_SECONDS` is 25. `ROOMY_BOUND_SECONDS - ROOMY_LIMIT.total_seconds()` is at least 10. Each of `WAIT_SECONDS` of `tests/adapters/test_claude_runtime_confinement.py`, `tests/adapters/opencode_stand_in.py`, `tests/adapters/test_opencode_resume_session.py` and `tests/adapters/test_opencode_events.py` (30 each) is above `ROOMY_BOUND_SECONDS`. `PAST_LIMIT_SECONDS` of `tests/adapters/test_opencode_sudo_time_limit.py` is above `ROOMY_LIMIT.total_seconds()` and below `ROOMY_BOUND_SECONDS`.
2. The runtimes' killed runs (the tests the Interface names in `test_claude_runtime_confinement.py`, `test_claude_runtime_provider_limit.py`, `test_claude_runtime_resume.py` but the rewrite, `test_opencode_budget.py`, `test_opencode_resume_session.py`, `test_opencode_events.py`, `test_opencode_confinement.py` and `test_opencode_sudo_time_limit.py`): each runs its call with `ROOMY_LIMIT`, still ends `time_limit` (or raises the wrapper's line), and still sees what the child did before the kill: the probe's one call record with an empty temporary folder, the confine stand-in's line, the stand-in's `arguments.json`, one call and no resume, two calls (the budget stop and its resume, in the budget test and in the resumed run whose resume the limit ended), the session of the events printed before the kill, an empty temporary root after the wrapper's killed run, the session `ses_a` and the login `api_key` of the step printed before the kill under `sudo`. The rows of the `sudo` test that end `died`, or whose `sudo` ends after `PAST_LIMIT_SECONDS`, end as before. Where it bounds the elapsed time, the bound is `ROOMY_BOUND_SECONDS`.
3. The process runner's and `make`'s killed children (the tests the Interface names in `test_process.py`, `test_process_streaming.py`, and `test_command_reaching_its_time_limit_is_killed`): each runs its child with `ROOMY_LIMIT`, still sees `started` in the output or reads the pid file the child wrote, still finds that process gone, and bounds the elapsed time by `ROOMY_BOUND_SECONDS`.
4. The resume gets what is left (the rewritten `test_resume_gets_what_is_left_of_the_time_limit_and_unknown_measures`, with the `recorder` fixture of `tests/conftest.py` given no results, so both calls run for real): the first call waits 2 s and prints a budget stop with 5 turns and a cost of 3.0, and the resume waits 60 s. With `ROOMY_LIMIT` the run ends `time_limit` after two calls, with turns, cost and tokens `None` and a duration of at least 2 s, within `ROOMY_BOUND_SECONDS`. The resume's request (the second of `recorder.requests`) has a time limit of at least `ROOMY_LIMIT` less the elapsed seconds and at most `ROOMY_LIMIT` less 2 s; the whole limit again (10 s) fails the test.
5. A one-second limit is taken (the rewritten `test_time_limit_of_one_second_runs`): with `make_commands.run_process` replaced through `monkeypatch` by `Recorder` of `tests/run_process_recorder.py`, holding one result (exit status 0, `timed_out` false, a duration of 0), `run("check", time_limit=timedelta(seconds=1))` passes. The one request handed to the process has the time limit `timedelta(seconds=1)`. `test_time_limit_of_zero_or_less_is_rejected` stays as it is, the refused side of the same rule.
6. `make check` stays green.
7. docs: `docs/project-guide/processes-and-checks.md`, *Starting a process*, after its line on the tests and their helpers: a test whose child must act before its limit (write a record or a pid file, print a line, finish a first call) takes `ROOMY_LIMIT` (10 s) and `ROOMY_BOUND_SECONDS` (25) from `tests/time_limits.py`; a child that need not start to be killed may keep a shorter limit. `docs/decisions.md`: an entry *A test whose child must act before its time limit gets ten seconds*, dated with the story. Its reasons: three seconds failed under a loaded `make check` on 2026-10-19; a runtime's kill is measured from its own start, so a killed run still ends near the limit; the bound stays below every stand-in's wait, so a missed kill fails. Rejected: waiting for the child's record before the limit counts (the limit is the runtime's own); five seconds (barely more than the three that failed); changing the shipped tester lesson now (the ten seconds are this repository's measure). `docs/operator-guide.md` and `README.md`: none, nothing an operator or a newcomer does changes.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
umask 022
TMPDIR="$d" uv run pytest --no-header --tb=short -p no:cacheprovider -n 64 tests/test_time_limits.py tests/adapters/test_claude_runtime_confinement.py tests/adapters/test_claude_runtime_provider_limit.py tests/adapters/test_claude_runtime_resume.py tests/adapters/test_opencode_budget.py tests/adapters/test_opencode_resume_session.py tests/adapters/test_opencode_events.py tests/adapters/test_opencode_confinement.py tests/adapters/test_opencode_sudo_time_limit.py tests/adapters/test_process.py tests/adapters/test_process_streaming.py tests/adapters/test_make_commands.py > "$d/out" 2>&1
echo "exit $?"
grep -c -E '^(FAILED|ERROR) ' "$d/out"
```
Expect: two lines, `exit 0` and `0` (64 workers on fewer cores, the load under which the 3-second row failed)

```bash
grep -c 'SHORT_LIMIT' tests/adapters/test_opencode_resume_session.py tests/adapters/test_opencode_events.py tests/adapters/test_opencode_confinement.py
uv run -q python -c 'import sys; sys.path.insert(0, "tests"); from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT; print(ROOMY_LIMIT.total_seconds(), ROOMY_BOUND_SECONDS)'
```
Expect: four lines, `tests/adapters/test_opencode_resume_session.py:0`, `tests/adapters/test_opencode_events.py:0`, `tests/adapters/test_opencode_confinement.py:0` and `10.0 25`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
