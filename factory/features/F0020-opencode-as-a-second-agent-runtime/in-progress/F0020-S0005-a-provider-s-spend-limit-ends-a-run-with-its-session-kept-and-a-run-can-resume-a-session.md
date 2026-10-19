---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 254
comments_read: [6261999766]
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-19T07:27:16.139978Z'
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
7. `read_settings` gives status 428 and message `None` without the variables or with blank ones, 429 for `429`; it raises `SettingsInvalid` naming `FACTORY_PROVIDER_LIMIT_STATUS` for `abc`, `99`, `600` and `٤٢٨`, and naming `FACTORY_PROVIDER_LIMIT_MESSAGE` for `(` (rows).
8. `stall_cause("provider_limit")` is `the provider's spend limit lasted past the waiting ceiling`, and `stall_note("provider_limit", 1, 2)` is `Stalled (attempt 1 of 2): the provider's spend limit lasted past the waiting ceiling. Retrying on the next tick.`
9. A stand-in `claude` that prints an error reply (`is_error` true) with `result` `API Error: 428 spend limit reached, try again in 7 minutes`, cost 0.01 and one turn ends the run `provider_limit` with that cost and turn, `limit_wait` 420 seconds and `session` the id the stand-in got with `--session-id`; the same reply with `result` `API Error: 500` ends `died` (rows).
10. A stand-in that prints no reply and `API Error: 428` on standard error ends `provider_limit` without measures; a runtime built with `ProviderLimit(status=429)` ends the same call `died`; a runtime built with `ProviderLimit(message="spend limit")` recognizes `result` `the spend limit is reached`; a call that prints `API Error: 428` on standard error and outlasts its time limit of 3 seconds ends `time_limit`; a budget reply (`error_max_budget_usd`) whose `result` names 428 ends `budget` and is resumed (rows).
11. A run whose budget stop is resumed and whose resume prints the 428 error reply ends `provider_limit` with both calls' measures and the session of both calls.
12. A request with `resume_session` `"ses_a"` makes the stand-in see `--resume ses_a` and no `--session-id`, with the request's prompt and `--max-budget-usd` of the agent's budget; the result's `session` is `ses_a`; a completed run of a request without it has a `session` equal to its `--session-id` (rows).
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
