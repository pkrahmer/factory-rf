---
stage: tests
pr: 171
blocked: null
comments_seen: 0
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
