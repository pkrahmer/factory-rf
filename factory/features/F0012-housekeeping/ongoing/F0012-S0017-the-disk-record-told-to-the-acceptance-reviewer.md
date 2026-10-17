---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The disk record told to the acceptance reviewer

## Assignment (as of log entry 1)

The second half of the human's disk watch: at each feature acceptance the disk is recorded, and the acceptance reviewer compares it with the last record and reports a growth that the change does not explain. The acceptance reviewer cannot read the state directory (it is the factory user's alone), so the factory tells it in its prompt. This story makes the acceptance reviewer's facts take a disk record of occasion `acceptance` (F0012-S0016's recorder) when its prompt is composed, and add two lines after the cost line: the record of now and the latest record before it, whatever its occasion (the instance's start or an earlier acceptance), or `none` when there is none, as the plan's watch says ("compares them with the last record"). A rerun of the acceptance stage records again; the previous record is then the rerun's own earlier one, which is still a comparison the reviewer can read. The shipped acceptance reviewer gets one sentence in its slow checks to make the comparison. Boundaries without the disk, the records or the settings (every test written before this story) give the facts their three lines as today, so no earlier test changes.

## Interface

`src/factory/domain/acceptance.py`, `AcceptanceFacts` gains two last fields:

```python
    disk_now: str | None = None
    disk_before: str | None = None
```

`lines()` gives the three lines as today, then, when `disk_now` is not `None`, `Disk now: <disk_now>` and `Disk at the previous record: <disk_before, or none>`. `acceptance_facts(files, cost_line, *, disk_now=None, disk_before=None)` passes them on.

`src/factory/application/acceptance.py`, `AcceptanceService.facts(feature)`: before it builds the facts, `previous = DiskRecorder(self._boundaries).last()`, the latest record of any occasion, then `now = DiskRecorder(self._boundaries).record("acceptance")`; `disk_now` is `disk_line(now)` and `disk_before` is `disk_line(previous)` or `None`; when `now` is `None` (no disk, records or settings), both are `None`. Nothing else in `facts` changes; `TaskComposer` still composes the acceptance prompt from it.

`claude/agents/acceptance-reviewer.md`: the check *The slow checks* (7.) ends with the sentence `When your prompt has a Disk now line, compare it with the Disk at the previous record line, whose occasion it names, and name any growth that the feature's changes do not explain.` Nothing else in the file changes.

Tests: `tests/domain/test_acceptance_facts_disk.py` (criteria 1 and 2); `tests/application/test_acceptance_facts_disk.py` (criteria 3 to 5), with the `walk` fixture to push the feature `F0002-todo` and its archived stories, then `boundaries.git.fetch()` and an `AcceptanceService` built on `dataclasses.replace(boundaries, disk=..., disk_records=..., settings=...)` and `walk.definition`, the disk a `FakeDiskSpace` of `tests/disk_support.py` (F0012-S0010) and the records a `JsonLinesRecordLog` in `tmp_path`; `tests/test_acceptance_reviewer_disk.py` (criterion 6, with `tests/shipped_agents.py`). No existing test changes.

## Acceptance criteria

1. Facts with `disk_now="disk acceptance: /work 1.0 GB free, 0.1 GB used"` and `disk_before=None` give five lines: the three of today, `Disk now: disk acceptance: /work 1.0 GB free, 0.1 GB used` and `Disk at the previous record: none`; with a `disk_before`, the last line names it; `acceptance_facts(files, cost_line, disk_now=..., disk_before=...)` gives facts holding both values.
2. Facts without `disk_now` give exactly the three lines of today, also when `disk_before` is set.
3. `AcceptanceService.facts` on boundaries with the disk, an empty record log and the settings appends one `acceptance` record and gives `disk_now` equal to its line and `disk_before` `None`; a second call gives `disk_before` equal to the first call's line.
4. A `start` record is a previous record too: with only a `start` record in the log, `disk_before` is that record's line, which begins with `disk start: `.
5. On boundaries without the disk, the records or the settings, the facts have `disk_now is None` and nothing is appended (the walk's existing prompt tests still pass unchanged).
6. The body of the shipped `acceptance-reviewer` agent holds the sentence of the Interface in its check *The slow checks*, and every test of `tests/test_claude_agent_texts.py` still passes.
7. `make check` stays green.
8. docs: the operator guide's section *When a feature acceptance is due* says that the acceptance reviewer's prompt carries the disk record of now and the latest one before it and that the report compares them; the project guide's section *The feature acceptance* names the two fields and lines. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from factory.domain.acceptance import AcceptanceFacts
facts = AcceptanceFacts(archived=['F0001-S0001'], next_story='F0001-S0002', cost_line='1 runs', disk_now='disk acceptance: /work 1.0 GB free, 0.1 GB used')
print('\n'.join(facts.lines()[3:]))
"
```
Expect: two lines: `Disk now: disk acceptance: /work 1.0 GB free, 0.1 GB used` and `Disk at the previous record: none`.

## Log (append only)

1. 2026-10-17 human: created.
