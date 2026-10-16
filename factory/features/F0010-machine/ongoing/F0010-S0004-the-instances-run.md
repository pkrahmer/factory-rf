---
stage: ready
pr: null
blocked: null
comments_seen: 0
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
