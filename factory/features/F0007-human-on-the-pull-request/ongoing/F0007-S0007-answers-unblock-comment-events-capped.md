---
stage: doing
pr: 88
blocked: null
comments_seen: 2
round: 0
attempts: 0
---
# Answers unblock, and comment events are capped

## Assignment (as of log entry 1)

Build the handler of `comment` events and the rule for what an answer does. A work item waits for the human when `blocked` is set; a comment written after the factory posted the question answers it: the comments are copied into the journal by id (S0001) and, in the same commit, the wait ends: `question`, `round_cap` and `send_back` are cleared; `attempts_cap` is cleared and `attempts` goes back to 0; `crash_cap` is cleared and `crashes` goes back to 0 (the interface sheet's `Blocked` table). A comment that is older than the post of the question is only recorded and the wait stays, because the watcher raises `comment` ahead of `ask` (F0006-S0002, tier 2): a comment that the human wrote while the stages worked, copied at the stop, must not answer a question the human has not seen. A comment on a work item that is not blocked, at an approval for instance, is only recorded. A comment event that fails is bounded like every other event: tried no more often than `ERROR_CAP` (3) on the same remote state and then reported once on the pull request, and a restart does not report it twice. The story proves that bound for the comment event and for one other pull request event (`ask`) through the dispatcher. It covers ST1.1 and R28 and keeps kept thing 10 (ask, don't guess: a question is recorded, then posted, and no comment the human has not seen next to it answers it) and kept thing 14 (the error is one of the four ways a work item does not move forward). The question of the crash cap and the rerun are F0008's; only the answer's effect on the state is here. No morning observation.

## Interface

`src/factory/domain/answers.py`

```python
def unblock(state: WorkItemState) -> WorkItemState: ...
```

`src/factory/application/handlers/comments.py` (adds to the module of S0001)

```python
class CommentHandler(Handler):      # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries) -> None: ...
    def handle(self, event: Event) -> None: ...
```

Rules:

- `unblock(state)` returns the state with `blocked` cleared and everything else as it was, except that `attempts` is 0 when `blocked` was `attempts_cap` and `crashes` is 0 when `blocked` was `crash_cap`. A state with `blocked` unset is returned as it is (an equal state). `round` is never changed: after a round-cap answer the next send-back at the cap asks again.
- `CommentHandler.handle` takes `target_of(event)` and `require_pull_request(target, "comment")`. When `target.state.blocked` is unset it calls `CommentCopier(boundaries).copy(snapshot, number)` with no `adjust`: the comments are recorded and nothing else changes. When it is set, it first lists the pull request's comments with `HostingService.list_comments(number)` and calls `CommentCopier(boundaries).copy(snapshot, number, adjust)`.
- `adjust(document, comments)` ends the wait when and only when both hold: (a) the wait has a post: the pull request holds a comment of the factory whose key is `PostKey(work_item=<id>, kind=<document.state.blocked>, n=str(<number of the document's latest journal record of kind question>))` (the post that `AskHandler` makes, S0002), and a document with no `question` record has none; (b) one of the `comments` handed to `adjust` has a non-blank body and an id greater than the id of that post. It then returns the document with its state replaced by `unblock(state)`; otherwise it returns the document as it is. Comments older than the post, blank comments and a wait whose question is not posted yet are therefore recorded and the work item stays blocked. The comments, the post and the end of the wait are read from data (ids, keys, records), never from what a comment says.
- The comments and the end of the wait are one commit. When no comment is recorded, nothing is written and the work item stays blocked.
- A comment at an approval stage, or on a work item whose `blocked` is unset, is recorded and changes nothing else.
- Every failure leaves `handle` by raising; the handler catches nothing. The dispatcher counts the error per event and remote state, tries it up to `ERROR_CAP` (3) times and reports it once (F0006).
- F0006-S0002's `question_posted` compares the post's `n` with the number of the latest `question` record, not of the last record, so the comments this story records after a question do not make the watcher raise `ask` again. This rule is built and tested by F0006-S0002 (`tests/domain/test_evaluation.py`); this story only relies on it.

Tests: `tests/domain/test_answers.py` and `tests/application/handlers/test_comment_handler.py`. The test for a wait that has a post makes the post with `AskHandler` (S0002) or with `hosting.post_comment` and the key above; the human's comments are `hosting.add_human_comment` before or after it. The dispatcher tests build `Dispatcher({"comment": ..., "ask": ...}, TickStatus(), StopService(boundaries))` and count the handler's calls with a small wrapper, a subclass of `Handler`, that delegates to the real handler; failures are injected with `hosting.fail_next("list_comments", times=10)` and, for `ask`, with a work item at the attempts cap that has no stall entry.

## Acceptance criteria

1. `unblock` clears `blocked` and changes nothing else for `question`, `round_cap` and `send_back` (three cases, one test); `round` is unchanged.
2. `unblock` of a state with `blocked == "attempts_cap"` and `attempts == 2` clears `blocked` and sets `attempts` to 0, leaving `round` and `crashes` as they were.
3. `unblock` of a state with `blocked == "crash_cap"` and `crashes == 2` clears `blocked` and sets `crashes` to 0, leaving `round` and `attempts` as they were.
4. `unblock` of a state with `blocked` unset returns an equal state.
5. `CommentHandler.handle` for a blocked work item whose question is posted, with a new human comment written after the post, copies the comment into the journal and clears the wait in one commit: the remote branch gains exactly one commit, and in it `comments_read` holds the id and `blocked` is unset.
6. With `blocked == "attempts_cap"` and its question posted, a new human comment written after the post gives a commit that also sets `attempts` to 0.
7. A blocked work item whose pull request has no new human comment stays blocked, and the remote branch does not move.
8. A blocked work item whose only new comments carry the factory marker stays blocked, and the remote branch does not move.
9. A comment on a work item at an approval stage (not blocked) is recorded in the journal, and `stage`, `blocked`, `round`, `attempts`, `crashes` and `handed_over` are as they were.
10. A comment on an in-flight work item that is not blocked is recorded and changes no other state field.
11. When `list_comments` fails, `handle` raises `HostingServiceError` and the remote branch does not move.
12. For a work item whose state has no pull request, `handle` raises `CannotHandle` with kind `comment`, and records nothing.
13. A human comment written before the factory posted the question (its id is smaller than the post's) is recorded as an entry and its id is in `comments_read`, in one commit, and `blocked` is still set: the next comment, written after the post, ends the wait.
14. A blocked work item whose question has not been posted yet (the `question` record exists, no factory comment carries its key) records a new human comment and stays blocked, and so does one with `blocked` set and no `question` record at all, and so does one whose only post is keyed to an earlier question number while a later `question` record is not posted yet (three cases, one test).
15. Of two new comments, one written before the post and one after it, both are recorded in the journal and the wait ends, in one commit.
16. A comment with a blank body written after the post gets its id into `comments_read`, gets no entry, and leaves the work item blocked.
17. A `comment` event that fails every time (ST1.1), dispatched four times on the same remote state, gives the outcomes `error`, `error`, `reported`, `capped`; the handler is called three times; the pull request has no factory post after the second dispatch, exactly one after the third, with key kind `error` and `n` equal to the first 12 digits of the remote state, and still exactly one after the fourth.
18. An `ask` event that fails every time behaves the same way: outcomes `error`, `error`, `reported`, `capped`, three calls, one post of kind `error` after the third dispatch and still one after the fourth.
19. After the report, a new `TickStatus` (a restart) lets the same failing comment event be tried three times again, and the pull request still has exactly one factory post of kind `error`.
20. make check stays green.
21. docs: `docs/operator-guide.md` states which comment answers which wait (a comment written after the question was posted; an earlier one is only recorded) and what each answer resets (`attempts` for the attempts cap, `crashes` for the crash cap, nothing else), that a comment at an approval is only recorded, and that a failing comment event is tried three times and then reported once on the pull request; `docs/decisions.md` records why every event, comment events included, goes through the error cap.

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
document = WorkItemDocument(state=WorkItemState(stage='doing', blocked='question'), body='# T\n')
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
2. intake: 1. The last rule of `## Interface` says F0006-S0002's `question_posted` compares the post's `n` with the number of the latest `question` record, not of the last record, so that comments recorded after a question do not make the watcher raise `ask` again. No criterion tests this behaviour. Two coders could read it two ways and both would pass the tests. Options: (a) add a criterion before the two closing ones, e.g. "a work item whose question is posted and followed by a recorded comment entry is not raised as `ask` again by the watcher's evaluation", with the failing side too ("a work item whose latest question record has no post with its number is still raised"); (b) drop the rule from this story if F0006-S0002 already tests it, and say so in the Interface. I would choose (a).
   2. The post lookup in `adjust` compares the key's `n` with the latest `question` record. The failing side is untested: a post keyed to an earlier question number, with a later question record that is not posted yet, must not end the wait. Criterion 14 covers only "no post at all". Options: add this as a case of criterion 14, or a new criterion. I would choose a new case in criterion 14.
3. human (pull request comment, 2026-10-14): 1 (b): F0006-S0002 already tests this rule on both sides in `tests/domain/test_evaluation.py`: `test_a_post_keyed_to_the_latest_question_is_the_posted_question` (parametrized `question-last` and `comment-after-question`) and `test_question_posted_is_false_without_a_post_for_the_latest_question`. Say in the Interface that the rule is built and tested by F0006-S0002 and that this story only relies on it; no new criterion for it.
   2: add it as a new case of criterion 14, as you proposed: a post keyed to an earlier question number, with a later `question` record not posted yet, does not end the wait.
4. intake: accepted. Carried in the human's answer (log entry 3), nothing else changed: (1b) the last rule of `## Interface` now says the `question_posted` rule is built and tested by F0006-S0002 (`tests/domain/test_evaluation.py`) and that this story only relies on it, with no new criterion; (2) criterion 14 gets a third case: a post keyed to an earlier question number while a later `question` record is not posted yet does not end the wait (now "three cases, one test"). The Assignment's meaning is unchanged.
   - Interface: `unblock` and `CommentHandler` are named with modules and signatures; the rules for `adjust` (post key, id comparison, blank body) are concrete and read from data.
   - Criteria: each is testable by one test function. Every rule has its failing side: not blocked (9, 10), no new comment (7), marker-only comments (8), older comment (13), no post, no question record and an earlier-keyed post (14), blank body (16), failing `list_comments` (11), no pull request (12), and the cap on both sides, through `error`, `error`, `reported`, `capped` and the restart (17-19).
   - Demo: both blocks are runnable, and each `Expect:` line names exact output to compare.
   - Architecture: the pure rule is in `factory.domain`, the handler in `factory.application.handlers`, and it uses `HostingService` only through its interface. Nothing is wired here.
   - Scope: within F0007's "Answers and comment events" scope. The crash-cap question and the rerun stay with F0008.
5. tester: wrote red tests for criteria 1-19, one test function per criterion.
   - criterion 1: tests/domain/test_answers.py::test_unblock_clears_the_wait_and_changes_nothing_else (parametrized: question, round_cap, send_back)
   - criterion 2: tests/domain/test_answers.py::test_unblock_at_the_attempts_cap_resets_the_attempts_only
   - criterion 3: tests/domain/test_answers.py::test_unblock_at_the_crash_cap_resets_the_crashes_only
   - criterion 4: tests/domain/test_answers.py::test_unblock_of_a_state_that_waits_for_nothing_returns_an_equal_state
   - criterion 5: tests/application/handlers/test_comment_handler.py::test_an_answer_after_the_posted_question_is_recorded_and_ends_the_wait_in_one_commit
   - criterion 6: …::test_an_answer_at_the_attempts_cap_also_resets_the_attempts
   - criterion 7: …::test_without_a_new_human_comment_the_work_item_stays_blocked_and_nothing_is_pushed
   - criterion 8: …::test_comments_that_carry_the_factory_marker_do_not_answer_and_push_nothing
   - criterion 9: …::test_a_comment_at_an_approval_is_recorded_and_changes_nothing_else
   - criterion 10: …::test_a_comment_on_a_work_item_that_waits_for_nothing_changes_no_other_field
   - criterion 11: …::test_a_failing_comment_listing_raises_and_pushes_nothing
   - criterion 12: …::test_a_work_item_without_a_pull_request_cannot_be_handled_and_records_nothing
   - criterion 13: …::test_a_comment_older_than_the_post_is_recorded_and_only_a_later_one_answers
   - criterion 14: …::test_a_comment_on_a_wait_whose_question_is_not_posted_does_not_answer (parametrized: question-not-posted, no-question-record, earlier-question-posted)
   - criterion 15: …::test_a_comment_before_and_one_after_the_post_are_both_recorded_and_end_the_wait
   - criterion 16: …::test_a_blank_comment_after_the_post_is_read_without_an_entry_and_does_not_answer
   - criterion 17: …::test_a_comment_event_that_always_fails_is_tried_three_times_and_reported_once
   - criterion 18: …::test_an_ask_event_that_always_fails_is_tried_three_times_and_reported_once (the failure is an AskHandler work item at the attempts cap with no stall entry)
   - criterion 19: …::test_after_a_restart_the_failing_comment_event_is_tried_again_and_not_reported_twice

   Files created: tests/domain/test_answers.py and tests/application/handlers/test_comment_handler.py. The question post is made with `hosting.post_comment` and the Interface's key (`PostKey(work_item, kind=blocked, n=<latest question record number>)`). The dispatcher tests use a small `Counting` subclass of `Handler` that passes each event to the real handler. Criteria 20 and 21 are the closing ones and get no tests.

   `make test`: both modules fail at collection for the expected reasons. `factory.domain.answers` does not exist, and `CommentHandler` cannot be imported from `factory.application.handlers.comments`. `make lint` is green. The type check was skipped as this stage says to.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
