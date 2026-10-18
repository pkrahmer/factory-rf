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
  started_at: '2026-10-18T21:47:49.404190Z'
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
