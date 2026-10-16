---
stage: tests
pr: 139
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The loop survives every kind of error

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

`Scheduler.run` (`src/factory/application/scheduler.py`) keeps the instance alive. Any `Exception` that the preparation or the tick raises is logged in one line as `iteration failed: <type>: <message>` and counts as idle. A `BaseException` such as `InjectedKill` leaves the loop. F0010-S0002 tested the first rule with `ValueError` alone, and so did criteria 7 and 8. The feature acceptance's hand mutation pass narrowed `except Exception` to `except ValueError`, and the whole test suite stayed green.

The errors a real loop meets are other kinds:

- `GitError` from a fetch or a push, a `FactoryError` and not a `ValueError`;
- `OSError` from a full disk or an unwritable state directory;
- `AgentRuntimeError` from a refused `sudo` after a claim (FEATURE.md decision 20);
- any `RuntimeError` from a library.

With the narrowed handler, each of them would end `factory-run` with a traceback. Docker would restart the container, and the operator would see a restart loop where the code promises one log line.

This story pins the rule for the kinds of exception the loop meets. It is tests only: the code already behaves as the criteria say, and the coder expects to change nothing in `src/`. A test that fails means the code is wrong, and the coder fixes it within the Interface.

## Interface

No new or changed names. The behaviour pinned is that of `Scheduler(prepare=..., tick=..., sleep=..., should_stop=..., log=...).run()`:

- an exception of any of the types `GitError("git fetch", 128, "boom")`, `OSError("boom")`, `AgentRuntimeError("boom")` and `RuntimeError("boom")`, raised by `tick` or by `prepare`, is caught;
- the log gets exactly one line, `iteration failed: <type name>: <str(error)>`, for these four `iteration failed: GitError: git fetch failed (exit 128): boom`, `iteration failed: OSError: boom`, `iteration failed: AgentRuntimeError: agent runtime failed: boom` and `iteration failed: RuntimeError: boom`;
- the iteration counts as idle, so the next sleep is `pause_after(<idle ticks>)`;
- after a failed `prepare`, the tick is not called in that iteration.

The side that is not caught, a `BaseException` that is not an `Exception`, stays pinned by `test_an_injected_kill_from_the_tick_leaves_the_loop_unlogged`. The tests go in `tests/application/test_scheduler.py`, as the rows of one new parametrized test with the `Loop` recorder that the module already has; each loop stops after its second sleep. Criteria 7 and 8 of F0010-S0002 and their tests stay as they are.

## Acceptance criteria

1. For each of the four exceptions, raised by the first `tick`, with a second `tick` that returns `True`: `run` raises nothing, the log holds exactly that exception's line from the Interface, the first iteration calls `prepare` then `tick`, and the sleeps are 30 seconds (one idle tick) then 15 seconds (activity).
2. For each of the four exceptions, raised by the first `prepare`, with a second `prepare` and a `tick` that return `True`: `run` raises nothing, the log holds exactly that exception's line, the first iteration calls no `tick`, and the sleeps are 30 then 15 seconds. Criteria 1 and 2 are the eight rows of one parametrized test, with the raising side as a parameter.
3. `make check` stays green.
4. docs: none. `docs/operator-guide.md`, "The loop and its pauses", already says that an exception is logged in one line and counts as idle; these tests pin that for the errors it names.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_scheduler.py
```
Expect: the last line is `26 passed in <time>` (18 tests before this story, and the eight rows of criteria 1 and 2).

## Log (append only)

1. 2026-10-16 human: created.
2. intake: accepted
   - Interface: no new names; it pins the behaviour of `Scheduler(...).run()` (`src/factory/application/scheduler.py`, handler at line 69 is `except Exception` logging `iteration failed: <type>: <error>`). The four log lines are concrete, and I checked that `AgentRuntimeError`'s message ("agent runtime failed: ...") matches the Interface. The `Loop` recorder in `tests/application/test_scheduler.py` exists and scripts outcomes.
   - Criteria: 1 and 2 are each testable by one parametrized test (four exceptions × raising side), with exact log line, call order and sleeps (30 then 15). The failing side (BaseException not caught) is already pinned by an existing test, which the Interface names. Criteria 3 and 4 are the closing ones.
   - Demo: the pytest command is runnable. Its Expect line (`26 passed`) is checkable; I did not recount the 18 existing parametrized tests, and the module has 12 test functions.
   - Architecture: tests only, in the application layer's test folder; no layering concern.
   - Scope: inside F0010 (the loop and its pauses, decision 4); the story is listed in FEATURE.md as S0021.
