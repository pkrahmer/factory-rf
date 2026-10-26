---
stage: intake
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 473
comments_read: []
handed_over: null
claim: null
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
- Another exit status raises `PowerOffError` whose detail names the status and the last non-empty line the command printed (standard error or output), or says it printed nothing; a call that reached `time_limit` raises `PowerOffError` naming the limit; a program that cannot be started raises `PowerOffError` whose detail begins `cannot start <sudo_executable>:`.

`factory.entry.wiring` (`entry`): `idle_shutdown_of(settings: InstanceSettings, boundaries: Boundaries) -> IdleShutdown | None` (in `__all__`): `None` when `settings.idle_shutdown_minutes` is `0`; otherwise `IdleShutdown(timedelta(minutes=settings.idle_shutdown_minutes), boundaries.clock, SystemctlPowerOff(), boundaries.log)`.

`factory.entry.run` (`entry`): `activity_tick(tick: Tick, idle: IdleShutdown | None = None) -> Callable[[], bool]`: each call runs `tick.run()`, hands the outcome to `idle.observe` when `idle` is given, and returns `activity(outcome)` as today; `run_instance` builds it with `idle_shutdown_of(settings, boundaries)`.

Tests (the tester writes them; the leave is decision 28 of `feature.md`): new modules at the tester's choice, for example `tests/domain/test_settings_idle_shutdown.py`, `tests/application/test_idle_shutdown.py`, `tests/adapters/test_power_off.py` (a stand-in for `sudo` written under `tmp_path`, never the real `sudo`), `tests/entry/test_wiring_idle_shutdown.py`. `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module`: its set gains `factory.adapters.power_off`, its name kept. No other earlier test changes; `tests/entry/test_run.py::test_the_activity_tick_keeps_one_tick_and_the_errors_of_both_calls` stays green unchanged.

## Acceptance criteria

1. The setting (rows of one parametrized test over `read_settings` with `BASE` of `tests/settings_support.py` and the row's value): unset, `""` and `"  "` give `idle_shutdown_minutes == 0`; `"0"` gives `0`; `"1"` gives `1`; `"30"` gives `30`; `"-1"`, `"x"`, `"1.5"` and `"٣"` raise `SettingsInvalid` with variable `FACTORY_IDLE_SHUTDOWN_MINUTES` and fault `is not a whole number of minutes`.
2. The stretch (rows of one parametrized test over `IdleShutdown` with `limit` 30 minutes, a `ManualClock`, a `PowerOff` of the test that counts its calls and the `RecordingLog` of `tests/recording_log.py`; times are minutes and seconds after the object was made; `idle` is an outcome of the event `idle` dispatched `handled`, `waits` the same with the detail `F0001-S0001 waits for the human` (the evaluation's form for a story waiting for its approval or an answer), `other` an outcome of the event `acceptance_due` for `F0001` dispatched `handled`, `stopped` an outcome with `stopped="main_branch_failing"`): `idle` at 00:00, 29:00 and 29:59 gives no call; `idle` at 30:00 gives one call and one log line that begins `idle shutdown: `; `waits` at 30:00 gives one call; `idle` at 30:00, 59:59 and 60:00 gives two calls, the second at 60:00; `idle` at 05:00, `other` at 10:00 and `idle` at 39:59 give no call, then `idle` at 40:00 one; `stopped` at 20:00 and `idle` at 49:59 give no call, then `idle` at 50:00 one; an `idle` event dispatched `error` at 30:00 gives no call; `idle` at 31:00 as the first outcome gives one call (the first stretch starts when the object is made).
3. A refused power-off (one test): with a `PowerOff` that raises `PowerOffError("sudo: a password is required")`, `idle` at 30:00 raises nothing, the log's last line begins `idle shutdown: ` and holds `sudo: a password is required`, and `idle` at 59:59 makes no second call while `idle` at 60:00 makes one.
4. The limit (rows of one parametrized test): `IdleShutdown(timedelta(0), ...)` and `IdleShutdown(timedelta(minutes=-1), ...)` raise `ValueError`; `IdleShutdown(timedelta(minutes=1), ...)` is made and its `limit` is one minute.
5. The wrapper (rows of one parametrized test over `SystemctlPowerOff(<stand-in>)` with stand-in programs under `tmp_path` that write their words to a file): a stand-in that exits 0 makes `power_off()` return, and its words are exactly `-n`, `/usr/bin/systemctl`, `poweroff`; one that prints `sudo: a password is required` to standard error and exits 1 raises `PowerOffError` whose text names the exit status `1` and holds `sudo: a password is required`; one that prints nothing and exits 1 raises `PowerOffError`; a path that does not exist raises `PowerOffError` whose detail begins `cannot start `; a stand-in that sleeps 60 seconds, with `time_limit` one second, raises `PowerOffError` within `ROOMY_BOUND_SECONDS` of `tests/time_limits.py`.
6. The activity tick (one test with a stand-in tick that returns an `idle` outcome, then an `other` outcome): `activity_tick(tick, idle)` returns `False`, then `True`, and the `IdleShutdown` stand-in (a subclass of the test that records `observe`) received exactly those two outcomes in order.
7. The wiring (rows of one parametrized test over `idle_shutdown_of` with the `boundaries` fixture): settings with `idle_shutdown_minutes` `0` give `None`; with `30` an `IdleShutdown` whose `limit` is 30 minutes and whose `power` is a `SystemctlPowerOff`; making it runs nothing (a stand-in `sudo` first on `PATH` records no call).
8. The wrappers (the structural test of `tests/test_wrapper_search.py`): the modules that import `factory.adapters.process` are the seven of the test's set on `main` before this story and `factory.adapters.power_off`.
9. `make check` stays green.
10. docs: `docs/operator-guide.md`, `## Configuration`: the row `FACTORY_IDLE_SHUTDOWN_MINUTES` (unset, blank or `0` off, the default; a whole number of minutes; the refusal); `## The loop and its pauses`: one paragraph that the idle shutdown counts the loop's idle ticks; `## The machine`: a section `### The idle shutdown` that says what counts as idle and what does not (decision 8 of `feature.md`: a story waiting for the human counts, a stop does not), the two log lines that begin `idle shutdown: `, that a refused power-off leaves the instance running and how to read it, that S0009's script option gives the right, and how the machine starts again: by hand with `gcloud compute instances start factory-vm --zone europe-west3-a`, or by a GCP instance schedule that only starts it (made by hand with `gcloud compute resource-policies create instance-schedule` and attached with `gcloud compute instances add-resource-policies`), and that a merge, a close or an answer given while the VM is off is seen at the first tick after the start. `docs/project-guide/watching.md`, `## Stops, the clock and the factory log`: a section *The idle shutdown* (`IdleShutdown`, `PowerOff`, `SystemctlPowerOff`, `idle_shutdown_of`, the rules of the stretch); `docs/project-guide/README.md`, *The files* and *Errors*: the line of `watching.md` follows and `PowerOffError` is listed. `docs/decisions.md`: a new entry "The machine powers itself off after an idle stretch, an option off by default" (F0045-S0008; decisions 8 to 12 of `feature.md` with their rejected options). `README.md`: none.

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
