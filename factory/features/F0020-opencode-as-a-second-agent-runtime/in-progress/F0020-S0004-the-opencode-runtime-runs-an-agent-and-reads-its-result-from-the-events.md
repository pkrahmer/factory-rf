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
  started_at: '2026-10-19T04:39:12.058578Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T04:39:12.053294Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T04:39:12.058578Z'
  stage: intake
---

# The opencode runtime runs an agent and reads its result from the events

## Description

This story adds the second implementation of the agent-runtime interface (R12): `OpencodeRuntime` runs an agent as one `opencode run --format json` call and turns the JSON events it prints into the run's result. The agent is the same `AgentDefinition` the Claude Code runtime gets from `claude/agents/*.md`: the runtime writes a configuration file per run, names it in `OPENCODE_CONFIG`, and defines in it one agent whose prompt is the agent file's body, whose tools are the agent file's tools in opencode's names, and whose shell commands are denied by the same patterns as Claude Code's (the `Bash(...)` entries of the installed `settings.json`); the agent files stay the one source of the pipeline's rules. opencode has no structured-output flag, so the runtime appends to the prompt a fixed block the agent must end with, and reads the decision and the entry from that block in the last text, strictly: a missing or malformed block is a run without a usable reply. The cost and the tokens are summed over the `step_finish` events, with the turns, the model time and the refused tool calls. The run starts as every Claude Code run does, through the parts S0002 made shared: the API key from S0001's login shell, `sudo` with `timeout` and `env -i` for the agent user, `factory-confine` with the run's rules, which allow opencode's own folders in the agent's home, and the run's temporary folder. The budget stop and the provider limit come in S0006, a resumed session in S0005, the choice of this runtime by the operator in S0008; until then nothing builds it but the tests.

## Interface

`factory.adapters.opencode_runtime` (`adapters`, new):

```python
CONFIG_VARIABLE = "OPENCODE_CONFIG"
AGENT_PREFIX = "factory-"
RUNTIME_FOLDERS = (".local/share/opencode", ".local/state/opencode", ".cache/opencode")
SWITCHES = {"PYTHONDONTWRITEBYTECODE": "1"}
OPENCODE_TOOLS = ("bash", "edit", "write", "read", "grep", "glob", "list", "patch",
                  "todowrite", "todoread", "webfetch", "task")
TOOL_NAMES = {"Bash": "bash", "Edit": "edit", "Write": "write", "Read": "read", "Grep": "grep",
              "Glob": "glob", "WebFetch": "webfetch", "Task": "task", "TodoWrite": "todowrite"}
RESULT_OPEN = "<factory-result>"
RESULT_CLOSE = "</factory-result>"
DENIAL_PATTERN = re.compile(r"permission|denied", re.IGNORECASE)

def result_instructions(allowed_decisions: Sequence[str]) -> str: ...
def parse_result_block(text: str, allowed_decisions: Sequence[str]) -> tuple[str, str] | None: ...

class OpencodeRuntime(AgentRuntime):
    def __init__(self, executable: str, state_directory: Path, kill_points: KillPoints | None = None, *,
                 models: Mapping[str, str] | None = None, settings_file: Path | None = None,
                 version_time_limit: timedelta = VERSION_TIME_LIMIT, sudo_executable: str = SUDO_EXECUTABLE,
                 api_login_file: Path | None = None, confine_executable: str | None = None,
                 temporary_root: Path | None = None) -> None: ...
    def run(self, request: AgentRunRequest) -> AgentRunResult: ...
    def version(self) -> str: ...
```

The call:

- The words are `[*login_argv(LoginFiles(api=api_login_file)), executable, "run", "--format", "json", "--auto", "--model", <model>, "--agent", f"factory-{agent.name}", request.prompt]`, then through `confined_argv` and `launch` of `agent_launch` (S0002) as the Claude Code runtime's are; started with `run_streaming` (S0003), whose callback here never stops the run, in `request.working_directory`.
- `<model>`: the agent's `model` as it is when it holds a `/`; otherwise `models[model]`. An alias without a mapping raises `AgentRuntimeError` `the opencode runtime has no model for <alias>: set FACTORY_OPENCODE_MODELS`, before any file is written or process started.
- The environment: the request's, without the two login names (`without_login`), with `OPENCODE_CONFIG` naming the run's configuration file and `SWITCHES`; nothing else.
- The run's files, named by a fresh run id (`uuid4`): the configuration `<state>/opencode-<run>.json` and, when confined, the rules `<state>/confine-<run>.json`, both written with mode `0640` before the call and removed after it, whatever the run's end; the temporary folder `temporary_folder(<temporary root>, <run>)`, removed after the call as the run's user with `cleanup_argv`, as the Claude Code runtime does.
- The rules are `run_confinement(request, temporary, runtime_folders=RUNTIME_FOLDERS, devices=existing_devices(DEVICE_FOLDERS, DEVICE_FILES))`: `<HOME>/.config/opencode` is not among them.
- A refused `sudo`, a refusal of the wrapper and a refused login file raise `AgentRuntimeError` with the texts of the Claude Code runtime (`<sudo> refused the agent run: <line>`, `<wrapper> refused the agent run: <line>`, `login_refusal`), when the call printed no event that validates.
- The result's `login` is `login_used(stderr)`; `None` without an API login file.
- After the run, the kill point `AGENT_RUN` is reached, as by the Claude Code runtime.
- The module reads no `os.environ`.

The configuration file: one JSON object with exactly these keys:

```json
{"autoupdate": false, "share": "disabled", "snapshot": false,
 "agent": {"factory-<name>": {"mode": "primary", "prompt": "<instructions>\n\n<result instructions>",
                              "tools": {"<each of OPENCODE_TOOLS>": true | false},
                              "permission": {"edit": "allow", "bash": {"*": "allow", "<pattern>": "deny"}}}}}
```

- `prompt`: the agent's instructions, a blank line, then `result_instructions(request.allowed_decisions)`.
- `tools`: every name of `OPENCODE_TOOLS`, `true` exactly for the agent's tools mapped through `TOOL_NAMES`. A tool outside `TOOL_NAMES` raises `AgentRuntimeError` `the opencode runtime has no tool for <tool>` before anything starts.
- `permission.bash`: `"*": "allow"` first, then `"<pattern>": "deny"` for every entry `Bash(<pattern>)` of the list `permissions.deny` in `settings_file`, in its order; other entries are ignored. Without a settings file, `{"*": "allow"}` alone. A settings file that cannot be read raises `AgentRuntimeError` `cannot read the agent settings <path>: <error>`; one that is no JSON object with a list of strings at `permissions.deny` raises `the agent settings <path> hold no permissions.deny list`; both before anything starts.

The result block:

- `result_instructions(["doing", "question"])` is exactly:

  ```text
  End your final message with this block, and nothing after it:
  <factory-result>
  decision: <one of: doing, question>
  entry:
  <your journal entry, without its number or your name: everything your instructions say the entry contains>
  </factory-result>
  ```

  (the placeholder in the entry's line is `ENTRY_DESCRIPTION` of `agent_launch`).
- `parse_result_block(text, allowed)`: the text, with trailing whitespace removed, must end with the line `</factory-result>`; the block opens at the last line `<factory-result>` before it; its first line is `decision: <word>` and its second `entry:`; the entry is the rest up to the closing line, stripped. It gives `(decision, entry)`, or `None` when the closing line does not end the text, no opening line precedes it, the decision line or the `entry:` line is missing, the decision is not one of `allowed`, or the entry is blank. Text before the block is ignored.

The events (one JSON object per line of standard output, as opencode 1.19.3 printed them in the probe and the stand-ins play them; every other line, an object without a string `type`, an unknown `type` and a line that does not validate are skipped):

```json
{"type": "step_start", "timestamp": 1000, "sessionID": "ses_a", "part": {"type": "step-start"}}
{"type": "tool_use", "timestamp": 1500, "sessionID": "ses_a", "part": {"type": "tool", "tool": "bash",
  "state": {"status": "error", "input": {"command": "git push"}, "error": "...", "time": {"start": 1200, "end": 1700}}}}
{"type": "text", "timestamp": 1900, "sessionID": "ses_a", "part": {"type": "text", "text": "..."}}
{"type": "step_finish", "timestamp": 2000, "sessionID": "ses_a", "part": {"type": "step-finish", "cost": 0.012,
  "tokens": {"input": 10, "output": 5, "reasoning": 2, "cache": {"read": 100, "write": 20}}}}
{"type": "error", "timestamp": 2100, "sessionID": "ses_a", "error": {"name": "APIError", "data": {"message": "...", "statusCode": 428}}}
```

- The models that read them are private, frozen and `extra="ignore"`: `_Event`, `_Part`, `_Tokens`, `_CacheTokens`, `_ToolState`, `_Span`, `_Error` and `_ErrorData` (the last two read the `error` event, which S0006 acts on). Timestamps, counts and costs are non-negative; a negative one fails the line's validation. A `step_finish` needs `cost` and `tokens` with `input` and `output`; `reasoning`, `cache` and the cache's `read` and `write` count 0 when absent.
- `cost_usd`: the sum of the `step_finish` costs (`Decimal(str(cost))` each); `tokens`: `input` the sum of the inputs, `output` the sum of output plus reasoning, `cache_read` and `cache_creation` the sums of the cache reads and writes; `turns`: the number of `step_finish` events. All three are `None` when there is none.
- `model_duration`: for each `step_finish`, its timestamp less that of the last `step_start` before it, less the spans (`end - start`) of the `tool_use` events between the two, at least zero; the sum over the steps; `None` when there is no `step_finish`.
- `permission_denials`: one `PermissionDenial(tool=<part.tool>, detail=json.dumps(<state.input>, sort_keys=True), path=<the path>)` per `tool_use` event with `status` `error` whose error matches `DENIAL_PATTERN`, in order.
- `PermissionDenial.path` (F0021-S0004) is the file the refused call named: the string at the key `filePath` of `<state.input>` when `<state.input>` is an object and that value is a string, else `None`. `filePath` is the key of opencode's own file tools (`write` and `edit`, as 1.19.3 names them; the stand-ins play it and the hand probe of change 6 confirms it against the real events), not Claude Code's `file_path`; a refused `bash` call, whose input names a `command` and no file, has no `path`, and no other key is read. So the run's cost record carries `denied_paths` for the files an opencode run was refused.
- The decision and the entry: `parse_result_block` of the last `text` event's text.
- The end reason: `time_limit` when the call reached its time limit (then the result has no measures, R24); `died` when it exited non-zero or printed no `step_finish`; `no_result` when the block gives nothing; `completed` otherwise. Every end but `time_limit` keeps the measures.

`version()`: the first word of `<executable> --version`, called without login words within `version_time_limit`; a call that cannot start, fails, reaches the limit or prints nothing raises `AgentRuntimeError` with the Claude Code runtime's texts.

Tests (the tester writes them): `tests/adapters/opencode_stand_in.py` (new support module: `write_opencode(directory, steps)`, which writes a stand-in that plays `Step`s and records its calls like `tests/adapters/claude_stand_in.py`, reusing that module's `Step`, `StandInCall` and `read_calls` by import, and that also records the text of the file `OPENCODE_CONFIG` names; and one builder per event above, each returning the event's JSON line, for this story's tests and S0005 to S0007's), `tests/adapters/test_opencode_runtime.py` (the call, the configuration, the files), `tests/adapters/test_opencode_result_block.py`, `tests/adapters/test_opencode_events.py` (the measures and the end reasons), `tests/test_opencode_runtime_search.py` (with `tests/source_search.py`: neither `factory.adapters.opencode_runtime` nor `factory.adapters.agent_launch` reads `os.environ`), `tests/adapters/test_opencode_runtime_launch.py` (the agent user through `_write_sudo` and `_sudo_calls` of `tests/adapters/test_claude_runtime_os_user.py`, the wrapper through `build_layout`, `write_confine` and `read_records` of `tests/confine_support.py`, the API key; all imported, none copied).

Changed under the feature's decision 19, by the tester only, nothing else in those modules: `tests/test_wrapper_search.py`, the test `test_only_the_three_wrappers_import_the_process_module`, whose expected importers gain `factory.adapters.opencode_runtime`; `tests/test_model_configuration.py`, the list `EXCEPTIONS`, which gains `factory.adapters.opencode_runtime._Event`, `._Part`, `._Tokens`, `._CacheTokens`, `._ToolState`, `._Span`, `._Error` and `._ErrorData`.

## Acceptance criteria

1. A run of agent `coder` (model `sonnet`, mapped to `anthropic/claude-sonnet-5-5`) with the prompt `Stage: doing` calls the stand-in with exactly `run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder Stage: doing` (the prompt one argument), in the request's working directory; a model `openai/gpt-5` is passed as it is (rows).
2. An alias without a mapping, a tool outside `TOOL_NAMES`, a settings file that is missing, one that is no JSON and one without a `permissions.deny` list each raise `AgentRuntimeError` with its text above; the stand-in is never called and the state directory holds no file (rows).
3. The configuration the stand-in reads is the JSON object above: `autoupdate` false, `share` `disabled`, `snapshot` false, one agent `factory-coder` of mode `primary`, its prompt the instructions, a blank line and the result instructions, `tools` true for `read` and `bash` and false for the other ten when the agent's tools are `Read` and `Bash`, and `permission` `{"edit": "allow", "bash": {"*": "allow", "git push*": "deny", "rm -rf *": "deny"}}` for a settings file whose `deny` list is `["Bash(git push*)", "Read(.env)", "Bash(rm -rf *)"]`; without a settings file, `bash` is `{"*": "allow"}` (rows).
4. The stand-in sees `OPENCODE_CONFIG` naming `<state>/opencode-<run>.json` with mode `0640`, and an environment of exactly the request's names without `ANTHROPIC_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN`, plus `OPENCODE_CONFIG` and `PYTHONDONTWRITEBYTECODE`; after a completed, a died and a timed-out run the state directory holds no file (rows).
5. `result_instructions(["doing", "question"])` is the text above, exactly.
6. `parse_result_block` gives `("doing", "Built it.")` for a text that ends with a valid block, also with text before it, with trailing spaces and line feeds after the closing line, and with spaces around the decision word; it gives the later block of two; it gives `None` for text after the closing line, a missing closing line, a missing opening line, a missing `decision:` line, a missing `entry:` line, the two lines in the other order, a decision outside the allowed ones and a blank entry (rows of one parametrized test).
7. Two steps with costs 0.012 and 0.03, inputs 10 and 20, outputs 5 and 6, reasoning 2 and 0, cache reads 100 and 0 and writes 20 and 5 give `cost_usd` `Decimal("0.042")`, tokens input 30, output 13, cache read 100, cache creation 25, and `turns` 2; a step without `reasoning` and without `cache` counts 0 for each (rows).
8. A step from 1000 to 2000 ms with a tool call from 1200 to 1700 ms, and a step from 3000 to 3400 ms without one, give a model time of 0.9 seconds; a step whose tool spans exceed it counts zero (rows).
9. A `tool_use` error `permission denied by rule git push*` and one `Denied: rm -rf *` are refused calls with the tool and the sorted input; an error `file not found` and a completed call are none (rows).
10. A refused `write` call whose input is `{"filePath": "/work/src/a.py", "content": "x"}` gives a denial with `path` `/work/src/a.py`, and so does a refused `edit` call with `filePath`; a refused `bash` call, one whose input is no object, one whose `filePath` is no string, and one whose input names only `file_path` give a denial with `path` `None`; a result with two refused calls on the same file records it once in `denied_paths` of its cost record (`CostRecorder.complete`) (rows).
11. Lines that are no JSON, an object without `type`, an unknown type, a `step_finish` with a negative cost and a `step_finish` without `cost` are skipped: the measures are those of the valid lines alone (rows).
12. The end reasons (rows): a valid block and exit 0 is `completed` with the block's decision and entry; a block naming `review` when only `doing` and `question` are allowed is `no_result` with its measures; a valid block and exit 1 is `died` with its measures; no `step_finish` is `died` with no measures; a stand-in that prints one step and waits 30 seconds under a time limit of 3 seconds is `time_limit` without measures, and the call returns within 20 seconds.
13. With an agent user, the stand-in `sudo` sees `-n -u agent -- timeout --signal=KILL <limit>s env -i` and the environment's assignments, `OPENCODE_CONFIG` among them, before the stand-in's words; a refusal `sudo: a password is required` raises `AgentRuntimeError` `<sudo> refused the agent run: sudo: a password is required` (rows).
14. Through a stand-in wrapper, the call starts as `<wrapper> --rules <state>/confine-<run>.json -- ...`; the rules allow `<HOME>/.local/share/opencode`, `<HOME>/.local/state/opencode` and `<HOME>/.cache/opencode` as folders and nothing under `<HOME>/.config`; the run's temporary folder is gone after the run; a wrapper line `factory-confine: ...` without events raises `AgentRuntimeError` naming it (rows).
15. With an API login file holding a key, the stand-in sees `ANTHROPIC_API_KEY` with the key and the result's `login` is `api_key`; with an empty file it sees no such name and `login` is `none`; without the file, no login words and `login` `None`; an API file that is a folder raises `AgentRuntimeError` `agent runtime failed: cannot read the agent's API login file <path>: cannot be read` and the stand-in is never called; the key stands in no argument, no configuration file and not in the result's JSON (rows).
16. `version()` gives `1.19.3` for `1.19.3\n`; a stand-in that exits 1, prints nothing or waits past a limit of 3 seconds raises `AgentRuntimeError` (rows).
17. The kill point `AGENT_RUN` is reached once after a run, `OpencodeRuntime` is an `AgentRuntime`, and the module reads no `os.environ` (a source search, which finds it in a snippet that does).
18. `make check` stays green.
19. docs: `docs/project-guide.md`: a section *The opencode runtime*: the call and its words, the per-run configuration and why it is generated from the agent files and `settings.json`, the result block and its strict parsing, the events and the measures read from them, opencode's own folders in the agent's home and the folder it may not write. `docs/decisions.md`: an entry *opencode's agent is generated per run from the shipped agent files* with the reasons of the feature's decisions 6, 7, 8 and 10, dated with the story.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir "$d/work"
cat > "$d/opencode" <<'EOF'
#!/bin/sh
here=$(dirname "$0")
printf '%s\n' "$*" > "$here/arguments"
cp "$OPENCODE_CONFIG" "$here/config.json"
cat <<'LINES'
{"type":"step_start","timestamp":1000,"sessionID":"ses_smoke","part":{"type":"step-start"}}
{"type":"tool_use","timestamp":1500,"sessionID":"ses_smoke","part":{"type":"tool","tool":"bash","state":{"status":"error","input":{"command":"git push"},"error":"permission denied by rule git push*","time":{"start":1200,"end":1700}}}}
{"type":"text","timestamp":1900,"sessionID":"ses_smoke","part":{"type":"text","text":"Done.\n<factory-result>\ndecision: question\nentry:\nThe smoke entry.\n</factory-result>"}}
{"type":"step_finish","timestamp":2000,"sessionID":"ses_smoke","part":{"type":"step-finish","reason":"stop","cost":0.012,"tokens":{"input":10,"output":5,"reasoning":2,"cache":{"read":100,"write":20}}}}
LINES
EOF
chmod +x "$d/opencode"
uv run -q python - "$d" <<'EOF'
import json
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest

d = Path(sys.argv[1])
agent = AgentDefinition(name="coder", model="sonnet", tools=["Read", "Bash"], budget_usd=Decimal("1"), instructions="Smoke.")
request = AgentRunRequest(agent=agent, prompt="Smoke.", allowed_decisions=["question"], time_limit=timedelta(seconds=60), working_directory=d / "work", environment={"PATH": "/usr/bin:/bin"})
result = OpencodeRuntime(str(d / "opencode"), d / "state", models={"sonnet": "anthropic/claude-sonnet-5-5"}).run(request)
tokens = result.tokens
print(result.end_reason, result.decision, result.entry)
print(result.cost_usd, result.turns, tokens.input, tokens.output, tokens.cache_read, tokens.cache_creation, result.model_duration.total_seconds())
print([denial.tool for denial in result.permission_denials])
config = json.loads((d / "config.json").read_text(encoding="utf-8"))
agent_config = config["agent"]["factory-coder"]
print(config["snapshot"], config["share"], sorted(name for name, on in agent_config["tools"].items() if on))
print(sorted(path.name for path in (d / "state").iterdir()))
EOF
cat "$d/arguments"
```
Expect: six lines, `completed question The smoke entry.`, `0.012 1 10 7 100 20 0.5`, `['bash']`, `False disabled ['bash', 'read']`, `[]`, `run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder Smoke.`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
