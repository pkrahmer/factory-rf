---
stage: accept
pr: 168
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
2. intake: accepted
   - Interface: names concrete modules and signatures (`AcceptanceFacts.disk_now`/`disk_before`, `acceptance_facts(..., *, disk_now, disk_before)`, `AcceptanceService.facts`, the sentence for `claude/agents/acceptance-reviewer.md` check 7). The things it uses exist: `DiskRecorder.record`/`last` in `application/disk_records.py`, `disk_line` in `domain/disk.py`, `FakeDiskSpace` in `tests/disk_support.py`, and check 7 "The slow checks" in the agent file.
   - Criteria: each is testable by one test function. Every Interface behaviour has one: the two added lines and `none` (1), the unchanged three lines (2), the previous record (3), a `start` record counting as previous (4), the sentence (6). The failing side is covered by 2 (no `disk_now`, also with `disk_before` set) and 5 (no disk, records or settings: `disk_now is None`, nothing appended).
   - Demo: runnable with `uv run python -c`, and its Expect line names the two exact lines to compare.
   - Architecture: the domain gets pure fields and lines. The application service calls `DiskRecorder` through the boundaries. No new layer crossing, no new dependency.
   - Scope: within F0012's item 1.4 ("the disk record (S0016, S0017)") and decision 23. It adds no new feature and touches nothing under "Out of scope".
3. tester: red tests written for criteria 1 to 6. `make lint` is green. I skipped the type check, as this stage says to.
   - criterion 1: tests/domain/test_acceptance_facts_disk.py::test_facts_with_a_disk_now_give_the_two_disk_lines_after_the_three_of_today (parametrized: no previous record gives `none`, a previous record gives that record) and ::test_acceptance_facts_pass_the_disk_values_on
   - criterion 2: tests/domain/test_acceptance_facts_disk.py::test_facts_without_a_disk_now_give_the_three_lines_of_today (parametrized: `disk_before` None and set)
   - criterion 3: tests/application/test_acceptance_facts_disk.py::test_the_facts_record_the_disk_at_acceptance_and_name_the_record_before
   - criterion 4: tests/application/test_acceptance_facts_disk.py::test_a_start_record_is_the_previous_record (the `start` record is written through `DiskRecorder(...).record("start")`)
   - criterion 5: tests/application/test_acceptance_facts_disk.py::test_without_the_disk_the_records_or_the_settings_the_facts_carry_no_disk (parametrized: no disk, no disk records, no settings). The walk's existing prompt tests are unchanged.
   - criterion 6: tests/test_acceptance_reviewer_disk.py::test_the_slow_checks_of_the_acceptance_reviewer_end_with_the_disk_comparison (the line starting `7. **The slow checks.**` ends with the sentence). The tests in tests/test_claude_agent_texts.py are unchanged and cover the rest of that criterion.
   Files created: tests/domain/test_acceptance_facts_disk.py, tests/application/test_acceptance_facts_disk.py, tests/test_acceptance_reviewer_disk.py. The application file has its own fixtures: `settings`, `records` (a JsonLinesRecordLog in tmp_path) and `recorded`. `recorded` builds the walk, fetches through `walk.status() == "due"` and replaces disk, disk_records and settings on the boundaries.
   Nothing failed to import: every module exists. In the single `make test` run the tests fail as intended: `AcceptanceFacts` refuses the unknown `disk_now`/`disk_before` fields, `acceptance_facts` takes no such keywords, `facts` records no disk, and the agent file lacks the sentence.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/application/test_acceptance_facts_disk.py::test_the_facts_record_the_disk_at_acceptance_and_name_the_record_before
4. coder: the acceptance reviewer's facts now include the disk record. `make check` is green and `make duplicates` reports 0 new, 39 known, 0 gone. Commit 6c2ff0f.
   - `src/factory/domain/acceptance.py`: `AcceptanceFacts` has two new last fields, `disk_now` and `disk_before`, both defaulting to `None`. `lines()` returns the three lines of today. When `disk_now` is set it adds `Disk now: …` and `Disk at the previous record: …`, using the existing `NONE_TEXT` ("none") when `disk_before` is `None`. `acceptance_facts` takes the two values as keyword-only arguments and passes them on.
   - `src/factory/application/acceptance.py`: `AcceptanceService.facts` gets the two values from a private `_disk_lines()`. That method calls `DiskRecorder.last()` first and `record("acceptance")` after it, so the new record is not counted as its own previous one. When there is no disk, record log or settings, `record` returns `None` and both values are `None`.
   - `claude/agents/acceptance-reviewer.md`: check 7 ends with the sentence from the Interface. Nothing else in the file changed.
   - Main design decision: the lines are built in the application with the existing `disk_line`, so the domain only holds strings, as the Interface asks. I rejected passing `DiskRecord` objects into `AcceptanceFacts`: that would put formatting in the facts and depart from the Interface.
   - Refactor: I read the diff and found nothing to change, so there is no refactor commit.
   - Open: criterion 8 (operator guide and project guide) is the documenter's and I did not touch it.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
   - Criteria 1 and 2: `tests/domain/test_acceptance_facts_disk.py` checks the five lines with and without a `disk_before`, checks that `acceptance_facts` passes both values on, and checks that facts without `disk_now` give exactly the three lines of today. That last test is parametrized with `disk_before` both None and set, which covers the failing side.
   - Criteria 3 to 5: `tests/application/test_acceptance_facts_disk.py` checks the following:
     - the first call appends one `acceptance` record, and the second call names the first call's line as `disk_before`;
     - a `start` record counts as the previous record;
     - taking away the disk, the record log or the settings, one per parametrized row, gives `None`/`None` and appends nothing.
   - Criterion 6: `tests/test_acceptance_reviewer_disk.py` pins the sentence at the end of line 7. The agent diff changes that one line and nothing else.
   - Architecture: the domain gets only plain string fields and the formatting of the lines. `AcceptanceService._disk_lines` (`src/factory/application/acceptance.py`) reuses the existing `DiskRecorder.last`/`record` and `disk_line`, so no helper is copied. It reads the previous record before it writes the new one, which is correct. No new layer crossing and no new dependency.
   - Security: nothing relevant. No suppression markers.
   - Quality: the docstrings of `AcceptanceFacts` and `lines()` were updated. `NONE_TEXT` is reused. The comment explains why the read comes before the record. The coder's entry reports `make duplicates` as 0 new.
   - Hygiene: the coder's entry reports `make check` green. The log records the decision to pass strings rather than `DiskRecord` objects, and the rejected alternative. Criterion 8 still describes what the documenter must write.
6. documenter: wrote the two documents criterion 8 names; no findings.
   - `docs/operator-guide.md`: in "When a feature acceptance is due", a paragraph says the acceptance reviewer's prompt carries `Disk now` and `Disk at the previous record` (the latest earlier record of any occasion, or `none`). It also says the report compares them and that the lines are left out without the disk, the records or the settings.
   - `docs/project-guide.md`: in "The feature acceptance", "The reviewer's facts" names the `disk_now` and `disk_before` fields, the order of `last()` then `record("acceptance")`, the two added lines, the `acceptance_facts` keywords and the reviewer's comparison sentence.
   - Checked: `python -m factory.entry.check_documents` prints `documents ok`. I did not run `make check`, since I changed only docs. The diff matches the Interface and criteria, so there are no findings for the coder.
   - Cross-read: the rest of both guides is unaffected by this diff. I saw nothing stale.

   `make check`: check: green
   `make documents`: documents ok
7. demo: ran the one demo command from the repository root as written. No findings.

   Command 1 (`uv run python -c` builds `AcceptanceFacts` with a `disk_now` and prints `lines()[3:]`). It exited with 0:
   ```
   Disk now: disk acceptance: /work 1.0 GB free, 0.1 GB used
   Disk at the previous record: none
   ```
   Met its Expect line: the two lines match exactly. With no `disk_before`, the second line says `none`.

   Checked against the acceptance criteria: the output agrees with criterion 1. The two disk lines come at indices 3 and 4, after the three lines of today, and `none` is shown when there is no previous record. It contradicts no other criterion. Criteria 2 to 6 are about the service, the record log and the agent text, which this demo does not exercise. The tests the reviewer read cover them.
