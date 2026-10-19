---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 243
comments_read: []
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-19T01:07:11.762646Z'
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
