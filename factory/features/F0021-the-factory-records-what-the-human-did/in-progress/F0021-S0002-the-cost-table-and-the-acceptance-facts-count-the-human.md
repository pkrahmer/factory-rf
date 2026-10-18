---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 236
comments_read: [6255900893]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T22:21:54.384718Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T22:21:54.391073Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-18T22:22:12.030092Z'
  stage: intake
  run: 2ce9b88aeef0402d90e293b38c35c7e7
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-18T22:24:31.203151Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-18T22:24:48.782669Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-18T22:25:05.816617Z'
  stage: intake
  run: 4f4ceead4423435e87ed35c2e6076a22
---

# The cost table and the acceptance facts count the human

## Description

S0001 put the cause of every blocking question into the journal. From those records a new domain module computes the human's waits: one per blocking question, from its `at` to the `at` of the next record the human spoke, and the line `<n> questions answered (<cause> <count>, ...), <hours> h waited`. The hand-over shows that line under the cost table it posts on the pull request, for a story and for an acceptance, and the acceptance reviewer's facts gain it as one more line, summed over the archived stories. A wait ends at the next record the human spoke, a `comment` or a `close`; a comment's record carries the time the factory copied it from the pull request, not the time the human wrote it, so a wait ends up to one tick late (the feature's decisions 5 and 6). The hours are rounded by one shared helper, the one the cost table already uses for its minutes, not by a second copy. The agent texts that use the new facts line are S0005's.

## Interface

`factory.domain.bills` (`domain`): one public helper, which its minutes and the human line both call; no second copy of the rounding.

```python
def one_decimal(value: Decimal) -> str:
    """`value` with one decimal, rounded half up."""
```

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
- `human_line`: `<n>` counts the answered waits only. The parenthesis follows only when `<n>` is above 0 and names each cause with at least one answered wait, as `<cause> <count>`, joined by `, `, in the order of `Blocked`'s values. `<hours>` is the sum of `answered_at - asked_at` over the answered waits, in hours, one decimal, rounded half up, as the cost table rounds its minutes. Unanswered waits count in neither. No waits: `0 questions answered, 0.0 h waited`. The rounding is the one the cost table uses for its minutes: `factory.domain.bills` gets one public helper, `one_decimal(value: Decimal) -> str` (half up), which its minutes and `human_line` both call; no second copy.

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

`factory.application.acceptance.AcceptanceService.facts` (`application`): passes `human_line` as the line of the waits of every archived story (not an acceptance report) in the feature's `done/` on `origin/main`, read from the story's file there, in the order of the stories. A done story file that the work item reader's `parse` refuses (`WorkItemFormatError`: no front matter, or a state it cannot read) adds no wait, so that one damaged archived file does not stop the acceptance. The reading reuses the way the service and `factory.application.acceptance_reading` already read a file at a ref (`git.show_file` and the work item reader's `parse`); no third copy.

Test modules (new): `tests/domain/test_human_waits.py`, `tests/domain/test_acceptance_facts_human.py`, `tests/application/test_human_line_posts.py`, `tests/application/test_acceptance_facts_human.py`. Earlier tests this story changes, under the feature's decision 13: `tests/application/handlers/test_hand_over.py`, `tests/application/test_stage_run_acceptance.py`, `tests/application/test_task_acceptance.py`, each only by adding the new line to an expected value.

## Acceptance criteria

1. `human_waits`, rows of one parametrized test, times in UTC on one day:
    - `question` at 10:00 with `blocked: crash_cap`, then a human `comment` at 11:30: one wait, `question` its number, `blocked` `crash_cap`, `asked_at` 10:00, `answered_at` 11:30.
    - The same with a `result` of the reviewer at 10:30 between them: the same wait (only the human's record ends it).
    - `question` at 10:00 with `blocked: send_back`, then a human `close` at 10:45: answered at 10:45.
    - `question` with `blocked: question` and no later human record: one wait with `answered_at` `None`.
    - `question` without `blocked`, then a human `comment`: no wait.
    - `question` with `blocked` but no `at`: no wait.
    - `question` with `blocked`, then a human `comment` without `at`, then a human `comment` at 12:00: answered at 12:00.
    - Two blocking questions, each followed by a human comment: two waits, in journal order.
    - A human `comment` at 09:00 before a `question` with `blocked` at 10:00, and no later human record: one wait with `answered_at` `None` (a human record before the question does not end it).
2. `human_line`, rows of one parametrized test:
    - no waits: `0 questions answered, 0.0 h waited`;
    - one answered `crash_cap` wait of 1 h 30 min: `1 questions answered (crash_cap 1), 1.5 h waited`;
    - answered waits `round_cap` of 15 min and `question` of 1 h 30 min, and one unanswered `send_back` wait: `2 questions answered (question 1, round_cap 1), 1.8 h waited` (1.75 rounds half up, the causes in `Blocked`'s order, the unanswered wait in neither count);
    - one answered wait of 2 min 24 s (0.04 h): `1 questions answered (question 1), 0.0 h waited`; one of 3 min (0.05 h): `... 0.1 h waited`;
    - only unanswered waits: `0 questions answered, 0.0 h waited`.
3. `cost_table_post("T")` is `Cost of this work item so far\n\nT`, and `cost_table_post("T", human="0 questions answered, 0.0 h waited")` is `Cost of this work item so far\n\nT\n\nHuman: 0 questions answered, 0.0 h waited` (rows of one parametrized test).
4. The hand-over of a story at its approval, and the hand-over of an acceptance at its approval (rows of one parametrized test), post the cost table with the line `Human: <human_line>` of the work item's own journal on its branch: a journal with one blocking question answered after 1 h 30 min gives `Human: 1 questions answered (question 1), 1.5 h waited`.
5. `AcceptanceFacts.lines()`, rows of one parametrized test: with `human_line` and without a disk, four lines, the last `Human interventions of the stories: <line>`, right after `Cost of the stories: ...`; with `human_line` and a disk, that line fourth and the two disk lines after it; without `human_line`, the lines as today. `acceptance_facts(files, cost_line, human_line="x")` passes the value on.
6. `AcceptanceService.facts` of a feature whose `done/` on `origin/main` holds two stories, one with a blocking question answered after 1 h and one with a blocking question answered after 30 min, plus an acceptance report with an answered blocking question of its own: `human_line` is `2 questions answered (question 1, crash_cap 1), 1.5 h waited` for the stories' causes `question` and `crash_cap`, the acceptance report not counted. A story in the feature's `backlog/` with a blocking question is not counted either, and a done story file without front matter adds nothing, and neither does a done story whose front matter fails validation (rows of one parametrized test: the counted stories, a backlog story, a file without front matter, a file whose front matter fails validation).
7. `make check` stays green.
8. docs:
    - `docs/project-guide.md`: a new subsection *The human's waits* under *Bills*: `human_waits` and `human_line`, with the rules of a wait and its end (the feature's decisions 5 and 6), including that a comment's record carries the time the factory copied it, so a wait ends up to one tick late; `one_decimal` as the one rounding of the minutes and the hours.
    - `docs/operator-guide.md`, *The cost table*: the `Human:` line under the table, what it counts and that a question answered by a close counts too; *When a feature acceptance is due*: the facts line `Human interventions of the stories`.

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
from factory.domain.post_texts import cost_table_post

print(repr(cost_table_post("T", human="0 questions answered, 0.0 h waited")))
'
```

Expect: `'Cost of this work item so far\n\nT\n\nHuman: 0 questions answered, 0.0 h waited'`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: The format check passed. The Interface, the architecture and the scope are fine. Two Interface clauses have no criterion, so I am asking. My choice for both is to add the rows.

   1. Criterion 6 and `AcceptanceService.facts`: the Interface says a done story file that `parse` refuses adds no wait, "no front matter, or a state it cannot read". The criterion's rows cover only "a file without front matter". The second branch, a file with front matter whose state cannot be read, has no row. Should I add a fourth row, "a done story whose front matter fails validation adds nothing"? I would choose yes.

   2. Criterion 1 and `human_waits`: the Interface says `answered_at` is the `at` of the first *later* record (higher `number`) of the human. No row shows that a human record *before* the question does not end the wait. Criterion 1's rows always put the human record after the question. Should I add a row with a human `comment` at 09:00 before a blocking question at 10:00 and no later human record, giving `answered_at` `None`? I would choose yes.

   Everything else is testable by one test function. The smoke test commands are runnable and their Expect lines can be checked against the output.
4. 2026-10-18 human: Yes to both: add the fourth row to criterion 6 (a done story whose front matter fails validation adds nothing) and the row to criterion 1 (a human `comment` at 09:00 before a blocking question at 10:00 and no later human record gives `answered_at` `None`).
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete modules and signatures (`factory.domain.bills.one_decimal`, `factory.domain.human_waits`, `cost_table_post`, `AcceptanceFacts`/`acceptance_facts`, the two handlers, `AcceptanceService.facts`). Every comment's behaviour has a criterion.
   - Criteria: each is testable by one parametrized test. Each rule has its failing side: unanswered waits, no `blocked`, no `at`, a human record without `at`, no waits, a backlog story, an acceptance report, a file without front matter. Carried in from the human's answer (journal entry 4): criterion 1 gained the row "a human comment at 09:00 before the blocking question gives `answered_at` None", and criterion 6 gained the row "a done story whose front matter fails validation adds nothing", plus the matching row list.
   - Smoke test: both commands are runnable, and each `Expect:` line is an exact output to compare.
   - Architecture: the pure rules are in `domain`, the posting and reading are in `application` and reuse `git.show_file` and `parse`, and no layer is crossed.
   - Scope: within the feature's S0002 bullets (the human line on the cost table and the acceptance facts). The changes to earlier tests are covered by decision 13.
