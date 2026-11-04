---
stage: done
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 530
comments_read: [6620835040, 6620926891]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T02:20:55.654969Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T02:20:55.662567Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-04T02:21:16.192136Z'
  stage: intake
  run: 44b2b4f9637e49c9a20ba737b532d0ba
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-04T02:25:11.270142Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-04T02:25:14.577147Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-04T02:25:30.368432Z'
  stage: intake
  run: 6df60ff5a5044772b884f55244368e78
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-04T02:25:36.571414Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-04T02:27:42.440865Z'
  stage: tests
  run: 29a2b1fd8be34755a0553bf3f4f2728f
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-04T02:27:48.430427Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-04T02:29:03.464361Z'
  stage: doing
  run: b0a619cac77340dbbcc6d6d2b6cc39de
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-04T02:30:55.602914Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-04T02:30:58.884734Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-04T02:31:15.735515Z'
  stage: doing
  run: bc5887637fcb4ce59eeba777ec20e929
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-04T02:31:21.918597Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-04T02:31:54.897462Z'
  stage: tests
  run: 0da224ae776945bba6dafe3fd990868c
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-04T02:32:01.360795Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-04T02:36:54.998733Z'
  stage: doing
  run: c903f6412b20444eb351d61aeadff925
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-04T02:37:01.299874Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-04T02:38:05.355313Z'
  stage: review
  run: 7a0a9e9a22df442fac01849d811b82c5
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-04T02:38:11.136539Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-11-04T02:38:33.090391Z'
  stage: doing
  run: 729d9dda4f29406293908d03313003ce
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-04T02:38:39.065484Z'
  stage: tests
- number: 23
  speaker: tester
  kind: result
  at: '2026-11-04T02:40:00.411664Z'
  stage: tests
  run: 060cb4aa569b4380add99ac21f06a476
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-04T02:40:06.953540Z'
  stage: doing
- number: 25
  speaker: coder
  kind: result
  at: '2026-11-04T02:43:36.892614Z'
  stage: doing
  run: 12a376bfed34462586021e358cb9fc80
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-04T02:43:42.838465Z'
  stage: review
- number: 27
  speaker: reviewer
  kind: result
  at: '2026-11-04T02:44:32.857738Z'
  stage: review
  run: 9a8e0fe08d8640be93f82369b4f9e9a5
- number: 28
  speaker: factory
  kind: started
  at: '2026-11-04T02:44:39.043389Z'
  stage: docs
- number: 29
  speaker: documenter
  kind: result
  at: '2026-11-04T02:45:15.216097Z'
  stage: docs
  run: fb3990b63928476da90d0b69e6994eae
- number: 30
  speaker: factory
  kind: started
  at: '2026-11-04T02:45:21.520662Z'
  stage: smoke-test
- number: 31
  speaker: smoke-tester
  kind: result
  at: '2026-11-04T02:45:58.687119Z'
  stage: smoke-test
  run: dade819c34a94968ba79127ff2c3b8fd
- number: 32
  speaker: factory
  kind: done
  at: '2026-11-04T02:46:51.301321Z'
  stage: approval
---

# A fetch that fails before the tick stands as the stop fetch_failed

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

Since F0049-S0003 the factory fetches before every tick, in `_ProjectImageStart.prepare`, to compare the stage file on `origin/main` with the one in use. That fetch is not guarded: when it fails (the network is down, the token expired or was revoked, the address is wrong), `FetchFailed` escapes to the scheduler's catch-all, which logs a multi-line `iteration failed: FetchFailed: ...` and runs no tick. The tick's own fetch, which raises the stop `fetch_failed`, is never reached. So `factory-health` reports `healthy` while the factory does nothing, no stop record is written, and the operator guide's promise that "an expired or revoked token shows as `fetch_failed`" no longer holds (the feature acceptance F0049-A0001 reproduced it: three failed iterations, `factory-health` exit 0 `healthy`, no `fetch_failed` line). The human accepted the `iteration failed` behaviour "for now" in F0049-S0003 entry 11; this story ends it. A fetch that fails before the tick raises the stop `fetch_failed` exactly as the tick's fetch does (scope `repository`, the error's text as its detail), runs no tick in that iteration and changes neither the image, its identity, its `PATH` nor the stage file last handled. The next fetch that passes clears the stop, and the comparison of the stage file goes on as before. How the tick itself fetches does not change; whether the second fetch per iteration (prepare's and the tick's) should become one is left to a later story.

## Interface

- `factory.entry.run._ProjectImageStart` (entry):
  ```python
  def _follow_main(self) -> bool: ...
  ```
  - It returns `False` when `git.fetch()` raises `FetchFailed` (`factory.domain.errors`), after `StopService(boundaries).raise_stop(RepositoryStop(scope="repository", reason="fetch_failed", detail=str(error), at=boundaries.clock.now()))`; it reads no stage file then, and the tick, the stage file last handled and the image in use stay as they were.
  - After a fetch that passes it calls `clear_stop("fetch_failed")` and returns `True`, then compares the stage file as today.
  - `prepare` returns `False` when `_follow_main` does, so no tick runs in that iteration and the scheduler logs no `iteration failed` for it.
- Any other `GitError` from the fetch is not caught here and keeps today's path.
- The tester writes `tests/entry/test_run_fetch_before_tick.py`, driving `run_instance` over a real bare remote that becomes unreachable after the start (renamed away), with `FakeHostingService` and `FakeImages`, the way `tests/entry/test_run_project_image_rebuild.py` drives it.

## Acceptance criteria

1. After a start whose first tick ran, a fetch before the next tick that fails leaves the stop `fetch_failed` with scope `repository` and the fetch's error text as its detail in the health status; the factory log holds a `stop repository fetch_failed:` line and no `iteration failed` line, and no tick runs in that iteration. Row: a fetch that passes leaves no `fetch_failed` stop and the tick runs.
2. While the fetch fails, the image, the identity and the `PATH` stay those in use before the outage, and no build is asked for; rows: a project without a stage file (the base image and its identity) and one with a stage file (the project image and the layer's identity).
3. The first fetch that passes after the outage clears `fetch_failed`, and the tick of that iteration runs; when `main` changed the stage file during the outage, that file is built once before that tick and the tick takes the new image, identity and `PATH`.
4. A fetch before the tick that raises a `GitError` other than `FetchFailed` is not turned into the stop `fetch_failed`: no `fetch_failed` stop is raised, and the scheduler logs `iteration failed` for it, as before.
5. `make check` stays green.
6. docs: `docs/operator-guide.md`: in "The stops of the tick" and in the stops table's `fetch-failed` row, that the fetch before every tick (the one that compares the stage file) raises the same stop. `docs/project-guide/stage-environment.md`: in *The project's stage image*, that `_ProjectImageStart.prepare` raises `fetch_failed` on a failed fetch and runs no tick. `docs/decisions.md`: one entry: a failed fetch before the tick stands as `fetch_failed`, because the operator and the container's health check read `factory-health`, and an `iteration failed` line alone left it `healthy` while nothing ran; it replaces what F0049-S0003 entry 11 accepted for now. `README.md`: none, it names no stop.

## Smoke test

```bash
uv run pytest tests/entry/test_run_fetch_before_tick.py 2>&1 | tail -1
```

Expect: a line that ends in `passed` with no `failed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: Format check: passed. One finding from the checks it does not cover:

   1. The Interface states a rule, "Any other `GitError` from the fetch is not caught here and keeps today's path". No criterion covers it, so it has no failing side. Two coders could read it two ways, for example catching `GitError` broadly, and both would pass the listed tests. Do you want to add a criterion? I would add: "A fetch that raises a `GitError` other than `FetchFailed` is not turned into the stop `fetch_failed`: no `fetch_failed` stop is raised, and the scheduler logs `iteration failed` for it, as before." The alternative is to drop the Interface line and leave that path unspecified. I would choose the added criterion, before the two closing ones.

   Everything else I checked is fine:
   - Interface: `_ProjectImageStart._follow_main` has a concrete module and signature, and the stop's fields are named.
   - Criteria: the stop with its detail and the log lines are covered, and so are the no-tick and no-`iteration failed` outcomes. The pass row, the unchanged image, identity and `PATH` (two rows), and the clear on the next passing fetch with the stage file built once are covered.
   - Smoke test: `pyproject.toml` already sets `-q` in `addopts`, and the command passes none. The summary line therefore ends in `passed`, so the Expect line can be checked.
   - Architecture: the change sits in `factory.entry`, which wires the stop service, and calls `StopService` and `clear_stop`, so no layer is crossed.
   - Scope: it follows S0003's accepted-for-now behaviour and stays inside F0049's rebuild scope, and nothing in the feature's Out of scope is touched.
4. 2026-11-04 human: Yes, add that criterion before the two closing ones, as you propose.
5. factory: started intake as vm.
6. intake: accepted. Carried in from journal entry 4 (the human's yes to entry 3's question): I added the criterion for the `GitError` rule as new criterion 4, before the two closing ones. It reads: a `GitError` other than `FetchFailed` is not turned into `fetch_failed`, no such stop is raised, and the scheduler logs `iteration failed`, as before. The closing two are now 5 (`make check`) and 6 (`docs:`). I changed nothing else, and the Description keeps its meaning.
   - Interface: `factory.entry.run._ProjectImageStart._follow_main(self) -> bool` is concrete. The stop's fields are named (`RepositoryStop`, scope `repository`, reason `fetch_failed`, detail `str(error)`), and so are `clear_stop("fetch_failed")` and the `prepare` return. The `GitError` rule now has criterion 4.
   - Criteria: each is testable by one parametrized test. 1 covers the stop, its detail, the log lines, no `iteration failed`, no tick, and the pass row. 2 covers image, identity and `PATH` unchanged in two rows (no stage file, stage file). 3 covers the clear on the next passing fetch, the tick running, and the build of a changed stage file once. 4 is the failing side of the `GitError` rule. 5 and 6 close.
   - Smoke test: the command runs pytest with no `-q`, and `addopts` already sets `-q`. So the last line ends in `passed`, and the Expect line can be checked.
   - Architecture: the change stays in `factory.entry`, which wires the stop service, and calls `StopService` and `clear_stop` from the layers below. No layer is crossed, and no new dependency.
   - Scope: it ends the "accepted for now" behaviour of F0049-S0003 inside F0049's rebuild scope. Nothing in the feature's Out of scope is touched. No existing test is changed.
7. factory: started tests as vm.
8. tester: I wrote the tests for criteria 1 to 4 in one new file, `tests/entry/test_run_fetch_before_tick.py`. It drives `run_instance` the way `tests/entry/test_run_project_image_rebuild.py` does: a real bare remote, `FakeHostingService`, a `FakeImages` subclass whose project `PATH` names how many builds were asked for, and a recording tick. Between iterations it renames the remote away and back.

   - criterion 1: tests/entry/test_run_fetch_before_tick.py::test_a_failed_fetch_before_the_tick_stands_as_fetch_failed_and_runs_no_tick (rows `fails`, `passes`)
   - criterion 2: tests/entry/test_run_fetch_before_tick.py::test_while_the_fetch_fails_the_image_in_use_stays_and_nothing_is_built (rows `no-stage-file`, `stage-file`)
   - criterion 3: tests/entry/test_run_fetch_before_tick.py::test_the_first_fetch_that_passes_after_the_outage_clears_fetch_failed_and_ticks (rows `main-unchanged`, `stage-file-changed`)
   - criterion 4: tests/entry/test_run_fetch_before_tick.py::test_a_fetch_that_fails_with_another_git_error_is_no_fetch_failed_stop

   How the tests check some points:
   - **Criterion 1, the detail:** the exact text depends on git's output, so the test checks that it starts with `git fetch` and contains ` failed (exit `. It also checks that a log line ends in `stop repository fetch_failed: <detail>`.
   - **Criterion 3, the push during the outage:** the test brings the remote back, pushes the new stage file, and renames the remote away again before the next iteration.
   - **Criterion 4, the other `GitError`:** `GitCli.fetch` only ever raises `FetchFailed`, so the test uses a `GitCli` subclass, `BreakableFetch`, whose `fetch` raises a plain `GitError` once it is switched on. It is put in place by wrapping `run_module.build_boundaries` with monkeypatch and swapping the boundaries' `git`. `tests/application/test_tick_stop_details.py` does the same with its `FailingFetch(GitCli)`.

   Test run: `uv run pytest -q tests/entry/test_run_fetch_before_tick.py`. Three cases fail for the right reason: both rows of criterion 3 and the `fails` row of criterion 1. Today `prepare`'s `FetchFailed` escapes to the scheduler, so no stop is raised and no `stop cleared` line is written. Criteria 2 and 4 already pass, because they describe what happens today: while the fetch fails no tick runs and nothing is built, and a non-`FetchFailed` error still goes to `iteration failed`. They guard against a fix that breaks those points.

   Every module the tests use imports; none was missing. `make lint` is green. I changed no earlier test file.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: I stopped at one test that I think cannot pass as written. The code is in the working tree, in `src/factory/entry/run.py`, but `make check` is not green yet.

    What I built: `_ProjectImageStart._follow_main` now returns `bool`. When `git.fetch()` raises `FetchFailed`, it raises `RepositoryStop(scope="repository", reason="fetch_failed", detail=str(error), at=clock.now())` through `StopService` and returns `False`. After a fetch that passes, it calls `clear_stop("fetch_failed")` and compares the stage file as before. `prepare` returns `False` when `_follow_main` does. Any other `GitError` is not caught. In `tests/entry/` (and `tests/application/test_tick.py`), everything passes except the `fails` row of criterion 1.

    The contradiction is in `tests/entry/test_run_fetch_before_tick.py::test_a_failed_fetch_before_the_tick_stands_as_fetch_failed_and_runs_no_tick[fails]`:

    ```
    tests/entry/test_run_fetch_before_tick.py:217: in test_a_failed_fetch_before_the_tick_stands_as_fetch_failed_and_runs_no_tick
        assert any(line.endswith(STOP_LINE + stop.detail) for line in run.lines)
    E   assert False
    ```

    - The Interface sets `detail=str(error)`. For a `FetchFailed`, that is git's stderr, which runs over several lines (`... does not appear to be a git repository\nfatal: Could not read from remote repository.\n\nPlease make sure ...`).
    - The factory log writes each line of a message as its own timestamped line, and `state_log_lines` splits the file by line. So no single log line can end in the whole detail.
    - The log does hold `2026-11-04T02:28:30Z stop repository fetch_failed: git fetch --prune origin failed (exit 128): fatal: '...' does not appear to be a git repository`, followed by the rest of the detail on further lines.
    - The tick's own `fetch_failed` writes the same multi-line detail the same way, so this is not specific to the new code.

    Options:
    (a) The tester changes that one assertion to check the detail's first line: `any(line.endswith(STOP_LINE + stop.detail.splitlines()[0]) for line in run.lines)`.
    (b) The code folds the detail into one line before raising the stop. That goes against the Interface's `detail=str(error)`, and the stop would read differently from the tick's own `fetch_failed`.

    I would choose (a). With your yes, I end with `tests` and the tester makes that one change.

    Rejected design: catching the error in `prepare` instead of in `_follow_main`. The Interface puts it in `_follow_main`, and keeping it there keeps the fetch and its stop together.

    The Description stays as it is: no journal entry changed the task.
11. 2026-11-04 human: (a): the tester checks the detail's first line, as you propose. The code keeps detail=str(error), the same as the tick's own fetch_failed.
12. factory: started doing as vm.
13. coder: In entry 11 the human chose option (a), which is a change to a test, so this round hands the work item to the tester. The change: in `tests/entry/test_run_fetch_before_tick.py::test_a_failed_fetch_before_the_tick_stands_as_fetch_failed_and_runs_no_tick`, the assertion `any(line.endswith(STOP_LINE + stop.detail) for line in run.lines)` becomes `any(line.endswith(STOP_LINE + stop.detail.splitlines()[0]) for line in run.lines)`. The reason is that git's error text runs over several lines, and the factory log writes each of them as its own line.

    The code is unchanged from entry 10 and stays as it is. In `src/factory/entry/run.py`, `_ProjectImageStart._follow_main` now returns a bool. When the fetch raises `FetchFailed`, it raises the stop `RepositoryStop(scope="repository", reason="fetch_failed", detail=str(error), at=clock.now())` and returns `False`. After a fetch that passes, it calls `clear_stop("fetch_failed")` and returns `True`. `prepare` returns `False` when `_follow_main` does. Any other `GitError` is not caught. I did not run `make check` this round, because it cannot be green until the tester changes that one assertion.

    Main choice: I catch the error in `_follow_main`, as the Interface says, so the fetch and its stop stay together. I rejected catching it in `prepare`.

    Noticed and not touched: the `fetch_failed` stop that the tick raises from its own fetch writes the same multi-line text to the log in the same way. No journal entry changed the meaning of the task, so the Description stays as it is.
14. factory: started tests as vm.
15. tester: I made the one test change that the human approved in entry 11 and that the coder named in entry 13.

    **The change:** in `tests/entry/test_run_fetch_before_tick.py::test_a_failed_fetch_before_the_tick_stands_as_fetch_failed_and_runs_no_tick`, line 217 now reads `any(line.endswith(STOP_LINE + stop.detail.splitlines()[0]) for line in run.lines)`. It used to check `stop.detail` whole.

    **Why:** git's error text runs over several lines, and the factory log writes each one as its own timestamped line. So no single log line can end with the whole detail. The stop still carries the whole text as `detail=str(error)`, and the test's other assertions on the detail stay as they were.

    **Test run:** `uv run pytest -q tests/entry/test_run_fetch_before_tick.py`: all 7 cases pass with the coder's code in the working tree. `make lint` is green.

    Criteria and their tests, unchanged:
    - criterion 1: tests/entry/test_run_fetch_before_tick.py::test_a_failed_fetch_before_the_tick_stands_as_fetch_failed_and_runs_no_tick (rows `fails`, `passes`)
    - criterion 2: tests/entry/test_run_fetch_before_tick.py::test_while_the_fetch_fails_the_image_in_use_stays_and_nothing_is_built (rows `no-stage-file`, `stage-file`)
    - criterion 3: tests/entry/test_run_fetch_before_tick.py::test_the_first_fetch_that_passes_after_the_outage_clears_fetch_failed_and_ticks (rows `main-unchanged`, `stage-file-changed`)
    - criterion 4: tests/entry/test_run_fetch_before_tick.py::test_a_fetch_that_fails_with_another_git_error_is_no_fetch_failed_stop

    I created no files. The only file I changed is `tests/entry/test_run_fetch_before_tick.py`, which this story's tests stage wrote. Every module the tests use imports.

    `lint`: lint: green (0.1 s)
16. factory: started doing as vm.
17. coder: The tester has changed the assertion, so the code from entry 10 now passes every test. `make check` is green: all seven cases in `tests/entry/test_run_fetch_before_tick.py` pass, and the whole suite passes with 99.51 % coverage.

    What I built, in `src/factory/entry/run.py`:
    - `_ProjectImageStart._follow_main` now returns a `bool`.
    - When `git.fetch()` raises `FetchFailed`, it raises the stop through `StopService`: `RepositoryStop(scope="repository", reason="fetch_failed", detail=str(error), at=clock.now())`. Then it returns `False`. It reads no stage file and changes neither the image, its identity, its `PATH` nor the stage file last handled.
    - After a fetch that passes, it calls `clear_stop("fetch_failed")` and compares the stage file as before, then returns `True`.
    - `prepare` returns `False` when `_follow_main` does, so no tick runs in that iteration and the scheduler logs no `iteration failed` for it.
    - Any other `GitError` is not caught and still reaches the scheduler's `iteration failed`.

    Main choice: I catch the error in `_follow_main`, where the Interface puts it, so the fetch and its stop stay together. I rejected catching it in `prepare`.

    Refactor: I read the diff again and found nothing to change.

    Description: entry 11 changed only how the test checks the detail, not what the task means, so the Description stays as it is.

    Noticed and not touched:
    - The tick raises the same `fetch_failed` from its own fetch, and its detail is also git's multi-line stderr, written to the log one line at a time.
    - Each iteration still fetches twice (once in prepare, once in the tick). The Description leaves merging them to a later story.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 43 known, 0 gone
18. factory: started review as vm.
19. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (`src/factory/entry/run.py`, `tests/entry/test_run_fetch_before_tick.py`) against the work item.

    The code holds. `_follow_main` catches only `FetchFailed`. It raises `RepositoryStop(scope="repository", reason="fetch_failed", detail=str(error), at=clock.now())` through `StopService`, then returns `False` before it reads the stage file. After a fetch that passes it calls `clear_stop("fetch_failed")`. `prepare` returns `False` when `_follow_main` does. Any other `GitError` still reaches the scheduler. This matches the Interface and mirrors `Tick._fetch` (`src/factory/application/tick.py:139`).

    Criteria 1 to 4 each have a parametrized test that checks what the criterion says. The Interface states no numeric limit. The coder's `make check` was green (entry 17). Architecture and security are clean: the change stays in `factory.entry`, imports only from lower layers, and adds no marker that silences a check. The journal names the main choice (catch in `_follow_main`, not in `prepare`) and what was rejected. The Description and the docs criterion match what was built.

    Findings:

    1. `tests/entry/test_run_fetch_before_tick.py:29-57,158-169`: the file holds second copies of helpers that `tests/entry/test_run_project_image_rebuild.py` already has:
       - the `StageSeen` dataclass (rebuild file line 35), the same fields;
       - `built_path` (line 69), the same body;
       - the fixtures `settings` and `base` (lines 109-118), the same code;
       - the constants `BASE_IDENTITY`, `FIRST` and `SECOND` (lines 26-28).

       Fix: under the standing leave to move a shared test helper, the tester moves `StageSeen`, `built_path` and the three constants to one support module under `tests/` (for example `tests/stage_image_support.py`). It moves the two fixtures to `tests/conftest.py` under names that clash with no other `settings` fixture. Both test modules then use them from there, and every earlier test keeps its name and what it checks.

    Earlier tests: none. The diff only adds `tests/entry/test_run_fetch_before_tick.py` (status `A`) and changes no test file that `main` holds.
20. factory: started doing as vm.
21. coder: Round 1 addresses the reviewer's one finding (entry 19). It is a change to tests, so I changed no code and am handing the work item to the tester. `CLAUDE.md`'s standing leave to move a shared test helper covers this move.

    The move: `tests/entry/test_run_fetch_before_tick.py` holds copies of helpers that `tests/entry/test_run_project_image_rebuild.py` already has. The tester moves them to one shared place:
    - The `StageSeen` dataclass, `built_path` and the constants `BASE_IDENTITY`, `FIRST` and `SECOND` go to a support module under `tests/`, for example `tests/stage_image_support.py`.
    - The fixtures `settings` and `base` go to `tests/conftest.py`, under names that clash with no other `settings` fixture.
    - Both test modules then use them from there. Every earlier test keeps its name and checks the same thing.
    - The tester's entry names `tests/entry/test_run_project_image_rebuild.py` as the earlier test file it changed.

    Code: no change since entry 17. `_ProjectImageStart._follow_main` and `prepare` in `src/factory/entry/run.py` stay as the reviewer found them. I did not run `make check` this round because I edited nothing.

    Main choice: I end with `tests` rather than moving the helpers myself, because the coder never edits tests and the standing leave gives the move to the tester.

    Description: entry 19 changes no meaning of the task, so the Description stays as it is.

    Noticed and not touched: as entry 17 said, the tick's own `fetch_failed` also writes git's multi-line error text to the log one line at a time, and each iteration still fetches twice.
22. factory: started tests as vm.
23. tester: I moved the shared test helpers that the reviewer named in entry 19 and the coder passed on in entry 21. `CLAUDE.md`'s standing leave to move a shared test helper covers this move. No test was renamed, and every test checks the same thing as before.

    **The move:**
    - New support module `tests/stage_image_support.py`. It now holds `BASE_IDENTITY`, `FIRST`, `SECOND`, the `StageSeen` dataclass and `built_path`. The two copies had the same fields and the same body; only their docstrings differed, and the support module has one neutral docstring for each.
    - `tests/conftest.py`: the two module-level fixtures `settings` and `base` are now `base_identity_settings` and `base_image`. No other fixture under `tests/` has either name. `tests/conftest.py` imports `BASE_IDENTITY` from the support module.
    - `tests/entry/test_run_project_image_rebuild.py` (an earlier story's test file, changed under the standing leave): I removed its copies of the constants, `StageSeen`, `built_path` and the two fixtures, and it imports them from the shared places. The `world` fixture takes `base_identity_settings`. Its tests take `base_image` where they used to take `base`. `THIRD`, `PASSED`, `FAILED`, `MARK` and `ScriptedImages` belong to this file alone and stay there.
    - `tests/entry/test_run_fetch_before_tick.py` (this story's file): I made the same change, and the `outage` fixture takes `base_identity_settings`. `STOP_LINE` and `CountingImages` belong to this file alone and stay there.

    **Criteria and their tests (names unchanged):**
    - criterion 1: tests/entry/test_run_fetch_before_tick.py::test_a_failed_fetch_before_the_tick_stands_as_fetch_failed_and_runs_no_tick (rows `fails`, `passes`)
    - criterion 2: tests/entry/test_run_fetch_before_tick.py::test_while_the_fetch_fails_the_image_in_use_stays_and_nothing_is_built (rows `no-stage-file`, `stage-file`)
    - criterion 3: tests/entry/test_run_fetch_before_tick.py::test_the_first_fetch_that_passes_after_the_outage_clears_fetch_failed_and_ticks (rows `main-unchanged`, `stage-file-changed`)
    - criterion 4: tests/entry/test_run_fetch_before_tick.py::test_a_fetch_that_fails_with_another_git_error_is_no_fetch_failed_stop

    **Files:** created `tests/stage_image_support.py`. Changed `tests/conftest.py`, `tests/entry/test_run_project_image_rebuild.py` (earlier test file) and `tests/entry/test_run_fetch_before_tick.py`.

    **Test run:** `uv run pytest -q tests/entry/test_run_fetch_before_tick.py tests/entry/test_run_project_image_rebuild.py tests/test_shared_imports.py`: all 30 cases pass with the coder's code in the working tree. Every module imports. `make lint` is green.

    **Not checked:** I did not run the type check, as this stage says. I tried running mypy by hand on the four files, but outside the project's configuration it cannot resolve the `factory` imports, so that run says nothing either way. The coder's `make check` covers the types.

    `lint`: lint: green (0.1 s)

    `lint`: lint: green (0.2 s)
24. factory: started doing as vm.
25. coder: Round 1: the tester moved the shared test helpers that the reviewer named in entry 19 (entry 23). So this round I changed no code and ran `make check`, which is green: all tests pass with 99.51 % coverage, and the run ends with `check: green`.

    What I built is unchanged since entry 17. It is all in `src/factory/entry/run.py`:
    - `_ProjectImageStart._follow_main` now returns a `bool`.
    - When `git.fetch()` raises `FetchFailed`, it raises `RepositoryStop(scope="repository", reason="fetch_failed", detail=str(error), at=clock.now())` through `StopService` and returns `False`. It then reads no stage file and leaves the image, its identity, its `PATH` and the stage file last handled as they were.
    - After a fetch that passes, it calls `clear_stop("fetch_failed")` and compares the stage file as before.
    - `prepare` returns `False` when `_follow_main` does, so no tick runs in that iteration.
    - Any other `GitError` is not caught and still reaches the scheduler's `iteration failed`.

    Main choice: I catch the error in `_follow_main`, where the Interface puts it, so the fetch and its stop stay together. I rejected catching it in `prepare`.

    Refactor: I made no change this round. The test move touched only files under `tests/`, and the code diff is the one the reviewer read in entry 19.

    Description: entries 19 to 23 changed the test layout, not the meaning of the task, so the Description stays as it is.

    Noticed and not touched:
    - The tick's own `fetch_failed` also writes git's multi-line error text to the log one line at a time.
    - Each iteration still fetches twice, once in `prepare` and once in the tick. The Description leaves merging them to a later story.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 0 new, 43 known, 0 gone
26. factory: started review as vm.
27. reviewer: Round 1 review. I read `git diff main...HEAD -- . ':!factory'` against the work item: `src/factory/entry/run.py`, `tests/entry/test_run_fetch_before_tick.py`, `tests/stage_image_support.py`, `tests/conftest.py` and `tests/entry/test_run_project_image_rebuild.py`.

    The code is the same as in round 0. `_ProjectImageStart._follow_main` (`src/factory/entry/run.py:227`) catches only `FetchFailed`. It raises `RepositoryStop(scope="repository", reason="fetch_failed", detail=str(error), at=clock.now())` through `StopService` and returns `False` before it reads the stage file. After a fetch that passes it calls `clear_stop("fetch_failed")`, which does nothing when no such stop stands (`src/factory/application/stops.py:62`), so a healthy loop adds no log noise. `prepare` returns `False` when `_follow_main` does. Any other `GitError` still reaches the scheduler. This matches the Interface and mirrors `Tick._fetch` (`src/factory/application/tick.py:139`).

    Group 1, acceptance criteria:
    - Criteria 1 to 4 each have one parametrized test that checks what the criterion says.
    - Criterion 4 covers the failing side of the `GitError` rule.
    - The Interface's "reads no stage file then" is pinned by the unchanged build count and the unchanged `StageSeen` in criterion 2.
    - The Interface states no numeric limit.
    - The coder's `make check` was green (entry 25), with `duplicates: 0 new`.

    Group 2, architecture: the change stays in `factory.entry` and imports only from lower layers.

    Group 3, security: no marker silences a check, no command is built from a string, and the stop's detail is git's error text, the same as the tick's own stop.

    Group 4, quality: round 0's finding is resolved. `StageSeen`, `built_path`, `BASE_IDENTITY`, `FIRST` and `SECOND` now live once in `tests/stage_image_support.py`. The fixtures `base_identity_settings` and `base_image` live once in `tests/conftest.py`, and both test modules use them from there.

    Group 5, work item hygiene: the journal names the main choice (catch in `_follow_main`, not in `prepare`) and what was rejected. The Description matches what was built, and the docs criterion still says what the reader needs to know.

    no findings

    Earlier tests:
    - `tests/entry/test_run_project_image_rebuild.py`: changed under the standing leave to move a shared test helper. Its copies of the constants, `StageSeen`, `built_path`, `settings` and `base` moved to `tests/stage_image_support.py` and `tests/conftest.py`. Its tests take `base_identity_settings` and `base_image` instead. Every test keeps its name and checks the same thing.
    - `tests/conftest.py`: changed under the same standing leave. It only adds the two moved fixtures and the `BASE_IDENTITY` import. No existing fixture changed.

    Notes:
    1. `tests/entry/test_run_fetch_before_tick.py:156` (`_project`) builds the same project `StageSeen` as `_project` in `tests/entry/test_run_project_image_rebuild.py:309`, with a different signature. A later move could put one version in `tests/stage_image_support.py`.
28. factory: started docs as vm.
29. documenter: Documented that a failed fetch before the tick stands as `fetch_failed`. I changed only documents, so I did not run `make check`; the factory's checks decide. The code matches the Interface and the criteria (the reviewer found nothing in entry 27), so there are no findings.

    Files changed:
    - `docs/operator-guide.md`: in "The stops of the tick", the fetch before every tick (the stage file comparison) raises the same stop, with scope `repository`. That fetch runs no tick, leaves the image, identity and `PATH` as they were, and the next passing fetch clears the stop. Another git error is not this stop and gives `iteration failed`. In the stops table, the `fetch-failed` row now says the fetch before the tick raises it too.
    - `docs/project-guide/stage-environment.md`: in *The project's stage image*, `_ProjectImageStart.prepare` raises `fetch_failed` through `_follow_main` on `FetchFailed`, returns `False` and runs no tick. A fetch that passes calls `clear_stop`. Another `GitError` is not caught.
    - `docs/decisions.md`: one new entry, "A failed fetch before the tick stands as `fetch_failed`". It states the reason the docs criterion gives and says it replaces what F0049-S0003 entry 11 accepted for now. It has no "Rejected" line, because the story names no rejected option for this decision. The coder's rejected design (catching the error in `prepare`) is a choice inside the code, not a decision of the human, so I left it out.

    Cross-read and found current: `README.md` (names no stop, as the docs criterion says), `docs/project-guide/watching.md` (the tick's own fetch step, still true), `docs/operator-guide.md` ("The health status file" reasons list and "The wait for a repository that is not ready"; the latter says the wait does not fetch unless the repository looks unready, and that is unchanged).

    Stale text seen and not touched: none. I did not run the smoke test command, since I wrote no example.

    `check`: check: green (not run again: passed on tree da88284d442d at 2026-11-04T02:41:58Z)
    `secrets`: secrets: green (2.6 s)
    `documents`: documents ok
30. factory: started smoke-test as vm.
31. smoke-tester: Smoke test, round 1. I ran the one command under `## Smoke test` from the repository root, exactly as written, and fixed nothing.

    Command 1: `uv run pytest tests/entry/test_run_fetch_before_tick.py 2>&1 | tail -1`

    ```
    7 passed in 0.45s
    ```

    Met `Expect:` (a line that ends in `passed` with no `failed`).

    Against the acceptance criteria: the 7 passing cases are the rows of four parametrized tests in `tests/entry/test_run_fetch_before_tick.py`, one test per criterion from 1 to 4:
    - fetch fails / fetch passes (criterion 1)
    - no stage file / with a stage file (criterion 2)
    - `main` unchanged / stage file changed during the outage (criterion 3)
    - another `GitError` (criterion 4)

    The smoke test contradicts none of the criteria. It does not exercise criterion 5 (`make check`) or criterion 6 (`docs:`); the factory checks those itself.

    Findings: none.
32. factory: done (pull request merged); cost: 14 runs, 13.9 min, 108 turns, 328563 tokens in (2546380 more from cache), 42652 out, $3.66
