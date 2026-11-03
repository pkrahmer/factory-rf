---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 507
comments_read: [6591979242]
handed_over: approval
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
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-03T00:24:51.750512Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-03T00:29:53.390405Z'
  stage: doing
  run: f1f102da0b3c490d9b6a6ad69c873f75
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-03T00:30:13.835586Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-03T00:31:07.505100Z'
  stage: review
  run: 9458fccd5c2740daa64ef6d6a5390ca7
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-03T00:31:27.972433Z'
  stage: docs
- number: 14
  speaker: documenter
  kind: result
  at: '2026-11-03T00:31:53.665607Z'
  stage: docs
  run: 8ba28379eddf46b691b93ea81ab82589
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-03T00:32:14.138762Z'
  stage: smoke-test
- number: 16
  speaker: smoke-tester
  kind: result
  at: '2026-11-03T00:32:33.620340Z'
  stage: smoke-test
  run: 62c77b3d4d6941d1bbfa18dbf925a7c3
- number: 17
  speaker: factory
  kind: done
  at: '2026-11-03T00:34:56.949194Z'
  stage: approval
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
9. factory: started doing as vm.
10. coder: Built: `src/factory/application/scheduler.py` only.
    - `pause_after(0)` now returns `timedelta(0)`. For 1 and more idle ticks it starts at `FIRST_IDLE_PAUSE` (30 s, renamed from `FIRST_PAUSE`, which was 15 s) and doubles `idle_ticks - 1` times, capped at `MAX_PAUSE`. The result is 30, 60, then 120 s, as before. A negative count still raises `ValueError`.
    - `Scheduler.run` still checks `should_stop` after each iteration. It calls `sleep` only when `idle_ticks > 0`. A failed iteration still counts as idle, so it sleeps and the pause grows as before.

    Main choice: `run` skips the `sleep` call after activity instead of calling `sleep(0)`. The Interface says it does not call `sleep`, and criterion 2 counts the calls. I rejected keeping 15 s as the base and adding a special case for 0 in the doubling. Starting the doubling at the first idle pause states the rule directly.

    Test run: the first `make test` had 7 failures in `tests/application/test_scheduler.py`, all from the 15 s pause after activity. All of them pass now.

    Refactor: in my own diff I changed the docstring to say "Zero after activity" and updated the overflow comment to the new exponent. Nothing else needed changing.

    `make check` is green: test green (80.6 s), check green.

    The journal did not change the meaning of the task. Entry 6 approved changing the four earlier tests, and the tester did that. The Description stays as it is.

    Noticed but not touched: `docs/decisions.md` line 265 and the operator guide still describe the 15 s pause after activity. The docs stage covers them under criterion 6.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
11. factory: started review as vm.
12. reviewer: no findings

    What I checked, in `git diff main...HEAD -- . ':!factory'` (`src/factory/application/scheduler.py`, `tests/application/test_scheduler.py`) and the work item:
    - Acceptance criteria:
      - Criterion 1: the table test has rows 0, 1, 2, 3, 4 and 10, with 0 giving 0 s, so the 0/1 boundary is tested on both sides. `test_negative_idle_count_is_refused` covers -1.
      - Criterion 2: `test_activity_iterations_do_not_sleep_and_an_idle_one_sleeps_thirty_seconds` pins the whole call order and the single 30 s sleep.
      - Criterion 3: `test_failed_iterations_each_sleep_growing_and_are_each_logged` has one row where prepare raises and one where tick raises. It checks the 30/60/120 growth and the three log lines.
      - Criterion 4: `test_a_stop_requested_during_an_activity_iteration_ends_the_run_before_the_next_tick` checks that no third tick runs, that nothing sleeps, and that `should_stop` comes before every `prepare`.
      - Both Interface rules have their failing side tested: the negative count, and the sleep after an idle or failed iteration. The coder's `make check` was green (entry 10).
    - Architecture: the change stays inside `factory.application.scheduler`, with no new import and no I/O.
    - Security: nothing relevant; no silencing markers.
    - Quality:
      - `FIRST_PAUSE` is renamed to `FIRST_IDLE_PAUSE`, and no other reference to it is left in `src`.
      - The doubling loop starts at the first idle pause, and the overflow comment matches the new exponent.
      - The docstrings of `pause_after` and `Scheduler` say why. `duplicates` reports 0 new.
      - Not counted as a finding: after an activity iteration, `run` now calls `should_stop` twice in a row (the check after the iteration, then the loop condition). This is harmless and is pinned only by criterion 4's ordering check.
    - Work item hygiene:
      - Entry 10 names the main choice (no `sleep` call rather than `sleep(0)`) and the rejected alternative.
      - The Description matches what was built.
      - The docs criterion covers the operator guide paragraph that is now stale, under "The loop and its pauses", lines 121–123, which still say 15 s. It also asks for one new entry in `docs/decisions.md`. For the documenter: the entries at lines 265 and 283 cite `FIRST_PAUSE` and the 15 s pause as history; the new entry can say that they are superseded.

    Earlier tests:
    - tests/application/test_scheduler.py, changed under the human's leave in journal entry 6. Option (a) changed four earlier tests, each keeping its name: `test_each_iteration_prepares_then_ticks_and_the_first_comes_before_any_sleep`, `test_sleeps_follow_the_idle_count_since_the_last_activity`, `test_a_failed_preparation_skips_the_tick_and_counts_as_idle` and `test_every_kind_of_error_the_loop_meets_is_logged_once_and_counts_as_idle`.
      - That last test now stops after its second iteration instead of at its second tick; on the prepare side the second iteration holds the first tick. This matches the intent of option (a): it cannot hang.
      - The table test was renamed to `test_pause_is_none_after_activity_and_doubles_from_thirty_seconds_up_to_two_minutes`. Criterion 1 allows changing it, and entry 6 approves the new name.
13. factory: started docs as vm.
14. documenter: Changed two files, both documents, so I did not run `make check` (the factory's checks decide).
    - `docs/operator-guide.md`, *The loop and its pauses*:
      - The first-iteration rule now says there is no pause after it when its tick found activity, and 30 seconds when it was idle.
      - The pause paragraph now says there is no pause after activity, and that idle pauses are 30, 60 and 120 seconds, each failed iteration counting as idle.
    - `docs/decisions.md`: one new entry, "No pause after a tick that found activity". It gives the reason (about twenty hand-overs a story, about five minutes in pauses, F0048 decision 17), the rejected `sleep(0)` and the 15-second base with a special case for zero. It marks the older 15-second wording as superseded.

    Checked against the diff (`src/factory/application/scheduler.py`): the code matches the Interface and the docs, and I found nothing to send back to the coder.

    Cross-read and found current: `README.md`; the rest of `docs/operator-guide.md`, including the idle-shutdown paragraph ("the pauses above are unchanged" is still true) and the repository-stop text ("pauses as for any idle iteration"); `docs/project-guide/watching.md`, whose remark about the loop's pauses is generic. I did not run the smoke command; it follows from the code diff (0 → 0.0, 1 → 30.0).

    Stale text I left alone: the entries of 2026-10-16 in `docs/decisions.md` (lines 265 and 283) still cite `FIRST_PAUSE` and the 15-second pause. They are dated history, and the new entry says it supersedes them.

    `check`: check: green (not run again: passed on tree d5a566d5a04c at 2026-11-03T00:28:21Z)
    `secrets`: secrets: green (2.1 s)
    `documents`: documents ok
15. factory: started smoke-test as vm.
16. smoke-tester: I ran the one command under `## Smoke test` from the repository root, exactly as written. I fixed nothing.

    Command 1:
    ```bash
    uv run python -c "from factory.application.scheduler import pause_after; print(pause_after(0).total_seconds(), pause_after(1).total_seconds())" 2>/dev/null
    ```
    Output (the exit status was 0):
    ```
    0.0 30.0
    ```
    Expect: `0.0 30.0`. Met.

    Against the acceptance criteria:
    - Criterion 1: the output agrees with it. 0 idle ticks gives 0 s, and 1 gives 30 s, which is unchanged.
    - Criteria 2 to 5: the output does not contradict any of them. The command does not exercise `Scheduler.run`, so for `run` I relied on the earlier stages: the reviewer's checks (entry 12) and the green `make check` (entries 10 and 14).
    - Criterion 6: I read `docs/operator-guide.md:123`. It now says there is no pause after activity, that idle pauses are 30, 60 and 120 seconds, and that a failed iteration counts as idle. That agrees with the output.

    Findings: none.
17. factory: done (pull request merged); cost: 7 runs, 6.6 min, 42 turns, 185403 tokens in (715429 more from cache), 20293 out, $1.77
