---
stage: tests
pr: 122
blocked: question
comments_seen: 2
round: 0
attempts: 0
---
# The instance's run

## Assignment (as of log entry 1)

Build the process that runs one instance. `main` reads the settings and runs the instance; an invalid environment, an unreadable token file and a repository URL without an owner and a name end the process with status 2, a time-stamped line and a machine stop, never with a traceback. `run_instance` reads the token, builds the boundaries (previous story), keeps one `Tick` for the whole run, so that the tick status lives in memory across ticks (F0006 decision 11, questionnaire 1, Q28), and hands a scheduler a `tick` callable that counts as activity only a handled event that is not `idle`: a standing stop, a capped event and an error are idle, so that the pause keeps growing while nothing changes (kept thing 16). The next story gives `factory-watch` the same settings. This story covers ST7.1 (the loop is the one `tick` callable) and the settings half of ST3.3's machine stop for an invalid environment, implements R25 and keeps kept thing 16. Later stories of this feature put the repository waiter, the preflight and the other machine checks into `build_tick` and `run_instance`; each states what it adds. A real container is the morning observation. The operator guide is told to install v1.1 only on a repository v1 has not worked in (decision 008 of factory-v2: v1.1 starts fresh and detects no v1 work item).

## Interface

`src/factory/entry/wiring.py` (extends the module)

```python
def build_tick(boundaries: Boundaries, settings: InstanceSettings) -> Tick: ...
def boundaries_from_environment(
    environ: Mapping[str, str], *, hosting: HostingService | None = None
) -> tuple[InstanceSettings, Boundaries]: ...
def machine_log(state_directory: Path, clock: Clock | None = None) -> FactoryLog: ...
def health_store(state_directory: Path) -> HealthStatusStore: ...
```

`src/factory/entry/run.py`

```python
def activity(outcome: TickOutcome) -> bool: ...
def activity_tick(tick: Tick) -> Callable[[], bool]: ...
def install_stop_handlers(stop: threading.Event) -> None: ...
def run_until_stopped(
    settings: InstanceSettings,
    stop: threading.Event | None = None,
    *,
    hosting: HostingService | None = None,
) -> None: ...
def run_instance(
    settings: InstanceSettings,
    *,
    sleep: Callable[[float], None],
    should_stop: Callable[[], bool],
    hosting: HostingService | None = None,
) -> None: ...
def main(
    environ: Mapping[str, str] | None = None,
    *,
    runner: Callable[[InstanceSettings], None] | None = None,
    state_directory: Path = STATE_DIRECTORY,
    clock: Clock | None = None,
) -> int: ...
```

Rules:

- `build_tick(boundaries, settings)` is `Tick(boundaries, settings.instance, handler_factory(boundaries, settings.instance, production_environment()))` (F0006-S0007), a new `Tick` on every call.
- Every reading of the settings in this story passes a file reader: `read_settings(environ, read_file=<the text of a file>)` (the first story), so that the image identity comes from the file `FACTORY_IMAGE_ID_FILE` names, `/opt/factory/image-id` by default. A missing or empty file is a `SettingsInvalid` like any other and ends the process with status 2; the tests put `FACTORY_IMAGE_ID_FILE`, naming a file in `tmp_path`, into every valid environment.
- `boundaries_from_environment(environ, hosting=None)` is `read_settings(environ, read_file=...)`, then `read_hosting_token(settings.token_file)`, then `build_boundaries(settings, token, hosting=hosting)`; it returns the settings and the boundaries. A `SettingsInvalid` from any of the three propagates.
- `activity(outcome)` is true exactly when `outcome.dispatch == "handled"` and `outcome.event` is not `None` and its `kind` is not `idle`. Every other outcome is idle: a tick that ended at a repository stop (`stopped` is set, no event), and a dispatch of `capped`, `error` or `reported`.
- `activity_tick(tick)` returns a function that calls `tick.run()` and returns `activity(<the outcome>)`; the same `Tick` serves every call, so its status is kept from one call to the next.
- `install_stop_handlers(stop)` makes the signals `SIGTERM` and `SIGINT` set `stop`.
- `run_until_stopped(settings, stop, hosting)` is the default runner of `main`: it makes a `threading.Event` when `stop` is `None`, installs the stop handlers on it, and calls `run_instance` with a sleep that calls `stop.wait(seconds)` as a statement and returns `None` (`stop.wait` itself is typed `(float | None) -> bool`, which `mypy --strict` refuses as a `Callable[[float], None]`), and with `stop.is_set` as `should_stop`.
- `run_instance` reads the token with `read_hosting_token(settings.token_file)` (a `SettingsInvalid` propagates), builds `build_boundaries(settings, token, hosting=hosting)`, one `build_tick(...)` for the whole run, a `CheckoutPreparer` and a `Scheduler(prepare=<the preparer's prepare>, tick=activity_tick(<that tick>), sleep=sleep, should_stop=should_stop, log=<the boundaries' log>)`, and calls its `run`.
- `main` calls `read_settings(environ if environ is not None else os.environ, read_file=...)` and then `runner(settings)` once (the default runner is `run_until_stopped`), and returns 0 when the runner returns. A `SettingsInvalid` from `read_settings` or from the runner ends differently (when `read_settings` raised, the runner is not called at all): the line `settings invalid: <variable>: <fault>` goes through `machine_log(state_directory, clock)` (a `TimestampedFactoryLog` at `state_directory / "factory.log"`, with `SystemClock()` when `clock` is `None`) and a `RepositoryStop(scope="machine", reason="preflight_failed", detail=<the message>, at=<the clock's now>)` is written through `health_store(state_directory)` (a `JsonHealthStatusFile` at `state_directory / "health.json"`), and `main` returns 2. Only `factory.entry.wiring` imports adapters (`tests/entry/test_wiring.py`), which is why `main` reaches the log and the health file through these two functions. The stop is added to the stops already in the file (a stop of the same reason is replaced), so that no stop in force is dropped. The stop is written directly: no boundaries exist yet.
- `python -m factory.entry.run` ends with `raise SystemExit(main())` under `if __name__ == "__main__":`.

Tests: `tests/entry/test_run.py`, `tests/entry/test_wiring_run.py`, `tests/test_run_module.py` (the source of `factory/entry/run.py`). The tests use the shared fixtures `remote`, `checkout`, `human`, `hosting`, `agent_runtime`, `boundaries`, `agent_home` and `clock`, a recording `sleep`, and for `run_instance` a settings object whose checkout, state directory and agent home lie in `tmp_path`, whose repository URL is the `remote` fixture, and whose token file holds `example-value`. The settings of the `run_instance` tests have a `claude_executable` that names a path in `tmp_path` that does not exist, so that no test starts the real `claude` once later stories put the preflight and its probe of an agent run into `build_tick`; the test of criterion 5 builds its `Tick` directly as `Tick(boundaries, "factory-1", handler_factory(boundaries, "factory-1", <a PATH and HOME mapping>))`, not through `build_tick`. The test of criterion 6 builds its settings like the `run_instance` tests (checkout and state directory in `tmp_path`, `agent_home` equal to the `agent_home` fixture), because later stories put the preflight, which writes its stamp into the state directory, and the agent user's `HOME`, the parent of `agent_home`, into `build_tick`.

## Acceptance criteria

1. `activity` is true for a `TickOutcome` with `dispatch == "handled"` and a `run` event.
2. `activity` is false for a handled `idle` event.
3. `activity` is false for `TickOutcome(stopped="fetch_failed")`, which has no event and no dispatch.
4. `activity` is false for a dispatch of `capped`, of `error` and of `reported`, so that a standing stop or a capped event does not keep the pause at 15 seconds.
5. `activity_tick` serves one `Tick` for every call: two calls over a remote whose started story fails twice in its handler leave `tick.status` with the error counted twice, not once.
6. `build_tick(boundaries, settings)` over a remote with one started story runs one stage in one `run()`: the outcome is `handled` for the event `run`, and `agent_runtime.requests()` holds one request whose `environment` equals `production_environment()`; two calls of `build_tick` return two different `Tick` objects; with settings whose instance is `factory-7`, the claim on the work item's branch names `factory-7`.
7. `boundaries_from_environment` with a valid mapping (the token file written in `tmp_path`) and `hosting` given returns settings equal to `read_settings` of the mapping with a `read_file` that reads the file (`Path.read_text`) and a `Boundaries` whose `settings` are those settings.
8. `boundaries_from_environment` raises `SettingsInvalid` naming `FACTORY_TOKEN_FILE` when the token file does not exist, and naming `FACTORY_INSTANCE` when the mapping has no instance, and naming `FACTORY_REPOSITORY_URL` for the URL `/srv/project.git` when `hosting` is not given.
9. `run_instance` on a missing checkout, with `hosting` given and `should_stop` true once the first sleep was recorded, clones the repository into `settings.checkout` (`origin/main` resolves there) and calls `sleep` exactly once with 30.0 seconds (the first iteration is idle, whatever the tick found).
10. `run_instance` raises `SettingsInvalid` naming `FACTORY_TOKEN_FILE` for a missing token file, before anything is cloned.
11. `install_stop_handlers` makes `SIGTERM` and `SIGINT` set the given event: after the call, `signal.raise_signal` of each sets a fresh event (the test restores the previous handlers).
12. `main` with an invalid environment (no `FACTORY_INSTANCE`) and the `clock` fixture as `clock` returns 2 without calling the runner, appends one line to `factory.log` that starts with a time stamp in the form `YYYY-MM-DDTHH:MM:SSZ` and then reads `settings invalid: FACTORY_INSTANCE`, and leaves a `health.json` that holds one stop with scope `machine`, reason `preflight_failed`, a detail that names `FACTORY_INSTANCE` and the `at` `clock.now()`.
13. `main` with `FACTORY_IMAGE_ID_FILE` naming a file that does not exist, or an empty one, returns 2 without calling the runner and writes the line `settings invalid: FACTORY_IMAGE_ID_FILE` after its time stamp; with a file that holds `build-7` the runner receives settings whose `image` is `build-7`.
14. `main` with an invalid environment keeps the stops already in force and replaces one of its own reason: with a `fetch_failed` stop and an older `preflight_failed` stop in `health.json` beforehand, the file afterwards holds the `fetch_failed` stop and exactly one `preflight_failed` stop, whose detail names `FACTORY_INSTANCE`.
15. `main` called without a mapping (its `state_directory` in `tmp_path`) reads `os.environ`: with `FACTORY_REPOSITORY_URL` set and `FACTORY_INSTANCE` removed through `monkeypatch` it returns 2 and writes the line `settings invalid: FACTORY_INSTANCE: ` followed by the fault.
16. `main` with a valid environment returns 0 and calls the runner exactly once with settings equal to `read_settings` of that environment with a `read_file` that reads the file.
17. A runner that raises `SettingsInvalid("FACTORY_TOKEN_FILE", "cannot read /run/secrets/hosting-token")` makes `main` return 2, write the line `settings invalid: FACTORY_TOKEN_FILE: cannot read /run/secrets/hosting-token`, and leave a `preflight_failed` machine stop whose detail names `FACTORY_TOKEN_FILE`; the process does not die with a traceback.
18. The source of `factory/entry/run.py` ends with `raise SystemExit(main())` under `if __name__ == "__main__":`.
19. `run_until_stopped` with its stop event already set returns at once and clones nothing: `settings.checkout` does not exist afterwards (the event's `is_set` is the loop's `should_stop`; the test restores the signal handlers).
20. `run_until_stopped(settings)` without a stop event, for settings whose token file does not exist, installs its own handlers for `SIGTERM` and `SIGINT` (`signal.getsignal` of each differs from the handler before the call) and raises `SettingsInvalid` naming `FACTORY_TOKEN_FILE` (the test restores the previous handlers).
21. `run_until_stopped(settings, stop, hosting=fake)` pauses on the stop event: with a `threading.Event` subclass whose `wait(timeout)` records the timeout, sets the event and returns `True`, and settings like those of criterion 9 (a missing checkout), the event's `wait` is called exactly once, with 30.0, and `run_until_stopped` then returns (the test restores the signal handlers).
22. `run_instance` keeps one `Tick` for the whole run (F0006 decision 11): with the name `build_tick` in `factory.entry.run` (which imports it from `factory.entry.wiring`) wrapped through `monkeypatch` by a recorder that calls the original, a run with `hosting` given and `should_stop` true once the third sleep was recorded calls it exactly once.
23. make check stays green.
24. docs: `docs/operator-guide.md` explains that an invalid environment, an unreadable token file and a repository URL without an owner and a name end the process with status 2 and a machine stop (the health check then fails), and says to install v1.1 only on a repository v1 has not worked in, or whose v1 work items are archived or discarded (decision 008), because nothing detects them; `docs/decisions.md` records why one `Tick` is kept for the whole run (its status lives in memory) and why only a handled event that is not `idle` counts as activity.

## Demo

```bash
uv run python -c "
from factory.application.tick import TickOutcome
from factory.entry.run import activity
print(activity(TickOutcome(stopped='fetch_failed')), activity(TickOutcome(dispatch='capped')))
"
```
Expect: one line, `False False`.

```bash
uv run python -c "
import tempfile, pathlib
from factory.entry.run import main
d = pathlib.Path(tempfile.mkdtemp())
print(main({'FACTORY_REPOSITORY_URL': '/srv/project.git'}, state_directory=d))
print((d / 'factory.log').read_text().strip().split(' ', 1)[1])
"
```
Expect: three lines: the time-stamped line the factory writes (it starts with a time stamp in the form `YYYY-MM-DDTHH:MM:SSZ` and then reads `settings invalid: FACTORY_INSTANCE: ` followed by the fault), then `2`, then the same line without the time stamp.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `wiring.py` and `run.py` signatures are concrete, and each rule (`build_tick`, `boundaries_from_environment`, `activity`, `activity_tick`, stop handlers, `run_until_stopped`, `run_instance`, `main`, the module end) is stated precisely enough to build from. Only `factory.entry.wiring` imports adapters, and `main` reaches the log and the health file through `machine_log` and `health_store`.
   - Criteria: each is testable by one test function. Every rule has its failing side: the invalid environment in 12–15 and 17 (including the unreadable image file in 13), the missing token and instance and the URL without an owner and a name in 8 and 10, the idle outcomes in 2–4, and the stops kept and replaced in 14. The Interface comments on the 30.0-second first pause, the `stop.wait` adapter, one `Tick` per run and the stop's union with existing stops are tested by 9, 21, 22 and 14.
   - Demo: both commands are runnable. The second is consistent because `TimestampedFactoryLog.line` also writes the stamped line to stdout, which gives the three lines in the `Expect:`. Each expectation is checkable against the output.
   - Architecture: the code lands in `factory.entry` (`run.py`, `wiring.py`), and the adapters stay behind the wiring module. The layering rule holds.
   - Scope: it is within F0010's scope (ST7.1, the settings half of ST3.3, decision 5), and nothing in the story falls under "Out of scope".
3. tester: wrote red tests for criteria 1–22 as the coder's specification. `make lint` is green. `make test` stops at collection on the two entry test modules, because `factory.entry.run` and the new names in `factory.entry.wiring` do not exist yet.

   Criterion → test:
   - criteria 1–4: tests/entry/test_run.py::test_only_a_handled_event_that_is_not_idle_counts_as_activity. One parametrized test with six rows: handled-run, handled-idle, repository-stop, capped, error, reported.
   - criterion 5: tests/entry/test_run.py::test_the_activity_tick_keeps_one_tick_and_its_error_counts_across_calls. It installs no agent definitions, so the run handler raises `AgentDefinitionMissing` before any claim is pushed. The remote state stays the same, which lets the one error entry reach a count of 2.
   - criterion 6: tests/entry/test_wiring_run.py::test_build_tick_runs_one_stage_in_the_production_environment_under_its_instance. Its settings name instance `factory-7`, and the test reads the claim from the remote work-item branch.
   - criterion 7: tests/entry/test_wiring_run.py::test_boundaries_from_environment_reads_the_settings_and_builds_their_boundaries
   - criterion 8: tests/entry/test_wiring_run.py::test_boundaries_from_environment_refuses_an_invalid_environment. Parametrized: missing token file, no instance, and the URL `/srv/project.git` without `hosting`.
   - criterion 9: tests/entry/test_run.py::test_run_instance_clones_a_missing_checkout_and_pauses_thirty_seconds_after_it
   - criterion 10: tests/entry/test_run.py::test_run_instance_refuses_a_missing_token_file_before_it_clones
   - criterion 11: tests/entry/test_run.py::test_the_stop_handlers_set_the_event_on_sigterm_and_sigint. Parametrized over SIGTERM and SIGINT; the `restored_signals` fixture puts the old handlers back.
   - criterion 12: tests/entry/test_run.py::test_main_refuses_an_environment_without_an_instance_with_a_line_and_a_machine_stop
   - criterion 13: tests/entry/test_run.py::test_main_refuses_a_missing_or_empty_image_identity_file (parametrized: missing, empty) and tests/entry/test_run.py::test_main_hands_the_runner_the_image_identity_of_the_file (`build-7`).
   - criterion 14: tests/entry/test_run.py::test_main_keeps_the_stops_in_force_and_replaces_its_own
   - criterion 15: tests/entry/test_run.py::test_main_without_a_mapping_reads_the_process_environment
   - criterion 16: tests/entry/test_run.py::test_main_runs_a_valid_environment_once_and_returns_zero
   - criterion 17: tests/entry/test_run.py::test_main_turns_a_settings_fault_of_the_runner_into_a_line_and_a_machine_stop
   - criterion 18: tests/test_run_module.py::test_the_run_module_ends_by_exiting_with_the_status_of_main. It compares `ast.unparse` of the module's last statement.
   - criterion 19: tests/entry/test_run.py::test_run_until_stopped_with_its_event_set_returns_and_clones_nothing
   - criterion 20: tests/entry/test_run.py::test_run_until_stopped_installs_its_own_handlers_and_refuses_a_missing_token_file
   - criterion 21: tests/entry/test_run.py::test_run_until_stopped_pauses_on_its_stop_event. It uses a `RecordingEvent` subclass whose `wait` records the timeout, sets the event and returns True.
   - criterion 22: tests/entry/test_run.py::test_run_instance_builds_one_tick_for_the_whole_run. It wraps `factory.entry.run.build_tick` through monkeypatch and stops after the third sleep.
   - criteria 23 and 24 (make check, docs) need no test.

   Files created: tests/entry/test_run.py, tests/entry/test_wiring_run.py, tests/test_run_module.py.

   Names the test runner could not import: the module `factory.entry.run` (`activity`, `activity_tick`, `install_stop_handlers`, `run_until_stopped`, `run_instance`, `main`), and in `factory.entry.wiring` the functions `build_tick`, `boundaries_from_environment` and `health_store`. `machine_log` is not imported by any test; `main` reaches it. tests/test_run_module.py fails with FileNotFoundError until `src/factory/entry/run.py` exists.

   Setup choices worth knowing:
   - The `run_instance` and `run_until_stopped` tests pass the fake `hosting` in criterion 19 too. Without it, `build_boundaries` would refuse the local remote's URL, which names no owner and no name.
   - Their settings use a checkout at `tmp_path/instance-checkout`, a state directory at `tmp_path/instance-state` (created by the fixture), the `agent_home` fixture, a `claude_executable` path that does not exist, and a token file holding `example-value`.
   - The stamp is matched as `YYYY-MM-DDTHH:MM:SSZ` followed by a space, the separator the second demo command relies on.

   Open: none.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: implementation committed (ba63be9). Two tests from the tester can't pass against the existing tick, and I have not edited them (R9). Everything else in `make check` is green (lint, types, layers, sast, secrets, licenses, the other 20 new tests, coverage 99.5 %).

   Built:
   - `src/factory/entry/run.py`: `activity`, `activity_tick`, `install_stop_handlers`, `run_until_stopped`, `run_instance`, `main`, and the closing `raise SystemExit(main())`.
   - `src/factory/entry/wiring.py`: `build_tick`, `boundaries_from_environment`, `machine_log`, `health_store`, plus two helpers that `main` needs because only the wiring may import adapters: `read_environment_settings` (`read_settings` with the UTF-8 file reader) and `system_clock` (gives the stop's `at` when `clock` is `None`). `build_boundaries` now gets its log and health file through `machine_log`/`health_store`.
   - `src/factory/domain/stops.py`: the private `_with_stop` from `application/stops.py` became `HealthStatus.with_stop`. `main` and `StopService.raise_stop` now share it instead of keeping two copies.

   Questions (I recommend option a for both):

   1. `tests/entry/test_run.py::test_the_activity_tick_keeps_one_tick_and_its_error_counts_across_calls` (criterion 5). The test installs no agent definitions and expects the run handler to raise `AgentDefinitionMissing`. But `PipelineLoader._require_agents` (`src/factory/application/pipeline_loading.py:49`) checks the agent home while it loads the definition. A missing agents directory therefore ends each tick at a `pipeline_definition_invalid` repository stop, with no dispatch, and `tick.status.errors` stays empty. Options:
      (a) The test installs the agents (`install_agents`) and queues an agent runtime run that raises, or uses some other failure inside the handler, so the run dispatches and errors twice.
      (b) The test builds the `Tick` with a handler factory whose `run` handler always raises, as `tests/application/test_tick.py` does with `Failing`.
      (c) Change the loader to stop checking agents at load time. I advise against it: that is existing behaviour outside this story.

   2. `tests/entry/test_wiring_run.py::test_build_tick_runs_one_stage_in_the_production_environment_under_its_instance` (criterion 6). The test reads the claim from the tip of the work item's branch after the stage has completed. A completed stage releases its claim, and the tip's state is `stage='tests'` with `claim=None`, so `state.claim is not None` fails. The rest of the test passes: `handled` `run`, one request in `production_environment()`, two different `Tick` objects. Options:
      (a) Read the instance from the claim commit, the first factory commit on the branch after the start, rather than from the tip.
      (b) Read it from a fake agent request or the journal, if the instance appears there.
      (c) Drop the instance check from this test.

   Refactor step: not done yet. It comes after the tests are fixed and `make check` is green.
5. human (pull request comment, 2026-10-16): 1 (a): the test installs the agents with `install_agents` and queues an agent runtime run that raises inside the handler, so each tick dispatches and the error count grows across the calls; the loader stays as it is.
   2 (a): the test reads the instance from the claim commit (the first factory commit on the branch after the start), not from the tip, where a completed stage has released its claim; the instance check stays.
   The tester makes both changes and nothing else. End with `tests` and name exactly these two changes.
6. coder: the human's answer (entry 5) calls for two test changes. The tester makes both and nothing else; I left the tests and the code alone.
   1. In `tests/entry/test_run.py::test_the_activity_tick_keeps_one_tick_and_its_error_counts_across_calls`, install the agents with `install_agents` and queue an agent runtime run that raises inside the run handler. That way each of the two ticks dispatches and `tick.status` counts the error twice. The loader stays as it is.
   2. In `tests/entry/test_wiring_run.py::test_build_tick_runs_one_stage_in_the_production_environment_under_its_instance`, read the instance `factory-7` from the claim commit, the first factory commit on the work item's branch after the start, not from the branch tip, where the completed stage has already released its claim. The instance check stays.
   The implementation in ba63be9 stays as it is. The refactor step and the final `make check` come once the ticket returns from the tester.
7. tester: tester (approved test change): I made both changes from entry 5, but change 1 does not give the result the criterion expects. This replaces my earlier `doing`, which I sent before `make test` finished.

   Changes made (nothing else touched):
   1. tests/entry/test_run.py::test_the_activity_tick_keeps_one_tick_and_its_error_counts_across_calls: the test now installs the agents with `install_agents` for the roles of `PIPELINE_YAML`. It queues two `ScriptedRun`s that each write to `../outside.md`, so `FakeAgentRuntime.run` raises `AgentRuntimeError` inside the run handler. New `COMPLETED` constant and its imports.
   2. tests/entry/test_wiring_run.py::test_build_tick_runs_one_stage_in_the_production_environment_under_its_instance: the test now reads the work item at the claim commit, the first commit of `git rev-list --reverse main..<branch>` in the bare remote, and still checks `claim.instance == "factory-7"`. `run_git` is now imported. This test was not among the failures.

   `make lint`: green. `make test`: the only failure it reported is change 1. Run on its own, that test fails at `[entry] = tick.status.errors` with `ValueError: too many values to unpack (expected 1)`. The two ticks leave more than one error entry, not one entry with count 2. Probable cause, not verified: the first tick pushes its claim before the run raises, so the second tick fails at a different point and gets a different error key.

   Question: how should criterion 5's test get the same error twice?
   (a) Keep the setup and check that the error count across all entries reaches 2, without requiring a single entry.
   (b) Build the `Tick` with a handler factory whose run handler always raises the same error, as tests/application/test_tick.py does with `Failing`. Nothing is pushed, so both ticks hit the same error key.
   (c) Keep the single-entry check and change the code so that a claim this instance already holds leads to the same error on the second tick.
   I recommend (b): it tests exactly what criterion 5 says (one `Tick` kept across calls, and its error count growing) without depending on how the claim behaves.
