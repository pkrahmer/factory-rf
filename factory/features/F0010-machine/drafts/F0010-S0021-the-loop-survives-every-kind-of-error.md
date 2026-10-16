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
- the log gets exactly one line, `iteration failed: <type name>: <str(error)>`;
- the iteration counts as idle, so the next sleep is `pause_after(<idle ticks>)`;
- after a failed `prepare`, the tick is not called in that iteration;
- `KeyboardInterrupt`, like `InjectedKill`, is not caught and leaves `run`.

The constructors of the errors follow `src/factory/domain/errors.py`; the tester uses each one's real signature. The tests go in `tests/application/test_scheduler.py`, as rows of one new parametrized test with the `Loop` recorder that the module already has. Criteria 7 and 8 of F0010-S0002 and their tests stay as they are.

## Acceptance criteria

1. For each of the four exception types, raised by the first `tick`, with a second `tick` that returns `True`: `run` raises nothing, and the log holds exactly the one line `iteration failed: <type name>: <message>`. The first sleep is 30 seconds (one idle tick) and the second is 15 seconds (activity). One parametrized test, one row per type.
2. For each of the four exception types, raised by the first `prepare`: `run` raises nothing, the log holds exactly the one line, the first iteration calls no `tick`, and the first sleep is 30 seconds. Rows of the same parametrized test as criterion 1, with the raising side as a parameter.
3. `KeyboardInterrupt` raised by the `tick` leaves `run` as `KeyboardInterrupt`, and the log holds no line.
4. `make check` stays green.
5. docs: none. `docs/operator-guide.md`, "The loop and its pauses", already says that an exception is logged in one line and counts as idle; these tests pin that for the errors it names.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider -q tests/application/test_scheduler.py
```
Expect: the last line is `<n> passed in <time>`, with n at least 9 more than before this story (eight rows for criteria 1 and 2, one test for criterion 3).

## Log (append only)

1. 2026-10-16 human: created.
