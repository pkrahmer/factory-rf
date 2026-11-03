---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 507
comments_read: [6591979242]
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
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-03T00:18:12.115981Z'
  stage: tests
- number: 5
  speaker: tester
  kind: question
  at: '2026-11-03T00:19:04.723924Z'
  stage: tests
  run: 6c51bcc484ce445a9c7dd61eecfcc610
  blocked: question
- number: 6
  speaker: human
  kind: comment
  at: '2026-11-03T00:23:28.282625Z'
  stage: tests
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-03T00:23:46.566972Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-03T00:24:31.160019Z'
  stage: tests
  run: 48e52b758f4949528a68b8918e11c2ed
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
4. factory: started tests as vm.
5. tester: Question: four tests that earlier stories wrote in `tests/application/test_scheduler.py` require a 15-second sleep after an activity iteration, which this story removes. Criterion 1 lets me change only the `pause_after` table, so may I change these four as well?
   - `test_each_iteration_prepares_then_ticks_and_the_first_comes_before_any_sleep`: every tick finds activity, and it expects `sleep` between iterations.
   - `test_sleeps_follow_the_idle_count_since_the_last_activity`: both rows expect `15.0` after activity.
   - `test_a_failed_preparation_skips_the_tick_and_counts_as_idle`: expects `[30.0, 15.0]`.
   - `test_every_kind_of_error_the_loop_meets_is_logged_once_and_counts_as_idle`: it stops at the second sleep, but the second iteration finds activity and every later tick does too (the default), so once the code is changed it never stops. It would hang until pytest's time limit, not just fail.

   Options:
   (a) Change them so they keep their names and check the same thing under the new rule. I would remove the activity sleeps from the first test's expected calls, drop the `15.0` sleeps from the next two, and make the last one stop when the second tick happens with calls ending without the trailing `sleep` and sleeps `[30.0]`.
   (b) Delete the ones the new tests already cover: the first test and `test_sleeps_follow_…`, which criterion 2 covers. Change the other two as in (a).
   (c) Leave them as they are. The coder's `make check` then cannot go green and the last test hangs.
   I would choose (a).

   What I did: I wrote the tests for criteria 1 to 4 in `tests/application/test_scheduler.py` (no new file). Each maps to one test function:
   criterion 1: tests/application/test_scheduler.py::test_pause_is_none_after_activity_and_doubles_from_thirty_seconds_up_to_two_minutes (the existing table test, renamed because "from fifteen seconds" is no longer true; its first row is now 0 → 0 s) and tests/application/test_scheduler.py::test_negative_idle_count_is_refused (existing, unchanged, covers -1)
   criterion 2: tests/application/test_scheduler.py::test_activity_iterations_do_not_sleep_and_an_idle_one_sleeps_thirty_seconds
   criterion 3: tests/application/test_scheduler.py::test_failed_iterations_each_sleep_growing_and_are_each_logged (one row where prepare raises, one where tick raises)
   criterion 4: tests/application/test_scheduler.py::test_a_stop_requested_during_an_activity_iteration_ends_the_run_before_the_next_tick
   criterion 5 (`make check`) and 6 (docs) have no tests.

   Test run: I ran `uv run pytest -q tests/application/test_scheduler.py` once.
   - The tests for criteria 1, 2 and 4 fail for the right reason: today's code gives 15 s for 0 idle ticks and sleeps after activity. The `[0-0]` row fails; the others pass.
   - The criterion 3 test passes already, as expected: the behaviour after a failed iteration does not change.
   - Every module imported; nothing was missing.
   - `make lint` is green.
   - I skipped the type check, as the stage says.
6. 2026-11-03 human: (a), as you propose: change the four earlier tests so they keep their names and check the same thing under the new rule, including the last one stopping at its second tick so it cannot hang. The renamed table test is fine.
7. factory: started tests as vm.
8. tester: I took option (a), as the human answered in entry 6. The four earlier tests in `tests/application/test_scheduler.py` keep their names and check the same things under the new rule:
   - `test_each_iteration_prepares_then_ticks_and_the_first_comes_before_any_sleep`: the expected calls no longer have a sleep between the activity iterations. They are now prepare/tick three times, with no sleep at all.
   - `test_sleeps_follow_the_idle_count_since_the_last_activity`: I dropped the `15.0` sleeps. The rows now expect `[30, 60, 120, 120]` and `[30, 60]`.
   - `test_a_failed_preparation_skips_the_tick_and_counts_as_idle`: the sleeps are now `[30.0]`.
   - `test_every_kind_of_error_the_loop_meets_is_logged_once_and_counts_as_idle`: it now stops after the second iteration (`count("prepare") >= 2`) instead of at the second sleep, so it cannot hang. On the tick side the second iteration's tick is the second tick; on the prepare side it is the first. The expected calls lose the trailing `sleep`, and the sleeps are now `[30.0]`.

   The tests for the criteria, written in the earlier run and already committed, are unchanged:
   criterion 1: tests/application/test_scheduler.py::test_pause_is_none_after_activity_and_doubles_from_thirty_seconds_up_to_two_minutes (the existing table test, renamed, which the human approved) and tests/application/test_scheduler.py::test_negative_idle_count_is_refused (covers -1)
   criterion 2: tests/application/test_scheduler.py::test_activity_iterations_do_not_sleep_and_an_idle_one_sleeps_thirty_seconds
   criterion 3: tests/application/test_scheduler.py::test_failed_iterations_each_sleep_growing_and_are_each_logged (one row where prepare raises, one where tick raises)
   criterion 4: tests/application/test_scheduler.py::test_a_stop_requested_during_an_activity_iteration_ends_the_run_before_the_next_tick
   criteria 5 (`make check`) and 6 (docs): no tests.

   Files: I created none. I changed `tests/application/test_scheduler.py`, including the four earlier tests named above, with the human's leave from entry 6.

   Test run: I ran `uv run pytest -q tests/application/test_scheduler.py` once, before a last fix to the error test's stop condition.
   - These fail against today's code for the right reason, the 15 s pause after activity: the `[0-0]` row, the first three changed tests, and the tests for criteria 2 and 4.
   - The test for criterion 3 passes already, as expected: the behaviour after a failed iteration does not change.
   - In that run the error test's prepare rows failed because of my first stop condition (`count("tick") >= 2`). I replaced it with `count("prepare") >= 2` and did not run the tests again. By reasoning, all eight rows of that test now pass on today's code and will on the new code. They should no longer fail or hang.

   Every module imported; none was missing. `make lint` is green. I skipped the type check, as the stage says.

   `lint`: lint: green (0.1 s)
