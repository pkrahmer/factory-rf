# The first pause in the operator guide

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

`docs/operator-guide.md`, section "The loop and its pauses", says: "The first iteration is idle whatever the tick found, so the first pause is 30 seconds." The code says otherwise. `Scheduler.run` (`src/factory/application/scheduler.py`) treats the first iteration like every other one, and `activity_tick` (`src/factory/entry/run.py`) returns `activity(tick.run())` from the first call on. A first tick that handles an event other than `idle` (a start, a question) is followed by a pause of 15 seconds. Only an idle first tick is followed by 30 seconds. The feature acceptance's demo showed this: its first tick ran the intake stage and paused 15 seconds.

The sentence came from F0010-S0004's criterion 9. That criterion runs over a remote with nothing to do, so its tick is idle, and its "whatever the tick found" describes that test's setup, not a rule. The documenter generalised it.

This story is documentation only: no code and no test changes. It replaces the sentence with the rule the code follows. It also repairs one stale cell in `docs/project-guide.md`, the git wrapper's table row for `fetch`, `remote_branches`, … `push`. That cell still says "no story names a single user yet", but the tick, the stages and the claim all use those operations now.

## Interface

No code. Two files change:

- `docs/operator-guide.md`, "The loop and its pauses": the first iteration runs at once and follows the same rule as every other iteration. The pause after it is 15 seconds when its tick handled an event other than `idle`, and 30 seconds otherwise (one idle tick). The sentence "The first iteration is idle whatever the tick found, so the first pause is 30 seconds" is gone.
- `docs/project-guide.md`, the table of the git wrapper's operations: the row for `fetch`, `remote_branches`, `resolve`, `show_file`, `list_files`, `is_ancestor`, `log`, `clone`, `checkout`, `commit`, `push` no longer says "no story names a single user yet". It names their users instead: the tick, the stages, the claim, and the checkout preparer for `clone`.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/operator-guide.md` "The loop and its pauses" states that the pause after the first iteration is 15 seconds when its tick handled an event other than `idle`, and 30 seconds when it was idle, and no longer says the first iteration is idle whatever the tick found. `docs/project-guide.md`'s git operations table no longer says "no story names a single user yet". The documenter cross-reads `README.md` and `docs/decisions.md` for the same claim.

## Demo

```bash
grep -n -F 'idle whatever the tick found' docs/operator-guide.md; grep -n -F 'no story names a single user yet' docs/project-guide.md; echo "exit=$?"
```
Expect: no matching line, then `exit=1`.

```bash
uv run python -c "
from factory.application.scheduler import Scheduler
for active in (True, False):
    sleeps = []
    Scheduler(prepare=lambda: True, tick=lambda: active, sleep=sleeps.append, should_stop=lambda: len(sleeps) >= 1, log=None).run()
    print(active, sleeps)
"
```
Expect: two lines, `True [15.0]` and `False [30.0]`, matching what the operator guide now says.

## Log (append only)

1. 2026-10-16 human: created.
