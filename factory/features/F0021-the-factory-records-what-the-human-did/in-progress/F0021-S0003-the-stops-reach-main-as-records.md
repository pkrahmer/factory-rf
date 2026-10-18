---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 237
comments_read: [6256126020]
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
