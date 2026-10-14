---
stage: doing
pr: 86
blocked: null
comments_seen: 4
round: 0
attempts: 0
---
# A close at the approval sends back, recorded first

## Assignment (as of log entry 1)

Build the second half of the handler of `closed` events: the human closes the pull request of a story that waits at an approval stage, which means "not like this". The handler records the close in the work item before it does anything else (the human's unread comments are copied, a `close` entry is added, the hand-over is marked as ended, all pushed), then reopens the pull request as a draft, then records the decision in a second push: the story goes back to the approval's second `next` stage with `round` + 1; when a reason was given (a comment after the latest `result`) and the round is within the cap of the stage that hands over to the approval, nothing more is needed; otherwise a send-back question with three options is recorded, `blocked` becomes `send_back`, and the `ask` handler (S0002) posts it. The reason is taken from the journal's data, never from the text, so the code does not interpret what the human wrote. If the reopen fails, the close stays recorded and the next tick finishes the send-back without a second `close` entry. It covers GH3.3 and R22 and keeps kept thing 1 (code never interprets the human's free text) and kept thing 11 (the three options of the question are existing paths: a comment, a second close, a merge). Acceptances are F0009's. No morning observation.

## Interface

`src/factory/domain/send_back.py`

```python
def reason_given(document: WorkItemDocument) -> bool: ...
def send_back_target(definition: PipelineDefinition, approval: str) -> str | None: ...
def send_back_cap(definition: PipelineDefinition, approval: str) -> int | None: ...
```

`src/factory/domain/post_texts.py` (adds)

```python
CLOSE_ENTRY_TEXT = "closed the pull request."
SEND_BACK_QUESTION = (
    "What should happen? 1. Comment what should change; the story is reworked with exactly that. "
    "2. Close the pull request again to discard the story: it goes back to the backlog as you wrote it, "
    "and its branch is deleted. 3. If closing was a mistake: mark the pull request ready for review "
    "and merge it, which accepts the story as it is."
)
def send_back_entry_text(target: str, round_number: int) -> str: ...
def send_back_question(round_number: int, cap: int | None, has_reason: bool) -> str | None: ...
```

`src/factory/application/handlers/closed.py` (the `ClosedHandler` of S0004 gains the approval case; its signature does not change)

```python
class ClosedHandler(Handler):      # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

Rules:

- `reason_given(document)` is true when `document.state.journal` holds a record of kind `comment` whose number is greater than the number of the latest record of kind `result` (any number counts when there is no `result` record). Only the records are read, never the entries' text.
- `send_back_target(definition, approval)` is the second entry of `definition.stages[approval].next`, or `None` when `next` has fewer than two.
- `send_back_cap(definition, approval)` is the `round_cap` of the first stage, in the pipeline definition's order, whose `next[0]` is `approval` and which has a `round_cap` (a stage that hands over to the approval but has no `round_cap` is skipped); `None` when there is none.
- `send_back_entry_text(target, round_number)` is `sent back to <target>, round <round_number>.`
- `send_back_question(round_number, cap, has_reason)`: when `cap` is not `None` and `round_number > cap`, `This story has now been sent back <round_number> times, more than <cap>. ` followed by `SEND_BACK_QUESTION`; otherwise, when `has_reason` is false, `The pull request was closed without a comment. ` followed by `SEND_BACK_QUESTION`; otherwise `None`.
- `ClosedHandler.handle` for a story whose stage is an approval stage of `definition` (its `approval` is true): it takes `target_of(event)` and `require_pull_request(target, "closed")`, and looks up `send_back_target` and `send_back_cap` for the stage. A missing target raises `CannotHandle("closed", ...)` before anything is recorded or reopened. Then, in this order:
  1. Record the close: `WorkItemRecorder.check_out(branch)`; read the work item; `CommentCopier.unread` and `append` the human's unread comments; unless the journal already holds a record of kind `close` numbered after the latest record of kind `result` (any `close` record counts when there is no `result` record), append `NewEntry(speaker=HUMAN, kind="close", text=CLOSE_ENTRY_TEXT, on=<the date of boundaries.clock.now() in UTC>)`; set `handed_over` to `None`. When the document differs from the one read, record it with the subject `commit_subject(id, "close recorded")`.
  2. Reopen: `HostingService.reopen(number)`, then `HostingService.set_draft(number, True)`.
  3. Record the decision with the subject `commit_subject(id, "sent back")`: `new_round = state.round + 1`; append `NewEntry(speaker=FACTORY, kind="send_back", text=send_back_entry_text(<target>, new_round))`; when `send_back_question(new_round, <cap>, reason_given(<the document>))` is not `None`, append it as `NewEntry(speaker=FACTORY, kind="question", text=<it>)` and set `blocked="send_back"`, else leave `blocked` unset; set `stage` to the target, `round` to `new_round` and `claim` to `None` (set directly in the state, not through `ClaimService.release`, which is built for an instance name that `ClosedHandler(boundaries, definition)` does not hold; `tests/test_claim_ownership.py` forbids only building a claim and judging a lease outside the service).
  4. After the decision is pushed, `HostingService.set_labels(number, labels_for(<the new state>))` (`factory.domain.labels`, F0005-S0007), so that the pull request does not keep `stage:approval` until the next stage finishes. A `set_labels` that fails raises; the decision stays recorded and the label stays stale until the next stage's result commit writes it (the labels are a projection of the stage, written and never read back, R10).
- The handler posts nothing. The question is posted by `AskHandler` (S0002) with kind `send_back` and the number of the question entry.
- A failing call raises; whatever was recorded stays recorded.

Tests: `tests/domain/test_send_back.py`, `tests/domain/test_send_back_texts.py` (a new file: `tests/domain/test_post_texts.py` is F0003-S0003's) and `tests/application/handlers/test_closed_send_back.py`. The fixture definition's approval is `approval` (`next: [done, doing]`) and the stage that hands over to it is `smoke-test` with `round_cap: 3`. A push of the decision that the remote rejects is made by a test subclass of the fake hosting service whose `set_draft` makes `human.push_file` push a commit to the work item's branch.

## Acceptance criteria

1. `reason_given` is true when the journal records hold a `comment` numbered after the latest `result`, and true when they hold a `comment` and no `result` record at all, judged from the records alone: the document's body in the test has no journal text (two cases, one test).
2. `reason_given` is false when every `comment` record is numbered before the latest `result` record, and false when there is no `comment` record (two cases, one test).
3. `send_back_target(definition, "approval")` is `doing` for the fixture definition, and `None` for a definition whose approval has only one entry in `next`.
4. `send_back_cap(definition, "approval")` is 3 for the fixture definition (the `round_cap` of `smoke-test`); it is 3 as well for the fixture definition with the stage `acceptance` (which hands over to the approval and has no `round_cap`) placed before `smoke-test`; and it is `None` for a definition in which no stage with a `round_cap` moves forward to the approval (three cases, one test).
5. `SEND_BACK_QUESTION` is exactly the text of the Interface, and states three numbered options: comment, close again to discard, and mark ready and merge.
6. `send_back_entry_text("doing", 3)` is `sent back to doing, round 3.`
7. `send_back_question(3, 3, True)` is `None` (the round equals the cap) and so is `send_back_question(9, None, True)`; `send_back_question(2, 3, False)` is `The pull request was closed without a comment. ` followed by `SEND_BACK_QUESTION` (three cases, one test).
8. `send_back_question(4, 3, True)` and `send_back_question(4, 3, False)` are both `This story has now been sent back 4 times, more than 3. ` followed by `SEND_BACK_QUESTION`: past the cap, the cap wins.
9. The close is recorded before the pull request is reopened: when `reopen` fails, `handle` raises `HostingServiceError`, and the work item's remote branch holds the unread comments as entries, a `close` entry (speaker `human`, text `CLOSE_ENTRY_TEXT`, dated with the clock's date) and `handed_over` unset, while the stage is still the approval and the pull request is still closed.
10. After that failure, handling the event again, with no comment written in between, reopens the pull request as a draft and records the decision, and the journal holds exactly one `close` record.
11. A story at the approval with `round` 2 and a reason is sent back within the cap: `stage` is `doing`, `round` is 3, `blocked` is unset, `claim` is unset, the journal ends with the `close` entry and a `send_back` entry (speaker `factory`, text `send_back_entry_text("doing", 3)`) and no `question` entry, and the pull request is open and a draft.
12. A comment copied at the close and a comment copied earlier (recorded as a `comment` entry after the latest `result`) both count as the reason (two cases, one test).
13. A close with no comment after the latest `result` records the send-back and then a `question` entry (speaker `factory`, text `send_back_question(<new round>, 3, False)`), sets `blocked` to `send_back` and `stage` to `doing`, and the pull request is open and a draft.
14. A close at `round` 3 (cap 3) with a reason records the `question` entry for the cap, `This story has now been sent back 4 times, more than 3. ` followed by `SEND_BACK_QUESTION`, with `round` 4 and `blocked == "send_back"`.
15. `handle` posts nothing; handling an `ask` event for the resulting state with `AskHandler` posts the question once, with kind `send_back` and `n` equal to the question entry's number.
16. A kill at `before-push` while the close is recorded leaves the remote branch as it was and the pull request still closed.
17. When the approval's `next` has only one entry, `handle` raises `CannotHandle` with kind `closed`, records nothing and leaves the pull request closed.
18. For a work item whose state has no pull request, `handle` raises `CannotHandle` with kind `closed` and records nothing.
19. When the push of the decision is rejected (the human pushed to the branch after the reopen), `handle` raises `PushFailed` with outcome `rejected`, the remote branch still holds the `close` entry and the human's commit, and handling the event again sends the story back once: the journal holds one `close` record and one `send_back` record.
20. A comment that the human writes after the reopen failed and before the retry is copied by the retry as a `comment` entry, and the journal still holds exactly one `close` record (the retry does not close again); that comment counts as the reason.
21. After the decision is pushed, `hosting.labels(<pull request>)` is `["stage:doing"]`; when `set_labels` fails, `handle` raises `HostingServiceError` and the remote branch holds the decision (two cases, one test).
22. A story at the approval whose journal holds a `close` record numbered before the latest `result` record (an earlier send-back) gets a new `close` entry when it is closed again, and the journal then holds two `close` records; a story whose journal holds a `close` record and no `result` record gets no second `close` entry.
23. make check stays green.
24. docs: `docs/operator-guide.md` explains the close at the approval (the comment that counts as the reason, the round cap, the three options of the send-back question) and that, after a kill between the reopen and the second record, the pull request is handed over again at the approval and the close has to be repeated; `docs/decisions.md` records why the close is recorded before the pull request is reopened.

## Demo

```bash
uv run python -c "
from factory.domain.journal import JournalRecord
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.post_texts import SEND_BACK_QUESTION, send_back_question
from factory.domain.send_back import reason_given, send_back_cap, send_back_target
from factory.domain.work_item import WorkItemDocument, WorkItemState
definition = PipelineDefinition(contract='1.0', roles={'coder': {'write_paths': ['src/*']}, 'smoke-tester': {'write_paths': ['x']}}, stages={'doing': {'role': 'coder', 'next': ['smoke-test']}, 'smoke-test': {'role': 'smoke-tester', 'next': ['approval', 'doing'], 'round_cap': 3}, 'approval': {'approval': True, 'next': ['done', 'doing']}, 'done': {}})
print(send_back_target(definition, 'approval'), send_back_cap(definition, 'approval'))
def document(*pairs):
    records = [JournalRecord(number=n, speaker=s, kind=k) for n, (s, k) in enumerate(pairs, 1)]
    return WorkItemDocument(state=WorkItemState(stage='approval', journal=records), body='# T\n')
print(reason_given(document(('human', 'created'), ('smoke-tester', 'result'))))
print(reason_given(document(('human', 'created'), ('smoke-tester', 'result'), ('human', 'comment'), ('human', 'close'))))
print(send_back_question(3, 3, True))
print(send_back_question(3, 3, False) == 'The pull request was closed without a comment. ' + SEND_BACK_QUESTION)
print(send_back_question(4, 3, True) == 'This story has now been sent back 4 times, more than 3. ' + SEND_BACK_QUESTION)
"
```
Expect: six lines: `doing 3`, `False`, `True`, `None`, `True`, `True`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: 1. The Interface rule for step 1 of `ClosedHandler.handle` says a `close` entry is added "unless the journal already holds a record of kind `close` numbered after the latest record of kind `result` (any `close` record counts when there is no `result` record)". No criterion tests the side where a `close` is added: a journal that holds an older `close` numbered before the latest `result`, as after an earlier send-back and rework, gets a new `close` entry. Criteria 10 and 20 only cover a `close` after the latest `result` that is not repeated. Without this criterion a coder can skip any earlier `close` and pass every test. I'd add a criterion before the two closing ones: "A story at the approval whose journal holds a `close` record numbered before the latest `result` record (an earlier send-back) gets a new `close` entry when it is closed again, and the journal then holds two `close` records." Please confirm or reword it.
   2. Optional, not blocking: `any close counts when there is no result` has no case either. I'd fold it into the same criterion as a second case (a `close` and no `result` record: no second `close`). Do you want that?
   The other checks passed. The Interface, the Demo and the other criteria are fine. The scope and architecture match `FEATURE.md`.
3. human (pull request comment, 2026-10-14): 1: confirmed as you worded it. 2: yes, fold it into the same criterion as a second case. The criterion, before the two closing ones: "A story at the approval whose journal holds a `close` record numbered before the latest `result` record (an earlier send-back) gets a new `close` entry when it is closed again, and the journal then holds two `close` records; a story whose journal holds a `close` record and no `result` record gets no second `close` entry." The Interface stays as it is.
4. intake: accepted. Carried in from log entry 3 (the human's answer): added criterion 22 before the two closing ones ("A story at the approval whose journal holds a `close` record numbered before the latest `result` record ... gets a new `close` entry ... two `close` records; a story whose journal holds a `close` record and no `result` record gets no second `close` entry"), worded as the human gave it. `make check` and `docs:` are now criteria 23 and 24. The Interface and the Assignment are unchanged, as the human said.
   - Interface: names concrete modules (`domain/send_back.py`, `domain/post_texts.py`, `application/handlers/closed.py`) with signatures and ordered handler steps. Every rule is stated exactly.
   - Criteria: each is testable by one test function. Every Interface rule has a criterion for its failing side: no reason, past the cap, one `next` entry, no pull request, a rejected push, a failed reopen, a failed `set_labels`. The two sides of the `close`-record rule are covered by criteria 10, 20 and 22.
   - Demo: runnable with `uv run python -c`. The `Expect:` line gives six checkable lines, and I traced them against the Interface rules.
   - Architecture: the pure rules are in domain, the handler is in application and uses the Boundaries interfaces. The claim is set directly in the state, as the Interface explains.
   - Scope: within the feature's scope (send-back, GH3.3, R22). It leaves the acceptances to F0009 and does not touch the `ask` handler.
5. tester: Wrote red tests for every acceptance criterion from the Interface. `make lint` is green. `make test` fails with 3 collection errors, as expected: `factory.domain.send_back` does not exist yet, and `factory.domain.post_texts` does not have `CLOSE_ENTRY_TEXT`, `SEND_BACK_QUESTION`, `send_back_entry_text` or `send_back_question` yet.

   Files created:
   - `tests/domain/test_send_back.py`
   - `tests/domain/test_send_back_texts.py`
   - `tests/application/handlers/test_closed_send_back.py`

   Criterion → test:
   - criterion 1: tests/domain/test_send_back.py::test_a_comment_after_the_latest_result_or_without_any_result_is_a_reason (two cases; the body is `# T\n` with no journal text)
   - criterion 2: tests/domain/test_send_back.py::test_no_comment_after_the_latest_result_is_no_reason (two cases)
   - criterion 3: tests/domain/test_send_back.py::test_the_send_back_target_is_the_second_next_of_the_approval_or_none_without_one
   - criterion 4: tests/domain/test_send_back.py::test_the_send_back_cap_is_the_round_cap_of_the_first_capped_stage_handing_over (three cases; for the `None` case, `doing` has a `round_cap` but does not hand over to the approval)
   - criterion 5: tests/domain/test_send_back_texts.py::test_the_send_back_question_offers_comment_close_again_and_merge. tests/domain/test_send_back_texts.py::test_the_close_entry_text_says_the_pull_request_was_closed also pins `CLOSE_ENTRY_TEXT` from the Interface.
   - criterion 6: tests/domain/test_send_back_texts.py::test_the_send_back_entry_names_the_target_and_the_round
   - criterion 7: tests/domain/test_send_back_texts.py::test_within_the_cap_only_a_missing_reason_asks (three cases; round equal to the cap is the accepted side of the boundary)
   - criterion 8: tests/domain/test_send_back_texts.py::test_past_the_cap_the_cap_question_wins_with_or_without_a_reason (4 > 3 is the refused side)
   - criterion 9: tests/application/handlers/test_closed_send_back.py::test_a_failed_reopen_leaves_the_close_recorded_and_the_story_at_the_approval (also checks the subject `close recorded` and the date in the rendered entry; the clock is moved to 2026-10-14 so that date differs from every other date in the test)
   - criterion 10: …::test_the_event_handled_again_after_a_failed_reopen_sends_back_with_one_close
   - criterion 11: …::test_a_close_with_a_reason_within_the_cap_sends_the_story_back_without_a_question (the state carries a claim before the close, so `claim` unset is a real check)
   - criterion 12: …::test_a_comment_copied_at_the_close_or_earlier_counts_as_the_reason (two cases)
   - criterion 13: …::test_a_close_without_a_comment_after_the_latest_result_records_the_question
   - criterion 14: …::test_a_close_past_the_round_cap_records_the_cap_question_even_with_a_reason
   - criterion 15: …::test_the_send_back_posts_nothing_and_the_ask_handler_posts_its_question_once (`AskHandler` runs twice and exactly one post is made)
   - criterion 16: …::test_a_kill_before_the_close_is_pushed_changes_nothing
   - criterion 17: …::test_an_approval_with_one_next_stage_cannot_be_sent_back_and_nothing_is_recorded (`PIPELINE_YAML` with `approval: next: [done]`, parsed through the pipeline reader)
   - criterion 18: …::test_a_story_without_a_pull_request_cannot_be_sent_back_and_nothing_is_recorded
   - criterion 19: …::test_a_rejected_push_of_the_decision_keeps_the_close_and_a_retry_sends_back_once. It uses the test subclass `_PushingOnDraft(FakeHostingService)`: once armed, its `set_draft` pushes `notes.md` to the branch through `human.push_file`. It is swapped in with `dataclasses.replace(boundaries, hosting=...)`.
   - criterion 20: …::test_a_comment_written_before_the_retry_is_copied_and_counts_as_the_reason
   - criterion 21: …::test_after_the_decision_the_labels_name_the_target_stage (two cases: labels are `["stage:doing"]`; and a failed `set_labels` raises while the decision stays recorded)
   - criterion 22: …::test_only_a_close_recorded_since_the_latest_result_spares_a_new_close_entry (two cases: two `close` records, and one)
   - criteria 23 and 24 are not tests (`make check`, docs).

   Notes for the coder:
   - The handler tests build each story at stage `approval` on its branch with `handed_over="approval"`. Before the event, the pull request is marked ready and then closed by the human, so "reopened as a draft" is a real change.
   - The pipeline is the shared `PIPELINE_YAML`. In it, `acceptance` comes after `smoke-test`, so the cap is 3.

   Nothing is open; no criterion needed interpreting.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
6. coder: Built the send-back at the approval and committed it as c985a77. Every new test passes except one, and that one fails because of how the test is built, not because of the code. `make check` is red only because of that test.

   What I built:
   - `src/factory/domain/send_back.py`: `reason_given`, `send_back_target` and `send_back_cap`. It also has a public helper, `recorded_since_latest_result(document, kind)`. `reason_given` uses it for `comment`, and the handler uses it for `close`, so both read the records with the same "after the latest `result`" rule.
   - `src/factory/domain/post_texts.py`: `CLOSE_ENTRY_TEXT`, `SEND_BACK_QUESTION`, `send_back_entry_text` and `send_back_question`.
   - `src/factory/application/handlers/closed.py`: `ClosedHandler` now handles a close at an approval stage. It checks the pull request and the send-back target first, then works in four steps:
     1. Records the close: copies the unread comments with `CommentCopier.unread` and `append`, adds a `close` entry unless one is already recorded since the latest `result`, unsets `handed_over`, and pushes only if the document changed.
     2. Reopens the pull request as a draft.
     3. Records the decision: the `send_back` entry, plus a `question` entry and `blocked="send_back"` when `send_back_question` returns a question; it sets `stage`, `round` and `claim=None` directly in the state.
     4. Calls `set_labels(labels_for(...))`.
   - Main design decision: I copy the comments inside the "close recorded" commit with `append`, rather than through `CommentCopier.copy`, which would be a separate push. One push keeps a kill between the two from leaving comments recorded without the close. That matches the Interface's step 1.

   The failing test: `tests/application/handlers/test_closed_send_back.py::test_a_close_with_a_reason_within_the_cap_sends_the_story_back_without_a_question` (criterion 11). The test's `CLAIM` is `Claim(stage="smoke-test", ...)`, and the `publish` fixture builds `WorkItemState(stage="approval", claim=CLAIM)`. `WorkItemState._claim_is_for_the_current_stage` refuses that pairing with a `ValidationError` in the fixture, before the handler runs. No change to the handler can make this test pass.

   Options:
   - (a) Change the test's `CLAIM` to `stage="approval"`. The criterion's check that `claim` ends up unset stays a real check. **I'd choose this.**
   - (b) Drop `claim=CLAIM` from that test, which leaves "claim is unset" checked only against a state that never had one.
   - (c) Relax the domain validator. I'd reject this: it is a rule outside this ticket.

   If you choose (a) or (b), I'll end the next run with `tests` and name exactly that change for the tester.

   Not yet done: the refactor pass. I'll do it with `make check` green, after the test is fixed.
7. human (pull request comment, 2026-10-14): (a): change that test's `CLAIM` to `stage="approval"`, so the check that `claim` ends up unset stays a real one; the domain validator stays as it is. End with `tests` and name exactly that change.
8. coder: Back to the tester, following the human's answer in log entry 7 (option (a)). The test change: in `tests/application/handlers/test_closed_send_back.py`, change the module constant `CLAIM` (line 55) from `stage="smoke-test"` to `stage="approval"`. That constant is used only by `test_a_close_with_a_reason_within_the_cap_sends_the_story_back_without_a_question` (criterion 11). With the change, the `publish` fixture can build `WorkItemState(stage="approval", claim=CLAIM)` without `_claim_is_for_the_current_stage` refusing it, and the check that `claim` ends up unset is still a real one. The domain validator stays as it is. No code changes in this run. The implementation is still c985a77. The refactor pass is still open and will happen in the next doing run, once `make check` is green.
9. tester: tester (approved test change): I made the change the human chose in log entry 7 (option (a)), as the coder's entry 8 names it. In `tests/application/handlers/test_closed_send_back.py`, the module constant `CLAIM` now has `stage="approval"` instead of `stage="smoke-test"`. Only `test_a_close_with_a_reason_within_the_cap_sends_the_story_back_without_a_question` (criterion 11) uses it. The `publish` fixture can now build `WorkItemState(stage="approval", claim=CLAIM)` without `_claim_is_for_the_current_stage` refusing it, and the test still really checks that `claim` ends up unset. Nothing else changed, and no code was touched. `make test`: test: green (total coverage 99.25%). Still open for the coder: the refactor pass that entry 8 names.

   `make lint`: lint: green
   `make test`: test: green
