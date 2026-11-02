# The factory does not pause after a tick that found activity

## Description

After every iteration whose tick found activity the instance pauses 15 seconds before its next tick. A story hands over between its stages about twenty times, so a story spends about five minutes in these pauses, a tenth of its time, while the work is ready to go on. The pause exists to keep an instance from asking the code host again and again while nothing changes; after activity there is no such reason, because the next tick has work. This story drops the pause after activity: the next iteration starts at once. The pauses after idle ticks stay as they are (30, 60, then 120 seconds), and an iteration that fails still counts as idle, so an instance that only meets errors or a standing stop keeps backing off.

## Interface

`src/factory/application/scheduler.py`

- `pause_after(0)` is `timedelta(0)`. `pause_after(n)` for `n` of 1 and more is unchanged: 30, 60, then 120 seconds from 3 on. A negative count is still refused with `ValueError`.
- `Scheduler.run`: after an iteration whose tick found activity it does not call `sleep`; it checks `should_stop` and starts the next iteration. After an idle or failed iteration it sleeps `pause_after(idle_ticks)` as today.

## Acceptance criteria

1. `pause_after` gives 0, 30, 60, 120, 120 and 120 seconds for 0, 1, 2, 3, 4 and 10 idle ticks (rows of one parametrized test, the existing one changed), and refuses -1.
2. A run of three iterations that find activity, then one idle iteration, then a stop, calls `sleep` once, with 30 seconds, after the idle iteration.
3. A run whose iterations fail (prepare or tick raises) still sleeps after each, growing as today, and logs `iteration failed: <exception type>: <message>` for each.
4. `should_stop` is still asked before every iteration: a stop requested during an activity iteration ends the run before the next tick.
5. `make check` stays green.
6. docs: `docs/operator-guide.md`, the instance's loop (*An instance repeats one iteration*): no pause after an iteration that found activity, the idle pauses 30, 60 and 120 seconds, and the first iteration's rule restated (no pause after it when it found activity, 30 seconds when it was idle); `docs/decisions.md`: one entry, the reason (the hand-overs of a story, about five minutes in pauses, F0048 decision 17); `README.md` and the other documents: none.

## Smoke test

```bash
uv run python -c "from factory.application.scheduler import pause_after; print(pause_after(0).total_seconds(), pause_after(1).total_seconds())" 2>/dev/null
```

Expect: `0.0 30.0`.

## Journal
