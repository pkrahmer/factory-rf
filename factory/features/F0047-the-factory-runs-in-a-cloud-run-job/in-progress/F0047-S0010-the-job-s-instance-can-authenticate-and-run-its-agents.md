---
stage: tests
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 491
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-01T09:12:14.215994Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-01T09:12:14.222772Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-01T09:12:35.742473Z'
  stage: intake
  run: a1ff226589e34a8885da7c86b778a854
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-01T09:12:55.946974Z'
  stage: tests
- number: 5
  speaker: tester
  kind: question
  at: '2026-11-01T09:17:39.309797Z'
  stage: tests
  run: 4a03d00f71da4968b2b20b339b5e4393
  blocked: question
---

# The job's instance can authenticate and run its agents

## Description

`vm/job-start.sh` (S0006) ends in `exec factory-run`, but the feature acceptance F0047-A0001 showed with its smoke test that the instance it starts cannot work, for two reasons, and that one log line misleads in a job:

- **The credential helper.** The factory's git always takes its credential from `/usr/local/bin/git-credential-factory` (`git_environment` in `factory.entry.wiring`). `vm/setup.sh` installs that helper on a VM; the job script does not. In a job, git answers `not found` and `could not read Username`, so no fetch of a private project and no push can authenticate.
- **The runs folder.** The agent runtimes keep a run's files in `<state>/runs`. `ClaudeCodeRuntime` makes that folder; `OpencodeRuntime` writes its configuration file there without making it, and an earlier test (F0020-S0004, the row `state-missing`) pins that as an error. A job starts with an empty state at every start and runs opencode by default, so the preflight's `agent-run-probe` fails at every start; a fresh VM with opencode fails the same way.
- **The idle line.** With `FACTORY_IDLE_SHUTDOWN_ACTION=exit` (S0008) the log still says `powering the machine off`, although only the factory's process ends.

This story: the script installs the code checkout's helper (decided by the acceptance); the opencode runtime makes its runs folder as the Claude Code runtime does (the human, 2026-11-01, with a leave over F0020-S0004's row); and with `exit` the idle line says what happens (the human, 2026-11-01). Unchanged: the twelve steps of the script, their names and their order, every other message and exit status, `vm/setup.sh`, the Claude Code runtime, the idle rule and the `poweroff` line.

## Interface

`vm/job-start.sh` (shell): the step `code`, right after `git -C "$code" checkout --detach "$FACTORY_CODE_REF"` succeeded and before the step `tools`, installs the checkout's own helper:

```sh
install -m 0755 "$code/vm/git-credential-factory" "$prefix/usr/local/bin/git-credential-factory" || failed code
```

A failing `install` of the helper stops the script with `job-start: code: failed` and exit 1, and neither `podman` nor `factory-run` is called. No other file is installed under `<prefix>/usr/local/bin` besides `runc` and the helper.

`factory.adapters.opencode_runtime` (adapters): before it writes a run's files, `OpencodeRuntime` makes its state directory with `mkdir(parents=True, exist_ok=True)`, as `ClaudeCodeRuntime` does (`src/factory/adapters/claude_runtime.py`); an `OSError` of that `mkdir` (for example a file where the folder should be) is the same `state_directory_error` as an `OSError` of the write today.

`factory.application.idle_shutdown` (application): `IdleShutdown.__init__` gains `action: str = "powering the machine off"`; the log line is `idle shutdown: idle for <n> minutes, <action>`. `factory.entry.wiring.idle_shutdown_of` passes `"ending the factory's process"` with `exit` and nothing with `poweroff`.

Tests (the tester writes them): `tests/test_vm_job_start_instance.py` (through `tests/vm_support.py::run_job_start`; a stand-in `install` that fails only for the helper's target may be added to `tests/vm_support.py` as a new option of `run_job_start`, every earlier caller keeping its behaviour), `tests/adapters/test_opencode_runtime_runs_folder.py`, rows added to `tests/entry/test_run_idle_exit.py` and `tests/application/test_idle_shutdown.py`.

The leave over an earlier test (the human, 2026-11-01): in `tests/adapters/test_opencode_runtime.py::test_a_run_that_cannot_start_names_the_reason`, the row `state-missing` becomes a row whose state path is a file, which still fails with `cannot write the state directory <state>: `; nothing else in that file changes. `tests/test_vm_job_start.py` passes unchanged.

## Acceptance criteria

1. With every input given, the script prints exactly the twelve step lines of S0006 in their order (`tests/test_vm_job_start.py` passes unchanged).
2. The step `code` makes one `install` call with `-m 0755`, the source `<root>/factory/vm/git-credential-factory` and the target `<prefix>/usr/local/bin/git-credential-factory`, after the `git` call holding `checkout --detach` and before the first `uv` call.
3. Rows of one test: a `FACTORY_CODE_REF` that does not exist stops the script with `job-start: code: no ref <ref> in <url>` and exit 1, with no `install` call naming the helper's target; an `install` that fails for the helper's target stops it with `job-start: code: failed` and exit 1, with no `podman` and no `factory-run` call.
4. The recorded `install` calls name exactly two targets under `<prefix>/usr/local/bin`: `runc` and `git-credential-factory`.
5. An opencode run whose state directory does not exist makes it (parents included) and runs; its configuration file is written there. A state path that is a file fails with `AgentRuntimeError` whose detail starts `cannot write the state directory <state>: ` (the earlier row, changed under the leave).
6. The idle line, rows of one test: with `exit` and a limit of 1 minute, `idle shutdown: idle for 1 minutes, ending the factory's process`; with `poweroff`, `idle shutdown: idle for 1 minutes, powering the machine off`, as before.
7. `make check` stays green.
8. docs: `docs/operator-guide.md`, *On Cloud Run*, *The steps*: step 8 names the helper's install and what it is for (the factory's git, the project's host only; see *The hosting-service token*); *In a job* (the idle exit): the log line with `exit`. `docs/project-guide/agents.md`, *The opencode runtime*: it makes its state directory, as the Claude Code runtime does. `docs/decisions.md`, *A bare job becomes an instance at start*: one line that the job installs the helper of its own code ref, and why (the factory's git has no other credential). `README.md`: none.

## Smoke test

```bash
grep -c 'usr/local/bin/git-credential-factory' vm/job-start.sh
```
Expect: `1`

```bash
uv run python -c "
from datetime import timedelta
from factory.adapters.clock import ManualClock
from factory.application.idle_shutdown import IdleShutdown
class Power:
    def power_off(self): pass
class Log:
    def line(self, text): print(text)
from datetime import datetime, timezone
IdleShutdown(timedelta(minutes=1), ManualClock(datetime(2026, 1, 1, tzinfo=timezone.utc)), Power(), Log(), action='ending the factory\'s process')._power_off()
"
```
Expect: one line, `idle shutdown: idle for 1 minutes, ending the factory's process`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-11-01 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: concrete. Names the shell line for step `code` (placement after `checkout --detach` at vm/job-start.sh:123, before `tools`), `OpencodeRuntime`'s `mkdir(parents=True, exist_ok=True)` with its OSError mapping, `IdleShutdown.__init__(..., action: str = "powering the machine off")` and the exact log line, and `idle_shutdown_of` passing the exit text (the current code already routes `exit` through `_idle_power`). The leave over the F0020-S0004 row `state-missing` is stated with the human's date.
   Criteria: each is testable by one test function or one parametrized test. Each rule has both sides: ref missing and install failing (3), a missing directory made and a file in its place refused (5), `exit` and `poweroff` lines (6). Every Interface clause has a criterion: the install call (2), the exactly-two-targets rule (4), the twelve lines unchanged (1), the unchanged `poweroff` default (6). Criterion 7 and 8 are the closing ones.
   Smoke test: both commands are runnable. Grep: `vm/job-start.sh` has no helper line yet, so the count goes from 0 to 1 with the install line (the comments and messages carry no such path). The Python snippet uses the real constructor and `_power_off`, with `ManualClock` and the two stand-ins, and prints one line that can be compared. Neither runs pytest, so the `-q` rule does not apply.
   Architecture: the changes sit in the right layers: the `mkdir` in the adapter, the `action` text in application, its choice in the entry wiring, the script under `vm/` (the coder's write path). No new dependency or module.
   Scope: within the feature's scope (S0010 is listed, refined on 2026-11-01, decision 21). It leaves `vm/setup.sh`, the Claude Code runtime and the idle rule alone. The only change to an earlier test is the one the human's leave names.
4. factory: started tests as vm.
5. tester: Question: two earlier tests pin the old idle line for `exit`, and the story gives no leave to change them.

   In `tests/entry/test_run_idle_exit.py`, `LINE` is `"idle shutdown: idle for 1 minutes, powering the machine off"`. `test_the_idle_exit_stops_the_loop_after_the_tick_that_ends_the_stretch` and `test_run_until_stopped_ends_through_the_idle_exit_with_its_own_event` both run with `idle_shutdown_action="exit"` and assert `_log(settings).count(LINE) == 1`. Criterion 6 makes the `exit` line `…, ending the factory's process`, so once the code is in, both tests fail. The leave in the Description covers only the `state-missing` row of `tests/adapters/test_opencode_runtime.py`.

   Options:
   (a) Leave to add `EXIT_LINE = "idle shutdown: idle for 1 minutes, ending the factory's process"` to that file and use it in the assertions of those two tests. `LINE` stays for `test_a_refused_power_off_does_not_stop_the_loop` (poweroff) and for the new poweroff row. Each test keeps its name and checks the same thing.
   (b) Drop the line count from those two tests.
   (c) Something else.
   I would choose (a).

   Where I stopped: all tests for the criteria are written, `make lint` is green, and the one `make test` run failed for the right reasons. The only exception was the new entry test's poweroff row: log lines carry a timestamp, so I changed that check to `endswith` and have not run the tests again.

   Criterion → test:
   criterion 1: tests/test_vm_job_start.py::test_the_steps_run_in_order_and_factory_run_replaces_the_script (unchanged)
   criterion 2: tests/test_vm_job_start_instance.py::test_the_code_step_installs_the_checkout_s_helper_between_the_checkout_and_uv
   criterion 3: tests/test_vm_job_start_instance.py::test_the_code_step_stops_the_script_on_a_missing_ref_or_a_failed_helper_install (rows no-ref, helper-install-fails)
   criterion 4: tests/test_vm_job_start_instance.py::test_only_runc_and_the_helper_are_installed_under_usr_local_bin
   criterion 5: tests/adapters/test_opencode_runtime_runs_folder.py::test_a_run_makes_its_missing_state_directory_and_writes_its_configuration_there; tests/adapters/test_opencode_runtime.py::test_a_run_that_cannot_start_names_the_reason[state-a-file] (the row `state-missing` changed under the human's leave: the state path is now a file, and the id is renamed to match)
   criterion 6: tests/application/test_idle_shutdown.py::test_the_idle_line_names_the_action (rows given, default); tests/entry/test_run_idle_exit.py::test_the_idle_line_says_what_the_action_does (rows exit, poweroff)

   Files created: tests/test_vm_job_start_instance.py, tests/adapters/test_opencode_runtime_runs_folder.py.
   Files changed: tests/vm_support.py (new keyword `failing_install_target` of `run_job_start`; `install` exits 1 only when that path is among its arguments; every earlier caller keeps its behaviour, as the Interface allows); tests/adapters/test_opencode_runtime.py (only the leave's row); tests/application/test_idle_shutdown.py and tests/entry/test_run_idle_exit.py (new tests appended).
   Modules the test run could not import: none. The failures: `TypeError` for `IdleShutdown(..., action=...)`; no helper `install` call in the script; `NotADirectoryError` for a state path that is a file and `AgentRuntimeError` for a missing state directory in the opencode runtime; the exit line is still the poweroff text.
