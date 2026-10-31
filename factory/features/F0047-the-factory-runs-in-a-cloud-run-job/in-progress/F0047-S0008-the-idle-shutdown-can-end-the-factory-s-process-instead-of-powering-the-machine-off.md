# The idle shutdown can end the factory's process instead of powering the machine off

## Description

The idle shutdown (F0045-S0008) switches the machine off after `FACTORY_IDLE_SHUTDOWN_MINUTES` of idle ticks, through `sudo -n /usr/bin/systemctl poweroff`. On a VM that ends the bill until the operator starts the machine again. In a Cloud Run job there is no `systemctl` and no `sudo`: the call is refused, the factory logs the refusal and runs on, and the job is billed until its task timeout. An execution of a job ends when its command ends, so the job's equivalent of switching the machine off is ending `factory-run` with exit status 0. This story adds that choice: `FACTORY_IDLE_SHUTDOWN_ACTION`, `poweroff` (the default, as today) or `exit`. With `exit` the idle shutdown asks the factory's own loop to stop, the same way a `SIGTERM` does: the scheduler ends after the tick in progress and `factory-run` returns 0. The job is started again by its schedule or by the operator (`gcloud run jobs execute`), as a VM is started again by its operator. Unchanged: the default, `SystemctlPowerOff`, the idle rule (which outcomes count, when the stretch starts again), the log line `idle shutdown: idle for <n> minutes, powering the machine off`, and every other setting. Left to S0006: the start script sets `exit` where the job gives no value.

## Interface

`factory.domain.settings` (domain): `IDLE_SHUTDOWN_ACTION_VARIABLE = "FACTORY_IDLE_SHUTDOWN_ACTION"` and the field `InstanceSettings.idle_shutdown_action: Literal["poweroff", "exit"] = "poweroff"`; unset or blank is `poweroff`, `poweroff` and `exit` are accepted, anything else is `SettingsInvalid(FACTORY_IDLE_SHUTDOWN_ACTION, "is neither poweroff nor exit")`. The action is read whether the idle shutdown is on or not; with `FACTORY_IDLE_SHUTDOWN_MINUTES` 0 it has no effect.

`factory.adapters.power_off` (adapters): `class ProcessExit(PowerOff)` with `__init__(request_stop: Callable[[], None])`; `power_off` calls `request_stop` once and returns. It raises nothing of its own.

`factory.entry.wiring` (entry): `idle_shutdown_of(settings, boundaries, request_stop: Callable[[], None] | None = None) -> IdleShutdown | None`. With minutes 0: `None`, as today. With `poweroff`: `SystemctlPowerOff()`, as today. With `exit`: `ProcessExit(request_stop)`; `exit` without a `request_stop` is a `ValueError("the idle shutdown's exit needs a way to stop the loop")`.

`factory.entry.run` (entry): `run_instance` gains `request_stop: Callable[[], None] | None = None` and hands it to `idle_shutdown_of`; `run_until_stopped` passes its event's `set`, so the idle shutdown and the signal handlers stop the same loop. `main` returns 0 after the loop ends this way, as after a `SIGTERM`.

Tests (the tester writes them): `tests/domain/test_settings_idle_shutdown_action.py`, `tests/adapters/test_process_exit.py`, `tests/entry/test_wiring_idle_shutdown_action.py`, `tests/entry/test_run_idle_exit.py` (the scheduler with the suite's scripted ticks and a manual clock, no sleep). `tests/entry/test_wiring_idle_shutdown.py`, `tests/entry/test_run_idle_shutdown.py`, `tests/application/test_idle_shutdown.py` and `tests/adapters/test_power_off.py` pass unchanged.

## Acceptance criteria

1. With `FACTORY_IDLE_SHUTDOWN_ACTION` unset the settings, `idle_shutdown_of` and the power switch are those of before this story (rows: minutes 0 gives `None`, minutes 30 gives an `IdleShutdown` whose `power` is a `SystemctlPowerOff`).
2. `FACTORY_IDLE_SHUTDOWN_ACTION` is read, rows of one test: unset and blank give `poweroff`; `poweroff` and `exit` give themselves; `Exit`, `stop` and `exit now` are refused as `is neither poweroff nor exit`; `exit` with minutes 0 is accepted.
3. `ProcessExit.power_off` calls its `request_stop` exactly once per call and raises nothing.
4. `idle_shutdown_of` with minutes 30 and `exit` and a `request_stop` gives an `IdleShutdown` whose `power` is a `ProcessExit` that calls it; with `exit` and no `request_stop` it raises the `ValueError` of the Interface; with minutes 0 and `exit` it gives `None`.
5. The loop: `run_instance`'s scheduler with idle ticks on a manual clock, minutes 1 and `exit`, stops after the tick that ends a one-minute idle stretch; the log holds `idle shutdown: idle for 1 minutes, powering the machine off`; no tick runs after it; a non-idle tick before the limit starts the stretch again, as today.
6. `main` with a runner that ends through the idle exit returns 0.
7. With `poweroff` the loop is not stopped by the idle shutdown: a refused power-off logs `the factory runs on` and the next tick runs, as before this story.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`: the variable in the configuration table, and in the idle shutdown's section a paragraph *In a job*: `exit` ends `factory-run` with status 0 after the limit, which ends the job's execution; the job's schedule or the operator starts it again; a VM keeps `poweroff`. `docs/project-guide/stage-environment.md` or the guide file that names the idle shutdown: `ProcessExit` beside `SystemctlPowerOff`. `docs/decisions.md`: an entry *In a job the idle shutdown ends the process*, from the feature's decision 18. `README.md`: none.

## Smoke test

```bash
uv run python -c "
from factory.adapters.power_off import ProcessExit
calls = []
ProcessExit(lambda: calls.append('stop')).power_off()
print(calls)
"
```
Expect: one line, `['stop']`

```bash
uv run python -c "
from factory.domain.settings import read_settings, SettingsInvalid
env = {'FACTORY_REPOSITORY_URL': 'https://example.invalid/o/r.git', 'FACTORY_INSTANCE': 'vm', 'FACTORY_CLAUDE_HOME': '/x/claude'}
print(read_settings(env).idle_shutdown_action, read_settings({**env, 'FACTORY_IDLE_SHUTDOWN_ACTION': 'exit'}).idle_shutdown_action)
try:
    read_settings({**env, 'FACTORY_IDLE_SHUTDOWN_ACTION': 'stop'})
except SettingsInvalid as error:
    print(error)
"
```
Expect: two lines, `poweroff exit` and a message that names `FACTORY_IDLE_SHUTDOWN_ACTION` and `is neither poweroff nor exit`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
