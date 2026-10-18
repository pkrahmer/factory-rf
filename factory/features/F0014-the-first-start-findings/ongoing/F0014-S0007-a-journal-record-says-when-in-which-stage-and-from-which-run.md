---
stage: demo
pr: 199
blocked: null
comments_seen: 4
round: 1
attempts: 0
---
# A journal record says when, in which stage and from which run

## Assignment (as of log entry 1)

The status map is a viewer that reads GitHub only (the human's word of 2026-10-17, `planning/overnight/first-start-checklist.md`, "Results", item 6). It can already read a work item's place, its `WorkItemState`, its claim, its cost records and the story form's sections. It cannot tell from a journal record when the entry was written, in which stage, or which agent run it came from: `JournalRecord` (`src/factory/domain/journal.py`) holds only `number`, `speaker` and `kind` (the decision log's "The journal's speaker and kind are data in the front matter, not read from the text", SI1.1). The human's word: `JournalRecord` gains `at` (UTC, when the entry was written, from the factory's clock through the existing `Clock` of the `Boundaries`), `stage` (the stage the work item was in when the entry was written) and `run` (the agent run's id the entry came from, `None` for an entry that comes from no run). The three are optional when read, so every record written before this story stays valid with no migration. Every entry the factory appends from now on carries `at` and `stage`, and `run` when it came from a run. `append_entry` stays the one writer of both halves of the journal: it takes the time and the run from its caller and the stage from the document's state. Every place in `src/factory` that appends an entry passes them. The front matter writer leaves out an unset field of a journal record, so an old record is written back exactly as it was read and the pinned layout of the file stays. No marker in the body and no change to the pull request. The cost record's `instance` is S0008. Twenty-six tests of earlier stories in thirteen modules change by the human's leave (FEATURE decision 27): only their expected records gain the new fields, or a call that builds an expected document gains `at`.

## Interface

`src/factory/domain/journal.py`:

- `JournalRecord` gains three fields after `kind`, in this order, each with the default `None`:

  | Field | Type | Meaning |
  |---|---|---|
  | `at` | `UtcDatetime \| None` (`factory.domain.times`) | when the entry was written; an aware time, stored in UTC; a naive time is refused |
  | `stage` | `Name \| None` (`factory.domain.identifiers`) | the stage of the work item's state when the entry was written |
  | `run` | `RunId \| None` (`factory.domain.cost_records`, 32 lowercase hexadecimal characters) | the id of the agent run the entry came from, the `run` of that run's cost record |

  The model stays frozen and refuses unknown keys. It has no rule that ties the three fields to one another: a reader accepts each alone. Its docstring names the three fields.
- `append_entry(document: WorkItemDocument, entry: NewEntry, *, at: datetime | None = None, run: RunId | None = None) -> WorkItemDocument`. With `at` given, the new record carries `at`, `stage` = the `stage` of `document.state` as given to the call, and `run` as given. Without `at`, the record carries none of the three, exactly as today. `run` given without `at` raises `ValueError("an entry with a run needs the time it was written")` before anything else. The rendered entry in the body does not change: no time, stage or run is shown there. `NewEntry` does not change.

`src/factory/domain/acceptance.py`: `book_merge(document, bill, *, before_approval=False, at: datetime | None = None)` and `book_refusal(document, *, role, on, bill, at: datetime | None = None)` pass `at` on to the `append_entry` of their `done` entry. Nothing else in the module changes.

`src/factory/adapters/work_item_markdown.py`: `FrontmatterWorkItemWriter.render` leaves out, in each element of `journal`, the keys `at`, `stage` and `run` whose value is `None`. Every other key is written as today (`claim: null`, `pull_request: null` and the rest stay). `at` is written like `claim.started_at`: single-quoted UTC text in `isoformat()` form ending in `Z`. A record with all three:

```yaml
- number: 2
  speaker: tester
  kind: result
  at: '2026-10-17T20:31:00Z'
  stage: tests
  run: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

The reader is unchanged: a record without the keys reads with `None`.

Every place that appends an entry passes `at` and `run` (the stage comes from the state it appends to):

| Module, method | Entry | `at` | `run` |
|---|---|---|---|
| `application/opening.py` `WorkItemOpening` (the new document) | `created` | `clock.now()` (the same reading as `on`) | `None` |
| `application/claims.py` `ClaimService._with_claim` | `started` | the claim's `started_at` | `None` |
| `application/stage.py` `AfterAgent.process` (the `form_invalid` stall) | the role's entry | `clock.now()` | `launched.cost.run` |
| `application/stage.py` `StageFinisher.finish` | the role's entry, and the factory's `question` of the move | `clock.now()` | `aftermath.cost.run` |
| `application/stage.py` `StageFinisher._stall_red` | the role's entry | `clock.now()` | `aftermath.cost.run` |
| `application/stalls.py` `StallService._stalled` | `stall` | `clock.now()` | the run of `context.cost`, `None` when `cost` is `None` |
| `application/recovery.py` `RecoveryHandler._crash_recorded` | `crash` or `expiry`, and the crash cap's `question` | `clock.now()` | `None` |
| `application/acceptance.py` (the human's close) | `close` | `clock.now()` | `None` |
| `application/acceptance.py` (the calls of `book_merge` and `book_refusal`) | `done` | `clock.now()` | `None` |
| `application/handlers/closed.py` `ClosedHandler` | `close`, `send_back`, `question` | `clock.now()` | `None` |
| `application/handlers/questions.py` `AskHandler` | `question` | `clock.now()` | `None` |
| `application/handlers/comments.py` `CommentCopier.append` | each `comment` | `clock.now()` | `None` |
| `application/handlers/reject.py` `RejectHandler._moved_back` | `move_back` | `clock.now()` | `None` |
| `application/handlers/merged.py` `MergedHandler._archived` | `done` | `clock.now()` | `None` |

`clock` is `self._boundaries.clock` in each. The `stage` each record gets follows from where the call stands: the entries of a stage's end carry the stage that ran; the `move_back` entry carries the stage the human set, since it is appended before the move back; the story's `done` entry carries the stage it was merged in, since `_archived` appends before it sets `done`; the acceptance's `done` entry carries `done`, since `_booked` sets the stage first (FEATURE decision 26). No call site changes its order.

Tests: new modules `tests/domain/test_journal_stamps.py`, `tests/adapters/test_journal_stamps_file.py` and `tests/application/test_journal_stamps.py` (or new test functions in the existing modules of the services the table names: adding a function changes no earlier test). By the human's leave (FEATURE decision 27, which gives every line), and no other change to an earlier story's test, these twenty-six tests in thirteen modules change only in their expected records (a `JournalRecord`, or a state holding one, for an entry the code under test appends), which gain the `at` and `stage` the table gives, or in the `at=` of a call that builds an expected document; their names and every other assertion stay:

- `tests/application/test_claims.py`: `test_claim_appends_one_started_journal_entry`
- `tests/application/test_opening.py`: `test_new_document_starts_at_the_first_stage`, `test_backlog_front_matter_is_dropped`, `test_new_document_journal_holds_the_created_entry`
- `tests/application/test_stage_launch.py`: `test_the_stage_start_commit_of_a_new_work_item_is_its_opening_commit`
- `tests/application/test_stalls.py`: `test_the_agents_rewrite_of_the_state_and_journal_is_put_back`, `test_the_journal_gains_one_stall_entry_of_the_factory_naming_the_cause`, `test_a_given_document_keeps_its_entries_above_the_stall_entry`
- `tests/application/test_recovery_expiry.py`: `test_the_journal_ends_with_a_factory_expiry_entry_naming_the_stage_start`, `test_at_the_cap_the_note_and_then_the_question_are_posted_and_nothing_reruns`
- `tests/application/test_recovery_crash.py`: `test_the_journal_ends_with_one_factory_crash_record`
- `tests/application/test_recovery_cap.py`: `test_the_crash_commit_at_the_cap_holds_the_crash_and_the_question_and_nothing_else`
- `tests/application/test_acceptance_closed.py`: `test_a_closed_acceptance_is_booked_refused_in_done_and_nothing_else_reaches_main` (its expected file is built with `append_entry` and `book_refusal`, which gain `at=`)
- `tests/application/test_acceptance_merged.py`: `test_a_merged_acceptance_is_booked_accepted_in_done_with_its_cost_records` (its expected file is built with `book_merge`, which gains `at=`)
- `tests/application/handlers/test_merged.py`: `test_the_archived_state_is_done_unblocked_and_unclaimed_and_keeps_the_rest`, `test_a_story_is_archived_the_same_way_at_whatever_stage_it_was_merged`, `test_the_archive_appends_one_done_entry_of_the_factory_with_the_bill`
- `tests/application/handlers/test_questions.py`: `test_at_the_attempts_cap_the_question_is_recorded_in_one_pushed_commit`, `test_the_attempts_cap_question_is_recorded_before_a_failing_post`
- `tests/application/handlers/test_comments.py`: `test_append_adds_one_dated_human_comment_entry_per_comment_in_order`
- `tests/application/handlers/test_reject.py`: the module constant `MOVE_BACK` gains `at` and `stage`, which changes the expectation of six tests (`test_the_correction_appends_one_move_back_entry_by_the_factory`, `test_without_a_pull_request_nothing_is_posted_and_the_stage_is_still_moved_back`, `test_a_kill_before_the_push_leaves_the_branch_and_a_second_run_corrects_once`, `test_a_kill_after_the_post_leaves_the_branch_and_a_second_run_posts_no_second_note`, `test_an_illegal_change_followed_by_a_commit_to_another_file_is_moved_back`, `test_a_failing_label_call_raises_and_the_correction_stays_on_the_branch`) and the given state of `test_a_stage_change_that_is_itself_a_correction_is_refused`, which stays green with it.

Every other direct call of `append_entry`, `book_merge` or `book_refusal` in the tests stays as it is: it compares its own result, or builds given data, and its records carry none of the three fields, as before.

## Acceptance criteria

1. A journal record without `at`, `stage` and `run` is valid and reads with each `None`; one with `at` = 2026-10-17 20:31 UTC, `stage` = `tests` and `run` = 32 times `a` reads with those values. `at` given at 22:31 with the offset +02:00 is stored as 20:31 UTC. A naive `at`, a `stage` that is not a `Name` (`Tests`), and a `run` of 31 characters, of 33 characters, with an uppercase letter or with a lowercase letter that is not hexadecimal (`g`) are refused, and 32 lowercase hexadecimal characters are accepted. One parametrized test holds every row (wrong-typed values constructed through a variable typed `type[BaseModel]`).
2. `append_entry` with `at` gives the new record `at`, the `stage` of the document's state, and `run` (`None` when not given); without `at` the record has none of the three, as today; `run` without `at` raises `ValueError` with the message of the Interface and the document is not changed, and so it does for a document without a state (the `ValueError`, not `WorkItemFormatError`). The rendered entry in the body is the same in each row that appends. One parametrized test holds the five rows (neither, `at` alone, `at` and `run`, `run` alone, `run` alone on a document without a state).
3. The writer writes a journal record that has `at`, `stage` and `run` with the three keys after `kind`, `at` single-quoted ending in `Z`, as in the Interface; a record with `at` and `stage` and no `run` without a `run` key; a record without the three with exactly the keys `number`, `speaker` and `kind`; a record whose `run` a YAML reader would take for a number (32 times `1`) with the `run` single-quoted. For each row `parse(render(document))` equals the document. One parametrized test holds the rows.
4. A work item file written before this story (records with `number`, `speaker` and `kind` only) reads, and its records have `at`, `stage` and `run` `None`; written back unchanged, its text is the same as before. A file with the three keys reads with their values. One parametrized test holds both sides.
5. Every entry the table of the Interface names is recorded with `at` from the factory's clock (the claim's `started_at` for `started`), the `stage` the Interface gives and the `run` it gives, tested through the services with the `ManualClock` of `tests/conftest.py`. The changed tests of FEATURE decision 27 pin `created`, `started`, the `stall` of a stall without a run, `crash`, `expiry` and the crash cap's `question`, the ask handler's `question`, `comment`, `move_back`, the story's `done` at each stage it was merged in, and the acceptance's `close` and `done`. New tests pin the rest, one test function each: (a) a stage's end whose decision asks a question: the role's entry and the factory's `question` both carry the stage that ran and the run of the stage's cost record (`aftermath.cost.run`), and the `started` entry of the same work item carries no run; (b) a stage's end with a red check: the role's entry and the `stall` both carry that run; (c) a stage whose agent leaves a new form finding (`form_invalid`): the role's entry and the `stall` both carry `launched.cost.run`; (d) a stall with no `cost` in its `StallContext`: the `stall` carries `at` and the stage, and no run; (e) a close of the pull request that sends the work item back with a question: the human's `close`, the factory's `send_back` and its `question` carry `at`, the stage the work item was in when it was closed, and no run.
6. `book_merge` and `book_refusal` given `at` record the `done` entry with it and `stage` = `done`; without `at` they record it as today.
7. What must still hold: the journal's two halves stay in step; the form check, `restore_state_and_journal`, `last_record` and the readers of the journal's data work on records with and without the new fields (the tests of `tests/domain/test_journal.py`, `tests/domain/test_journal_records.py`, `tests/adapters/test_work_item_markdown.py`, `tests/adapters/test_journal_as_data.py` and `tests/test_no_journal_reading.py` pass).
8. `make check` stays green.
9. docs: the project guide's *The data of a work item*, part *The journal's data*, names the three fields (types, optional when read, set for every new entry, where `at`, `stage` and `run` come from, the `stage` of a `move_back` and of a `done` entry); *The journal's entries* says that `append_entry` takes `at` and `run` and the stage from the state, and the printed record of its example becomes `number=2 speaker='intake' kind='result' at=None stage=None run=None`; *Reading and writing a work item file*, *The layout*, says that a journal record's `at`, `stage` and `run` are left out when unset, shows one record with them, and says that a `run` a YAML reader would take for a number is single-quoted. The decision log gets one entry, "Journal records say when, in which stage and from which run; cost records on which instance" (the human's word of 2026-10-17 for the status map, which reads GitHub only; optional when read, no migration; why an unset field is left out of the file rather than written `null`; why the stage comes from the state and the time from the `Clock`; which entries carry a run), and the entry of SI1.1 ("The journal's speaker and kind are data in the front matter") gets one sentence pointing to it. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from datetime import UTC, date, datetime
from factory.adapters.work_item_markdown import FrontmatterWorkItemWriter
from factory.domain.journal import NewEntry, append_entry
from factory.domain.work_item import WorkItemDocument, initial_state
doc = WorkItemDocument(state=initial_state('tests'), body='# T\n\n## Journal\n')
doc = append_entry(doc, NewEntry(speaker='human', kind='created', text='created.', on=date(2026, 10, 17)))
doc = append_entry(doc, NewEntry(speaker='tester', kind='result', text='tests written.'), at=datetime(2026, 10, 17, 20, 31, tzinfo=UTC), run='a' * 32)
text = FrontmatterWorkItemWriter().render(doc)
print(text[text.index('journal:'):text.index('---', 4)], end='')
"
```
Expect: ten lines: `journal:`, `- number: 1`, `  speaker: human`, `  kind: created`, `- number: 2`, `  speaker: tester`, `  kind: result`, `  at: '2026-10-17T20:31:00Z'`, `  stage: tests`, `  run: ` followed by 32 times `a`. The first record has no `at`, `stage` or `run` line.

```bash
uv run pytest --no-header -p no:cacheprovider tests/domain/test_journal_stamps.py tests/adapters/test_journal_stamps_file.py tests/domain/test_journal.py tests/adapters/test_work_item_markdown.py tests/application/test_stage_finish.py tests/application/test_after_agent.py tests/application/test_stalls.py tests/application/test_claims.py tests/application/test_opening.py tests/application/handlers/test_closed_send_back.py tests/application/handlers/test_reject.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted. I read the story and the feature's FEATURE.md. The format check passed.
   - Interface: it names concrete modules and signatures. These are the three `JournalRecord` fields with their types and defaults, `append_entry(document, entry, *, at, run)`, the `book_merge` and `book_refusal` `at` parameter, and the writer's omission rule with a YAML example. It also has a table of 14 call sites that gives the `at`, `stage` and `run` of each. The ordering notes (`move_back`, the story's `done`, the acceptance's `done`) are stated precisely. Each behaviour in an Interface comment has a criterion: UTC storage and naive refusal in 1, the stage taken from the state in 2, the `Z` text and the single-quoted numeric-looking `run` in 3, and the call-site stamps in 5.
   - Criteria: each is testable by named tests, and the parametrized rows are listed. Every rule has its failing side. Criterion 1 refuses a naive `at`, `Tests` as a stage, and runs of 31 chars, 33 chars, uppercase and `g`, and accepts 32 hex chars. Criterion 2 has `run` without `at`, also on a document without a state. Criterion 4 covers the old files. Criterion 5 pins each call site, with five new named tests (a) to (e) for the paths the changed tests do not cover. Criterion 5 is long, but each of its parts names its own test. I did not change it.
   - Demo: both commands run. Expect lines are checkable: ten named lines, with the first record having no new keys, and the pytest command ends in `<n> passed` with no failures or skips.
   - Architecture: domain gets the record and `append_entry`, adapters get the writer, and application gets the call sites, with the clock reached through `Boundaries`. The domain gets no clock because `at` is a parameter. This matches the layers in CLAUDE.md.
   - Scope: the story is within the feature's scope (the status-map data, decisions 25 to 27, and the stories S0007 and S0008). The cost record's `instance`, the body markers, any change to the pull request and a `run` on `crash` and `expiry` are out of scope and are not touched. The 26 changed earlier tests are covered by the human's leave in decision 27, which gives every line.
3. tester: Tests written from the Interface and the criteria. They are red on purpose. `make lint` is green. I ran `make test` once: it fails, and `tests/application/handlers/test_reject.py` fails at collection because its module constant `MOVE_BACK` now builds a `JournalRecord` with `at` and `stage`, which the model forbids until those fields exist. Every other new or changed expectation fails because a field is missing (`at`, `stage`, `run`) or `append_entry`, `book_merge` and `book_refusal` don't take the `at`/`run` keywords yet. No module is missing: all three new test modules import names that already exist.

   Criterion → test:
   - criterion 1: tests/domain/test_journal_stamps.py::test_a_journal_record_reads_its_time_stage_and_run_when_valid. The rows are: none of the three, all three, +02:00 stored as UTC, 32 hex accepted, naive `at`, stage `Tests`, run of 31, run of 33, uppercase, `g`. It builds the record through `type[BaseModel]`.
   - criterion 2: tests/domain/test_journal_stamps.py::test_append_entry_stamps_the_record_with_the_time_the_state_stage_and_the_run. The five rows are neither, `at` alone, `at`+`run`, `run` alone, and `run` alone without a state. The `ValueError` message is matched exactly, the document is left unchanged, and the body line is the same in each row that appends.
   - criterion 3: tests/adapters/test_journal_stamps_file.py::test_the_writer_writes_a_records_time_stage_and_run_only_when_set. The rows are all three, no run, none of the three, and the numeric-looking run `'111…'` single-quoted. Each row checks the whole text and the round trip `parse(render(doc)) == doc`.
   - criterion 4: tests/adapters/test_journal_stamps_file.py::test_a_work_item_file_reads_with_and_without_the_stamps_and_is_written_back_the_same. It has an old file and a stamped file, and each is written back byte for byte.
   - criterion 5 (new tests):
     (a) tests/application/test_stage_finish.py::test_a_stage_end_that_asks_a_question_stamps_both_entries_with_the_stage_and_its_run. This uses the findings question of the move. The role's `result` and the factory's `question` carry `aftermath.cost.run`, and `started` has no run.
     (b) tests/application/test_stage_finish.py::test_a_red_check_stamps_the_entry_and_the_stall_with_the_stages_run
     (c) tests/application/test_after_agent.py::test_a_new_form_finding_stamps_the_entry_and_the_stall_with_the_launched_run
     (d) tests/application/test_stalls.py::test_a_stall_without_a_cost_stamps_its_entry_with_the_time_and_stage_and_no_run
     (e) tests/application/handlers/test_closed_send_back.py::test_a_send_back_with_a_question_stamps_its_entries_with_the_stage_closed_at_and_no_run
   - criterion 5 (changed tests under FEATURE decision 27): only the expected records gain `at=clock.now()` (the ManualClock fixture) and the table's `stage`, or the expected-document calls gain `at=`. The changes are in:
     - test_claims::test_claim_appends_one_started_journal_entry
     - test_opening, its three tests (`created` at stage `intake`)
     - test_stage_launch::test_the_stage_start_commit_of_a_new_work_item_is_its_opening_commit
     - test_stalls, its three tests
     - test_recovery_expiry, its two tests, and test_recovery_crash, its one test. The stage there is `before.stage`.
     - test_recovery_cap::test_the_crash_commit_at_the_cap_…
     - test_acceptance_closed: `at=` on the comment and close `append_entry` calls and on `book_refusal`
     - test_acceptance_merged: `at=` on `book_merge`
     - handlers/test_merged, its three tests. The stage is the one the story was merged in: `doing`, the parametrized stage, and `approval`.
     - handlers/test_questions, its two tests (stage `doing`)
     - handlers/test_comments::test_append_adds_one_dated_human_comment_entry_per_comment_in_order
     - handlers/test_reject: `MOVE_BACK` gains `at=2026-10-12 12:00 UTC` and `stage="doing"`, the stage the human set.

     Where a test needed it, the `clock: ManualClock` fixture parameter and its import were added. Test names and other assertions are unchanged.
   - criterion 6: tests/domain/test_journal_stamps.py::test_booking_records_the_done_entry_with_the_time_and_the_done_stage (merge and refusal, each with and without `at`)
   - criterion 7: covered by the existing tests the criterion names. No new test.
   - criteria 8 and 9: not tests (the gate, and docs).

   Files created: tests/domain/test_journal_stamps.py, tests/adapters/test_journal_stamps_file.py.

   Files changed:
   - New test functions in tests/application/test_stage_finish.py, test_after_agent.py, test_stalls.py and handlers/test_closed_send_back.py.
   - The decision-27 edits in the files listed above.
   - Formatting by `ruff format`, which also reformatted some of the lines I edited.

   What the coder should know:
   - In (e), the `question` after a send-back is expected to carry the approval stage the item was closed in, as the criterion says, even though `send_back` moves the stage.
   - In test_acceptance_closed, the copied `comment` entry is expected with `at=clock.now()`, following the CommentCopier row of the table.

   `make lint`: lint: green (0.0 s)
   `make test`: ERROR tests/application/handlers/test_reject.py - pydantic_core._pydantic_cor...
4. coder: Question: one test and the Interface disagree about the `stage` of the `move_back` entry. Which stage should the record carry?

   The Interface says: "the `move_back` entry carries the stage the human set, since it is appended before the move back". `append_entry` takes the stage from the document's state, and "no call site changes its order". In the tests of `tests/application/handlers/test_reject.py`, the human's illegal change goes from `doing` to `approval`, so at the moment of the append the state's stage is `approval`. The test's module constant `MOVE_BACK` expects `stage="doing"` instead, which is the stage the work item is moved back to. The tester's entry calls `doing` "the stage the human set". Because of this, six tests fail with `stage='approval' != 'doing'`: `test_the_correction_appends_one_move_back_entry_by_the_factory`, `test_without_a_pull_request_nothing_is_posted_and_the_stage_is_still_moved_back`, `test_a_kill_before_the_push_leaves_the_branch_and_a_second_run_corrects_once`, `test_a_kill_after_the_post_leaves_the_branch_and_a_second_run_posts_no_second_note`, `test_an_illegal_change_followed_by_a_commit_to_another_file_is_moved_back` and `test_a_failing_label_call_raises_and_the_correction_stays_on_the_branch`. Every other test passes, and lint, types and layers are green.

   Options:
   - (A) Keep the Interface: `move_back` carries the stage the human set (`approval`). The tester changes `MOVE_BACK` in `tests/application/handlers/test_reject.py` from `stage="doing"` to `stage="approval"`. No code change. **I recommend A**: it matches the Interface's wording and reason, the "no order change" rule, and `append_entry`'s single source for the stage. It also records what the state really held when the entry was written.
   - (B) Keep the test: `move_back` carries the stage it moves back to (`doing`). `RejectHandler._moved_back` would set the stage before appending, which breaks "no call site changes its order". The Interface sentence and the docs criterion would need rewriting.

   Built so far, committed as 3fffb043:
   - `JournalRecord` has the fields `at`, `stage` and `run` (`src/factory/domain/journal.py`).
   - `append_entry(..., *, at, run)` checks `run`-without-`at` first, before the state check.
   - `book_merge` and `book_refusal` take `at=` (`src/factory/domain/acceptance.py`).
   - The writer drops unset stamps through `model_dump(exclude_none=True)` on each record (`src/factory/adapters/work_item_markdown.py`). I chose this over a list of named keys because the other fields of a record are never `None`.
   - Every call site in the Interface table passes `at` and `run`. `StallService._stalled` now takes the `StallContext`, so it gets the stage and the cost's run from it instead of growing a sixth parameter.

   Not yet done: the refactor pass and the final `make check`. I'll do both once this is answered.
5. human (pull request comment, 2026-10-18): (A): `move_back` carries the stage the human set, `approval`. FEATURE decision 27 already gives the constant exactly so: `MOVE_BACK = JournalRecord(number=2, speaker=FACTORY, kind="move_back", at=datetime(2026, 10, 12, 12, 0, tzinfo=UTC), stage="approval")`. The tester changes `stage="doing"` to `stage="approval"` there and nothing else; no code change, no call site changes its order.
6. coder: The human answered with option (A) in entry 5. That calls for one test change and no code change, so I am handing it to the tester.

   The change: in `tests/application/handlers/test_reject.py`, the module constant `MOVE_BACK` (line 34) changes `stage="doing"` to `stage="approval"`, the stage the human set, and nothing else.

   With that change, the six reject tests listed in entry 4 should pass against the code already committed in 3fffb043. When the ticket comes back to doing, I will do the refactor pass and the final `make check`, then hand it to review.
7. tester: Tester, making the test change the human approved in entry 5 and the coder named in entry 6. In `tests/application/handlers/test_reject.py`, I changed one value in the module constant `MOVE_BACK` (line 34): `stage="doing"` is now `stage="approval"`. That is the stage the human set, and it is the stage the state holds when the `move_back` entry is appended. I changed nothing else and made no code change.

   I ran `make test` once and it passed: `test: green (33.3 s)`, with 99.47 % coverage. That includes the six reject tests listed in entry 4. The ticket goes back to doing, where the coder does the refactor pass and the final `make check`.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (30.6 s)
8. coder: The implementation is finished and `make check` passes (`check: green`, coverage 99.47 %). The feature work is in 3fffb043 and the refactor is in 3f7b85b8. The human's answer in entry 5 needed no code change: the `move_back` entry already got the stage the human set from the state, and the tester's one-value change in entry 7 makes the six reject tests pass.

   What I built:
   - `src/factory/domain/journal.py`: `JournalRecord` gains `at` (`UtcDatetime | None`), `stage` (`Name | None`) and `run` (`RunId | None`), each defaulting to `None`. `append_entry(document, entry, *, at=None, run=None)` checks for a `run` without an `at` before anything else, so it raises that `ValueError` even for a document with no state. A private `_record` stamps `at`, the state's `stage` and `run` only when `at` is given.
   - `src/factory/domain/acceptance.py`: `book_merge` and `book_refusal` take `at=` and pass it through `_booked`. `_booked` sets the stage to `done` before it appends.
   - `src/factory/adapters/work_item_markdown.py`: `render` writes each journal record with `model_dump(exclude_none=True)`.
   - Every call site in the Interface's table now passes `at` from `self._boundaries.clock.now()`, or the claim's `started_at` for the `started` entry, and `run` where the table gives one. The files are in `src/factory/application/`: `opening.py`, `claims.py`, `stage.py` (AfterAgent's `form_invalid` and both StageFinisher paths), `stalls.py`, `recovery.py`, `acceptance.py`, and `handlers/closed.py`, `comments.py`, `merged.py`, `questions.py`, `reject.py`. No call site changes its order.

   Design decisions:
   - The writer leaves out unset stamps with `exclude_none` on each record, not with a list of named keys. The other fields of a record are never `None`, so the effect is the same and a later optional field gets the same treatment.
   - `StallService._stalled` now takes the `StallContext` instead of the stage alone, so it gets both the stage and `context.cost` from one argument rather than gaining a sixth parameter.

   Refactor pass: I read the diff as a reviewer would. The only change is in `recovery.py`, where I gave the crash cap's `question` entry a name like the crash entry above it. Behaviour is unchanged. Nothing else needed changing.

   Noticed but not touched: `CommentCopier.append` reads the clock once per comment. Under the real clock, comments copied in one tick can therefore carry slightly different times. That matches the Interface's table (`clock.now()` per entry).

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
9. reviewer: no findings. I read the ticket and the whole diff, `git diff main...HEAD -- . ':!factory'`: 14 source files and 18 test files.

   1. Acceptance criteria: each criterion has a test that tests what it is named for.
      - Criterion 1: `tests/domain/test_journal_stamps.py` builds the record through `type[BaseModel]`. Its rows: none of the three, all three, +02:00 stored as UTC, 32 hex characters accepted, and naive `at`, `Tests`, 31, 33, an uppercase letter and `g` refused. Both sides of the 32-character limit are covered.
      - Criterion 2: five rows. The `ValueError` message is matched exactly, the document is checked unchanged, and the body is checked the same in each row that appends.
      - Criteria 3 and 4: `tests/adapters/test_journal_stamps_file.py` compares the whole text and does the round trip, including the single-quoted run of 32 times `1` and an old file written back byte for byte.
      - Criterion 5: (a) to (e) are in `test_stage_finish.py`, `test_after_agent.py`, `test_stalls.py` and `handlers/test_closed_send_back.py`. The changed tests of decision 27 match the list in the Interface, `MOVE_BACK` with `stage="approval"` as the human answered in entry 5.
      - Criterion 6: four booking rows.
      - The coder's entry 8 reports `make check` green and `make duplicates` with 0 new findings.
   2. Architecture: the domain gets no clock, because `at` is a parameter. `journal.py` imports only domain modules (`cost_records.RunId`, `times.UtcDatetime`). Every call site reads the clock through `self._boundaries.clock`. No layer is crossed and no tool is called outside its wrapper.
   3. Security: no secrets; the hex test values are low-entropy (`"a" * 32`). There is one new `# noqa: DTZ001` on the naive-`at` row. It is the established pattern for that row (`tests/domain/test_disk_records.py:38` on main) and is needed to build a naive datetime on purpose. No `nosec`, `nosemgrep` or baseline entry was added.
   4. Quality:
      - `append_entry` checks for a `run` without an `at` before it reads the state, as the Interface asks.
      - The private `_record` does one thing.
      - The writer uses `model_dump(exclude_none=True)` per record. I accept the coder's reason: the other fields of a record can never be `None`, so the effect is the same.
      - `StallService._stalled` now takes the `StallContext` instead of a sixth parameter.
      - The `JournalRecord` docstring names the three fields. The comment in `work_item_markdown.py` says why.
      - No order of a call site changed: `move_back` is appended before the move back, the story's `done` before `done` is set, and `_booked` sets `done` first.
   5. Ticket hygiene: the log explains the `move_back` question and its answer, and the `exclude_none` and `StallContext` choices. The Assignment matches what was built. The docs criterion (9) still describes what the documenter has to write.

   Open for the docs stage: criterion 9 (project guide, decision log, and one pointer sentence in the entry for SI1.1).
10. documenter: criterion 9 written; no findings. The code matches the Interface.

    Files changed:
    - `docs/project-guide.md`, *The journal's data*: names `at`, `stage` and `run` with their types. It says they are optional when read, set on every new entry, and where each comes from. It also gives the stage of a `move_back`, a story's `done` and the acceptance's `done`, and says which entries carry a run.
    - `docs/project-guide.md`, *The journal's entries*: `append_entry` takes `at` and `run` and gets the stage from the state. It covers the `run`-without-`at` `ValueError` and says the rendered body is unchanged. The printed record of the example is now `number=2 speaker='intake' kind='result' at=None stage=None run=None`. I ran the example and it prints exactly that.
    - `docs/project-guide.md`, *The layout*: the three fields are left out when unset. It shows a full record, and says a numeric-looking `run` is single-quoted.
    - `docs/decisions.md`: new entry "Journal records say when, in which stage and from which run; cost records on which instance". It covers the human's word, optional when read with no migration, why an unset field is left out rather than written `null`, why the time comes from the `Clock` and the stage from the state, which entries carry a run, and what was rejected. The SI1.1 entry gets one pointing sentence.

    Cross-read: the rest of `project-guide.md` (the entries that mention `append_entry`, the hand-over and stall text) and `README.md`. I found nothing else stale. `python -m factory.entry.check_documents` prints `documents ok`. I changed only documents, so I did not run `make check`.

    Stale but unrelated: none seen.

    `make check`: check: green
    `make documents`: documents ok
11. demo: Ran the two commands under `## Demo` from the repository root, in order, exactly as written.

    Command 1 (rendering a document with an old-style record and a stamped record):
    ```
    journal:
    - number: 1
      speaker: human
      kind: created
    - number: 2
      speaker: tester
      kind: result
      at: '2026-10-17T20:31:00Z'
      stage: tests
      run: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    ```
    Exit 0. Met its `Expect:` line: ten lines in the stated order. The first record has no `at`, `stage` or `run` line. `at` is single-quoted and ends in `Z`, and the three keys come after `kind` (criteria 2 and 3).

    Command 2 (pytest over eight modules):
    ```
    ERROR: file or directory not found: tests/application/test_journal_stamps.py

    no tests ran in 0.00s
    ```
    Exit 4. Did not meet its `Expect:` line: there is no `<n> passed`, and no tests ran.

    Context, not part of the demo: the tester did not create `tests/application/test_journal_stamps.py`. The new criterion-5 tests went into existing modules: `tests/application/test_stage_finish.py`, `tests/application/test_after_agent.py`, `tests/application/test_stalls.py` and `tests/application/handlers/test_closed_send_back.py`. I made one run of my own: command 2 without the missing file, plus those four modules. It gave `334 passed, 16 errors`, every error in `handlers/test_closed_send_back.py`. That module passes when it runs with its own folder (`tests/application/handlers/`: all passed). So those errors seem to come from how my selection collected the modules, not from the code. This run is not the demo and I am not judging it as one. No command contradicted any acceptance criterion.

    Findings:
    1. Command 2 (`uv run pytest … tests/application/test_journal_stamps.py …`). Expected: a last line naming `<n> passed`, with no `failed`, `error` or `skipped` count. Observed: `ERROR: file or directory not found: tests/application/test_journal_stamps.py`, no tests ran, exit 4. Criterion: none is contradicted. The command errors because a module it names does not exist on the branch. `## Demo` is the human's and the tests are the tester's, so the fix is one of two. Either the human changes the command to name the modules that hold the criterion-5 tests (`tests/application/test_stage_finish.py`, `tests/application/test_after_agent.py`, `tests/application/test_stalls.py`, `tests/application/handlers/test_closed_send_back.py`), or the tests move to `tests/application/test_journal_stamps.py`. If the command is changed, check that the combined selection passes: my ad-hoc run of these modules together gave errors in `test_closed_send_back.py`.
12. coder: coder, round 1: the demo's finding (entry 11) can't be fixed in the code, so I need your decision. The second demo command names `tests/application/test_journal_stamps.py`, which doesn't exist. The tester put the criterion-5 tests into four existing modules instead: `tests/application/test_stage_finish.py`, `tests/application/test_after_agent.py`, `tests/application/test_stalls.py` and `tests/application/handlers/test_closed_send_back.py`. `## Demo` is yours and the tests are the tester's, so I changed nothing, and there is no commit from me this round.

    What I checked about the errors the demo saw in its own run:
    - They are not caused by the code. The demo command without the missing file passes: 223 passed.
    - Each of the four modules passes when run together with `tests/application/handlers/test_reject.py` (65, 51, 47 and 36 passed).
    - The 16 errors (`fixture 'pull_request' not found`) were reported by `test_reject.py`'s tests, not by `test_closed_send_back.py` as entry 11 said. They appear only when `test_closed_send_back.py` and `test_reject.py` are far apart in the argument list, with modules from other folders between them. The `pull_request` fixture comes from `tests/application/handlers/conftest.py`, so this looks like how pytest collects that folder's conftest when its files are split up in the arguments, not a fault in the code. With the two handler modules next to each other, everything passes (`test_stalls.py`, `test_closed_send_back.py`, `test_reject.py`: 65 passed).

    Options:
    (A) You change the second demo command: replace `tests/application/test_journal_stamps.py` with the four modules and keep the two `handlers/` modules next to each other, for example `… tests/application/test_stage_finish.py tests/application/test_after_agent.py tests/application/test_stalls.py tests/application/test_claims.py tests/application/test_opening.py tests/application/handlers/test_closed_send_back.py tests/application/handlers/test_reject.py`.
    (B) The ticket goes to the tester, who moves criterion 5's tests (a) to (e) into a new `tests/application/test_journal_stamps.py`, as the demo command expects.

    I recommend (A). The tests already pin criterion 5 where the services they test are already tested, and the reviewer accepted them there. (B) would only move tests so that they match a command.
13. human (pull request comment, 2026-10-18): (A): the tests stay where the tester put them. The second command of `## Demo` becomes, in place of the one naming `tests/application/test_journal_stamps.py`, with the two `handlers/` modules next to each other: `uv run pytest --no-header -p no:cacheprovider` followed by the other modules of the present command, then `tests/application/test_stage_finish.py tests/application/test_after_agent.py tests/application/test_stalls.py tests/application/test_claims.py tests/application/test_opening.py tests/application/handlers/test_closed_send_back.py tests/application/handlers/test_reject.py`; its Expect line stays (a passed count, no failed, error or skipped). The stage that receives this rewrites that one command in the story and cites this answer; nothing else in the story changes, and no test moves.
14. coder: coder, round 1: I made the change the human asked for in entry 13, option (A). In `## Demo`, I rewrote the second command and changed nothing else in the story. No test moved, and there is no code change or commit from me this round. The factory commits the story edit.

    The new command is `uv run pytest --no-header -p no:cacheprovider` followed by the old command's other modules:
    - `tests/domain/test_journal_stamps.py`
    - `tests/adapters/test_journal_stamps_file.py`
    - `tests/domain/test_journal.py`
    - `tests/adapters/test_work_item_markdown.py`

    and then, in the order the human gave:
    - `tests/application/test_stage_finish.py`
    - `tests/application/test_after_agent.py`
    - `tests/application/test_stalls.py`
    - `tests/application/test_claims.py`
    - `tests/application/test_opening.py`
    - `tests/application/handlers/test_closed_send_back.py`
    - `tests/application/handlers/test_reject.py`

    The missing `tests/application/test_journal_stamps.py` is gone, and the two `handlers/` modules are now next to each other. The Expect line is unchanged.

    I ran the new command and it passed: `350 passed in 23.21s`, with no failed, error or skipped count. That clears the demo's finding in entry 11.

    Refactor pass: this round has no code diff, so there was nothing to refactor.

    `make check`: check: green

    `make check`: check: green
    `make duplicates`: duplicates: 0 new, 39 known, 0 gone
15. reviewer: reviewer, round 1: no findings. I read the ticket, the diff's `--stat` (34 files) and the whole source and test diff (`git diff main...HEAD -- . ':!factory'`). The code diff has not changed since entry 9: no commit after 3f7b85b8. This round's only change is the second `## Demo` command, rewritten exactly as the human asked in entry 13 (the missing `tests/application/test_journal_stamps.py` dropped, the four modules added, the two `handlers/` modules next to each other). The coder reports 350 passed with that command.

    1. Acceptance criteria:
       - Criterion 1: `tests/domain/test_journal_stamps.py` builds the record through `type[BaseModel]` in one parametrized test. Both sides of every limit are covered: a naive `at` is refused and an aware one is stored in UTC; `Tests` is refused as a stage; runs of 31 and 33 characters, one with an uppercase letter and one with `g` are refused, and 32 hex characters are accepted.
       - Criterion 2: five rows. The message is matched exactly (`^…$`), the document is checked unchanged, the no-state row gets `ValueError` because the check in `append_entry` (`src/factory/domain/journal.py`) runs before `_state_of`, and the body is checked the same in each row that appends.
       - Criteria 3 and 4: `tests/adapters/test_journal_stamps_file.py` compares the whole text, does the round trip, and covers the single-quoted `'111…'` run and an old file written back byte for byte.
       - Criterion 5: the new tests (a) to (e) check `at`, `stage` and `run` against `clock.now()` and `aftermath.cost.run` / `launched.cost.run`. The decision-27 edits match the list in the Interface, and `MOVE_BACK` has `stage="approval"` as the human answered in entry 5.
       - Criterion 6: four rows (merge and refusal, each with and without `at`).
       - The coder's entry 14 reports `check: green`, and `make duplicates` reports 0 new findings.
    2. Architecture: `journal.py` imports only domain modules (`RunId`, `UtcDatetime`) and the domain gets no clock, because `at` is a parameter. Every call site reads time through `self._boundaries.clock`, except `started`, which uses the claim's `started_at`. `_stall_red` and `AfterAgent` pass `cost=` into `StallContext`, so the run of the `stall` comes from it. No call site changes its order.
    3. Security: no secrets; the test hex values are low-entropy. The only new marker is `# noqa: DTZ001` on the naive-`at` row, which builds a naive datetime on purpose (the same pattern as `tests/domain/test_disk_records.py`). No `nosec`, `nosemgrep` or baseline entry was added.
    4. Quality:
       - The private `_record` does one thing.
       - `model_dump(exclude_none=True)` per record carries a comment saying why; the other fields of a record are never `None`.
       - `_stalled` taking the `StallContext` avoids a sixth parameter.
       - The docstrings of `JournalRecord` and `append_entry` name the three fields.
    5. Ticket hygiene: the log explains the `move_back` question, the demo fix and the `exclude_none` and `StallContext` choices. The Assignment matches what was built, and criterion 9 still describes what the documenter writes (already done in entry 10).
16. documenter: documenter, round 1: I made no new edit. Round 1 changed only the second `## Demo` command in the story (entry 14), with no code diff since 3f7b85b8. The documentation I wrote in round 0 (entry 10) still matches the code, so I re-read it against the diff and kept it.

    Files already changed on the branch:
    - `docs/project-guide.md`: *The journal's data* names `at`, `stage` and `run` (types, optional when read, where each comes from, the `move_back` and `done` stages, which entries carry a run). *The journal's entries* describes `append_entry(..., at, run)` and its example now prints `at=None stage=None run=None`. *The layout* says unset stamps are left out, shows a record with all three, and says a numeric-looking `run` is single-quoted.
    - `docs/decisions.md`: one new entry, "Journal records say when, in which stage and from which run; cost records on which instance", plus one sentence in the SI1.1 entry pointing to it.

    I ran `python -m factory.entry.check_documents` and it printed `documents ok`. I did not run `make check`, because I changed no file outside README and docs this round. The working tree is clean.

    Cross-read and current: `README.md` and `docs/operator-guide.md` do not mention journal records, so they need no change.

    Findings: none. Nothing stale that is unrelated to this story.

    `make check`: check: green
    `make documents`: documents ok
