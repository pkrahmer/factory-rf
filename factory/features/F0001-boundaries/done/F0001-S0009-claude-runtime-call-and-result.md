---
stage: done
pr: 9
blocked: null
comments_seen: 2
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
20. A reply whose `usage` has only `input_tokens` 10 and `output_tokens` 5 gives `tokens` with those two counts and cache-read and cache-creation counts of 0.
21. A permission denial whose `tool_input` is `{"b": 1, "a": 2}` has the detail `{"a": 2, "b": 1}`.
22. make check stays green.
23. docs: `docs/project-guide.md` describes the `claude -p` runtime so far (the flags, the files under the state directory, the environment with no inherited variable and no added `PATH`, the end reasons, unknown measures); `docs/operator-guide.md` says that the runtime uses the operator's own `claude` login and that the flags are v1's, to be checked against the pinned version (WE6.3).

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
2. intake: Intake checked S0009 and cannot accept it yet. The format check passed. The Interface, the Demo, the architecture and the scope are fine. Two behaviours stated in the Interface have no criterion that tests them:

   1. The Interface says `tokens` is known when `input_tokens` and `output_tokens` are both present, "the cache counts default to 0". Criterion 8 gives all four counts. Criterion 10 only covers `tokens` being `None`. Nothing tests a `usage` with just input and output tokens, which should give cache counts of 0. Two coders could read the default two ways, for example `None` or a missing count, and both would pass. Proposal: add a criterion, before the two closing ones, saying that a reply whose `usage` has only `input_tokens` 10 and `output_tokens` 5 gives `tokens` with those two counts and cache-read and cache-creation counts of 0. I would choose this.

   2. The Interface says a denial's detail is `json.dumps(tool_input, sort_keys=True)`. Criterion 8 uses a one-key input, so the sorting is never tested. Proposal: add a criterion, or extend criterion 8, so the denial's `tool_input` has two keys in non-alphabetical order (for example `{"b": 1, "a": 2}`) and the detail is `{"a": 2, "b": 1}`. I would choose this.

   Please answer, or say that I should write both criteria as proposed.
3. human (pull request comment, 2026-10-13): Write both criteria as proposed, before the two closing ones: (1) a reply whose `usage` has only `input_tokens` 10 and `output_tokens` 5 gives `tokens` with those two counts and cache-read and cache-creation counts of 0; (2) a denial whose `tool_input` is `{"b": 1, "a": 2}` has the detail `{"a": 2, "b": 1}`. Both close a behaviour the Interface already states.
4. intake: accepted. Checked again with the human's answer (log entry 3), which settles both questions of entry 2. I wrote exactly what that answer says, as new criteria 20 and 21 before the two closing ones. The old 20 and 21 are now 22 (`make check`) and 23 (`docs:`). The Assignment's meaning is unchanged, so I did not rewrite it.
   - Interface: names concrete modules and signatures (`ClaudeCodeRuntime`, `ENTRY_DESCRIPTION`, the argument list, the files, the schema). Every behaviour it states now has a criterion. The cache counts defaulting to 0 is the new criterion 20. The sorted-JSON denial detail is the new criterion 21.
   - Criteria: each can be tested by one test function. Every rule has a failing side: `died` and `no_result` (11, 12, 13), a missing executable (17), an unwritable state directory (18), `time_limit` (14), and files removed after a kill or an error (7).
   - Demo: runnable with stand-in scripts written to a temp directory. Its `Expect:` line gives two exact output lines that can be checked.
   - Architecture: the runtime sits in `factory.adapters`. The only process starter it imports is `factory.adapters.process`, and criterion 19 checks that.
   - Scope: within F0001's agent-runtime scope. The budget resume and the version query are left to S0010. The guard hook command is left to F0004, and the environment scrubbing and OS user to F0010. All of these are in the feature's "Out of scope".
5. tester: I wrote red tests for every criterion of the `claude -p` runtime. They use a stand-in executable; the real `claude` is never run.

   Criterion → test:
   - criterion 1: tests/adapters/test_claude_runtime.py::test_call_passes_every_flag_in_order
   - criterion 2: tests/adapters/test_claude_runtime.py::test_call_without_effort_guard_or_tools_leaves_those_flags_out
   - criterion 3: tests/adapters/test_claude_runtime.py::test_json_schema_asks_for_an_allowed_decision_and_an_entry
   - criterion 4: tests/adapters/test_claude_runtime.py::test_call_runs_in_the_requests_working_directory
   - criterion 5: tests/adapters/test_claude_runtime.py::test_call_gets_only_the_requests_environment_and_the_switches
   - criterion 6: tests/adapters/test_claude_runtime.py::test_call_sees_instructions_guard_and_hooks_files (parametrized over a state directory with and without a space)
   - criterion 7: tests/adapters/test_claude_runtime.py::test_run_files_are_removed_after_a_result, ::test_run_files_are_removed_after_an_injected_kill, ::test_run_files_are_removed_after_a_missing_executable
   - criterion 8: tests/adapters/test_claude_runtime.py::test_success_reply_gives_decision_entry_and_measures
   - criterion 9: tests/adapters/test_claude_runtime.py::test_duration_is_measured_by_the_factory
   - criterion 10: tests/adapters/test_claude_runtime.py::test_measures_missing_from_the_reply_are_unknown, ::test_usage_with_input_tokens_only_gives_unknown_tokens
   - criterion 11: tests/adapters/test_claude_runtime.py::test_reply_without_a_usable_decision_is_no_result (parametrized: no structured_output, decision not allowed, blank entry)
   - criterion 12: tests/adapters/test_claude_runtime.py::test_failed_call_died (exit status 1, not JSON), ::test_error_reply_died_with_its_cost
   - criterion 13: tests/adapters/test_claude_runtime.py::test_reply_without_a_required_field_died (parametrized: subtype, is_error)
   - criterion 14: tests/adapters/test_claude_runtime.py::test_call_over_its_time_limit_is_killed_with_unknown_measures
   - criterion 15: tests/adapters/test_claude_runtime.py::test_armed_kill_point_fires_after_the_calls_writes (parametrized: completed, died)
   - criterion 16: tests/adapters/test_claude_runtime.py::test_unarmed_kill_point_is_reached_once
   - criterion 17: tests/adapters/test_claude_runtime.py::test_missing_executable_is_a_runtime_error
   - criterion 18: tests/adapters/test_claude_runtime.py::test_unwritable_state_directory_is_a_runtime_error (checks that the detail contains `str(state_directory)`)
   - criterion 19: tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module
   - criterion 20: tests/adapters/test_claude_runtime.py::test_cache_counts_default_to_zero
   - criterion 21: tests/adapters/test_claude_runtime.py::test_denial_detail_is_json_with_sorted_keys
   - criteria 22 and 23: the factory's check and the documenter stage; no test.

   Files I created:
   - tests/adapters/claude_stand_in.py: `write_stand_in(directory, steps)`, `read_calls(directory)`, and the Pydantic models `Step` (writes, wait_seconds, stdout, stderr, exit_status) and `StandInCall` (arguments, environment, working_directory, files). The stand-in records each call to `calls.jsonl` before it plays its step. The recorded files are every file named in the arguments, plus the guard file named after `--settings` inside the hooks file's command.
   - tests/adapters/test_claude_runtime.py
   - tests/test_wrapper_search.py

   Red as intended: `make test` stops at collection with `ModuleNotFoundError: No module named 'factory.adapters.claude_runtime'`. That is the only module the runner could not import. Once the module exists, test_wrapper_search fails on a wrong result until claude_runtime imports `factory.adapters.process`. `make lint` is green.

   A choice the coder should know about: the leftover-file checks look for files matching `instructions-*.md`, `guard-*.json` and `hooks-*.json` in the state directory. They do not require the directory to be empty.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
6. coder: I built `ClaudeCodeRuntime.run` and `ENTRY_DESCRIPTION` in src/factory/adapters/claude_runtime.py (commit 68ce293), then a refactor in a5d1c80. All the tester's tests pass without changes, `make check` is green (coverage 99.77 %), and the Demo prints exactly the two expected lines.

   What it does:
   - `run` turns the request into the Interface's argument list, in its order, and writes the run files: `instructions-<session>.md`, plus `guard-<session>.json` and `hooks-<session>.json` when there is a guard.
   - It calls `run_process` with `{**request.environment, **SWITCHES}`, so no `PATH` is added and nothing is inherited.
   - It parses the reply through private Pydantic models (`_Reply`, `_Usage`, `_Denial`, `_StructuredOutput`). Unknown fields are ignored and `is_error` must be a real boolean. `total_cost_usd` is read as a float and turned into `Decimal(str(value))`.
   - The end reason is decided in `_end_reason` in this order: `time_limit`, then `died`, then `no_result`, then `completed`.
   - Measures are `None` when the output does not parse as a reply or when the call was ended by the time limit. `duration` is measured with `time.monotonic` from the start of `run`.
   - `KillPoint.AGENT_RUN` is reached after the result is built. A `finally` removes the run files.

   Main design decision: `run` creates the state directory before the `try`/`finally` that removes the files, not inside it. If the directory cannot be created (the state directory sits below a regular file), the cleanup has nothing to remove. If the cleanup ran there, `unlink` would raise `NotADirectoryError` and hide the `AgentRuntimeError`. I rejected the other fix, wrapping the removal in `suppress(OSError)`, because it would hide real cleanup failures too.

   Also rejected: reading the reply with `json.loads` into a dict. The architecture asks for DTOs, so the reply goes through private models instead.

   Refactor (a5d1c80): the two state-directory errors now share `_state_error`, and I removed the docstrings on the private classes, as the docstring rule asks.

   Noticed but not touched:
   - A reply whose optional fields have the wrong type (for example `num_turns` as a string) fails validation as a whole. The run then counts as `died` with unknown measures, because the Interface counts "not a JSON object with `subtype` and `is_error`" as died.
   - `ClaudeCodeRuntime` does not yet satisfy the `AgentRuntime` protocol. `version` comes with S0010, as the Assignment says.
   - Docs (criterion 23) are left to the documenter.

   `make check`: check: green
7. reviewer: no findings.

   What I checked, group by group:
   - Acceptance criteria: each of criteria 1–21 has a test in the tester's mapping (entry 5), and I read each test against its criterion. The failing sides are tested:
     - `died`: exit status 1, output that is not JSON, `is_error` true, `subtype` missing, `is_error` missing.
     - `no_result`: no `structured_output`, a decision that is not allowed, a blank entry.
     - Unknown measures: no measure fields at all, `input_tokens` only, and a timed-out call.
     - Errors: a missing executable, and a state directory below a regular file.
     - Leftover files: none after a result, after `InjectedKill`, or after an `AgentRuntimeError`.
     - Kill point: reached for a completed run and for a died one.
     - Shell quoting: a guard path with a space and one without.
     The coder's entry says the factory's `make check` was green after their work.
   - Architecture: `src/factory/adapters/claude_runtime.py` imports only `factory.domain` and `factory.adapters.process`. It starts its process only through `run_process`, and `tests/test_wrapper_search.py` confirms the three wrappers are the only importers. The reply is read through private Pydantic models, so no `dict[str, Any]` crosses a function boundary.
   - Security: no shell is used. The guard path in the hook command is shell-quoted with `shlex.quote`. The environment is exactly `request.environment` plus the three switches, with nothing inherited. The diff adds no `noqa`, `nosec`, `nosemgrep` or baseline entry, and no secrets.
   - Quality: names are clear and each function does one thing. Docstrings are on the module and on the public class and its methods, not on private names. Comments explain why (the switches, the float-to-`Decimal` reading, why a timed-out call's output is not used as its measure). Creating the state directory before the `try`/`finally` is correct. It keeps the cleanup from hiding the `AgentRuntimeError` for an unwritable directory.
   - Ticket hygiene: the coder's entry explains the main decision and what was rejected (`suppress(OSError)`, and reading the reply with `json.loads` into a dict). The Assignment matches what was built, a single call with the resume and `version` left to S0010. Criterion 23 still describes what the documenter has to write.

   Open, not a finding: the reply models do not require non-negative numbers. A `claude` reply with a negative `num_turns` or token count would fail when the `AgentRunResult` or `TokenCounts` is built, and `run` would raise a raw `ValidationError` instead of returning `died`. The Interface does not cover this input, and the real tool does not produce it. It could be tightened together with S0010's work on the reply.
8. documenter: I wrote the `claude -p` runtime documentation (criterion 23). `make check` is green. I found nothing in the code that contradicts the Interface, so there are no findings.

   Files changed:
   - `docs/project-guide.md`: new section "The `claude -p` runtime" under *The agent runtime*. It covers:
     - the flags in order, and when `--effort` and `--settings` are left out;
     - the files under the state directory and when they are removed;
     - the environment: nothing inherited, no `PATH` added, `factory-guard` found only through the request's `PATH`;
     - the end-reason rules;
     - unknown measures, the cache counts defaulting to 0, and the sorted-key denial detail;
     - the kill point and the two `AgentRuntimeError` cases;
     - the stand-in tests.
     I also changed the sentence that said the implementation "follows in later stories".
   - `docs/operator-guide.md`: new section "The agent runtime". It says the runtime uses the operator's own `claude` login and holds no API key, and that the flags are v1's and not yet checked against the pinned version (WE6.3). It also says that a died, timed-out or no-result run is a stall, and that the cost and tokens of a timed-out run are shown as unknown.
   - `README.md`: the status sentence now mentions the first half of the `claude -p` runtime.

   Cross-read and found current: *Starting a process* (it already names the three wrappers), the kill-point table (`AGENT_RUN` is already listed for the two runtimes), the errors section, `docs/decisions.md`, and `src/factory/adapters/claude_runtime.py` against the Interface. I did not run any new example: I added no runnable code, only an argument layout. The coder already ran the story's Demo.

   Stale but unrelated, left alone: nothing seen.

   One point for later, not a finding: the reviewer noted that a reply with a negative number would raise a raw `ValidationError` instead of returning `died`. I left it out of the docs because the Interface does not cover it, and S0010 can tighten it.

   `make check`: check: green
9. demo: I ran the one Demo command from the repository root, exactly as written. It matched its `Expect:` line, so there are no findings.

   Command 1 (the `uv run python -c` script: two stand-in executables, `good` and `bad`, each run through `ClaudeCodeRuntime(...).run` with an empty environment):

   ```text
   good completed doing 3 0.25 (10, 5)
   bad died None None None None
   ```

   Exit status 0. This met the `Expect:` line: the two lines are exactly `good completed doing 3 0.25 (10, 5)` and then `bad died None None None None`.

   Checked against the acceptance criteria:
   - No criterion is contradicted.
   - The `good` reply has a valid `structured_output`. It gives `completed` with the decision, `turns` 3, `cost_usd` 0.25 as a `Decimal`, and the input and output tokens (criteria 8 and 20). The demo prints only input and output, so the cache counts of 0 are not shown.
   - The output that is not JSON gives `died`, with every measure `None` rather than 0 (criteria 10 and 12).
   - Both stand-ins ran under an empty request environment, so no `PATH` was given, and the shebang's absolute interpreter path still started them (criterion 5).
   - The other criteria (flags, files, time limit, kill point, errors) are outside what this command exercises. The tests cover them, as the earlier entries say.
10. done (pull request merged); cost: 7 runs, 6.5 min, 50 turns, 178k tokens in (924k more from cache), 35k out, $2.02
