---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 236
comments_read: [6255900893]
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-18T22:43:38.623875Z'
  lease_duration: 60
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
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-18T22:25:25.776032Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-18T22:30:07.250495Z'
  stage: tests
  run: 09babd471f6240a996849cc227a1eb6b
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-18T22:30:28.113455Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-18T22:33:49.317029Z'
  stage: doing
  run: f2da7d2ed3f94db4b7f39dd494b8794a
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-18T22:34:09.457636Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-18T22:35:19.926532Z'
  stage: review
  run: 1d62b2f5c2664b57aa086aa73088877d
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-18T22:35:40.104083Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-18T22:35:56.627584Z'
  stage: doing
  run: baa0eae1398b4abc8231fe6aed8bebc7
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-18T22:36:16.863129Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-18T22:38:07.076533Z'
  stage: tests
  run: d0b58d36f47a4f519d5c02ed94228694
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-18T22:38:27.345494Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-18T22:40:13.913077Z'
  stage: doing
  run: 95e29051987346d7be2854a2709e4069
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-18T22:40:33.923489Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-18T22:41:36.048994Z'
  stage: review
  run: 8f2015ac74b24879a2737b0416ff75f4
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-18T22:41:56.493614Z'
  stage: docs
- number: 22
  speaker: documenter
  kind: result
  at: '2026-10-18T22:43:18.500621Z'
  stage: docs
  run: b5186e19f7234c70b9e0c4aff96c3a03
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-18T22:43:38.623875Z'
  stage: smoke-test
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
7. factory: started tests as self.
8. tester: I wrote the red tests for every acceptance criterion. Nothing needed interpreting, so there is no question.

   Criteria → tests:
   - criterion 1: tests/domain/test_human_waits.py::test_each_blocking_question_waits_until_the_next_human_record_with_a_time. It has 9 rows, including the human comment before the question from journal entry 4.
   - criterion 2: tests/domain/test_human_waits.py::test_the_human_line_counts_the_answered_waits_by_cause_and_their_hours. Its rows: no waits, one answered, mixed causes with 1.75 rounding half up, 0.04 h, 0.05 h, only unanswered.
   - criterion 3: tests/domain/test_human_waits.py::test_the_cost_table_post_ends_with_the_human_line_when_given. Its rows are without human and with human.
   - criterion 4: tests/application/test_human_line_posts.py::test_the_hand_over_posts_the_cost_table_with_the_human_line_of_the_journal. Its rows are story (HandOverHandler) and acceptance (AcceptanceHandOver). Each expects the post `render_post(cost_table_post(table, human="1 questions answered (question 1), 1.5 h waited"), cost_table_key(...))`.
   - criterion 5: tests/domain/test_acceptance_facts_human.py::test_the_human_line_follows_the_cost_line_and_precedes_the_disk_lines covers the human line with and without a disk, and no human line with and without a disk. tests/domain/test_acceptance_facts_human.py::test_acceptance_facts_pass_the_human_line_on covers the passing on.
   - criterion 6: tests/application/test_acceptance_facts_human.py::test_the_facts_carry_the_waits_of_the_archived_stories_only. Its rows: counted-stories, backlog-story, no-front-matter, invalid-front-matter. The invalid file has front matter with an unknown key. The acceptance report in `done/` carries a round_cap wait of 2 h, which must not be counted.
   - criterion 7: no test. It is `make check`.
   - criterion 8: no test. It is the docs stage's.

   Files created: tests/domain/test_human_waits.py, tests/domain/test_acceptance_facts_human.py, tests/application/test_human_line_posts.py, tests/application/test_acceptance_facts_human.py.

   Earlier tests changed, each only to add the new line to an expected value, under the feature's decision 13 as the Interface names them:
   - tests/application/handlers/test_hand_over.py: `_expected_post` now passes `human="0 questions answered, 0.0 h waited"`. That journal has no blocking question.
   - tests/application/test_stage_run_acceptance.py: the prompt's tail slice goes from `[-3:]` to `[-4:]`.
   - tests/application/test_task_acceptance.py: the slice goes from `[-4:]` to `[-5:]`.

   The last two slices grow because the facts now always carry the human line. The done files in those tests have no front matter, so the line is `0 questions answered, 0.0 h waited`.

   The tests stay off one thing the criteria don't name: `one_decimal` gets no test of its own. Criterion 2 checks the rounding only through `human_line`.

   Test run: `make test` is red as intended. The test runner could not import `factory.domain.human_waits`, which does not exist yet. The tests of `AcceptanceFacts.human_line`, of `cost_table_post(..., human=...)` and the two prompt-slice tests fail with wrong results. `make lint` is green. I skipped the type check, as the stage says.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/domain/test_human_waits.py - ImportError while importing test mod...
9. factory: started doing as self.
10. coder: I implemented the human's waits and their line, and wired the line into both cost-table posts and the acceptance facts. `make check` is green, `make duplicates` reports `0 new, 36 known, 3 gone`, and both smoke-test commands print their Expect lines.

    What I built:
    - `src/factory/domain/human_waits.py` (new): `HumanWait`, `human_waits` and `human_line`. A wait ends at the `at` of the first later human record that has an `at`, whatever its kind. The causes are listed in the order of `get_args(Blocked)`. The hours are summed over the answered waits only.
    - `src/factory/domain/bills.py`: the public `one_decimal` (half up). `_minutes` now calls it, and `human_line` uses it for the hours, so there is one rounding.
    - `src/factory/domain/post_texts.py`: `cost_table_post(table, human=None)` adds an empty line and `Human: <human>` when `human` is given.
    - `src/factory/domain/acceptance.py`: `AcceptanceFacts.human_line` and the `human_line` keyword of `acceptance_facts`. `lines()` puts `Human interventions of the stories: ...` after the cost line and before the disk lines.
    - `src/factory/application/handlers/hand_over.py` and `src/factory/application/acceptance.py` (`AcceptanceHandOver`): `_show` now receives the state that `handle` already checked, and posts `human_line(human_waits(state.journal))` under the table. The post's key is unchanged.
    - `src/factory/application/acceptance.py` (`AcceptanceService.facts`): in the same loop that reads the cost records, it reads each archived story's waits through the new `_waits`. A `WorkItemFormatError` means that story adds nothing. Acceptance reports in `done/` are skipped, as the cost loop already did.
    - `src/factory/application/acceptance_reading.py`: I split the private `_document` into a public `AcceptanceReader.document(ref, path)` (`show_file` plus `parse_at`). `_document` keeps its own check that the state is an acceptance's. `AcceptanceService` calls `document` through its existing `_reader`, so the file reading at a ref is not copied a third time.

    Main choice: I gave the handlers' `_show` the already-checked `WorkItemState` as one more parameter. The alternative I rejected was calling `require_state` again inside `_show`, which repeats a check and a `CannotHandle` that `handle` has already made.

    Refactor: I read my diff once. The only change I made was to replace the walrus count in `_causes` with a plain list count; nothing else needed changing.

    The journal did not change what the task means, so I left the Description as it is.

    Noticed, not touched:
    - `_hours` and `_minutes` each turn a timedelta into a `Decimal` of seconds the same way (two lines each). I did not share that step, to keep the change inside the Interface's `one_decimal`.
    - `make duplicates` reports 3 baseline findings as gone, among them the unused `close` methods in `pygithub_hosting.py` and `application/hosting.py`. The baseline is not mine to update.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 36 known, 3 gone
11. factory: started review as self.
12. reviewer: 1. `src/factory/domain/human_waits.py` `HumanWait.question` (`tests/domain/test_human_waits.py`): the Interface types `question` as `PositiveInt`, but no test checks either side of that limit. Every row uses 2, 3 or 4, so nothing shows that 0 is refused or that 1 is accepted. CLAUDE.md *Tests* says a stated limit is tested on both sides even when no criterion names the refused side. This is also a gap in the story: no criterion covers the refused side, so I am naming it for the human. Fix: the tester adds one parametrized test that builds `HumanWait` through a variable typed `type[BaseModel]`, with a row for `question=0` (raises `ValidationError`) and a row for `question=1` (accepted). Criterion 1 or 2 should gain that row so the Description matches the tests.

    Groups 2 to 5 were not reviewed because group 1 failed. I did not run `make check`; the coder's entry 10 reports it green.

    Earlier tests:
    - `tests/application/handlers/test_hand_over.py`: changed under the feature's decision 13, which the Interface cites (`_expected_post` passes the human line). Only the expected value changed.
    - `tests/application/test_stage_run_acceptance.py`: changed under the feature's decision 13. The compared prompt tail grows by one line (`[-3:]` → `[-4:]`), nothing else.
    - `tests/application/test_task_acceptance.py`: changed under the feature's decision 13. The compared prompt tail grows by one line (`[-4:]` → `[-5:]`), nothing else.
13. factory: started doing as self.
14. coder: Round 1. The reviewer has one finding, and it is about tests, not code: no test checks either side of the `PositiveInt` limit on `HumanWait.question`. Fixing it is the tester's job (R9), so I changed no code and no test. `src/factory/domain/human_waits.py` already declares `question: PositiveInt`, so the new test should pass as soon as it exists.

    The test change for the tester: in `tests/domain/test_human_waits.py`, add one parametrized test that builds `HumanWait` through a variable typed `type[BaseModel]`, with two rows:
    - `question=0` raises `ValidationError`;
    - `question=1` is accepted.

    Each row also needs `blocked="question"` and a UTC `asked_at`.

    What the journal changed: nothing in what the task means. `PositiveInt` was already in the Interface, and CLAUDE.md *Tests* asks for a test on both sides of every limit the Interface states. The reviewer also suggests that criterion 1 gain a matching row. I left `## Description` as it is because no journal entry changed the meaning of the task. If that row should be written into the Description, the tester can add it with the test.

    Not run: `make check`, because nothing changed since entry 10, where it was green.
15. factory: started tests as self.
16. tester: Round 1, test change (step 0). Entry 14 (coder) names this change, which comes from the reviewer's finding in entry 12: no test checked either side of the `PositiveInt` limit on `HumanWait.question`. CLAUDE.md *Tests* asks for a test on both sides of every limit the Interface states.

    What I changed, only in `tests/domain/test_human_waits.py`:
    - Added `test_a_wait_names_a_question_numbered_from_one`, one parametrized test that builds `HumanWait` through a variable typed `type[BaseModel]`. Each row also passes `blocked="question"` and a UTC `asked_at`.
      - `zero`: `question=0` raises `ValidationError`.
      - `one`: `question=1` is accepted and keeps the value.
    - Imported `BaseModel` and `ValidationError` from pydantic.
    - Ran `ruff format` on the file to add the blank line that `make lint` asked for.

    No other test changed. I did not add a criterion row to `## Description`. Entry 14 left it open, and the limit was already stated in the Interface.

    Test run: `make test` is green (`test: green (40.8 s)`), so the code already refuses 0 and accepts 1. Every module imported. `make lint` is green.

    `lint`: lint: green (0.0 s)
    `test`: test: green (39.4 s)
17. factory: started doing as self.
18. coder: Round 1. The reviewer's only finding in entry 12 was a missing test on both sides of the `PositiveInt` limit on `HumanWait.question`. The tester added that test in entry 16 (`tests/domain/test_human_waits.py::test_a_wait_names_a_question_numbered_from_one`). The code already declares `question: PositiveInt` in `src/factory/domain/human_waits.py`, so it already refuses 0 and accepts 1, and no code needed to change. I ran `make check` on the committed state with the new test, and it is green (`check: green`).

    What I built is unchanged from entry 10: `src/factory/domain/human_waits.py`, `src/factory/domain/bills.py` (`one_decimal`), `src/factory/domain/post_texts.py`, `src/factory/domain/acceptance.py`, `src/factory/application/handlers/hand_over.py`, `src/factory/application/acceptance.py` and `src/factory/application/acceptance_reading.py` (the public `AcceptanceReader.document`). The main choice is also unchanged. The handlers' `_show` receives the state that `handle` already checked, rather than calling `require_state` a second time.

    Refactor: there was no new diff this round, so nothing needed changing.

    What the journal changed: nothing in what the task means. The limit was already in the Interface. Neither the coder (entry 14) nor the tester (entry 16) added a criterion row for it, so `## Description` stays as it is. The reviewer had suggested a matching row for criterion 1 or 2. That is open for the reviewer or the human to decide.

    Still open from entry 10, not touched: `_hours` and `_minutes` each turn a timedelta into a Decimal of seconds the same way. Also, `make duplicates` reports 3 baseline findings as gone, and the baseline is not mine to update.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 0 new, 36 known, 3 gone
19. factory: started review as self.
20. reviewer: no findings

    Round 1, second review. I read the work item, the diff stat, the name-status list and the full diff of `src` and `tests` (`git diff main...HEAD -- . ':!factory'`). I did not run `make check`: entry 18 reports it green on the committed state.

    1. Acceptance criteria: every criterion from 1 to 6 has one parametrized test whose rows match the criterion's bullets.
       - Criterion 1 has 9 rows, including the human record before the question.
       - Criterion 2 has 6 rows, including both sides of the 0.05 h rounding.
       - Criterion 3 has 2 rows.
       - Criterion 4 covers the story and the acceptance through `HandOverHandler` and `AcceptanceHandOver`.
       - Criterion 5 has 4 rows plus the test that the value is passed on.
       - Criterion 6 has the counted stories, the backlog story, a file without front matter and a file with invalid front matter. The acceptance report's 2 h `round_cap` wait would change the expected line if it were counted.
       - The one numeric limit in the Interface, `HumanWait.question: PositiveInt`, is now tested at 0 and 1 as rows of one test (entry 16). That closes entry 12's finding.
    2. Architecture: `human_waits` is pure domain code and imports only `bills`, `journal` and `times`. The handlers and `AcceptanceService` sit in `application` and call domain functions. The file is read at a ref through the existing `AcceptanceReader`, whose private `_document` was split into a public `document` (show_file plus `parse_at`), so there is no third copy of that reading. No layer is crossed and no tool is called directly.
    3. Security: no strings are built into commands or SQL, and no silencing markers were added. A damaged archived file is caught as `WorkItemFormatError` and adds no waits, as the Interface says.
    4. Quality: one rounding (`one_decimal`) is used for both the minutes and the hours. Docstrings are present and say what each function does. The comment in `_answered_at` explains why a wait ends up to one tick late.
       - Considered and not counted as a finding: `_hours` (`src/factory/domain/human_waits.py`) repeats the one-line conversion `Decimal(str(duration.total_seconds()))` from `bills._minutes`.
       - Why: the Interface limits `bills` to one public helper, `one_decimal(value: Decimal)`. Sharing the conversion would need a second public helper, which the human did not grant. The rule the story asks to share, the rounding, is shared. `make duplicates` reports 0 new findings.
    5. Work item hygiene:
       - The journal records the main choice (pass the state `handle` already checked into `_show`, not a second `require_state`) and what was rejected.
       - The Description matches what was built.
       - The docs criterion still describes what the documenter has to write.
       - Entry 12 suggested adding a criterion row for the `PositiveInt` limit. Leaving it out is fine: CLAUDE.md *Tests* already requires that test.

    Earlier tests:
    - `tests/application/handlers/test_hand_over.py`: changed under the feature's decision 13, fourth bullet (`_expected_post` passes the human line). Only the expected value changed.
    - `tests/application/test_stage_run_acceptance.py`: changed under the feature's decision 13, fifth bullet (the compared prompt tail grows from `[-3:]` to `[-4:]`). Nothing else changed.
    - `tests/application/test_task_acceptance.py`: changed under the feature's decision 13, fifth bullet (the compared prompt tail grows from `[-4:]` to `[-5:]`). Nothing else changed.
21. factory: started docs as self.
22. documenter: Docs round 1. No findings: the code matches the Interface and the criteria.

    Files changed (documents only, so I did not run `make check`; the factory's run after this stage decides):
    - `docs/project-guide.md`: a new subsection *The human's waits* under *Bills*. It covers `human_waits`, `human_line` and the rules of a wait and its end, including that a comment's record carries the time the factory copied it, so a wait ends up to one tick late. It also covers `cost_table_post(..., human=)` and how the two hand-overs and `AcceptanceService.facts` use it. In *Bills* I added `one_decimal` as the one rounding of the minutes and the hours. I updated the `AcceptanceFacts` paragraph (new field `human_line`, the extra line in `lines()`, the new `acceptance_facts` signature) and the line in the request section that lists the fact lines.
    - `docs/operator-guide.md`: *The cost table* now describes the `Human:` line (what it counts, that a close counts as an answer, the one-tick lateness, `factory-bill` unchanged). *When a feature acceptance is due* now describes the `Human interventions of the stories` line. *The hand-over at the approval* now mentions the `Human:` line after the cost table.

    Cross-read and found current: `README.md`, `docs/decisions.md` (nothing about this story), and the rest of both guides against the diff. I did not run the Smoke test commands; the new text is taken from the code and the criteria.

    Stale text noticed and left alone: none. From the earlier entries: `_hours` repeats a one-line conversion from `bills._minutes`, which the reviewer accepted. The `make duplicates` baseline has 3 findings reported as gone; the baseline is not mine to update.

    `check`: check: green
    `documents`: documents ok
23. factory: started smoke-test as self.
