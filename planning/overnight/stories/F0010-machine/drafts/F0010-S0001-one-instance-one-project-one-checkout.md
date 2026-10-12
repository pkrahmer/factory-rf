# One instance, one project, one checkout

## Assignment (as of log entry 1)

Build the settings and the loop of one factory instance. An instance is told its project and its name by two environment variables, keeps its checkout at one fixed path, reclones that checkout when it is missing, and ticks in a loop whose pause is 15 seconds after activity and doubles while idle, up to 120 seconds. Nothing in the loop or the settings can name a second project. This covers ST7.1, ST7.2 and ST7.3, implements R2 and R25, and keeps kept thing 15 (one instance, one project) and kept thing 16 (the pause follows activity). The console script entries `factory-run` and `factory-health` belong in `pyproject.toml`, which lies outside the coder's write paths: this story makes the modules runnable with `python -m` and the human adds the entries. Later stories of this feature add fields to `InstanceSettings` and wrap the checkout preparation; the first tick of a run happens at once, so a restart with the same instance name reaches its first look without waiting out any pause.

## Interface

`src/factory/domain/errors.py` gains one type:

```python
class SettingsInvalid(FactoryError):
    variable: str
    fault: str
    def __init__(self, variable: str, fault: str) -> None: ...   # the message is "<variable>: <fault>"
```

`src/factory/domain/settings.py`

```python
CHECKOUT_PATH = Path("/work/checkout")
STATE_DIRECTORY = Path("/state")
REPOSITORY_URL_VARIABLE = "FACTORY_REPOSITORY_URL"
INSTANCE_VARIABLE = "FACTORY_INSTANCE"

class InstanceSettings(BaseModel):            # frozen, extra="forbid", like every DTO
    repository_url: str
    instance: Name                            # factory.domain.identifiers.Name
    checkout: Path = CHECKOUT_PATH
    state_directory: Path = STATE_DIRECTORY

def read_settings(environ: Mapping[str, str]) -> InstanceSettings: ...
```

`src/factory/application/scheduler.py`

```python
FIRST_PAUSE = timedelta(seconds=15)
MAX_PAUSE = timedelta(seconds=120)

def pause_after(idle_ticks: int) -> timedelta: ...      # min(FIRST_PAUSE * 2 ** idle_ticks, MAX_PAUSE)

class Scheduler:
    def __init__(
        self,
        prepare: Callable[[], bool],
        tick: Callable[[], bool],
        sleep: Callable[[float], None],
        should_stop: Callable[[], bool],
        log: FactoryLog,
    ) -> None: ...
    def run(self) -> None: ...

class CheckoutPreparer:
    def __init__(self, git: Git, settings: InstanceSettings) -> None: ...
    def prepare(self) -> bool: ...
```

`src/factory/entry/run.py`

```python
def run_instance(
    settings: InstanceSettings,
    *,
    sleep: Callable[[float], None],
    should_stop: Callable[[], bool],
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

- `read_settings` reads exactly two variables, `FACTORY_REPOSITORY_URL` and `FACTORY_INSTANCE`. `checkout` and `state_directory` are always the two constants; no variable changes them.
- A variable that is missing, empty or only whitespace raises `SettingsInvalid` whose `variable` is that variable's name.
- `repository_url` must contain no whitespace and no comma (one repository, R2), else `SettingsInvalid` with `variable == "FACTORY_REPOSITORY_URL"`.
- `instance` must match `Name` (`^[a-z][a-z0-9-]*$`), else `SettingsInvalid` with `variable == "FACTORY_INSTANCE"`.
- `pause_after(n)` is the pause after an iteration that left `n` consecutive idle ticks since the last activity (0 right after activity). A negative `n` raises `ValueError`.
- `Scheduler.run` repeats iterations until `should_stop()` is true. It asks `should_stop()` before every iteration and again after every iteration, before the sleep. The first iteration runs before any sleep.
- One iteration calls `prepare()`. When that returns `False` the tick is not called and the iteration counts as idle. Otherwise it calls `tick()`; `True` means activity, `False` idle. After the iteration it calls `sleep(pause_after(idle_ticks).total_seconds())`.
- An `Exception` raised by `prepare` or `tick` is caught, written as one line `iteration failed: <exception type name>: <message>` through `log.line`, and counts as idle. A `BaseException` (such as `InjectedKill`) is not caught.
- `CheckoutPreparer.prepare` returns `True` without calling git when `settings.checkout / ".git"` exists. Otherwise it calls `git.clone(settings.repository_url)` and returns `True`. A `GitError` from the clone is not caught.
- `main` calls `read_settings(environ if environ is not None else os.environ)`. On success it calls `runner(settings)` once (the default runner installs handlers for SIGTERM and SIGINT that set a stop event and calls `run_instance` with `event.wait` as the sleep and `event.is_set` as `should_stop`) and returns 0. On `SettingsInvalid` it does not call the runner. It writes the line `settings invalid: <variable>: <fault>` through a `TimestampedFactoryLog` at `state_directory / "factory.log"`, writes a `HealthStatus` holding one `RepositoryStop(scope="machine", reason="preflight_failed", detail=<the message>)` through a `JsonHealthStatusFile` at `state_directory / "health.json"` (written directly: no boundaries exist yet), and returns 2.
- `python -m factory.entry.run` ends with `raise SystemExit(main())`. `run_instance` builds `build_boundaries(settings)`, a `CheckoutPreparer`, the tick of `factory.application.tick` and a `Scheduler`, and passes a `tick` that returns `True` unless the tick's event was `idle`.

Tests: `tests/domain/test_settings.py`, `tests/application/test_scheduler.py`, `tests/entry/test_run.py`, `tests/test_single_project.py` (the search). The scheduler tests pass recording callables for `prepare`, `tick`, `sleep` and `should_stop`, and a `FactoryLog` that collects lines; the preparer tests use `GitCli` on a real bare remote in `tmp_path`.

## Acceptance criteria

1. `read_settings({"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "factory-1"})` returns settings with that repository URL and that instance name, `checkout == Path("/work/checkout")` and `state_directory == Path("/state")`.
2. Each of the two variables, when missing, empty or only spaces (six cases), raises `SettingsInvalid` whose `variable` is that variable's name.
3. A repository URL that contains a comma (`a/b,c/d`) or a space (`a b`) raises `SettingsInvalid` with `variable == "FACTORY_REPOSITORY_URL"`; `https://github.com/owner/project.git` is accepted.
4. An instance name is accepted when it matches `^[a-z][a-z0-9-]*$` (`factory-1`, `a`) and raises `SettingsInvalid` with `variable == "FACTORY_INSTANCE"` for `Factory-1`, `1st`, `factory_1` and `-x`.
5. `FACTORY_CHECKOUT`, `FACTORY_STATE_DIRECTORY` and any other variable in the mapping change nothing: `checkout` and `state_directory` stay the two constants.
6. A search of every `.py` file under `src/factory` finds no occurrence of the text `REPOS` (v1's list of repositories is gone, ST7.2).
7. `pause_after(n)` for `n` in 0, 1, 2, 3, 4 and 10 is 15, 30, 60, 120, 120 and 120 seconds.
8. `pause_after(-1)` raises `ValueError`.
9. `Scheduler.run` calls `prepare` and `tick` once per iteration, in that order, and the first call it makes is `prepare`, before any `sleep`: with `should_stop` true after the third `tick`, `tick` was called exactly 3 times and `sleep` exactly 2 times (ST7.1: the one `tick` callable is the whole loop).
10. The sleeps follow the idle count since the last activity: ticks returning `True, False, False, False, False, False` give sleeps of 15.0, 30.0, 60.0, 120.0 and 120.0 seconds, and ticks returning `False, False, True, False` give 30.0, 60.0 and 15.0 seconds.
11. When `prepare` returns `False` the tick is not called and the iteration counts as idle: `prepare` results `False, True, True` with a `tick` that always returns `True` and `should_stop` true after the third `prepare` give two tick calls and sleeps of 30.0 and 15.0 seconds.
12. A `ValueError("boom")` raised by `tick` writes the line `iteration failed: ValueError: boom` through the log, the loop goes on with the next iteration, and the sleep that follows is the idle pause of 30.0 seconds.
13. An `InjectedKill` raised by `tick` leaves `Scheduler.run` and is not logged.
14. `CheckoutPreparer.prepare` on a missing checkout directory clones the settings' repository into it and returns `True`: `origin/main` then resolves in the new checkout; after `shutil.rmtree` of the whole checkout, a second `prepare` clones again (ST7.3).
15. `CheckoutPreparer.prepare` on a checkout that already holds a clone returns `True` and leaves it as it is: a file the test added to the work tree is still there.
16. `CheckoutPreparer.prepare` on a directory that holds files but no `.git` raises `GitError` and changes nothing in the directory.
17. `main` with an invalid environment (no `FACTORY_INSTANCE`) returns 2 without calling the runner, appends one line to `factory.log` that starts with a time stamp in the form `YYYY-MM-DDTHH:MM:SSZ` and then reads `settings invalid: FACTORY_INSTANCE`, and leaves a `health.json` that holds one stop with scope `machine` and reason `preflight_failed` whose detail names `FACTORY_INSTANCE`.
18. `main` with a valid environment returns 0 and calls the runner exactly once with settings equal to `read_settings` of that environment.
19. `make check` stays green.
20. docs: `docs/operator-guide.md` lists the two variables (`FACTORY_REPOSITORY_URL`, `FACTORY_INSTANCE`), the fixed checkout path `/work/checkout` and state directory `/state`, the pauses (15 seconds after activity, doubling to 120 seconds while idle) and that an invalid environment ends the process with status 2 and a machine stop; `docs/decisions.md` records why one instance runs one project (R2).

## Demo

```bash
uv run python -c "
from factory.domain.settings import read_settings
s = read_settings({'FACTORY_REPOSITORY_URL': '/srv/project.git', 'FACTORY_INSTANCE': 'factory-1'})
print(s.instance, s.repository_url, s.checkout, s.state_directory)
"
```
Expect: one line, `factory-1 /srv/project.git /work/checkout /state`.

```bash
uv run python -c "
from factory.application.scheduler import pause_after
print([int(pause_after(n).total_seconds()) for n in range(6)])
"
```
Expect: `[15, 30, 60, 120, 120, 120]`.

```bash
uv run python -c "
from factory.application.scheduler import Scheduler
results = iter([True, False, False])
sleeps = []
class Log:
    def line(self, text):
        print('log:', text)
Scheduler(prepare=lambda: True, tick=lambda: next(results), sleep=sleeps.append, should_stop=lambda: len(sleeps) >= 3, log=Log()).run()
print(sleeps)
"
```
Expect: one line, `[15.0, 30.0, 60.0]`: the first tick ran at once, activity gave 15 seconds and each idle tick doubled the pause.

## Log (append only)

1. 2026-10-12 human: created.
