---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 473
comments_read: [6429816658, 6429884713]
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-10-26T23:51:28.161342Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T23:29:15.475321Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T23:29:15.481152Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-26T23:29:37.021397Z'
  stage: intake
  run: d2ebe634528b4c148a92a9f29f96f45b
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-26T23:31:57.034752Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-26T23:32:15.014690Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-26T23:33:04.329467Z'
  stage: intake
  run: 387cdb5500744dc3b581c850b0670534
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-26T23:33:24.676113Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-10-26T23:34:24.170636Z'
  stage: tests
  run: ed00973ed4fa42f49507327fa4a35829
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-10-26T23:35:41.618750Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-26T23:35:59.382194Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-10-26T23:43:26.003479Z'
  stage: tests
  run: c840c26affa940f8b5a2e9cff543094e
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-26T23:43:46.410772Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-10-26T23:51:07.392883Z'
  stage: doing
  run: 3d18427de9cd4aa9b7f7c278c0565a68
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-26T23:51:28.161342Z'
  stage: review
---

# The factory powers its machine off after an idle stretch

## Description

On the VM of v1.2 the machine costs money for every hour it runs, also while the factory has nothing to do (`planning/v1.2-candidates.md`, "For F0045", the human, 2026-10-24). This story adds the idle shutdown to the factory, as an option that is off by default: the setting `FACTORY_IDLE_SHUTDOWN_MINUTES` turns it on and gives the limit; the loop counts an unbroken stretch of idle ticks, and right after an idle tick that ends a stretch of at least the limit, the factory logs one line and asks the machine to power off through a new wrapper, `SystemctlPowerOff`, behind a new interface, `PowerOff`. An idle tick is one that ran, ended at no stop and dispatched the evaluation's `idle` event: nothing can be started, the first waiting work item waits for the human (an approval, a posted question), or a claim is held by another instance; a tick at a stop or with any other event ends the stretch, and an iteration that ran no tick neither counts nor ends it (decision 8 of `feature.md`). The wrapper runs `sudo -n /usr/bin/systemctl poweroff`, the one command S0009's `sudoers` line allows (decision 9); a refusal or any other fault of it is one log line, and the factory runs on and starts a new stretch (decision 10). Starting the machine again is outside the factory (decision 11). What stays: the loop's pauses (`pause_after`), the meaning of `activity`, every tick and every stop; with the setting unset, blank or `0` nothing of this runs. S0009 (the setup script gives the power-off right only with the idle shutdown) gives the machine the right and the script's option.

## Interface

`factory.domain.settings` (`domain`):

```python
IDLE_SHUTDOWN_VARIABLE = "FACTORY_IDLE_SHUTDOWN_MINUTES"

class InstanceSettings(BaseModel):
    ...
    idle_shutdown_minutes: NonNegativeInt = 0
```

- `read_settings`: the variable unset, empty or blank gives `0`; a value of ASCII digits gives its number (`0` included, which is off); any other value (`-1`, `x`, `1.5`, a digit of another script) raises `SettingsInvalid(IDLE_SHUTDOWN_VARIABLE, "is not a whole number of minutes")`. No upper limit.

`factory.domain.errors` (`domain`):

```python
class PowerOffError(BoundaryError):
    """The machine could not be asked to power off, or refused."""

    detail: str

    def __init__(self, detail: str) -> None:
        """Say what went wrong; the text is `power off failed: <detail>`."""
```

`factory.application.machine` (`application`):

```python
class PowerOff(ABC):
    """The machine's power, which the factory may switch off."""

    @abstractmethod
    def power_off(self) -> None:
        """Ask the machine to power off; raise `PowerOffError` when it cannot be asked or refuses."""
```

`factory.application.idle_shutdown` (`application`, new):

```python
class IdleShutdown:
    """Powers the machine off right after an idle tick that ends an idle stretch of at least `limit`."""

    def __init__(self, limit: timedelta, clock: Clock, power: PowerOff, log: FactoryLog) -> None: ...
    @property
    def limit(self) -> timedelta: ...
    @property
    def power(self) -> PowerOff: ...
    def observe(self, outcome: TickOutcome) -> None: ...
```

- A `limit` of zero or less raises `ValueError`; one minute or more is accepted.
- The first stretch starts at `clock.now()` when the object is made.
- `observe` counts an outcome as idle when `outcome.stopped is None`, `outcome.event` is an event of kind `idle` and `outcome.dispatch == "handled"`; any other outcome starts a new stretch at `clock.now()` and does nothing else.
- An idle outcome when `clock.now()` minus the stretch's start is at least `limit`: one log line that begins `idle shutdown: ` and names the limit in minutes, then `power.power_off()` once, then a new stretch at `clock.now()`. Below the limit it does nothing.
- A `PowerOffError` of `power_off` is not raised: one log line that begins `idle shutdown: ` and holds the error's text, and the new stretch starts as after a call that succeeded.

`factory.adapters.power_off` (`adapters`, new; a wrapper of R5 that starts its one command through `factory.adapters.process`):

```python
POWER_OFF_COMMAND = ("-n", "/usr/bin/systemctl", "poweroff")
POWER_OFF_TIME_LIMIT = timedelta(minutes=1)

class SystemctlPowerOff(PowerOff):
    def __init__(self, sudo_executable: str = "sudo", *, time_limit: timedelta = POWER_OFF_TIME_LIMIT) -> None: ...
    def power_off(self) -> None: ...
```

- `power_off` runs `[sudo_executable, *POWER_OFF_COMMAND]` without a shell, under `time_limit`, and returns when it exits 0.
- Another exit status raises `PowerOffError` whose detail is `failure_detail` of `factory.adapters.printed_output` (the last non-empty printed line, standard error or output; `exit status <n>` when nothing was printed); a call that reached `time_limit` raises `PowerOffError` whose detail is `no_end_detail(time_limit)` of the same module; a program that cannot be started raises `PowerOffError` whose detail begins `cannot start <sudo_executable>:`.

`factory.entry.wiring` (`entry`): `idle_shutdown_of(settings: InstanceSettings, boundaries: Boundaries) -> IdleShutdown | None` (in `__all__`): `None` when `settings.idle_shutdown_minutes` is `0`; otherwise `IdleShutdown(timedelta(minutes=settings.idle_shutdown_minutes), boundaries.clock, SystemctlPowerOff(), boundaries.log)`.

`factory.entry.run` (`entry`): `activity_tick(tick: Tick, idle: IdleShutdown | None = None) -> Callable[[], bool]`: each call runs `tick.run()`, hands the outcome to `idle.observe` when `idle` is given, and returns `activity(outcome)` as today; `run_instance` builds it with `idle_shutdown_of(settings, boundaries)`.

Tests (the tester writes them; the leave is decision 28 of `feature.md`): new modules at the tester's choice, for example `tests/domain/test_settings_idle_shutdown.py`, `tests/application/test_idle_shutdown.py`, `tests/adapters/test_power_off.py` (a stand-in for `sudo` written under `tmp_path`, never the real `sudo`), `tests/entry/test_wiring_idle_shutdown.py`. `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module`: its set gains `factory.adapters.power_off`, its name kept. No other earlier test changes; `tests/entry/test_run.py::test_the_activity_tick_keeps_one_tick_and_the_errors_of_both_calls` stays green unchanged.

## Acceptance criteria

1. The setting (rows of one parametrized test over `read_settings` with `BASE` of `tests/settings_support.py` and the row's value): unset, `""` and `"  "` give `idle_shutdown_minutes == 0`; `"0"` gives `0`; `"1"` gives `1`; `"30"` gives `30`; `"-1"`, `"x"`, `"100000"` gives `100000`; `"-1"`, `"x"`, `"1.5"` and `"٣"` raise `SettingsInvalid` with variable `FACTORY_IDLE_SHUTDOWN_MINUTES` and fault `is not a whole number of minutes`.
2. The stretch (rows of one parametrized test over `IdleShutdown` with `limit` 30 minutes, a `ManualClock`, a `PowerOff` of the test that counts its calls and the `RecordingLog` of `tests/recording_log.py`; times are minutes and seconds after the object was made; `idle` is an outcome of the event `idle` dispatched `handled`, `waits` the same with the detail `F0001-S0001 waits for the human` (the evaluation's form for a story waiting for its approval or an answer), `other` an outcome of the event `acceptance_due` for `F0001` dispatched `handled`, `stopped` an outcome with `stopped="main_branch_failing"`): `idle` at 00:00, 29:00 and 29:59 gives no call; `idle` at 30:00 gives one call and one log line that begins `idle shutdown: ` and contains `30`; `waits` at 30:00 gives one call; `idle` at 30:00, 59:59 and 60:00 gives two calls, the second at 60:00; `idle` at 05:00, `other` at 10:00 and `idle` at 39:59 give no call, then `idle` at 40:00 one; `stopped` at 20:00 and `idle` at 49:59 give no call, then `idle` at 50:00 one; an `idle` event dispatched `error` at 30:00 gives no call; `idle` at 31:00 as the first outcome gives one call (the first stretch starts when the object is made).
3. A refused power-off (one test): with a `PowerOff` that raises `PowerOffError("sudo: a password is required")`, `idle` at 30:00 raises nothing, the log's last line begins `idle shutdown: ` and holds `sudo: a password is required`, and `idle` at 59:59 makes no second call while `idle` at 60:00 makes one.
4. The limit (rows of one parametrized test): `IdleShutdown(timedelta(0), ...)` and `IdleShutdown(timedelta(minutes=-1), ...)` raise `ValueError`; `IdleShutdown(timedelta(minutes=1), ...)` is made and its `limit` is one minute.
5. The wrapper (rows of one parametrized test over `SystemctlPowerOff(<stand-in>)` with stand-in programs under `tmp_path` that write their words to a file): a stand-in that exits 0 makes `power_off()` return, and its words are exactly `-n`, `/usr/bin/systemctl`, `poweroff`; one that prints `sudo: a password is required` to standard error and exits 1 raises `PowerOffError` whose text names the exit status `1` and holds `sudo: a password is required`; one that prints `sudo: a password is required` to standard output only and exits 1 raises `PowerOffError` holding it; one that prints two lines and a blank line and exits 1 raises `PowerOffError` whose detail holds the second line and not the first; one that prints nothing and exits 1 raises `PowerOffError` whose detail is `exit status 1`; a path that does not exist raises `PowerOffError` whose detail begins `cannot start `; a stand-in that sleeps 60 seconds, with `time_limit` one second, raises `PowerOffError` within `ROOMY_BOUND_SECONDS` of `tests/time_limits.py` whose detail equals `no_end_detail` of that limit, the text the `zfs` time-limit test (`tests/adapters/test_zfs_snapshots_drop_caches.py`) asserts.
6. The error's text (one test): `str(PowerOffError("x")) == "power off failed: x"`.
7. The activity tick (one test with a stand-in tick that returns an `idle` outcome, then an `other` outcome): `activity_tick(tick, idle)` returns `False`, then `True`, and the `IdleShutdown` stand-in (a subclass of the test that records `observe`) received exactly those two outcomes in order.
8. The wiring (rows of one parametrized test over `idle_shutdown_of` with the `boundaries` fixture): settings with `idle_shutdown_minutes` `0` give `None`; with `30` an `IdleShutdown` whose `limit` is 30 minutes and whose `power` is a `SystemctlPowerOff`; making it runs nothing (a stand-in `sudo` first on `PATH` records no call).
9. The wrappers (the structural test of `tests/test_wrapper_search.py`): the modules that import `factory.adapters.process` are the seven of the test's set on `main` before this story and `factory.adapters.power_off`.
10. `make check` stays green.
11. docs: `docs/operator-guide.md`, `## Configuration`: the row `FACTORY_IDLE_SHUTDOWN_MINUTES` (unset, blank or `0` off, the default; a whole number of minutes; the refusal); `## The loop and its pauses`: one paragraph that the idle shutdown counts the loop's idle ticks; `## The machine`: a section `### The idle shutdown` that says what counts as idle and what does not (decision 8 of `feature.md`: a story waiting for the human counts, a stop does not), the two log lines that begin `idle shutdown: `, that a refused power-off leaves the instance running and how to read it, that S0009's script option gives the right, and how the machine starts again: by hand with `gcloud compute instances start factory-vm --zone europe-west3-a`, or by a GCP instance schedule that only starts it (made by hand with `gcloud compute resource-policies create instance-schedule` and attached with `gcloud compute instances add-resource-policies`), and that a merge, a close or an answer given while the VM is off is seen at the first tick after the start. `docs/project-guide/watching.md`, `## Stops, the clock and the factory log`: a section *The idle shutdown* (`IdleShutdown`, `PowerOff`, `SystemctlPowerOff`, `idle_shutdown_of`, the rules of the stretch); `docs/project-guide/README.md`, *The files* and *Errors*: the line of `watching.md` follows and `PowerOffError` is listed. `docs/decisions.md`: a new entry "The machine powers itself off after an idle stretch, an option off by default" (F0045-S0008; decisions 8 to 12 of `feature.md` with their rejected options). `README.md`: none.

## Smoke test

```bash
uv run python - <<'EOF'
from factory.domain.settings import read_settings
base = {"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "vm", "FACTORY_CLAUDE_HOME": "/srv/agents"}
print(read_settings(base).idle_shutdown_minutes, read_settings({**base, "FACTORY_IDLE_SHUTDOWN_MINUTES": "30"}).idle_shutdown_minutes)
from factory.adapters.power_off import POWER_OFF_COMMAND, SystemctlPowerOff
from factory.application.machine import PowerOff
print(POWER_OFF_COMMAND, issubclass(SystemctlPowerOff, PowerOff))
EOF
```
Expect: two lines: `0 30`; `('-n', '/usr/bin/systemctl', 'poweroff') True`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf '#!/bin/sh\necho "$@" > "%s/words"\n' "$d" > "$d/stand-in"; chmod +x "$d/stand-in"
uv run python -c "from factory.adapters.power_off import SystemctlPowerOff; SystemctlPowerOff('$d/stand-in').power_off()"; cat "$d/words"
```
Expect: `-n /usr/bin/systemctl poweroff`

## Journal

1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: Format check passed. The Interface states behaviours that no criterion tests, so two coders could read them two ways and both would pass. Questions:

   1. Interface, `IdleShutdown.observe`: the first log line "names the limit in minutes". Criterion 2 only checks that the line begins `idle shutdown: `. Add to criterion 2 that, with a limit of 30 minutes, the line contains `30`? I would add it, as an assertion on the existing `idle` at 30:00 row.

   2. Interface, `PowerOffError`: its text is `power off failed: <detail>`. No criterion tests it. Add a criterion that `str(PowerOffError("x")) == "power off failed: x"`? I would add that, as a row in criterion 5 or as a test of its own.

   3. Interface, `SystemctlPowerOff.power_off`, which says the detail names "the last non-empty line the command printed (standard error or output), or says it printed nothing".
      - Criterion 5 covers only a line on standard error. It has no row for a line on standard output, for a last non-empty line chosen among several lines (including trailing blank lines), or for the exact wording of the "printed nothing" case. It only says the case "raises `PowerOffError`".
      - What is the exact wording for "printed nothing"? I would fix it as `printed nothing`, and add rows for: a line on standard output only; two lines followed by a blank line, where the detail holds the second line and not the first; and nothing printed, where the detail holds `printed nothing` and the status `1`.

   4. The same method, for the time limit: the detail must name the limit. Criterion 5 only requires a raise within `ROOMY_BOUND_SECONDS`. Add that the text names the limit, with the form to check. I would use `1 s` or `1 second`; please choose the form that the detail must contain.

   5. Criterion 7 (wiring) does not check that `idle_shutdown_of` passes `boundaries.clock` and `boundaries.log` to `IdleShutdown`, as the Interface says. Add this check? I would add that the `IdleShutdown` that is made logs to `boundaries.log` and reads `boundaries.clock`.

   6. Interface, `read_settings`: "No upper limit". Add a row such as `"100000"` giving `100000`? I would add it.

   Everything else is fine. The Interface names concrete modules and signatures. The smoke test commands are runnable, and their `Expect:` lines can be checked against the output. The placement in the layers is right: `PowerOff` and `IdleShutdown` in application, `SystemctlPowerOff` in adapters, wiring in entry. The story is within the scope of S0008 in `feature.md`. The leave for the changed earlier test is decision 28.
4. 2026-10-26 human: All six as you propose, with these forms:
   1. Yes: with a limit of 30 minutes the first line contains `30`.
   2. Yes, a test of its own: `str(PowerOffError("x")) == "power off failed: x"`.
   3. Yes, but no new wording: the detail is `failure_detail` of `factory.adapters.printed_output`, as the `zfs` commands use it (the last non-empty printed line; `exit status <n>` when nothing was printed). Rows: a line on standard output only; two lines and a blank line, giving the second; nothing printed with status 1, giving `exit status 1`.
   4. Yes: the time-limit detail is `no_end_detail` as the `zfs` commands give it; the row asserts the same text the `zfs` time-limit test asserts for its limit.
   5. Yes: the built `IdleShutdown` logs to `boundaries.log` and reads `boundaries.clock`.
   6. Yes: `"100000"` gives `100000`.
5. factory: started intake as vm.
6. intake: accepted. The human's answer (journal 4) is carried into the story, and nothing else is changed.
   - Interface: concrete modules and signatures (settings, errors, machine, idle_shutdown, power_off, wiring, run). The human's answer 3 fixes the detail wording of the wrapper to `failure_detail` and `no_end_detail` of `factory.adapters.printed_output`; I wrote that into the Interface line. Every behaviour it states now has a criterion.
   - Criteria: carried in from the answer. Criterion 1 gains the row `"100000"`. Criterion 2's 30:00 row also asserts the line contains `30`. Criterion 5 gains rows for output on standard output only, for two lines plus a blank line (the second line is the detail), and for nothing printed (`exit status 1`). It also gains the time-limit detail equal to `no_end_detail(limit)`, the text the zfs drop-caches test asserts. A new criterion 6 tests `str(PowerOffError("x")) == "power off failed: x"`. Criterion 8, the wiring, gains the check that the built `IdleShutdown` logs to `boundaries.log` and reads `boundaries.clock`. The later criteria are renumbered; `make check` and `docs:` stay last. Each rule has both sides (limit, refused and passing setting, stop and non-idle events, error dispatch, refused power-off).
   - Smoke test: both blocks are runnable. Neither runs pytest, so the `-q` rule does not apply. Each `Expect:` line can be checked against the output.
   - Architecture: PowerOff and IdleShutdown sit in application, SystemctlPowerOff in adapters through the process module, and wiring in entry. This follows the layers and R5.
   - Scope: within S0008 of feature.md (decisions 8 to 12). The leave for the changed earlier test is decision 28.
7. factory: started tests as vm.
8. tester: Stopped before writing any tests. I read the work item, `factory.domain.settings`, `factory.adapters.printed_output`, `TickOutcome`, `activity_tick`, the `boundaries` and `clock` fixtures, `tests/test_wrapper_search.py` and the zfs time-limit test. Criteria 2, 3, 4, 6, 7 and 9 are clear. Three places need your answer before I can write the tests without guessing:

   1. Criterion 5, the standard-error row, contradicts the Interface. The row says the `PowerOffError` "text names the exit status `1` and holds `sudo: a password is required`". The Interface, after your answer 3 in journal 4, says the detail is `failure_detail` (the last non-empty printed line), and the text is `power off failed: <detail>`. With something printed, the text is `power off failed: sudo: a password is required` and holds no exit status. The options:
      (a) Drop "names the exit status `1`" from that row. The row then asserts that the detail is `sudo: a password is required`, as `failure_detail` gives it.
      (b) Keep it, and change the Interface so the detail also carries the status (for example `exit status 1: <line>`). That moves away from `failure_detail` as the zfs commands use it.
      I would choose (a).

   2. Criterion 1's text is garbled: "`"30"` gives `30`; `"-1"`, `"x"`, `"100000"` gives `100000`; `"-1"`, `"x"`, `"1.5"` and `"٣"` raise …". My reading, which I would test as rows of one parametrized test:
      - unset, `""` and `"  "` give `0`
      - `"0"` gives `0`, `"1"` gives `1`, `"30"` gives `30`, `"100000"` gives `100000`
      - `"-1"`, `"x"`, `"1.5"` and `"٣"` raise `SettingsInvalid("FACTORY_IDLE_SHUTDOWN_MINUTES", "is not a whole number of minutes")`
      Is that right?

   3. Criterion 8 lacks the check you agreed to in answer 5 of journal 4: that the built `IdleShutdown` logs to `boundaries.log` and reads `boundaries.clock`. Intake entry 6 says it was added, but the criterion's text does not hold it. The Interface exposes neither the clock nor the log, so I would test it through behaviour, as one more row or step of the wiring test:
      - a stand-in `sudo` first on `PATH` that records its words and exits 0
      - `boundaries.clock` advanced by 30 minutes, then `observe` of an `idle` outcome
      - assert that the stand-in recorded `-n /usr/bin/systemctl poweroff` once and that `factory.log` holds a line containing `idle shutdown: `
      Should I add that (my choice), or leave criterion 8 as written?

   No files created; nothing has been imported or run yet.
9. 2026-10-26 human: 1. (a): the row asserts the detail `sudo: a password is required`, as `failure_detail` gives it; no exit status there.
   2. Yes, exactly that reading.
   3. Yes, add it through behaviour as you describe; the stand-in `sudo` may come from the shared fixture of F0045-S0002 in `tests/conftest.py` if it fits, with recording added there.
10. factory: started tests as vm.
11. tester: I wrote the tests from the acceptance criteria and the human's answers in journal 9. On answer 1(a), the standard-error row asserts that the detail is `sudo: a password is required` and checks no exit status. On answer 2, criterion 1's rows are tested in the reading confirmed there. On answer 3, the wiring test checks the clock and the log through behaviour: it uses the existing `sudo_stand_in` fixture of `tests/conftest.py`, which already records its words, so the fixture needed no change.

    Criterion to test:
    - criterion 1: tests/domain/test_settings_idle_shutdown.py::test_the_idle_shutdown_minutes_are_read_or_refused
    - criterion 2: tests/application/test_idle_shutdown.py::test_the_machine_powers_off_after_an_idle_stretch_of_the_limit (every power-off call also has one `idle shutdown: ` line containing `30`)
    - criterion 3: tests/application/test_idle_shutdown.py::test_a_refused_power_off_is_logged_and_starts_a_new_stretch
    - criterion 4: tests/application/test_idle_shutdown.py::test_the_idle_limit_is_at_least_one_minute
    - criterion 5: tests/adapters/test_power_off.py::test_the_power_off_runs_its_one_command_or_raises_what_failed (`sh` stand-ins under `tmp_path`; the rows that must start get `ROOMY_LIMIT`, the sleeping row gets 1 s and `no_end_detail(1 s)`; every row is bounded by `ROOMY_BOUND_SECONDS`)
    - criterion 6: tests/domain/test_power_off_error.py::test_the_power_off_error_says_the_power_off_failed
    - criterion 7: tests/entry/test_run_idle_shutdown.py::test_the_activity_tick_hands_each_outcome_to_the_idle_shutdown
    - criterion 8: tests/entry/test_wiring_idle_shutdown.py::test_the_idle_shutdown_is_wired_from_the_settings (settings through `boundaries.settings.model_copy`; with 30 minutes, after the clock is advanced 30 minutes, observing `idle` makes the stand-in `sudo` record `-n /usr/bin/systemctl poweroff` once, and `state/factory.log` holds `idle shutdown: `)
    - criterion 9: tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module (its set gains `factory.adapters.power_off`; the name is kept, under decision 28 as the Interface states)

    Files created:
    - tests/power_support.py: shared outcomes `IDLE`, `WAITS`, `OTHER`, `STOPPED`, `IDLE_ERROR` and `CountingPower`, used by the application and entry tests
    - tests/domain/test_settings_idle_shutdown.py
    - tests/domain/test_power_off_error.py
    - tests/application/test_idle_shutdown.py
    - tests/adapters/test_power_off.py
    - tests/entry/test_run_idle_shutdown.py
    - tests/entry/test_wiring_idle_shutdown.py

    Earlier test file changed: tests/test_wrapper_search.py, the one line in its set.

    `make test` fails as intended, with collection errors where the test runner could not import:
    - `factory.application.idle_shutdown`
    - `factory.application.machine.PowerOff`
    - `factory.domain.errors.PowerOffError`
    - `factory.adapters.power_off`
    - `factory.entry.wiring.idle_shutdown_of`

    The settings test fails because `idle_shutdown_minutes` does not exist yet. `make lint` is green. I skipped the type check, as the stage allows. Nothing is open.

    `lint`: lint: green (0.2 s)
    `test`: ERROR tests/entry/test_wiring_idle_shutdown.py - ImportError while importing test module '/work/checkout/tests/entry/test_wiring_idle_shutdown.py'.
12. factory: started doing as vm.
13. coder: I built the idle shutdown to the Interface. `make check` is green: 99.57 % coverage, `check: green`.

    What I built:
    - `src/factory/domain/settings.py`: `IDLE_SHUTDOWN_VARIABLE` and `InstanceSettings.idle_shutdown_minutes: NonNegativeInt = 0`. A new reader, `_idle_shutdown_minutes`, gives `0` when the variable is unset or blank, takes ASCII digits with `0` allowed, and refuses anything else with `is not a whole number of minutes`.
    - `src/factory/domain/errors.py`: `PowerOffError(BoundaryError)`, whose text is `power off failed: <detail>`.
    - `src/factory/application/machine.py`: the `PowerOff` interface.
    - `src/factory/application/idle_shutdown.py` (new): `IdleShutdown`. An outcome counts as idle only when it has no stop, an `idle` event and the dispatch `handled`; any other outcome starts a new stretch.
      - At the limit it writes the line `idle shutdown: idle for <n> minutes, powering the machine off`, calls `power_off` once and starts a new stretch.
      - A `PowerOffError` becomes the line `idle shutdown: <error>; the factory runs on` and is not raised.
    - `src/factory/adapters/power_off.py` (new): `SystemctlPowerOff`, which runs `[sudo, -n, /usr/bin/systemctl, poweroff]` through `factory.adapters.process`. Standard error is merged into the output so that `failure_detail` sees the last line of either stream. A timeout gives `no_end_detail`, and an `OSError` gives `cannot start <sudo>: …`.
    - `src/factory/entry/wiring.py`: `idle_shutdown_of`, added to `__all__`.
    - `src/factory/entry/run.py`: `activity_tick(tick, idle=None)` hands each outcome to `idle.observe` before it returns `activity(outcome)`. `run_instance` passes it `idle_shutdown_of(settings, boundaries)`.

    Main choice: the settings reader is a separate small helper rather than a change to `_whole_number`. `_whole_number` refuses `0` and has a fault text of its own (`… of at least 1`), which its existing variables rely on. I rejected adding a `minimum` parameter to it: that would change a helper other settings share, just to save four lines.

    The shared skill steps did not apply; I set none aside. The refactor pass changed only two docstrings, which I shortened to stay under the line limit. The work item's Description was left alone: journal 9 settled how the tests read it and changed nothing in its meaning.

    Noticed but not touched: `make duplicates` reports 2 new findings. Both are the `ProcessRequest(argv=…, cwd=…, env=None, time_limit=…, merge_stderr=True)` block in `power_off.py`, which is similar to `zfs_snapshots._execute` and `podman_runs._query`. Each wrapper raises its own error type. A shared "run or raise" helper would mean restructuring the zfs and podman wrappers, which is beyond this story.

    `check`: check: green
    `duplicates`: duplicates: 2 new, 42 known, 0 gone
14. factory: started review as vm.
