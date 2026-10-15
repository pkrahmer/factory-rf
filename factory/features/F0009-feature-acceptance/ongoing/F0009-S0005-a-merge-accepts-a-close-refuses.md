---
stage: doing
pr: 107
blocked: null
comments_seen: 2
round: 1
attempts: 0
---
# A merge accepts, a close refuses

## Assignment (as of log entry 1)

The human's merge or close of an acceptance's pull request decides its result, whatever the reviewer recommended. This story books both results as data and handles the merge; S0007 handles the close. A merge books the acceptance as `accepted`: the report moves with its cost records to the feature's `done` folder, its state says `done` and `accepted`, its journal gets one `done` entry with the acceptance's own cost, and the proposed stories that the merge brought into the feature's backlog stay there, untouched; the acceptance's branch is deleted. A close books it as `refused`: the report is written at `done` with the human's reason as the first paragraph under the recommendation, `refused` as the outcome and the cost in a `done` entry, and the proposed stories, which were only on the branch, are dropped with it. The two booking functions are built here (`book_refusal` and `refusal_reason` are used by S0007's handler). Code never interprets the human's text: it is copied unchanged. The merge handler can be run again after a kill and books nothing twice. It follows F0007's `MergedHandler` (F0007-S0003) step for step and reuses its helpers (`target_of`, `WorkItemRecorder`, `destination_path`, `done_entry_text`, `commit_subject`, and `move_with_cost_records`, which it makes public); it differs in the outcome and in the `AcceptanceState` it books. Merging an acceptance before it reached its approval, and the second acceptance of a feature, are the next story. Covers no handover condition alone (ST2.1, ST2.2 and R31 are built on this in S0006 and S0011); keeps kept thing 2 (the human accepts by merging, and a refusal returns the human's text), kept thing 19 (the result is the human's act, not the recommendation) and kept thing 20 (each acceptance costed). The report and its sidecar move or are written; nothing else on the main branch changes. `AcceptanceMerged` is registered, inside a `SplitByWorkItemKind`, in `factory.entry.wiring.build_handlers` by S0010.

## Interface

`src/factory/domain/acceptance.py` (grown)

```python
NO_REASON = "no reason given"

def book_merge(document: WorkItemDocument, bill: Bill) -> WorkItemDocument: ...
def book_refusal(document: WorkItemDocument, *, role: str, on: date, bill: Bill) -> WorkItemDocument: ...
def refusal_reason(document: WorkItemDocument, role: str) -> str: ...
```

`src/factory/application/acceptance.py` (grown)

```python
class AcceptanceMerged(Handler):         # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

`Bill`, `bill` and `cost_line` are in `factory.domain.bills`, `done_entry_text` in `factory.domain.post_texts` (F0007-S0003), `destination_path` in `factory.domain.archive` (F0007-S0003), `target_of`, `commit_subject` and `WorkItemRecorder` in `factory.application.handlers.recording` (F0007-S0001), which also holds the `move_with_cost_records` that this story makes public; `NewEntry` and `append_entry` are in `factory.domain.journal`; `insert_paragraph`, `sections` and `JOURNAL` in `factory.domain.sections`; `cost_records_path` in `factory.domain.paths`.

Rules:

- `book_merge(document, bill)` needs a document whose state is an `AcceptanceState`, else `ValueError`. It sets `stage` to `DONE_STAGE`, `outcome` to `"accepted"`, `claim` and `blocked` to `None`, and keeps every other field; it appends one entry (speaker `factory`, kind `done`) with the text `done_entry_text(bill)`, that is `done (pull request merged); cost: ` and `cost_line(bill)`.
- `refusal_reason(document, role)` is the visible text (`entry_text`), stripped, of every journal record with speaker `human` and kind `comment` that comes after the last record with `speaker == role` and kind `result` (after none, when there is no such record), in order, joined with one space; it is `NO_REASON` when there is none. The text is never interpreted.
- `book_refusal(document, role=..., on=..., bill=...)` needs an `AcceptanceState` too, else `ValueError`. It sets `stage` to `DONE_STAGE`, `outcome` to `"refused"`, `claim` and `blocked` to `None`, and keeps every other field. It makes `Refused by the human on <on as YYYY-MM-DD>: <refusal_reason(document, role)>` the first paragraph under the report's `## Recommendation` heading (`insert_paragraph`); a body without that section gets the section, holding only that paragraph, just before its journal section (`JOURNAL`, never the literal), and at the end of the body when it has no journal section either. It appends one entry (speaker `factory`, kind `done`) with the text `done (pull request closed by the human); cost: ` and `cost_line(bill)`.
- `AcceptanceMerged.__init__` stores its arguments and never raises.
- `AcceptanceMerged.handle(event)` raises `CannotHandle(kind=<the event's kind>, reason=...)` with these reasons, checked in this order: `"not a merged event"` for another kind; `"not an acceptance"` when the event has no work item or its id is a story's; `"no acceptance stage"` when `definition.acceptance_stage` is `None`; `"pull request is not merged"` when `event.pull_request` is `None` or its state is not `merged`. It changes nothing then.
- Otherwise it calls `WorkItemRecorder.check_out(MAIN_BRANCH)` and takes `target_of(event)`. When the report is in `in-progress/` at the snapshot's path in the checkout, it reads it, takes `bill(records)` of the records that the cost record reader returns for `cost_records_path(snapshot.path)` (a missing file gives no records; read at `HEAD`, which is `origin/main`, as F0007-S0003 does), and then, in this order: move the report and its cost records file with F0007-S0003's move, which this story makes the public `move_with_cost_records(git: Git, path: str, folder: LifecycleFolder) -> str` of `factory.application.handlers.recording` (it returns the destination; `MergedHandler` calls it in place of its `_move`, and nothing else of `merged.py` changes); write `book_merge(document, bill)` at the new path; commit with `commit_subject(id, "merged, archived")` and push `main` with `WorkItemRecorder.publish` (`PushFailed` when the outcome is not `pushed`). When the report is already in `done/` and not in `in-progress/`, it books nothing; when it is in neither, it raises `CannotHandle(kind=<the event's kind>, reason="no report on the main branch")`. Last, it deletes the branch `work-item/<id>` with `WorkItemRecorder.delete_branch` (F0007-S0001: `PushFailed` when the remote refuses, the booking stays pushed; then the local branch); a branch that is already gone is not an error. The move comes before the write: `git mv` onto an existing file fails.
- The own cost of the acceptance is read from the checkout at `HEAD` (the commit the handler works on) and not through `BillService`, whose remote-tracking refs give the same commit; the line therefore counts only the acceptance's own records (GH4.4, shown in S0003 criterion 18).

Tests: `tests/domain/test_acceptance_booking.py`, `tests/application/test_acceptance_merged.py`; the `remote`, `checkout`, `human`, `hosting`, `clock`, `kill_points` and `boundaries` fixtures; the feature is a `F0002-todo` that the test pushes (the fixture's `F0001` has a backlog story and is never due), the acceptance is opened with `AcceptanceService.open`, its pull request is created with `hosting.create_pull_request` and its number written into the report's state on the branch with `human.push_file`, and the human acts with `human.merge`, `hosting.merge_by_human` and `hosting.add_human_comment`.

## Acceptance criteria

1. `book_merge` sets the stage to `done`, the outcome to `accepted`, `claim` and `blocked` to `None`, and leaves `stories`, `round`, `attempts`, `crashes`, `pull_request`, `comments_read` and `handed_over` as they were.
2. `book_merge` appends one record (speaker `factory`, kind `done`) whose number follows the journal's last, and whose visible text equals `done_entry_text(bill)`.
3. `book_merge` and `book_refusal` raise `ValueError` for a document whose state is a plain `WorkItemState`.
4. `refusal_reason` joins the texts of the human's `comment` records after the reviewer's last `result` record with one space, unchanged between the stripped ends: the texts `Too wide.` and `Cut the second story.` give `Too wide. Cut the second story.`
5. `refusal_reason` ignores a `comment` record before the reviewer's last `result` record, a human `close` record and the factory's records.
6. `refusal_reason` is `no reason given` when no human comment follows the reviewer's last result, and uses every human comment when the journal has no result of the reviewer.
7. `refusal_reason` strips leading and trailing whitespace from each comment's text and keeps the text between unchanged; a comment that is blank after stripping is skipped, and `no reason given` results when no other comment remains.
8. `book_refusal` sets the stage to `done`, the outcome to `refused`, `claim` and `blocked` to `None`, and leaves the other state fields as they were.
9. `book_refusal` makes `Refused by the human on 2026-10-12: <the reason>` the first paragraph of the `## Recommendation` section, above the reviewer's recommendation text, and leaves the rest of the body as it was.
10. `book_refusal` on a body without a `## Recommendation` section adds that section, holding only the refusal paragraph, just before the `## Journal` section.
11. `book_refusal` on a body with neither a `## Recommendation` nor a `## Journal` section adds the section with the refusal paragraph at the end of the body.
12. `book_refusal` appends one record (speaker `factory`, kind `done`) whose visible text is `done (pull request closed by the human); cost: ` followed by `cost_line(bill)`.
13. After the human merged the acceptance's pull request, `AcceptanceMerged.handle` leaves on `origin/main` the report in the feature's `done/` folder, equal to `book_merge(<the merged report>, <bill of its records>)` as the writer renders it, and its cost records file beside it with the same records, neither file left in `in-progress/`; a report merged without a cost records file is booked alone in `done/`, its entry's cost `cost_line(bill([]))` (two cases, one test).
14. After `handle` the branch `work-item/<id>` is gone on the remote and locally, and a second `handle` of the same event makes no new commit and raises no error.
15. The commit `handle` makes on the main branch changes only the report's and the cost records file's paths: the proposed stories that the merge brought into the feature's backlog are still there, byte for byte.
16. A merge of an acceptance whose recommendation is `not accepted` is booked `accepted`: the recommendation text does not change the outcome.
17. `AcceptanceMerged.handle` raises `CannotHandle` with the five reasons the Interface gives (another kind of event, a story's event, no acceptance stage, a pull request that is not merged, no report on the main branch), each in its place in the order, and changes nothing.
18. After `kill_points.arm(KillPoint.AFTER_PUSH)` made the first `handle` raise `InjectedKill` right after the push of the main branch, a second `handle` leaves exactly one `done` record in the report, one new commit on `origin/main`, and the branch gone.
19. `AcceptanceMerged(boundaries, definition)` with `definition.acceptance_stage` `None` is built without an error.
20. When the remote's main branch moved since the last fetch (the human pushed to it), `AcceptanceMerged.handle` raises `PushFailed` with the outcome `rejected`, and the branch `work-item/<id>` is still on the remote.
21. When the remote refuses the deletion of the branch (`receive.denyDeletes` set in the bare remote), `handle` raises `PushFailed` with the outcome `rejected` after the booking is pushed: `origin/main` holds the report in `done/` and the branch is still on the remote.
22. make check stays green.
23. docs: `docs/operator-guide.md` explains what the human's merge and close of an acceptance do (accepted or refused whatever the recommendation; where the report lands; that the reason is the human's comments unchanged; that a refusal drops the proposed stories and a merge keeps them in the backlog); `docs/decisions.md` records why each acceptance has its own report and cost records.

## Demo

```bash
uv run python -c "
from datetime import date
from factory.domain.acceptance import AcceptanceState, book_merge, book_refusal, refusal_reason
from factory.domain.bills import bill, cost_line
from factory.domain.journal import JournalRecord, entry_text
from factory.domain.post_texts import done_entry_text
from factory.domain.work_item import WorkItemDocument
records = [('factory', 'started'), ('acceptance-reviewer', 'result'), ('human', 'comment'), ('human', 'comment')]
journal = [JournalRecord(number=n, speaker=s, kind=k) for n, (s, k) in enumerate(records, 1)]
body = '# Acceptance of Todo service\n\n## Recommendation\n\nnot accepted\n\n## Journal\n\n1. factory: started.\n2. acceptance-reviewer: not accepted\n3. 2026-10-12 human: Too wide.\n4. 2026-10-12 human: Cut the second story.\n'
document = WorkItemDocument(state=AcceptanceState(stage='approval', stories=['F0001-S0001'], journal=journal), body=body)
print(refusal_reason(document, 'acceptance-reviewer'))
refused = book_refusal(document, role='acceptance-reviewer', on=date(2026, 10, 12), bill=bill([]))
print(refused.state.stage, refused.state.outcome)
line = 'Refused by the human on 2026-10-12: Too wide. Cut the second story.'
print(line in refused.body, refused.body.index(line) < refused.body.index('not accepted'))
print(entry_text(refused, 5) == 'done (pull request closed by the human); cost: ' + cost_line(bill([])))
accepted = book_merge(document, bill([]))
print(accepted.state.stage, accepted.state.outcome, entry_text(accepted, 5) == done_entry_text(bill([])))
"
```
Expect: five lines: `Too wide. Cut the second story.`, `done refused`, `True True`, `True`, then `done accepted True`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: 1. The Interface says `refusal_reason` takes the visible text of each human comment *stripped*, but no criterion tests it. Criterion 4 says "unchanged", which sits oddly beside "stripped", and the story never says what a comment that is only whitespace does. Does it count as a comment and add an empty string to the join, or is it skipped (and give `no reason given` if it was the only one)? Without a criterion two coders will read this two ways and both will pass the tests. My suggestion is to add a criterion after 6: "`refusal_reason` strips leading and trailing whitespace from each comment's text and keeps the text between unchanged; a comment that is blank after stripping is skipped, and `no reason given` results when no other comment remains." Alternatively, drop "stripped" from the Interface and say the text is copied exactly.

   Everything else I checked is in order. The Interface names concrete modules and signatures. The rules' failing sides have criteria: the plain-state `ValueError` is criterion 3, the five `CannotHandle` reasons 16, the rejected push 19, and the refused branch deletion 20. The Demo is runnable and its `Expect:` line is checkable. The story fits the architecture and the feature's scope.
3. human (pull request comment, 2026-10-15): Add the criterion after 6, as you worded it: "`refusal_reason` strips leading and trailing whitespace from each comment's text and keeps the text between unchanged; a comment that is blank after stripping is skipped, and `no reason given` results when no other comment remains." This matches F0007's answer rule, where only a non-blank comment counts (`factory.domain.answers.unblock`). Reword criterion 4's "unchanged" to "unchanged between the stripped ends" so the two agree. The Interface stays as it is.
4. intake: accepted. The human's answer (log entry 3) is written into the story: the new criterion 7 (`refusal_reason` strips each comment, skips blank ones, gives `no reason given` when none remain), as the human worded it. Criterion 4 now says "unchanged between the stripped ends". The old criteria 7 to 22 are now 8 to 23, and `make check` and `docs:` are still last. The Interface and the Assignment are unchanged.
   - Interface: names concrete modules and signatures (`factory.domain.acceptance`, `factory.application.acceptance`). Every stated behaviour has a criterion, including the stripping.
   - Criteria: each is testable by one test function. Failing sides are covered: plain-state `ValueError` (3), the five `CannotHandle` reasons (16), a rejected push (19), a refused branch deletion (20), and blank comments (7).
   - Demo: runnable, and the `Expect:` line is checkable line by line.
   - Architecture: domain holds the pure booking functions and application holds the handler. It reuses F0007's helpers and makes `move_with_cost_records` public. Layers are respected.
   - Scope: within the feature's scope (the merge result and the booking functions). S0007's close handler is left out.
5. tester: wrote red tests for criteria 1–21, one test per criterion. `make lint` is green. `make test` stops at collection on both new files because `book_merge`, `book_refusal`, `refusal_reason` and `NO_REASON` do not exist yet in `factory.domain.acceptance`, and `AcceptanceMerged` does not exist yet in `factory.application.acceptance`. Ruff passes both files, so the errors are missing names, not syntax.

   Files created: `tests/domain/test_acceptance_booking.py`, `tests/application/test_acceptance_merged.py`.

   - criterion 1: tests/domain/test_acceptance_booking.py::test_a_merge_books_the_acceptance_done_and_accepted_and_keeps_the_other_fields
   - criterion 2: tests/domain/test_acceptance_booking.py::test_a_merge_appends_one_done_entry_of_the_factory_with_the_bill
   - criterion 3: tests/domain/test_acceptance_booking.py::test_booking_a_document_whose_state_is_not_an_acceptance_state_is_refused (rows: merge, refusal)
   - criterion 4: tests/domain/test_acceptance_booking.py::test_the_refusal_reason_joins_the_human_comments_after_the_last_result_with_a_space
   - criterion 5: tests/domain/test_acceptance_booking.py::test_the_refusal_reason_ignores_earlier_comments_human_closes_and_factory_records
   - criterion 6: tests/domain/test_acceptance_booking.py::test_the_refusal_reason_without_a_later_comment_or_without_a_result (rows: no comment after the result, no result)
   - criterion 7: tests/domain/test_acceptance_booking.py::test_the_refusal_reason_strips_each_comment_and_skips_blank_ones (rows: stripped ends, a two-line comment kept, blank skipped, only blank)
   - criterion 8: tests/domain/test_acceptance_booking.py::test_a_refusal_books_the_acceptance_done_and_refused_and_keeps_the_other_fields
   - criterion 9: tests/domain/test_acceptance_booking.py::test_a_refusal_puts_its_paragraph_first_under_the_recommendation_and_keeps_the_rest (compares the whole body)
   - criterion 10: tests/domain/test_acceptance_booking.py::test_a_refusal_adds_the_recommendation_section_just_before_the_journal
   - criterion 11: tests/domain/test_acceptance_booking.py::test_a_refusal_adds_the_recommendation_section_at_the_end_of_a_body_without_a_journal
   - criterion 12: tests/domain/test_acceptance_booking.py::test_a_refusal_appends_one_done_entry_of_the_factory_with_the_bill
   - criterion 13: tests/application/test_acceptance_merged.py::test_a_merged_acceptance_is_booked_accepted_in_done_with_its_cost_records (rows: costs, none)
   - criterion 14: tests/application/test_acceptance_merged.py::test_after_the_booking_the_branch_is_gone_and_a_second_handling_changes_nothing
   - criterion 15: tests/application/test_acceptance_merged.py::test_the_booking_commit_changes_only_the_report_and_keeps_the_proposed_stories
   - criterion 16: tests/application/test_acceptance_merged.py::test_a_merge_books_accepted_whatever_the_recommendation_says
   - criterion 17: tests/application/test_acceptance_merged.py::test_an_event_the_handler_cannot_book_raises_its_reason_and_changes_nothing (six rows: another kind, a story, no acceptance stage, no pull request, an open pull request, no report on main)
     - Each row also fails every check that comes after its own, so the order is tested.
   - criterion 18: tests/application/test_acceptance_merged.py::test_after_a_kill_after_the_push_a_second_handling_books_once_and_deletes_the_branch
   - criterion 19: tests/application/test_acceptance_merged.py::test_the_handler_is_built_without_an_acceptance_stage
   - criterion 20: tests/application/test_acceptance_merged.py::test_a_main_moved_since_the_fetch_rejects_the_booking_and_keeps_the_branch
   - criterion 21: tests/application/test_acceptance_merged.py::test_a_refused_branch_deletion_fails_after_the_booking_is_pushed

   Open point for the coder (criterion 11):
   - **The gap:** `book_refusal` must append a `done` entry. `append_entry` raises `WorkItemFormatError` on a body without a `## Journal` section. The story does not say how the entry is appended when that section is missing.
   - **What the test checks:** only what the criterion states.
     - The original body is kept.
     - `## Recommendation` follows it as the first section and holds only the refusal paragraph.
     - The function must not raise.
   - **What the test leaves open:** whether a journal section is created after the recommendation for the entry. If that needs a decision, ask the human.

   Not run: the type check, which this stage skips.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
6. coder: wrote the code for criteria 1–21. All tests pass and `make check` is green (coverage 99.49 %). There are two commits: feat 4873587 and refactor bf889fa.

   What I built:
   - `src/factory/domain/acceptance.py`
     - Added `NO_REASON`, `book_merge`, `refusal_reason` and `book_refusal`.
     - They share a private `_booked`, which:
       - raises `ValueError` unless the state is an `AcceptanceState`;
       - sets `done` and the outcome, and clears `claim` and `blocked`;
       - appends the factory's `done` entry with `append_entry`.
     - `refusal_reason` reads the visible text with `entry_text` for the human's `comment` records after the reviewer's last `result`. It strips each text, skips blank ones and joins the rest with one space. With no text left it returns `NO_REASON`.
     - `book_refusal` writes the refusal paragraph:
       - it uses `insert_paragraph` when a `## Recommendation` section exists;
       - otherwise it inserts a new section just before the `JOURNAL` section;
       - with no journal either, the section goes at the end of the body.
   - `src/factory/application/handlers/recording.py`
     - `move_with_cost_records(git, path, folder) -> str` is the old `MergedHandler._move`, now public, and it returns the destination.
     - `merged.py` calls it, and its private `_move` is gone. Nothing else in `merged.py` changed.
   - `src/factory/application/acceptance.py`
     - Added `AcceptanceMerged`. It checks the four `CannotHandle` reasons in the Interface's order, then checks out `main`.
     - When the report is at `HEAD` under `in-progress/`, it:
       1. reads the report, and its cost records with `read_cost_records` at `HEAD`;
       2. moves both with `move_with_cost_records`;
       3. writes `book_merge` at the destination;
       4. publishes with `commit_subject(id, "merged, archived")`.
     - When the report is already in `done/`, it books nothing. When it is in neither folder, it raises `"no report on the main branch"`.
     - Last, it deletes the branch with `WorkItemRecorder.delete_branch`. `GitCli.delete_remote_branch` already treats a branch that is gone as deleted, so a rerun after a kill only deletes the branch.

   Main design decision:
   - The open point the tester flagged for criterion 11: when the body has no `## Journal` section, `book_refusal` adds an empty `## Journal` section after the new `## Recommendation`. The `done` entry has to go somewhere, and `append_entry` refuses a body without a journal.
   - Rejected: changing `append_entry` to create the section, which would change a shared helper's contract for every caller; and recording the entry in the state without a visible line, which would break the rule that state and journal agree.
   - In practice `acceptance_head` always writes a journal, so this case only comes up with a hand-edited report.

   Refactor: `_with_recommendation` now reads the body's sections once instead of twice, and a comment says why `book_refusal` checks the state first.

   Noticed but not touched:
   - `MergedHandler` has no "already in `done/`" guard, so a second run for a story fails in `git mv`. `AcceptanceMerged` has the guard, as this story asks.
   - `AcceptanceMerged` is not yet registered in `build_handlers`; S0010 does that.
   - The docs criterion (23) is left to the documenter.

   `make check`: check: green
7. reviewer: sent back for two Quality findings (group 4). Groups 1–3 pass.
   - Criteria: each of criteria 1–21 has a test that checks what the criterion says.
     - The failing sides are covered: the plain-state `ValueError` rows, all six `CannotHandle` rows (each also fails every later check, so the order is tested), the rejected push and the refused branch deletion.
     - The missing-sidecar case and the already-gone branch are also covered.
     - The coder's entry says `make check` was green.
   - Architecture: layers and wrappers hold. `move_with_cost_records` is public in `recording.py`, and the only change to `merged.py` is that it now calls it.
   - Security: no markers, no secrets, no strings passed to a shell.

   Findings:
   1. `src/factory/domain/acceptance.py:289` (`_with_recommendation`): `{section.heading: section for section in reversed(sections(body))}` rebuilds the first-section-by-heading lookup that `factory.domain.sections._first_section` already does. CLAUDE.md counts a second copy of an existing helper as a finding. Fix: make it public in `factory.domain.sections` (`first_section`) and use it for both the `RECOMMENDATION` and the `JOURNAL` lookup.
   2. `src/factory/domain/acceptance.py:276` (the `refusal_reason` docstring): "never read" says the opposite of what the function does, because it reads every comment. Fix: say the texts are copied unchanged and never interpreted.

   Open (no finding against the build): for a body with neither `## Recommendation` nor `## Journal`, `book_refusal` adds an empty `## Journal` after the new section so the `done` entry has a place. The coder logged this choice (log entry 6) and criterion 11's test allows it. The Interface still says the section goes "at the end of the body". The documenter or the human may want the Interface to mention the added journal.
