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
  instance: vm
  stage: intake
  started_at: '2026-11-01T09:12:14.222772Z'
  lease_duration: 60
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
