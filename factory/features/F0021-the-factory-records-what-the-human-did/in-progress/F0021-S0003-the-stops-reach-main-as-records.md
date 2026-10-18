---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-18T22:46:44.901225Z'
  lease_duration: 60
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
5. `StopService.clear_stop`, rows of one parametrized test: clearing a standing `fetch_failed` appends one `cleared` record with scope `repository` and the clock's time; clearing a standing `disk_low` gives scope `machine`; clearing a reason that does not stand appends nothing.
6. With `stop_records` `None`, a raise and a clear write the log lines and the health status as today and append nowhere.
7. A record log whose `append` raises `OSError`: `raise_stop` still writes the log line and the health status, and then raises that `OSError`; `clear_stop` removes the stop from the health status, writes `stop cleared <reason>`, and then raises it (rows of one parametrized test).
8. `StopPublisher.publish` with two local records and no `factory/stops.jsonl` on `origin/main`: it returns both, `origin/main` then holds the file with exactly their two lines in local order, and the commit's subject is `stops recorded`.
9. `StopPublisher.publish` when `origin/main`'s file already holds lines, rows of one parametrized test: the file holds the first of three local records and one line that does not validate: it returns the second and third, and the file holds its earlier two lines unchanged followed by the two new lines; the file's last line has no newline: a newline is added after it, before the new lines; the local log holds the second record twice: it is returned and written once.
10. `StopPublisher.publish` makes no commit (`origin/main`'s head unchanged) and returns `[]`, rows of one parametrized test: with `stop_records` `None`; with an empty record log; when `origin/main`'s file holds every local record.
11. `StopPublisher.publish` when `main` moved on the remote after the fetch (the human pushed): `PushFailed` is raised, `origin/main` holds no `stops recorded` commit, and a second call after a fetch publishes the records once.
12. `Tick.run` and the publish, rows of one parametrized test on the records of `origin/main`'s `factory/stops.jsonl` after each tick: a tick with a local record that `origin/main` does not hold publishes it; a tick whose fetch fails publishes nothing, and the next tick, whose fetch succeeds, publishes the `raised` and the `cleared` record of `fetch_failed`; a tick stopped by `disk_low` (a disk below `min_free_gb`) publishes nothing, and the next tick with room publishes its `raised` and `cleared` records.
13. `Tick.run` when the publish fails, rows of one parametrized test: the publish's push is refused (a hook of the remote refuses `main`); `origin/main` holds a folder `factory/stops.jsonl/`, so that the write raises `OSError`. In both the factory log holds a line starting `cannot publish the stop records: `, the local records stay, and the tick still evaluates and dispatches its event.
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
