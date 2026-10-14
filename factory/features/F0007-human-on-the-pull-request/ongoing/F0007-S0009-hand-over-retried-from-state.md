---
stage: tests
pr: 90
blocked: null
comments_seen: 2
round: 0
attempts: 0
---
# The hand-over at the approval, retried from state

## Assignment (as of log entry 1)

Build the handler of `hand_over` events. When a work item reaches an approval stage, the pull request must show the human what to decide: the handler assembles the pull request description by code from fixed sections of the story and the latest `result` entries of the tester, reviewer, documenter and smoke tester (found by speaker and kind in the journal's data, never by the text), replaces the description, marks the pull request ready for review, posts the cost table (read from the cost record file in the repository), and only then records `handed_over = <stage>` in the work item and pushes. Because the record comes last and every effect is safe to repeat (the description is replaced, the draft flag is set, the post is keyed), a failure or a kill anywhere leaves `handed_over` unset, the watcher raises the event again, and the next tick completes the hand-over without a second post. A hand-over that fails every time is reported on the pull request at the error cap. It covers ST1.2 and ST1.3, uses SI1.1 (speaker and kind as data) and keeps kept thing 11 (draft says the factory works, ready says the human decides) and kept thing 20 (the bill is posted at the approval). No morning observation.

## Interface

`src/factory/domain/sections.py` (adds one constant next to `ACCEPTANCE_CRITERIA` and `SMOKE_TEST`, in the same form)

```python
DESCRIPTION = "Description"
```

`src/factory/domain/hand_over.py`

```python
HAND_OVER_CLOSING = (
    "Merge to accept the story. To send it back, close the pull request with a comment that says "
    "what should change; a close without one is answered with a question. Comments written while "
    "the story waits here are recorded in its journal and become the reason if you then close."
)
REPORT_SECTIONS: tuple[tuple[str, str], ...] = (
    ("Tests", "tester"),
    ("Review", "reviewer"),
    ("Documentation", "documenter"),
    ("Smoke test", "smoke-tester"),
)

def hand_over_description(document: WorkItemDocument, commits: Sequence[CommitInfo]) -> str: ...
```

`src/factory/domain/post_texts.py` (adds one function)

```python
def cost_table_post(table: str) -> str: ...
```

`src/factory/application/handlers/hand_over.py`

```python
class HandOverHandler(Handler):      # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

Rules:

- `cost_table_post(table)` is `Cost of this work item so far`, a blank line, and the table.
- `hand_over_description(document, commits)` is made of these parts, in this order, joined by one blank line, and ends with one newline:
  1. a line `## Description`, a blank line, and `section_text(document.body, DESCRIPTION)`;
  2. a line `## Acceptance criteria`, a blank line, and `section_text(document.body, ACCEPTANCE_CRITERIA)`;
  3. for each `(title, speaker)` in `REPORT_SECTIONS`, in that order: a line `## <title>`, a blank line, and the text of the work item's latest journal record with that speaker and kind `result` (found with `last_record(document, speaker=speaker, kind="result")`, its text read with `entry_text`);
  4. a line `## Commits`, a blank line, and a fenced block: a line of three backticks with no info string, one line per commit in the order given (the first seven characters of the commit id, a space, and the subject), and a closing line of three backticks; with no commit the two fence lines follow each other with nothing between;
  5. `HAND_OVER_CLOSING`.
  A section that is missing or present but empty (`section_text` returns `None` for the first and `""` for the second), and a speaker with no `result` record, give the text `none`.
- `HandOverHandler.handle` takes `target_of(event)` and `require_pull_request(target, "hand_over")`. It calls `WorkItemRecorder.check_out(branch)` and reads the work item. A stage that is not an approval stage of `definition` raises `CannotHandle("hand_over", ...)`. When `state.handed_over == state.stage` there is nothing to do and it returns without any effect.
- Otherwise, in this order: read the cost records from `cost_records_path(snapshot.path)` in the checkout (after `check_out` it holds `origin/<branch>`'s file, whatever sidecar was there before); take `Git.log("origin/<branch>", since="origin/main")` as the commits; `HostingService.set_description(number, hand_over_description(...))`; `HostingService.set_draft(number, False)`; post `cost_table_post(cost_table(bills_by_stage(records)))` with `PostKey(work_item=<id>, kind="cost_table", n=str(<number of the latest record of kind result, 0 when there is none>))`; and last, set `handed_over` to the stage and record with the subject `commit_subject(id, "handed over at <stage>")`.
- Every failure leaves `handle` by raising. Nothing is recorded before the last step.

Tests: `tests/domain/test_hand_over.py` and `tests/application/handlers/test_hand_over.py`. The journal records of the test documents are built independently of the body's visible text; the dispatcher tests are built as in S0008 (the wrapper that counts calls subclasses `Handler`).

## Acceptance criteria

1. `hand_over_description` contains the headings `## Description`, `## Acceptance criteria`, `## Tests`, `## Review`, `## Documentation`, `## Smoke test` and `## Commits`, in that order, with `HAND_OVER_CLOSING` as its last paragraph, and ends with one newline.
2. The Description and Acceptance criteria sections hold the story's own sections, verbatim; a section the story lacks, and a section that is present but empty, each give `none` (two cases, one test).
3. A report section holds the text of the latest `result` record by its speaker; when the tester has two `result` records, the later one is used.
4. A report section whose speaker has no `result` record holds `none`.
5. A report section is found by the records' data and not by the visible text: an entry whose visible line names another speaker is still attributed to the speaker in its record.
6. The Commits section is a fenced block (a line of three backticks, the commit lines, a line of three backticks) with one line per commit in the order given, each the first seven characters of the id, a space and the subject; with no commit the two fence lines follow each other with nothing between.
7. `cost_table_post("T")` is `Cost of this work item so far`, a blank line and `T`.
8. `HAND_OVER_CLOSING` is exactly the text of the Interface and states that a merge accepts, that a close with a comment sends the story back, and that a close without one is answered with a question.
9. `HandOverHandler.handle` for a work item at the approval sets the pull request's description to `hand_over_description` of the work item and of `Git.log("origin/<branch>", since="origin/main")`, and marks the pull request ready for review (not a draft).
10. It posts one comment on the pull request: `cost_table_post(cost_table(bills_by_stage(records)))` of the cost records committed on the work item's branch, with key kind `cost_table` and `n` equal to the number of the latest `result` record; the table is computed from the cost record file at `origin/<branch>`, not from the checkout's working copy of it: a local sidecar that differs and was in the checkout before `check_out` does not change the posted text; for a work item with no `result` record the key's `n` is `0`.
11. It then records `handed_over == <stage>` in the work item and pushes: the remote branch gains one commit, and the journal and the other state fields are as they were.
12. The record comes last: when `post_comment` fails, `handle` raises `HostingServiceError`, the description is already set, and the remote branch holds no `handed_over`.
13. After that failure, handling the event again completes the hand-over and leaves exactly one cost table post (ST1.2).
14. A kill at `after-post` leaves one cost table post and no `handed_over`; handling the event again records `handed_over` and leaves exactly one cost table post.
15. A work item whose `handed_over` already equals its stage is handled without any effect: no description change, no post, no commit.
16. A work item at a stage that is not an approval raises `CannotHandle` with kind `hand_over`, and nothing is changed or posted.
17. For a work item whose state has no pull request, `handle` raises `CannotHandle` with kind `hand_over`, and nothing is changed or posted.
18. A hand-over that fails every time (ST1.3), dispatched four times on the same remote state, gives the outcomes `error`, `error`, `reported`, `capped`; the handler is called three times; the pull request has no factory post of kind `error` after the second dispatch, exactly one after the third and still exactly one after the fourth.
19. make check stays green.
20. docs: `docs/operator-guide.md` describes the pull request description at the approval (its sections, that it replaces what the human wrote there), the cost table post, that a hand-over that fails is retried on the next tick and reported once at the error cap.

## Demo

```bash
uv run python -c "
from datetime import UTC, datetime
from factory.domain.git import CommitInfo
from factory.domain.hand_over import HAND_OVER_CLOSING, hand_over_description
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, WorkItemState
records = [JournalRecord(number=1, speaker='human', kind='created'), JournalRecord(number=2, speaker='tester', kind='result')]
body = '# T\n\n## Description\n\nBuild it.\n\n## Acceptance criteria\n\n1. One.\n\n## Journal\n\n1. 2026-10-12 human: created.\n2. tester: wrote the tests.\n'
document = WorkItemDocument(state=WorkItemState(stage='approval', journal=records), body=body)
commit = CommitInfo(commit='a' * 40, parents=[], subject='feat: build it', author='coder', committed_at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC))
text = hand_over_description(document, [commit])
print([line for line in text.splitlines() if line.startswith('## ')])
print(text.split('## Tests')[1].split('## Review')[0].strip())
print(text.split('## Review')[1].split('## Documentation')[0].strip())
print('aaaaaaa feat: build it' in text, text.rstrip().endswith(HAND_OVER_CLOSING))
"
```
Expect: four lines: `['## Description', '## Acceptance criteria', '## Tests', '## Review', '## Documentation', '## Smoke test', '## Commits']`; then `wrote the tests.`; then `none` (no reviewer record); then `True True`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: concrete modules and signatures are named (`domain/sections.py`, `domain/hand_over.py`, `domain/post_texts.py`, `application/handlers/hand_over.py`). The rules fix the section order, the `none` cases, the fence format, the post key and the order of effects.
   - Criteria: each one fits a single test function. Each Interface behaviour has a criterion: order and closing text (1, 8), the verbatim sections and the `none` cases (2, 4), the latest `result` record (3), speaker read from data (5), the fence and the empty-commit case (6), `cost_table_post` (7), the effects and the key (9-11). Each rule has its failing side: a post failure (12, 13), a kill (14), already handed over (15), a non-approval stage (16), no pull request (17) and the error cap (18).
   - Demo: runnable as written. Each `Expect:` line can be checked against the output.
   - Architecture: the pure text builders sit in the domain layer. The handler sits in application and uses the Boundaries and hosting interfaces. It calls no tool directly.
   - Scope: the story is within F0007's "hand-over at the approval" scope item. It touches nothing listed under Out of scope.
3. tester: wrote the red tests for the hand-over at the approval.

   Criterion → test:
   - criterion 1: tests/domain/test_hand_over.py::test_the_description_has_its_headings_in_order_and_ends_with_the_closing_paragraph
   - criterion 2: tests/domain/test_hand_over.py::test_the_description_and_criteria_sections_hold_the_story_sections_verbatim (verbatim, multi-line with an inner blank line and indentation) and ::test_a_missing_or_empty_story_section_gives_none (parametrized: missing, empty)
   - criterion 3: tests/domain/test_hand_over.py::test_each_report_section_holds_the_latest_result_text_of_its_speaker
   - criterion 4: tests/domain/test_hand_over.py::test_a_report_section_whose_speaker_has_no_result_record_holds_none (parametrized over REPORT_SECTIONS; the speaker has only a `question` record)
   - criterion 5: tests/domain/test_hand_over.py::test_a_report_section_is_found_by_the_record_and_not_by_the_visible_speaker
   - criterion 6: tests/domain/test_hand_over.py::test_the_commits_section_is_a_fenced_block_of_short_ids_and_subjects (parametrized: two commits, no commit)
   - criterion 7: tests/domain/test_hand_over.py::test_the_cost_table_post_is_a_heading_line_a_blank_line_and_the_table
   - criterion 8: tests/domain/test_hand_over.py::test_the_closing_paragraph_says_how_to_accept_send_back_and_what_a_bare_close_does
   - criterion 9: tests/application/handlers/test_hand_over.py::test_the_hand_over_sets_the_description_and_marks_the_pull_request_ready
   - criterion 10: tests/application/handlers/test_hand_over.py::test_the_hand_over_posts_the_cost_table_of_the_branch_records_keyed_by_the_latest_result (parametrized: latest result n=3, no result n=0; an untracked, differing sidecar is written into the checkout before handling)
   - criterion 11: tests/application/handlers/test_hand_over.py::test_the_hand_over_then_records_handed_over_in_one_commit_and_changes_nothing_else (also checks the subject `commit_subject(id, "handed over at approval")` from the Interface rule)
   - criterion 12: tests/application/handlers/test_hand_over.py::test_a_failing_post_raises_after_the_description_and_before_any_record
   - criterion 13: tests/application/handlers/test_hand_over.py::test_after_a_failing_post_the_next_handling_completes_with_one_cost_table_post
   - criterion 14: tests/application/handlers/test_hand_over.py::test_a_kill_after_the_post_leaves_one_post_and_the_next_handling_records_without_another
   - criterion 15: tests/application/handlers/test_hand_over.py::test_a_work_item_already_handed_over_at_its_stage_is_handled_without_any_effect
   - criterion 16: tests/application/handlers/test_hand_over.py::test_a_work_item_at_a_stage_that_is_not_an_approval_cannot_be_handed_over (stage `smoke-test` of PIPELINE_YAML)
   - criterion 17: tests/application/handlers/test_hand_over.py::test_a_work_item_without_a_pull_request_cannot_be_handed_over
   - criterion 18: tests/application/handlers/test_hand_over.py::test_a_hand_over_that_always_fails_is_tried_three_times_and_reported_once (the failure is `set_description` failing every time; the `Counting` wrapper subclasses `Handler`, as in S0008)
   - criteria 19 and 20: not test criteria (make check, docs).

   Files created: tests/domain/test_hand_over.py, tests/application/handlers/test_hand_over.py. The journal records in the test documents are built by hand, separately from the visible journal lines. The handler tests use the definition from `PIPELINE_YAML`, a real bare remote, and the fake hosting service with its `fail_next` and the `after-post` kill point.

   The test runner could not import `factory.domain.hand_over` or `factory.application.handlers.hand_over`, so both files fail at collection. `make test` stops with 2 collection errors, which is the expected red state. The tests also import `DESCRIPTION` from `factory.domain.sections` and `cost_table_post` from `factory.domain.post_texts`, which don't exist yet either. `make lint` is green.

   Open: tests/application/handlers/test_handlers_raise.py lists the handler modules in `REQUIRED`, and `hand_over` isn't in that list. Its module walk will still pick up the new module, so I left that test alone because it isn't mine.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: question. An existing test contradicts the Interface, and I have not changed it.

   Built and committed in 82ef94e:
   - `src/factory/domain/hand_over.py`: `HAND_OVER_CLOSING`, `REPORT_SECTIONS` and `hand_over_description`.
   - `DESCRIPTION` in `src/factory/domain/sections.py`.
   - `cost_table_post` in `src/factory/domain/post_texts.py`.
   - `src/factory/application/handlers/hand_over.py`: `HandOverHandler`. It checks out the branch, refuses a stage that is not an approval, and returns at once when `handed_over == stage`. Otherwise it reads the cost records from the checkout, then calls set_description, set_draft(False) and the keyed post, and records `handed_over` last.

   All 25 tests in `tests/domain/test_hand_over.py` and `tests/application/handlers/test_hand_over.py` pass.

   `make check` is red on one test: `tests/test_no_journal_reading.py::test_no_module_reads_data_from_the_journal_text` reports `factory.domain.hand_over references entry_text`. That test's `ALLOWED["entry_text"]` set permits `factory.application.handlers.hand_over` but not `factory.domain.hand_over`. The Interface does the opposite: `hand_over_description(document, commits)` in the domain reads each report's text "with `entry_text`", and the domain tests call it with only a document and commits. So the text has to be read in the domain module.

   Options:
   1. (I recommend this.) The tester changes `ALLOWED["entry_text"]` in `tests/test_no_journal_reading.py`, replacing `factory.application.handlers.hand_over` with `factory.domain.hand_over`. The use is for display only: the speaker is still found from the record's data, which is what that test protects.
   2. I add a helper in `factory.domain.journal`, for example `latest_result_text(document, speaker)`, and the domain module calls that instead. The test passes with no change, but it gets around the allow list rather than respecting it.
   3. Change the Interface so the handler reads the texts and passes them to `hand_over_description`. That changes the signature and the domain tests.

   Refactor step: not done yet, because the check is red.
5. human (pull request comment, 2026-10-14): 1: the tester changes `ALLOWED["entry_text"]` in `tests/test_no_journal_reading.py` (F0005-S0009's test), replacing `factory.application.handlers.hand_over` with `factory.domain.hand_over`, and changes nothing else in that file. The Interface puts the reading in the domain, and the use is for display only; the speaker is still taken from the record's data. This is the human's word for that one change. End with `tests` and name exactly that change.
6. coder: tests. The human answered in log entry 5. In `tests/test_no_journal_reading.py`, in `ALLOWED["entry_text"]` (line 12), replace `"factory.application.handlers.hand_over"` with `"factory.domain.hand_over"` and change nothing else in that file.

   The implementation is already in 82ef94e and I did not change it. Once the test is changed, `make check` should go green. The refactor step is still to do: I will do it on the next doing run, when the check is green.
