---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The claude agent runtime: the call and its result

## Assignment (as of log entry 1)

Build the first half of the first implementation of the agent-runtime interface (R12): `ClaudeCodeRuntime.run`, which runs an agent as one `claude -p` call under the operator's own login, in v1's way. It turns an `AgentRunRequest` into the call's flags (model, effort, tools, a session id the factory chooses, the agent's instructions as a system-prompt file, the guard hook as a settings file, the budget, a JSON schema for the decision and the entry), runs it in the working directory with exactly the environment the request gives plus three switches, and turns the JSON the call prints into an `AgentRunResult`: completed with a decision and an entry, or one of the other end reasons, with the duration measured by the factory and cost and tokens left unknown when the call reported none. It reaches the `agent-run` kill point after the run's writes. The budget resume (a stop on the budget gets one more short call), the `time_limit` that counts across both calls, and the version query follow in S0010; this story makes one call. That is why `ClaudeCodeRuntime` satisfies the `AgentRuntime` protocol only with S0010, which adds `version`. The guard hook command (`factory-guard`) is built by F0004; running as another OS user and scrubbing the environment are F0010. Covers R12, R7 and R24 (a timed-out or killed run's cost and tokens are unknown, never invented); keeps kept thing 20 (duration, turns, tokens and cost of every agent run are reported) and R5 (a search shows the three wrappers are the only users of `run_process`). The flags are those of v1's book (chapter 8, "Starting the agent"); none is added. They were not checked against the pinned `claude`: that check is a morning observation, tied to F0010's preflight probe (ST5.3). Tests use a stand-in executable written into `tmp_path`, never the real `claude`.

## Interface

`src/factory/adapters/claude_runtime.py`

```python
ENTRY_DESCRIPTION = "your journal entry, without its number or your name: everything your instructions say the entry contains"

class ClaudeCodeRuntime:
    def __init__(self, executable: str, state_directory: Path, kill_points: KillPoints | None = None) -> None: ...
    def run(self, request: AgentRunRequest) -> AgentRunResult: ...
```

The call, argument by argument, in this order (`executable` is the program; `<session>` is a new `uuid4` in its hyphenated form):

```text
-p <request.prompt>
--model <agent.model>
--effort <agent.effort>                              only when effort is set
--tools <agent.tools joined with commas>             always; an empty list gives an empty value
--session-id <session>
--append-system-prompt-file <state_directory>/instructions-<session>.md
--settings <state_directory>/hooks-<session>.json    only when request.guard is set
--permission-mode auto
--permission-prompts none
--strict-mcp-config
--max-budget-usd <format(agent.budget_usd, "f")>
--output-format json
--json-schema <the schema below as JSON text>
```

The files written under `state_directory` (created, with its parents, when missing) before the call and removed when the run ends, however it ends (a result, `InjectedKill`, `AgentRuntimeError`):

- `instructions-<session>.md`: `agent.instructions`.
- `guard-<session>.json`, only when `request.guard` is set: `request.guard.model_dump_json()`.
- `hooks-<session>.json`, only when `request.guard` is set: the Claude Code settings

```json
{"hooks": {"PreToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "factory-guard --settings <guard file path, shell-quoted>"}]}]}}
```

The JSON schema of the decision:

```json
{"type": "object",
 "properties": {
   "decision": {"type": "string", "enum": ["<request.allowed_decisions, in order>"]},
   "entry": {"type": "string", "description": "<ENTRY_DESCRIPTION>"}},
 "required": ["decision", "entry"],
 "additionalProperties": false}
```

The rules, each with a criterion below:

- The call runs in `request.working_directory` with the environment `request.environment` plus `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1` and `PYTHONDONTWRITEBYTECODE=1`; nothing is inherited from the factory's own environment and nothing else is added, `PATH` included. The hook command `factory-guard` is therefore found through the `PATH` that the request's environment carries; giving the request one that holds `factory-guard` is F0005's and F0010's. `request.os_user` is not used here.
- The call prints one JSON object. The fields read are `subtype` (string) and `is_error` (bool), which are required, and `num_turns`, `total_cost_usd` (a JSON number, taken as `Decimal(str(value))`), `usage` (`input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`), `permission_denials` (a list of objects with `tool_name` and `tool_input`) and `structured_output` (`decision`, `entry`), which are optional.
- The end reason is: `time_limit` when the call was ended by the time limit; otherwise `died` when the exit status is not 0, or the output is not a JSON object with `subtype` and `is_error`, or `is_error` is true; otherwise `completed` when `structured_output` has a `decision` that is one of `allowed_decisions` and a non-blank `entry`, and `no_result` in every other case. A reply whose `subtype` is `error_max_budget_usd` is not decided here: S0010 resumes it, whatever the exit status, before this rule applies; no criterion of this story sends such a reply.
- Measures come from the JSON object whenever the output is one, except for a call ended by the time limit; they are unknown (`None`) otherwise and for every field the JSON does not carry. `turns` is `num_turns`; `cost_usd` is `total_cost_usd`; `tokens` is known when `input_tokens` and `output_tokens` are both present (the cache counts default to 0) and unknown otherwise; each denial is `PermissionDenial(tool=tool_name, detail=json.dumps(tool_input, sort_keys=True))`.
- `duration` is the time the factory measured from the start of `run` to its end; the JSON's own durations are ignored. The call is killed with its children at `request.time_limit`.
- After the call has ended and the result is made, `run` reaches `KillPoint.AGENT_RUN` (when it has kill points), whatever the end reason, and then returns.
- A call that cannot be started (the executable is missing, the state directory cannot be written) raises `AgentRuntimeError` whose detail names the cause; the kill point is not reached.
- Only `factory.adapters.git_cli`, `factory.adapters.make_commands` and `factory.adapters.claude_runtime` import `factory.adapters.process`.

Tests: `tests/adapters/test_claude_runtime.py`, `tests/adapters/claude_stand_in.py` (`write_stand_in(directory, steps)` writes an executable Python script whose first line is `#!` and `sys.executable`; on each call it appends a record of its arguments, its whole environment, its working directory and the content of every file named in its arguments, and of the file named after `--settings` inside the hook command of the hooks file, to `calls.jsonl` beside it, then plays the next step: write files, wait, print stdout and stderr, exit with a status; `read_calls(directory)` returns the records), `tests/test_wrapper_search.py` (uses `tests/source_search.py` from S0003). The only waiting in the tests is for a stand-in that the `time_limit` kills, and a stand-in that waits a fraction of a second to give `duration` something to measure.

## Acceptance criteria

1. For a request with `effort="high"`, tools `["Read", "Edit"]`, a guard, `allowed_decisions=["review", "doing", "question"]` and a budget of `Decimal("3")`, the call's arguments are exactly the list in the Interface, in that order, with the model, `high`, `Read,Edit`, a `--session-id` that is a valid UUID, the paths under `state_directory`, `3` as the budget, and the prompt after `-p`; the arguments hold `--permission-mode auto` followed by `--permission-prompts none`.
2. For a request without `effort`, without `guard` and with `tools=[]`, the call has no `--effort` and no `--settings`, and `--tools` is followed by an empty argument.
3. The `--json-schema` argument parses to the schema of the Interface, with the `enum` equal to `allowed_decisions` in the request's order and `ENTRY_DESCRIPTION` as the description of `entry`.
4. The stand-in's working directory is `request.working_directory`.
5. For a request whose `environment` is `{"LC_ALL": "C.UTF-8", "TOKEN_PROBE": "x"}`, every variable of the stand-in's environment is one of those two, the three switches, or `LC_CTYPE` (which CPython adds to a stand-in started under the C locale); both given variables and the three switches are present with their values; a variable set in the test process is not there; and for a request whose `environment` is empty the stand-in's environment has no `PATH`.
6. While the stand-in runs, `instructions-<session>.md` holds `agent.instructions`, `guard-<session>.json` parses back to the request's `GuardSettings`, and `hooks-<session>.json` holds the settings of the Interface with the command `factory-guard --settings` and the guard file's path (quoted when it holds a space); all three are in `state_directory`.
7. After `run` returns, after `run` raises `InjectedKill`, and after `run` raises `AgentRuntimeError` for a missing executable, none of the three files is left in `state_directory`.
8. For a reply with `subtype` `success`, `is_error` false, `num_turns` 3, `total_cost_usd` 0.25, a `usage` with 10 input, 5 output, 7 cache-read and 2 cache-creation tokens, one permission denial (`tool_name` `Bash`, `tool_input` `{"command": "git push"}`) and a `structured_output` with `decision` `doing` and `entry` `Done.`, `run` returns `end_reason` `completed`, `decision` `doing`, `entry` `Done.`, `turns` 3, `cost_usd` `Decimal("0.25")`, those four token counts, and one denial with tool `Bash` and detail `{"command": "git push"}`.
9. `duration` is at least the time a stand-in waits before replying (0.3 seconds) and does not take the JSON's `duration_ms` (set to 99999) into account.
10. A reply without `num_turns`, `total_cost_usd` and `usage` gives `turns`, `cost_usd` and `tokens` equal to `None`, not 0; a reply whose `usage` has `input_tokens` only gives `tokens` `None`.
11. A successful reply gives `no_result`, with `decision` and `entry` `None`, when `structured_output` is missing, when its `decision` is not in `allowed_decisions`, and when its `entry` is blank.
12. The end reason is `died` for an exit status of 1 with a valid success reply, for an output that is not JSON, and for a reply with `is_error` true and `subtype` `error_during_execution`; in the last case the cost the reply reports is still in `cost_usd`.
13. The end reason is `died` for a JSON object without `subtype` and for one without `is_error`, each with a valid `structured_output`.
14. With `time_limit=timedelta(seconds=1)` and a stand-in that waits 60 seconds, `run` returns within 6 seconds with `end_reason` `time_limit`, `decision` `None`, and `turns`, `tokens` and `cost_usd` `None`.
15. With `KillPoint.AGENT_RUN` armed, `run` raises `InjectedKill` after the stand-in's writes are on disk, for a completed reply and for a `died` one.
16. With the point not armed, `run` returns normally and `reached(AGENT_RUN)` counts 1; a `ClaudeCodeRuntime` built without kill points returns normally.
17. With `executable="/no/such/claude"`, `run` raises `AgentRuntimeError` whose detail contains that path, and `reached(AGENT_RUN)` is 0.
18. With a `state_directory` below a regular file, `run` raises `AgentRuntimeError` whose detail names that path, the stand-in is never called, and `reached(AGENT_RUN)` is 0.
19. Among the modules of `src/factory`, exactly `factory.adapters.git_cli`, `factory.adapters.make_commands` and `factory.adapters.claude_runtime` import `factory.adapters.process`.
20. make check stays green.
21. docs: `docs/project-guide.md` describes the `claude -p` runtime so far (the flags, the files under the state directory, the environment with no inherited variable and no added `PATH`, the end reasons, unknown measures); `docs/operator-guide.md` says that the runtime uses the operator's own `claude` login and that the flags are v1's, to be checked against the pinned version (WE6.3).

## Demo

```bash
uv run python -c "
import sys, tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
root = Path(tempfile.mkdtemp())
good = '''import json
print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'num_turns': 3, 'total_cost_usd': 0.25, 'usage': {'input_tokens': 10, 'output_tokens': 5}, 'permission_denials': [], 'structured_output': {'decision': 'doing', 'entry': 'Done.'}}))
'''
bad = 'print(\"not json\")' + chr(10)
agent = AgentDefinition(name='coder', model='sonnet', tools=['Read'], budget_usd=Decimal('3'), instructions='Code.')
request = AgentRunRequest(agent=agent, prompt='Stage: doing', allowed_decisions=['review', 'doing', 'question'], time_limit=timedelta(minutes=5), working_directory=root, environment={})
for name, body in (('good', good), ('bad', bad)):
    script = root / name
    script.write_text('#!' + sys.executable + chr(10) + body)
    script.chmod(0o755)
    result = ClaudeCodeRuntime(str(script), root / 'state').run(request)
    tokens = result.tokens and (result.tokens.input, result.tokens.output)
    print(name, result.end_reason, result.decision, result.turns, result.cost_usd, tokens)
"
```
Expect: two lines: `good completed doing 3 0.25 (10, 5)`, then `bad died None None None None`.

## Log (append only)

1. 2026-10-12 human: created.
