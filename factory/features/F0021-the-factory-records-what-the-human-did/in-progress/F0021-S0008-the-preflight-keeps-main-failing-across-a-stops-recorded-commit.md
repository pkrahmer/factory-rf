---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 243
comments_read: []
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-19T01:21:48.955295Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T01:03:27.835216Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T01:03:27.841706Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T01:03:43.258715Z'
  stage: intake
  run: 6b424916888c4fd19914b75b84f9e288
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T01:04:03.849629Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T01:06:51.375124Z'
  stage: tests
  run: efe185d0f7ce45588091db9c02369c14
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T01:07:11.762646Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T01:09:12.619941Z'
  stage: doing
  run: b1dd6c008bf34208822ef8d894a6eab0
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T01:09:33.117637Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T01:10:49.028949Z'
  stage: review
  run: 48340b1330eb463e9c6e45a9c88766f5
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T01:11:09.485931Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-19T01:11:24.050324Z'
  stage: doing
  run: a0f57d8bebda4eeb917b1997291e426c
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T01:11:44.171802Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-19T01:14:35.249729Z'
  stage: tests
  run: 87678f39cc634ffda0f6e20ceb773eb9
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-19T01:14:55.661810Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-19T01:18:03.045864Z'
  stage: doing
  run: 2eecade3647247ac9c39f29e8abb5dce
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-19T01:18:23.176071Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-10-19T01:19:06.505874Z'
  stage: review
  run: cbd75f0eecbb4478adae2b428899864a
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-19T01:19:27.191498Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-10-19T01:21:28.504290Z'
  stage: docs
  run: 1bf7504188b54a5888b4cea781a55e81
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-19T01:21:48.955295Z'
  stage: smoke-test
---

# The preflight keeps main failing across a stops recorded commit

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0021-S0003 publishes every stop event to `factory/stops.jsonl` on `main` as a `stops recorded` commit. The preflight's stale-stop rule clears `main_branch_failing` while the machine's items fail, as soon as `origin/main` is no longer the commit the stamp remembers as failing. So a `stops recorded` commit clears the stop, and writes a `cleared` record, although `main` is still as red as before. The probe raises it again only once the machine's items pass. The feature accepted this for now (its decision 1, the human's answer of 2026-10-18) and left to "a later story" making the rule ignore a commit that changes only `factory/stops.jsonl`. This story is that change, for the operator who reads the health status and for the reader of `factory/stops.jsonl`, who would otherwise see a `cleared` for a `main` nobody fixed. A stop stays when every path that differs between the remembered failing commit and the checkout is `factory/stops.jsonl`. Any other changed path still clears it as today, and so does a git error while comparing. What stays as it is: the probe of a new `main` once the machine's items pass (a `stops recorded` commit is still probed once), the stamp (not rewritten), and every other preflight rule. Skipping the probe for such a commit is left to a later story.

## Interface

`factory.domain.preflight` (`domain`):

```python
def changes_only_stop_records(paths: Sequence[ChangedPath]) -> bool:
    """Whether `paths` is not empty and every one of them is the stop records file."""
```

- True when `paths` holds at least one `ChangedPath` and every one has `path == STOP_RECORDS_FILE` (`factory.domain.paths`), whatever its `change` (`added`, `modified` or `deleted`). False for an empty list and for a list with any other path.

`factory.application.preflight.Preflight._clear_stale_failing_stop` (`application`):

- When the stamp's `main_failed` differs from the resolved `origin/main`, it calls `self._boundaries.git.changed_paths(stamp.main_failed)`. When `changes_only_stop_records` of the result is true, the stop `main_branch_failing` stays: `clear_stop` is not called, so no `cleared` record and no `stop cleared main_branch_failing` log line are written.
- When the result has any other path, or `changed_paths` raises `GitError` (for example, the remembered commit is not in the clone), the stop is cleared as today.
- Every other branch (no stamp, no `main_failed`, `resolve` raising `GitError`, `main` equal to `main_failed`) is unchanged.

Test modules (new): `tests/domain/test_preflight_stop_records_paths.py`, `tests/application/test_preflight_stops_commit.py`. The application tests reuse the `rig` and `red_main` fixtures of `tests/application/test_preflight_run.py` the way `tests/application/test_preflight_stale_main_stop.py` does. No earlier test changes.

## Acceptance criteria

1. `changes_only_stop_records`, rows of one parametrized test:
   - `[]` gives `False`;
   - `[factory/stops.jsonl modified]`, `[factory/stops.jsonl added]` and `[factory/stops.jsonl deleted]` give `True`;
   - `[factory/stops.jsonl modified, src/a.py modified]` gives `False`;
   - `[src/a.py modified]` gives `False`;
   - `[factory/stops.jsonl.bak added]` gives `False`;
   - `[factory/other.jsonl modified]` gives `False`.
2. `Preflight.run` with the machine's items failing and a `main_branch_failing` stop standing for the stamp's `main_failed`, after `origin/main` moved on by the rows below (rows of one parametrized test). Each row checks that `run` returns `preflight_failed`, whether the stop is still in the health status, and whether the factory log holds `stop cleared main_branch_failing`:
   - one commit that changes only `factory/stops.jsonl`: the stop stays and no line is logged;
   - two such commits: the stop stays and no line is logged;
   - one commit that changes `factory/stops.jsonl` and another file: the stop is cleared and the line logged;
   - one commit that changes another file only: the stop is cleared and the line logged.
3. With the stop records configured (`Boundaries.stop_records`), the first row of criterion 2 appends no `cleared` record, and the third row appends one `cleared` record for `main_branch_failing` (rows of one parametrized test).
4. `Preflight.run` with the machine's items failing, a `main_branch_failing` stop standing and a stamp whose `main_failed` is a commit the clone does not hold (`"a" * 40`): the stop is cleared and the line logged, as today.
5. `make check` stays green.
6. docs:
   - `docs/operator-guide.md`, the preflight's bullets: "A `stops recorded` commit is a new `main`" says that the stale-stop rule keeps `main_branch_failing` across a commit that changes only `factory/stops.jsonl`. It also says that the probe still runs once for such a commit when the machine's items pass again. "A failed machine clears a stale stop" names the exception.
   - `docs/project-guide.md`, the preflight section: `changes_only_stop_records` and its use in `_clear_stale_failing_stop`.
   - `docs/decisions.md`, "The stops reach main as raised and cleared records": the "Accepted effect" line says the effect was removed by this story, and why (a `cleared` record for a `main` nobody fixed misleads the viewer).

## Smoke test

```bash
uv run -q python -c '
from factory.domain.git import ChangedPath
from factory.domain.preflight import changes_only_stop_records

for paths in ([], ["factory/stops.jsonl"], ["factory/stops.jsonl", "src/a.py"]):
    print(changes_only_stop_records([ChangedPath(path=p, change="modified") for p in paths]))
'
```

Expect: three lines, `False`, `True`, `False`.

```bash
grep -c "the rule does not yet ignore a commit that changes only" docs/operator-guide.md
```

Expect: `0`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: `changes_only_stop_records(paths: Sequence[ChangedPath]) -> bool` in `factory.domain.preflight` and the change to `Preflight._clear_stale_failing_stop` are concrete. `ChangedPath` (`factory.domain.git`), `Git.changed_paths(since)`, `STOP_RECORDS_FILE` (`factory.domain.paths`) and the method itself exist. The domain function sits in the domain layer, the use of `git.changed_paths` in the application layer.
   Criteria: each is testable by one parametrized test. Criterion 1 covers every Interface clause: empty, each change kind, mixed paths, a similar name and another path. Criterion 2 covers the keep (one commit, two commits) and the clear (mixed, other file). Criterion 3 covers the `cleared` record on both sides. Criterion 4 covers the `GitError` side. The no-stamp, no-`main_failed`, `resolve` error and equal-main branches are stated unchanged, so they need no new criterion.
   Smoke test: both commands are runnable. The Python snippet prints three lines, and the `grep -c` prints a count. Each `Expect:` line can be checked against the output.
   Architecture: the layering follows CLAUDE.md. There is no new dependency, and the test modules mirror the package and reuse existing fixtures. Docs go to the three named files.
   Scope: the work is within feature decision 1, which left this change to a later story. The probe of a new `main`, the stamp and the other preflight rules stay as they are. The existing sentence in `docs/operator-guide.md` line 348 is what the docs criterion replaces.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 to 4. Each one is a parametrized test where the criterion lists rows.
   criterion 1: tests/domain/test_preflight_stop_records_paths.py::test_only_the_stop_records_file_is_a_change_of_stop_records_only (rows: empty, modified, added, deleted, mixed, other, similar-name, other-jsonl)
   criterion 2: tests/application/test_preflight_stops_commit.py::test_a_failed_machine_keeps_the_failing_stop_only_across_stop_records_commits (rows: one-stops-commit, two-stops-commits, stops-and-other-file, other-file-only)
   criterion 3: tests/application/test_preflight_stops_commit.py::test_a_kept_failing_stop_appends_no_cleared_record (rows: one-stops-commit gives 0 `cleared` records for main_branch_failing, stops-and-other-file gives 1)
   criterion 4: tests/application/test_preflight_stops_commit.py::test_a_failed_machine_clears_the_stop_when_the_remembered_commit_is_not_in_the_clone
   criteria 5 and 6: no test (`make check` and the docs).

   Files created: tests/domain/test_preflight_stop_records_paths.py, tests/application/test_preflight_stops_commit.py. No earlier test file changed. The application module reuses the `rig` and `red_main` fixtures of tests/application/test_preflight_run.py, as test_preflight_stale_main_stop.py does.

   How the tests move main: the human clone makes the commits, then the checkout fetches and goes to main at `origin/main` (`checkout` plus `reset_to`). That is where the tick's restore leaves the checkout before the preflight runs. It matters because `Git.changed_paths(since)` compares `since` with the work tree, not with `origin/main`. Without that step the probe leaves the checkout on the old failing commit, and the diff would come back empty. The stops file the tests commit holds valid `StopRecord` lines.

   Run of `make test`: the domain module could not be imported (`changes_only_stop_records` is missing from factory.domain.preflight). In the application module, these rows fail because the stop is still cleared: the one-stops-commit and two-stops-commits rows of the criterion 2 test, and the one-stops-commit row of the criterion 3 test. The clear rows and criterion 4 already pass. That is expected: they describe what the code does today. `make lint` is green.

   Open: nothing.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/domain/test_preflight_stop_records_paths.py - ImportError while i...
6. factory: started doing as self.
7. coder: I added the rule so the preflight keeps `main_branch_failing` standing across a commit that changes only the stop records file. `make check` is green: it ran after my last edit, and there was nothing to refactor after that.

   What I built:
   - `src/factory/domain/preflight.py`: a new function, `changes_only_stop_records(paths)`. It returns true when `paths` is not empty and every path in it is `STOP_RECORDS_FILE` (from `factory.domain.paths`), whatever kind of change it is.
   - `src/factory/application/preflight.py`: `_clear_stale_failing_stop` now clears the stop only when `main` differs from `stamp.main_failed` and the paths changed since `main_failed` are not the stop records file alone. A new private method, `_changes_only_stop_records(since)`, asks `git.changed_paths(since)` for those paths. If git raises `GitError`, the method returns false, so the stop is cleared as it is today.

   Main choice: I put the `GitError` handling in a small private method that returns false, and kept the `if` in `_clear_stale_failing_stop` as one condition. I rejected nesting the try/except inside `_clear_stale_failing_stop`, which already holds one try/except for `resolve`. A second one would have given it two error paths and an extra branch that both clear the stop. Inside the method, the comment explains why a commit the clone cannot compare counts as a fix: that way a stop never outlasts a `main` the clone cannot check.

   Noticed but did not touch:
   - `changed_paths` compares against the work tree, not `origin/main`, as the tester's entry says. The rule therefore relies on the tick's restore leaving the checkout on `origin/main` before the preflight runs. That is the behaviour today, and I did not change it.
   - The journal did not change what the task means, so I left the Description as it is.
   - The docs for this story belong to the documenter.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 36 known, 3 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (src/factory/domain/preflight.py, src/factory/application/preflight.py, two new test modules) against the work item.

   Acceptance criteria: criteria 1 to 4 each have one parametrized test that checks what the criterion says. The Interface's failing sides are covered: other paths in criterion 1 and rows 3 and 4 of criterion 2, `GitError` in criterion 4, the empty list in criterion 1. Journal entry 7 records `make check` green. Architecture: the domain function imports only `factory.domain`, and the application method reaches git through `Boundaries.git`. I also checked that `changed_paths` compares against the work tree, not `origin/main`, and that this is safe: the tick's `_restore_checkout` calls `checkout(main, start_point=origin/main)`, a `switch --force-create`, before the stops are published and the preflight runs. So the work tree never lags `origin/main`, and an extra path in the work tree only makes the rule clear the stop. Security: nothing to report. Quality fails in the new test module, on helpers copied from other modules:

   1. tests/application/test_preflight_stops_commit.py:29 `_log_lines` is a copy of `_log_lines` in tests/application/test_preflight_stale_main_stop.py:23 (also held in test_tick_stop_records.py:86, test_stale_branches.py:26, test_tick.py:183, test_disk_recorder.py:75). Fix: under the standing leave, move it to one shared place under `tests/` and use it from there.
   2. tests/application/test_preflight_stops_commit.py:21 and :80-89 `CLEARED_LINE` and the `failed_once` fixture (body in `_failed_once`) copy `CLEARED_LINE` and `failed_once` in tests/application/test_preflight_stale_main_stop.py:20 and :46. Fix: move both to a shared place (the fixture to `tests/conftest.py` or beside `rig`/`red_main`) and use them from there; the recording variant can build on the shared fixture.
   3. tests/application/test_preflight_stops_commit.py:73 the `records` fixture copies `records` in tests/application/test_tick_stop_records.py:97, word for word. Fix: move it to `tests/conftest.py` under the standing leave and use it from both modules.
   4. tests/application/test_preflight_stops_commit.py:38 `_commit_on_main` is a second implementation, in raw git calls, of `HumanClone.push_file` (tests/human_clone.py:29): fetch, switch to `origin/main`, write, commit, push. Fix: use `rig.human.push_file("main", ...)` for the one-file rows. For the two-file row, reuse the shared helper rather than another raw-git copy.

   Earlier tests: none. Every test file in the diff has status `A`.
10. factory: started doing as self.
11. coder: Round 1. The reviewer's four findings (entry 9) all concern copied helpers in the new test module, tests/application/test_preflight_stops_commit.py. The code in src/factory/domain/preflight.py and src/factory/application/preflight.py does not change. Under the standing leave in CLAUDE.md (*Tests*), the tester moves the helpers, not the coder. These are the moves I am asking the tester to make:
    1. `_log_lines`: move it to one shared module at the root of `tests/`. Use it there from test_preflight_stops_commit.py and the earlier copies: tests/application/test_preflight_stale_main_stop.py, test_tick_stop_records.py, test_stale_branches.py, test_tick.py and test_disk_recorder.py.
    2. `CLEARED_LINE` and the `failed_once` fixture (body `_failed_once`): move them out of tests/application/test_preflight_stale_main_stop.py to a shared place. The constant goes in a shared module and the fixture in `tests/conftest.py` or beside `rig`/`red_main`. test_preflight_stops_commit.py then builds its recording variant on the shared fixture.
    3. The `records` fixture: move it from tests/application/test_tick_stop_records.py to `tests/conftest.py`, and use it from both modules.
    4. `_commit_on_main` in test_preflight_stops_commit.py: replace it with `rig.human.push_file("main", ...)` (tests/human_clone.py) for the one-file rows. For the two-file row, reuse that shared helper (or extend HumanClone in tests/human_clone.py) instead of writing raw git calls again.
    Every earlier test keeps its name and checks the same thing. I did not touch any test. The journal did not change what the task means, so the Description is unchanged. Not touched: the reliance of `changed_paths` on the tick's restore leaving the work tree at `origin/main`. The reviewer confirmed it is safe.
12. factory: started tests as self.
13. tester: Round 1, a test change. I made the four helper moves the coder named in entry 11, from the reviewer's findings in entry 9. They fall under the standing leave in CLAUDE.md (*Tests*) to move a shared test helper. Every earlier test keeps its name and checks the same thing. No source file changed.

    The criterion → test mapping is the same as in entry 5:
    criterion 1: tests/domain/test_preflight_stop_records_paths.py::test_only_the_stop_records_file_is_a_change_of_stop_records_only
    criterion 2: tests/application/test_preflight_stops_commit.py::test_a_failed_machine_keeps_the_failing_stop_only_across_stop_records_commits
    criterion 3: tests/application/test_preflight_stops_commit.py::test_a_kept_failing_stop_appends_no_cleared_record
    criterion 4: tests/application/test_preflight_stops_commit.py::test_a_failed_machine_clears_the_stop_when_the_remembered_commit_is_not_in_the_clone
    criteria 5 and 6: no test (`make check` and the docs).

    The moves:
    1. `_log_lines` is now `log_lines` in a new module, tests/log_support.py. These files use it from there instead of their own copy: tests/application/test_preflight_stops_commit.py, test_preflight_stale_main_stop.py, test_tick_stop_records.py, test_stale_branches.py, test_tick.py and test_disk_recorder.py.
    2. `CLEARED_LINE`, the probe-once helper `fail_once` and the `failed_once` fixture are in a new module, tests/preflight_support.py. The fixture depends on `red_main`, which lives in tests/application/test_preflight_run.py, so it cannot go in conftest.py. Both test_preflight_stale_main_stop.py and test_preflight_stops_commit.py bind it with `failed_once = preflight_support.failed_once`, the same way they already bind `rig`. `failed_once_recording` builds on `fail_once`.
    3. The `records` fixture (stop records) moved from tests/application/test_tick_stop_records.py to tests/conftest.py. The new module uses it from there too. Modules that define their own `records` override it as before. test_stop_publisher.py still holds an identical copy; entry 11 did not name it, so I left it.
    4. `_commit_on_main` is gone. The one-file rows use `Rig.push_main`, which calls `HumanClone.push_file`. For the two-file row I added `HumanClone.push_files(branch, files)` in tests/human_clone.py, and `push_file` now delegates to it with the same commit message.

    Files created: tests/log_support.py, tests/preflight_support.py.
    Earlier test files changed: test_preflight_stale_main_stop.py, test_tick_stop_records.py, test_stale_branches.py, test_tick.py and test_disk_recorder.py (all in tests/application/), plus tests/conftest.py and tests/human_clone.py.
    Modules the test run could not import: none.

    `make lint` and `make test` are both green; total coverage is 99.06 %.

    `lint`: lint: green (0.0 s)
    `test`: test: green (48.5 s)
14. factory: started doing as self.
15. coder: Round 1. All four findings in entry 9 were about copied test helpers. The tester resolved them in entry 13 under the standing leave: tests/log_support.py, tests/preflight_support.py, the shared `records` fixture in tests/conftest.py, and `HumanClone.push_files` in tests/human_clone.py. None of the findings concerned code, so I changed no source this round. src/factory/domain/preflight.py (`changes_only_stop_records`) and src/factory/application/preflight.py (`_clear_stale_failing_stop` and the private `_changes_only_stop_records`) are as entry 7 describes. I ran `make check` on the committed state with the tester's moves in place and it is green (coverage 99.06 %).

    Main choice: same as entry 7. I kept the `GitError` handling in a small private method that returns false, so the stop is cleared. The rejected alternative was a second try/except nested in `_clear_stale_failing_stop`. Refactor: no diff this round, so nothing to change.

    Noticed but did not touch:
    - tests/application/test_stop_publisher.py still holds its own identical copy of the `records` fixture, as the tester noted in entry 13. Removing it is a test change for the tester, and no finding names it.
    - The journal did not change what the task means, so the Description stays as it is.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 0 new, 36 known, 3 gone
16. factory: started review as self.
17. reviewer: no findings

    Round 1 review of `git diff main...HEAD -- . ':!factory'` against the work item. I read the code itself, not the journal's account of it.

    - Acceptance criteria: criteria 1 to 4 each have one parametrized test, and each test checks what its criterion says.
      - Criterion 1 (tests/domain/test_preflight_stop_records_paths.py) has all eight rows. Both sides of the "not empty" limit are tested: `[]` and a single path.
      - Criterion 2 has four rows. Each checks `preflight_failed`, the stop's presence and the log line.
      - Criterion 3 (`stop_records` wired in) expects 0 `cleared` records on one row and 1 on the other.
      - Criterion 4 covers the `GitError` side with `"a" * 40`.
      - Entry 15 records `make check` green after the tester's moves.
    - Architecture:
      - `changes_only_stop_records` (src/factory/domain/preflight.py) is pure and imports only `factory.domain`.
      - `_changes_only_stop_records` (src/factory/application/preflight.py) reaches git only through `Boundaries.git`, and turns `GitError` into a clear, as the Interface says.
      - The other branches of `_clear_stale_failing_stop` are unchanged.
    - Security: nothing to report. No markers, no new baseline entries, no strings built into commands.
    - Quality:
      - The round-0 findings (entry 9) are resolved. The new module now uses `log_lines` (tests/log_support.py), `CLEARED_LINE`/`fail_once`/`failed_once` (tests/preflight_support.py), the shared `records` fixture (tests/conftest.py) and `Rig.push_main`/`HumanClone.push_files` (tests/human_clone.py) in place of its own copies.
      - The comment in `_changes_only_stop_records` explains why.
    - Hygiene: the Description and the docs criterion match what was built.

    Earlier tests:
    - tests/application/test_disk_recorder.py: standing leave. Only `_log_lines` was replaced by the shared `log_lines`.
    - tests/application/test_preflight_stale_main_stop.py: standing leave. `CLEARED_LINE`, the `failed_once` fixture and `_log_lines` moved to tests/preflight_support.py and tests/log_support.py; the tests keep their names and checks.
    - tests/application/test_stale_branches.py: standing leave (`_log_lines` → `log_lines`).
    - tests/application/test_tick.py: standing leave (`_log_lines` → `log_lines`).
    - tests/application/test_tick_stop_records.py: standing leave. The `records` fixture moved to tests/conftest.py, and `_log_lines` became `log_lines`.
    - tests/conftest.py: standing leave. It only gains the shared `records` fixture.
    - tests/human_clone.py: standing leave. The new module's commit helper moved here as `push_files`. `push_file` delegates to it with the same steps and the same commit message.
18. factory: started docs as self.
19. documenter: Docs round 1. No findings; the code matches the Interface and the criteria.

    Files changed (documents only, so I did not run `make check`; the factory's run after this stage decides):
    - `docs/operator-guide.md`, preflight bullets: "A failed machine clears a stale stop" now names the exception (a `main` that differs from the failing commit only in `factory/stops.jsonl`) and says a git error while comparing clears the stop. "A `stops recorded` commit is a new `main`" now says the stop is kept across such a commit with no `cleared` record, that the probe still runs once when the machine's items pass, and that a commit with another file clears as before. The sentence "the rule does not yet ignore a commit that changes only..." is gone.
    - `docs/project-guide.md`, after the preflight paragraph: new paragraph on `Preflight._clear_stale_failing_stop`, `changes_only_stop_records` (`factory.domain.preflight`), the `GitError` branch, and that `changed_paths` compares with the work tree, which the tick's restore leaves at `origin/main`.
    - `docs/decisions.md`, "The stops reach main as raised and cleared records": the "Accepted effect" line now says F0021-S0008 removed it and why (a `cleared` for a `main` nobody fixed misleads the viewer of `factory/stops.jsonl`). It also says skipping the probe is left to a later story.

    Ran the story's smoke test: the Python snippet printed `False`, `True`, `False`, and the `grep -c` printed `0`.

    Cross-read and found current: `README.md`, and the rest of `docs/operator-guide.md` (the stop records section, line ~514) and `docs/project-guide.md` (stop records, tick step 3a/4).

    Stale text noticed, not touched: none. The tests' duplicate `records` fixture in `tests/application/test_stop_publisher.py` (coder's entry 15) is a test matter, not a doc matter.

    `check`: check: green
    `documents`: documents ok
20. factory: started smoke-test as self.
