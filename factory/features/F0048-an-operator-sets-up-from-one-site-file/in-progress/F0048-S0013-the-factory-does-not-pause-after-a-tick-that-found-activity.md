---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 507
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T00:17:32.160334Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T00:17:32.166646Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-03T00:17:51.589266Z'
  stage: intake
  run: cec122e6f2024695b657f783e5bbfa8a
---

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

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: `src/factory/application/scheduler.py` names `pause_after` and `Scheduler.run`. I compared them with the code: `pause_after(0)` is 15 s today and 1, 2, 3 and up give 30, 60 and 120 s, so "unchanged from 1" is true. The negative `ValueError` exists. `run` sleeps after every iteration today, so the change is concrete. Both stated behaviours (0 gives zero, no sleep after activity) have a criterion.
   Criteria: all testable by one test function each. 1 is the existing parametrized test with its rows changed, including the -1 refusal. 2 pins the activity-then-idle sleep count and the 30 s value. 3 covers the failing side: an iteration that raises still sleeps with growth, and logs the line. 4 covers `should_stop` before each iteration. 5 and 6 are the closing criteria in order. Each rule has both its passing and failing side.
   Smoke test: the command is runnable and has no pytest `-q` issue. `Expect: 0.0 30.0` can be checked against the printed output.
   Architecture: the change stays in `factory.application.scheduler`, which has no new import or layer crossing.
   Scope: it matches feature.md, whose story list includes S0013 and decision 17. It touches no Out of scope item. The docs criterion names the operator guide's *The loop and its pauses* and `docs/decisions.md`. The guide's current text, "15 seconds when the tick found activity" and the first-iteration rule, is what the story rewrites.
