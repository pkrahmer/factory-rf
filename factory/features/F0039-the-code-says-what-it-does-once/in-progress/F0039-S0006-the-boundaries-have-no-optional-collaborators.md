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
  started_at: '2026-10-21T02:08:18.064279Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T02:08:18.058735Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T02:08:18.064279Z'
  stage: intake
---

# The boundaries have no optional collaborators

## Description

Six fields of `Boundaries` (`src/factory/application/boundaries.py`), `settings`, `disk`, `disk_records`, `stop_records`, `waiter` and `result_records`, are `| None = None` under the comment "Last and optional, so that every construction written before them stays valid". The constructions written before them are gone: `build_boundaries` sets all six, and the `boundaries` fixture of `tests/conftest.py` and `tests/proof_support.py` set none. So the whole suite runs with the low-disk stop, the disk records, the stop records, the provider-limit waits and the known results switched off, and a second entry point or a change to `build_boundaries` that drops a field type-checks and loses a safety feature silently (the review's A3). The human chose to make them required (the feature's decision 8). This story makes the six fields required, removes every `is None` branch on them in `factory.application` (thirteen in seven modules, and the one in `AcceptanceService._disk_lines` that only follows from `DiskRecorder.record` returning `None`), and has the two test constructions set all six with real collaborators under `tmp_path`. The tester first changes the fixture and the earlier tests that switch a feature off with `None`, under the human's leave (the feature's decision 11). Unchanged: what each service does when the field is set, `build_boundaries`, the keyword-only and frozen rules, and every field not named here (a later optional field with a meaning of its own for `None`, such as F0040's `agent_home`, stays optional).

## Interface

`src/factory/application/boundaries.py` (`application`):

```python
@dataclass(frozen=True, kw_only=True)
class Boundaries:
    ...
    checkout: Path
    settings: InstanceSettings
    disk: DiskSpace
    disk_records: RecordLog[DiskRecord]
    stop_records: RecordLog[StopRecord]
    waiter: Waiter
    result_records: RecordLog[ResultRecord]
```

- The six fields have no default and no `None` in their type; the comment "Last and optional, ..." goes. `Boundaries(...)` without any one of them raises `TypeError`.

The branches that go (`application`), each service then using the field as it does today when the field is set:

- `factory.application.costs`, `CostRecorder.begin`: `image` and `instance` are `settings.image` and `settings.instance` (two branches).
- `factory.application.disk_records`, `DiskRecorder`: `record(self, occasion: DiskOccasion) -> DiskRecord` always measures, logs and appends (one branch over three fields), and its docstring loses the sentence on `None`; `last()` stays `-> DiskRecord | None` and is `None` only without a record (one branch).
- `factory.application.acceptance`, `AcceptanceService._disk_lines`: the `if now is None` branch goes, since `record` always returns a record.
- `factory.application.known_results`, `KnownResults.run` always builds a key and reads the records (one branch); `_key`'s `image` is `settings.image` (one branch).
- `factory.application.provider_limits`, `PatientRuns`: the limit is `settings.provider_limit` (one branch), and the loop waits whenever a run ends `provider_limit` (the `waiter is not None` condition goes; one branch); its `__init__` docstring loses "if they have one".
- `factory.application.stops`: `StopService._record` always appends, with `instance=settings.instance` (two branches); `StopPublisher.publish` reads `stop_records` (one branch).
- `factory.application.task`, `TaskComposer._os_user`: `settings.agent_user` (one branch).
- `factory.application.tick`, `Tick._check_disk`: always checks (one branch).
- No other module under `src/factory/` changes; `build_boundaries` already sets all six.

Tests (the tester changes them first, under the feature's decision 11; each changed test keeps every line not named here):

- `tests/conftest.py`, the `boundaries` fixture: it also sets `settings=InstanceSettings(repository_url="/srv/project.git", instance="factory-1", checkout=tmp_path / CHECKOUT, state_directory=state, agent_home=agent_home)`, `disk=FakeDiskSpace(free={tmp_path: 10**12, state: 10**12}, used={tmp_path: 1, state: 1})` (`disk_support`), `disk_records=JsonLinesRecordLog(state / "records" / "disk.jsonl", DiskRecord)`, `stop_records=JsonLinesRecordLog(state / "records" / "stops.jsonl", StopRecord)` (the path of the `records` fixture), `waiter=ManualWaiter(clock)` and `result_records=JsonLinesRecordLog(state / "records" / "known-results.jsonl", ResultRecord)`; its docstring names them.
- `tests/proof_support.py`, `_assemble`: the same six, under its `root` and `state`, with `instance=INSTANCE`.
- The seventeen earlier tests the feature's decision 11 names, in fifteen modules: seven that the fixture's features change (an expected record or text gains what the fixture's settings or disk give, or a check of `None` goes) and ten that switch a feature off with `None` (removed, a row removed, or changed as it says). Each module drops the imports and the `| None` of its own helpers that nothing needs any more.
- `tests/application/test_boundaries_required.py` (new): criteria 1 and 2.

## Acceptance criteria

1. Each of the six fields is required (rows of one parametrized test, one per field): `Boundaries(**others)`, `others` the fields of the `boundaries` fixture without that one, called through a variable typed `Callable[..., Boundaries]`, raises `TypeError`; with all fields given it builds a `Boundaries` equal to the fixture's.
2. The fixture's boundaries carry every feature: `boundaries.settings.instance` is `factory-1`, `boundaries.settings.state_directory` is `tmp_path / "state"`, `isinstance(boundaries.waiter, ManualWaiter)`, and `DiskRecorder(boundaries).record("start")` returns a `DiskRecord` whose folders' `path`s are `str(tmp_path)` and `str(tmp_path / "state")`, each with `free_bytes` `10**12` and `used_bytes` `1`, and `boundaries.disk_records.read()` is that one record.
3. The production wiring still sets all six: `tests/entry/test_wiring_boundaries.py`, `test_wiring_known_results.py`, `test_wiring_record_logs.py`, `test_wiring_stop_records.py` and `test_wiring_waiter.py` pass, the first with its test changed under decision 11.
4. Every service does with the field what it did when the field was set: the seventeen tests of decision 11 as changed, the other tests of their modules, and `tests/application/test_tick.py`, `test_stage_known_results.py`, `test_stage_provider_limit.py`, `test_tick_stop_records.py` and `test_sealed_runs_runner.py`, pass, and no module under `src/factory/application/` compares one of the six fields, or a local name read from one, with `None` (`grep` of the smoke test).
5. `make check` stays green.
6. docs: `docs/project-guide/watching.md`, *Boundaries*: the six fields are required and `build_boundaries` sets them; the sentences that call them optional or `None` by default go, and "a `Boundaries` built by hand holds `None`" goes; the paragraph on the `boundaries` fixture names the six as the fixture sets them (the fake disk with ample room, the three record logs under `<tmp_path>/state/records/`, the manual waiter on the `clock` fixture, the settings) and says that a test that needs a feature off replaces its collaborator with one of its own, never with `None`. *The tick*, step 0: "With `boundaries.disk` or `boundaries.settings` `None` it does nothing." goes. `docs/project-guide/stages.md` (`PatientRuns`, `TaskComposer`), `docs/project-guide/processes-and-checks.md` (the known results) and `docs/project-guide/agents.md` (`os_user`): every clause on what happens without the settings, the waiter or the records goes. `docs/decisions.md`, the entry *The services read the instance's settings from `Boundaries.settings`*: one line, dated with the story, that the field and the five others became required once `build_boundaries` set them all, because an optional collaborator let a construction drop a stop silently (the feature's decision 8). `README.md` and `docs/operator-guide.md`: none, nothing an operator or a newcomer sees changes.

## Smoke test

```bash
uv run python - <<'PY'
import dataclasses
from factory.application.boundaries import Boundaries
fields = {f.name: f for f in dataclasses.fields(Boundaries)}
print([n for n in ("settings", "disk", "disk_records", "stop_records", "waiter", "result_records") if fields[n].default is not dataclasses.MISSING])
PY
grep -rnE '\b(settings|disk|records|waiter)\b is (not )?None|if (disk|records|settings) is None' src/factory/application/costs.py src/factory/application/disk_records.py src/factory/application/known_results.py src/factory/application/provider_limits.py src/factory/application/stops.py src/factory/application/task.py src/factory/application/tick.py | wc -l
```
Expect: two lines, `[]` and `0` (before the story, `['settings', 'disk', 'disk_records', 'stop_records', 'waiter', 'result_records']` and `13`)

```bash
grep -c 'holds `None`' docs/project-guide/watching.md
```
Expect: one line, `0` (before the story, `1`)

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
