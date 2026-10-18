---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 237
comments_read: [6256126020, 6256259182, 6256356204]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T22:46:44.894540Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T22:46:44.901225Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-18T22:47:01.667121Z'
  stage: intake
  run: 5d1423ebb19442048d35512415edc976
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-18T22:48:18.289456Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-18T22:48:35.785156Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-18T22:48:55.189607Z'
  stage: intake
  run: f584f613515e4e1cac9ff6bb6407a1d5
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-18T22:49:15.553197Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-18T22:54:31.153953Z'
  stage: tests
  run: bd9ecdf01ed346f3b2c348090b7ca8c1
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-18T22:54:51.522529Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-18T22:58:46.457824Z'
  stage: doing
  run: 6b4701134d7d4c3f8feaa0508449ca57
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-18T22:59:06.989398Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-18T23:00:20.925662Z'
  stage: review
  run: 2c05376bbe2f4030bc177027c09b4058
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-18T23:00:41.938784Z'
  stage: doing
- number: 14
  speaker: coder
  kind: question
  at: '2026-10-18T23:01:09.171400Z'
  stage: doing
  run: 1cd3c380014e4e4391ea7a5b39933061
  blocked: question
- number: 15
  speaker: human
  kind: comment
  at: '2026-10-18T23:02:25.486970Z'
  stage: doing
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-18T23:02:42.986595Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-10-18T23:04:17.888582Z'
  stage: doing
  run: b95fd51aa7ff4e6b83a0357ad17941d8
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-18T23:04:38.186578Z'
  stage: tests
- number: 19
  speaker: tester
  kind: result
  at: '2026-10-18T23:06:58.219503Z'
  stage: tests
  run: bcbfa723bba04dd3b3bae392a4097d65
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-18T23:07:18.146766Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-10-18T23:09:16.702072Z'
  stage: doing
  run: 39be84f13ce74600aa8f49a7eaa7e920
- number: 22
  speaker: factory
  kind: started
  at: '2026-10-18T23:09:36.870902Z'
  stage: review
- number: 23
  speaker: reviewer
  kind: question
  at: '2026-10-18T23:11:43.155277Z'
  stage: review
  run: c661d758aeb347b29204bedfc0bd085f
  blocked: question
- number: 24
  speaker: human
  kind: comment
  at: '2026-10-18T23:13:00.080334Z'
  stage: review
---

# The stops reach main as records

## Description

A stop of the repository or the machine (`fetch_failed`, `disk_low`, `preflight_failed` and the rest) is today a line in `/state/factory.log` and an entry in the health status, both on the instance, where the status-map viewer cannot reach them. This story records each stop as two events, `raised` when a stop of its reason is first raised and `cleared` when it clears, each a JSON line in `records/stops.jsonl` in the state directory, and every tick, right after the checkout was restored and before the preflight, pushes to `factory/stops.jsonl` on `main` the records `main` does not hold yet. A record holds the event, the scope, the reason, the time and the instance, never the stop's detail (the feature's decisions 1 to 3). A tick that stops before the restore succeeded (`disk_low`, `fetch_failed`, `pipeline_definition_invalid`, `agent_definition_invalid`, `checkout_restore_failed`) publishes nothing; the records wait in the state directory for the next tick that gets past the restore. A failed push, any other git error or a failed write leaves the records in the state directory for the next tick and only writes a line to the factory log, so a stop is never lost because git was what failed, and a record is never pushed twice. The factory now pushes `main` after a stop event as well as after an archive: the commit `stops recorded` runs the preflight's probe of `main` again, and while `preflight_failed` stands it clears a standing `main_branch_failing` although `main` is still red; the feature's decision 1 accepts that for now, and the documents say so. The health status, the factory log's stop lines and the stop written by `factory-run` for invalid settings stay as they are. The run record's refused tool calls are S0004's.

## Interface

`factory.domain.stops` (`domain`):

```python
StopEvent = Literal["raised", "cleared"]


class StopRecord(BaseModel):
    """One event of a stop of the repository or the machine, as the remote keeps it."""

    event: StopEvent
    scope: StopScope
    reason: RepositoryStopReason
    at: UtcDatetime
    instance: Name | None = None


def stop_records_text(records: Sequence[StopRecord]) -> str:
    """One `model_dump_json()` line per record, each ending in a newline; `""` for none."""


def parse_stop_records(text: str) -> list[StopRecord]:
    """The records of the lines of `text` that validate, in order; other lines are skipped."""
```

- `scope` must match `reason` exactly as for `RepositoryStop` (`machine` for `preflight_failed` and `disk_low`, `repository` for every other reason); the rule is one function both models use, not a copy.
- The fields are written in the order above; a record's line is `{"event":...,"scope":...,"reason":...,"at":"<UTC>Z","instance":...}`.

`factory.domain.paths` (`domain`): `STOP_RECORDS_FILE = "factory/stops.jsonl"`.

`factory.application.boundaries.Boundaries` (`application`): a new last field `stop_records: RecordLog[StopRecord] | None = None`.

`factory.application.stops` (`application`):

- `StopService.raise_stop(stop)`: when the health status read before the write holds no stop of `stop.reason`, it also appends `StopRecord(event="raised", scope=stop.scope, reason=stop.reason, at=stop.at, instance=<settings.instance, or None without settings>)` to `stop_records`. A stop of that reason already standing appends nothing. The append is tried like the log line and the health status (the decision "Both destinations of a stop are tried"): an `OSError` of any of the three is raised after all three were tried.
- `StopService.clear_stop(reason)`: when a stop of `reason` stood, after the health status and the log line, it appends `StopRecord(event="cleared", scope=<the standing stop's scope>, reason=reason, at=clock.now(), instance=...)`. Nothing stood: nothing is appended. An `OSError` of the append propagates, as one of the health status write does today.
- Without `stop_records` (`None`), both behave exactly as today.

```python
class StopPublisher:
    """Pushes the stop records the remote's main does not hold yet to its stop records file."""

    def __init__(self, boundaries: Boundaries) -> None: ...

    def publish(self) -> list[StopRecord]:
        """Push the missing records to `STOP_RECORDS_FILE` on main; return them.

        Raises `GitError`, `PushFailed`, and `OSError` when the file cannot be written.
        """
```

- Without `stop_records`, or with no record in it, `publish` returns `[]` and calls no git operation. When `origin/main`'s `STOP_RECORDS_FILE` (read with `git.show_file`; a missing file reads as empty) holds every local record (`parse_stop_records`, compared as whole records), it returns `[]` and makes no commit.
- Otherwise it stands on `main` at `origin/main` through `WorkItemRecorder.check_out`, writes `boundaries.checkout / STOP_RECORDS_FILE` with `Path.write_text(..., encoding="utf-8", newline="\n")`, creating `factory/` when it is missing, as the text it read, with a newline added when that text is not empty and does not end in one, followed by `stop_records_text(missing)` (the missing records in local order, each once), and commits and pushes through `WorkItemRecorder.publish(MAIN_BRANCH, "stops recorded")`. Lines of the file that do not validate stay as they are.
- A refused push raises `PushFailed`; the local records stay, so the next call pushes them.

`factory.application.tick.Tick.run` (`application`): right after the restore succeeded (the checkout clean on `main` at `origin/main`), before the preflight, the tick calls `StopPublisher(boundaries).publish()`. A `GitError`, `PushFailed` or `OSError` from it writes `cannot publish the stop records: <error>` to the factory log, and the tick goes on as if it had published nothing. A tick that stops before the restore succeeds (`disk_low`, `fetch_failed`, `pipeline_definition_invalid`, `agent_definition_invalid`, `checkout_restore_failed`) publishes nothing; the records wait in the state directory for the next tick that gets past the restore.

`factory.entry.wiring.build_boundaries` (`entry`): `stop_records=JsonLinesRecordLog(<state directory>/records/stops.jsonl, StopRecord)`.

Test modules (new): `tests/domain/test_stop_records.py`, `tests/application/test_stop_records_service.py`, `tests/application/test_stop_publisher.py`, `tests/application/test_tick_stop_records.py`, `tests/entry/test_wiring_stop_records.py`. No earlier test changes.

## Acceptance criteria

1. `StopRecord`, rows of one parametrized test: `scope="machine"` with `reason="disk_low"` and with `reason="preflight_failed"`, and `scope="repository"` with `reason="fetch_failed"`, are accepted; `scope="repository"` with `reason="disk_low"` and `scope="machine"` with `reason="fetch_failed"` are refused; `event="paused"` (through a variable typed `type[BaseModel]`) is refused.
2. `stop_records_text` of a `raised` record at 2026-10-18 10:00 UTC for `disk_low`, instance `self`, is exactly `{"event":"raised","scope":"machine","reason":"disk_low","at":"2026-10-18T10:00:00Z","instance":"self"}` and a newline; of no records, `""`.
3. `parse_stop_records`, rows of one parametrized test: the text of two records gives both in order; a blank line, a line that is not JSON and a line with an unknown reason between them are skipped; `""` gives `[]`.
4. `StopService.raise_stop`, rows of one parametrized test: a first `fetch_failed` appends one `raised` record with the stop's scope, reason and `at` and the settings' instance; a second raise of `fetch_failed` while it stands appends nothing more; a `disk_low` raised while `fetch_failed` stands appends a `raised` record for `disk_low`; boundaries without settings give `instance` `None`.
5. `StopService.clear_stop`, rows of one parametrized test: clearing a standing `fetch_failed` appends one `cleared` record with scope `repository` and the clock's time; clearing a standing `disk_low` gives scope `machine`; clearing a reason that does not stand appends nothing; the `cleared` record's `instance` is the settings' instance.
6. With `stop_records` `None`, a raise and a clear write the log lines and the health status as today and append nowhere.
7. A record log whose `append` raises `OSError`: `raise_stop` still writes the log line and the health status, and then raises that `OSError`; `clear_stop` removes the stop from the health status, writes `stop cleared <reason>`, and then raises it (rows of one parametrized test).
8. `StopPublisher.publish` with two local records and no `factory/stops.jsonl` on `origin/main`: it returns both, `origin/main` then holds the file with exactly their two lines in local order, and the commit's subject is `stops recorded`; the same when `origin/main` has no `factory/` folder at all (a second row of the same parametrized test).
9. `StopPublisher.publish` when `origin/main`'s file already holds lines, rows of one parametrized test: the file holds the first of three local records and one line that does not validate: it returns the second and third, and the file holds its earlier two lines unchanged followed by the two new lines; the file's last line has no newline: a newline is added after it, before the new lines; the local log holds the second record twice: it is returned and written once.
10. `StopPublisher.publish` makes no commit (`origin/main`'s head unchanged) and returns `[]`, rows of one parametrized test: with `stop_records` `None`; with an empty record log; when `origin/main`'s file holds every local record.
11. `StopPublisher.publish` when `main` moved on the remote after the fetch (the human pushed): `PushFailed` is raised, `origin/main` holds no `stops recorded` commit, and a second call after a fetch publishes the records once.
12. `Tick.run` and the publish, rows of one parametrized test on the records of `origin/main`'s `factory/stops.jsonl` after each tick: a tick with a local record that `origin/main` does not hold publishes it; a tick whose fetch fails publishes nothing, and the next tick, whose fetch succeeds, publishes the `raised` and the `cleared` record of `fetch_failed`; a tick stopped by `disk_low` (a disk below `min_free_gb`) publishes nothing, and the next tick with room publishes its `raised` and `cleared` records; a tick stopped by `pipeline_definition_invalid`, one by `agent_definition_invalid` and one by `checkout_restore_failed`, each with a local record present, leave `origin/main` without a new commit on that tick.
13. `Tick.run` when the publish fails, rows of one parametrized test: the publish's push is refused (a hook of the remote refuses `main`); `origin/main` holds a folder `factory/stops.jsonl/`, so that the write raises `OSError`; `origin/main` does not resolve, so that `publish` raises `GitError`. In all three the factory log holds a line starting `cannot publish the stop records: `, the local records stay, and the tick still evaluates and dispatches its event.
14. `StopPublisher.publish` with a local record, on a checkout whose `origin/main` does not resolve (a bare remote with no `main`, fetched): it raises `GitError`, and the local record log holds the same records afterwards.
15. `build_boundaries` gives `stop_records` a record log at `<state directory>/records/stops.jsonl` that reads back a record it appended.
16. `make check` stays green.
17. docs:
    - `docs/operator-guide.md`, *The records*: `records/stops.jsonl` (its fields, when each event is written, that it is never cleared by the factory and is safe to delete only when `main` holds every line); *The stops*: that each stop's events reach `factory/stops.jsonl` on `main` at the next tick that gets past the restore, as commits `stops recorded`, without the detail, and the log line `cannot publish the stop records: <error>`; and that the human pulls `main` before pushing to it, since the factory now pushes `main` after a stop event as well as after an archive; *The stamp and the probe of the main branch*: a `stops recorded` commit counts as a new `main`, so the probe runs again, and while the machine's items fail (`preflight_failed` stands) it clears `main_branch_failing` and writes a `cleared` record for it although `main` is still red; the probe raises it again once the machine's items pass (the feature's decision 1 accepts this for now).
    - `docs/project-guide.md`, *Stops, the clock and the factory log*: `StopRecord`, `StopPublisher` and the tick's call, with its place after the restore and why (the restore logs what a killed stage left behind before the publisher's checkout could discard it).
    - `docs/decisions.md`: a new entry, "The stops reach main as raised and cleared records", with the reason and the rejected places of the feature's decisions 1 to 3, the place of the publish in the tick, and the accepted effect on the preflight's stale-stop rule (a `stops recorded` commit clears `main_branch_failing` while `preflight_failed` stands; a later story may make the rule ignore a commit that changes only `factory/stops.jsonl`).

## Smoke test

```bash
uv run -q python -c '
from datetime import UTC, datetime
from factory.domain.stops import StopRecord, parse_stop_records, stop_records_text

at = datetime(2026, 10, 18, 10, 0, tzinfo=UTC)
record = StopRecord(event="raised", scope="machine", reason="disk_low", at=at, instance="self")
text = stop_records_text([record])
print(text, end="")
print(parse_stop_records(text + "not json\n") == [record])
try:
    StopRecord(event="cleared", scope="repository", reason="disk_low", at=at)
except ValueError:
    print("refused")
'
```

Expect: three lines, `{"event":"raised","scope":"machine","reason":"disk_low","at":"2026-10-18T10:00:00Z","instance":"self"}`, `True`, `refused`.

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: Format check passed. Interface, architecture and scope are fine: the layers are right, the story sits inside feature.md's decisions 1 to 3, and the smoke test is runnable with checkable Expect lines. Three Interface clauses have no criterion, so two coders could read them two ways.

   1. The tick's error handling names `GitError`, `PushFailed` and `OSError`. Criterion 13 covers only a refused push (`PushFailed`) and a folder in the file's place (`OSError`). Should a third row make `publish` raise `GitError` inside `Tick.run`, for example with `origin/main` unresolvable, and check the same log line and that the tick goes on? I would add that row to criterion 13.

   2. The Interface says a tick that stops before the restore succeeds publishes nothing, and it lists five reasons: `disk_low`, `fetch_failed`, `pipeline_definition_invalid`, `agent_definition_invalid` and `checkout_restore_failed`. Criterion 12 tests only `fetch_failed` and `disk_low`. Should it get rows for the other three? I would add them, each with a local record present, checking that `origin/main` gains nothing on that tick.

   3. `publish` must create `factory/` "when it is missing", but criterion 8 does not say whether the checkout has that folder. Should criterion 8 gain a row where `origin/main` has no `factory/` folder at all and the file still ends up with the two lines? I would add it. Otherwise I would drop the clause.

   A smaller point, not blocking: criterion 5 does not check `instance` on the `cleared` record, though the Interface sets it. I would add "instance is the settings' instance" to that criterion.
4. 2026-10-18 human: 1. Yes: add the `GitError` row (origin/main unresolvable) to criterion 13, same log line, the tick goes on.
   2. Yes: add rows for `pipeline_definition_invalid`, `agent_definition_invalid` and `checkout_restore_failed` to criterion 12, each with a local record present, origin/main gains nothing.
   3. Yes: add the row to criterion 8 where origin/main has no `factory/` folder; keep the clause.
   4. Yes: add "instance is the settings' instance" to criterion 5.
5. factory: started intake as self.
6. intake: accepted. The human's answer is journal entry 4. I carried its four edits into the story and changed nothing else:
   - Criterion 5: the `cleared` record's `instance` is the settings' instance.
   - Criterion 8: a second row where `origin/main` has no `factory/` folder. The `factory/` clause stays.
   - Criterion 12: rows for `pipeline_definition_invalid`, `agent_definition_invalid` and `checkout_restore_failed`, each with a local record present and no new commit on `origin/main`.
   - Criterion 13: a third row where `origin/main` does not resolve, so `publish` raises `GitError`. The same log line is expected and the tick goes on.

   Checks:
   - Interface: it names concrete modules and signatures (`factory.domain.stops`, `factory.domain.paths`, `Boundaries`, `StopService`, `StopPublisher`, `Tick.run`, `build_boundaries`). Every behaviour stated in an Interface comment has a criterion: the JSON line format and field order (2), the scope rule (1), the append and no-append cases (4, 5), the `None` case (6), the `OSError` after all three destinations were tried (7), and the file text rules for newline, duplicates and unvalidated lines (9).
   - Criteria: each is testable by one parametrized test, and each rule has a criterion for its failing side. Examples: the refused scopes and the unknown event (1); the refused push (11, 13); the `GitError` (14, 13); no commit for `None`, an empty log or a file that already holds every record (10); and the five pre-restore stops publishing nothing (12).
   - Smoke test: it is runnable. The three Expect outputs (the JSON line, `True`, `refused`) can be checked against the output.
   - Architecture: `domain` holds the record and the pure text functions. `application` holds the service and the publisher, which reach git only through `WorkItemRecorder` and the boundaries. `entry` holds the wiring. The layering is respected.
   - Scope: the story is inside the feature's decisions 1 to 3. It leaves out `factory-run`'s invalid-settings stop, the health status and S0004's refused calls, as the feature's "Out of scope" requires.
7. factory: started tests as self.
8. tester: I wrote the tests for criteria 1 to 15. Each criterion is one test function, and a criterion with rows is one parametrized test. `make lint` is green. One `make test` run fails as it should: the new test modules hit an ImportError at collection, because `StopRecord`, `stop_records_text`, `parse_stop_records`, `StopPublisher`, `STOP_RECORDS_FILE` and `Boundaries.stop_records` do not exist yet. The tail of the output named four of the modules; `test_stop_publisher.py` imports the same missing names.

   - criterion 1: tests/domain/test_stop_records.py::test_a_stop_record_accepts_a_known_event_and_the_scope_of_its_reason
   - criterion 2: tests/domain/test_stop_records.py::test_the_records_text_is_one_json_line_per_record_in_field_order
   - criterion 3: tests/domain/test_stop_records.py::test_parsing_keeps_the_records_that_validate_in_order
   - criterion 4: tests/application/test_stop_records_service.py::test_a_raise_appends_a_raised_record_when_no_stop_of_its_reason_stands
   - criterion 5: tests/application/test_stop_records_service.py::test_a_clear_of_a_standing_stop_appends_a_cleared_record_at_the_clock_time
   - criterion 6: tests/application/test_stop_records_service.py::test_without_stop_records_a_raise_and_a_clear_write_only_the_log_and_the_health_status
   - criterion 7: tests/application/test_stop_records_service.py::test_an_unwritable_record_log_raises_after_the_log_and_the_health_status_were_written
   - criterion 8: tests/application/test_stop_publisher.py::test_the_local_records_reach_a_new_file_on_main_in_local_order
   - criterion 9: tests/application/test_stop_publisher.py::test_only_the_missing_records_are_added_after_the_lines_main_holds
   - criterion 10: tests/application/test_stop_publisher.py::test_nothing_to_publish_makes_no_commit
   - criterion 11: tests/application/test_stop_publisher.py::test_a_main_moved_on_after_the_fetch_refuses_the_push_and_the_next_call_publishes_once
   - criterion 12: tests/application/test_tick_stop_records.py::test_a_tick_publishes_the_records_only_once_it_got_past_the_restore
   - criterion 13: tests/application/test_tick_stop_records.py::test_a_failed_publish_is_logged_and_the_tick_goes_on
   - criterion 14: tests/application/test_stop_publisher.py::test_a_main_that_does_not_resolve_raises_git_error_and_keeps_the_records
   - criterion 15: tests/entry/test_wiring_stop_records.py::test_the_built_stop_records_read_back_a_record_from_the_state_directory

   How I set up the harder cases:
   - **Criterion 12, fetch row:** the fetch fails because the checkout's `origin` URL is pointed at a path that does not exist, and the next step points it back.
   - **Criterion 12, restore row:** a read-only folder makes the restore fail, as in `test_tick.py`. The row is skipped when the tests run as root.
   - **Criterion 13, refused push:** a `pre-receive` hook in the bare remote refuses `refs/heads/main`.
   - **Criterion 13, `GitError` row:** a tick that gets past the restore always has a resolvable `origin/main`. So this row uses `_UnresolvableMainForStopRecords`, a `GitCli` subclass that is real git throughout. Only while `factory/stops.jsonl` is read does it delete `refs/remotes/origin/main` and then put it back, so the `GitError` comes from real git.
   - **Criterion 14:** this one needs no subclass. The test deletes `main` in the bare remote and fetches with prune, so `origin/main` really does not resolve.
   - **Reading the remote:** the tests read `main:factory/stops.jsonl` straight from the bare remote.

   I changed no earlier test file. Criteria 16 and 17 have no test: they are `make check` and the docs.

   Files created: tests/domain/test_stop_records.py, tests/application/test_stop_records_service.py, tests/application/test_stop_publisher.py, tests/application/test_tick_stop_records.py, tests/entry/test_wiring_stop_records.py.

   Modules the test run could not import: `factory.domain.stops` lacks `StopRecord`, `stop_records_text` and `parse_stop_records`; `factory.application.stops` lacks `StopPublisher`; `factory.domain.paths` lacks `STOP_RECORDS_FILE`.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/entry/test_wiring_stop_records.py - ImportError while importing t...
9. factory: started doing as self.
10. coder: I built the stop records and their publish to `main`. The tester's tests were not changed, and `make check` is green (lint, types, layers, sast, secrets, licenses, test). `make duplicates` reports 0 new, 36 known and 3 gone.

    What I changed:
    - `src/factory/domain/stops.py`: added `StopEvent`, `StopRecord`, `stop_records_text` and `parse_stop_records`. The scope-for-reason rule is now one private function, `_require_scope_of_reason`, and the validators of both `RepositoryStop` and `StopRecord` call it. `parse_stop_records` skips any line that raises `ValidationError`, which also covers blank lines and lines that are not JSON.
    - `src/factory/domain/paths.py`: added `STOP_RECORDS_FILE`.
    - `src/factory/application/boundaries.py`: added `stop_records` as the new last field.
    - `src/factory/application/stops.py`:
      - `StopService.raise_stop` appends a `raised` record only when the health status it read held no stop of that reason. The append is tried like the log line and the health status, and the first `OSError` is raised after all three were tried.
      - `clear_stop` appends a `cleared` record, with the standing stop's scope and the clock's time, after the health status and the log line.
      - One private helper, `_record`, builds both records. It takes the instance from the settings, or `None` without settings.
      - Added the new `StopPublisher`. It reads `origin/main`'s file with `git.show_file`, works out the missing records (local order, each once) and makes no git call when there is nothing to publish. Otherwise it checks out `main` through `WorkItemRecorder.check_out`, writes the file (creating `factory/` and adding a newline the old text lacked) and calls `WorkItemRecorder.publish(MAIN_BRANCH, "stops recorded")`.
    - `src/factory/application/tick.py`: added `_publish_stop_records`, which runs between `_restore()` and `_run_preflight()`. On `GitError`, `PushFailed` or `OSError` it writes `cannot publish the stop records: <error>` to the log and the tick goes on. The module docstring now names the step.
    - `src/factory/entry/wiring.py`: `stop_records` is now a `JsonLinesRecordLog` at `<state>/records/stops.jsonl`.

    Main choice: I put `StopPublisher` in `factory.application.stops` and had it reuse `WorkItemRecorder` from `factory.application.handlers.recording`, as the Interface says. The alternative I rejected was a new module for the publisher, or copying `WorkItemRecorder`'s checkout and commit-and-push steps. The new module would split the stop code across two places, and the copy would be a second copy of an existing helper. The import causes no cycle, because `handlers/recording.py` imports neither `stops` nor the handlers.

    Refactor pass: the only change was folding the `show_file` read and its `or ""` into one line. Nothing else needed changing.

    Noticed but not touched:
    - When `raise_stop` cannot read the health status, it appends no `raised` record. It cannot tell whether the stop is new, and recording it anyway could give a duplicate `raised` line. No criterion covers this case.
    - `make duplicates` lists three findings as gone: the unused `close` methods in `fake_hosting.py`, `pygithub_hosting.py` and `application/hosting.py`. They come from earlier work on `main`, not this story.

    The journal did not change the meaning of the task, so I left `## Description` as it is.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 36 known, 3 gone
11. factory: started review as self.
12. reviewer: Group 1 (acceptance criteria) fails. I read every new test against its criterion. Criteria 1 to 15 each have a test, and each test checks what its criterion says. The coder's entry 10 reports the factory's `make check` as green. One rule the Interface states has no criterion for its failing side, and the code reads that rule in a way the human has not decided.

    1. Story, criterion 7, against the Interface clause of `StopService.raise_stop`. The Interface says "an `OSError` of any of the three is raised after all three were tried", but criterion 7 only covers the record log's `append` failing. When the log line raises, or the health status read or write raises, nothing tests that a `raised` record is still appended and the `OSError` raised after it. Fix: the human adds a criterion with those rows: the log line raises, the health status write raises, the health status read raises. Until then the coder can only ask, under R9.
    2. `src/factory/application/stops.py`, `raise_stop`. `standing = True` sits before `health.read()`, so a failed read skips the append. That stop then never reaches the records, and the Interface's "all three were tried" does not hold. The coder noted this in entry 10 but no criterion settles it. Fix: the coder asks the human (R8) whether a failed read should still append the `raised` record, at the risk of a second `raised` line, or append nothing. The answer goes into the criterion of finding 1, and the code follows it.

    Earlier tests: none. `git diff --name-status main...HEAD` shows only added test files (status `A`), so no test that `main` already holds was changed, renamed or deleted.
13. factory: started doing as self.
14. coder: Round 1. I stopped before changing any code. Both review findings (entry 12) need a decision from the human before code or tests can change (R8, R9). The code from entry 10 is unchanged in the working tree, and `make check` was green there.

    **The question.** `StopService.raise_stop` has three steps: the log line, the health status (a read, then a write) and the record append. The Interface says "an `OSError` of any of the three is raised after all three were tried". When should a `raised` record be appended if the log line or the health status fails? This is in `src/factory/application/stops.py`, `raise_stop`.

    What the code does now:
    - **The log line raises:** the record is appended, then the `OSError` is raised.
    - **The health status write raises** (the read worked): the read already showed whether the stop was standing, so the record is appended exactly as without the error, then the `OSError` is raised.
    - **The health status read raises:** the code cannot tell whether a stop of this reason already stands, so it appends nothing. The `OSError` is raised. The status is not written either.

    There are two options for the read failure:
    - **(a) Append the `raised` record anyway.** The stop is in the records right away. But the health status still does not hold the stop, so the next raise of the same reason appends a second `raised` line. And if the cause goes away before the status is readable again, `clear_stop` finds nothing standing. The `raised` then never gets a `cleared`.
    - **(b) Append nothing (what the code does now).** The records stay paired with the health status. The next raise that can read the status finds no stop standing and appends the `raised` record then. The cost: if the cause clears before the status can be read again, that brief stop never reaches the records. The factory log still holds its line.

    **I would choose (b).** Records that agree with the health status give every `raised` exactly one `cleared`, which is what the status-map viewer needs. The Interface sentence would then read: "tried like the log line and the health status, except that without a readable health status no record is appended".

    Whichever you choose, this needs a new criterion, placed before 16 (`make check` stays green) and 17 (docs), as rows of one parametrized test:
    - the log line raises: a `raised` record is appended and the `OSError` is raised;
    - the health status write raises: a `raised` record is appended and the `OSError` is raised;
    - the health status read raises: under (b) no record is appended, under (a) one is; either way the `OSError` is raised.

    The intake stage then puts it into the story, and the tester writes the test. If you choose (a), I change `raise_stop` to append whenever the read failed.

    **Noticed, not touched:** nothing new beyond entry 10.
15. 2026-10-18 human: (b): without a readable health status no record is appended. Change the Interface sentence as you propose, and add the new criterion before 16 as rows of one parametrized test (log line raises: record appended, OSError raised; status write raises: record appended, OSError raised; status read raises: no record, OSError raised).
16. factory: started doing as self.
17. coder: Round 1, after the human's answer (entry 15: option (b)). This needs a new test, so I am handing to the tester.

    The test change: in `tests/application/test_stop_records_service.py`, add one parametrized test of `StopService.raise_stop` with three rows, one per failing destination:
    - the log line raises: a `raised` record is appended and the `OSError` is raised;
    - the health status write raises: a `raised` record is appended and the `OSError` is raised;
    - the health status read raises: no record is appended and the `OSError` is raised.

    Code: `src/factory/application/stops.py`, `raise_stop`, already behaves this way. The code from entry 10 is unchanged apart from one comment I added before `standing = True`, which says why: without a readable status no record is appended, so the records stay paired with the health status. `make check` is green after the change.

    Main choice: I kept the existing control flow, which already gives (b). The alternative I rejected was restructuring `raise_stop` so the read and the write are tried separately. Nothing in the answer asks for that, and behaviour would not change.

    Work item not updated: my edit of the work item was refused with `Permission denied`, so the work item is outside my write paths. The journal changed the task in two places, and both are still open for whoever can write the work item:
    - The Interface sentence of `StopService.raise_stop` should read: "The append is tried like the log line and the health status (the decision "Both destinations of a stop are tried"), except that without a readable health status no record is appended: an `OSError` of any of the three is raised after all three were tried."
    - A new criterion 16 should hold the three rows above, so that `make check` becomes 17 and docs becomes 18.

    Noticed, not touched: nothing beyond entry 10.
18. factory: started tests as self.
19. tester: Round 1. This is the test change the human approved: the answer is entry 15, and the coder named the change in entry 17. I added one parametrized test to `tests/application/test_stop_records_service.py` and changed nothing else.

    - new criterion (`raise_stop` when the log line or the health status fails): tests/application/test_stop_records_service.py::test_a_raise_whose_log_or_health_status_fails_records_only_with_a_readable_status. It has three rows:
      - `log-line`: the factory log raises. One `raised` record is appended and the `OSError` is raised.
      - `health-status-write`: the health status write raises. One `raised` record is appended and the `OSError` is raised.
      - `health-status-read`: the health status read raises. No record is appended and the `OSError` is raised.

      Each row checks that the error raised is the very `OSError` that was injected, and reads the records back from a real `JsonLinesRecordLog` under `tmp_path`.

    How the failures are made: I added two private fakes to the module, each built on its interface. `_UnwritableLog` is a `FactoryLog` that raises on every line. `_FailingHealth` is an empty `HealthStatusStore` that raises on either `read` or `write`. Each row is a typed `Callable[[Boundaries, OSError], Boundaries]` that swaps one of these into the boundaries with `dataclasses.replace`. The two `_UnwritableHealth` fakes in `test_stops.py` and `test_pipeline_loading.py` were no use here: both read fine and only refuse writes, so they cannot fail a read. I did not move them, and I changed no earlier test file.

    `make test` is green, new test included, because `raise_stop` already behaves as option (b) (entry 17). `make lint` is green after a `ruff format` of the file.

    Still open, and outside this change: the work item's `## Description` does not have the new Interface sentence or the new criterion yet (the coder's edit was refused, entry 17). That criterion should become 16, so `make check` becomes 17 and docs becomes 18.

    Files changed: tests/application/test_stop_records_service.py. Files created: none. Modules the test run could not import: none.

    `lint`: lint: green (0.0 s)
    `test`: test: green (39.6 s)
20. factory: started doing as self.
21. coder: Round 1, after the tester's entry 19. That entry added the test the human approved in entry 15 (option (b)): tests/application/test_stop_records_service.py::test_a_raise_whose_log_or_health_status_fails_records_only_with_a_readable_status. The code already did what that test checks (entries 10 and 17), so I changed no code this run. `make check` is green with the new test (test: green, coverage 99.07 %, check: green). I did not change any test.

    What I built (same as entries 10 and 17, nothing new this run): src/factory/domain/stops.py, src/factory/domain/paths.py, src/factory/application/boundaries.py, src/factory/application/stops.py (`StopService.raise_stop`/`clear_stop` record the stop events; `StopPublisher`), src/factory/application/tick.py (`_publish_stop_records` between the restore and the preflight), src/factory/entry/wiring.py.

    The review findings in entry 12:
    - Finding 1 (no criterion for a failing log line or health status): now covered by the tester's new three-row test.
    - Finding 2 (a failed health status read skips the append): the human chose option (b) in entry 15, so no record is appended without a readable status. That is what `raise_stop` does. One comment says why, at the line `standing = True` in src/factory/application/stops.py.

    Main choice: I kept `raise_stop`'s control flow as it is, because it already does (b). I rejected splitting the health status read and write into separate try blocks, because behaviour would not change.

    Refactor pass: I reread the diff and found nothing to change.

    Still open:
    - The journal changed the task, but the work item is outside my write paths, so its `## Description` and criteria are not updated (entry 17).
    - The Interface sentence of `StopService.raise_stop` should gain: "except that without a readable health status no record is appended".
    - A new criterion 16 should hold the three rows of the new test. `make check` then becomes 17 and docs 18.

    Noticed, not touched: nothing beyond entry 10. That is the three `close` methods that `make duplicates` lists as gone, which came from earlier work on main.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 36 known, 3 gone
22. factory: started review as self.
23. reviewer: Round 1 review. I read the source diff and the five new test modules against the criteria. Groups 1 to 4 pass. Criteria 1 to 15 each have a test that checks what the criterion says, and the human's entry 15 has its three-row test, `tests/application/test_stop_records_service.py::test_a_raise_whose_log_or_health_status_fails_records_only_with_a_readable_status`. The factory's `make check` after the coder was green (entry 21). The layers hold: `StopPublisher` reaches git only through the boundaries and `WorkItemRecorder`. The scope rule is one shared function, and nothing silences a check. Group 5 fails:

    1. Work item, `## Interface`, the `StopService.raise_stop` clause: it lacks the human's option (b) from entry 15, which the code (`src/factory/application/stops.py`, `raise_stop`) and the new test implement. Fix: change the sentence to the one entry 17 proposes: "…tried like the log line and the health status (the decision "Both destinations of a stop are tried"), except that without a readable health status no record is appended: an `OSError` of any of the three is raised after all three were tried."
    2. Work item, `## Acceptance criteria`: no criterion matches that new test, although entry 15 asked for one before the closing two. Fix: add criterion 16, "`StopService.raise_stop` when a destination fails, rows of one parametrized test: the log line raises: one `raised` record is appended and the `OSError` is raised; the health status write raises: the same; the health status read raises: no record is appended and the `OSError` is raised". `make check` becomes 17 and docs becomes 18.
    3. Work item, the docs criterion, `docs/operator-guide.md` *The records*: "when each event is written" leaves out the option (b) exception, so the documenter would not write it. Fix: add "a raise whose health status cannot be read writes no `raised` record; the next raise that can read it does".

    **Question for the human.** Nobody in the `doing` loop can make these edits. In `factory/pipeline.yml` the coder's write paths are `src/*`, `image/*`, `template/*` and `claude/*`. Its edit of the work item was refused (entry 17). Sending the work item back to `doing` would only stall it. The reviewer's write paths do include `{work_item}`, but my role is to find problems, not fix them. The options I see:
    - (a) You commit the three edits to the work item's Description yourself. The next review then checks them and passes to `docs`.
    - (b) You give the reviewer leave to make exactly these three edits on the next review run, and nothing else. It then reviews again and passes to `docs`.
    - (c) You accept the Description as it is, with entry 15 as the record. In that case the operator guide will probably not mention the read-failure case.

    I would choose (b). It keeps the edits inside the pipeline, and the wording is already fixed by entries 15 and 17.

    Earlier tests: none needed. `git diff --name-status main...HEAD` shows every test file as added (`A`), so no test file that `main` already holds was changed, renamed or deleted.
24. 2026-10-18 human: (b): the reviewer has leave to make exactly these three edits to the work item on the next review run, worded as in entries 15 and 17 (the Interface sentence, criterion 16 with make check 17 and docs 18, and the docs criterion's line on a raise without a readable health status), and nothing else; then review again.
