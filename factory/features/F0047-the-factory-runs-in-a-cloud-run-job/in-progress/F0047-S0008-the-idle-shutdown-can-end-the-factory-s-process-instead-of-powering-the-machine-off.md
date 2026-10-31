---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 487
comments_read: [6550196915]
handed_over: approval
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
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-31T23:04:18.787389Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: result
  at: '2026-10-31T23:05:08.142441Z'
  stage: review
  run: 760c9f1438a4421a883a0332d075fb61
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-31T23:05:28.514966Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-31T23:05:45.234065Z'
  stage: doing
  run: f565e34fc2fa47189e321409d2d357e3
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-31T23:06:05.494442Z'
  stage: tests
- number: 20
  speaker: tester
  kind: result
  at: '2026-10-31T23:12:16.551436Z'
  stage: tests
  run: e2141de88bb04d91a4b24db43f53b960
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-31T23:12:36.823098Z'
  stage: doing
- number: 22
  speaker: coder
  kind: result
  at: '2026-10-31T23:18:49.845627Z'
  stage: doing
  run: 4262698d07ae405bb8abbe9313a3af37
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-31T23:19:10.028241Z'
  stage: review
- number: 24
  speaker: reviewer
  kind: result
  at: '2026-10-31T23:20:05.866248Z'
  stage: review
  run: 4206674c0ff446acb7538a875912dc5e
- number: 25
  speaker: factory
  kind: started
  at: '2026-10-31T23:20:26.078508Z'
  stage: docs
- number: 26
  speaker: documenter
  kind: result
  at: '2026-10-31T23:21:06.726286Z'
  stage: docs
  run: b42c61df599947ca9bd79f7d31936e6b
- number: 27
  speaker: factory
  kind: started
  at: '2026-10-31T23:21:27.443930Z'
  stage: smoke-test
- number: 28
  speaker: smoke-tester
  kind: result
  at: '2026-10-31T23:21:52.129255Z'
  stage: smoke-test
  run: dd4a2d13216d447d8a305872f460a5d3
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
8. `run_until_stopped` itself (not a stand-in runner) with minutes 1 and `exit`, scripted idle ticks on a manual clock and its own `stop` event: it returns after the tick that ends the one-minute idle stretch, with `stop` set by the idle shutdown, and no tick runs after it.
9. `make check` stays green.
10. docs: `docs/operator-guide.md`: the variable in the configuration table, and in the idle shutdown's section a paragraph *In a job*: `exit` ends `factory-run` with status 0 after the limit, which ends the job's execution; the job's schedule or the operator starts it again; a VM keeps `poweroff`. `docs/project-guide/stage-environment.md` or the guide file that names the idle shutdown: `ProcessExit` beside `SystemctlPowerOff`. `docs/decisions.md`: an entry *In a job the idle shutdown ends the process*, from the feature's decision 18. `README.md`: none.

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
15. factory: started review as vm.
16. reviewer: Reviewer, round 0. I read the diff against main (src/factory/adapters/power_off.py, src/factory/domain/settings.py, src/factory/entry/run.py, src/factory/entry/wiring.py, the four new test modules and the change to tests/entry/test_run.py) and the work item. Group 1 (acceptance criteria) has a gap, so I stopped there and did not judge groups 2 to 5. I went through every criterion and every rule of the Interface. Criteria 1 to 7 each have a test that checks what the criterion says. Criterion 2 covers both sides of the setting, criterion 4 covers all three branches of the wiring including the ValueError, and criterion 5 tests the limit at 0:59 and at 1:00. The factory's `make check` after the coder was green (entry 14).

    Findings:
    1. criterion 8 added: it needs its test. The gap is at src/factory/entry/run.py:96-98. The Interface's rule "`run_until_stopped` passes its event's `set`, so the idle shutdown and the signal handlers stop the same loop" is not tested. tests/entry/test_run_idle_exit.py::test_main_returns_zero_after_the_idle_exit_ends_the_loop calls `main` with a stand-in `runner` that calls `run_instance` with its own `request_stop`. The run_until_stopped tests in tests/entry/test_run.py never turn on the idle shutdown with `exit`. So deleting `request_stop=event.set` at line 97 would still pass every test, and in production `exit` would then fail with the ValueError in `idle_shutdown_of`. That call is the wiring that makes the story work in a job. Fix: the tester adds a test in tests/entry/test_run_idle_exit.py that calls `run_until_stopped(settings, stop, hosting=hosting)` with minutes 1 and `exit`. It reuses the module's `on_the_manual_clock` fixture and `_scripted` ticks, and checks that the call returns with `stop` set after the tick that ends the stretch, with no tick after it. No change under src/ is needed. I added this as criterion 8 in `## Acceptance criteria`; the two closing criteria are now 9 and 10.

    Earlier tests:
    - tests/entry/test_run.py: under the human's leave in journal entry 8. Only the `recording_of` stand-in's signature changed, widened to take `request_stop`, which it passes on to `original_of`. The test keeps its name and checks the same thing.
17. factory: started doing as vm.
18. coder: Coder, round 1: I changed no code. The reviewer's one finding (entry 16) is the new criterion 8, and it needs only its test. That test does not exist yet: `tests/entry/test_run_idle_exit.py` has no call to `run_until_stopped`.

    For the tester: criterion 8 needs a test in `tests/entry/test_run_idle_exit.py`. The test calls `run_until_stopped(settings, stop, hosting=hosting)` itself, not through a stand-in runner, with minutes 1 and `exit`, and reuses the module's `on_the_manual_clock` fixture and `_scripted` idle ticks. It checks that the call returns after the tick that ends the one-minute idle stretch, that `stop` is set by the idle shutdown, and that no scripted tick runs after it.

    Nothing under src/ needs to change: `run_until_stopped` already passes `request_stop=event.set` (`src/factory/entry/run.py:96-98`, committed in bb2ef5948). The code is unchanged since entry 14, where the coder's `make check` was green. I did not run `make check` this round.

    What I built (unchanged from entry 14): `src/factory/domain/settings.py`, `src/factory/adapters/power_off.py` (`ProcessExit`), `src/factory/entry/wiring.py` (`idle_shutdown_of` with `request_stop`, through `_idle_power`), and `src/factory/entry/run.py`.

    Main choice (unchanged): the action is chosen in the entry wiring, with `ProcessExit` as one more implementation of the existing `PowerOff` interface. I rejected a separate stop interface in `factory.application`.

    Refactor: none this round, because there is no new code.

    Journal: the reviewer added criterion 8 to `## Acceptance criteria`. The meaning of the task is unchanged, so I left `## Description` as it is.

    Noticed, not touched: the idle shutdown's log line still says `powering the machine off` with `exit`. The Description requires that line to stay as it is.
19. factory: started tests as vm.
20. tester: Tester, round 1: I wrote the test for criterion 8, the one the reviewer added (entry 16) and the coder named (entry 18). I changed nothing else.

    criterion 8: tests/entry/test_run_idle_exit.py::test_run_until_stopped_ends_through_the_idle_exit_with_its_own_event

    How it works: the test calls `run_until_stopped(settings, stop, hosting=hosting)` directly, with no stand-in runner. It uses minutes 1 and `exit`, the module's `on_the_manual_clock` fixture, and `_scripted` idle ticks at 0:30, 0:59, 1:00 and 1:30. It checks four things:
    - `stop` is set.
    - Exactly 3 ticks ran, so the tick that ends the stretch is the last one.
    - The script is not used up.
    - The log holds the idle-shutdown line once.

    `stop` is a small local event, `_ScriptBoundEvent`, whose `wait` returns at once and never sets the event. So `stop` can only be set by the idle exit through `request_stop=event.set`, and the loop needs no real time. If the exit is missed, the script runs out and `wait` raises, so the test fails instead of looping. The `restored_signals` fixture from tests/conftest.py puts back the handlers that `run_until_stopped` installs.

    Criteria 1 to 7: same tests as in entry 5. Criteria 9 and 10 (make check, docs) have no test of their own.

    Files changed: tests/entry/test_run_idle_exit.py (my own module from this story; one import added, the new event class and the new test). Files created: none. Earlier tests from other stories: none changed.

    Modules the test run could not import: none. The code is already in place (bb2ef5948), so the new test passes rather than failing first.
    `make test`: test: green (165.2 s), coverage 99.56 %. `make lint`: lint: green.

    `lint`: lint: green (0.2 s)
    `test`: test: green (163.4 s)
21. factory: started doing as vm.
22. coder: Coder, round 1: I changed no code. The reviewer's one finding (entry 16) was the new criterion 8, and it needed only a test. The tester wrote it in entry 20: `tests/entry/test_run_idle_exit.py::test_run_until_stopped_ends_through_the_idle_exit_with_its_own_event`. It passes against the code already committed in bb2ef5948, because `run_until_stopped` already passes `request_stop=event.set` (`src/factory/entry/run.py:96-98`). I ran `make check` this round and it is green: `test: green (165.0 s)`, total coverage 99.56 %, then `check: green`.

    What I built (unchanged since entry 14):
    - `src/factory/domain/settings.py`: `IDLE_SHUTDOWN_ACTION_VARIABLE`, the type `IdleShutdownActionName`, and the field `InstanceSettings.idle_shutdown_action`. The value is read through the existing `_one_of` helper.
    - `src/factory/adapters/power_off.py`: `ProcessExit(PowerOff)`.
    - `src/factory/entry/wiring.py`: `idle_shutdown_of(settings, boundaries, request_stop=None)`, which picks the power switch through the private `_idle_power`.
    - `src/factory/entry/run.py`: `run_instance(..., request_stop=None)`, with `run_until_stopped` passing `event.set`. I also added `build_boundaries` to `__all__`.

    Main choice (unchanged): the action is chosen in the entry wiring, with `ProcessExit` as one more implementation of the existing `PowerOff` interface. I rejected a separate stop interface in `factory.application`, because `PowerOff` already says what the idle shutdown needs.

    Refactor: I read the diff against main again and found nothing to change.

    Journal: the reviewer added criterion 8. That does not change what the task means, so I left `## Description` unchanged.

    Noticed, not touched: with `exit`, the idle shutdown still logs `powering the machine off`. The Description requires that line to stay as it is.

    `check`: check: green
    `duplicates`: duplicates: 1 new, 41 known, 1 gone
23. factory: started review as vm.
24. reviewer: Reviewer, round 1. I read the work item and `git diff main...HEAD -- . ':!factory'`: four files under `src/` (power_off.py, settings.py, run.py, wiring.py), the four new test modules, and the change to tests/entry/test_run.py. I went through groups 1 to 5 and found nothing that sends the work item back.

    Group 1: every criterion has a test, and each test checks what its criterion says.
    - Criteria 1 and 4 are covered in tests/entry/test_wiring_idle_shutdown_action.py, including the `ValueError` and the case of minutes 0.
    - Criterion 2 is in tests/domain/test_settings_idle_shutdown_action.py: unset, empty, blank, both accepted values, three refused values and `exit` with minutes 0, all rows of one test.
    - Criterion 3 is in tests/adapters/test_process_exit.py.
    - Criteria 5 to 8 are in tests/entry/test_run_idle_exit.py. Criterion 5 tests the one-minute limit on both sides (0:59 runs on, 1:00 stops) and the restart of the stretch after a non-idle tick (1:44 runs on, 1:45 stops).
    - Criterion 8, added in round 0, now calls `run_until_stopped` itself with its own event. That event's `wait` never sets it, so only `request_stop=event.set` at src/factory/entry/run.py:96-98 can stop the loop. Deleting that argument would make the test fail.
    - Every rule of the Interface has a test for the side that fails.
    - The factory's `make check` after the coder was green (entry 22).

    Group 2, architecture: the setting is in the domain. `ProcessExit` is in the adapters and inherits `PowerOff`. The choice of action is made in `factory.entry.wiring`. No import goes upward.

    Group 3, security: no markers, no strings built into shell commands, nothing new reaches a tool.

    Group 4, quality: the setting is read through the existing `_one_of`. The docstrings are present and accurate. The one new item in `make duplicates` is an unused `__call__` reported in src/factory/adapters/oauth_token.py, a file this story does not touch. The same `__call__` shows as gone under the label "method", so it is a known item listed under a different label.

    Group 5, work item hygiene: the journal explains the main choice (a second `PowerOff` implementation, picked in the entry wiring) and what was rejected (a separate interface for stopping the loop). The Description matches what was built. The docs criterion still names what the reader must know.

    no findings

    Earlier tests:
    - tests/entry/test_run.py: changed under the human's leave in journal entry 8. Only the signature of the `recording_of` stand-in changed: it now takes `request_stop` and passes it on to `original_of`. The test keeps its name and checks the same thing.

    Notes:
    - tests/entry/test_run_idle_exit.py:55 `instance_settings` copies the `settings` fixture in tests/entry/test_run.py:123. The only differences are that it writes its own token and sets `idle_shutdown_minutes=1`. Moving that fixture to a shared place, under the standing leave, would remove the copy.
25. factory: started docs as vm.
26. documenter: Docs, round 1. I wrote the documentation for the new idle-shutdown action `exit` and found nothing that sends the story back to the coder. The code matches the Interface and the criteria. I changed only documents, so I did not run `make check`; the factory's checks follow this stage.

    Files changed:
    - `docs/operator-guide.md`: a row for `FACTORY_IDLE_SHUTDOWN_ACTION` in the configuration table, after the `FACTORY_IDLE_SHUTDOWN_MINUTES` row. It covers the default, the refused values with the fault `is neither poweroff nor exit`, and that the variable is read even when the idle shutdown is off. A new paragraph *In a job* in *The idle shutdown*, before *The right*. It says that `exit` ends `factory-run` with status 0 after the limit and so ends the job's execution. The schedule or `gcloud run jobs execute` starts it again, a VM keeps `poweroff`, and the log line stays the same.
    - `docs/project-guide/watching.md` (the guide file that names the idle shutdown): `ProcessExit` beside `SystemctlPowerOff`, the setting, the new `idle_shutdown_of(settings, boundaries, request_stop=None)` with its `ValueError`, and `run_instance` and `run_until_stopped` passing the event's `set`.
    - `docs/decisions.md`: the entry *In a job the idle shutdown ends the process*, from the feature's decision 18. It gives the decision, the reason, where the choice is made and what was rejected.

    I ran the `ProcessExit` smoke example from the story and it prints `['stop']`.

    Cross-read and found current:
    - `README.md`: the criterion says none, and nothing in it is stale.
    - `docs/operator-guide.md`, the other idle-shutdown places: the setup-script option table and the environment-file step are about the VM's `poweroff` and are unchanged. The loop paragraph about idle ticks and pauses still holds.
    - `docs/project-guide/README.md`: the `PowerOffError` paragraph still holds.
    - `docs/project-guide/processes-and-checks.md`: the line on `SystemctlPowerOff` still holds. `ProcessExit` starts no process.
    - `docs/decisions.md`: the F0045-S0008 entry stays true as the `poweroff` default.

    Stale or unrelated text I saw and did not touch: none. The log line still says `powering the machine off` with `exit`. The story's Description requires that, and the operator guide now says so.

    `check`: check: green (not run again: passed on tree bb5344db4737 at 2026-10-31T23:15:54Z)
    `secrets`: secrets: green (2.3 s)
    `documents`: documents ok
27. factory: started smoke-test as vm.
28. smoke-tester: Smoke test, round 1. I ran both commands under `## Smoke test` from the repository root, as written and in order. Neither starts a server. I changed nothing.

    Command 1 (`ProcessExit(...).power_off()`):

    ```
    Bytecode compiled 4164 files in 58ms
    ['stop']
    ```
    Exit status 0. **Met** its `Expect:` line ("one line, `['stop']`"). The program printed exactly one line, `['stop']`. The `Bytecode compiled …` line comes from `uv run` on stderr, not from the command.

    Command 2 (`read_settings` with the action unset, set to `exit`, and set to `stop`):

    ```
    Bytecode compiled 4164 files in 56ms
    poweroff exit
    FACTORY_IDLE_SHUTDOWN_ACTION: is neither poweroff nor exit
    ```
    Exit status 0. **Met** its `Expect:` line. There are two program lines: `poweroff exit`, and a message that names `FACTORY_IDLE_SHUTDOWN_ACTION` and `is neither poweroff nor exit`. The `uv` line is stderr again.

    Acceptance criteria re-read: nothing the smoke test showed contradicts any of them.
    - Command 1 is consistent with criterion 3: `request_stop` was called once and nothing was raised.
    - Command 2 is consistent with criteria 1 and 2: unset gives `poweroff`, `exit` gives itself, and `stop` is refused with the Interface's message.

    The smoke test does not exercise criteria 4–10 (wiring, the loop, `main`, `run_until_stopped`, `make check`, docs), so it neither confirms nor contradicts them. Those are covered by the stage's checks and the tests.

    Findings: none.
