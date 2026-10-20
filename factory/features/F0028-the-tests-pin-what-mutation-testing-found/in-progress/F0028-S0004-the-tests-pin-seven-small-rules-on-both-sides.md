---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 315
comments_read: []
handed_over: null
claim:
  instance: self
  stage: docs
  started_at: '2026-10-20T01:57:52.420115Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T01:50:30.241730Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T01:50:30.248029Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T01:50:47.406238Z'
  stage: intake
  run: 430878f612d64237b197c6dd864c4240
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T01:51:08.331366Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T01:54:25.524657Z'
  stage: tests
  run: a51c56aa11c348bba549e8d58e1a10ad
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T01:54:45.980303Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T01:56:33.296079Z'
  stage: doing
  run: 3748915cd3034ea7b0781de24f164234
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T01:56:53.572061Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T01:57:31.926040Z'
  stage: review
  run: fbe07127019d444c848523f1cf0e01cf
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T01:57:52.420115Z'
  stage: docs
---

# The tests pin seven small rules on both sides

## Description

The mutation sweep of 2026-10-19 left one or two live mutants each in seven modules of `factory.domain`, each a side of a rule that no test reaches. The tick status marks an error as reported only when both its event key and its remote state match, but no status in a test holds an entry that matches one and not the other. A named wait of one second is a wait and one of zero seconds none, but only minutes and larger values are tested, against the both-sides rule of `CLAUDE.md`. A resume that its time limit ended keeps the first call's session when the second has none, which only the other end reasons test. A pylint message of another symbol before a `duplicate-code` message, and a blank line before a vulture finding, are skipped without dropping what follows, but every input puts them last or nowhere. An agent definition error without a name is only its fault, which `adapters/agent_files.py:55` raises and no test reads. A send-back reads no records from a document without a state, and a comment numbered 1 with no result counts, both untested. The evaluation's merged, closed, hand-over and ask events carry an empty detail, which `entry/watch.py` prints, and no test reads it. Two more rows come from the guards the sweep called dead (decision 4 of `feature.md`): `question_posted` of a work item without a state is `False`, and a claimed work item whose claim status is `none` raises no event of the agent tier. This story pins all of them as criteria. The code already behaves this way, so the coder has nothing to change: only the tester's work, as in F0025-S0003.

## Interface

No module under `src/factory/` changes. The behaviour pinned (`domain`):

- `factory.domain.tick_status.mark_reported(status, event_key, remote_state)`: marks exactly the entries whose `event_key` and `remote_state` both match.
- `factory.domain.provider_limits.named_wait(text)`: a named wait of more than 0 seconds is that wait, one of 0 seconds is `None`.
- `factory.domain.agent_runs.resumed_result(first, second)`: when `second` ended by `time_limit`, the result's session is `second.session` when that is not `None`, else `first.session`; its end reason is `time_limit` and its duration the sum of both calls' durations.
- `factory.domain.duplicates.similar_code_findings(pylint_json)` and `dead_code_findings(vulture_text)`: an element of another symbol, and a blank line, are skipped, and what follows them is still read.
- `factory.domain.errors.AgentDefinitionError(name, fault)`: `str()` is `agent <name>: <fault>` with a name and `<fault>` without one.
- `factory.domain.send_back.reason_given(document)` and `recorded_since_latest_result(document, kind)`: a document without a state has no records; without a `result` record every record of the kind counts, numbered 1 included.
- `factory.domain.evaluation.evaluate(facts, lookup, claim_status)`: the detail of a merged, closed, hand-over or ask event of the human tier is `""` (an ask without a pull request: `no pull request`); a claimed work item whose `claim_status` is `none` falls through to new work. `question_posted(snapshot, comments)` is `False` for a snapshot without a state.

Tests (the tester writes them): `tests/domain/test_tick_status_mark.py`, `tests/domain/test_provider_limits_one_second.py`, `tests/domain/test_resumed_result_time_limit.py`, `tests/domain/test_duplicates_skipped_lines.py`, `tests/domain/test_errors_agent_definition.py`, `tests/domain/test_send_back_records.py` and `tests/domain/test_evaluation_details.py`. The last builds its inputs with `DEFINITION`, `_snapshot`, `_blocked`, `_at_approval`, `_claimed`, `_view`, `_factory_comment`, `_Lookup`, `_ClaimStatus` and `_evaluate` of `tests/domain/test_evaluation.py`, which the tester moves to a shared module, `tests/evaluation_support.py`, under the standing leave of `CLAUDE.md` (*Tests*): `tests/domain/test_evaluation.py` then imports them from there and keeps every test's name and what it checks. No other earlier test changes.

## Acceptance criteria

1. `mark_reported` (rows of one parametrized test, on `TickStatus(errors=[ErrorCount(event_key="run:F0001-S0001", remote_state="a" * 40, count=1), ErrorCount(event_key="run:F0001-S0001", remote_state="b" * 40, count=1), ErrorCount(event_key="ask:F0001-S0002", remote_state="a" * 40, count=1)])`): marking `("run:F0001-S0001", "a" * 40)` gives the `reported` values `[True, False, False]`; marking `("ask:F0001-S0002", "b" * 40)` gives `[False, False, False]`. Every other field of every entry stays as it was.
2. `named_wait` at one second (rows of one parametrized test): `in 1 second` and `Retry-After: 1` give `timedelta(seconds=1)`; `in 0 seconds` and `Retry-After: 0` give `None`.
3. A resume ended by its time limit (rows of one parametrized test; `first` is `AgentRunResult(end_reason="provider_limit", duration=timedelta(seconds=60), session="ses_a", limit_wait=timedelta(seconds=420))`, `second` is `AgentRunResult(end_reason="time_limit", duration=timedelta(seconds=60), session=<session>)`): with `session=None` the result's session is `ses_a`, with `session="ses_b"` it is `ses_b`; in both rows the result's `end_reason` is `time_limit` and its `duration` `timedelta(seconds=120)`.
4. What the duplicates readers skip (rows of one parametrized test):
   - `similar_code_findings` of the JSON array `[{"symbol": "unused-import", "message": "Unused import os"}, {"symbol": "duplicate-code", "message": "Similar lines in 2 files\n==factory.a:[1:5]\n==factory.b:[2:6]\nx = 1\n"}]`, and of the same array without its first element, each give exactly `[DuplicateFinding(key="similar-code factory.a, factory.b: x = 1", where="factory.a:[1:5], factory.b:[2:6]", message="Similar lines in 2 files")]`.
   - `dead_code_findings` of `\nsrc/factory/x.py:3: unused import 'os' (90% confidence)\n`, and of the same text without its first line end, each give exactly `[DuplicateFinding(key="dead-code src/factory/x.py: unused import 'os'", where="src/factory/x.py:3", message="unused import 'os' (90% confidence)")]`.
5. `AgentDefinitionError` (rows of one parametrized test): `AgentDefinitionError("", "no agent files")` has `str()` `no agent files`, `name` `""` and `fault` `no agent files`; `AgentDefinitionError("coder", "no agent files")` has `str()` `agent coder: no agent files`, `name` `coder` and `fault` `no agent files`.
6. The send-back's records (rows of one parametrized test, each a `WorkItemDocument(state=<state>, body="# T\n")`): no state gives `reason_given` `False`. `WorkItemState(stage="approval", journal=[JournalRecord(number=1, speaker="human", kind="comment")])` gives `reason_given` `True`, and `recorded_since_latest_result(document, "close")` `False`. The same journal with `JournalRecord(number=2, speaker="coder", kind="result")` after it gives `reason_given` `False`.
7. The details of the human tier (rows of one parametrized test, each `_evaluate(_snapshot(1, <state>), lookup=_Lookup(view=<view>))`, giving the event's `kind` and exactly its `detail`): `_at_approval()` with `_view("merged")`: `merged`, `""`. `_at_approval()` with `_view("closed")`: `closed`, `""`. `_at_approval(handed_over=None)` with `_view()`: `hand_over`, `""`. `_blocked()` with `_view()` and no comments: `ask`, `""`. `_blocked(pull_request=None)`: `ask`, `no pull request`.
8. A question is posted only for a work item with a state (rows of one parametrized test): `question_posted(_snapshot(1, None), [])` is `False`; `question_posted(_snapshot(1, _blocked()), [_factory_comment(1)])` is `True`.
9. The agent tier by claim status (rows of one parametrized test, each `_evaluate(_snapshot(1, _claimed()), claim_status=_ClaimStatus(<status>))`, giving `kind`, `detail` and the event's work item): `none`: `run`, `""`, `F0001-S0001` (the claim raises nothing; the work item is new work). `own`: `crash`, `""`, `F0001-S0001`. `expired`: `expired`, `""`, `F0001-S0001`. `held`: `idle`, `F0001-S0001 is held by factory-2`, no work item.
10. `make check` stays green.
11. docs: none. These are the rules the project guide already describes, and this story changes no behaviour.

## Smoke test

```bash
uv run -q python - <<'EOF'
from datetime import timedelta

from factory.domain.agent_runs import AgentRunResult, resumed_result
from factory.domain.errors import AgentDefinitionError
from factory.domain.provider_limits import named_wait
from factory.domain.send_back import reason_given
from factory.domain.work_item import WorkItemDocument

print(named_wait("in 1 second"), named_wait("in 0 seconds"))
first = AgentRunResult(
    end_reason="provider_limit",
    duration=timedelta(seconds=60),
    session="ses_a",
    limit_wait=timedelta(seconds=420),
)
print(resumed_result(first, AgentRunResult(end_reason="time_limit", duration=timedelta(seconds=60))).session)
print(AgentDefinitionError("", "no agent files"))
print(reason_given(WorkItemDocument(state=None, body="# T\n")))
EOF
```

Expect: four lines, `0:00:01 None`, `ses_a`, `no agent files` and `False`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: no `src/` change. The seven `factory.domain` functions and classes it names are concrete, with their signatures. Each stated behaviour (matching on both key and state, a wait of 0 s versus more than 0 s, the session fallback with the summed duration, skipped lines that still let later ones be read, the error text with and without a name, the records rules, the evaluation details and the `none` claim) has a criterion. The shared-helper move to `tests/evaluation_support.py` is the standing leave in CLAUDE.md, and it names the helpers.
   - Criteria: each is testable by one parametrized test with the exact inputs and values given. Every rule has both sides: the key matching and the state matching (1), 1 s versus 0 s (2), session None versus set (3), the skipped line with and without it (4), a name versus no name (5), no state, a record, and a record followed by a result (6), the five evaluation rows (7), `question_posted` without and with a state (8), and the four claim statuses (9). 10 and 11 are the closing criteria.
   - Smoke test: the script is runnable with the imports shown, and the `Expect:` line gives four checkable lines (`0:00:01 None`, `ses_a`, `no agent files`, `False`).
   - Architecture: all behaviour lives in `factory.domain`, with tests under `tests/domain/` and one shared module at the `tests/` root. No layer is crossed.
   - Scope: within F0028's Scope entry for S0004, and none of it is in the feature's Out of scope. The two guards of decision 4 are pinned by criteria 8 and 9, as decided there.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 to 9. The story says the code already behaves this way, so the tests pass now and are not red: the one `make test` run ended `test: green (39.0 s)`. `make lint` is green. The code under test already exists, so I also ran `make types`, which is green too.

   Criterion → test:
   - criterion 1: tests/domain/test_tick_status_mark.py::test_only_entries_matching_key_and_state_are_marked_reported
   - criterion 2: tests/domain/test_provider_limits_one_second.py::test_a_named_wait_of_one_second_is_a_wait_and_of_zero_none
   - criterion 3: tests/domain/test_resumed_result_time_limit.py::test_a_resume_ended_by_its_time_limit_keeps_a_session_and_sums_durations
   - criterion 4: tests/domain/test_duplicates_skipped_lines.py::test_a_skipped_element_or_line_leaves_what_follows_it_read
   - criterion 5: tests/domain/test_errors_agent_definition.py::test_an_agent_definition_error_names_its_agent_only_when_it_has_one
   - criterion 6: tests/domain/test_send_back_records.py::test_the_send_back_reads_records_only_from_a_state_and_since_the_latest_result
   - criterion 7: tests/domain/test_evaluation_details.py::test_the_human_tiers_events_carry_their_exact_detail
   - criterion 8: tests/domain/test_evaluation_details.py::test_a_question_is_posted_only_for_a_work_item_with_a_state
   - criterion 9: tests/domain/test_evaluation_details.py::test_the_agent_tier_follows_the_claim_status
   - criteria 10 and 11: no test (`make check` and docs: none).

   Files created: tests/evaluation_support.py and the seven test modules above.

   Earlier test file changed under the standing leave in CLAUDE.md (*Tests*): tests/domain/test_evaluation.py.
   - These helpers moved to tests/evaluation_support.py: `DEFINITION`, `_snapshot`, `_blocked`, `_at_approval`, `_claimed`, `_view`, `_factory_comment`, `_Lookup`, `_ClaimStatus` and `_evaluate`.
   - So did what they depend on: `MAIN`, `BRANCH_COMMIT`, `MERGE_COMMIT`, `PULL_REQUEST`, `OTHER_INSTANCE`, `AT`, `_id`, `_journal` and `_facts`.
   - test_evaluation.py now imports them from there. Its own `_runnable` and `_human_comment` stay in it, and every test keeps its name and what it checks.
   - No other earlier test changed.

   In criterion 6, the row with a result after the comment checks only `reason_given`, because the criterion names nothing else for that row.

   Modules the test run could not import: none. No `src/` change is expected from the coder.

   `lint`: lint: green (0.0 s)
   `test`: test: green (38.5 s)
6. factory: started doing as self.
7. coder: Built nothing: no path under `src/` changed, as the Interface says ("No module under `src/factory/` changes"). The tester's seven test modules and `tests/evaluation_support.py` already pass against the existing code. I ran `make check` once in the foreground and it ended `test: green (40.3 s)` and `check: green`, with total coverage at 99.14 %.
   - Main choice: hand forward with no code change. The alternative I rejected was touching the code that the new tests pin, such as removing guards the mutation sweep called dead. The story pins that behaviour as it is, and decision 4 of the feature keeps those guards.
   - Refactor: there was no diff of mine to refactor.
   - Description: the journal did not change the meaning of the task, so I did not rewrite it.
   - Noticed but did not touch: the tester's note on criterion 6. In the row with a `result` record after the comment, the test checks only `reason_given`, because the criterion names nothing else for that row. That is a question for the review to weigh, not something for me to change.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   I read the work item and `git diff main...HEAD -- . ':!factory'`. The diff has seven new test modules under `tests/domain/`, the new shared module `tests/evaluation_support.py` and a change to `tests/domain/test_evaluation.py`. Nothing under `src/` changes, as the Interface says.
   - Criteria 1 to 9: each has one parametrized test, and its rows are exactly the inputs and values the criterion gives. Each rule is tested on both sides:
     - 1: the key and the state both match, then only one matches; the test also checks that every other field stays as it was.
     - 2: 1 s and 0 s, for both forms.
     - 3: a second session of `None` and one that is set, each with `time_limit` and a duration of 120 s.
     - 4: the other symbol or the blank line is first, then absent.
     - 5: an error with a name and one without.
     - 6: no state, a comment numbered 1, then a result after the comment. The last row checks only `reason_given`, which is all the criterion asks of it.
     - 7: the five details of the human tier.
     - 8: `question_posted` without a state and with one.
     - 9: all four claim statuses.
   - The coder's journal entry (7) says `make check` was green.
   - Architecture and security: only test code changes. No marker silences a check, and the fake commit ids are low-entropy.
   - Quality: I checked the neighbouring test modules (`test_send_back.py`, `test_resumed_result.py`, `test_evaluation_reject.py`). The new modules copy none of their helpers. `_approval` in `test_send_back_records.py` returns a `WorkItemState` built from records, so it is not a copy of `_document` in `test_send_back.py`.
   - Work item hygiene: the Description matches what was built. The journal names the main choice (no code change) and what was rejected. The docs criterion "none" still holds, because no behaviour changes.

   Earlier tests:
   - tests/domain/test_evaluation.py: changed under the standing leave in `CLAUDE.md` (*Tests*) to move a shared test helper. The change moves `MAIN`, `BRANCH_COMMIT`, `MERGE_COMMIT`, `PULL_REQUEST`, `OTHER_INSTANCE`, `AT`, `DEFINITION`, `_id`, `_snapshot`, `_journal`, `_blocked`, `_at_approval`, `_claimed`, `_view`, `_factory_comment`, `_Lookup`, `_ClaimStatus`, `_facts` and `_evaluate` unchanged to `tests/evaluation_support.py` and imports them from there. The diff touches only the module's head, so every test there keeps its name and what it checks.
10. factory: started docs as self.
