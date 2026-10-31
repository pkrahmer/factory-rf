---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 487
comments_read: [6550196915]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-31T22:33:39.553128Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-31T22:33:39.558909Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-31T22:34:00.002935Z'
  stage: intake
  run: 4db00bd8845f4b288a5435c9653de70a
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-31T22:34:20.215645Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-31T22:42:06.777368Z'
  stage: tests
  run: 488b33b7863046f08de2fece06cc5d30
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-31T22:42:26.877155Z'
  stage: doing
- number: 7
  speaker: coder
  kind: question
  at: '2026-10-31T22:49:25.368963Z'
  stage: doing
  run: 60e6493e4827420b8b58f396030e0a38
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-10-31T22:50:40.475978Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-31T22:50:58.215813Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-31T22:51:17.054603Z'
  stage: doing
  run: b267ee26d52443dca5981e6de34d9b03
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-31T22:51:37.143297Z'
  stage: tests
- number: 12
  speaker: tester
  kind: result
  at: '2026-10-31T22:57:33.487299Z'
  stage: tests
  run: f80deaa61f9e4e9aa42acbcbc91d9759
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-31T22:57:53.894727Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-31T23:03:58.497955Z'
  stage: doing
  run: 36b2379c630d49f698e8f0cb792e8399
---

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
1. 2026-10-31 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: concrete modules and signatures (`factory.domain.settings` constant and field, `factory.adapters.power_off.ProcessExit(request_stop)`, `factory.entry.wiring.idle_shutdown_of` with the optional `request_stop`, `factory.entry.run.run_instance` / `run_until_stopped`). I checked them against the code: `idle_shutdown_of` and `run_instance` exist as the story describes, and `power_off.py` holds `SystemctlPowerOff(PowerOff)`. The only behaviours the Interface states are the default, the validation, the `ValueError` and "returns 0", and each has a criterion.
   Criteria: each can be tested by one test function. Criteria 1 and 7 cover the unchanged default and the `poweroff` side. Criterion 2 covers the setting on both sides (unset, blank, both values, three refused values, `exit` with minutes 0). Criterion 3 covers `ProcessExit`. Criterion 4 covers the wiring in all three branches, including the `ValueError` and minutes 0. Criterion 5 covers the loop, the log line, no tick after the stop, and the stretch restarting. Criterion 6 covers `main` returning 0. Criteria 8 and 9 are the two closing ones.
   Smoke test: both blocks are plain `uv run python -c` snippets and none runs pytest, so the `-q` rule does not apply. `read_settings` exists, and each `Expect:` line gives output that can be compared (`['stop']`; `poweroff exit` plus a message naming the variable and `is neither poweroff nor exit`).
   Architecture: the domain holds the setting, the adapter holds `ProcessExit` as an implementation of the `PowerOff` interface, and the entry layer wires it and passes the event's `set`. This matches the layering in `CLAUDE.md`. No new dependency is added.
   Scope: this is S0008 of F0047, listed in the feature's Scope and in decision 18. It names the earlier idle-shutdown tests that must pass unchanged, so no other story's test is changed.
4. factory: started tests as vm.
5. tester: I wrote the tests for criteria 1 to 7. Each one fails because the code it needs does not exist yet, not because of a broken test. `make lint` is green. I skipped the type check, as this stage says to.

   Criterion → test:
   - criterion 1: tests/entry/test_wiring_idle_shutdown_action.py::test_without_an_action_the_idle_shutdown_powers_the_machine_off (rows: minutes 0 gives None, minutes 30 gives SystemctlPowerOff; the setting reads `poweroff`)
   - criterion 2: tests/domain/test_settings_idle_shutdown_action.py::test_the_idle_shutdown_action_is_read_or_refused (rows: unset, empty, blank, poweroff, exit, exit with minutes 0, Exit, stop, exit now)
   - criterion 3: tests/adapters/test_process_exit.py::test_each_power_off_requests_the_stop_once
   - criterion 4: tests/entry/test_wiring_idle_shutdown_action.py::test_the_exit_action_stops_the_loop_it_is_given (rows: exit with a stop gives a ProcessExit that calls it; exit without a stop raises the ValueError; exit with minutes 0 gives None)
   - criterion 5: tests/entry/test_run_idle_exit.py::test_the_idle_exit_stops_the_loop_after_the_tick_that_ends_the_stretch (rows: idle at 0:59 does not stop the loop and idle at 1:00 does; a non-idle tick at 0:45 starts the stretch again, so 1:44 runs on and 1:45 stops. Each row checks that the log line appears once and that no scripted tick runs after the stop.)
   - criterion 6: tests/entry/test_run_idle_exit.py::test_main_returns_zero_after_the_idle_exit_ends_the_loop
   - criterion 7: tests/entry/test_run_idle_exit.py::test_a_refused_power_off_does_not_stop_the_loop (a `sudo` stand-in first on PATH exits 1; the log holds `the factory runs on`, the next tick runs, and the stop is never requested)

   How the loop tests work: `run_instance` runs with a real clone of the `remote` fixture and the fake hosting service. Two things are patched in `factory.entry.run`, as `tests/entry/test_run.py` already does:
   - `build_tick` returns a scripted tick. Each run moves the manual clock to its step's time and returns IDLE or OTHER from `power_support`.
   - `build_boundaries` calls the real one, then sets the boundaries' clock and log (`machine_log`) to the manual clock.

   The test passes `request_stop=stop.set`, and `should_stop` returns `stop.is_set() or tick.exhausted`, so an idle shutdown that never stops the loop ends with the script rather than hanging the test. There is no real sleep.

   Rejected:
   - A test that only checks the `IDLE_SHUTDOWN_ACTION_VARIABLE` constant. No criterion asks for it.
   - Moving the `settings`/`token_file` fixtures out of `tests/entry/test_run.py`. My module has its own small `instance_settings` fixture, so I changed no earlier test file.

   Files created: tests/domain/test_settings_idle_shutdown_action.py, tests/adapters/test_process_exit.py, tests/entry/test_wiring_idle_shutdown_action.py, tests/entry/test_run_idle_exit.py.

   Modules pytest could not import: tests/adapters/test_process_exit.py and tests/entry/test_wiring_idle_shutdown_action.py, both because `ProcessExit` does not exist yet in `factory.adapters.power_off`. The other two modules import, and their tests fail on the missing `InstanceSettings.idle_shutdown_action` (AttributeError, or SettingsInvalid not raised) and on `run_instance()` not accepting `request_stop`.

   Process note: my one `make test` run went to the background because I gave it the default timeout. I waited for it to finish and read its result. I ran `make lint` in the foreground.

   `lint`: lint: green (0.2 s)
   `test`: ERROR tests/entry/test_wiring_idle_shutdown_action.py - ImportError while importing test module '/work/checkout/tests/entry/test_wiring_idle_shutdown_action.py'.
6. factory: started doing as vm.
7. coder: Question: an earlier story's test, `tests/entry/test_run.py::test_run_instance_hands_the_idle_shutdown_of_its_settings_to_the_activity_tick`, conflicts with this story's Interface. May the tester change that test's stand-in?

   The conflict: the test patches `factory.entry.run.idle_shutdown_of` with a local `recording_of(given, boundaries)` that takes exactly two arguments. The Interface says `run_instance` "hands [request_stop] to `idle_shutdown_of`". So the call `idle_shutdown_of(settings, boundaries, request_stop)` fails in both rows of that test:
   ```
   E   TypeError: test_run_instance_hands_the_idle_shutdown_of_its_settings_to_the_activity_tick.<locals>.recording_of() takes 2 positional arguments but 3 were given
   FAILED tests/entry/test_run.py::test_run_instance_hands_the_idle_shutdown_of_its_settings_to_the_activity_tick[0-None]
   FAILED tests/entry/test_run.py::test_run_instance_hands_the_idle_shutdown_of_its_settings_to_the_activity_tick[30-limit1]
   ```
   These two are the only failures in `make test`. All four new test modules pass, and lint, types, layers, sast, secrets and licenses are green. The story's list of tests that must pass unchanged does not name `tests/entry/test_run.py`. The test is not mine, though, and the change is not the standing leave to move a shared helper, so I need your leave.

   Options:
   - (a) The tester widens `recording_of` to `(given, boundaries, request_stop=None)` and passes `request_stop` on to `original_of`. The test keeps its name and still checks the same thing. I would choose this.
   - (b) `run_instance` calls `idle_shutdown_of(settings, boundaries)` when `request_stop` is None and passes three arguments only otherwise. That shapes production code around a test's stand-in; I reject it.
   - (c) Pass `request_stop` some other way, for example a closure set on the boundaries. That goes against the Interface.

   What I built (left in the working tree; `make check` is red only on those two rows):
   - `src/factory/domain/settings.py`: `IDLE_SHUTDOWN_ACTION_VARIABLE`, the type `IdleShutdownActionName`, and the field `InstanceSettings.idle_shutdown_action = "poweroff"`. The value is read through the existing `_one_of`, so unset or blank gives `poweroff` and anything else is refused with `is neither poweroff nor exit`.
   - `src/factory/adapters/power_off.py`: `ProcessExit(PowerOff)`, which calls `request_stop` on each `power_off`.
   - `src/factory/entry/wiring.py`: `idle_shutdown_of(settings, boundaries, request_stop=None)`. A private `_idle_power` picks `SystemctlPowerOff()` or `ProcessExit(request_stop)`, and raises the Interface's `ValueError` for `exit` without a `request_stop`.
   - `src/factory/entry/run.py`: `run_instance(..., request_stop=None)` hands it on, and `run_until_stopped` passes `event.set`. I also added `build_boundaries` to `__all__`, because the new `tests/entry/test_run_idle_exit.py` patches `run_module.build_boundaries` and mypy refuses an attribute the module does not export. `build_tick` is exported for the same reason.

   Main choice: the action is picked in the entry wiring (`_idle_power`), not inside `IdleShutdown`. The application layer keeps knowing only the `PowerOff` interface. I rejected a new stop interface in `factory.application`, because `PowerOff` already says what the idle shutdown needs.

   Refactor: I read my diff and found nothing to change.

   Journal: nothing in the journal changed the task's meaning, so `## Description` is unchanged.

   Noticed, not touched: nothing else.
8. 2026-10-31 human: Answer: (a). The tester widens `recording_of` in `tests/entry/test_run.py::test_run_instance_hands_the_idle_shutdown_of_its_settings_to_the_activity_tick` to `(given, boundaries, request_stop=None)` and passes `request_stop` on to `original_of`; the test keeps its name and checks the same thing. The leave covers that stand-in's signature and nothing else in the file. End with `tests` and name the change.
9. factory: started doing as vm.
10. coder: Test change for the tester, as the human answered in entry 8 (option a): in `tests/entry/test_run.py::test_run_instance_hands_the_idle_shutdown_of_its_settings_to_the_activity_tick`, widen the local stand-in `recording_of(given, boundaries)` to `recording_of(given, boundaries, request_stop=None)` and pass `request_stop` on to `original_of`. The test keeps its name and checks the same thing. The leave covers this signature and nothing else in the file.

    Code: I changed nothing this round. The implementation from entry 7 is already committed (bb2ef5948):
    - `src/factory/domain/settings.py`
    - `src/factory/adapters/power_off.py`
    - `src/factory/entry/wiring.py`
    - `src/factory/entry/run.py`

    `run_instance` calls `idle_shutdown_of(settings, boundaries, request_stop)` at `src/factory/entry/run.py:126`. That three-argument call is what the stand-in refuses. When I ran `make test` in entry 7, the two rows of that test were its only failures; everything else in `make check` was green. Once the stand-in is widened, `make check` should be green, but no check has been run since that change. The coder runs it when the work item comes back.

    Journal: the answer changes no meaning of the task, so `## Description` is unchanged.

    Noticed, not touched: nothing else.
11. factory: started tests as vm.
12. tester: Tester: I made the test change the human approved in entry 8 and the coder named in entry 10, and nothing else.

    Change, in tests/entry/test_run.py::test_run_instance_hands_the_idle_shutdown_of_its_settings_to_the_activity_tick: the local stand-in `recording_of(given, boundaries)` now takes `(given, boundaries, request_stop: Callable[[], None] | None = None)` and passes `request_stop` on to `original_of`. The test keeps its name and checks the same thing. No other line in the file changed. Why: `run_instance` now calls `idle_shutdown_of(settings, boundaries, request_stop)`, as the Interface says, and the old two-argument stand-in refused that call with a TypeError in both rows.

    Criterion → test: unchanged from entry 5. This round adds or removes no test.

    Files changed: tests/entry/test_run.py (the earlier test file, under the human's leave in entry 8). Files created: none. Modules the test run could not import: none.

    `make test`: test: green (164.7 s), total coverage 99.56 %.
    `make lint`: lint: green (0.2 s).

    `lint`: lint: green (0.2 s)
    `test`: test: green (163.4 s)
13. factory: started doing as vm.
14. coder: Coder: I changed no code this round. The tester widened the `recording_of` stand-in in `tests/entry/test_run.py` (entry 12). Those two rows were the only failures in entry 7, and `make check` is now green: `test: green (164.6 s)` with coverage at 99.56 %, then `check: green`.

    What I built (committed in bb2ef5948):
    - `src/factory/domain/settings.py`: `IDLE_SHUTDOWN_ACTION_VARIABLE`, the type `IdleShutdownActionName` (`Literal["poweroff", "exit"]`) and the field `InstanceSettings.idle_shutdown_action = "poweroff"`. The value is read through the existing `_one_of` helper with the fault `is neither poweroff nor exit`, so unset or blank gives `poweroff`.
    - `src/factory/adapters/power_off.py`: `ProcessExit(PowerOff)`. Each call to `power_off` calls `request_stop` once.
    - `src/factory/entry/wiring.py`: `idle_shutdown_of(settings, boundaries, request_stop=None)`. The private `_idle_power` returns `SystemctlPowerOff()` for `poweroff` and `ProcessExit(request_stop)` for `exit`. For `exit` without a `request_stop` it raises the Interface's `ValueError`.
    - `src/factory/entry/run.py`: `run_instance(..., request_stop=None)` passes `request_stop` to `idle_shutdown_of`, and `run_until_stopped` passes `event.set`. The idle exit therefore stops the same loop the signal handlers stop, and `main` returns 0 as it does after a `SIGTERM`. I added `build_boundaries` to `__all__` because the new loop test patches it on the module, and mypy refuses an attribute the module does not export.

    Main choice: the action is picked in the entry wiring, as one more implementation of the existing `PowerOff` interface. `IdleShutdown` in the application layer is unchanged. I rejected a separate stop interface in `factory.application`: `PowerOff` already says what the idle shutdown needs, and the idle rule and its log line stay exactly as they were.

    Refactor: I read the whole diff against main and found nothing to change.

    Journal: the human's answer in entry 8 changed only a test stand-in, not the meaning of the task, so I left `## Description` unchanged.

    Noticed, not touched: the log line still says `powering the machine off` when the action is `exit`. The Description requires that line unchanged, so it stays as it is.

    `check`: check: green
    `duplicates`: duplicates: 1 new, 41 known, 1 gone
