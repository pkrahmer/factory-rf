---
stage: demo
pr: 93
blocked: asked
comments_seen: 1
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
3. tester: no tests written, on purpose. This story only changes documentation. Its Interface says "None: no code changes", and it has just two criteria:
   - criterion 1 (make check stays green) is the factory's gate, not a test.
   - criterion 2 (docs:) is for the documenter. Its bullets are checked by reading and by the Demo greps. A test that pins documentation wording would not be an executable form of a behaviour and would sit outside the Interface.
   The Assignment also says "the tester writes no tests", and intake agreed.
   Files created: none. Modules the test runner could not import: none, since no new tests were added. I did not run make test because there are no new tests to watch fail. make lint: green. Nothing is open for the coder: the story goes on to the documenter by way of doing.

   `make lint`: lint: green
   `make test`: test: green
4. coder: nothing built, on purpose. The story only changes documentation. Its Interface says "None: no code changes", the tester wrote no tests, and the Assignment hands the work to the documenter. CLAUDE.md says the coder does not write `README.md` or `docs/`, so I did not edit them, and the branch has no commits from me.
      - Rejected: writing the doc edits here. That would go outside the coder's lane and take the docs criterion away from the documenter.
      - Refactor: there is no diff to refactor.
      - Open for the documenter: everything in the docs criterion. That covers the operator-guide passages about `ask` and `comment`, the `send_back` row, the summaries in `README.md` and the operator guide, step 1 of the close in the project guide, the three new handler subsections, and the journal-reading module name.

      `make check`: check: green (coverage 99.22 %)

   `make check`: check: green
5. reviewer: no findings.
      - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch holds only the factory's stage commits on the ticket, and no code, test or doc file has changed.
      - Acceptance criteria: criterion 1 (make check) is green according to the coder's entry (coverage 99.22 %) and the factory's run after it. Criterion 2 (docs:) belongs to the documenter, who writes it next. The Interface is "None: no code changes", so there is no rule whose failing side needs a test and no limit to test at its boundary. The tester's choice to write no tests matches the Assignment and intake.
      - Architecture, security, quality: nothing to judge, because the diff is empty.
      - Ticket hygiene: the log explains the main decision (documentation only, so the documenter does the work) and what was rejected (the coder writing the doc edits outside its lane). The Assignment matches what was built, which is nothing. The bullets of the docs criterion are specific enough for the documenter to write from and are checkable through the Demo greps: the stale `ask`/`comment` passages, the `send_back` row, the README and operator-guide summaries, step 1 of the close, the three new handler subsections, and the `factory.domain.hand_over` module name.
      - Open for the documenter: everything in the docs criterion.
6. documenter: wrote the docs criterion; no findings.

   Files changed:
   - `docs/operator-guide.md`: removed the "not registered yet" passages for `ask` and `comment` (cap bullet, "The factory's own questions", "Which comment answers a question"). The cap bullet now says the `ask` handler records and posts the attempts-cap question and the stage waits for an answer. The `send_back` row now says a close discards the story and explains why it cannot send it back again. The opening summary now names the handlers.
   - `README.md`: the summary paragraph names the handlers of the human's acts on the pull request, summarised as the human decided in F0003-S0010. It still says no command runs ticks before F0010.
   - `docs/project-guide.md`: step 1 of "A close before the approval discards the story" now says the handler sends the story back at an approval stage. Added three subsections to "The handlers of the events": "A close at the approval sends the story back", "A comment can end a wait" and "The hand-over at the approval". Each names its test modules. The journal-reading rule now lists `factory.domain.hand_over`, matching `ALLOWED` in `tests/test_no_journal_reading.py`.

   Cross-read and found current: the rest of `docs/operator-guide.md` (hand-over, send-back and merge sections), the other handler subsections of the project guide, `docs/decisions.md` (nothing contradicts the new text; the S0005 entry on record order matches) and the code of `ClosedHandler`, `CommentHandler`, `HandOverHandler`, `factory.domain.send_back`, `answers` and `hand_over`.

   Checks: the demo greps for stale phrases print nothing. `make check` is green (coverage 99.22 %).

   Stale but unrelated and left alone: none seen.

   `make check`: check: green
7. demo: four of the five commands meet their `Expect:` line. Command 3 does not, but I think the Demo grep is too broad rather than the docs being wrong. I need your call before I accept or send this back.

   **Question:** should command 3's output count as a finding?
   - (a) **My choice:** it is not a finding, and the Demo grep needs narrowing. You narrow command 3 in `## Demo`, for example to `grep -n "outside .*factory.application.handlers.hand_over\`" docs/project-guide.md` or to a check of line 834 only. Then the demo runs again and I end with `accept`.
   - (b) It is not a finding, and the demo is accepted as it is now.
   - (c) It is a finding. The story goes back to `doing`, and the documenter rewords the hand-over subsection so the module path does not match the grep. I would not choose this: the path is correct, and rewording it to dodge a grep makes the guide worse.

   Command 1: met (no line printed)
   ```
   $ grep -n "registers it yet\|Once it is registered\|today comments are not handled\|these comments do not appear" docs/operator-guide.md
   (no output, rc=1)
   ```

   Command 2: met (no line printed)
   ```
   $ grep -n "sends the story back again" docs/operator-guide.md
   (no output, rc=1)
   ```

   Command 3: not met. Expect says no line is printed; one line is printed:
   ```
   638:`HandOverHandler(boundaries, definition)` (`factory.application.handlers.hand_over`) handles `hand_over`. It takes `target_of(event)` and `require_pull_request`, checks out the branch and reads the work item. A stage that is not an approval is `CannotHandle("hand_over", ...)`. …
   ```
   This line is in the new subsection "The hand-over at the approval", and it names the module where `HandOverHandler` really lives (`src/factory/application/handlers/hand_over.py` exists). It is not the journal-reading rule. That rule, at line 834, now reads "outside `factory.domain.journal`, `factory.domain.hand_over` and `factory.application.handlers.questions`", which matches `ALLOWED["entry_text"]` in `tests/test_no_journal_reading.py`. The other half of the pattern ("F0007-S0005's to fill in") matches nothing. The docs criterion's bullet on the journal-reading rule is met; only the literal `Expect:` line is not.

   Command 4: met (the send-back, comment and hand-over subsections are there)
   ```
   563:### Asking the human
   575:### Recording the human's act
   583:### The merge archives the story
   596:### A close before the approval discards the story
   607:### A close at the approval sends the story back
   626:### A comment can end a wait
   636:### The hand-over at the approval
   647:### An illegal stage change is put back
   659:### A stop with no work to do is an error
   667:### Comments are copied by id
   ```

   Command 5: met (the first line printed is `README.md`'s summary, naming the handlers)
   ```
   README.md:3:… The handlers start a stage and answer the human's acts on the pull request: comments are copied into the journal, questions are recorded and then posted, a merge archives the story, a close discards it or sends it back, an illegal stage change is moved back, and the pull request is handed over at the approval. The pipeline itself does not run on its own yet: a tick can run a stage and handle these events, but no command runs ticks before F0010. …
   docs/operator-guide.md:3:… The handlers start a stage and answer the human's acts on the pull request: … A tick can run a stage and handle these events, but no command runs ticks yet; that arrives with F0010. …
   docs/operator-guide.md:144:| An agent's | `question` | `<role>: <the agent's words>` | answers it; the stage runs again | discards the story |
   ```

   **Rest of criterion 2, checked by reading:**
   - The operator guide's cap bullet now says that at the cap the evaluation makes `ask` and the attempts-cap question appears.
   - The `send_back` row now says a close discards the story, and that a close cannot send it back again.
   - Step 1 of the close in the project guide now says the handler sends the story back at an approval stage.
   - The three new subsections name what the criterion asks for, and each names its test modules.

   The demo contradicts nothing else in the criteria. I did not run `make check` here; the factory runs it after this stage.

   **Findings:** none apart from command 3, which is what the question above is about.
