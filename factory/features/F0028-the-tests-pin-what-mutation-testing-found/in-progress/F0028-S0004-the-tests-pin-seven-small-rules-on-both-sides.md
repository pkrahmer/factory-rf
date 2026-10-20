---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-20T01:50:30.248029Z'
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
