---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 385
comments_read: [6309137603]
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-21T05:55:04.938270Z'
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
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T02:08:35.543754Z'
  stage: intake
  run: 1eb297bcb69044778803ba136459af33
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T02:08:56.158350Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T02:15:01.562129Z'
  stage: tests
  run: 20a1addaee2848efbeab3071612dfcbb
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T02:15:22.435919Z'
  stage: doing
- number: 7
  speaker: coder
  kind: question
  at: '2026-10-21T02:17:32.778862Z'
  stage: doing
  run: dbddf8ce4ce94c14bd61f5efc9f8d801
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-10-21T05:54:46.917249Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-21T05:55:04.938270Z'
  stage: doing
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
3. intake: accepted
   - Interface: concrete. It names `src/factory/application/boundaries.py` with the six fields and their types. It lists each removed branch by module, class and method (`CostRecorder.begin`, `DiskRecorder.record` and `last`, `AcceptanceService._disk_lines`, `KnownResults.run` and `_key`, `PatientRuns`, `StopService._record`, `StopPublisher.publish`, `TaskComposer._os_user`, `Tick._check_disk`). It gives the exact fixture and `_assemble` constructions.
   - Criteria: criterion 1 is one parametrized test, one row per field, with the failing side (`TypeError`) and the passing side. Criterion 2 is a single test with concrete values. Criteria 3 and 4 name the existing tests that pin the other behaviours. Criterion 4's "no `None` comparison" part is checked by grep only in the smoke test. That grep covers seven modules and not `acceptance.py`; this is a small gap, but the removed `_disk_lines` branch is covered by the acceptance tests of decision 11. The `last()` rule (`None` only without a record) is kept by existing disk-recorder tests. Criterion 5 is `make check`. Criterion 6 is the docs.
   - Smoke test: the Python snippet and the greps are runnable. Each `Expect:` line gives a checkable value (`[]` and `0`, then `0`), with the before-values stated. No pytest command is used, so the `-q` rule does not apply.
   - Architecture: `Boundaries` stays in `factory.application`. The collaborators are existing interfaces (`DiskSpace`, `RecordLog`, `Waiter`). The test fakes and real `JsonLinesRecordLog` are used under `tmp_path`, as `CLAUDE.md` allows. `build_boundaries` and the layers are untouched.
   - Scope: the story is within the feature's scope, which lists the same S0006 files. The earlier-test changes rest on the human's leave in decision 11, which is granted and names each of the 17 tests. `agent_home` stays optional, as decision 10 says. The `CLAUDE.md` example change is the human's separate change after the merge, not this story's.
4. factory: started tests as self.
5. tester: Tests written. I made the fixture changes and the seventeen earlier test changes under the human's leave (the feature's decision 11), and added a new module for criteria 1 and 2.

   Criteria → tests:
   - criterion 1: tests/application/test_boundaries_required.py::test_boundaries_without_one_of_the_collaborators_are_refused. It has one row per field (settings, disk, disk_records, stop_records, waiter, result_records). Without that field, `Boundaries` called through `Callable[..., Boundaries]` must raise `TypeError`. With all fields it must build a `Boundaries` equal to the fixture's.
   - criterion 2: tests/application/test_boundaries_required.py::test_the_fixture_boundaries_carry_every_feature
   - criterion 3: covered by the existing tests/entry/test_wiring_boundaries.py, test_wiring_known_results.py, test_wiring_record_logs.py, test_wiring_stop_records.py and test_wiring_waiter.py. In the first, `test_the_built_boundaries_read_the_disk_and_boundaries_without_one_have_none` became `test_the_built_boundaries_read_the_disk`, without `others` and its last assertion. I dropped the `fields` and `Boundaries` imports that nothing used any more.
   - criterion 4: covered by the seventeen tests of decision 11 as changed, the other tests of their modules, and test_tick.py, test_stage_known_results.py, test_stage_provider_limit.py, test_tick_stop_records.py and test_sealed_runs_runner.py. The grep for `None` comparisons is in the smoke test, not in pytest.
   - criteria 5 and 6: `make check` and the docs, so no tests.

   Earlier test files changed under decision 11:
   - tests/conftest.py: the `boundaries` fixture now sets all six fields exactly as the Interface gives them, and its docstring names them.
   - tests/proof_support.py: `_assemble` sets the same six under `root` and `state`, with `instance=INSTANCE`.
   - test_boundaries_settings.py: the test is renamed `test_boundaries_hold_the_settings_they_are_given`, and the `is None` assertion is gone.
   - test_costs.py: the expected `CostRecord` now has `instance="factory-1"`.
   - test_patient_runs.py:
     - the without-a-waiter test is removed;
     - `test_with_the_default_settings_the_default_limit_applies` now uses `InstanceSettings(repository_url="/srv/project.git", instance="factory-1")`, rows unchanged.
   - test_preflight.py: `assert ready.settings is None` became `assert ready.settings != settings`, where `settings` is the one the test gives.
   - test_stage_run_acceptance.py and test_task_acceptance.py: the expected facts are the later `facts()` with `disk_before=None`. The line slices grew by the two disk lines. A new assertion checks those two lines: `{tmp_path}` and `{tmp_path}/state`, each "1000.0 GB free, 0.0 GB used", and "Disk at the previous record: none".
   - test_stop_records_service.py: the without-stop-records test is removed.
   - test_acceptance_facts_disk.py: the without-disk test is removed, along with the `Callable` import.
   - test_disk_recorder.py: the record-nothing test is removed. In `test_last_gives_the_latest_record_whatever_its_occasion`, the `no-record-log` row and `with_log` are gone, and `Callable` is no longer imported.
   - test_known_results.py: the without-records test is removed, and `with_records` is gone from `_rig`.
   - test_stop_publisher.py: the `no-record-log` row and `with_records` are gone.
   - test_tick_disk.py: the without-disk-or-settings test is removed, and `_tick` no longer takes `| None`.
   - test_cost_image.py: the `no-settings` row is gone, and the parameter is typed `InstanceSettings`.
   - test_task_os_user.py: the `no-settings` row and `NO_SETTINGS` are gone.

   Files created: tests/application/test_boundaries_required.py.

   `make test` failed for the right reason: only the six rows of the criterion-1 test failed ("DID NOT RAISE TypeError"), because the fields still have defaults. I read the list of failures from .reports/junit.xml and did not run the tests again. Every other test passes with the new fixture, the criterion-2 test included, since it checks the fixture. Every module was imported; none was missing. `make lint` is green.

   Notes:
   - The Interface leaves the list of the seventeen tests to "the feature's decision 11", so I read that one entry of feature.md and nothing else of it.
   - After the removed test, the class `CountingGit` in test_known_results.py has no user. The leave names only imports, parameters and `| None`, so I left the class in place. The human can decide whether it goes.
   - I kept `assert ... is not None` lines in helpers that still type-check (`_limit` in test_patient_runs.py, `test_a_start_record_is_the_previous_record`), because decision 11 does not name them.
   - The type check was not run, as this stage says.

   `lint`: lint: green (0.6 s)
   `test`: FAILED tests/application/test_boundaries_required.py::test_boundaries_without_one_of_the_collaborators_are_refused[result_records] - Failed: DID NOT RAISE TypeError
6. factory: started doing as self.
7. coder: Question: two earlier tests outside decision 11 still pass `settings=None` to `Boundaries`. They contradict the Interface, and I may not edit them (R9).

   Where I stopped: the source change is complete and left in the working tree. In `src/factory/application/`:
   - `boundaries.py`: the six fields are required, and the "Last and optional" comment is gone.
   - `costs.py`, `disk_records.py` (`record` now returns `DiskRecord` and its docstring lost the `None` sentence; `last` is `None` only without a record), `acceptance.py` (`_disk_lines`), `known_results.py`, `provider_limits.py`, `stops.py`, `task.py`, `tick.py`: every `is None` branch on the six fields is gone, and the unused `ProviderLimit` import in `provider_limits.py` is removed.

   A grep over `src/factory` finds no `None` comparison on the six fields any more. `make lint` is green. `make check` is red, only because of these two test rows:

   1. `tests/application/test_cost_instance.py::test_a_cost_record_names_the_instance_of_the_settings_and_keeps_it_when_completed`, row `no-settings` (`(None, None)`), with the parameter typed `InstanceSettings | None`.
      - mypy: `test_cost_instance.py:30: error: Argument "settings" to "replace" of "Boundaries" has incompatible type "InstanceSettings | None"; expected "InstanceSettings"  [arg-type]`
      - pytest: `FAILED ...[no-settings] - AttributeError: 'NoneType' object has no attribute ...`
   2. `tests/application/test_stop_records_service.py::test_a_raise_appends_a_raised_record_when_no_stop_of_its_reason_stands`, row `no-settings` (`with_settings=False`, which expects `instance=None`). Its line 82 is `settings = local_settings if with_settings else None`.
      - mypy: `test_stop_records_service.py:83: error: Argument "settings" to "replace" of "Boundaries" has incompatible type "InstanceSettings | None"; expected "InstanceSettings"  [arg-type]`
      - pytest: `FAILED ...[no-settings] - AttributeError: 'NoneType' object has no attribute 'inst...`

   Both rows test exactly the branches the Interface removes: "no settings gives instance `None`". The tester's list of decision 11's seventeen tests does not include them, so I take it the human's leave does not cover them.

   Options:
   - (a) Give leave to remove both `no-settings` rows. That also means dropping `with_settings` and `local_settings if ... else None` in the second test (every remaining row passes `True`), and typing the first test's parameters `InstanceSettings` and `str`. **This is my choice**: it is the same kind of change decision 11 made in `test_cost_image.py` and `test_task_os_user.py`.
   - (b) Keep the rows and keep `settings` optional. That contradicts the feature's decision 8 and the Interface.

   With (a), I would end the next round with `tests` and name these two row removals for the tester. No code change is needed after that.

   Main design choice so far: in `DiskRecorder.record` I read `disk_records` and `settings` straight from `self._boundaries` instead of keeping local names. I rejected the locals because they only existed to narrow the type for the `None` check.

   Seen but not touched: `CountingGit` in `tests/application/test_known_results.py` has no user since the tester removed a test; the tester raised this already. The refactor step will run once `make check` can be green.
8. 2026-10-21 human: The human's answer (2026-10-21): (a), granted. The tester removes the `no-settings` row of `tests/application/test_cost_instance.py::test_a_cost_record_names_the_instance_of_the_settings_and_keeps_it_when_completed` (its parameters typed `InstanceSettings` and `str`) and the `no-settings` row of `tests/application/test_stop_records_service.py::test_a_raise_appends_a_raised_record_when_no_stop_of_its_reason_stands` (with `with_settings` and `local_settings if ... else None`). Each test keeps its name and its other rows. Recorded in the feature's decision 11.
9. factory: started doing as self.
