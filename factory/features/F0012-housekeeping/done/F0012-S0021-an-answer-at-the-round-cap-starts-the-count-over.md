---
stage: done
pr: 171
blocked: null
comments_seen: 2
round: 0
attempts: 0
---
# An answer at the round cap starts the count of rounds over

## Assignment (as of log entry 1)

When a rework would send a work item back more often than its stage's `round_cap`, the stage stays, blocked `round_cap`, and the factory asks the human. Today an answer ends the wait but keeps `round`, so the rerun's first send-back passes the cap again and asks again: the human cannot grant one more round. v1 had the same trap, and the human's answer "one more round" on F0011-S0001 could not work. The human's word (item 1.5) is that the answer at the cap can grant more rounds. This story makes an answer to a `round_cap` wait set `round` to 0, as an answer to the attempts cap resets `attempts` and one to the crash cap resets `crashes` (FEATURE decision 26): the human who answers grants the cap's rounds again; the human who wants it to stop closes the pull request. The question says so. Two tests of earlier stories change by the human's leave (FEATURE decision 40).

## Interface

`src/factory/domain/answers.py`, `unblock(state)`: for `blocked == "round_cap"` it returns the state with `blocked=None` and `round=0`, and nothing else changed. The other cases do not change: `question` and `send_back` end the wait and keep `round`; `attempts_cap` resets `attempts`; `crash_cap` resets `crashes`; a state that waits for nothing is returned unchanged. The docstring's sentence on `round` changes accordingly.

`src/factory/domain/post_texts.py`, `round_cap_question(rounds, cap)` returns:

```text
This work item has now been sent back <rounds> times, more than <cap>. What should happen? Answer with a comment, which starts the count of rounds over; close the pull request to discard the work item.
```

Tests: `tests/domain/test_answers_round_cap.py` (criterion 1) and `tests/test_round_cap_answer.py` (criterion 3), with the `world` and `work_item` fixtures of `tests/conftest.py` and `drive_to`, `completed`, `run_ticks`, `head_state`, `posts` and `pull_request_of` of `tests/proof_support.py`: the story is driven to `review` and sent back four times, as `tests/test_fault_paths_7_to_13.py::test_round_cap_question_killed_between_post_and_record_posts_once_and_waits` drives it (without its kill), then the human comments through `world.hosting.add_human_comment`, one tick runs, and one more reviewer run decides `doing`. By the human's leave (FEATURE decision 40), and no other change to an earlier story's test: the `round_cap` row moves out of `test_unblock_clears_the_wait_and_changes_nothing_else` in `tests/domain/test_answers.py` (its `question` and `send_back` rows stay), and the expected text of `test_the_round_cap_question_names_the_rounds_and_the_cap` in `tests/domain/test_question_texts.py` becomes the text of the Interface for 4 and 3.

## Acceptance criteria

1. `unblock` of a state blocked `round_cap` with `round=4`, `attempts=2` and `crashes=2` returns that state with `blocked=None` and `round=0`, `attempts` and `crashes` still 2; a state blocked `question` or `send_back` with `round=4` keeps `round=4`. Rows of one parametrized test.
2. `round_cap_question(4, 3)` is the text of the Interface with 4 and 3.
3. A work item blocked `round_cap` at `review` with `round == 4` and one `round_cap` post, answered by a human comment on its pull request, is unblocked with `round == 0` on its branch after one tick; the next reviewer run that decides `doing` moves it to `doing` with `round == 1`, and the pull request still holds exactly one `round_cap` post.
4. The unchanged answers still hold: `attempts_cap` resets the attempts only, `crash_cap` the crashes only (the existing tests of `tests/domain/test_answers.py`).
5. `make check` stays green.
6. docs: the operator guide's section *The factory's own questions* (where it explains the round cap question and what an answer does) says that an answer starts the count of rounds over, which also counts the approval's send-backs, that a close discards the work item, and that an answer to the approval's send-back question keeps the count, so the next send-back past the cap asks the round cap question once more; the project guide's description of `unblock` says the same; the decision log records why the count starts over instead of granting exactly one round (the code does not read the answer's words, so an answer can only reset or keep the count, and keeping it made "one more round" impossible). No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from factory.domain.answers import unblock
from factory.domain.journal import HUMAN, JournalRecord
from factory.domain.post_texts import round_cap_question
from factory.domain.work_item import WorkItemState
state = WorkItemState(stage='review', blocked='round_cap', round=4, journal=[JournalRecord(number=1, speaker=HUMAN, kind='created')])
after = unblock(state)
print(after.blocked, after.round)
print(round_cap_question(4, 3))
"
```
Expect: two lines: `None 0` and `This work item has now been sent back 4 times, more than 3. What should happen? Answer with a comment, which starts the count of rounds over; close the pull request to discard the work item.`

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names `src/factory/domain/answers.py` `unblock(state)` and `src/factory/domain/post_texts.py` `round_cap_question(rounds, cap)`, with the exact new text and the unchanged cases listed (question, send_back, attempts_cap, crash_cap, no wait). Also names the test files and the fixtures and helpers they use.
   - Criteria: each is testable by one test function. 1 is a parametrized table covering round_cap (reset to 0, attempts and crashes kept) and the question and send_back rows (round kept). 2 pins the text. 3 is the end-to-end test: unblocked at round 0, then the next `doing` decision gives round 1, and the pull request holds one round_cap post. 4 points at the existing tests for the unchanged caps. Every rule in the Interface has a criterion for each side.
   - Demo: one runnable `uv run python -c` command. Its `Expect:` line gives both exact output lines, so it can be checked.
   - Architecture: both changes are in `factory.domain`, pure and with no I/O. The tests go in the mirrored `tests/domain/` and at the `tests/` root. No new dependency or module.
   - Scope: this is item 1.5 of FEATURE.md, as decisions 26 and 47 confirm. The two existing tests it changes have the human's leave (decision 40) and are named in the Interface.
3. tester: red on purpose; this is the coder's specification.
   - criterion 1: tests/domain/test_answers_round_cap.py::test_unblock_resets_the_round_only_at_the_round_cap. Rows: round_cap (round 4 → 0), question and send_back (round 4 kept). Every row also checks that attempts and crashes stay 2 and nothing else changes.
   - criterion 2: tests/domain/test_question_texts.py::test_the_round_cap_question_names_the_rounds_and_the_cap. Its expected text is now the Interface's text for 4 and 3, as the Interface allows (FEATURE decision 40).
   - criterion 3: tests/test_round_cap_answer.py::test_an_answer_at_the_round_cap_starts_the_count_of_rounds_over. It drives the story to review and sends it back 4 times, the way the fault-path test does but without the kill, and checks blocked round_cap at review with round 4 and one round_cap post. Then a human comment through world.hosting.add_human_comment and one tick: unblocked with round 0. Then one reviewer run that decides doing and one more tick: stage doing with round 1, and still exactly one round_cap post.
   - criterion 4: the existing tests in tests/domain/test_answers.py (test_unblock_at_the_attempts_cap_resets_the_attempts_only, test_unblock_at_the_crash_cap_resets_the_crashes_only, test_unblock_of_a_state_that_waits_for_nothing_returns_an_equal_state) are unchanged. In test_unblock_clears_the_wait_and_changes_nothing_else I removed only the round_cap row; the question and send_back rows stay (decision 40).
   - Created: tests/domain/test_answers_round_cap.py, tests/test_round_cap_answer.py. Changed (with the human's leave): tests/domain/test_answers.py, tests/domain/test_question_texts.py.
   - Every module imports, so there are no collection errors. `make test` has 3 failures, the three tests above (the round_cap row, the question text, the end-to-end test), because the current code keeps round and the old question text. I did not rerun to check exactly which assertion the end-to-end test fails on. `make lint` is green.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/test_round_cap_answer.py::test_an_answer_at_the_round_cap_starts_the_count_of_rounds_over
4. coder: question. The implementation is done and committed (ee88826), but `tests/test_round_cap_answer.py::test_an_answer_at_the_round_cap_starts_the_count_of_rounds_over` cannot pass against the factory as it is built. All other tests are green.

   - Built: `src/factory/domain/answers.py` `unblock` now sets `round=0` for a `round_cap` wait, and its docstring sentence on `round` is updated. `src/factory/domain/post_texts.py` `round_cap_question` returns the Interface's text. Criteria 1, 2 and 4 pass.
   - The contradiction: the tick that decides the fourth send-back records the question in the journal and blocks the item `round_cap`. The ask handler posts that question on the next tick (record first, post once; see `src/factory/application/handlers/questions.py`). The fault-path test it copies allows for this by running more ticks after the blocking tick. The new test reads `posts(world, work_item, "round_cap")` and adds the human comment right after the blocking tick, so it sees no post: it fails at `assert len(caps_asked) == 1` (0 == 1). Even past that assert, the comment would come before the post, and `_ending_the_wait` (`src/factory/application/handlers/comments.py`) rightly ignores a comment written before the question was posted.
   - Checked: in a scratch copy (deleted, never committed) I added one `world.tick.run()` between the fourth `completed("doing", "Finding.")` tick and `capped = head_state(...)`. With that one line the test passes against this implementation.
   - Options: (a) the tester adds that one `world.tick.run()` after the fourth send-back tick, before `capped` and `caps_asked` are read. (b) Change the stage so it posts the round cap question in the same tick as the block. That reverses the record-then-post design that the fault paths depend on, and it is beyond this story's scope. I would choose (a). If you answer (a), I will end with `tests` and name that change.
   - Refactor step: not reached. The diff is 5 lines and needs none.
5. human (pull request comment, 2026-10-17): (a). The tester adds one `world.tick.run()` after the fourth send-back tick, before `capped` and `caps_asked` are read, as the fault-path test does; the record-then-post design stays.
6. coder: tests. The human chose (a) in entry 5, so the test needs one change: in `tests/test_round_cap_answer.py::test_an_answer_at_the_round_cap_starts_the_count_of_rounds_over`, add one `world.tick.run()` after the fourth send-back tick (line 24, after `world.agent_runtime.queue(completed("doing", "Finding."))` and its `world.tick.run()`) and before `capped` and `caps_asked` are read (line 25). That extra tick posts the round cap question that the blocking tick recorded.
      - The implementation is already committed (ee88826): `src/factory/domain/answers.py` `unblock` sets `round=0` for a `round_cap` wait, and `src/factory/domain/post_texts.py` `round_cap_question` returns the Interface's text. When I tried this change in a scratch copy in entry 4, the test passed against this implementation. No code changed in this run.
      - Once the tester has made the change, the ticket comes back here for the refactor step and `review`. The diff is 5 lines and probably needs no refactor.
7. tester: approved test change made, as the human chose (a) in entry 5 and the coder named in entry 6.
      - Changed: `tests/test_round_cap_answer.py::test_an_answer_at_the_round_cap_starts_the_count_of_rounds_over`. Added one `world.tick.run()` after the fourth send-back tick and before `capped` and `caps_asked` are read. The blocking tick only records the round cap question; this extra tick posts it, the way the fault-path test does. That way the question is posted before the human comment, and `len(caps_asked) == 1` holds. Nothing else in the test changed, and no other file changed.
      - `make test`: green against the coder's commit ee88826 (test: green (28.2 s), coverage 99.51 %).

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (27.6 s)
8. coder: review. All tests pass now that the tester has made the change from entry 7. `make check` passes (check: green, coverage 99.51 %).
      - Built (commit ee88826):
        - `src/factory/domain/answers.py` `unblock`: it sets `round=0` for a `round_cap` wait, the same way `attempts_cap` resets `attempts` and `crash_cap` resets `crashes`. The other waits keep `round`. The docstring sentence on `round` now says this.
        - `src/factory/domain/post_texts.py` `round_cap_question`: it returns the Interface's text ("Answer with a comment, which starts the count of rounds over; …").
      - Main decision: the reset is one more line in the existing branch-per-cap update dict inside `unblock`. I rejected a separate table that maps each cap to its counter: with three entries, that adds indirection and changes nothing.
      - Rejected earlier (entries 4 and 5): posting the round cap question in the same tick as the block. The human kept the record-then-post design.
      - Refactor step: I read the diff `git diff main...HEAD -- src` (5 lines). Nothing needs changing, so there is no refactor commit.
      - Open: criterion 6 (the operator guide, the project guide and the decision log) is for the documenter stage. I changed no documents.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
9. reviewer: no findings.
      - Acceptance criteria: criterion 1 is `tests/domain/test_answers_round_cap.py::test_unblock_resets_the_round_only_at_the_round_cap`. It has three rows: round_cap goes to round 0, question and send_back keep round 4, and every row also checks that attempts and crashes stay 2 and that nothing else changes. Criterion 2 is `tests/domain/test_question_texts.py::test_the_round_cap_question_names_the_rounds_and_the_cap`, which checks the Interface's text exactly. Criterion 3 is `tests/test_round_cap_answer.py::test_an_answer_at_the_round_cap_starts_the_count_of_rounds_over`. It checks blocked round_cap at review with round 4 and one post, then round 0 after the comment and one tick, then doing with round 1, and still exactly one round_cap post at the end. The extra tick before the post is read is the change the human approved in entry 5. Criterion 4 is covered by the existing attempts_cap, crash_cap and no-wait tests in `tests/domain/test_answers.py`, which are unchanged. Only the round_cap row left `test_unblock_clears_the_wait_and_changes_nothing_else`, which FEATURE decision 40 allows. Both sides of the Interface's rule are tested: round_cap resets the count, while question and send_back keep it. The coder's entry 8 reports `make check` green.
      - Architecture: both changes are in `factory.domain`. They are pure, with no new imports or I/O.
      - Security: no new markers, secrets or process calls.
      - Quality: `src/factory/domain/answers.py:19-20` follows the existing branch-per-cap pattern. The docstring sentence on `round` is updated to match, and the module docstring ("its own counter starts over") now fits every cap. No other place in `src/factory` still says that an answer keeps `round`. `make duplicates` reports 0 new findings.
      - Ticket hygiene: the log gives the main decision, the per-cap branch rather than a lookup table, and the rejected option of posting in the same tick as the block. Assignment and Interface match the code. Criterion 6 still describes what the documenter has to write.
10. documenter: wrote criterion 6. I ran no `make check`, because I changed only documents. `python -m factory.entry.check_documents` prints `documents ok`.
    - `docs/operator-guide.md`, "The factory's own questions":
      - The table row for the round cap now says an answer starts the count over.
      - The bullet on what an answer resets now says `round` goes back to 0 for the round cap. It says the count also holds the approval's send-backs. It says an answer to the approval's send-back question keeps `round`, so the next send-back past the cap asks again.
      - The round cap question text is the new one. The paragraph says an answer resets `round` and a close discards the work item.
    - `docs/project-guide.md`: the description of `unblock` (line 693) says the same.
    - `docs/decisions.md`: new entry "An answer at the round cap starts the count of rounds over". It records why the count starts over instead of granting exactly one round: the code does not read the answer's words, so an answer can only reset or keep the count, and keeping it made "one more round" impossible.
    - Cross-read against the diff and found current: the rest of the operator guide and project guide, including the "The reason and the round cap" section and the post-text paragraph (it names the function, not the text). I did not read README.md.
    - Stale but not touched: nothing seen.
    - Findings: none. The code matches the Interface.

    `make check`: check: green
    `make documents`: documents ok
11. demo: accepted, with no findings. I ran the one command under `## Demo` from the repository root, exactly as written.

    Command 1 (`uv run python -c "…unblock…round_cap_question(4, 3)"`):
    ```
    None 0
    This work item has now been sent back 4 times, more than 3. What should happen? Answer with a comment, which starts the count of rounds over; close the pull request to discard the work item.
    ```
    It met its `Expect:` line. Both lines match word for word.

    - I checked the output against the acceptance criteria:
      - Criterion 1: `unblock` of a state blocked `round_cap` with round 4 returns `blocked=None` and `round=0`.
      - Criterion 2: the question text is exactly the Interface's text for 4 and 3.
      - The demo does not cover criterion 3 (the end-to-end tick), criterion 4 (the other caps), criterion 5 (`make check`) or criterion 6 (docs). The output contradicts none of them.
    - Not run in this stage: `make check`. The factory runs it after this stage.
12. done (pull request merged); cost: 9 runs, 5.8 min, 57 turns, 182k tokens in (760k more from cache), 15k out, $1.16
