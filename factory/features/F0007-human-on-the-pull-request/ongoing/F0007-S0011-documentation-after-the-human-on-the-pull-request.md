---
stage: tests
pr: 93
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Documentation after the human on the pull request

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

The feature acceptance of F0007 read `README.md` and `docs/` from the top. Each story documented its own handler, and those sections match the code and the feature demo. But S0010 registered all of the feature's handlers at the end, and passages that earlier stories wrote while a handler was "built but not registered" were left behind. Five things are now wrong or missing:

- **The operator guide says `ask` and `comment` are not handled.** Three passages say so: the cap bullet of "A stall: the stall note" ("The handler of `ask` is built … but no tick registers it yet, so today the event is a counted error"), the opening paragraph of "The factory's own questions" ("no tick registers it yet, so today these comments do not appear") and the opening paragraph of "Which comment answers a question" ("no tick registers it yet, so today comments are not handled … Once it is registered"). `factory.entry.wiring.build_handlers` registers both, and "An event that keeps failing" in the same guide says so.
- **The send-back row of the questions table is wrong about a close.** Under "The factory's own questions", the row for `send_back` says that closing the pull request "sends the story back again, or discards it". The send-back has already moved the story to the approval's second `next` stage, which is not an approval stage, so `ClosedHandler` discards the story; a close cannot send it back again. Option 2 of the question itself says "discard", which is right.
- **The summaries of what is built stop before F0007.** `README.md` and the opening paragraph of `docs/operator-guide.md` name "the dispatcher with the run handler that starts a stage". Neither names the handlers of the human's acts on the pull request, so a newcomer reads that only the run handler exists.
- **The project guide still describes the discard-only closed handler.** Under "A close before the approval discards the story", step 1 says that at an approval stage the handler "returns and does nothing: the send-back is F0007-S0005's to fill in there". It sends the story back. The section "The handlers of the events" has subsections for the ask, merged, closed (discard), reject and lookup handlers and for the shared recorder and copier. It has none for the send-back (`ClosedHandler._send_back`, `factory.domain.send_back`), for the comment handler's answer rule (`CommentHandler`, `factory.domain.answers.unblock`) or for the hand-over (`HandOverHandler`, `factory.domain.hand_over`). The operator guide describes all three for the operator; an agent changing the code finds no section in its own guide.
- **The project guide names the wrong module in the journal-reading rule.** Its list of the modules that may reference `entry_text` names `factory.application.handlers.hand_over`. `tests/test_no_journal_reading.py` allows `factory.domain.hand_over` instead, by the human's answer in F0007-S0009. An agent following the guide would put the reading where the test refuses it.

This story is documentation only: the tester writes no tests and the coder has nothing to build; the documenter writes it from the docs criterion. The human may prefer to make the edit by hand.

## Interface

None: no code changes. Files: `README.md`, `docs/operator-guide.md`, `docs/project-guide.md`. `docs/decisions.md` is read for consistency and changed only where it contradicts the new text.

## Acceptance criteria

1. make check stays green.
2. docs: this story is the documentation. `README.md`, `docs/operator-guide.md` and `docs/project-guide.md` change; `docs/decisions.md` changes only where it contradicts the new text. Afterwards:
   - No passage of `docs/operator-guide.md` says that the handler of `ask` or of `comment` is not registered, or that comments or questions are not handled today. The cap bullet of "A stall: the stall note" says what happens at the cap: the `ask` handler records and posts the attempts-cap question, and the stage does not run again until the human answers. "Which comment answers a question" describes the rule as it works now, without "once it is registered".
   - In the questions table of "The factory's own questions", the `send_back` row says that closing the pull request discards the story (back to the backlog as the human wrote it, its branch and bill deleted). It no longer says that a close sends the story back again.
   - The summary of what is built, in `README.md` and in the opening paragraph of `docs/operator-guide.md`, also names the handlers of the human's acts on the pull request: comments copied into the journal, questions recorded and then posted, a merge archiving the story, a close discarding it or sending it back, an illegal stage change moved back, and the hand-over at the approval. It summarises rather than lists, as the human decided on 2026-10-14 (F0003-S0010). It still says that no command runs ticks before F0010.
   - Under "A close before the approval discards the story" in `docs/project-guide.md`, step 1 says that at an approval stage the handler sends the story back instead (see the new subsection), and no longer says that it returns and does nothing.
   - "The handlers of the events" in `docs/project-guide.md` has a subsection for each of: the send-back (the order record close → reopen as draft → record decision → labels; `send_back_target`, `send_back_cap`, `reason_given` and `recorded_since_latest_result` of `factory.domain.send_back`; the reason judged from records, never from text), the comment handler (`CommentHandler`: copy, and in the same commit `unblock` when a non-blank comment is newer than the post keyed to the blocked value and the latest `question` record; what `unblock` resets) and the hand-over (`HandOverHandler` and `hand_over_description`: the sections, the reports found by speaker and kind, the effects before the record, the cost table key). Each names its test modules, as the other subsections do.
   - The journal-reading rule in `docs/project-guide.md` lists `factory.domain.hand_over` where it listed `factory.application.handlers.hand_over`, matching `ALLOWED` in `tests/test_no_journal_reading.py`.

## Demo

```bash
grep -n "registers it yet\|Once it is registered\|today comments are not handled\|these comments do not appear" docs/operator-guide.md
```
Expect: no line is printed.

```bash
grep -n "sends the story back again" docs/operator-guide.md
```
Expect: no line is printed.

```bash
grep -n "F0007-S0005's to fill in\|factory.application.handlers.hand_over\`" docs/project-guide.md
```
Expect: no line is printed.

```bash
grep -n "^### " docs/project-guide.md | sed -n '/Asking the human/,/Comments are copied by id/p'
```
Expect: the subsections of "The handlers of the events" include one on the send-back, one on the comment handler's answers and one on the hand-over.

```bash
grep -n -i "comments\|sen[dt].* back\|hand-over\|discard" README.md docs/operator-guide.md | head -3
```
Expect: a line of `README.md` (its summary paragraph) is printed, naming the handlers of the human's acts on the pull request; before this story `README.md` prints none.

## Log (append only)

1. 2026-10-14 human: created.
2. intake: accepted
   - Interface: "None: no code changes", and no Interface comment states a behaviour, so there is nothing to test or pin down. The files named (README.md, docs/operator-guide.md, docs/project-guide.md) exist. The stale passages the Assignment cites are there: operator-guide.md line 138 ("no tick registers it yet, so today these comments do not appear"), and the `ALLOWED` set in tests/test_no_journal_reading.py lists `factory.domain.hand_over`, as the story says.
   - Criteria: only two exist, `make check` and `docs:`. The `docs:` criterion is for the documenter, and its bullets can be checked by reading and by the Demo greps. No rule has a failing side. The tester has no test to write; I judge that fine because the story says so in its Assignment.
   - Demo: all five blocks are runnable and every `Expect:` line is checkable. I ran the sed range of block 4 and it works: the "Asking the human" and "Comments are copied by id" headings exist in docs/project-guide.md. I ran the grep of block 5: today it prints lines from docs/operator-guide.md and none from README.md, which matches the story's "before this story README.md prints none".
   - Architecture: documentation only, so no layer or interface is touched. docs/decisions.md changes only where it contradicts the new text.
   - Scope: the story fits F0007 (it is listed in FEATURE.md as proposed by the feature acceptance). It touches no test, no code and nothing out of scope.
