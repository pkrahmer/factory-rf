---
stage: review
pr: 120
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
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
11. `CheckoutPreparer.prepare` on a checkout that already holds a clone returns `True` without calling git and leaves it as it is: `CheckoutPreparer(GitCli(<the checkout>, GitOptions(executable=<a path in tmp_path that does not exist>)), settings).prepare()` returns `True` (any git call would raise `GitError`), and a file the test added to the work tree is still there.
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
2. intake: accepted
   - Interface: `src/factory/application/scheduler.py` names the constants, `pause_after`, `Scheduler` and `CheckoutPreparer` with full signatures. Each type it uses exists: `FactoryLog.line` in application/machine.py, `Git.clone` in application/git.py, `InstanceSettings` in domain/settings.py, `InjectedKill` in domain/kill_points.py. The only Interface comment that states a behaviour is the `pause_after` formula, and criteria 1 and 2 test it.
   - Criteria: each one fits a single test function with concrete values. Each rule has its failing side covered: a negative `n` (2), `prepare` returning False or raising (6, 8), `tick` raising (7), a BaseException not caught (9), a checkout that already exists (11), and a directory without `.git` (12). Criterion 4 covers should_stop true from the start. The sleeps are given as a table (3, 5, 6).
   - Demo: both commands are runnable and each Expect line can be checked against the output. The second command prints only the list, since `Log.line` is never called.
   - Architecture: the scheduler and the preparer sit in `factory.application` and use only the `Git` and `FactoryLog` interfaces. The tests use real `GitCli` on a bare remote, as CLAUDE.md requires.
   - Scope: the story fits F0010's scope (the loop, its pauses, the reclone: ST7.1 and ST7.3), is not in "Out of scope", and matches decision 33.
3. tester: Wrote red tests for every criterion that a test can check, in tests/application/test_scheduler.py (new file).
   - criterion 1: tests/application/test_scheduler.py::test_pause_doubles_from_fifteen_seconds_up_to_two_minutes (parametrized over 0, 1, 2, 3, 4, 10)
   - criterion 2: ::test_negative_idle_count_is_refused (-1; the 0 side is a row of criterion 1's test)
   - criterion 3: ::test_each_iteration_prepares_then_ticks_and_the_first_comes_before_any_sleep (checks the whole order of calls: prepare, tick, sleep, … ; 3 ticks, 2 sleeps)
   - criterion 4: ::test_stop_from_the_start_calls_nothing
   - criterion 5: ::test_sleeps_follow_the_idle_count_since_the_last_activity (both tick sequences as rows)
   - criterion 6: ::test_a_failed_preparation_skips_the_tick_and_counts_as_idle
   - criterion 7: ::test_an_exception_from_the_tick_is_logged_and_counts_as_idle (the tick raises, then returns True; the loop stops after the second tick)
   - criterion 8: ::test_an_exception_from_the_preparation_is_logged_skips_the_tick_and_counts_as_idle
   - criterion 9: ::test_an_injected_kill_from_the_tick_leaves_the_loop_unlogged
   - criterion 10: ::test_a_missing_checkout_is_cloned_and_cloned_again_after_removal (GitCli on tmp_path/work/checkout, a real bare remote, origin/main resolves after each prepare)
   - criterion 11: ::test_an_existing_clone_is_kept_without_calling_git (uses the `checkout` fixture's clone; GitCli with an executable path that does not exist)
   - criterion 12: ::test_a_directory_with_files_but_no_clone_is_refused_unchanged (compares every file and directory under the checkout before and after, so a leftover `.git` would also fail the test)
   - criteria 13 and 14 are the make check gate and the docs stage's work; no test.
   The scheduler tests use a local `Loop` recorder (scripted bool or exception outcomes for each call, every call kept in order) and a local `RecordingLog(FactoryLog)`, the same kind of class test_dispatcher.py has. Not importable: `factory.application.scheduler` (ModuleNotFoundError at collection, as expected). make lint is green. I skipped the type check, as this stage's instructions say.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Built `src/factory/application/scheduler.py` (commit 273dcc0). It holds `FIRST_PAUSE`, `MAX_PAUSE`, `pause_after`, `Scheduler` and `CheckoutPreparer`, as the Interface says. All tests in tests/application/test_scheduler.py pass, and `make check` is green (coverage 99.54 %).
      - `pause_after` doubles step by step from 15 s and stops at 120 s. I rejected the literal `min(FIRST_PAUSE * 2 ** n, MAX_PAUSE)` because `timedelta` raises OverflowError once n reaches the high thirties, and a long idle run reaches that.
      - `Scheduler.run` asks `should_stop` before each iteration and again before each sleep. One iteration is `prepare() and tick()`. Any `Exception` writes `iteration failed: <type>: <message>` and counts as idle. A `BaseException` such as `InjectedKill` is not caught and leaves the loop. An activity resets the idle count to 0. The sleep is `pause_after(idle_ticks)`.
      - `CheckoutPreparer.prepare` calls `git.clone(settings.repository_url)` only when `settings.checkout / ".git"` is missing, and always returns True. A non-empty directory without `.git` fails inside `GitCli.clone`, where git itself refuses it, so it raises `GitError` and changes nothing.
      - Refactor pass: I read the diff and changed nothing. The module is small, it has no duplicates, and no existing helper does the same thing.
      - Not touched: the docs criterion (14) belongs to the documenter.

   `make check`: check: green
