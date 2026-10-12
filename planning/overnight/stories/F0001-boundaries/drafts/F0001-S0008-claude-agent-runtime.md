# The claude agent runtime

## Assignment (as of log entry 1)

Build the first implementation of the agent-runtime interface (R12): `ClaudeCodeRuntime`, which runs an agent as one `claude -p` call under the operator's own login, in v1's way. It turns an `AgentRunRequest` into the call's flags (model, effort, tools, a session id the factory chooses, the agent's instructions as a system-prompt file, the guard hook as a settings file, the budget, a JSON schema for the decision and the entry), runs it in the working directory with exactly the environment the request gives plus three switches, and turns the JSON the call prints into an `AgentRunResult`: completed with a decision and an entry, or one of the other end reasons, with duration measured by the factory and cost and tokens left unknown when the call reported none. When the budget is exhausted it resumes the same session once with a short budget and the message to finish; one `time_limit` counts across both calls. It reaches the `agent-run` kill point after the run's writes. It also answers the version query that the preflight uses later (F0010). The guard hook command (`factory-guard`) is built by F0004; running as another OS user and scrubbing the environment are F0010. Covers R12, R7 and R24 (a timed-out or killed run's cost and tokens are unknown, never invented); keeps kept thing 20 (duration, turns, tokens and cost of every agent run are reported) and R5 (a search shows the three wrappers are the only users of `run_process`). Tests use a stand-in executable written into `tmp_path`, never the real `claude`.

## Interface

`src/factory/adapters/claude_runtime.py`

```python
FINISH_MESSAGE = "Finish now: give your decision (question if the work is not done) and your entry."
ENTRY_DESCRIPTION = "your journal entry, without its number or your name: everything your instructions say the entry contains"
MINIMUM_RESUME_BUDGET = Decimal("0.50")

def resume_budget(budget: Decimal) -> Decimal: ...

class ClaudeCodeRuntime:      # satisfies AgentRuntime structurally, no inheritance
    def __init__(self, executable: str, state_directory: Path, kill_points: KillPoints | None = None) -> None: ...
    def run(self, request: AgentRunRequest) -> AgentRunResult: ...
    def version(self) -> str: ...
```

The first call, argument by argument, in this order (`executable` is the program; `<session>` is a new `uuid4` in its hyphenated form):

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

The files written under `state_directory` (created, with its parents, when missing) before the first call and removed when the run ends, also when a kill point ended it:

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

- The call runs in `request.working_directory` with the environment `request.environment` plus `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1` and `PYTHONDONTWRITEBYTECODE=1`; nothing is inherited from the factory's own environment. `request.os_user` is not used here.
- The call prints one JSON object. The fields read are `subtype` (string), `is_error` (bool), `num_turns`, `total_cost_usd` (a JSON number, taken as `Decimal(str(value))`), `usage` (`input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`), `permission_denials` (a list of objects with `tool_name` and `tool_input`) and `structured_output` (`decision`, `entry`).
- The end reason is: `time_limit` when the call was ended by the time limit; otherwise `died` when the exit status is not 0, or the output is not a JSON object with the fields above, or `is_error` is true with a `subtype` other than `error_max_budget_usd`; otherwise, for `subtype` `error_max_budget_usd`, the resume below; otherwise `completed` when `structured_output` has a `decision` that is one of `allowed_decisions` and a non-blank `entry`, and `no_result` in every other case.
- Measures come from the JSON object whenever the output is one, except for a call ended by the time limit; they are unknown (`None`) otherwise and for every field the JSON does not carry. `turns` is `num_turns`; `cost_usd` is `total_cost_usd`; `tokens` is known when `input_tokens` and `output_tokens` are present (the cache counts default to 0); each denial is `PermissionDenial(tool=tool_name, detail=json.dumps(tool_input, sort_keys=True))`.
- Resume. When the first call ends with `error_max_budget_usd`, the same session is resumed once: the same arguments, except `-p` is `FINISH_MESSAGE`, `--session-id <session>` becomes `--resume <session>`, and `--max-budget-usd` is `format(resume_budget(agent.budget_usd), "f")`. `resume_budget(budget)` is a quarter of the budget, at least `MINIMUM_RESUME_BUDGET`, rounded half up to cents. The measures of both calls are added up (a call that reported none adds nothing; unknown when neither reported) and the denials are joined. When the resumed call also ends with `error_max_budget_usd`, the end reason is `budget`; a third call is never made.
- One `time_limit` counts across the whole run: the first call may take `request.time_limit`, the resume what is left of it, and no resume is started when nothing is left (the end reason is then `time_limit`). A call that reaches the limit is killed with its children.
- `duration` is the time the factory measured from the start of `run` to its end, both calls included; the JSON's own durations are ignored.
- After the last call has ended and the result is made, `run` reaches `KillPoint.AGENT_RUN` (when it has kill points), whatever the end reason, and then returns.
- A call that cannot be started (the executable is missing, the state directory cannot be written) raises `AgentRuntimeError` whose detail names the cause; the kill point is not reached.
- `version()` runs `<executable> --version` with a limit of 30 seconds in the factory's environment and returns the first whitespace-separated word of the first non-blank line of its output, for example `2.1.289` for `2.1.289 (Claude Code)`. It raises `AgentRuntimeError` when the call cannot be started, exits non-zero, reaches the limit or prints nothing.
- Only `factory.adapters.git_cli`, `factory.adapters.make_commands` and `factory.adapters.claude_runtime` import `factory.adapters.process`.

Tests: `tests/adapters/test_claude_runtime.py`, `tests/adapters/claude_stand_in.py` (`write_stand_in(directory, steps)` writes an executable Python script whose first line is `#!` and `sys.executable`; on each call it appends a record of its arguments, its whole environment, its working directory and the content of every file named in its arguments to `calls.jsonl` beside it, then plays the next step: write files, wait, print stdout and stderr, exit with a status; `read_calls(directory)` returns the records), `tests/test_wrapper_search.py`. A test module assigns `ClaudeCodeRuntime` to a variable annotated `AgentRuntime`, so that mypy checks the fit. The only waiting in the tests is for a stand-in that the `time_limit` kills, and a stand-in that waits a fraction of a second to give `duration` something to measure.

## Acceptance criteria

1. For a request with `effort="high"`, tools `["Read", "Edit"]`, a guard, `allowed_decisions=["review", "doing", "question"]` and a budget of `Decimal("3")`, the first call's arguments are exactly the list in the Interface, in that order, with the model, `high`, `Read,Edit`, a `--session-id` that is a valid UUID, the paths under `state_directory`, `3` as the budget, and the prompt after `-p`.
2. For a request without `effort`, without `guard` and with `tools=[]`, the first call has no `--effort` and no `--settings`, and `--tools` is followed by an empty argument.
3. The `--json-schema` argument parses to the schema of the Interface, with the `enum` equal to `allowed_decisions` in the request's order and `ENTRY_DESCRIPTION` as the description of `entry`.
4. The stand-in's working directory is `request.working_directory`.
5. The stand-in's whole environment is `request.environment` plus the three switches, and a variable set in the test process is not in it.
6. While the stand-in runs, `instructions-<session>.md` holds `agent.instructions`, `guard-<session>.json` parses back to the request's `GuardSettings`, and `hooks-<session>.json` holds the settings of the Interface with the command `factory-guard --settings` and the guard file's path (quoted when it holds a space); all three are in `state_directory`, and after `run` returns, and after `run` raises `InjectedKill`, none of them is left.
7. For a reply with `subtype` `success`, `is_error` false, `num_turns` 3, `total_cost_usd` 0.25, a `usage` with 10 input, 5 output, 7 cache-read and 2 cache-creation tokens, one permission denial (`tool_name` `Bash`, `tool_input` `{"command": "git push"}`) and a `structured_output` with `decision` `doing` and `entry` `Done.`, `run` returns `end_reason` `completed`, `decision` `doing`, `entry` `Done.`, `turns` 3, `cost_usd` `Decimal("0.25")`, those four token counts, and one denial with tool `Bash` and detail `{"command": "git push"}`.
8. `duration` is at least the time a stand-in waits before replying (0.3 seconds) and does not take the JSON's `duration_ms` (set to 99999) into account.
9. A reply without `num_turns`, `total_cost_usd` and `usage` gives `turns`, `cost_usd` and `tokens` equal to `None`, not 0.
10. A successful reply gives `no_result`, with `decision` and `entry` `None`, when `structured_output` is missing, when its `decision` is not in `allowed_decisions`, and when its `entry` is blank.
11. The end reason is `died` for an exit status of 1 with a valid success reply, for an output that is not JSON, and for a reply with `is_error` true and `subtype` `error_during_execution`; in the last case the cost the reply reports is still in `cost_usd`.
12. With `time_limit=timedelta(seconds=1)` and a stand-in that waits 60 seconds, `run` returns within 6 seconds with `end_reason` `time_limit`, `decision` `None`, and `turns`, `tokens` and `cost_usd` `None`.
13. When the first reply has `subtype` `error_max_budget_usd`, a second call is made whose arguments are those of the first except `-p` is `FINISH_MESSAGE`, `--resume` and the same session id replace `--session-id`, and `--max-budget-usd` is the resume budget; the second call's files are the same ones.
14. `resume_budget` gives `1.00` for `Decimal("4")`, `0.75` for `Decimal("3")`, `0.50` for `Decimal("2")`, `0.50` for `Decimal("1")`, `0.50` for `Decimal("0.40")` and `0.51` for `Decimal("2.04")`.
15. When the resumed call completes, `end_reason` is `completed` and `turns`, `cost_usd` and the token counts are the sums of both calls' values, and the permission denials of both are joined, first call's first.
16. When the resumed call also ends with `error_max_budget_usd`, `end_reason` is `budget` and exactly two calls were made.
17. With `time_limit=timedelta(seconds=2)`, a first call that takes 1 second and ends with `error_max_budget_usd`, and a resumed call that would wait 60 seconds, `run` returns within 5 seconds with `end_reason` `time_limit`; the resumed call's limit was what was left of the 2 seconds.
18. With `KillPoint.AGENT_RUN` armed, `run` raises `InjectedKill` after the stand-in's writes are on disk, for a completed reply and for a `died` one; without kill points, and with the point unarmed, `run` returns normally and `reached(AGENT_RUN)` counts 1.
19. With `executable="/no/such/claude"`, `run` raises `AgentRuntimeError` whose detail contains that path, and `reached(AGENT_RUN)` is 0.
20. `version()` returns `2.1.289` for a stand-in that prints `2.1.289 (Claude Code)`, also when blank lines come first.
21. `version()` raises `AgentRuntimeError` for a missing executable, for exit status 1, and for a stand-in that prints nothing.
22. Among the modules of `src/factory`, exactly `factory.adapters.git_cli`, `factory.adapters.make_commands` and `factory.adapters.claude_runtime` import `factory.adapters.process`.
23. `ClaudeCodeRuntime` is not a subclass of `AgentRuntime`, and a test module assigns a `ClaudeCodeRuntime` to a variable annotated `AgentRuntime`, so that `make check` (mypy) proves the structural fit.
24. make check stays green.
25. docs: `docs/project-guide.md` describes the `claude -p` runtime (flags, the files under the state directory, the end reasons, the resume and the shared `time_limit`, unknown measures); `docs/operator-guide.md` says that the runtime uses the operator's own `claude` login, which `claude` version is expected (the preflight checks it from F0010) and what a budget stop or a `time_limit` costs (WE6.3).

## Demo

```bash
uv run python -c "
import stat, sys, tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
root = Path(tempfile.mkdtemp())
body = '''import json, sys
if sys.argv[1:] == ['--version']:
    print('2.1.289 (Claude Code)')
else:
    print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'num_turns': 3, 'total_cost_usd': 0.25, 'usage': {'input_tokens': 10, 'output_tokens': 5}, 'permission_denials': [], 'structured_output': {'decision': 'doing', 'entry': 'Done.'}}))
'''
script = root / 'claude'
script.write_text('#!' + sys.executable + chr(10) + body)
script.chmod(0o755)
agent = AgentDefinition(name='coder', model='sonnet', tools=['Read'], budget_usd=Decimal('3'), instructions='Code.')
request = AgentRunRequest(agent=agent, prompt='Stage: doing', allowed_decisions=['review', 'doing', 'question'], time_limit=timedelta(minutes=5), working_directory=root, environment={})
runtime = ClaudeCodeRuntime(str(script), root / 'state')
print(runtime.version())
result = runtime.run(request)
print(result.end_reason, result.decision, result.turns, result.cost_usd, result.tokens.input, result.tokens.output)
"
```
Expect: two lines: `2.1.289`, then `completed doing 3 0.25 10 5`.

```bash
uv run python -c "
from decimal import Decimal
from factory.adapters.claude_runtime import resume_budget
print([str(resume_budget(Decimal(value))) for value in ('4', '3', '2', '1', '2.04')])
"
```
Expect: one line, `['1.00', '0.75', '0.50', '0.50', '0.51']`.

## Log (append only)

1. 2026-10-12 human: created.
