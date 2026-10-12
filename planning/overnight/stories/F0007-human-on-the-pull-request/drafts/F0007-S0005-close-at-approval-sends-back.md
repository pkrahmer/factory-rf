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
class ClosedHandler:
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

Rules:

- `reason_given(document)` is true when `document.state.journal` holds a record of kind `comment` whose number is greater than the number of the latest record of kind `result` (any number counts when there is no `result` record). Only the records are read, never the entries' text.
- `send_back_target(definition, approval)` is the second entry of `definition.stages[approval].next`, or `None` when `next` has fewer than two.
- `send_back_cap(definition, approval)` is the `round_cap` of the first stage, in the pipeline definition's order, whose `next[0]` is `approval` and which has a `round_cap`; `None` when there is none.
- `send_back_entry_text(target, round_number)` is `sent back to <target>, round <round_number>.`
- `send_back_question(round_number, cap, has_reason)`: when `cap` is not `None` and `round_number > cap`, `This story has now been sent back <round_number> times, more than <cap>. ` followed by `SEND_BACK_QUESTION`; otherwise, when `has_reason` is false, `The pull request was closed without a comment. ` followed by `SEND_BACK_QUESTION`; otherwise `None`.
- `ClosedHandler.handle` for a story whose stage is an approval stage of `definition` (its `approval` is true): it takes `target_of(event)` and `require_pull_request(target, "closed")`, and looks up `send_back_target` and `send_back_cap` for the stage. A missing target raises `CannotHandle("closed", ...)` before anything is recorded or reopened. Then, in this order:
  1. Record the close: `WorkItemRecorder.check_out(branch)`; read the work item; `CommentCopier.unread` and `append` the human's unread comments; unless the latest journal record is of kind `close`, append `NewEntry(speaker=HUMAN, kind="close", text=CLOSE_ENTRY_TEXT, on=<the date of boundaries.clock.now() in UTC>)`; set `handed_over` to `None`. When the document differs from the one read, record it with the subject `commit_subject(id, "close recorded")`.
  2. Reopen: `HostingService.reopen(number)`, then `HostingService.set_draft(number, True)`.
  3. Record the decision with the subject `commit_subject(id, "sent back")`: `new_round = state.round + 1`; append `NewEntry(speaker=FACTORY, kind="send_back", text=send_back_entry_text(<target>, new_round))`; when `send_back_question(new_round, <cap>, reason_given(<the document>))` is not `None`, append it as `NewEntry(speaker=FACTORY, kind="question", text=<it>)` and set `blocked="send_back"`, else leave `blocked` unset; set `stage` to the target, `round` to `new_round` and `claim` to `None`.
- The handler posts nothing. The question is posted by `AskHandler` (S0002) with kind `send_back` and the number of the question entry.
- A failing call raises; whatever was recorded stays recorded.

Tests: `tests/domain/test_send_back.py`, `tests/domain/test_post_texts.py` and `tests/application/handlers/test_closed_send_back.py`. The fixture definition's approval is `approval` (`next: [done, doing]`) and the stage that hands over to it is `smoke-test` with `round_cap: 3`.

## Acceptance criteria

1. `reason_given` is true when the journal records hold a `comment` numbered after the latest `result`, judged from the records alone: the document's body in the test has no journal text.
2. `reason_given` is false when every `comment` record is numbered before the latest `result` record, and false when there is no `comment` record (two cases, one test).
3. `send_back_target(definition, "approval")` is `doing` for the fixture definition, and `None` for a definition whose approval has only one entry in `next`.
4. `send_back_cap(definition, "approval")` is 3 for the fixture definition (the `round_cap` of `smoke-test`), and `None` for a definition in which no stage with a `round_cap` moves forward to the approval.
5. `SEND_BACK_QUESTION` is exactly the text of the Interface, and states three numbered options: comment, close again to discard, and mark ready and merge.
6. `send_back_entry_text("doing", 3)` is `sent back to doing, round 3.`
7. `send_back_question(3, 3, True)` is `None` (the round equals the cap) and so is `send_back_question(9, None, True)`; `send_back_question(2, 3, False)` is `The pull request was closed without a comment. ` followed by `SEND_BACK_QUESTION` (three cases, one test).
8. `send_back_question(4, 3, True)` and `send_back_question(4, 3, False)` are both `This story has now been sent back 4 times, more than 3. ` followed by `SEND_BACK_QUESTION`: past the cap, the cap wins.
9. The close is recorded before the pull request is reopened: when `reopen` fails, `handle` raises `HostingServiceError`, and the work item's remote branch holds the unread comments as entries, a `close` entry (speaker `human`, text `CLOSE_ENTRY_TEXT`, dated with the clock's date) and `handed_over` unset, while the stage is still the approval and the pull request is still closed.
10. After that failure, handling the event again reopens the pull request as a draft and records the decision, and the journal holds exactly one `close` record.
11. A story at the approval with `round` 2 and a reason is sent back within the cap: `stage` is `doing`, `round` is 3, `blocked` is unset, `claim` is unset, the journal ends with the `close` entry and a `send_back` entry (speaker `factory`, text `send_back_entry_text("doing", 3)`) and no `question` entry, and the pull request is open and a draft.
12. A comment copied at the close and a comment copied earlier (recorded as a `comment` entry after the latest `result`) both count as the reason (two cases, one test).
13. A close with no comment after the latest `result` records the send-back and then a `question` entry (speaker `factory`, text `send_back_question(<new round>, 3, False)`), sets `blocked` to `send_back` and `stage` to `doing`, and the pull request is open and a draft.
14. A close at `round` 3 (cap 3) with a reason records the `question` entry for the cap, `This story has now been sent back 4 times, more than 3. ` followed by `SEND_BACK_QUESTION`, with `round` 4 and `blocked == "send_back"`.
15. `handle` posts nothing; handling an `ask` event for the resulting state with `AskHandler` posts the question once, with kind `send_back` and `n` equal to the question entry's number.
16. A kill at `before-push` while the close is recorded leaves the remote branch as it was and the pull request still closed.
17. When the approval's `next` has only one entry, `handle` raises `CannotHandle` with kind `closed`, records nothing and leaves the pull request closed.
18. For a work item whose state has no pull request, `handle` raises `CannotHandle` with kind `closed` and records nothing.
19. make check stays green.
20. docs: `docs/operator-guide.md` explains the close at the approval (the comment that counts as the reason, the round cap, the three options of the send-back question) and that, after a kill between the reopen and the second record, the pull request is handed over again at the approval and the close has to be repeated; `docs/decisions.md` records why the close is recorded before the pull request is reopened.

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
