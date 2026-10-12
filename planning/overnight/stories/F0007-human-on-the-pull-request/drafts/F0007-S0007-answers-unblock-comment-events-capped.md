# Answers unblock, and comment events are capped

## Assignment (as of log entry 1)

Build the handler of `comment` events and the rule for what an answer does. A work item waits for the human when `blocked` is set; the human's next comment answers it: the comments are copied into the journal by id (S0001) and, in the same commit, the wait ends: `question`, `round_cap` and `send_back` are cleared; `attempts_cap` is cleared and `attempts` goes back to 0; `crash_cap` is cleared and `crashes` goes back to 0 (the interface sheet's `Blocked` table). A comment on a work item that is not blocked, at an approval for instance, is only recorded. A comment event that fails is bounded like every other event: tried no more often than `ERROR_CAP` (3) on the same remote state and then reported once on the pull request, and a restart does not report it twice. The story proves that bound for the comment event and for one other pull request event (`ask`) through the dispatcher. It covers ST1.1 and R28 and keeps kept thing 14 (the error is one of the four ways a work item does not move forward). The question of the crash cap and the rerun are F0008's; only the answer's effect on the state is here. No morning observation.

## Interface

`src/factory/domain/answers.py`

```python
def unblock(state: WorkItemState) -> WorkItemState: ...
```

`src/factory/application/handlers/comments.py` (adds to the module of S0001)

```python
class CommentHandler:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def handle(self, event: Event) -> None: ...
```

Rules:

- `unblock(state)` returns the state with `blocked` cleared and everything else as it was, except that `attempts` is 0 when `blocked` was `attempts_cap` and `crashes` is 0 when `blocked` was `crash_cap`. A state with `blocked` unset is returned as it is (an equal state). `round` is never changed: after a round-cap answer the next send-back at the cap asks again.
- `CommentHandler.handle` takes `target_of(event)` and `require_pull_request(target, "comment")`, and calls `CommentCopier(boundaries).copy(snapshot, number, adjust)` where `adjust` replaces the document's state with `unblock(state)`. The comments and the end of the wait are therefore one commit. When no comment is recorded, nothing is written and the work item stays blocked.
- A comment at an approval stage, or on a work item whose `blocked` is unset, is recorded and changes nothing else.
- Every failure leaves `handle` by raising; the handler catches nothing. The dispatcher counts the error per event and remote state, tries it up to `ERROR_CAP` (3) times and reports it once (F0006).

Tests: `tests/domain/test_answers.py` and `tests/application/handlers/test_comment_handler.py`. The dispatcher tests build `Dispatcher({"comment": ..., "ask": ...}, TickStatus(), StopService(boundaries))` and count the handler's calls with a small wrapper that delegates to the real handler; failures are injected with `hosting.fail_next("list_comments", times=10)` and, for `ask`, with a work item at the attempts cap that has no stall entry.

## Acceptance criteria

1. `unblock` clears `blocked` and changes nothing else for `question`, `round_cap` and `send_back` (three cases, one test); `round` is unchanged.
2. `unblock` of a state with `blocked == "attempts_cap"` and `attempts == 2` clears `blocked` and sets `attempts` to 0, leaving `round` and `crashes` as they were.
3. `unblock` of a state with `blocked == "crash_cap"` and `crashes == 2` clears `blocked` and sets `crashes` to 0, leaving `round` and `attempts` as they were.
4. `unblock` of a state with `blocked` unset returns an equal state.
5. `CommentHandler.handle` for a blocked work item with a new human comment copies the comment into the journal and clears the wait in one commit: the remote branch gains exactly one commit, and in it `comments_read` holds the id and `blocked` is unset.
6. With `blocked == "attempts_cap"`, the same commit sets `attempts` to 0.
7. A blocked work item whose pull request has no new human comment stays blocked, and the remote branch does not move.
8. A blocked work item whose only new comments carry the factory marker stays blocked, and the remote branch does not move.
9. A comment on a work item at an approval stage (not blocked) is recorded in the journal, and `stage`, `blocked`, `round`, `attempts`, `crashes` and `handed_over` are as they were.
10. A comment on an in-flight work item that is not blocked is recorded and changes no other state field.
11. When `list_comments` fails, `handle` raises `HostingServiceError` and the remote branch does not move.
12. For a work item whose state has no pull request, `handle` raises `CannotHandle` with kind `comment`, and records nothing.
13. A `comment` event that fails every time (ST1.1), dispatched four times on the same remote state, gives the outcomes `error`, `error`, `reported`, `capped`; the handler is called three times; the pull request has no factory post after the second dispatch, exactly one after the third, with key kind `error` and `n` equal to the first 12 digits of the remote state, and still exactly one after the fourth.
14. An `ask` event that fails every time behaves the same way: outcomes `error`, `error`, `reported`, `capped`, three calls, one post of kind `error` after the third dispatch and still one after the fourth.
15. After the report, a new `TickStatus` (a restart) lets the same failing comment event be tried three times again, and the pull request still has exactly one factory post of kind `error`.
16. make check stays green.
17. docs: `docs/operator-guide.md` states which comment answers which wait and what each answer resets (`attempts` for the attempts cap, `crashes` for the crash cap, nothing else), that a comment at an approval is only recorded, and that a failing comment event is tried three times and then reported once on the pull request; `docs/decisions.md` records why every event, comment events included, goes through the error cap.

## Demo

```bash
uv run python -c "
from factory.domain.answers import unblock
from factory.domain.work_item import WorkItemState
for blocked in ('question', 'round_cap', 'send_back', 'attempts_cap', 'crash_cap', None):
    after = unblock(WorkItemState(stage='doing', blocked=blocked, round=2, attempts=2, crashes=2))
    print(blocked, after.blocked, after.round, after.attempts, after.crashes)
"
```
Expect: six lines: `question None 2 2 2`, `round_cap None 2 2 2`, `send_back None 2 2 2`, `attempts_cap None 2 0 2`, `crash_cap None 2 2 0`, `None None 2 2 2`.

```bash
uv run python -c "
from types import SimpleNamespace
from factory.application.handlers.comments import CommentHandler
from factory.domain.events import Event
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
document = WorkItemDocument(state=WorkItemState(stage='doing', blocked='question'), body='# T
')
snapshot = WorkItemSnapshot(id='F0001-S0001', path='factory/features/F0001-x/in-progress/F0001-S0001-y.md', folder='in-progress', branch='work-item/F0001-S0001', branch_commit='1' * 40, document=document)
handler = CommentHandler(SimpleNamespace())
try:
    handler.handle(Event(kind='comment', work_item=snapshot, remote_state='1' * 40))
except Exception as error:
    print(type(error).__name__, error)
"
```
Expect: one line, `CannotHandle cannot handle comment: work item F0001-S0001 has no pull request`: a comment event for a work item without a pull request leaves the handler by raising, and nothing was swallowed.

## Log (append only)

1. 2026-10-12 human: created.
