---
stage: tests
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 254
comments_read: [6261999766, 6262128853]
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-19T07:49:32.734323Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T07:25:18.086867Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T07:25:18.091627Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-19T07:25:41.567350Z'
  stage: intake
  run: 99589987c2734d4eb32f91bec4df5b0d
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-19T07:26:58.091006Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-19T07:27:16.139978Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-19T07:27:36.153542Z'
  stage: intake
  run: 5630e5c1e65b4046a2b3999a48486767
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-19T07:27:56.618032Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-10-19T07:34:10.256555Z'
  stage: tests
  run: 03db98305dc646e580ed9154d53918e8
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-10-19T07:35:28.019041Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T07:35:46.155444Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-10-19T07:38:44.180897Z'
  stage: tests
  run: c1602f4e806d46c2b262a998d9b08212
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T07:39:04.600998Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-10-19T07:46:51.207230Z'
  stage: doing
  run: 07ccd54c62c048ae8237285abeb1b5a9
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-19T07:47:11.513638Z'
  stage: review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-10-19T07:48:32.654219Z'
  stage: review
  run: fc2f2989da7e46d091c901ea2c527e00
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-19T07:48:53.131740Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-10-19T07:49:12.315731Z'
  stage: doing
  run: 45b46b45a9d34f1e95fcd3673ede0ce5
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-19T07:49:32.734323Z'
  stage: tests
---

# A provider's spend limit ends a run with its session kept, and a run can resume a session

## Description

At the human's work, the API gateway limits the spend per model in a rolling window (about $3 per 10 minutes); past it, a call returns HTTP 428 with a message saying so. Today such a call ends the Claude Code run `died`, which counts as a stall and an attempt, and nothing could continue it. This story gives the limit its own end reason, `provider_limit`, recognized by a pattern the operator can set (status 428 by default, plus an optional message pattern, because the gateway's exact text is not known here), and keeps the run's session on every result, so that the application layer can wait and continue the same session (S0007). It also lets a request name a session to resume: the Claude Code runtime then calls `--resume <session>` with the request's prompt and budget, the opencode runtime `--session <session>`. A message that names a wait ("try again in 7 minutes") gives the run's `limit_wait`. The Claude Code runtime recognizes the limit in its error result after the call has ended; the opencode runtime recognizes it while the run streams, in S0006. The stall reason `provider_limit` and its sentence come here too, because a run ended by the limit is a stall until S0007 waits it out.

## Interface

`factory.domain.agent_runs` (`domain`):

```python
EndReason = Literal["completed", "no_result", "time_limit", "budget", "died", "provider_limit"]

class AgentRunRequest(BaseModel):
    ...
    resume_session: str | None = None   # new, last

class AgentRunResult(BaseModel):
    ...
    session: str | None = None          # new, after login
    limit_wait: timedelta | None = None # new, last
```

- `resume_session`, when set, is not blank (else a validation error); it names a session the same runtime made.
- `session` is the runtime's own id of the session the run used, set by both runtimes whatever the end reason; `None` when the runtime never learned one.
- `limit_wait` is set only when the end reason is `provider_limit` (`a run that ended by <reason> has no limit_wait` otherwise) and is positive.
- `resumed_result` (S0002) takes `second`'s `session`, or `first`'s when `second` has none, and `second`'s `limit_wait`.

`factory.domain.provider_limits` (`domain`, new):

```python
DEFAULT_LIMIT_STATUS = 428

class ProviderLimit(BaseModel):
    status: int = DEFAULT_LIMIT_STATUS    # 100 to 599
    message: str | None = None            # a regular expression

def limit_in_text(text: str, limit: ProviderLimit) -> bool: ...
def named_wait(text: str) -> timedelta | None: ...
```

- `ProviderLimit` refuses a status below 100 or above 599 and a `message` that does not compile as a regular expression.
- `limit_in_text`: true when the status stands in the text as a whole number (not inside a longer number: `428` in `HTTP 428:` and `(428)`, not in `14280`), or when `message` is set and searches the text (`re.search`, as written); false for an empty text.
- `named_wait`: the first wait the text names, by the earliest match of either form, case-insensitive: `in <n> <unit>` or `after <n> <unit>`, the unit `s`, `sec`, `second(s)`, `m`, `min`, `minute(s)`, `h`, `hour(s)`, or none (seconds); and `retry-after` with an optional colon and `<n>` seconds. `<n>` has one to six digits. A wait of zero, or none named, is `None`.

`factory.domain.settings` (`domain`):

```python
PROVIDER_LIMIT_STATUS_VARIABLE = "FACTORY_PROVIDER_LIMIT_STATUS"
PROVIDER_LIMIT_MESSAGE_VARIABLE = "FACTORY_PROVIDER_LIMIT_MESSAGE"

class InstanceSettings(BaseModel):
    ...
    provider_limit: ProviderLimit = ProviderLimit()   # new, last
```

- `read_settings`: an unset or blank status variable gives 428; a value of ASCII digits from 100 to 599 gives that status; any other raises `SettingsInvalid` naming the variable with `is not an HTTP status from 100 to 599`. An unset or blank message variable gives `None`; a value that is not a regular expression raises `SettingsInvalid` naming the variable with `is not a regular expression: <error>`.

`factory.domain.journal`, `factory.domain.post_texts` (`domain`):

- `StallReason` (in `factory.domain.journal`, where F0021-S0001 moved it; `factory.domain.decisions` keeps the name by assignment and changes in no line) gains `provider_limit`, so a `JournalRecord` of kind `stall` may carry it as its `reason`; `stall_reason_of` and `decisions` do not change. Its sentence in `post_texts` is `the provider's spend limit lasted past the waiting ceiling` (a stall note is built from it as for every reason).

`factory.adapters.claude_runtime` (`adapters`):

- `ClaudeCodeRuntime.__init__` gains the keyword `provider_limit: ProviderLimit | None = None` (`None` is `ProviderLimit()`); the reply model `_Reply` gains `result: str | None = None`.
- A call ends `provider_limit` when it did not reach its time limit, was not stopped by its budget, and either its reply is an error (`is_error`) whose `result` the limit is in (`limit_in_text`), or no reply parses and a line of its standard error holds the limit. Such a result keeps the reply's measures, as a `died` one does, and its `limit_wait` is `named_wait` of that `result` or line.
- Every result's `session` is the session the run used: the new id of `--session-id`, or the request's `resume_session`.
- A request with `resume_session` is called with `--resume <resume_session>` in place of `--session-id <new id>`, with the request's prompt and the agent's budget; the run's files are still named by a fresh id. A budget stop of such a call resumes the same session once, as today.
- A budget-stop resume that ends `provider_limit` makes the run's result `provider_limit`, with both calls' measures (`resumed_result`).

`factory.adapters.opencode_runtime` (`adapters`):

- A request with `resume_session` is called with `--session <resume_session>` right before the prompt.
- Every result's `session` is the `sessionID` of the first event that carries one, else the request's `resume_session`, else `None`.

`factory.application.costs` (`application`):

- `CostRecorder.complete` treats a `provider_limit` result as a run that replied: its record gets `denials` and `denied_paths` from the result's refused calls, like a `completed`, `no_result` or `budget` one, and not `None` (only `died` and `time_limit` leave them unknown). `end_reason` `provider_limit` is copied as it is.

`factory.domain.contract` (`domain`), `src/factory/contract/*.schema.json`:

- The end reason `provider_limit` is an added value of `cost-record`'s `end_reason`, and the stall reason an added value of the `reason` of the journal records in `work-item-state` and `acceptance-state`, so the records contract's minor version rises: `RECORDS_CONTRACT` goes from `"1.1"` (S0001) to `"1.2"`, and the committed schemas are regenerated in this story with `uv run python -m factory.entry.contract` (never by hand): `cost-record.schema.json`, `work-item-state.schema.json` and `acceptance-state.schema.json` list `provider_limit` among those values, and every file carries `"x-records-contract": "1.2"`. `limit_wait` is a field of `AgentRunResult`, which no schema describes, so no schema gains it.

`factory.entry.wiring` (`entry`):

- `build_boundaries` passes `settings.provider_limit` to `ClaudeCodeRuntime`.

Tests (the tester writes them): `tests/domain/test_provider_limits.py`, `tests/domain/test_agent_runs_session.py`, `tests/domain/test_settings_provider_limit.py`, `tests/domain/test_provider_limit_stall_text.py`, `tests/adapters/test_claude_runtime_provider_limit.py` and `tests/adapters/test_claude_runtime_resume_session.py` (with `tests/adapters/claude_stand_in.py`; `_request` of `tests/adapters/test_claude_runtime_os_user.py` imported, not copied), `tests/adapters/test_opencode_resume_session.py` (with `tests/adapters/opencode_stand_in.py` of S0004), `tests/entry/test_wiring_provider_limit.py`, `tests/application/test_costs_provider_limit.py`.

Changed under the feature's decision 19, by the tester only, nothing else in those modules: `tests/domain/test_agent_runs.py`, the test `test_question_and_the_five_end_reasons`, renamed `test_question_and_the_six_end_reasons`, whose expected count is 6 and whose expected set gains `provider_limit`; `tests/domain/test_contract.py`, the test `test_a_schema_starts_with_the_dialect_and_the_contract_version`, whose expected version is `"1.2"` (the test keeps its name).

## Acceptance criteria

1. `EndReason` holds the six reasons; a `provider_limit` result with `limit_wait` of 420 seconds is valid; a `died` result with a `limit_wait` is refused with `a run that ended by died has no limit_wait`, and a `limit_wait` of zero is refused (rows).
2. An `AgentRunRequest` with `resume_session` `"ses_a"` is valid; with `""` or `"  "` it is refused (rows).
3. `resumed_result` gives the second call's `session` and `limit_wait`, and the first call's `session` when the second has none (rows).
4. `limit_in_text` with the default limit is true for `API Error: 428 {"message": "limit"}`, `status (428)` and `HTTP 428:`, and false for `14280 tokens`, `4280`, `""` and `rate limited`; with `message` `spend limit` it is true for `the spend limit is reached` without a status (rows).
5. `ProviderLimit` refuses status 99 and 600 and accepts 100 and 599, and refuses `message` `"("` (rows).
6. `named_wait` gives 420 seconds for `try again in 7 minutes`, 420 for `in 7 min` and for `in 7 m`, 120 seconds for `retry after 120 seconds`, `in 120 s`, `in 120 sec`, `Retry-After: 120` and `retry-after 120`, 2 hours for `in 2 h` and `in 2 hours`, 1 hour for `in 1 hour`, 45 seconds for `in 45`, the earlier of two, and `None` for `in 0 minutes`, `in 1234567`, `limit reached` and `in seven minutes` (rows).
7. `read_settings` gives status 428 and message `None` without the variables or with blank ones, 429 for `429`; it raises `SettingsInvalid` naming `FACTORY_PROVIDER_LIMIT_STATUS` for `abc`, `99`, `600` and `٤٢٨`, and naming `FACTORY_PROVIDER_LIMIT_MESSAGE` for `(` (rows); `FACTORY_PROVIDER_LIMIT_MESSAGE` `spend limit` gives `provider_limit.message` `spend limit`.
8. `stall_cause("provider_limit")` is `the provider's spend limit lasted past the waiting ceiling`, and `stall_note("provider_limit", 1, 2)` is `Stalled (attempt 1 of 2): the provider's spend limit lasted past the waiting ceiling. Retrying on the next tick.`
9. A stand-in `claude` that prints an error reply (`is_error` true) with `result` `API Error: 428 spend limit reached, try again in 7 minutes`, cost 0.01 and one turn ends the run `provider_limit` with that cost and turn, `limit_wait` 420 seconds and `session` the id the stand-in got with `--session-id`; the same reply with `result` `API Error: 500` ends `died` (rows).
10. A stand-in that prints no reply and `API Error: 428, try again in 7 minutes` on standard error ends `provider_limit` without measures and with `limit_wait` 420 seconds; the same with `API Error: 428` alone ends `provider_limit` with `limit_wait` `None`; a runtime built with `ProviderLimit(status=429)` ends the same call `died`; a runtime built with `ProviderLimit(message="spend limit")` recognizes `result` `the spend limit is reached`; a call that prints `API Error: 428` on standard error and outlasts its time limit of 3 seconds ends `time_limit`; a budget reply (`error_max_budget_usd`) whose `result` names 428 ends `budget` and is resumed (rows).
11. A run whose budget stop is resumed and whose resume prints the 428 error reply ends `provider_limit` with both calls' measures and the session of both calls.
12. A request with `resume_session` `"ses_a"` makes the stand-in see `--resume ses_a` and no `--session-id`, with the request's prompt and `--max-budget-usd` of the agent's budget; the result's `session` is `ses_a`; a completed run of a request without it has a `session` equal to its `--session-id`; the run's files of a request with `resume_session` are named by a fresh id that differs from `resume_session` (rows).
13. A request with `resume_session` whose call is stopped by its budget is resumed once with `--resume ses_a` and the finish message.
14. The opencode runtime with `resume_session` `"ses_a"` calls the stand-in with `--session ses_a` right before the prompt; its result's `session` is the first `sessionID` of the events, and `ses_a` when no event carries one; a run without it and without events has `session` `None` (rows).
15. `build_boundaries` with a `provider_limit` of status 429 gives a Claude Code runtime whose run ends `provider_limit` on a stand-in error result naming 429 (`confine_executable=None`).
16. `CostRecorder.complete` with a `provider_limit` result that holds one refused call naming `/work/a.py` writes `end_reason` `provider_limit`, `denials` 1 and `denied_paths` `["/work/a.py"]`; with no refused call, `denials` 0 and `denied_paths` `[]`; a `died` and a `time_limit` result leave both unknown (rows).
17. A `JournalRecord` of kind `stall` with `reason` `provider_limit` is valid and round-trips through the work item's state; every value of `StallReason` in `factory.domain.journal` is still a row of F0021-S0001's criterion that covers them, and `factory.domain.decisions.StallReason` is the same type.
18. The records contract's version is `1.2` and the committed schemas are the generated ones: `provider_limit` is among the values of `end_reason` in `cost-record.schema.json` and of the journal record's `reason` in `work-item-state.schema.json` and `acceptance-state.schema.json`; `stop-record.schema.json` and `pipeline-definition.schema.json` differ from the earlier ones only in `x-records-contract`, which reads `1.2` in all five; `uv run python -m factory.entry.contract` leaves the committed files unchanged (the existing comparison test passes).
19. `make check` stays green.
20. docs: `docs/operator-guide.md`: the configuration table gets `FACTORY_PROVIDER_LIMIT_STATUS` (default 428) and `FACTORY_PROVIDER_LIMIT_MESSAGE` (a regular expression, unset by default), with a sentence on what each matches and where (an error result or event and standard error, never the agent's own text); the stall reasons gain `provider_limit`; the records contract's version now reads `1.2` and the cost record's `end_reason` and the journal record's `reason` list `provider_limit`. `docs/project-guide/agents.md`: the end reason `provider_limit`, `AgentRunResult.session` and `limit_wait`, `AgentRunRequest.resume_session` and how each runtime resumes a session. `docs/decisions.md`: an entry *A provider's spend limit is its own end reason, and the session is kept*, dated with the story, with the reasons of the feature's decisions 12 and 13.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir "$d/work"
cat > "$d/claude" <<'EOF'
#!/bin/sh
printf '%s\n' "$*" >> "$(dirname "$0")/arguments"
printf '%s\n' '{"type":"result","subtype":"success","is_error":true,"num_turns":1,"total_cost_usd":0.01,"result":"API Error: 428 spend limit reached, try again in 7 minutes","usage":{"input_tokens":1,"output_tokens":1},"permission_denials":[]}'
EOF
chmod +x "$d/claude"
uv run -q python - "$d" <<'EOF'
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from factory.domain.provider_limits import ProviderLimit, limit_in_text, named_wait

d = Path(sys.argv[1])
agent = AgentDefinition(name="coder", model="sonnet", tools=["Read"], budget_usd=Decimal("1"), instructions="Smoke.")
request = AgentRunRequest(agent=agent, prompt="Smoke.", allowed_decisions=["question"], time_limit=timedelta(seconds=60), working_directory=d / "work", environment={"PATH": "/usr/bin:/bin"})
runtime = ClaudeCodeRuntime(str(d / "claude"), d / "state")
first = runtime.run(request)
print(first.end_reason, first.cost_usd, first.limit_wait.total_seconds())
second = runtime.run(AgentRunRequest(agent=agent, prompt="Continue.", allowed_decisions=["question"], time_limit=timedelta(seconds=60), working_directory=d / "work", environment={"PATH": "/usr/bin:/bin"}, resume_session=first.session))
calls = (d / "arguments").read_text(encoding="utf-8").splitlines()
print(f"--session-id {first.session}" in calls[0], f"--resume {first.session}" in calls[1], second.session == first.session)
print(limit_in_text("HTTP 428:", ProviderLimit()), limit_in_text("14280 tokens", ProviderLimit()), named_wait("Retry-After: 120"))
EOF
```
Expect: three lines, `provider_limit 0.01 420.0`, `True True True`, `True False 0:02:00`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: Format check passed. I checked the Interface, criteria, smoke test, architecture and scope. The architecture and the scope are fine: the layers are right, and everything is inside F0020's scope and decisions 12, 13, 19 and 23. The smoke test is runnable, and each of its Expect values can be checked. Three Interface clauses have no criterion, and I did not answer them myself:

   1. `read_settings` with `FACTORY_PROVIDER_LIMIT_MESSAGE` set to a valid regular expression (for example `spend limit`) should give `InstanceSettings.provider_limit.message` equal to that value. Criterion 7 only covers the unset, blank and invalid (`(`) cases. Without this, a coder could ignore a valid value and still pass. Proposed: add a row to criterion 7 where the message variable is `spend limit` and `provider_limit.message` is `spend limit`. A row where the status variable is `429` and `provider_limit.status` is 429 is already there.

   2. `claude_runtime` says that with `resume_session` "the run's files are still named by a fresh id". No criterion tests it. Proposed: add to criterion 12 that the run's files (the run folder or file the runtime names by the id) use a new id that differs from `resume_session`. Or say which observable thing the test checks. Or drop the clause.

   3. `limit_wait` for the standard-error path ("`named_wait` of that `result` or line"): criterion 9 tests the wait only for the `result` path. Criterion 10's standard-error row says "without measures" and does not mention the wait. Proposed: change that row so a stand-in printing `API Error: 428, try again in 7 minutes` on standard error gives `limit_wait` of 420 seconds. Also add a row where the stderr line names no wait and `limit_wait` is `None`.

   I would choose all three proposals as written.
4. 2026-10-19 human: 1. Yes: add the row to criterion 7 (message variable `spend limit` gives `provider_limit.message` `spend limit`).
   2. Yes, the first proposal: add to criterion 12 that the run's files use a new id that differs from `resume_session`.
   3. Yes: change criterion 10's standard-error row so `API Error: 428, try again in 7 minutes` gives `limit_wait` 420 seconds, and add the row where the line names no wait and `limit_wait` is `None`.
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete modules and signatures are named (`domain.agent_runs`, `domain.provider_limits`, `domain.settings`, `domain.journal`/`post_texts`, `adapters.claude_runtime`/`opencode_runtime`, `application.costs`, `domain.contract`, `entry.wiring`). The behaviours in its comments each have a criterion now, after the human's answer (entry 4).
   - Criteria: each can be tested by one test function. Each rule has its failing side: blank `resume_session`, `limit_wait` on a non-limit reason and zero, status 99 and 600, an invalid message regular expression, invalid settings values, `died` on 500 or on status 429, `time_limit` beating the limit, and a budget reply that names 428. I wrote in the three additions from the human's answer in entry 4:
     - Criterion 7 has a new row: `FACTORY_PROVIDER_LIMIT_MESSAGE` `spend limit` gives `provider_limit.message` `spend limit`.
     - Criterion 12 now also checks that the run's files of a request with `resume_session` use a fresh id that differs from `resume_session`.
     - Criterion 10's standard-error row now gives `limit_wait` 420 seconds for `API Error: 428, try again in 7 minutes`, and `None` for `API Error: 428` alone.
   - Smoke test: runnable with a stand-in `claude`. The three Expect values (`provider_limit 0.01 420.0`, `True True True`, `True False 0:02:00`) can be checked against the output.
   - Architecture: pure rules are in `domain`, the tool-specific recognition is in the adapters, and the wiring is in `entry`. The layer order is kept.
   - Scope: inside F0020's scope and its decisions 12, 13, 19 and 23. The test changes it names are the ones decision 19 allows.
7. factory: started tests as self.
8. tester: Question: when the records contract goes to 1.2, an earlier story's test breaks, and the story does not name that test. `tests/domain/test_contract_login.py::test_the_committed_cost_record_schema_lists_the_optional_login_at_version_1_1` checks `RECORDS_CONTRACT == "1.1"` and checks that all five schemas say `"1.1"`. After criterion 18 that test is red, so criterion 19 (`make check` green) cannot pass. Under decision 19 the story lets the tester change only `test_contract.py` and `test_agent_runs.py`.

   Options:
   - (a) Remove that test's two version assertions, keep its login checks, and rename it to `test_the_committed_cost_record_schema_lists_the_optional_login`. The new `tests/domain/test_contract_provider_limit.py` now checks that the version is 1.2.
   - (b) Keep the name and change both `"1.1"` to `"1.2"`. The name would then be wrong.
   - (c) Leave it red. This contradicts criterion 19.

   I would choose (a). If you agree, I make exactly that change and nothing else in the module.

   Tests written so far, which stay in the tree:
   - criterion 1: tests/domain/test_agent_runs.py::test_question_and_the_six_end_reasons (renamed under decision 19: count 6, set gains `provider_limit`) and tests/domain/test_agent_runs_session.py::test_a_limit_wait_is_positive_and_only_on_a_provider_limit
   - criterion 2: tests/domain/test_agent_runs_session.py::test_a_session_to_resume_is_not_blank
   - criterion 3: tests/domain/test_agent_runs_session.py::test_a_resumed_result_takes_the_second_session_else_the_first_and_the_second_wait
   - criterion 4: tests/domain/test_provider_limits.py::test_the_limit_is_in_a_text_by_its_whole_status_or_its_message
   - criterion 5: tests/domain/test_provider_limits.py::test_a_limit_needs_an_http_status_and_a_message_that_compiles
   - criterion 6: tests/domain/test_provider_limits.py::test_the_named_wait_is_the_first_one_the_text_names. The "earlier of two" rows are mine: `retry after 30 seconds, or else in 7 minutes` gives 30 s, and `try again in 7 minutes; Retry-After: 120` gives 420 s.
   - criterion 7: tests/domain/test_settings_provider_limit.py::test_the_limit_status_is_read_or_refused (also 100 and 599 accepted, as the Interface's range says) and ::test_the_limit_message_is_read_or_refused
   - criterion 8: tests/domain/test_provider_limit_stall_text.py::test_the_provider_limit_stall_has_its_sentence_and_note
   - criteria 9 and 10: tests/adapters/test_claude_runtime_provider_limit.py::test_a_call_the_limit_refused_ends_provider_limit_with_its_wait_and_session (rows), plus ::test_a_call_past_its_time_limit_ends_time_limit_though_it_named_the_limit (its own small executable prints `API Error: 428` on standard error, then outlasts a 3 s limit; the elapsed time must stay under 20 s) and ::test_a_budget_stop_that_names_the_status_ends_budget_and_is_resumed
   - criterion 11: tests/adapters/test_claude_runtime_provider_limit.py::test_a_resume_the_limit_refused_ends_provider_limit_with_both_calls_measures
   - criterion 12: tests/adapters/test_claude_runtime_resume_session.py::test_a_run_starts_a_new_session_or_resumes_the_named_one_and_keeps_it. The run-files id is read from the `--append-system-prompt-file` name.
   - criterion 13: tests/adapters/test_claude_runtime_resume_session.py::test_a_resumed_session_stopped_by_its_budget_is_resumed_once_with_the_finish_message
   - criterion 14: tests/adapters/test_opencode_resume_session.py::test_a_run_resumes_the_named_session_and_reports_the_first_session_of_its_events
   - criterion 15: tests/entry/test_wiring_provider_limit.py::test_the_built_runtime_recognizes_the_configured_limit_status
   - criterion 16: tests/application/test_costs_provider_limit.py::test_a_provider_limit_record_counts_its_denials_and_keeps_its_end_reason
   - criterion 17: tests/domain/test_provider_limit_stall_text.py::test_a_provider_limit_stall_record_round_trips_through_the_work_item_state and ::test_the_decisions_stall_reason_is_the_journals_type. The rows over every `StallReason` value in tests/domain/test_journal_causes.py pick up the new value without any change.
   - criterion 18: tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version (expected version now "1.2", name kept, under decision 19) and the new tests/domain/test_contract_provider_limit.py::test_the_committed_schemas_list_provider_limit_at_version_1_2. That "stop-record and pipeline-definition change only in their version" is left to the existing comparison of generated and committed schemas.

   Files created: tests/domain/test_provider_limits.py, tests/domain/test_agent_runs_session.py, tests/domain/test_settings_provider_limit.py, tests/domain/test_provider_limit_stall_text.py, tests/domain/test_contract_provider_limit.py, tests/adapters/test_claude_runtime_provider_limit.py, tests/adapters/test_claude_runtime_resume_session.py, tests/adapters/test_opencode_resume_session.py, tests/entry/test_wiring_provider_limit.py, tests/application/test_costs_provider_limit.py.

   Earlier test files changed: tests/domain/test_agent_runs.py and tests/domain/test_contract.py, both only as the story names, under decision 19.

   Helpers are imported, not copied:
   - `_request` and `REPLY` from adapters/test_claude_runtime_os_user
   - `_after` and `_budget_reply` from adapters/test_claude_runtime_resume
   - `_runtime` from adapters/test_opencode_runtime
   - `_committed` and `_values` from domain/test_contract_login

   Module the test run could not import: `factory.domain.provider_limits`. It causes collection errors in test_provider_limits.py, test_claude_runtime_provider_limit.py and test_wiring_provider_limit.py. The other new tests fail because the new fields and `provider_limit` don't exist yet, or the runtime doesn't use `--resume` yet. `make lint` is green.
9. 2026-10-19 human: (a): leave, in the form of decision 19: in `tests/domain/test_contract_login.py`, remove the two version assertions of `test_the_committed_cost_record_schema_lists_the_optional_login_at_version_1_1`, keep its login checks, and rename it `test_the_committed_cost_record_schema_lists_the_optional_login`; nothing else in that module. The version is pinned by your new `tests/domain/test_contract_provider_limit.py`.
10. factory: started tests as self.
11. tester: I made the change the human approved in entry 9 (option a). In `tests/domain/test_contract_login.py` I renamed `test_the_committed_cost_record_schema_lists_the_optional_login_at_version_1_1` to `test_the_committed_cost_record_schema_lists_the_optional_login`. I removed its two version assertions: `RECORDS_CONTRACT == "1.1"` and the check that all five schemas carry "1.1". Its login checks are unchanged. The only other edit in that module is the import of `CONTRACT, RECORDS_CONTRACT, schema_file_name`, which I removed because nothing used it once the assertions were gone and lint would otherwise fail. The module's docstring is unchanged. `tests/domain/test_contract_provider_limit.py` now pins the version at 1.2.

    Criterion → test (the tests written in entry 8 are unchanged):
    - criterion 1: tests/domain/test_agent_runs.py::test_question_and_the_six_end_reasons, tests/domain/test_agent_runs_session.py::test_a_limit_wait_is_positive_and_only_on_a_provider_limit
    - criterion 2: tests/domain/test_agent_runs_session.py::test_a_session_to_resume_is_not_blank
    - criterion 3: tests/domain/test_agent_runs_session.py::test_a_resumed_result_takes_the_second_session_else_the_first_and_the_second_wait
    - criterion 4: tests/domain/test_provider_limits.py::test_the_limit_is_in_a_text_by_its_whole_status_or_its_message
    - criterion 5: tests/domain/test_provider_limits.py::test_a_limit_needs_an_http_status_and_a_message_that_compiles
    - criterion 6: tests/domain/test_provider_limits.py::test_the_named_wait_is_the_first_one_the_text_names
    - criterion 7: tests/domain/test_settings_provider_limit.py::test_the_limit_status_is_read_or_refused, ::test_the_limit_message_is_read_or_refused
    - criterion 8: tests/domain/test_provider_limit_stall_text.py::test_the_provider_limit_stall_has_its_sentence_and_note
    - criterion 9: tests/adapters/test_claude_runtime_provider_limit.py::test_a_call_the_limit_refused_ends_provider_limit_with_its_wait_and_session
    - criterion 10: tests/adapters/test_claude_runtime_provider_limit.py::test_a_call_the_limit_refused_ends_provider_limit_with_its_wait_and_session (rows), ::test_a_call_past_its_time_limit_ends_time_limit_though_it_named_the_limit, ::test_a_budget_stop_that_names_the_status_ends_budget_and_is_resumed
    - criterion 11: tests/adapters/test_claude_runtime_provider_limit.py::test_a_resume_the_limit_refused_ends_provider_limit_with_both_calls_measures
    - criterion 12: tests/adapters/test_claude_runtime_resume_session.py::test_a_run_starts_a_new_session_or_resumes_the_named_one_and_keeps_it
    - criterion 13: tests/adapters/test_claude_runtime_resume_session.py::test_a_resumed_session_stopped_by_its_budget_is_resumed_once_with_the_finish_message
    - criterion 14: tests/adapters/test_opencode_resume_session.py::test_a_run_resumes_the_named_session_and_reports_the_first_session_of_its_events
    - criterion 15: tests/entry/test_wiring_provider_limit.py::test_the_built_runtime_recognizes_the_configured_limit_status
    - criterion 16: tests/application/test_costs_provider_limit.py::test_a_provider_limit_record_counts_its_denials_and_keeps_its_end_reason
    - criterion 17: tests/domain/test_provider_limit_stall_text.py::test_a_provider_limit_stall_record_round_trips_through_the_work_item_state, ::test_the_decisions_stall_reason_is_the_journals_type (the existing rows over every `StallReason` value in tests/domain/test_journal_causes.py also cover it)
    - criterion 18: tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version (expects "1.2"), tests/domain/test_contract_provider_limit.py::test_the_committed_schemas_list_provider_limit_at_version_1_2, and the existing comparison of generated and committed schemas

    Files created (entry 8): tests/domain/test_provider_limits.py, tests/domain/test_agent_runs_session.py, tests/domain/test_settings_provider_limit.py, tests/domain/test_provider_limit_stall_text.py, tests/domain/test_contract_provider_limit.py, tests/adapters/test_claude_runtime_provider_limit.py, tests/adapters/test_claude_runtime_resume_session.py, tests/adapters/test_opencode_resume_session.py, tests/entry/test_wiring_provider_limit.py, tests/application/test_costs_provider_limit.py.

    Earlier test files changed:
    - tests/domain/test_agent_runs.py and tests/domain/test_contract.py, under decision 19.
    - tests/domain/test_contract_login.py, with the human's leave in entry 9.

    Module the test run could not import: `factory.domain.provider_limits`. This causes collection errors in test_provider_limits.py, test_claude_runtime_provider_limit.py and test_wiring_provider_limit.py. The other new tests fail because the new fields and the `provider_limit` behaviour do not exist yet. `make lint` is green.

    `lint`: lint: green (0.0 s)
    `test`: ERROR tests/entry/test_wiring_provider_limit.py - ImportError while importing...
12. factory: started doing as self.
13. coder: I made the failing tests pass without editing any test. `make check` is green.

    What I built:
    - `src/factory/domain/provider_limits.py` (new). It holds `ProviderLimit`: status 100 to 599, and a `message` that must compile; a `re.error` is turned into a `ValueError` so Pydantic refuses it. It also holds `limit_in_text`, which matches the status as a whole number through `(?<!\d)`/`(?!\d)` or searches the message, and `named_wait`, which is one case-insensitive regex. Its unit list puts the longer names first, so `min` is not read as `m`.
    - `src/factory/domain/agent_runs.py`:
      - `EndReason` gains `provider_limit`.
      - `AgentRunRequest.resume_session` refuses a blank value.
      - `AgentRunResult.session` and `limit_wait` are new; a separate validator refuses a `limit_wait` on any other reason, or one that is not positive.
      - `resumed_result` takes the second call's session, else the first's.
    - `src/factory/domain/settings.py`: `PROVIDER_LIMIT_STATUS_VARIABLE`, `PROVIDER_LIMIT_MESSAGE_VARIABLE` and `InstanceSettings.provider_limit`. The status takes ASCII digits only, the same guard as `_min_free_gb`.
    - `src/factory/domain/journal.py` and `src/factory/domain/post_texts.py`: the stall reason `provider_limit` and its sentence.
    - `src/factory/domain/contract.py`: `RECORDS_CONTRACT` is now `"1.2"`. I regenerated the five schemas under `src/factory/contract/` with `uv run python -m factory.entry.contract`.
    - `src/factory/adapters/claude_runtime.py`:
      - `_Reply.result` is new, and so is the constructor keyword `provider_limit`.
      - `_limit_text` returns the error reply's `result`, or, when no reply parses, the first standard error line that holds the limit. `_end_reason` checks it after `time_limit` and `budget`.
      - `limit_wait` is `named_wait` of that text.
      - Every result carries `session`.
      - `_session_arguments` uses `--resume <resume_session>` in place of `--session-id`. The run's files still take a fresh uuid.
      - `_resume_arguments` leaves an existing `--resume` as it is.
      - Adding the new return in `_end_reason` hit ruff's PLR0911 limit, so I moved the answer check into `_answered`.
    - `src/factory/adapters/opencode_runtime.py`:
      - `_Event.session_id` (alias `sessionID`) is new.
      - `_session` gives the first event's session, else the request's `resume_session`.
      - `--session <id>` goes right before the prompt.
      - A time-limited result also carries the session, so the events are now parsed before the time-limit return.
    - `src/factory/entry/wiring.py`: passes `settings.provider_limit` to `ClaudeCodeRuntime`.
    - `src/factory/application/costs.py` needed no change: it already treats only `died` and `time_limit` as having no reply.

    Main design choice: `_result` in the Claude runtime is given the session as a parameter, and the resume call gets `first.session`. I rejected two alternatives:
    - Reading the session back from the argument list.
    - A helper that raises when a result has no session. That would be a branch no test can reach, only there to satisfy the type.

    I also rejected stretching `_end_reason` with a seventh return and a lint exception. Splitting out `_answered` keeps it under ruff's limit.

    Refactor pass: I moved the comment in the opencode `_result` back next to the `if process.timed_out` it explains. Nothing else needed changing.

    Seen but not touched: `make duplicates` reports 5 new findings, none from this story's diff. Three are code shared between the two runtimes, at the `call_refusal`, `version_printed` and `confine_executable` blocks. Two are vulture dead-code reports: `status_code` at opencode_runtime.py:193 and the class `OpencodeRuntime`. The opencode ones are not in `security/duplicates-baseline.txt` (it has no opencode entries at all), so they most likely come from the earlier opencode stories. The docs (criterion 20) are for the docs stage.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 35 known, 1 gone
14. factory: started review as self.
15. reviewer: Review, round 0. I read the work item and `git diff main...HEAD -- . ':!factory'` without the generated schemas. Of those schemas, I checked that `stop-record` and `pipeline-definition` differ only in `x-records-contract` (now `1.2`). The factory's `make check` after the coder was green (entry 13). Group 1 (acceptance criteria) fails, so this report stops there. The other criteria each have a passing test that checks what the criterion says. I checked these points:
    - the budget row really uses an `is_error` reply naming 428, so the ordering is pinned
    - the run-files id is read from the instructions file name
    - `--session` comes right before the prompt
    - `_events` skips malformed lines, so parsing before the time-limit return cannot raise

    Findings:
    1. `tests/domain/test_provider_limits.py`, `test_the_named_wait_is_the_first_one_the_text_names`: the Interface's limit "`<n>` has one to six digits" is tested only on its refused side (`in 1234567` → `None`). No row has six digits, so a pattern capped at three or four digits would still pass every row. Fix: add a row such as `in 999999` → `timedelta(seconds=999999)` (and `retry-after 999999` for the second form) to the same parametrized table.
    2. `tests/adapters/test_claude_runtime_provider_limit.py`, `test_a_budget_stop_that_names_the_status_ends_budget_and_is_resumed`: criterion 10 asks for rows, but this side of the rule (a budget stop beats the limit) is a separate test function. The table `test_a_call_the_limit_refused_ends_provider_limit_with_its_wait_and_session` could hold it if its step became a list of steps. Fix: make it a row of that parametrized table, with the expected end reason `budget` and `limit_wait` `None`, plus the resume check. The time-limit case can stay separate: it needs its own executable that prints to standard error before it waits, which `Step` cannot do.

    Earlier tests:
    - tests/domain/test_agent_runs.py: the leave the story names under the feature's decision 19 (rename to `test_question_and_the_six_end_reasons`, count 6, `provider_limit` added); within that leave.
    - tests/domain/test_contract.py: the leave the story names under decision 19 (expected version `"1.2"`, name kept); within that leave.
    - tests/domain/test_contract_login.py: the human's leave in journal entry 9 (two version assertions removed, test renamed). The removed import is the unused import that this removal left, so it is within that leave.
16. factory: started doing as self.
17. coder: Round 1. Both of the reviewer's findings in entry 15 are changes to tests, not to code. I changed nothing under `src/`, and the code from entry 13 stays as it is.

    Changes for the tester:
    1. `tests/domain/test_provider_limits.py`, `test_the_named_wait_is_the_first_one_the_text_names`: add the accepted side of the one-to-six-digit limit. That means a row `in 999999` → `timedelta(seconds=999999)`, plus a row for the second form, `retry-after 999999`, in the same parametrized table.
    2. `tests/adapters/test_claude_runtime_provider_limit.py`: fold `test_a_budget_stop_that_names_the_status_ends_budget_and_is_resumed` into `test_a_call_the_limit_refused_ends_provider_limit_with_its_wait_and_session` as a row. The table's step becomes a list of steps, and the new row expects end reason `budget`, `limit_wait` `None`, and the resume check. The time-limit case stays a separate test.

    What I expect from the code: `named_wait` in `src/factory/domain/provider_limits.py` already accepts up to six digits, so the new rows should pass without a code change. If either one fails, the work item comes back here.

    Not touched: the 5 new `make duplicates` findings reported in entry 13. None of them comes from this story's diff.
18. factory: started tests as self.
