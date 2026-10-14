# The scheduler and the checkout preparer

## Assignment (as of log entry 1)

Build the loop of one factory instance and the preparation of its checkout. The loop ticks with a pause of 15 seconds after activity that doubles while idle, up to 120 seconds, and the checkout, which lies at one fixed path, is recloned when it is missing. Nothing in the loop can name a second project: it calls one `tick` and one `prepare`. This covers ST7.1 and ST7.3, implements R25, and keeps kept thing 16 (the pause follows activity). The settings that name the repository and the checkout are the previous story's. This story builds the pure parts: the scheduler and the checkout preparer. The story after the next builds the process that runs them (`main`, `run_instance`). Later stories of this feature wrap the checkout preparation; the first tick of a run happens at once, so a restart with the same instance name reaches its first look without waiting out any pause. A checkout whose clone was killed half-way is not recognised: R18 calls the checkout disposable, and the operator guide tells the operator to delete the directory.

## Interface

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

Rules:

- `pause_after(n)` is the pause after an iteration that left `n` consecutive idle ticks since the last activity (0 right after activity). A negative `n` raises `ValueError`.
- `Scheduler.run` repeats iterations until `should_stop()` is true. It asks `should_stop()` before every iteration and again after every iteration, before the sleep. The first iteration runs before any sleep.
- One iteration calls `prepare()`. When that returns `False` the tick is not called and the iteration counts as idle. Otherwise it calls `tick()`; `True` means activity, `False` idle. After the iteration it calls `sleep(pause_after(idle_ticks).total_seconds())`.
- An `Exception` raised by `prepare` or `tick` is caught, written as one line `iteration failed: <exception type name>: <message>` through `log.line`, and counts as idle. A `BaseException` (such as `InjectedKill`) is not caught.
- `CheckoutPreparer.prepare` returns `True` without calling git when `settings.checkout / ".git"` exists. Otherwise it calls `git.clone(settings.repository_url)` and returns `True`. A `GitError` from the clone is not caught. A checkout whose clone was killed half-way is not recognised: the operator guide tells the operator to delete the directory, because R18 calls the checkout disposable and a clone killed half-way is rare.

Tests: `tests/application/test_scheduler.py`. The scheduler tests pass recording callables for `prepare`, `tick`, `sleep` and `should_stop`, and a `FactoryLog` that collects lines; the preparer tests use `GitCli` on a real bare remote in `tmp_path`.

## Acceptance criteria

1. `pause_after(n)` for `n` in 0, 1, 2, 3, 4 and 10 is 15, 30, 60, 120, 120 and 120 seconds.
2. `pause_after(-1)` raises `ValueError`.
3. `Scheduler.run` calls `prepare` and `tick` once per iteration, in that order, and the first call it makes is `prepare`, before any `sleep`: with `should_stop` true after the third `tick`, `tick` was called exactly 3 times and `sleep` exactly 2 times (ST7.1: the one `tick` callable is the whole loop).
4. With `should_stop` true from the start, `Scheduler.run` returns without calling `prepare`, `tick` or `sleep`.
5. The sleeps follow the idle count since the last activity: ticks returning `True, False, False, False, False, False` give sleeps of 15.0, 30.0, 60.0, 120.0 and 120.0 seconds, and ticks returning `False, False, True, False` give 30.0, 60.0 and 15.0 seconds.
6. When `prepare` returns `False` the tick is not called and the iteration counts as idle: `prepare` results `False, True, True` with a `tick` that always returns `True` and `should_stop` true after the third `prepare` give two tick calls and sleeps of 30.0 and 15.0 seconds.
7. A `ValueError("boom")` raised by `tick` writes the line `iteration failed: ValueError: boom` through the log, the loop goes on with the next iteration, and the sleep that follows is the idle pause of 30.0 seconds.
8. A `ValueError("boom")` raised by `prepare` writes the line `iteration failed: ValueError: boom` through the log, `tick` is not called in that iteration, and the sleep that follows is the idle pause of 30.0 seconds.
9. An `InjectedKill` raised by `tick` leaves `Scheduler.run` and is not logged.
10. `CheckoutPreparer.prepare` on a missing checkout directory clones the settings' repository into it and returns `True`: `origin/main` then resolves in the new checkout; after `shutil.rmtree` of the whole checkout, a second `prepare` clones again (ST7.3).
11. `CheckoutPreparer.prepare` on a checkout that already holds a clone returns `True` and leaves it as it is: a file the test added to the work tree is still there.
12. `CheckoutPreparer.prepare` on a directory that holds files but no `.git` raises `GitError` and changes nothing in the directory.
13. make check stays green.
14. docs: `docs/operator-guide.md` states the pauses (15 seconds after activity, doubling to 120 seconds while idle) and that only a missing checkout is recloned, so the operator deletes a checkout whose clone was killed half-way; `docs/decisions.md` records why a checkout whose clone was killed half-way is not recognised (R18: the checkout is disposable).

## Demo

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
