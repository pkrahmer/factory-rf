---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 542
comments_read: [6633278047, 6634278570, 6634494947]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T14:22:54.868675Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T14:22:54.875427Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-04T14:23:19.708543Z'
  stage: intake
  run: a95ab27cceb64c3091dcc3fc2106828a
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-04T14:31:26.065363Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-04T14:31:29.781306Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-04T14:31:52.155648Z'
  stage: intake
  run: 674bc08686514862aed357edc80cbb89
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-04T14:31:58.485851Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-04T14:49:14.386835Z'
  stage: tests
  run: d8bef35f8c6746e7b8eef074bebc42b8
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-04T14:49:20.687350Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-04T15:00:56.640501Z'
  stage: doing
  run: 5c0e524494694c48acd6cdd8e4627e4e
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-04T15:13:12.132976Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-04T15:13:15.697178Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-04T15:13:37.986085Z'
  stage: doing
  run: 99f72d43d2e4467a9cdc43d95c13d4ff
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-04T15:13:44.631580Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-04T15:14:26.652106Z'
  stage: tests
  run: 43aeb62bd64d41b2af91152bc65008be
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-04T15:14:33.642174Z'
  stage: doing
- number: 17
  speaker: coder
  kind: question
  at: '2026-11-04T15:17:19.694353Z'
  stage: doing
  run: 7a688b7a31b14b53a60d59b2aab9e706
  blocked: question
- number: 18
  speaker: human
  kind: comment
  at: '2026-11-04T15:23:20.892601Z'
  stage: doing
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-04T15:23:24.572329Z'
  stage: doing
- number: 20
  speaker: coder
  kind: result
  at: '2026-11-04T15:23:45.104012Z'
  stage: doing
  run: 729b091edc144db0811584a17dbc4633
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-04T15:23:51.732732Z'
  stage: tests
- number: 22
  speaker: tester
  kind: result
  at: '2026-11-04T15:24:23.453891Z'
  stage: tests
  run: 8672c5cfee9f48ccafdd868bd1faae83
- number: 23
  speaker: factory
  kind: started
  at: '2026-11-04T15:24:29.704776Z'
  stage: doing
- number: 24
  speaker: coder
  kind: result
  at: '2026-11-04T15:28:23.657638Z'
  stage: doing
  run: 7e692fb34c324dd3835d9cfcfd810037
---

# One fetch per iteration

## Description

Since F0049-S0003 and S0004 the factory fetches twice in every iteration: once before the tick, where it compares the stage file on a new `main` (`_ProjectImageStart._follow_main` in `factory.entry.run`), and once more at the start of the tick itself (`factory.application.tick`). The second fetch finds nothing new in almost every case, but it costs a call to the remote and its time in every iteration, and both places raise and clear `fetch_failed` on their own. This story makes the factory fetch once per iteration: the fetch before the tick serves the tick too, and `fetch_failed` is raised and cleared in one place. What the tick sees of `origin/main` and of the work-item branches does not change.

## Interface

- `Tick.run(fetched: bool = False)` in `factory.application.tick`: with `fetched=True` it skips `git.fetch()` and its raise and clear of `fetch_failed`, because the caller already fetched; the default fetches as today.
- `_ProjectImageStart._follow_main` in `factory.entry.run` keeps the one fetch and the one raise and clear of `fetch_failed` in an iteration, and passes `fetched=True` to the tick of the same iteration. One iteration of `factory-run` calls `Git.fetch` once; the tick still works on a fresh `origin/main` and fresh work-item branches.
- `src/factory/application/scheduler.py:126` stays as it is: `prepare()` fetches there only when the checkout is not ready yet.
- A failed fetch stands as `fetch_failed` (S0004 of F0049), raised in one place, and ends the iteration without a tick; a passed fetch clears it.
- `factory-watch` and every other caller of the tick keep fetching as today, when they run the tick without the fetch before it.

## Acceptance criteria

1. One iteration of `factory-run` with a passed fetch calls `Git.fetch` exactly once and runs the tick on what that fetch brought: rows for a new commit on `main` and for a new commit on a work-item branch, each seen by the same iteration's tick.
2. One iteration with a failed fetch calls `Git.fetch` once, raises `fetch_failed` with the fetch's first line in its detail, and runs no tick; the next iteration with a passed fetch clears the stop and runs the tick.
3. A tick run without the fetch before it (as `factory-watch` runs it) still fetches once.
4. A tick run alone (`fetched=False`) whose fetch fails raises `fetch_failed` and runs nothing; the next one with a passed fetch clears it, as today.
5. `make check` stays green.
6. docs: `docs/project-guide/` in the file on the tick or the stage environment: where the iteration fetches, once. `docs/operator-guide.md` and `docs/decisions.md`: none, unless an existing sentence says the tick fetches; then that sentence follows. `README.md`: none.

## Smoke test

```bash
grep -rn 'git.fetch()' src/factory/application src/factory/entry | wc -l
uv run pytest tests/entry tests/application -k fetch 2>&1 | tail -1
```

Expect: a number not larger than before the story (3 on `main` when it was written), then a line that ends in `passed` with no `failed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed):

   1. The Interface names no concrete seam. "The coder decides which of the two places keeps it and how the other learns that the fetch was made" leaves the tester without a signature to write tests against. Two testers could pick different seams, and both would pass criteria 1 to 3. Please name the seam. For example: `Tick.run(fetched: bool = False)` in `factory.application.tick`, which skips `git.fetch()` when the caller already fetched; `_ProjectImageStart._follow_main` in `factory.entry.run` keeps the one fetch and the one raise and clear of `fetch_failed`. I would choose this option, because `factory-watch` then keeps today's default.

   2. `src/factory/application/scheduler.py:126` also calls `self._boundaries.git.fetch()`. The Description and the smoke test count three calls on `main`: tick.py:148, scheduler.py:126 and run.py:235. The story does not say what that call does, or whether it is in the iteration's path. Please say if it belongs to this story (for example, if it is the tick's fetch via the scheduler) or stays as it is. The smoke test's "not larger than before" count depends on the answer.

   3. The Interface says a failed fetch is "raised in one place". Criterion 2 tests this only through `factory-run`. A tick run without the fetch before it, as `factory-watch` runs it, also raises and clears `fetch_failed` at tick.py:148. Does criterion 3 cover that failing side? Please add a criterion for it: a tick run alone with a failed fetch stops as it does today, or the Interface says it no longer raises it. Without this the failing side of the "keep fetching as today" rule has no test.

   4. Criterion 1 has two clauses, a new commit on `main` and a new commit on a work-item branch, in one criterion. A single test function cannot easily show both. Please split it into two criteria, or confirm that one test with two assertions is meant.

   The other checks passed. The smoke test is runnable, and `addopts` already sets `-q`, so the `tail -1` summary line exists. The scope fits the feature (S0004 in `feature.md`). The layers hold: the entry fetches and the application tick receives the knowledge.
4. 2026-11-04 human: Answers of the human:

   1. Yes, as you propose: `Tick.run(fetched: bool = False)` in `factory.application.tick` skips `git.fetch()` (and its raise and clear of `fetch_failed`) when the caller already fetched; `_ProjectImageStart._follow_main` in `factory.entry.run` keeps the one fetch and the one raise and clear of `fetch_failed`, and passes `fetched=True` to the tick of the same iteration. `factory-watch` and every other caller keep the default. Put this into the Interface.

   2. `scheduler.py:126` stays as it is. It is not in a normal iteration: `prepare()` fetches there only when the checkout is not ready yet (no `origin/main` or no pipeline definition), as its comment says. The smoke test's count stays "not larger than 3".

   3. Yes: add a criterion that a tick run alone (with `fetched=False`) whose fetch fails raises `fetch_failed` and runs nothing, and that the next one with a passed fetch clears it, as today.

   4. One parametrized test with two rows (a new commit on `main`, a new commit on a work-item branch), as the project's tests do for the sides of one rule; the criterion stays one.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: carried in the human's answers from journal entry 4 (answers 1 and 2). It now names `Tick.run(fetched: bool = False)` in `factory.application.tick`. It names `_ProjectImageStart._follow_main` in `factory.entry.run` as the one fetch and the one raise and clear of `fetch_failed`, passing `fetched=True` to the tick. It also says `scheduler.py:126` stays as it is. These are the human's edits carried in; I added nothing of my own.
   - Criteria: carried in from answer 3 as new criterion 4: a tick run alone (`fetched=False`) whose fetch fails raises `fetch_failed` and runs nothing, and the next one with a passed fetch clears it. The closing two are now 5 and 6. Per answer 4, criterion 1 stays one criterion, tested by one parametrized test with two rows (a new commit on `main`, a new commit on a work-item branch). Each criterion is testable by one test function. Both sides of the fetch rule are covered: failed and passed in criterion 2 for `factory-run`, and in criterion 4 for a tick run alone. Criterion 3 covers the default fetching once.
   - Smoke test: runnable. `addopts` already sets `-q`, so `tail -1` shows the summary line. The Expect line is checkable: a count not larger than 3 (answer 2 confirms it), then a line ending in `passed` with no `failed`.
   - Architecture: the entry layer fetches and the application tick receives the flag, so no layer rule is broken. No new interface or dependency.
   - Scope: within S0004 of `feature.md` and not in its Out of scope. The Description is unchanged in meaning.
7. factory: started tests as vm.
8. tester: Wrote the tests for criteria 1–4. They are red on purpose and form the coder's specification.

   - criterion 1: tests/entry/test_run_one_fetch.py::test_an_iteration_fetches_once_and_its_tick_sees_what_that_fetch_brought (parametrized: `new-commit-on-main`, `new-commit-on-branch`)
   - criterion 2: tests/entry/test_run_one_fetch.py::test_a_failed_fetch_in_an_iteration_stands_as_fetch_failed_and_the_next_passed_one_clears_it
   - criterion 3: tests/application/test_tick_own_fetch.py::test_a_tick_run_without_the_fetch_before_it_fetches_once (parametrized: `default` = `tick.run()`, `fetched-false` = `tick.run(fetched=False)`)
   - criterion 4: tests/application/test_tick_own_fetch.py::test_a_tick_run_alone_whose_fetch_fails_stops_and_the_next_passed_one_clears_it
   - criteria 5 and 6 (make check, docs): no test.

   Files created: tests/application/test_tick_own_fetch.py, tests/entry/test_run_one_fetch.py. No earlier test file was changed.

   How the tests work:
   - The entry tests run `run_instance` against a real local remote. `GitCli.fetch` is wrapped through monkeypatch so it counts every call and still runs the real fetch.
   - `run_module.build_tick` is replaced by a real `Tick` whose handler, for every event, records what the tick's checkout holds as `origin/main` and `origin/<branch>`.
   - Iterations are separated at `sleep`, which is called after each idle iteration.
   - The work-item branch is `work-item/F0001-S0009`, which has no story. I chose this because a started work item makes the tick active, and an active tick never calls `sleep`, so the loop never pauses (my first attempt hung for that reason). A cap of 20 handled events in `should_stop` makes a loop that never pauses fail instead of hang.
   - The application tests use a `GitCli` subclass that counts its fetches on the test's checkout. They break the remote by renaming it away, as tests/application/test_tick.py does.

   The one run, `uv run pytest -q` on the two files:
   - Failing for the right reason:
     - both criterion 1 rows: `assert 2 == 1`, i.e. two fetches in the iteration today
     - the `fetched-false` row of criterion 3 and the criterion 4 test: `TypeError: Tick.run() got an unexpected keyword argument 'fetched'`
   - Passing already:
     - the `default` row of criterion 3: today's tick already fetches once
     - criterion 2: a failed fetch before the tick already ends the iteration after one fetch. This test guards that behaviour so it stays.

   No module failed to import: the tests reach the missing `fetched` parameter only when they call `Tick.run`.

   `make lint` is green. The type check was skipped, as this stage says.

   Note for review: `Instance.go_away`/`come_back` in the new entry test repeat the same two methods of `Outage` in tests/entry/test_run_fetch_before_tick.py. I did not use the standing leave to move them into a shared helper. If the reviewer counts the copy as a finding, that move is the tester's to make.

   `lint`: lint: green (0.2 s)
9. factory: started doing as vm.
10. coder: Question: the Interface's `Tick.run(fetched: bool = False)` breaks six test doubles that subclass `Tick` and override `run(self)` with no parameters. Other stories wrote them, and the standing leave does not cover changing them. Which way do you want it?

    What I did. The implementation is in the working tree:
    - `src/factory/application/tick.py`: `run(self, *, fetched: bool = False)` skips `_fetch()` when `fetched` is true. The disk check still runs first.
    - `src/factory/entry/run.py`: `activity_tick(tick, idle=None, *, fetched=False)` passes the flag on. `_ProjectImageStart._choose` builds the tick with `fetched=True`, since `_follow_main` fetches and raises or clears `fetch_failed` before every tick.

    With it, the new tests in `tests/entry/test_run_one_fetch.py` and `tests/application/test_tick_own_fetch.py` pass: `uv run pytest -q` on those two files gives `......` with no failure.

    `make check` is red: I did not run the whole target, but mypy alone fails. These test doubles still override `run(self)`:
    - `tests/entry/test_run_stop_requested.py:31` (`AskingTick`)
    - `tests/entry/test_run_project_image_rebuild.py:75` (`RecordingTick`)
    - `tests/entry/test_run_image_sizes.py:39` (`SeeingTick`)
    - `tests/entry/test_run_fetch_before_tick.py:54` (`RecordingTick`)
    - `tests/entry/test_run_idle_shutdown.py:21` (`_ScriptedTick`)
    - `tests/scripted_tick_support.py:44` (`ScriptedTick`)

    Two failures follow:
    - `mypy --strict` reports `Signature of "run" incompatible with supertype "factory.application.tick.Tick"  [override]` for each, ending in `Found 6 errors in 6 files`.
    - At runtime, the ones that `run_instance` builds now get `fetched=True`, for example `iteration failed: TypeError: SeeingTick.run() got an unexpected keyword argument 'fetched'` and then `tests/entry/test_run_image_sizes.py:84: AssertionError`.

    Options:
    - A (my choice): the tester changes only the signature of those six overrides to `def run(self, *, fetched: bool = False) -> TickOutcome:` and leaves their bodies alone, so each test still checks the same thing. The code stays as the Interface says, and the coder then only re-runs `make check`.
    - B: a different seam that leaves `Tick.run()` without a parameter, for example a constructor flag on `Tick` or a no-op fetch in the boundaries the entry hands to the tick. This contradicts the Interface. It also fails the new tests, which call `tick.run(fetched=False)` (criteria 3 and 4) and replace `build_tick` with a plain `Tick(boundaries, ...)` (criteria 1 and 2). It would need new tests as well.

    With A, the next coder round ends with `tests`, naming the six signatures.

    Noticed, not touched: the tester's note that `Instance.go_away`/`come_back` in `tests/entry/test_run_one_fetch.py` copy `Outage` in `tests/entry/test_run_fetch_before_tick.py`. I did no refactor step, because the stage stops here. The project guide was not changed: that is the docs stage's work.
11. 2026-11-04 human: Answer of the human: **A** "the tester changes only the signature of those six overrides to `def run(self, *, fetched: bool = False) -> TickOutcome:` and leaves their bodies alone, so each test still checks the same thing."

    Leave for the tester: in exactly the six places you list (`tests/entry/test_run_stop_requested.py:31`, `tests/entry/test_run_project_image_rebuild.py:75`, `tests/entry/test_run_image_sizes.py:39`, `tests/entry/test_run_fetch_before_tick.py:54`, `tests/entry/test_run_idle_shutdown.py:21`, `tests/scripted_tick_support.py:44`), only the signature of `run`; nothing else in those modules. The copy of `Outage` in `tests/entry/test_run_one_fetch.py` may move to one shared place under the standing leave. End with `tests` as you propose.
12. factory: started doing as vm.
13. coder: Test change, as the human answered in entry 11 (option A). In each of these six test doubles, change only the signature of `run` to `def run(self, *, fetched: bool = False) -> TickOutcome:` and leave the bodies as they are: `tests/entry/test_run_stop_requested.py:31` (`AskingTick`), `tests/entry/test_run_project_image_rebuild.py:75` (`RecordingTick`), `tests/entry/test_run_image_sizes.py:39` (`SeeingTick`), `tests/entry/test_run_fetch_before_tick.py:54` (`RecordingTick`), `tests/entry/test_run_idle_shutdown.py:21` (`_ScriptedTick`), `tests/scripted_tick_support.py:44` (`ScriptedTick`). The human also allowed an optional move under the standing leave: `Instance.go_away`/`come_back` in `tests/entry/test_run_one_fetch.py` copy `Outage` in `tests/entry/test_run_fetch_before_tick.py`, and that copy may move to one shared place under `tests/`.

    The code change is already on the branch, from the earlier doing run:
    - `src/factory/application/tick.py`: `run(self, *, fetched: bool = False)` skips the fetch when the caller has already fetched.
    - `src/factory/entry/run.py`: `activity_tick(..., fetched=...)` passes the flag on, and `_ProjectImageStart` builds its tick with `fetched=True`.

    I changed no code in this run. Not checked in this run: I did not re-run `make check`. It stays red until the six signatures change, because `mypy --strict` reports an `[override]` error for each of them. Once the tester sends the work item back, I run `make check` and do the refactor step.
14. factory: started tests as vm.
15. tester: Approved test change (the human's answer in entry 11, option A, named by the coder in entry 13). I changed only the signature of `run` to `def run(self, *, fetched: bool = False) -> TickOutcome:` in the six test doubles below. Their bodies and everything else in those modules are unchanged, so each test still checks the same thing.
    - tests/entry/test_run_stop_requested.py:31 (`AskingTick`)
    - tests/entry/test_run_project_image_rebuild.py:75 (`RecordingTick`)
    - tests/entry/test_run_image_sizes.py:39 (`SeeingTick`)
    - tests/entry/test_run_fetch_before_tick.py:54 (`RecordingTick`)
    - tests/entry/test_run_idle_shutdown.py:21 (`_ScriptedTick`)
    - tests/scripted_tick_support.py:44 (`ScriptedTick`)

    Criterion → test mapping, unchanged from entry 8:
    - criterion 1: tests/entry/test_run_one_fetch.py::test_an_iteration_fetches_once_and_its_tick_sees_what_that_fetch_brought
    - criterion 2: tests/entry/test_run_one_fetch.py::test_a_failed_fetch_in_an_iteration_stands_as_fetch_failed_and_the_next_passed_one_clears_it
    - criterion 3: tests/application/test_tick_own_fetch.py::test_a_tick_run_without_the_fetch_before_it_fetches_once
    - criterion 4: tests/application/test_tick_own_fetch.py::test_a_tick_run_alone_whose_fetch_fails_stops_and_the_next_passed_one_clears_it

    Files created: none in this run. The earlier test files I changed are the six above, under the human's leave in entry 11. Every module imported.

    Not done: the optional move of the `Outage` copy (`Instance.go_away`/`come_back` in tests/entry/test_run_one_fetch.py) to a shared place. The human allowed it but did not require it, and I kept this run to exactly the approved change. It can still be made under the standing leave if review counts the copy as a finding.

    The one run was `uv run pytest -q` on the six changed modules, the test modules that use scripted_tick_support, and the two new test files. All 45 tests passed, with no failure. `make lint`: lint: green (0.1 s). I skipped the type check, as this stage says; the coder's `make check` covers it.

    `lint`: lint: green (0.1 s)
16. factory: started doing as vm.
17. coder: Question: one more test double breaks on the new `fetched` flag. It is a seventh place, outside the six signatures your leave in entry 11 covered. How do you want it handled?

    The test: `tests/entry/test_run.py::test_run_instance_hands_the_idle_shutdown_of_its_settings_to_the_activity_tick` (both rows, `0-None` and `30-limit1`). It replaces `run_module.activity_tick` with `recording_tick(tick: Tick, idle: IdleShutdown | None = None)` at `tests/entry/test_run.py:287`. `_ProjectImageStart._choose` now calls `activity_tick(tick, inputs.idle, fetched=True)`, so every iteration fails. From `make check` (`--tb=short`):
    - `iteration failed: TypeError: test_run_instance_hands_the_idle_shutdown_of_its_settings_to_the_activity_tick.<locals>.recording_tick() got an unexpected keyword argument 'fetched'`
    - `E   assert [] == [None]` (and, for the other row, `E   assert [] == [<factory.app...IdleShutdown object ...>]`)

    Options:
    - A (my choice): the tester changes only `recording_tick` at `tests/entry/test_run.py:287` to `def recording_tick(tick: Tick, idle: IdleShutdown | None = None, *, fetched: bool = False) -> Callable[[], bool]:` and makes it return `original_tick(tick, idle, fetched=fetched)`. The test still checks the same thing, which is the idle shutdown handed to the activity tick. The next coder round then ends with `tests`, naming this change.
    - B: leave `activity_tick(tick, idle)` without the flag. `_ProjectImageStart` would hand it a delegating `Tick` subclass whose `run()` calls the real tick's `run(fetched=True)`. No test changes, but it is a hollow subclass that skips `Tick.__init__` only to get around one test double. I reject it.
    - C: put the flag on the `Tick` instance (a setter, or a constructor argument) instead of passing it to `run`. This contradicts the Interface's `Tick.run(fetched: bool = False)` and the new tests that call `tick.run(fetched=False)`.

    The current code:
    - `src/factory/application/tick.py`: `run(self, *, fetched: bool = False)` skips `_fetch()` when `fetched` is true.
    - `src/factory/entry/run.py`: `activity_tick(tick, idle=None, *, fetched=False)` passes the flag on, and `_ProjectImageStart._choose` builds its tick with `fetched=True`, because `_follow_main` fetches and raises or clears `fetch_failed` before every tick.

    In this run I also fixed `tests/application/test_tick_docstrings.py::test_the_docstrings_say_what_the_code_does[tick-run]`. It pins the docstring of `Tick.run`, and the earlier run had added a paragraph to it. I put the docstring back as it was on `main` and moved the reason into a one-line comment above the skipped fetch. That test passes now.

    Status of `make check`: red only on the two rows above. Lint, types and the other tests passed, and coverage is 99.42 %. I did not do the refactor step, because the stage stops here. The diff otherwise reads clean.

    Noticed, not touched: the copy of `Outage` (`Instance.go_away`/`come_back` in `tests/entry/test_run_one_fetch.py`). Moving it to a shared place is the tester's job, under the standing leave.
18. 2026-11-04 human: Answer of the human: **A** "the tester changes only `recording_tick` at `tests/entry/test_run.py:287` to `def recording_tick(tick: Tick, idle: IdleShutdown | None = None, *, fetched: bool = False) -> Callable[[], bool]:` and makes it return `original_tick(tick, idle, fetched=fetched)`."

    Leave for the tester: only that function in `tests/entry/test_run.py`; nothing else in that module. If the tester finds any further test double that only needs the same signature for `fetched`, the same leave covers it (the signature and the passing on of `fetched`, nothing else), and its entry names each one, so that no further question is needed for this kind.
19. factory: started doing as vm.
20. coder: Test change, following the human's answer A in entry 18. In `tests/entry/test_run.py:287`, change only the function `recording_tick` to `def recording_tick(tick: Tick, idle: IdleShutdown | None = None, *, fetched: bool = False) -> Callable[[], bool]:` and make it return `original_tick(tick, idle, fetched=fetched)`. Nothing else in that module changes. The human's leave also covers any other test double that needs only this signature and the passing on of `fetched`. The tester's entry names each one it changes.

    I changed no code in this run. The code from the earlier doing runs is still on the branch:
    - `src/factory/application/tick.py`: `run(self, *, fetched: bool = False)` skips the fetch when the caller has already fetched.
    - `src/factory/entry/run.py`: `activity_tick(..., *, fetched=False)` passes the flag on, and `_ProjectImageStart._choose` builds its tick with `fetched=True`.

    I did not run `make check` in this run. In entry 17 it was red only on the two rows of `test_run_instance_hands_the_idle_shutdown_of_its_settings_to_the_activity_tick`, and this change fixes them. When the work item comes back, I run `make check` and do the refactor step.

    Noticed, not touched: `Instance.go_away`/`come_back` in `tests/entry/test_run_one_fetch.py` copy `Outage` in `tests/entry/test_run_fetch_before_tick.py`. The tester may move that copy to a shared place under the standing leave.
21. factory: started tests as vm.
22. tester: Approved test change: the human's answer A in entry 18, named by the coder in entry 20. In `tests/entry/test_run.py`, inside `test_run_instance_hands_the_idle_shutdown_of_its_settings_to_the_activity_tick`, I changed only the nested function `recording_tick`. Its signature is now `def recording_tick(tick: Tick, idle: IdleShutdown | None = None, *, fetched: bool = False) -> Callable[[], bool]:`, split over three lines so that `ruff format` accepts it, and it returns `original_tick(tick, idle, fetched=fetched)`. Nothing else in that module changed. The test still checks the same thing: the idle shutdown that is handed to the activity tick.

    No other test double needed the same change. The only other callers of `activity_tick` in the tests (`tests/entry/test_run.py:207` and `tests/entry/test_run_idle_shutdown.py:39`) call the real function. They do not replace it, so the leave in entry 18 was not used anywhere else.

    Criterion → test mapping, unchanged from entry 8:
    - criterion 1: tests/entry/test_run_one_fetch.py::test_an_iteration_fetches_once_and_its_tick_sees_what_that_fetch_brought
    - criterion 2: tests/entry/test_run_one_fetch.py::test_a_failed_fetch_in_an_iteration_stands_as_fetch_failed_and_the_next_passed_one_clears_it
    - criterion 3: tests/application/test_tick_own_fetch.py::test_a_tick_run_without_the_fetch_before_it_fetches_once
    - criterion 4: tests/application/test_tick_own_fetch.py::test_a_tick_run_alone_whose_fetch_fails_stops_and_the_next_passed_one_clears_it

    Files created: none. Earlier test file changed: tests/entry/test_run.py, under the human's leave in entry 18. Every module imported.

    The one run was `uv run pytest -q tests/entry/test_run.py`: all 31 tests passed. `make lint`: lint: green (0.2 s). I skipped the type check, as this stage says.

    Still open: the optional move of the `Outage` copy (`Instance.go_away`/`come_back` in tests/entry/test_run_one_fetch.py) to a shared place. I did not make it, because this run is limited to the approved change.

    `lint`: lint: green (0.2 s)
23. factory: started doing as vm.
24. coder: `make check` is green: `check: green`, coverage 99.42 %. This run follows the tester's approved change in entry 22. The code is unchanged from the earlier doing runs, and the refactor step found nothing to change.

    What I built:
    - `src/factory/application/tick.py`: `Tick.run(self, *, fetched: bool = False)`. With `fetched=True` the tick skips `_fetch()`, and with it the raise and clear of `fetch_failed`. The disk check still runs first. The docstring is the same as on `main`, which `test_tick_docstrings` pins. The reason for the skip is a one-line comment instead.
    - `src/factory/entry/run.py`: `activity_tick(tick, idle=None, *, fetched=False)` passes the flag on to `tick.run`. `_ProjectImageStart._choose` builds its tick with `fetched=True`, because `_follow_main` fetches before every tick and raises or clears `fetch_failed` itself. `factory-watch` and every other caller keep the default, so they still fetch in the tick. `scheduler.py:126` is untouched.

    Main decision: the flag goes to `run`, as the Interface says, and is passed through `activity_tick`. I rejected two other ways:
    - a delegating `Tick` subclass, which needs no test change but skips `Tick.__init__` just to get around a test double;
    - a flag stored on the `Tick` instance, which contradicts the Interface and the new tests that call `tick.run(fetched=False)`.

    Refactor: I read my diff (`git diff main` outside `factory/` and `tests/`). Nothing needed renaming, simplifying or removing.

    Description: no rewrite. The journal (entries 4, 11 and 18) only made the seam concrete and gave leave for the test signatures. The intake had already carried that into the Interface and criteria.

    Smoke test: there are still three `git.fetch()` calls in `src/factory/application` and `src/factory/entry`, the same count as before the story.

    Noticed, not touched: `Instance.go_away`/`come_back` in `tests/entry/test_run_one_fetch.py` copy `Outage` in `tests/entry/test_run_fetch_before_tick.py`. Moving them to a shared place is the tester's job, under the standing leave.

    `check`: check: green
    `duplicates`: duplicates: 3 new, 43 known, 0 gone
