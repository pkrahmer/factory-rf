# The stops and the refused tool calls reach the remote as records

## Description

A stop of the repository or the machine (`fetch_failed`, `disk_low`, `preflight_failed` and the rest) is today a line in `/state/factory.log` and an entry in the health status, both on the instance, where the status-map viewer cannot reach them. This story records each stop as two events, `raised` when a stop of its reason is first raised and `cleared` when it clears, each a JSON line in `records/stops.jsonl` in the state directory, and every tick, right after a successful fetch, pushes to `factory/stops.jsonl` on `main` the records `main` does not hold yet. A record holds the event, the scope, the reason, the time and the instance, never the stop's detail (the feature's decisions 1 to 3). A failed push or any other git error leaves the records in the state directory for the next tick and only writes a line to the factory log, so a stop is never lost because git was what failed, and a record is never pushed twice. The story also gives the run record room for what the runtime already reports: the cost record of a completed run gains `denials`, the number of tool calls the agent runtime reports as refused (the result's `permission_denials`, whatever refused them: a permission or deny rule of the runtime's settings or anything else the runtime reports there; under opencode, F0020 fills the same list), and `denied_paths`, the files those calls named (the feature's decision 8). Both are optional and left out of the sidecar line when unknown, so every line written before stays as it is; F0020 adds its spend-limit waits beside them in the same way (decision 9). A refusal the runtime does not report as a refused tool call, such as a write the kernel refuses, is only text in a tool's output inside the agent's transcript; it is not parsed and not counted. The health status, the factory log's stop lines and the stop written by `factory-run` for invalid settings stay as they are.

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

        Raises `GitError` and `PushFailed`.
        """
```

- Without `stop_records`, or with no record in it, `publish` returns `[]` and calls no git operation. When `origin/main`'s `STOP_RECORDS_FILE` (read with `git.show_file`; a missing file reads as empty) holds every local record (`parse_stop_records`, compared as whole records), it returns `[]` and makes no commit.
- Otherwise it stands on `main` at `origin/main` through `WorkItemRecorder.check_out`, writes the file as the text it read, with a newline added when that text is not empty and does not end in one, followed by `stop_records_text(missing)` (the missing records in local order, each once), and commits and pushes through `WorkItemRecorder.publish(MAIN_BRANCH, "stops recorded")`. Lines of the file that do not validate stay as they are.
- A refused push raises `PushFailed`; the local records stay, so the next call pushes them.

`factory.application.tick.Tick.run` (`application`): right after the fetch succeeded (and `fetch_failed` is cleared), before the pipeline definition is loaded, the tick calls `StopPublisher(boundaries).publish()`. A `GitError` or `PushFailed` from it writes `cannot publish the stop records: <error>` to the factory log, and the tick goes on as if it had published nothing. A tick that stops before the fetch succeeds (`disk_low`, `fetch_failed`) publishes nothing.

`factory.entry.wiring.build_boundaries` (`entry`): `stop_records=JsonLinesRecordLog(<state directory>/records/stops.jsonl, StopRecord)`.

`factory.domain.agent_runs.PermissionDenial` (`domain`): a new field `path: str | None = None`, the file the refused call named.

`factory.adapters.claude_runtime` (`adapters`): `_denials` sets `path` to the denial's `tool_input["file_path"]`, or else its `tool_input["notebook_path"]`, when `tool_input` is an object and that value is a string; otherwise `None`. `detail` stays as today.

`factory.domain.cost_records.CostRecord` (`domain`): two new last fields, after `instance`:

```python
denials: NonNegativeInt | None = None
denied_paths: list[str] | None = None
```

- A `started` record with either set is refused, like its other measures.

`factory.application.costs.CostRecorder.complete` (`application`): the completed record gets `denials=len(result.permission_denials)` and `denied_paths` the `path` of each denial that has one, each path once, in the order the runtime reported them; for a run that ended `died` or `time_limit` (no reply from the runtime) both stay `None`.

`factory.adapters.cost_records_jsonl` (`adapters`): the line leaves `denials` out when it is `None` and `denied_paths` out when it is `None`, as it leaves out a `None` `instance`; when set they are written after `instance`, and the reader reads them back.

Test modules (new): `tests/domain/test_stop_records.py`, `tests/application/test_stop_records_service.py`, `tests/application/test_stop_publisher.py`, `tests/application/test_tick_stop_records.py`, `tests/entry/test_wiring_stop_records.py`, `tests/adapters/test_claude_runtime_denial_paths.py`, `tests/domain/test_cost_record_denials.py`, `tests/application/test_costs_denials.py`, `tests/adapters/test_cost_records_jsonl_denials.py`. Earlier tests this story changes, under the feature's decision 14: `tests/adapters/test_claude_runtime_resume.py`, the expected `Write` denial gaining `path="x"`, and nothing else.

## Acceptance criteria

1. `StopRecord`, rows of one parametrized test: `scope="machine"` with `reason="disk_low"` and with `reason="preflight_failed"`, and `scope="repository"` with `reason="fetch_failed"`, are accepted; `scope="repository"` with `reason="disk_low"` and `scope="machine"` with `reason="fetch_failed"` are refused; `event="paused"` (through a variable typed `type[BaseModel]`) is refused.
2. `stop_records_text` of a `raised` record at 2026-10-18 10:00 UTC for `disk_low`, instance `self`, is exactly `{"event":"raised","scope":"machine","reason":"disk_low","at":"2026-10-18T10:00:00Z","instance":"self"}` and a newline; of no records, `""`.
3. `parse_stop_records`, rows of one parametrized test: the text of two records gives both in order; a blank line, a line that is not JSON and a line with an unknown reason between them are skipped; `""` gives `[]`.
4. `StopService.raise_stop`, rows of one parametrized test: a first `fetch_failed` appends one `raised` record with the stop's scope, reason and `at` and the settings' instance; a second raise of `fetch_failed` while it stands appends nothing more; a `disk_low` raised while `fetch_failed` stands appends a `raised` record for `disk_low`; boundaries without settings give `instance` `None`.
5. `StopService.clear_stop`, rows of one parametrized test: clearing a standing `fetch_failed` appends one `cleared` record with scope `repository` and the clock's time; clearing a standing `disk_low` gives scope `machine`; clearing a reason that does not stand appends nothing.
6. With `stop_records` `None`, a raise and a clear write the log lines and the health status as today and append nowhere.
7. A record log whose `append` raises `OSError`: `raise_stop` still writes the log line and the health status, and then raises that `OSError`; `clear_stop` removes the stop from the health status, writes `stop cleared <reason>`, and then raises it (rows of one parametrized test).
8. `StopPublisher.publish` with two local records and no `factory/stops.jsonl` on `origin/main`: it returns both, `origin/main` then holds the file with exactly their two lines in local order, and the commit's subject is `stops recorded`.
9. `StopPublisher.publish` when `origin/main`'s file holds the first of three local records and one line that does not validate: it returns the second and third, and the file on `origin/main` holds its earlier two lines unchanged followed by the two new lines.
10. `StopPublisher.publish` makes no commit (`origin/main`'s head unchanged) and returns `[]`, rows of one parametrized test: with `stop_records` `None`; with an empty record log; when `origin/main`'s file holds every local record.
11. `StopPublisher.publish` when `main` moved on the remote after the fetch (the human pushed): `PushFailed` is raised, `origin/main` holds no `stops recorded` commit, and a second call after a fetch publishes the records once.
12. `Tick.run` with a local record that `origin/main` does not hold: after the tick, `origin/main`'s `factory/stops.jsonl` holds it. A tick whose fetch fails publishes nothing, and the next tick, whose fetch succeeds, publishes the `raised` and the `cleared` record of `fetch_failed` (rows of one parametrized test on the file's records after each tick).
13. `Tick.run` when the publish's push is refused: the factory log holds a line starting `cannot publish the stop records: `, and the tick still evaluates and dispatches its event.
14. `build_boundaries` gives `stop_records` a record log at `<state directory>/records/stops.jsonl` that reads back a record it appended.
15. `_denials` of the `claude -p` runtime's reply, rows of one parametrized test: a `Write` with `{"file_path": "src/a.py"}` gives `path` `src/a.py`; a `NotebookEdit` with `{"notebook_path": "n.ipynb"}` gives `n.ipynb`; a call with both keys gives the `file_path`; a `Bash` with `{"command": "git push"}` gives `None`; `{"file_path": 3}` gives `None`; a `tool_input` that is a string gives `None`. `detail` is as today in every row.
16. `CostRecord`, rows of one parametrized test: a `completed` record with `denials=0` and with `denials=2` and `denied_paths=["src/a.py"]` is accepted; `denials=-1` is refused; a `started` record with `denials=0`, and one with `denied_paths=[]`, is refused.
17. `CostRecorder.complete`, rows of one parametrized test over the end reasons: a `completed`, a `budget` and a `no_result` run with the denials `Write src/a.py`, `Bash` (no path), `Edit src/a.py`, `Write docs/b.md` give `denials` 4 and `denied_paths` `["src/a.py", "docs/b.md"]`; a `completed` run without denials gives `denials` 0 and `denied_paths` `[]`; a `died` and a `time_limit` run give `None` for both.
18. The cost record writer, rows of one parametrized test: a record with both `None` is written as today, without `denials` and `denied_paths` keys; a record with `denials` 2 and `denied_paths` `["src/a.py"]` is written with `"denials":2,"denied_paths":["src/a.py"]` after `instance`; each line read back equals its record.
19. `make check` stays green.
20. docs:
    - `docs/operator-guide.md`, *The records*: `records/stops.jsonl` (its fields, when each event is written, that it is never cleared by the factory and is safe to delete only when `main` holds every line); *The stops*: that each stop's events reach `factory/stops.jsonl` on `main` after the next successful fetch, as commits `stops recorded`, without the detail, and the log line `cannot publish the stop records: <error>`; *The cost table* or *What a work item cost*: the sidecar's `denials` and `denied_paths`, and that only the tool calls the runtime reports as refused are in them, not a refusal that is only text in a tool's output.
    - `docs/project-guide.md`, *Stops, the clock and the factory log*: `StopRecord`, `StopPublisher` and the tick's call; *Cost records*: the two new fields and their `None`.
    - `docs/decisions.md`: a new entry, "The stops reach main as raised and cleared records", with the reason and the rejected places of the feature's decisions 1 to 3.

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

```bash
uv run -q python -c '
import json
from datetime import UTC, datetime
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordWriter
from factory.domain.cost_records import CostRecord

fields = dict(
    run="a" * 32, work_item="F0001-S0001", stage="doing", role="coder", attempt=0,
    started_at=datetime(2026, 10, 18, 10, 0, tzinfo=UTC),
)
started = CostRecord(status="started", **fields)
done = CostRecord(
    status="completed", duration_seconds=1.0, end_reason="completed",
    denials=2, denied_paths=["src/a.py"], **fields,
)
for line in JsonLinesCostRecordWriter().render([started, done]).splitlines():
    record = json.loads(line)
    print(record.get("denials", "absent"), record.get("denied_paths", "absent"))
'
```

Expect: two lines, `absent absent` and `2 ['src/a.py']`.

## Journal
