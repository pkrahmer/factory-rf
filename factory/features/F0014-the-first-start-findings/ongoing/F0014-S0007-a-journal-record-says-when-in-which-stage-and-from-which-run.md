---
stage: doing
pr: 199
blocked: null
comments_seen: 2
round: 0
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
uv run pytest --no-header -p no:cacheprovider tests/domain/test_journal_stamps.py tests/adapters/test_journal_stamps_file.py tests/application/test_journal_stamps.py tests/domain/test_journal.py tests/adapters/test_work_item_markdown.py tests/application/test_claims.py tests/application/test_opening.py tests/application/handlers/test_reject.py
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
