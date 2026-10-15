---
stage: docs
pr: 109
blocked: null
comments_seen: 2
round: 0
attempts: 0
---
# A close is recorded, then booked refused

## Assignment (as of log entry 1)

Handle the human's close of an acceptance's pull request, at whatever stage the acceptance has reached: while the reviewer works or asks, at the approval, or after a failed hand-over (a close books `refused`, as v1's "close = refused"). The human's comments and the close are first recorded in the report on its branch and pushed (R22), then the report is written to the main branch at `done` with the human's reason as the first paragraph under the recommendation (`book_refusal`, S0005), `refused` as the outcome and the cost records beside it, and the proposed stories, which were only on the branch, are dropped with it; the branch is deleted. Code never interprets the human's text: it is copied unchanged. The handler can be run again after a kill, also after the branch is gone, and books nothing twice. It follows F0007's `ClosedHandler` (F0007-S0004, S0005) and uses its helpers by name (`CommentCopier.unread` and `append`, `WorkItemRecorder`, `commit_subject`, `CLOSE_ENTRY_TEXT`, `destination_path`, `target_of`); it differs in the outcome, in the refusal paragraph and in skipping the `close` entry when any `close` record exists (an acceptance ends at its first close, where F0007-S0005 skips only a `close` numbered after the latest `result`). Covers no handover condition alone (ST2.2's refused side and the close before the approval are shown here and over ticks in S0011); keeps kept thing 2 (a refusal returns the human's text), kept thing 19 (the result is the human's act) and kept thing 20 (each acceptance costed). The report and its sidecar are written; nothing else on the main branch changes. `AcceptanceClosed` is registered, inside a `SplitByWorkItemKind`, in `factory.entry.wiring.build_handlers` by S0010.

## Interface

`src/factory/application/acceptance.py` (grown)

```python
class AcceptanceClosed(Handler):         # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

`CommentCopier` is in `factory.application.handlers.comments` and `WorkItemRecorder`, `target_of` and `commit_subject` in `factory.application.handlers.recording` (F0007-S0001); `CLOSE_ENTRY_TEXT` is in `factory.domain.post_texts` (F0007-S0005); `destination_path` in `factory.domain.archive` (F0007-S0003); `book_refusal` and `refusal_reason` come from S0005; `NewEntry` is in `factory.domain.journal`; `cost_records_path` in `factory.domain.paths`.

Rules:

- `AcceptanceClosed.__init__` stores its arguments and never raises.
- `handle(event)` raises `CannotHandle(kind=<the event's kind>, reason=...)` with these reasons, checked in this order: `"not a closed event"` for another kind; `"not an acceptance"` when the event has no work item or its id is a story's; `"no acceptance stage"` when `definition.acceptance_stage` is `None`; `"pull request is not closed"` when `event.pull_request` is `None` or its state is not `closed`. It changes nothing then.
- Otherwise, in this order:
  1. Locate. When `origin/<branch>` resolves: `WorkItemRecorder.check_out(branch)` and read the report at the snapshot's path; the bill is `bill(records)` of the records that the cost record reader returns for `cost_records_path(snapshot.path)` in that checkout (none when the file is missing). When `origin/<branch>` does not resolve (a second run after step 4) and the report's file name is in `done/` on `origin/main` (`destination_path(snapshot.path, "done")` exists there), nothing more is done than step 4. When it does not resolve and the report is not in `done/` either, the handler raises `CannotHandle(kind=<the event's kind>, reason="no report on the branch or the main branch")`.
  2. Record. Every comment that `CommentCopier.unread(state, number)` returns becomes journal entries through `CommentCopier.append` (in the order listed; a comment with a blank body gets no entry, but its id still goes into `comments_read`, which stays ascending); then one entry (speaker `human`, kind `close`, text `CLOSE_ENTRY_TEXT`, `on` the date of `Clock.now()` in UTC) unless the journal already holds a record with speaker `human` and kind `close`. When the document changed, `WorkItemRecorder.record(branch, path, document, commit_subject(id, "close recorded"))` writes, commits and pushes the branch (`PushFailed` when not pushed).
  3. Book. `WorkItemRecorder.check_out(MAIN_BRANCH)`; unless the report's file name is already in `done/` on the main branch, write `book_refusal(document, role=<the role of acceptance_stage>, on=<the date of Clock.now()>, bill=<the bill of step 1>)` at `destination_path(snapshot.path, "done")`, copy the branch's cost records file (read with `Git.show_file("origin/<branch>", ...)`, when it has one) to `cost_records_path` of that path with the cost record reader and writer, and publish with `commit_subject(id, "closed, refused")` (`PushFailed` when the outcome is not `pushed`).
  4. Delete the branch with `WorkItemRecorder.delete_branch(branch)` (F0007-S0001), as the merged handler does: `PushFailed` when the remote refuses, then the local branch; a branch that is already gone is not an error.
- The proposed stories exist on the branch only; nothing of them is written to the main branch.
- The stage at which the acceptance is closed does not matter: an acceptance closed at the stage `acceptance`, at `approval` or while `blocked` is booked the same way.

Tests: `tests/application/test_acceptance_closed.py`; the `remote`, `checkout`, `human`, `hosting`, `clock`, `kill_points` and `boundaries` fixtures; the feature is a `F0002-todo` that the test pushes (the fixture's `F0001` has a backlog story and is never due), the acceptance is opened with `AcceptanceService.open`, its pull request is created with `hosting.create_pull_request` and its number written into the report's state on the branch with `human.push_file`, and the human acts with `hosting.close_by_human` and `hosting.add_human_comment`. The handler is called with a hand-built `Event(kind="closed", work_item=<the acceptance's snapshot>, pull_request=<the closed view>, remote_state=<the head of the branch>)`.

## Acceptance criteria

1. After the human commented twice and closed the pull request (`hosting.close_by_human`), `AcceptanceClosed.handle` records on `origin/<branch>` two `comment` records (speaker `human`, in comment order, dated with the date of each comment's `created_at`, the texts unchanged), adds their ids to `comments_read` in ascending order, and records one `close` record (speaker `human`, dated with the fixture clock's date).
2. A comment the factory posted (it carries the marker) is not recorded, and its id is not added to `comments_read`.
3. A human comment with a blank body gets no journal entry, and its id is added to `comments_read`; `handle` raises no error.
4. `handle` leaves on `origin/main` the report in the feature's `done/` folder equal to `book_refusal(<the recorded report>, role="acceptance-reviewer", on=<the fixture clock's date>, bill=<bill of its records>)` as the writer renders it, the branch's cost records file beside it (none when the branch has none), and nothing else: the proposed stories of the branch are not on `origin/main`.
5. After `handle` the branch `work-item/<id>` is gone on the remote and locally, and a second `handle` of the same event (the branch no longer resolves, the report is in `done/`) raises no error and makes no new commit.
6. After `kill_points.arm(KillPoint.BEFORE_PUSH, after=1)` made the first `handle` raise `InjectedKill` at the push of the main branch, `origin/<branch>` already holds the `comment` and `close` records; a second `handle` leaves exactly one `close` record, one report in `done/`, one new commit on `origin/main`, and the branch gone.
7. When the branch is gone and the report is in neither the branch nor `done/` on `origin/main`, `handle` raises `CannotHandle` with the reason `no report on the branch or the main branch` and changes nothing.
8. An acceptance closed at the stage `acceptance` (before its approval, with the reviewer working), one closed at the stage `acceptance` with `blocked == "question"`, and one closed at the stage `approval` after its hand-over, are each booked in `done/` with the outcome `refused`, `blocked` `None`, the first paragraph `Refused by the human on <date>: no reason given` when no comment follows, and the branch deleted (three cases, one test).
9. `AcceptanceClosed.handle` raises `CannotHandle` with the four reasons the Interface gives (another kind of event, a story's event, no acceptance stage, a pull request that is not closed), in that order, and changes nothing.
10. `AcceptanceClosed(boundaries, definition)` with `definition.acceptance_stage` `None` is built without an error.
11. ST2.2: after an acceptance was refused, the feature's status is `refused` and it is not due; once another story is archived the feature is `due` again, `due_features()` lists it and `AcceptanceService.open` opens `F0002-A0002`.
12. When the remote's main branch moved since the last fetch (the human pushed to it), `AcceptanceClosed.handle` raises `PushFailed` with the outcome `rejected` after the close is recorded on `origin/<branch>`, and the branch is still on the remote.
13. When the remote refuses the deletion of the branch (`receive.denyDeletes` set in the bare remote), `handle` raises `PushFailed` with the outcome `rejected` after the refusal is pushed: `origin/main` holds the report in `done/` and the branch is still on the remote.
14. A report whose journal already holds a `close` record of the human before the reviewer's latest `result` gets no second `close` record when `handle` records the close: an acceptance ends at its first close.
15. After `kill_points.arm(KillPoint.AFTER_PUSH, after=1)` made the first `handle` raise `InjectedKill` right after the push of the main branch, a second `handle` leaves one report in `done/`, one new commit on `origin/main` and the branch gone.
16. make check stays green.
17. docs: `docs/operator-guide.md` explains what a close of an acceptance's pull request does at any stage (booked refused, the human's comments as the reason, the proposed stories dropped, the branch deleted, a rerun after a kill harmless) and that a refused feature is due again only after another story is archived.

## Demo

```bash
uv run python -c "
from types import SimpleNamespace
from factory.application.acceptance import AcceptanceClosed
from factory.application.dispatcher import Handler
from factory.domain.errors import CannotHandle
from factory.domain.events import Event
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
definition = PipelineDefinition(contract='1.0', stages={'intake': StageDefinition(role='intake', next=['approval']), 'approval': StageDefinition(approval=True, next=['done']), 'done': StageDefinition()}, roles={'intake': RoleDefinition(write_paths=['{work_item}'])})
handler = AcceptanceClosed(SimpleNamespace(), definition)
print(isinstance(handler, Handler))
document = WorkItemDocument(state=WorkItemState(stage='approval'), body='# T\n')
snapshot = WorkItemSnapshot(id='F0001-A0001', path='factory/features/F0001-x/in-progress/F0001-A0001-acceptance.md', folder='in-progress', branch='work-item/F0001-A0001', branch_commit=None, document=document)
try:
    handler.handle(Event(kind='closed', work_item=snapshot, remote_state='0' * 40))
except CannotHandle as error:
    print(error)
"
```
Expect: two lines: `True`, then `cannot handle closed: no acceptance stage` (the definition has no `acceptance_stage`, so the handler is built and refuses the event before it touches anything).

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `AcceptanceClosed(boundaries, definition)` in `factory.application.acceptance` is concrete. It names its collaborators (`CommentCopier`, `WorkItemRecorder`, `commit_subject`, `CLOSE_ENTRY_TEXT`, `destination_path`, `target_of`, `book_refusal`, `cost_records_path`) with their modules, and the four steps (locate, record, book, delete) are ordered.
   - Criteria: each is testable by one test function. The rules' failing sides are covered: the four `CannotHandle` reasons in order (9), no report anywhere (7), a blank comment body (3), a factory comment skipped (2), an existing `close` record (14), a rejected push of main (12), a refused branch deletion (13), kills before and after the push (6, 15), and a rerun with the branch gone (5). Criterion 10 covers the constructor that never raises. Criteria 16 and 17 are the two closing ones.
   - Demo: the command is runnable. `Expect:` names two checkable lines, `True` and `cannot handle closed: no acceptance stage`.
   - Architecture: the handler stays in `factory.application`, reuses F0007's helpers by name and reaches git only through `WorkItemRecorder` and `Git.show_file`. No layer is crossed.
   - Scope: this is FEATURE.md scope ("a close, at any stage, books refused with the human's reason") and decisions 19, 20 and 21. Nothing in Out of scope is touched.
3. tester: wrote red tests for `AcceptanceClosed` in tests/application/test_acceptance_closed.py, one test per criterion.
      - criterion 1: tests/application/test_acceptance_closed.py::test_the_humans_comments_and_the_close_are_recorded_on_the_branch
      - criterion 2: ::test_a_comment_the_factory_posted_is_neither_recorded_nor_marked_read
      - criterion 3: ::test_a_blank_comment_gets_no_entry_and_is_marked_read
      - criterion 4: ::test_a_closed_acceptance_is_booked_refused_in_done_and_nothing_else_reaches_main. Parametrized: with cost records and without.
      - criterion 5: ::test_after_the_booking_the_branch_is_gone_and_a_second_handling_changes_nothing
      - criteria 6 and 15: ::test_after_a_kill_at_the_push_of_main_a_second_handling_books_once. One test with two rows, `BEFORE_PUSH` and `AFTER_PUSH`, both armed `after=1`. The `BEFORE_PUSH` row also checks that the comment and close records are already on `origin/<branch>`.
      - criterion 7: ::test_a_gone_branch_without_a_report_in_done_raises_and_changes_nothing
      - criterion 8: ::test_an_acceptance_closed_at_any_stage_is_booked_refused_without_a_reason. Three rows: reviewer working, reviewer asking (`blocked="question"`), and after the hand-over at `approval`.
      - criterion 9: ::test_an_event_the_handler_cannot_book_raises_its_reason_and_changes_nothing. Rows for another kind, a story, no acceptance stage, no pull request, and an open pull request.
      - criterion 10: ::test_the_handler_is_built_without_an_acceptance_stage
      - criterion 11: ::test_a_refused_feature_is_due_again_only_after_another_story_is_archived
      - criterion 12: ::test_a_main_moved_since_the_fetch_rejects_the_booking_after_the_close_is_recorded
      - criterion 13: ::test_a_refused_branch_deletion_fails_after_the_refusal_is_pushed
      - criterion 14: ::test_an_earlier_close_of_the_human_gets_no_second_close_record
      - Two test choices the coder should know:
        - A successful `handle` deletes the branch, so the tests for criteria 1–3 read `origin/<branch>` another way. A helper (`_record_only`) arms `KillPoint.BEFORE_PUSH` with `after=1`, which stops the handler at the push of main, after the branch push. This needs the comments and the close to be recorded in one push, as Interface step 2 says (one `WorkItemRecorder.record`).
        - For criterion 4, the test builds the expected recorded report itself with `append_entry` from the snapshot: the comment entry (dated with `created_at`), `comments_read`, then the close entry dated `CLOSED_ON`. It then compares `book_refusal(...)` of that report, as the writer renders it, with the file in `done/`.
      - The `publish` fixture moves the clock 2 days forward, to 2026-10-14, so the close's date differs from the comments' dates (2026-10-12).
      - Files created: tests/application/test_acceptance_closed.py.
      - Could not import: `AcceptanceClosed` from `factory.application.acceptance`, so collection fails with an ImportError, the expected reason. `make lint` is green. The type check was not run, as this stage skips it.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: implemented `AcceptanceClosed` in `src/factory/application/acceptance.py` (commit fc2504e). Every test in `tests/application/test_acceptance_closed.py` passes except both rows of `test_after_a_kill_at_the_push_of_main_a_second_handling_books_once`. lint, types, layers, sast, secrets and licences are green, so `make check` is red only on those two rows, and the cause is a mistake in the test, not in the handler.

   The test fails at `assert _reports_in_done(checkout) == ["F0002-A0001-acceptance.md"]`. The helper `_reports_in_done` returns `checkout.list_files("origin/main", DONE)`, filtered on `"-A"`. `Git.list_files` returns repository-relative paths, as its docstring says and as `src/factory/adapters/git_cli.py:187` implements. So the actual value is `["factory/features/F0002-todo/done/F0002-A0001-acceptance.md"]`: the right single report, compared against a bare file name. No change to the handler can make this assertion pass.

   Options:
   (a) Compare against the full path, `[DONE_REPORT]`, a constant the test already defines.
   (b) Strip the paths in `_reports_in_done` to file names, e.g. `PurePosixPath(name).name`.
   I would choose (a): it is the smallest change and reuses the existing constant. After your answer the coder ends with `tests` and names that change.

   What I built:
   - `AcceptanceClosed(boundaries, definition)` checks the event in the order the Interface gives (kind, acceptance, acceptance stage, closed pull request).
   - When `origin/<branch>` resolves, it checks the branch out and reads the cost records at `origin/<branch>` with `read_cost_records`.
   - Record step: `CommentCopier.unread` and `append` add the comments, then a `close` entry is appended unless a human `close` record already exists (found with `last_record`). It records once with the subject "close recorded".
   - Book step: it checks out main and, unless the file is already in `done/`, writes `book_refusal(...)` at `destination_path(path, "done")` plus the cost records beside it, then publishes "closed, refused".
   - Delete step: `WorkItemRecorder.delete_branch`.
   - When the branch is gone: it only deletes if the report is already in `done/` on `origin/main`, and otherwise raises "no report on the branch or the main branch".
   - I moved `AcceptanceHandOver._reviewer_role` to a module function `_reviewer_role(definition, kind)` so both handlers share it instead of having a second copy.

   Design choices:
   - Main decision: the cost records are read once from `origin/<branch>` and used for both the bill and the copy. I rejected reading the sidecar file in the checkout for the bill and then running `show_file` again for the copy, because both read the same text.
   - Noticed but not changed: a branch whose cost records file exists but is empty gets no copy on main, because the copy is skipped when there are no records.
   - The refactor step is still to do; it waits until `make check` is green.
5. human (pull request comment, 2026-10-15): (a): the tester compares against the full path, `[DONE_REPORT]`, in `test_after_a_kill_at_the_push_of_main_a_second_handling_books_once`, and changes nothing else. End with `tests` and name exactly that change.
6. coder: the human's answer (entry 5, option (a)) calls for a test change. Tester: in `tests/application/test_acceptance_closed.py::test_after_a_kill_at_the_push_of_main_a_second_handling_books_once`, change line 371 from `assert _reports_in_done(checkout) == ["F0002-A0001-acceptance.md"]` to `assert _reports_in_done(checkout) == [DONE_REPORT]`, and change nothing else. I made no code change this run. The handler is still as committed in fc2504e. The refactor step is still to do and comes once `make check` is green after this test change.
7. tester: made the test change the human approved in entry 5, option (a), which the coder named in entry 6.
      - The change is in tests/application/test_acceptance_closed.py::test_after_a_kill_at_the_push_of_main_a_second_handling_books_once, line 371. The assertion `assert _reports_in_done(checkout) == ["F0002-A0001-acceptance.md"]` is now `assert _reports_in_done(checkout) == [DONE_REPORT]`.
      - Why: `Git.list_files` returns repository-relative paths, so the old assertion compared a full path with a bare file name. `DONE_REPORT` is the full path the test already defines.
      - Nothing else in the file changed.
      - Ran `make test` once after the change: green, total coverage 99.52 %.

   `make lint`: lint: green
   `make test`: test: green
8. coder: the tester's change (entry 7) made the suite green. `make check` is green, with total coverage at 99.52 %. I did the refactor step that entry 4 had put off.
      - What I built: `AcceptanceClosed` in `src/factory/application/acceptance.py`, commit fc2504e, as entry 4 describes. In short:
        - It checks the event in the Interface's order.
        - It records the comments and one `close` entry on the branch in a single `WorkItemRecorder.record`, skipping the `close` entry when any human `close` record already exists.
        - It books `book_refusal(...)` and the branch's cost records at `destination_path(path, "done")` on main, unless they are already there.
        - It deletes the branch with `WorkItemRecorder.delete_branch`.
        - When the branch is gone, it only deletes when the report is already in `done/`, and otherwise raises "no report on the branch or the main branch".
        - `_reviewer_role(definition, kind)` is now a module function that both `AcceptanceHandOver` and `AcceptanceClosed` use.
      - Refactor (e5d791c): `handle` now builds `origin/<branch>` once and passes it to `_branch_records`. Before, two copies of the same f-string built it. Nothing else needed changing.
      - Main decision: the cost records are read once from `origin/<branch>` with `read_cost_records`, and that one read gives both the bill and the copy to main. I rejected reading the sidecar in the checkout for the bill and then calling `show_file` again for the copy, because both read the same text.
      - Noticed, not touched:
        - When the branch has a cost records file but it is empty, nothing is copied to main, because the copy is skipped when there are no records.
        - `handlers/closed.py:93` and `AcceptanceClosed._today` both compute "today in UTC" with the same one-line expression (`clock.now().astimezone(UTC).date()`). Sharing it would mean a change to F0007's handler, outside this ticket.

   `make check`: check: green
9. reviewer: No findings.

   Scope reviewed: `src/factory/application/acceptance.py` (the new `AcceptanceClosed`, and `_reviewer_role` moved out of `AcceptanceHandOver` so both handlers share it) and `tests/application/test_acceptance_closed.py`. The diff also touches `docs/runs/2026-10-12-overnight/night-log.md`, but that is the human's own commit f717116, not stage work.

   - Acceptance criteria: criteria 1–15 each map to the tests named in log entry 3. Criteria 6 and 15 are rows of one parametrized test. Each test checks what its criterion says.
     - Criterion 4 compares the whole rendered `book_refusal(...)` report. It checks the sidecar both with cost records and without, checks that only the report and sidecar changed on main, and checks that the proposed story is absent.
     - Criterion 9's rows also show the order of the checks: kind before acceptance, acceptance before stage, stage before pull request.
     - The "no work item" side of "not an acceptance" cannot be built: `Event`'s validator refuses a `closed` event without a work item.
     - The coder's entry 8 reports `make check` green, with coverage at 99.52 %.
   - Architecture: the handler stays in `factory.application` and reaches git only through `WorkItemRecorder`, `Git.resolve`/`show_file` and `read_cost_records`. `mkdir` on the checkout follows the existing pattern in `AcceptanceService.open`.
   - Security: no markers, no strings built into commands, and the error reasons are fixed texts.
   - Quality:
     - The steps follow the Interface's order: locate, record (one `record` when changed), book (skipped when the report is already in `done/`), delete.
     - No duplicate helper: no shared "today in UTC" helper exists to reuse. The same one-line expression in `handlers/closed.py:93` is inline code, not a helper.
     - Docstrings are present and say why.
   - Known gap, not a finding: the coder noted that a sidecar that exists but is empty is not copied to main (`if records:`). The Interface says "when it has one", but such a file is not produced in practice and no criterion covers it.
   - Ticket hygiene: the log gives the main decision (one read of `origin/<branch>` gives both the bill and the copy) and what was rejected. `Assignment` matches what was built. Docs criterion 17 still says what the operator must know.
