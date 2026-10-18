---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 235
comments_read: []
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-18T22:04:19.606918Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T21:47:49.397840Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T21:47:49.404190Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T21:48:05.945446Z'
  stage: intake
  run: 7589b9ea023b4c5a82537dfe3cb5c7b5
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-18T21:48:26.171210Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-18T21:53:39.863063Z'
  stage: tests
  run: e712012ae52341c1a14bfaf0619ff2d2
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-18T21:53:59.940064Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-18T21:58:48.441392Z'
  stage: doing
  run: edbfd0d70b2a42538d5d911df4eb91f2
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-18T21:59:08.759637Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-18T22:00:19.888400Z'
  stage: review
  run: 49ffbc9e4efb4d90bd5b8c4ecbb0a79a
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-18T22:00:39.958843Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-18T22:00:59.871617Z'
  stage: doing
  run: f5dcf02c01a345fe88ea6820e8113a52
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-18T22:01:19.948537Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-18T22:03:59.269344Z'
  stage: tests
  run: dd7576238bcc4c4d97efa53225f6a120
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-18T22:04:19.606918Z'
  stage: doing
---

# The journal records why a work item waited or stalled

## Description

Today a work item's front matter says that a question was asked or that a stage stalled, but not why: the cause is only in the entry's text, which no code reads. This story puts the cause into the record. A journal record of kind `question` gains an optional `blocked`, the block the question opened (`question`, `attempts_cap`, `round_cap`, `crash_cap` or `send_back`), and a record of kind `stall` an optional `reason`, the stall reason the factory already decides (`died`, `time_limit`, `budget`, `no_result`, `decision_not_allowed`, `left_branch`, `form_invalid`, `check_red`, `merge_conflict`, `nested_repository`). Every place that records a blocking question or a stall writes the field; records without it, every record written before this story included, stay valid and are written back without it. `crash` and `expiry` records get no reason (the feature's decision 4). What is computed from these records is S0002's: the human's waits, the line under the cost table and the line of the acceptance's facts. The agent texts that use that line are S0005's; the stop records are S0003's and the run record's refusals S0004's.

## Interface

`factory.domain.journal` (`domain`): the two cause types move here, so that the record can name them without a circular import. `factory.domain.work_item` keeps `Blocked` and `factory.domain.decisions` keeps `StallReason` by assignment (`Blocked = journal.Blocked`, `StallReason = journal.StallReason`), so every module and test that imports them from there stays valid under `mypy --strict`.

```python
Blocked = Literal["question", "attempts_cap", "round_cap", "crash_cap", "send_back"]
StallReason = Literal[
    "died", "time_limit", "budget", "no_result", "decision_not_allowed",
    "left_branch", "form_invalid", "check_red", "merge_conflict", "nested_repository",
]


class JournalRecord(BaseModel):
    number: PositiveInt
    speaker: Speaker
    kind: JournalKind
    at: UtcDatetime | None = None
    stage: Name | None = None
    run: RunId | None = None
    blocked: Blocked | None = None
    reason: StallReason | None = None


def append_entry(
    document: WorkItemDocument,
    entry: NewEntry,
    *,
    at: datetime | None = None,
    run: RunId | None = None,
    blocked: Blocked | None = None,
    reason: StallReason | None = None,
) -> WorkItemDocument: ...
```

- `blocked` is allowed only on a record of kind `question`, `reason` only on a record of kind `stall`; either on any other kind raises a `ValueError` (Pydantic's validation error). A value outside its type is refused.
- `append_entry` puts `blocked` and `reason` into the new record as given, with or without `at`; the rules above apply to the record it builds.
- The work item writer writes the fields only when they are set: `model_dump(exclude_none=True)` already leaves a `None` out, as for `run`.

The writers of the fields (`application`), each one argument more to its existing `append_entry` call:

- `StageFinisher.finish` (`factory.application.stage`): the agent's entry gets `blocked=move.blocked` when its kind is `question` (rule 2); the factory's question of the move gets `blocked=move.blocked` (rule 1: `question`; rule 4: `round_cap`). A `result` entry gets none.
- `StallService._stalled` (`factory.application.stalls`): the stall entry gets `reason=<the stall's reason>`.
- `AskHandler._record_attempts_cap_question` (`factory.application.handlers.questions`): `blocked="attempts_cap"`.
- `RecoveryHandler._crash_recorded` (`factory.application.recovery`): the crash-cap question gets `blocked="crash_cap"`, after a crash and after an expiry; the `crash` and `expiry` records get no reason.
- `ClosedHandler._record_decision` (`factory.application.handlers.closed`): the send-back question gets `blocked="send_back"`.

Test modules (new): `tests/domain/test_journal_causes.py`, `tests/adapters/test_journal_causes_file.py`, `tests/application/test_stage_finish_causes.py`, `tests/application/test_stall_reasons_recorded.py`, `tests/application/test_question_causes_recorded.py`. Earlier tests this story changes, under the feature's decision 13: `tests/application/handlers/test_questions.py`, `tests/application/test_stalls.py`, `tests/application/test_recovery_cap.py`, `tests/application/test_recovery_expiry.py`, each only by adding the new field to an expected value.

## Acceptance criteria

1. `JournalRecord` with `blocked` and `reason`, rows of one parametrized test: kind `question` with `blocked="crash_cap"` is accepted; kind `stall` with `reason="time_limit"` is accepted; kind `question` and kind `stall` with neither field are accepted; `blocked="question"` on kind `result`, `comment` and `stall` is refused; `reason="check_red"` on kind `crash`, `expiry` and `question` is refused (a `ValueError`).
2. Through a variable typed `type[BaseModel]`: `blocked="maybe"` on a `question` record and `reason="slow"` on a `stall` record are refused, and every value of `Blocked` and of `StallReason` is accepted on its kind (rows of one parametrized test).
3. `Blocked` imported from `factory.domain.work_item` and `StallReason` imported from `factory.domain.decisions` are the same types as those of `factory.domain.journal` (`typing.get_args` equal).
4. `append_entry` with `blocked="round_cap"` on a `question` entry, and with `reason="merge_conflict"` on a `stall` entry, each with and without `at`: the new record carries the value; without `at` it carries no `stage` and no `run`, as today (rows of one parametrized test). `append_entry` with `blocked` on a `result` entry raises `ValueError`.
5. A work item whose journal holds a `question` record with `blocked: crash_cap` and a `stall` record with `reason: time_limit`, written by the work item writer and read back, equals the document written, and its front matter holds `blocked: crash_cap` and `reason: time_limit` in those records. A record without them is written without a `blocked:` or `reason:` key (rows of one parametrized test).
6. `StageFinisher.finish`, rows of one parametrized test on the work item's last two records: an agent deciding `question` (rule 2) leaves its own `question` record with `blocked: question`; a forward decision on a work item whose form findings were already there at the stage start (rule 1) leaves the agent's `result` record without `blocked` and the factory's `question` record with `blocked: question`; a rework past the round cap (rule 4) leaves the factory's `question` record with `blocked: round_cap`; a forward move (rule 6) leaves a `result` record without `blocked`.
7. `StallService.stall` with each value of `StallReason` (rows of one parametrized test, every value one row) leaves a last record of kind `stall` whose `reason` is that value.
8. A stall at the doing stage's red check (rule 5) and a stall by a merge conflict at the stage start leave a `stall` record with `reason: check_red` and `reason: merge_conflict` (rows of one parametrized test).
9. The ask handler at the attempts cap records the question with `blocked: attempts_cap`.
10. The recovery at the crash cap, after a `crash` and after an `expiry` (rows of one parametrized test), records the question with `blocked: crash_cap`, and the `crash` or `expiry` record before it has no `reason`.
11. A close at the approval that sends the story back with a question (no reason given) records the question with `blocked: send_back`.
12. `make check` stays green.
13. docs:
    - `docs/project-guide.md`, *The journal's data*: the rows `blocked` (on a `question` record: the block it opened, one of `Blocked`'s values) and `reason` (on a `stall` record: the stall reason), both optional and left out when unset; that `crash` and `expiry` records carry no reason, and why (the feature's decision 4).
    - `docs/decisions.md`: a new entry, "A question records the block it opened, a stall its reason", with the reason (the status map reads the front matter and never parses prose) and the rejected alternatives: parsing the entry texts, and a reason on crash records.

## Smoke test

```bash
uv run -q python -c '
from factory.domain.journal import JournalRecord

for kind, field, value in (
    ("stall", "reason", "time_limit"),
    ("crash", "reason", "time_limit"),
    ("question", "blocked", "send_back"),
    ("result", "blocked", "send_back"),
):
    try:
        JournalRecord(number=1, speaker="factory", kind=kind, **{field: value})
        print(kind, field, "accepted")
    except ValueError:
        print(kind, field, "refused")
'
```

Expect: four lines, `stall reason accepted`, `crash reason refused`, `question blocked accepted`, `result blocked refused`.

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: names concrete modules and signatures (`factory.domain.journal` types, `JournalRecord` fields, `append_entry` parameters) and the five application writers, each with its module and method. The aliases kept by assignment in `work_item` and `decisions` are stated. The validation rule (`blocked` only on `question`, `reason` only on `stall`, otherwise `ValueError`) and the writer behaviour (omit when `None`) are explicit.
   - Criteria: each is testable by one parametrized test with no open decision. Both sides of each rule are covered. Criterion 1 covers `blocked` and `reason` accepted on their kind and refused on others. Criterion 2 covers values outside the types and every value of both types. Criterion 4 covers `append_entry` with and without `at`, and `blocked` on a `result` entry. Criterion 5 covers the round trip and omission when unset. Criteria 6 to 11 cover every writer, including the `result` record having no `blocked` and the crash and expiry records having no `reason`. Criterion 3 covers the alias identity. Earlier tests changed are named and match the feature's decision 13.
   - Smoke test: the command runs as written with `uv run -q python -c`. Its `Expect:` line gives four exact output lines that can be compared with the output.
   - Architecture: the causes move into `domain` and are re-exported upward. The writers sit in `application`, in the modules that already make the `append_entry` calls. No layer is crossed and no new dependency is added. The writer in `adapters` needs no change because it already uses `exclude_none`.
   - Scope: within the feature's S0001 scope (the cause on the record). It leaves the computation to S0002, the stops to S0003, refusals to S0004 and agent texts to S0005. It adds no reason on `crash` or `expiry`, which matches decision 4 and the out-of-scope list.
4. factory: started tests as self.
5. tester: I wrote one test for each acceptance criterion. All of them are red, and each fails for the right reason: the module and attribute that are missing (`Blocked`/`StallReason` in `factory.domain.journal`, `JournalRecord.blocked`/`.reason`) or an unknown field (`extra_forbidden`). Nothing fails on a setup fault. `make lint` is green.

   - criterion 1: tests/domain/test_journal_causes.py::test_a_cause_is_accepted_only_on_its_own_kind
   - criterion 2: tests/domain/test_journal_causes.py::test_a_cause_outside_its_type_is_refused_and_every_value_of_it_accepted
   - criterion 3: tests/domain/test_journal_causes.py::test_the_cause_types_kept_in_work_item_and_decisions_are_the_journals
   - criterion 4: tests/domain/test_journal_causes.py::test_append_entry_puts_the_cause_into_the_new_record and ::test_append_entry_refuses_a_blocked_on_a_result_entry
   - criterion 5: tests/adapters/test_journal_causes_file.py::test_the_writer_writes_a_records_cause_only_when_set_and_reads_it_back
   - criterion 6: tests/application/test_stage_finish_causes.py::test_a_stage_end_records_the_block_its_question_opened (rows rule-2, rule-1, rule-4, rule-6; driven through `StageRunner.run`, which ends in `StageFinisher.finish`)
   - criterion 7: tests/application/test_stall_reasons_recorded.py::test_a_stall_records_its_reason (one row per value of `StallReason`)
   - criterion 8: tests/application/test_stall_reasons_recorded.py::test_a_stage_run_that_stalls_records_the_reason (rows red-check at `doing`, merge-conflict)
   - criterion 9: tests/application/test_question_causes_recorded.py::test_the_ask_handler_at_the_attempts_cap_records_the_question_with_its_block
   - criterion 10: tests/application/test_question_causes_recorded.py::test_the_recovery_at_the_crash_cap_records_the_question_with_its_block (rows crash, expiry)
   - criterion 11: tests/application/test_question_causes_recorded.py::test_a_close_that_sends_back_without_a_reason_records_the_question_with_its_block
   - criteria 12 and 13: not tested here (the `make check` gate and the docs stage).

   Files created: tests/domain/test_journal_causes.py, tests/adapters/test_journal_causes_file.py, tests/application/test_stage_finish_causes.py, tests/application/test_stall_reasons_recorded.py, tests/application/test_question_causes_recorded.py, tests/stage_run_support.py.

   Earlier tests changed under the feature's decision 13, which the Interface names. Each change only adds the new field to an expected record:
   - tests/application/handlers/test_questions.py: `blocked="attempts_cap"` in two expected question records.
   - tests/application/test_stalls.py: `reason="died"` in three expected stall records.
   - tests/application/test_recovery_cap.py and tests/application/test_recovery_expiry.py: `blocked="crash_cap"` in the expected question record.

   Earlier test changed under the standing leave to move a shared test helper:
   - tests/application/test_stage_run.py: its constants and its open/Makefile/run/head/state helpers moved to tests/stage_run_support.py as `open_story`, `stage_makefile`, `completed`, `run_stage`, `branch_head` and `pushed_state`.
   - `open_story` gained the optional `state`, `body` and `roles` parameters. Their defaults keep the old behaviour.
   - Every test there keeps its name and checks the same thing, and that module stayed green in the run.

   Modules the test run could not import: tests/domain/test_journal_causes.py and tests/adapters/test_journal_causes_file.py both fail at collection on the new names in `factory.domain.journal` and the new fields.

   Rejected: copying test_stage_finish.py's large helper set for criteria 6 and 8. The whole stage run reaches every rule with less setup.

   Small helpers deliberately repeated in tests/application/test_question_causes_recorded.py:
   - `_pull_request`, which several handler tests already have.
   - An expired event built inline, as test_recovery_expiry.py does.

   Open: none.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/domain/test_journal_causes.py - ImportError while importing test ...
6. factory: started doing as self.
7. coder: I made the tester's tests pass without changing them. `make check` is green.

   Built:
   - `src/factory/domain/journal.py`:
     - `Blocked` and `StallReason` now live here.
     - `JournalRecord` gains optional `blocked` and `reason`. An after-validator refuses `blocked` on any kind but `question` and `reason` on any kind but `stall`, with a `ValueError`.
     - `append_entry` takes the two causes and puts them into the record as given.
     - The private `_record` helper is gone; the record is built inline (`stage` only when `at` is given, as before).
   - `src/factory/domain/work_item.py` keeps `Blocked = journal.Blocked`, and `src/factory/domain/decisions.py` keeps `StallReason = journal.StallReason`, both by assignment.
   - Writers, one argument more each:
     - `StageFinisher.finish` (`src/factory/application/stage.py`): the agent's entry gets `move.blocked` only when its kind is `question`; the factory's question gets `move.blocked`.
     - `StallService._stalled` (`src/factory/application/stalls.py`): `reason=reason`.
     - `AskHandler` (`src/factory/application/handlers/questions.py`): `blocked="attempts_cap"`.
     - `RecoveryHandler._crash_recorded` (`src/factory/application/recovery.py`): `blocked="crash_cap"` on the cap question only.
     - `ClosedHandler._record_decision` (`src/factory/application/handlers/closed.py`): `blocked="send_back"`; its local `blocked` is now typed `Blocked | None` and set before the append, so the value is written once.
   - The work item writer needed no change: `exclude_none` already leaves unset causes out.

   Main decision: `append_entry` takes the causes as `**causes: Unpack[JournalCauses]`, a `TypedDict` (`total=False`) with `blocked` and `reason`, rather than the two plain keyword-only parameters the Interface shows.
   - Why: with two more parameters ruff's `PLR0913` refuses the function (6 > 5).
   - What I rejected:
     - A per-file ignore in `pyproject.toml`, as `claude_runtime.py` already has: the file is outside my write paths (the write was refused).
     - A `# noqa`: the source has none.
   - Effect on callers: they call it exactly as the Interface says (`append_entry(doc, entry, at=..., blocked="round_cap")`), and mypy checks the values against `Blocked` and `StallReason`.
   - For the reviewer: if the plain signature is wanted, the human would need to add the `pyproject.toml` ignore.

   Refactor pass: besides the `closed.py` change above, I renamed `own_block` to `agent_block` in `stage.py`. Nothing else needed changing.

   Noticed, not touched:
   - `AskHandler` writes the literal `"attempts_cap"` twice: once on the record, once on the state.
   - Running pytest directly in this sandbox fails 8 tests in `test_scheduler`, `test_nested_repositories` and `test_repository_waiter` with `RepositoryUnsealed` ("`.git` is writable by its group"). It comes from this sandbox's folder permissions, not from this change: they pass under `make test`.

   The journal did not change the meaning of the task, so I left the Description as it is.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 36 known, 3 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` against the work item.

   Groups 1 to 3 pass:
   - Each criterion from 1 to 11 has a test that checks what the criterion says.
   - The refused sides are tested: wrong kind, value outside the type, `blocked` through `append_entry` on a `result` entry.
   - The coder's journal entry reports `make check` green.
   - The layers hold: the cause types live in `factory.domain.journal` and are kept by assignment in `work_item` and `decisions`.
   - No markers, no secrets.

   Group 4 (quality) fails on helpers the new test module copies from earlier tests:

   1. `tests/application/test_question_causes_recorded.py:44` `_pull_request` is a third copy of `_pull_request` in `tests/application/test_recovery_cap.py:49` and `tests/application/test_recovery_expiry.py:46`, and of the `pull_request` fixture in `tests/application/handlers/conftest.py:64`. Fix: under the standing leave, the tester moves it to `tests/crash_support.py`, which all three modules already import, and has the earlier modules use it from there.
   2. `tests/application/test_question_causes_recorded.py:36-37,88-95` copies three things from `tests/application/test_recovery_expiry.py`:
      - `OTHER_INSTANCE` and `LEASE` (lines 39-40);
      - the other instance's recovery handler, `_other` (line 67);
      - the expired event, `_expired` (line 73).
      It also inlines `_expired_claim`'s clock advance (line 52). Fix: the tester moves these constants and helpers to `tests/crash_support.py` under the standing leave and uses them in both modules. Every earlier test keeps its name and checks the same thing.

   The tester's entry 5 names both copies as "deliberately repeated", but the standing leave in `CLAUDE.md` is meant for exactly this case. These are test changes, so the coder ends with `tests` and names the moves for the tester.

   Not reported because the stop is at the first failing group (group 5): `append_entry`'s built signature is `**causes: Unpack[JournalCauses]` (`src/factory/domain/journal.py:174-188`), not the two keyword-only parameters the Interface shows. The coder's entry 7 explains this.

   Earlier tests (item 6):
   - `tests/application/handlers/test_questions.py`: human's leave. The story's Interface names it under the feature's decision 13. The change only adds `blocked="attempts_cap"` to two expected records.
   - `tests/application/test_recovery_cap.py`: human's leave, the same way. The change only adds `blocked="crash_cap"` to the expected question record.
   - `tests/application/test_recovery_expiry.py`: human's leave, the same way. The change only adds `blocked="crash_cap"` to the expected question record.
   - `tests/application/test_stalls.py`: human's leave, the same way. The change only adds `reason="died"` to three expected stall records.
   - `tests/application/test_stage_run.py`: standing leave to move a shared test helper. Its constants and helpers moved to `tests/stage_run_support.py`; `STORY` is the same text, and the new `open_story` parameters default to the old behaviour. Every test keeps its name and what it checks.
10. factory: started doing as self.
11. coder: Round 1: both of the reviewer's findings are copies of test helpers. Under the standing leave in `CLAUDE.md`, moving them is the tester's job, so I changed no code and end with `tests`.

    I checked the copies with grep, and they match the findings. `tests/crash_support.py` holds none of these names yet, and all three modules below already import from it.

    Moves for the tester, all to `tests/crash_support.py`:
    1. `_pull_request(hosting)`. It is now in three places:
       - `tests/application/test_question_causes_recorded.py:44`
       - `tests/application/test_recovery_cap.py:49`
       - `tests/application/test_recovery_expiry.py:46`

       Move it to one shared public helper and have the three modules use it. The reviewer also names the matching `pull_request` fixture in `tests/application/handlers/conftest.py:64`. Whether that fixture should use the shared helper is the tester's choice under the leave.
    2. These are copied from `tests/application/test_recovery_expiry.py` into `tests/application/test_question_causes_recorded.py`:
       - the constants `OTHER_INSTANCE` and `LEASE` (expiry module lines 39-40; new module lines 36-37);
       - the other instance's recovery handler `_other` (line 67);
       - the expired event `_expired` (line 73);
       - the clock advance in `_expired_claim` (line 52), which the new module inlines.

       Move them to the shared module, and have both modules use them there.

    Every earlier test keeps its name and checks the same thing.

    Rejected: changing the tests myself. The coder never edits tests (R9), and the leave belongs to the tester.

    Noticed, not touched: the reviewer stopped at group 4, so group 5 is still open. That is the `append_entry` signature, which takes `**causes: Unpack[JournalCauses]` instead of the two keyword-only parameters the Interface shows. The reason is in entry 7: ruff's `PLR0913` refuses the function, and a per-file ignore would mean editing `pyproject.toml`, which the write guard refused. It may come back as a finding once the tests are green.

    The journal did not change the meaning of the task, so the Description stays as it is.

    I did not run `make check` this round because nothing changed. It was green at the end of round 0.
12. factory: started tests as self.
13. tester: Mode: a test change the human approved. I moved the copied test helpers that the reviewer found (entry 9) and the coder listed (entry 11). I did this under the standing leave in `CLAUDE.md` for moving a shared test helper. No acceptance criterion was added or changed, so the criterion-to-test mapping from entry 5 still holds.

    New in `tests/crash_support.py` (none of these names were there before):
    - `OTHER_INSTANCE`, `LEASE`: the constants from `test_recovery_expiry.py`.
    - `open_pull_request(hosting)`: was the `_pull_request` copy. It is now the one shared helper, and the title is `f"{WORK_ITEM}: {STORY_TITLE}"`.
    - `expired_claim(...)`: was `_expired_claim`. It claims as `INSTANCE`, then advances the clock by `LEASE`.
    - `expired_event(work_item)`: was `_expired`.
    - `other_handler(boundaries, claimed, run)`: was `_other`, the other instance's `RecoveryHandler`.

    Earlier test files I changed under the standing leave (every test keeps its name and checks the same thing):
    - `tests/application/test_recovery_expiry.py`:
      - Removed its local `OTHER_INSTANCE`, `LEASE`, `_pull_request`, `_expired_claim`, `_other` and `_expired`.
      - It now imports them from `crash_support` under the new names.
      - `CAP`, `UNTRACKED` and `COMMITTED` stay in the module.
    - `tests/application/test_recovery_cap.py`: removed its `_pull_request` and uses `open_pull_request`.

    This story's test changed: `tests/application/test_question_causes_recorded.py`.
    - Its own `OTHER_INSTANCE`, `LEASE` and `_pull_request` are removed.
    - The expiry row of `test_the_recovery_at_the_crash_cap_records_the_question_with_its_block` now uses `expired_claim` (with `crashes=1`), `other_handler` and `expired_event` instead of the inlined copies.
    - Its pull request title is now `"<id>: First story"` instead of `"<id>: first"`. None of its assertions read the title.

    Rejected: changing the `pull_request` fixture in `tests/application/handlers/conftest.py` to use the shared helper. That was left to me (entry 11). The fixture belongs to the handler tests and has its own `WORK_ITEM`/`BRANCH` constants and its own title (`"…: first"`). `test_closed_send_back.py:420` uses the same title inline. Switching would change the pull request title for every handler test, which goes beyond moving a copy.

    Results:
    - `make test`: `test: green (40.3 s)`. The tests are green because the code was already built in round 0.
    - `make lint`: `lint: green`.
    - No module failed to import.

    Files changed: `tests/crash_support.py`, `tests/application/test_recovery_expiry.py`, `tests/application/test_recovery_cap.py`, `tests/application/test_question_causes_recorded.py`.

    Still open, from entry 11: group 5. `append_entry`'s signature is `**causes: Unpack[JournalCauses]`, not the two keyword-only parameters in the Interface.

    `lint`: lint: green (0.0 s)
    `test`: test: green (37.7 s)
14. factory: started doing as self.
