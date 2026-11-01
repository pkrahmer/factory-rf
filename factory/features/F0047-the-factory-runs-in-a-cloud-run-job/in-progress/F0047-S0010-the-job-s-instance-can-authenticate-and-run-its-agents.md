---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 491
comments_read: [6556021304]
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
- number: 6
  speaker: human
  kind: comment
  at: '2026-11-01T09:18:54.669850Z'
  stage: tests
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-01T09:19:12.694260Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-01T09:25:29.142773Z'
  stage: tests
  run: bb1c2562fc694066a678ee8b613094a1
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-01T09:25:49.562208Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-01T09:40:05.214748Z'
  stage: doing
  run: d4ed25846562424da45e9e626b271dd9
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-01T09:40:25.706425Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-01T09:41:08.467249Z'
  stage: review
  run: 8e482822f26448cbabff84f96f362dc8
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-01T09:41:29.021596Z'
  stage: docs
- number: 14
  speaker: documenter
  kind: result
  at: '2026-11-01T09:42:03.346645Z'
  stage: docs
  run: d3f23c9647ea4be88dc91d45d37da04d
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-01T09:42:23.733200Z'
  stage: smoke-test
- number: 16
  speaker: smoke-tester
  kind: result
  at: '2026-11-01T09:42:48.830785Z'
  stage: smoke-test
  run: 273c8bcb49cf4bc0a8c75bebefa7bb5f
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
6. 2026-11-01 human: Answer: (a). Add `EXIT_LINE = "idle shutdown: idle for 1 minutes, ending the factory's process"` to `tests/entry/test_run_idle_exit.py` and use it in the assertions of `test_the_idle_exit_stops_the_loop_after_the_tick_that_ends_the_stretch` and `test_run_until_stopped_ends_through_the_idle_exit_with_its_own_event`; `LINE` stays for the poweroff tests. Each test keeps its name and checks the same thing; the changed line is the decision of the human this story carries (decision 21). Run `make test` once more after the `endswith` change.
7. factory: started tests as vm.
8. tester: Made the change from the human's answer (a) in `tests/entry/test_run_idle_exit.py`. I added `EXIT_LINE = "idle shutdown: idle for 1 minutes, ending the factory's process"` and used it in the line-count assertions of `test_the_idle_exit_stops_the_loop_after_the_tick_that_ends_the_stretch` and `test_run_until_stopped_ends_through_the_idle_exit_with_its_own_event`. Both tests keep their names and check the same thing. `LINE` still covers the poweroff tests. The `exit` row of the new idle-line test now uses `EXIT_LINE` too. I ran `make test` once, as the answer asked. It was red only for the reasons below, and the `endswith` check on the poweroff row now passes. `make lint` is green.

   Criterion → test:
   criterion 1: tests/test_vm_job_start.py::test_the_steps_run_in_order_and_factory_run_replaces_the_script (unchanged)
   criterion 2: tests/test_vm_job_start_instance.py::test_the_code_step_installs_the_checkout_s_helper_between_the_checkout_and_uv
   criterion 3: tests/test_vm_job_start_instance.py::test_the_code_step_stops_the_script_on_a_missing_ref_or_a_failed_helper_install (rows no-ref, helper-install-fails)
   criterion 4: tests/test_vm_job_start_instance.py::test_only_runc_and_the_helper_are_installed_under_usr_local_bin
   criterion 5: tests/adapters/test_opencode_runtime_runs_folder.py::test_a_run_makes_its_missing_state_directory_and_writes_its_configuration_there; tests/adapters/test_opencode_runtime.py::test_a_run_that_cannot_start_names_the_reason[state-a-file] (the old row `state-missing`, changed under the human's leave)
   criterion 6: tests/application/test_idle_shutdown.py::test_the_idle_line_names_the_action (rows given, default); tests/entry/test_run_idle_exit.py::test_the_idle_line_says_what_the_action_does (rows exit, poweroff)

   Files created (in the earlier run): tests/test_vm_job_start_instance.py, tests/adapters/test_opencode_runtime_runs_folder.py.
   Earlier test files changed: tests/vm_support.py (the new option `failing_install_target` of `run_job_start`, which the Interface allows); tests/adapters/test_opencode_runtime.py (only the leave's row); tests/entry/test_run_idle_exit.py (`EXIT_LINE` in the two tests, under the human's answer of entry 6, plus the new test); tests/application/test_idle_shutdown.py (new test added).

   Modules the test run could not import: none. Red as intended:
   - the three `exit` tests in test_run_idle_exit.py, because the code still logs the poweroff text;
   - `IdleShutdown(action=...)` raises `TypeError`;
   - the script makes no `install` call for the helper (criteria 2, 3 and 4);
   - the opencode runtime raises `NotADirectoryError` for a state path that is a file, and `AgentRuntimeError` for a missing state directory.

   `lint`: lint: green (0.2 s)
   `test`: FAILED tests/adapters/test_opencode_runtime.py::test_a_run_that_cannot_start_names_the_reason[state-a-file] - NotADirectoryError: [Errno 20] Not a directory: '/tmp/pytest-of-factory/pytest-0/popen-...
9. factory: started doing as vm.
10. coder: Made the failing tests pass. I changed no tests. `make check` is green (`test: green (187.8 s)`, `check: green`).

    What I built:
    - `vm/job-start.sh`: step `code` now runs `install -m 0755 "$code/vm/git-credential-factory" "$prefix/usr/local/bin/git-credential-factory" || failed code`. It comes right after the `checkout --detach` line and before step `tools`. A one-line comment above it says why (the factory's git has no other credential). The smoke grep counts `1`.
    - `src/factory/adapters/opencode_runtime.py`: new `_make_state_directory`, which does `mkdir(parents=True, exist_ok=True)` and turns an `OSError` into `state_directory_error`, the same pattern as `ClaudeCodeRuntime._make_state_directory`. `run` calls it before the `try`/`finally` that writes and removes the run's files.
    - `src/factory/application/idle_shutdown.py`: `IdleShutdown.__init__` takes `action: str = "powering the machine off"`, and the log line uses it.
    - `src/factory/entry/wiring.py`: `idle_shutdown_of` passes `action="ending the factory's process"` with `exit`, and nothing with `poweroff`.

    Main choice: the directory is made before the `try`/`finally`, not inside `_write_files`. I tried it inside first. When the state path is a file, the `finally`'s `files.remove()` then fails on `unlink` with `NotADirectoryError`, which hides the `AgentRuntimeError` (the `state-a-file` row failed this way). Before the `try` there are no run files to clean up yet, and the order matches the Claude Code runtime.

    Rejected: building the idle shutdown in the wiring with `functools.partial` and an optional `action`. Two explicit `IdleShutdown(...)` calls read more plainly.

    Refactor pass: I read the diff. Besides the `partial` change above, I only reworded a docstring line that was too long. Nothing else needed changing.

    Noticed, not touched:
    - The `OSError` branch of `OpencodeRuntime._write_files` (`opencode_runtime.py:625-626`) is no longer covered. The test row that reached it now fails earlier, at the `mkdir`. The branch can still happen (permissions, a full disk), so I kept it. Overall coverage is still 99.5 %.
    - I did not run `make duplicates`.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
11. factory: started review as vm.
12. reviewer: no findings

    What I checked:
    - Criteria 1 to 6. Each has a test, and each test checks what its criterion says:
      - 1: `tests/test_vm_job_start.py` is not in the diff.
      - 2: the test pins the helper's one `install` call: its argv, and that it comes after `checkout --detach` and before the first `uv` call.
      - 3: one parametrized test with the rows no-ref and helper-install-fails. Both rows check no `podman` and no `factory-run`. The no-ref row also checks that no `install` names the helper's target.
      - 4: exactly `{runc, git-credential-factory}` under `<prefix>/usr/local/bin`.
      - 5: a missing nested `empty-state/runs` is made and the config file is written inside it; a state path that is a file fails with `cannot write the state directory`.
      - 6: rows of one test in both the application and the entry tests (given/default, exit/poweroff).
    - The Interface's failing sides are tested: a failed helper `install`, and a state path that is a file, which raises `FileExistsError` from `mkdir(exist_ok=True)` and maps to `state_directory_error`.
    - Coder's journal entry 10: `make check` was green after the coder.
    - Architecture: the `mkdir` is in the adapter, `action` is a plain string in application, and the entry wiring picks it from `idle_shutdown_action`. No new tool call or dependency.
    - Security: no suppression markers or secrets. The shell line quotes its paths and goes through `failed code`.
    - Quality: `_make_state_directory` follows the same pattern as `ClaudeCodeRuntime`. It runs before the `try`/`finally` so the cleanup cannot hide the error, as entry 10 explains. The new test helper `_index` in `tests/test_vm_job_start_instance.py` finds a call by identity. `_first` in `tests/test_vm_job_start.py` finds one by name, so `_index` is not a copy of it.
    - The Description and the docs criterion match what was built.

    Earlier tests:
    - tests/adapters/test_opencode_runtime.py: the human's leave stated in the Description (the `state-missing` row becomes `state-a-file`). The `else` that writes the file is the least the row needs to make its state path a file.
    - tests/entry/test_run_idle_exit.py: the human's answer in journal entry 6 (`EXIT_LINE` in the two named tests). The new test is an addition.
    - tests/application/test_idle_shutdown.py: none needed. It only adds a test.
    - tests/vm_support.py: the story's Interface allows the new `failing_install_target` option of `run_job_start`. Earlier callers keep their behaviour because the default is `None`.
13. factory: started docs as vm.
14. documenter: Documented the three changes of the story; I found no contradiction between the Interface, the criteria and the code, so there are no findings. I changed only documents, so I did not run `make check`; the factory's checks decide.

    Files changed:
    - `docs/operator-guide.md`, *On Cloud Run*, *The steps*, step 8 `code`: it names the helper's install (`vm/git-credential-factory` to `/usr/local/bin/git-credential-factory`, mode 0755), the `job-start: code: failed` stop, and what the helper is for (the factory's git, the project's host only, with a pointer to *The hosting-service token*).
    - `docs/operator-guide.md`, *The idle shutdown*, *In a job*: the log line with `exit` is `…, ending the factory's process`. With `poweroff` it is unchanged.
    - `docs/project-guide/agents.md`, *The opencode runtime*: it made the old sentence "the state directory must exist (the runtime does not create it)" wrong. It now says the runtime makes its state directory as the Claude Code runtime does. It also says why the `mkdir` runs before the `try`/`finally`: the cleanup would otherwise hide the error. I did not touch the other mention of `/state/runs` in the image.
    - `docs/project-guide/watching.md`, the `IdleShutdown` rules: the log line takes `<action>`, with the default and what `idle_shutdown_of` passes for each setting.
    - `docs/decisions.md`: one line in *A bare job becomes an instance at start* (the job installs the helper of its own code ref, because the factory's git has no other credential). I also changed the one sentence in *In a job the idle shutdown ends the process* that said the log line stays `powering the machine off` with `exit`, because it is now false.

    Cross-read and found current: README.md (the docs criterion says none), the table row of `FACTORY_IDLE_SHUTDOWN_ACTION` and the 0-status line in the operator guide, the Cloud Run list of variables and the step list otherwise.

    Not touched: nothing stale that is unrelated to this story.

    I did not run the smoke-test commands; they are the smoke tester's.

    `check`: check: green (not run again: passed on tree 4abef89d0f05 at 2026-11-01T09:36:47Z)
    `secrets`: secrets: green (2.8 s)
    `documents`: documents ok
15. factory: started smoke-test as vm.
16. smoke-tester: I ran the two smoke-test commands as written, in order, from the repository root. Both met their `Expect:` lines. There are no findings.

    Command 1: `grep -c 'usr/local/bin/git-credential-factory' vm/job-start.sh`
    ```
    1
    ```
    Met `Expect: 1` (exit status 0).

    Command 2: the `uv run python -c "…"` snippet, which calls `IdleShutdown(..., action='ending the factory\'s process')._power_off()`
    ```
    Bytecode compiled 4164 files in 72ms
    idle shutdown: idle for 1 minutes, ending the factory's process
    ```
    Met `Expect: one line, idle shutdown: idle for 1 minutes, ending the factory's process` (exit status 0). The `Bytecode compiled …` line is uv's own status message on stderr, not the program's output. The snippet printed exactly one line, and it is the expected text.

    Criteria read again against what the smoke test showed and against the code it points at:
    - 2: the helper's install is at `vm/job-start.sh:125`. It comes after `checkout --detach` (line 123) and before `step tools` (line 127), with `-m 0755`, the source `$code/vm/git-credential-factory` and `|| failed code`.
    - 4: the only other `install` under `$prefix/usr/local/bin` is `runc` (line 93).
    - 5: `OpencodeRuntime` makes its state directory with `mkdir(parents=True, exist_ok=True)` (`src/factory/adapters/opencode_runtime.py:618`).
    - 6: the default `action` is still `"powering the machine off"` (`src/factory/application/idle_shutdown.py:21`). `idle_shutdown_of` passes the exit text only for `exit` (`src/factory/entry/wiring.py:591-593`).

    Nothing the smoke test showed contradicts a criterion. I did not run `make check`; the factory runs the stage's checks.
