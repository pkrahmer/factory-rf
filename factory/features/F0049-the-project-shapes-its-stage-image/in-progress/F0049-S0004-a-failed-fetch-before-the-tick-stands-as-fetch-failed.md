---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 530
comments_read: [6620835040]
handed_over: null
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
