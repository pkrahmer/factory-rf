# The journal records why a work item waited or stalled, and the cost table counts the human

## Description

Today a work item's front matter says that a question was asked or that a stage stalled, but not why: the cause is only in the entry's text, which no code reads. This story puts the cause into the record. A journal record of kind `question` gains an optional `blocked`, the block the question opened (`question`, `attempts_cap`, `round_cap`, `crash_cap` or `send_back`), and a record of kind `stall` an optional `reason`, the stall reason the factory already decides (`died`, `time_limit`, `budget`, `no_result`, `decision_not_allowed`, `left_branch`, `form_invalid`, `check_red`, `merge_conflict`, `nested_repository`). Every place that records a blocking question or a stall writes the field; records without it, every record written before this story included, stay valid and are written back without it. From these records a new domain module computes the human's waits: one per blocking question, from its `at` to the `at` of the next record the human spoke, and the line `<n> questions answered (<cause> <count>, ...), <hours> h waited`. The hand-over shows that line under the cost table it posts on the pull request, for a story and for an acceptance, and the acceptance reviewer's facts gain it as one more line, summed over the archived stories. `crash` and `expiry` records get no reason (the feature's decision 4). The agent texts that use the new facts line are S0003's; the stop records and the run record's refusals are S0002's.

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

`factory.domain.human_waits` (`domain`, new):

```python
class HumanWait(BaseModel):
    """One wait for the human: the blocking question, its cause, when it was asked and answered."""

    question: PositiveInt
    blocked: Blocked
    asked_at: UtcDatetime
    answered_at: UtcDatetime | None = None


def human_waits(journal: Sequence[JournalRecord]) -> list[HumanWait]:
    """One wait per question record with a `blocked` and an `at`, in journal order."""


def human_line(waits: Sequence[HumanWait]) -> str:
    """`<n> questions answered (<cause> <count>, ...), <hours> h waited`."""
```

- A wait is a record of kind `question` that has both `blocked` and `at`; any other record starts none. Its `answered_at` is the `at` of the first later record (higher `number`) whose `speaker` is `human` and that has an `at`, whatever its kind (`comment` or `close`); `None` when there is none.
- `human_line`: `<n>` counts the answered waits only. The parenthesis follows only when `<n>` is above 0 and names each cause with at least one answered wait, as `<cause> <count>`, joined by `, `, in the order of `Blocked`'s values. `<hours>` is the sum of `answered_at - asked_at` over the answered waits, in hours, one decimal, rounded half up, as the cost table rounds its minutes. Unanswered waits count in neither. No waits: `0 questions answered, 0.0 h waited`.

`factory.domain.post_texts` (`domain`):

```python
def cost_table_post(table: str, human: str | None = None) -> str: ...
```

- Without `human`, the text is as today. With it, the text is followed by an empty line and `Human: <human>`.

`factory.application.handlers.hand_over.HandOverHandler` and `factory.application.acceptance.AcceptanceHandOver` (`application`): the cost table post passes `human=human_line(human_waits(<state>.journal))` of the document the handler read. The post's key is unchanged.

`factory.domain.acceptance` (`domain`):

```python
class AcceptanceFacts(BaseModel):
    archived: list[WorkItemId]
    next_story: WorkItemId
    cost_line: str
    human_line: str | None = None
    disk_now: str | None = None
    disk_before: str | None = None


def acceptance_facts(
    files: FeatureFiles,
    cost_line: str,
    *,
    human_line: str | None = None,
    disk_now: str | None = None,
    disk_before: str | None = None,
) -> AcceptanceFacts: ...
```

- `lines()` gives, when `human_line` is set, the line `Human interventions of the stories: <human_line>` right after `Cost of the stories: ...` and before the disk lines. Without it, the lines are as today.

`factory.application.acceptance.AcceptanceService.facts` (`application`): passes `human_line` as the line of the waits of every archived story (not an acceptance report) in the feature's `done/` on `origin/main`, read from the story's file there, in the order of the stories. A file without a state adds no wait. The reading reuses the way the service and `factory.application.acceptance_reading` already read a file at a ref (`git.show_file` and the work item reader's `parse`); no third copy.

Test modules (new): `tests/domain/test_journal_causes.py`, `tests/domain/test_human_waits.py`, `tests/domain/test_acceptance_facts_human.py`, `tests/adapters/test_journal_causes_file.py`, `tests/application/test_stage_finish_causes.py`, `tests/application/test_stall_reasons_recorded.py`, `tests/application/test_question_causes_recorded.py`, `tests/application/test_human_line_posts.py`, `tests/application/test_acceptance_facts_human.py`. Earlier tests this story changes, under the feature's decision 13: `tests/application/handlers/test_questions.py`, `tests/application/test_stalls.py`, `tests/application/test_recovery_cap.py`, `tests/application/test_recovery_expiry.py`, `tests/application/handlers/test_hand_over.py`, `tests/application/test_stage_run_acceptance.py`, `tests/application/test_task_acceptance.py`, each only by adding the new field or line to an expected value.

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
12. `human_waits`, rows of one parametrized test, times in UTC on one day:
    - `question` at 10:00 with `blocked: crash_cap`, then a human `comment` at 11:30: one wait, `question` its number, `blocked` `crash_cap`, `asked_at` 10:00, `answered_at` 11:30.
    - The same with a `result` of the reviewer at 10:30 between them: the same wait (only the human's record ends it).
    - `question` at 10:00 with `blocked: send_back`, then a human `close` at 10:45: answered at 10:45.
    - `question` with `blocked: question` and no later human record: one wait with `answered_at` `None`.
    - `question` without `blocked`, then a human `comment`: no wait.
    - `question` with `blocked` but no `at`: no wait.
    - `question` with `blocked`, then a human `comment` without `at`, then a human `comment` at 12:00: answered at 12:00.
    - Two blocking questions, each followed by a human comment: two waits, in journal order.
13. `human_line`, rows of one parametrized test:
    - no waits: `0 questions answered, 0.0 h waited`;
    - one answered `crash_cap` wait of 1 h 30 min: `1 questions answered (crash_cap 1), 1.5 h waited`;
    - answered waits `round_cap` of 15 min and `question` of 1 h 30 min, and one unanswered `send_back` wait: `2 questions answered (question 1, round_cap 1), 1.8 h waited` (1.75 rounds half up, the causes in `Blocked`'s order, the unanswered wait in neither count);
    - one answered wait of 2 min 24 s (0.04 h): `1 questions answered (question 1), 0.0 h waited`; one of 3 min (0.05 h): `... 0.1 h waited`;
    - only unanswered waits: `0 questions answered, 0.0 h waited`.
14. `cost_table_post("T")` is `Cost of this work item so far\n\nT`, and `cost_table_post("T", human="0 questions answered, 0.0 h waited")` is `Cost of this work item so far\n\nT\n\nHuman: 0 questions answered, 0.0 h waited` (rows of one parametrized test).
15. The hand-over of a story at its approval, and the hand-over of an acceptance at its approval (rows of one parametrized test), post the cost table with the line `Human: <human_line>` of the work item's own journal on its branch: a journal with one blocking question answered after 1 h 30 min gives `Human: 1 questions answered (question 1), 1.5 h waited`.
16. `AcceptanceFacts.lines()`, rows of one parametrized test: with `human_line` and without a disk, four lines, the last `Human interventions of the stories: <line>`, right after `Cost of the stories: ...`; with `human_line` and a disk, that line fourth and the two disk lines after it; without `human_line`, the lines as today. `acceptance_facts(files, cost_line, human_line="x")` passes the value on.
17. `AcceptanceService.facts` of a feature whose `done/` on `origin/main` holds two stories, one with a blocking question answered after 1 h and one with a blocking question answered after 30 min, plus an acceptance report with an answered blocking question of its own: `human_line` is `2 questions answered (question 1, crash_cap 1), 1.5 h waited` for the stories' causes `question` and `crash_cap`, the acceptance report not counted. A story in the feature's `backlog/` with a blocking question is not counted either, and a done story file without front matter adds nothing.
18. `make check` stays green.
19. docs:
    - `docs/project-guide.md`, *The journal's data*: the rows `blocked` (on a `question` record: the block it opened, one of `Blocked`'s values) and `reason` (on a `stall` record: the stall reason), both optional and left out when unset; that `crash` and `expiry` records carry no reason, and why (the feature's decision 4). A new subsection *The human's waits* under *Bills*: `human_waits` and `human_line`, with the rules of a wait and its end (the feature's decisions 5 and 6).
    - `docs/operator-guide.md`, *The cost table*: the `Human:` line under the table, what it counts and that a question answered by a close counts too; *When a feature acceptance is due*: the facts line `Human interventions of the stories`.
    - `docs/decisions.md`: a new entry, "A question records the block it opened, a stall its reason", with the reason (the status map reads the front matter and never parses prose) and the rejected alternatives: parsing the entry texts, and a reason on crash records.

## Smoke test

```bash
uv run -q python -c '
from datetime import UTC, datetime
from factory.domain.human_waits import human_line, human_waits
from factory.domain.journal import JournalRecord

def at(hour, minute):
    return datetime(2026, 10, 18, hour, minute, tzinfo=UTC)

journal = [
    JournalRecord(number=1, speaker="human", kind="created"),
    JournalRecord(number=2, speaker="factory", kind="question", at=at(10, 0), blocked="crash_cap"),
    JournalRecord(number=3, speaker="human", kind="comment", at=at(11, 30)),
    JournalRecord(number=4, speaker="reviewer", kind="question", at=at(12, 0), blocked="question"),
]
print(human_line(human_waits(journal)))
'
```

Expect: `1 questions answered (crash_cap 1), 1.5 h waited`

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

```bash
uv run -q python -c '
from factory.domain.post_texts import cost_table_post

print(repr(cost_table_post("T", human="0 questions answered, 0.0 h waited")))
'
```

Expect: `'Cost of this work item so far\n\nT\n\nHuman: 0 questions answered, 0.0 h waited'`

## Journal
