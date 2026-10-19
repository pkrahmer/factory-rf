---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 251
comments_read: [6259811093, 6259973629, 6260061257]
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-19T05:20:51.457424Z'
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
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-19T04:39:38.517187Z'
  stage: intake
  run: 5f835af96aea46b2943097666c68d747
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-19T04:41:57.255889Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-19T04:42:14.852550Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-19T04:42:35.507885Z'
  stage: intake
  run: 81e36e6f3fed4c91b6bf302fd542e530
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-19T04:42:55.866030Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-19T04:49:19.475246Z'
  stage: tests
  run: c87e26bb2e344fabaea4a7b6f0a56994
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-19T04:49:39.935705Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-10-19T04:54:30.355887Z'
  stage: doing
  run: ac22a570d30c4544a587165d9b406023
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-10-19T04:55:46.723662Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T04:56:04.376420Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-10-19T04:56:27.696241Z'
  stage: doing
  run: cb69f9748f684748a10c5733253bb31c
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-19T04:56:48.036135Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-10-19T04:58:32.190684Z'
  stage: tests
  run: 108e574eb374401489989af7f5696cde
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-19T04:58:52.107502Z'
  stage: doing
- number: 17
  speaker: coder
  kind: question
  at: '2026-10-19T05:00:28.736833Z'
  stage: doing
  run: bb075045ead94cb1acaeac4ef0535430
  blocked: question
- number: 18
  speaker: human
  kind: comment
  at: '2026-10-19T05:04:51.128229Z'
  stage: doing
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-19T05:05:09.026289Z'
  stage: doing
- number: 20
  speaker: coder
  kind: result
  at: '2026-10-19T05:07:02.417045Z'
  stage: doing
  run: 3208ffcbb2bd4b9fadae1298a6a8bf64
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-19T05:07:22.444491Z'
  stage: review
- number: 22
  speaker: reviewer
  kind: result
  at: '2026-10-19T05:09:41.141306Z'
  stage: review
  run: d7065fff3f6c40b59d4c2c57fe0de3c7
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-19T05:10:01.637468Z'
  stage: doing
- number: 24
  speaker: coder
  kind: result
  at: '2026-10-19T05:17:28.244557Z'
  stage: doing
  run: dc6e66f97146489eaa37833f837d2826
- number: 25
  speaker: factory
  kind: started
  at: '2026-10-19T05:17:48.908099Z'
  stage: tests
- number: 26
  speaker: tester
  kind: result
  at: '2026-10-19T05:20:31.438504Z'
  stage: tests
  run: 3a34411588de4dd68bb1ef8ff67962b6
- number: 27
  speaker: factory
  kind: started
  at: '2026-10-19T05:20:51.457424Z'
  stage: doing
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
8. A step from 1000 to 2000 ms with a tool call from 1200 to 1700 ms, and a step from 3000 to 3400 ms without one, give a model time of 0.9 seconds; a step whose tool spans exceed it counts zero; a `step_finish` with no earlier `step_start` adds 0 to the model time and still counts as a turn; the tool calls "between" a step's start and finish are those by line order (rows).
9. A `tool_use` error `permission denied by rule git push*` and one `Denied: rm -rf *` are refused calls with the tool and the sorted input; an error `file not found` and a completed call are none (rows).
10. A refused `write` call whose input is `{"filePath": "/work/src/a.py", "content": "x"}` gives a denial with `path` `/work/src/a.py`, and so does a refused `edit` call with `filePath`; a refused `bash` call, one whose input is no object, one whose `filePath` is no string, and one whose input names only `file_path` give a denial with `path` `None`; a result with two refused calls on the same file records it once in `denied_paths` of its cost record (`CostRecorder.complete`) (rows).
11. Lines that are no JSON, an object without `type`, an unknown type, a `step_finish` with a negative cost, a `step_finish` without `cost`, one with a negative `timestamp`, one with a negative `input`, one without `tokens` and one whose `tokens` lack `output` are skipped: the measures are those of the valid lines alone (rows).
12. The end reasons (rows): a valid block and exit 0 is `completed` with the block's decision and entry; a block naming `review` when only `doing` and `question` are allowed is `no_result` with its measures; a valid block and exit 1 is `died` with its measures; no `step_finish` is `died` with no measures; a stand-in that prints one step and waits 30 seconds under a time limit of 3 seconds is `time_limit` without measures, and the call returns within 20 seconds.
13. With an agent user, the stand-in `sudo` sees `-n -u agent -- timeout --signal=KILL <limit>s env -i` and the environment's assignments, `OPENCODE_CONFIG` among them, before the stand-in's words; a refusal `sudo: a password is required` raises `AgentRuntimeError` `<sudo> refused the agent run: sudo: a password is required` (rows).
14. Through a stand-in wrapper, the call starts as `<wrapper> --rules <state>/confine-<run>.json -- ...`, the rules file having mode `0640`; the rules allow `<HOME>/.local/share/opencode`, `<HOME>/.local/state/opencode` and `<HOME>/.cache/opencode` as folders and nothing under `<HOME>/.config`; the run's temporary folder is gone after the run; a wrapper line `factory-confine: ...` without events raises `AgentRuntimeError` naming it (rows).
15. With an API login file holding a key, the stand-in sees `ANTHROPIC_API_KEY` with the key and the result's `login` is `api_key`; with an empty file it sees no such name and `login` is `none`; without the file, no login words and `login` `None`; an API file that is a folder raises `AgentRuntimeError` `agent runtime failed: cannot read the agent's API login file <path>: cannot be read` and the stand-in is never called; the key stands in no argument, no configuration file and not in the result's JSON (rows).
16. `version()` gives `1.19.3` for `1.19.3\n`, and the stand-in's recorded call is `<executable> --version` alone, without login words, also when an API login file is set; a stand-in that exits 1, prints nothing or waits past a limit of 3 seconds raises `AgentRuntimeError` (rows).
17. The kill point `AGENT_RUN` is reached once after a run, `OpencodeRuntime` is an `AgentRuntime`, and the module reads no `os.environ` (a source search, which finds it in a snippet that does).
18. The errors carry the Claude Code runtime's texts (rows): `version()` of an executable that exits 1 raises `<executable> --version failed: <stderr>`, of one that prints nothing `<executable> --version printed nothing`, and of one that does not exist `cannot start <executable>: <error>`; a run whose executable does not exist raises `cannot start <executable>: <error>` and leaves the state directory without a file; a run whose state directory does not exist raises `cannot write the state directory <path>: <error>` and the stand-in is never called.
19. The non-negative limits are tested on the accepted side too: a `step_finish` with cost 0, `input` 0 and timestamp 0, after a `step_start` at timestamp 0, is a valid step that counts as a turn, with `cost_usd` `Decimal("0")`, tokens input 0 and a model time of 0 seconds (rows beside the negative ones of criterion 11).
20. `make check` stays green.
21. docs: `docs/project-guide.md`: a section *The opencode runtime*: the call and its words, the per-run configuration and why it is generated from the agent files and `settings.json`, the result block and its strict parsing, the events and the measures read from them, opencode's own folders in the agent's home and the folder it may not write. `docs/decisions.md`: an entry *opencode's agent is generated per run from the shipped agent files* with the reasons of the feature's decisions 6, 7, 8 and 10, dated with the story.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir "$d/work" "$d/state"
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
3. intake: Questions (the format check passed; the architecture and scope are fine: the new module sits in `adapters`, change 2 of CLAUDE.md and change 7 of pyproject.toml are in place, and every item is within the feature's Scope for S0004):

   1. Interface, the event models: "Timestamps, counts and costs are non-negative; a negative one fails the line's validation", and "a `step_finish` needs `cost` and `tokens` with `input` and `output`". Criterion 11 tests only a negative cost and a missing cost. Nothing tests a negative timestamp, a negative token count (input, output, reasoning, cache read, cache write), a negative tool-span time, a `step_finish` without `tokens`, or one with `tokens` lacking `input` or `output`. Each is a stated rule whose failing side has no criterion. Option I would choose: extend criterion 11's rows with a negative `timestamp`, a negative `input`, a `step_finish` without `tokens`, and `tokens` without `output`, each skipped.

   2. Interface, `model_duration`: "its timestamp less that of the last `step_start` before it". The story does not say what happens when a `step_finish` has no `step_start` before it. Counting it as zero, skipping the step, or using another start would each pass the criteria as written. Also, "the `tool_use` events between the two" does not say whether "between" is by event timestamp or by line order. Option I would choose: a `step_finish` with no earlier `step_start` adds 0 to the model time (and still counts as a turn), and "between" is by line order. Please add a criterion row for it in criterion 8.

   3. Interface, the run's files: the rules file `confine-<run>.json` must also be written with mode `0640`. Criterion 4 checks the mode only of the configuration file, and criterion 14 does not check the rules file's mode. Option I would choose: add the rules file's mode `0640` to criterion 14.

   4. Interface, `version()`: "called without login words". Criterion 16 does not test this, so a call through the login shell would pass. Option I would choose: add to criterion 16 that the stand-in's recorded call for `--version` has no login words (it is called as `<executable> --version` alone, even when an API login file is set).

   5. Smoke test: `OpencodeRuntime(..., d / "state", ...)` is given a state directory that does not exist, and the Expect line ends with `[]` from `(d / "state").iterdir()`. The story does not say the runtime creates the state directory. If it does not, the smoke test fails with `FileNotFoundError` before any output. Option I would choose: add the sentence "the state directory is created when missing" to the Interface's run files and a row for it in criterion 4. The other choice is to make the smoke test create `state` first.
4. 2026-10-19 human: 1. Yes: extend criterion 11's rows with a negative `timestamp`, a negative `input`, a `step_finish` without `tokens`, and `tokens` without `output`, each skipped.
   2. Yes: a `step_finish` with no earlier `step_start` adds 0 to the model time and still counts as a turn; "between" is by line order. Add the row to criterion 8.
   3. Yes: add the rules file's mode `0640` to criterion 14.
   4. Yes: add to criterion 16 that `--version` is called as `<executable> --version` alone, without login words, even when an API login file is set.
   5. The other choice: the smoke test creates `state` first (`mkdir` before the runtime is built); the runtime does not create its state directory, which always exists in the instance. The `Expect:` line stays.
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete module `factory.adapters.opencode_runtime`, with constants, signatures, the call words, the configuration keys, the result block and the events all stated. The answers to my questions are carried in; the state directory is not created by the runtime, per journal entry 4.
   - Criteria: each is testable as rows of one test. Every Interface rule has both sides. Carried in from the human's answers (journal entry 4), as edits to the story and no other change of mine:
     - Criterion 11: added rows for a negative `timestamp`, a negative `input`, a `step_finish` without `tokens`, and `tokens` without `output`, each skipped (answer 1).
     - Criterion 8: added the row for a `step_finish` with no earlier `step_start`, which adds 0 to the model time and still counts as a turn, and that "between" is by line order (answer 2).
     - Criterion 14: the rules file has mode `0640` (answer 3).
     - Criterion 16: `--version` is called as `<executable> --version` alone, without login words, also with an API login file set (answer 4).
   - Smoke test: runnable. Per answer 5 it now runs `mkdir "$d/work" "$d/state"` before the runtime is built, and the `Expect:` line is unchanged and checkable line by line.
   - Architecture: the new module sits in `adapters`, and the Wrappers bullet of CLAUDE.md already allows `opencode_runtime`. The runtime reads no `os.environ`, and the interface is an ABC implementation.
   - Scope: within the feature's Scope for S0004, outside its Out of scope. The two test-module changes are covered by decision 19.
7. factory: started tests as self.
8. tester: Wrote the tests of every acceptance criterion against the Interface. They are red on purpose: `factory.adapters.opencode_runtime` does not exist yet.

   Criterion → test:
   - criterion 1: tests/adapters/test_opencode_runtime.py::test_a_run_calls_opencode_run_with_its_words_in_the_working_directory (rows: alias, provider-model)
   - criterion 2: tests/adapters/test_opencode_runtime.py::test_a_request_the_runtime_cannot_configure_fails_before_anything_starts (rows: alias without mapping, tool outside `TOOL_NAMES`, settings missing, settings no JSON, a JSON array, `{}`, no `deny`, `deny` not a list, `deny` not all strings)
   - criterion 3: tests/adapters/test_opencode_runtime.py::test_the_configuration_defines_the_agent_from_its_definition_and_the_settings (rows: settings, no-settings; it also checks the order of the `bash` keys)
   - criterion 4: tests/adapters/test_opencode_runtime.py::test_the_call_sees_its_configuration_file_and_only_the_request_s_environment and ::test_the_state_directory_holds_no_file_after_a_run (rows: completed, died, timed-out)
   - criterion 5: tests/adapters/test_opencode_result_block.py::test_the_result_instructions_name_the_allowed_decisions_and_the_entry
   - criterion 6: tests/adapters/test_opencode_result_block.py::test_the_result_block_gives_its_decision_and_entry_only_when_it_ends_the_text_whole
   - criterion 7: tests/adapters/test_opencode_events.py::test_cost_tokens_and_turns_are_summed_over_the_finished_steps
   - criterion 8: tests/adapters/test_opencode_events.py::test_the_model_time_is_each_step_less_its_tool_calls_summed (rows include a finish without a start, a tool line between by line order, and a tool line after the finish)
   - criterion 9: tests/adapters/test_opencode_events.py::test_a_tool_call_refused_by_permission_is_a_denial_with_its_sorted_input
   - criterion 10: tests/adapters/test_opencode_events.py::test_a_denial_names_the_file_path_of_its_call and ::test_two_refused_calls_on_one_file_record_it_once_in_the_cost_record
   - criterion 11: tests/adapters/test_opencode_events.py::test_a_line_that_does_not_validate_is_skipped
   - criterion 12: tests/adapters/test_opencode_events.py::test_the_end_reason_follows_the_exit_the_steps_and_the_block and ::test_a_call_past_its_time_limit_ends_by_time_limit_without_measures
   - criterion 13: tests/adapters/test_opencode_runtime_launch.py::test_with_an_agent_user_sudo_starts_the_call_after_env_i_and_its_environment (rows: runs, refused)
   - criterion 14: tests/adapters/test_opencode_runtime_launch.py::test_through_the_wrapper_the_call_gets_its_rules_with_opencode_s_folders and ::test_a_wrapper_line_without_events_is_a_runtime_error_naming_it
   - criterion 15: tests/adapters/test_opencode_runtime_launch.py::test_the_call_gets_the_api_file_s_key_and_the_result_names_the_login (rows: key, empty, no-file) and ::test_an_api_file_that_is_a_folder_stops_the_run_naming_it
   - criterion 16: tests/adapters/test_opencode_runtime_launch.py::test_the_version_is_the_first_word_of_a_call_without_login_words and ::test_a_version_that_cannot_be_read_is_a_runtime_error (rows: exit-1, nothing, waits past a 3 s limit)
   - criterion 17: tests/adapters/test_opencode_runtime.py::test_the_kill_point_is_reached_once_after_a_run_and_the_runtime_is_an_agent_runtime and tests/test_opencode_runtime_search.py::test_neither_the_opencode_runtime_nor_the_launch_module_reads_os_environ

   Files created:
   - tests/adapters/opencode_stand_in.py: `write_opencode`, `read_config_modes`, one builder per event (`step_start`, `tool_use`, `text`, `step_finish`, `error`), `result_text`, `stdout`, `opencode_request` and `MODELS`. It reuses `Step`, `STEPS` and `read_calls`/`StandInCall` from `claude_stand_in`. The configuration file's text goes into `StandInCall.files` and its mode into `config-modes.jsonl`, because `StandInCall` forbids extra fields.
   - tests/adapters/test_opencode_runtime.py
   - tests/adapters/test_opencode_result_block.py
   - tests/adapters/test_opencode_events.py
   - tests/adapters/test_opencode_runtime_launch.py (it imports `_write_sudo`/`_sudo_calls` and the `confine_support` helpers rather than copying them)
   - tests/test_opencode_runtime_search.py

   Earlier test files changed under the feature's decision 19, nothing else in them:
   - tests/test_wrapper_search.py: `factory.adapters.opencode_runtime` added to the expected importers.
   - tests/test_model_configuration.py: `EXCEPTIONS` gains the eight private event models.

   Readings to check:
   - Criterion 2's "one that is no JSON": I read it as the Interface's "no JSON object with a list of strings at `permissions.deny`". So invalid JSON expects `the agent settings <path> hold no permissions.deny list`, not `cannot read ...`. The parallel wording supports this; if the coder or reviewer reads it the other way, it is a question for the human.
   - Following the intake answer, the runtime does not create its state directory, so every test creates `state` first.
   - `version()` without login words is checked through the stand-in: its arguments are `["--version"]` and `ANTHROPIC_API_KEY` is absent, with an API file holding a key. The process-module `recorder` fixture patches `claude_runtime` only.

   `make test`: the four new adapter modules fail at collection with ImportError, because `factory.adapters.opencode_runtime` cannot be imported. The search, wrapper-search and model-configuration tests fail on a wrong result. `make lint` is green. I skipped the type check, as the stage says.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/adapters/test_opencode_runtime_launch.py - ImportError while impo...
9. factory: started doing as self.
10. coder: Question: `make check` is red, and the only failing step is in a test file this story's tester wrote, which I may not change.

    `make secrets` (detect-secrets, Secret Keyword) flags `tests/adapters/test_opencode_runtime.py:213`. That line is in `test_the_call_sees_its_configuration_file_and_only_the_request_s_environment`, where the dict `given` holds the API login variable as a quoted literal key with a value (wording changed by the human: the quote itself tripped `make secrets`). The keyword detector matches the quoted key name, whatever the value is. Earlier tests avoid this by keying with the constant: `tests/adapters/test_agent_launch_login.py:62` writes `API_LOGIN_VARIABLE: ...`.

    The options I see:
    - (a) The tester rewrites the two keys of `given` as `API_LOGIN_VARIABLE` and `LOGIN_VARIABLE` (both from `factory.adapters.agent_launch`). The test keeps its name and checks the same thing. **This is the one I would choose.**
    - (b) Add a `pragma: allowlist secret` on that line. CLAUDE.md lists this under "Not without asking", and it would also break `tests/test_process_search.py::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper`.
    - (c) Add a `.secrets.baseline` entry. This is also under "Not without asking".

    If you answer (a), the next doing run ends with `tests` and names this change.

    Where I stopped: the implementation is done. Every other step of the check is green when run on its own: lint, types, layers, sast, licenses, and `make test` (98.98 % coverage, with every new opencode test passing).

    What I built: `src/factory/adapters/opencode_runtime.py` (new), following the Interface:
    - `result_instructions` and `parse_result_block`.
    - The eight private event models. `_Event` carries an after-validator that refuses a `step_finish` without cost or tokens, a `tool_use` without tool or state, and a `text` without text. Its `type` is a `Literal` of the five known types, so an unknown type fails validation and the line is skipped.
    - Measures from the `step_finish` events. Model time follows line order and adds 0 for a finish with no earlier start.
    - Denials matched by `DENIAL_PATTERN`, with the path taken from `filePath`.
    - The per-run configuration, including `Bash(...)` deny patterns read from `settings.json`.
    - `OpencodeRuntime.run` and `version`. Model, tools and settings are checked before any file is written. The call is launched through `login_argv`, `confined_argv` and `launch`, and run with `run_streaming` and a callback that never stops it.

    Main choice: the settings file is parsed with a `TypeAdapter(JsonValue)` and then checked with `isinstance`. I rejected a private Pydantic settings model, because `tests/test_model_configuration.py` would then need a new `EXCEPTIONS` entry that the tester did not add. Text that is not JSON gives "hold no permissions.deny list", as the tester's reading (journal entry 8) and the tests expect. The runtime does not create its state directory (journal entry 4).

    Refactor: I removed a `# noqa: PLR0913` that `test_process_search` counts as a forbidden marker. Ruff did not need it. Nothing else needed changing.

    Noticed but not touched:
    - `make duplicates` reports 7 new similar-code blocks against `claude_runtime`: the refusal checks, the temporary-folder cleanup, `version`, and building the `ProcessRequest` from `launch`. They cannot move into `agent_launch` without it importing the process module, which `tests/test_wrapper_search.py` forbids. Sharing them is a restructuring for its own story.
    - Vulture reports `_ErrorData.status_code` and `OpencodeRuntime` as unused (60 % confidence). The first is the field the provider-limit story will read; the runtime is wired in a later story.
11. 2026-10-19 human: (a): the tester rewrites the two keys of `given` in `test_the_call_sees_its_configuration_file_and_only_the_request_s_environment` as `API_LOGIN_VARIABLE` and `LOGIN_VARIABLE` (from `factory.adapters.agent_launch`), as `tests/adapters/test_agent_launch_login.py` does; the test keeps its name and checks the same thing. No pragma, no baseline entry.
12. factory: started doing as self.
13. coder: The human chose option (a) in entry 11, and that needs a test change, so this goes to the tester. In `tests/adapters/test_opencode_runtime.py::test_the_call_sees_its_configuration_file_and_only_the_request_s_environment`, change the two literal keys of `given` (`"ANTHROPIC_API_KEY"`, `"CLAUDE_CODE_OAUTH_TOKEN"`) to `API_LOGIN_VARIABLE` and `LOGIN_VARIABLE` from `factory.adapters.agent_launch`, as `tests/adapters/test_agent_launch_login.py` does. Nothing else changes: the test keeps its name and checks the same thing. This makes `make secrets` green; it is the only step of `make check` still red. The implementation is still the one entry 10 describes: `src/factory/adapters/opencode_runtime.py`, committed, and I changed no code in this run. The journal changed nothing in the meaning of the task, so `## Description` stays as it is. Still open from entry 10, not touched: `make duplicates` reports 7 blocks similar to `claude_runtime`, and vulture flags `_ErrorData.status_code` and `OpencodeRuntime` as unused, both of which later stories will use.
14. factory: started tests as self.
15. tester: I made the test change the human approved in entry 11, as the coder named it in entry 13. Nothing else changed.

    - In `tests/adapters/test_opencode_runtime.py::test_the_call_sees_its_configuration_file_and_only_the_request_s_environment`, the two literal keys of `given` are now the constants `API_LOGIN_VARIABLE` and `LOGIN_VARIABLE`. They replace `"ANTHROPIC_API_KEY"` and `"CLAUDE_CODE_OAUTH_TOKEN"`.
    - Both constants are imported from `factory.adapters.agent_launch`, the same way `tests/adapters/test_agent_launch_login.py` uses them.
    - The test keeps its name and its values, and still checks that the request's login variables do not reach the call's environment.

    Why: detect-secrets flagged the quoted key name as a Secret Keyword, so `make secrets` was red. Using the constants clears that without a pragma or a baseline entry, as the human decided.

    File changed: `tests/adapters/test_opencode_runtime.py` (one import line, two dict keys). No files created. Every module imported: `make test` is green with 98.98 % coverage, and `make lint` is green.

    `lint`: lint: green (0.0 s)
    `test`: test: green (37.7 s)
16. factory: started doing as self.
17. coder: Question: `make check` is still red. The only failing step is `make secrets`, and the line it flags is in this work item's own journal, which I may not edit.

    detect-secrets (Secret Keyword) flags `factory/features/F0020-opencode-as-a-second-agent-runtime/in-progress/F0020-S0004-the-opencode-runtime-runs-an-agent-and-reads-its-result-from-the-events.md:353`. That line is in my journal entry 10. It quotes the tester's old dict line in backticks (the quote is reworded by the human). The tester's fix (entry 15) cleaned the test file, but the quote in the journal now trips the same detector. The front matter and `## Journal` belong to the factory (R5): any edit I make there is dropped, so I cannot remove the quote myself.

    Every other step is green: lint, types, layers, sast and licenses all pass in this `make check` run, and `make test` is green with 98.98 % coverage. The implementation has not changed since entry 10 (`src/factory/adapters/opencode_runtime.py`), and I changed no code in this run.

    The options I see:
    - (a) You edit journal entry 10 by hand: drop the quoted literal, or write it as `ANTHROPIC_API_KEY: request-key` without the quotes, which the keyword detector does not match. Then the doing stage runs again and ends with `review`. **This is the one I would choose.** It changes a factory-owned record, but only by wording, and adds no marker.
    - (b) Add a `.secrets.baseline` entry for that line. This is under "Not without asking", and the entry would point at a line number that moves as the journal grows.
    - (c) Add a `pragma: allowlist secret` in the journal. Same objection, and it breaks `tests/test_process_search.py`'s marker count only if that test scans work items (I have not checked).

    Not touched: the open points from entry 10 still stand. `make duplicates` reports 7 blocks similar to `claude_runtime`, and vulture flags `_ErrorData.status_code` and `OpencodeRuntime` as unused; later stories will use both. The journal did not change what the task means, so `## Description` stays as it is.
18. 2026-10-19 human: (a), done by the human on the branch: the quote is reworded in journal entries 10 and 18 (commits 0b383f77 and 9d83e265); `detect-secrets scan` over every file the branch changes now finds nothing. No baseline entry, no pragma. Go on to review.
19. factory: started doing as self.
20. coder: `make check` is green: every step passes, `make secrets` included, and the last line is `check: green`. `make test` is green with 98.98 % coverage. The human reworded the quote in the journal (entry 18), and that was the only thing keeping `make secrets` red.

    What I built: `src/factory/adapters/opencode_runtime.py` (new), the one described in entry 10. I changed no code in this run. Already in the module:
    - `result_instructions` and `parse_result_block`.
    - The eight private event models. `_Event`'s `type` is a `Literal` of the five known types, and an after-validator refuses a `step_finish` without cost or tokens.
    - The measures over the `step_finish` events. The model time goes by line order, and a finish with no earlier start adds 0.
    - The denials, with the path read from `filePath`.
    - The configuration for each run, with the `Bash(...)` deny patterns read from `settings.json`.
    - `OpencodeRuntime.run` and `version`, launched through `login_argv`, `confined_argv`, `launch` and `run_streaming`.

    Main choice: the settings file is read with a `TypeAdapter(JsonValue)` and then checked with `isinstance`. I rejected a private Pydantic settings model, because it would need a new `EXCEPTIONS` entry in `tests/test_model_configuration.py` that the tester did not add. Text that is not JSON gives the error "hold no permissions.deny list", which is how the tester read criterion 2 (entry 8).

    Refactor: I did the refactor in entry 10 (I removed a `# noqa: PLR0913` that ruff did not need). Nothing more needed changing.

    Description: entries 11 to 18 changed only wording in a test and the journal, not what the task means, so `## Description` stays as it is.

    Noticed but not touched:
    - `make duplicates` reports 7 blocks similar to code in `claude_runtime`: the refusal checks, the temporary-folder cleanup, `version`, and building the `ProcessRequest`. They cannot move into `agent_launch` without it importing the process module, which `tests/test_wrapper_search.py` forbids. Sharing them would be a restructuring for its own story.
    - Vulture flags `_ErrorData.status_code` (S0006 will read it) and `OpencodeRuntime` (S0008 wires it in) as unused.

    `check`: check: green
    `duplicates`: duplicates: 9 new, 35 known, 4 gone
21. factory: started review as self.
22. reviewer: Review, round 0: 7 findings, so the work item goes back to doing. I read every file in the diff against the 19 criteria. Criteria 1 to 17 each have a test, and each test checks what its criterion says. The architecture holds: the module sits in `adapters`, `test_wrapper_search` lets it import the process module, it reads no `os.environ`, and it implements the interface's ABC. Security is clean: no new markers, and the prompt is passed as a single argument. The findings are about copied helpers, one dead field and two behaviours no criterion named. I ran `make duplicates`: 7 new similar blocks against `claude_runtime`, all covered by findings 1 to 4.

    1. `src/factory/adapters/opencode_runtime.py:254` `_since` is a second copy of `claude_runtime._since`. Fix: move it into `factory.adapters.agent_launch` (it needs no process import) and have both runtimes import it from there.
    2. `src/factory/adapters/opencode_runtime.py:380` `_denied_path` copies `claude_runtime._denied_path`; only the keys differ. Fix: one shared function in `agent_launch` that takes the keys as an argument (`("filePath",)` here, `("file_path", "notebook_path")` in the Claude runtime).
    3. `src/factory/adapters/opencode_runtime.py:452-470` `_has_usable_events`, `_sudo_refusal`, `_confine_refusal` and `_confinement` copy `claude_runtime._has_usable_reply`, `_sudo_refusal`, `_confine_refusal` and `_confinement`. Fix: share them in `agent_launch` with plain inputs (stderr, a usable flag, `os_user`, `runtime_folders`), so `agent_launch` still never imports the process module.
    4. `src/factory/adapters/opencode_runtime.py:532-653` `version`, `_call`, `_check_confinement`, `_check_login`, `_remove_temporary_folder` and `_process_request` copy the `ClaudeCodeRuntime` methods of the same names almost line for line. Entry 10 says these cannot move because `agent_launch` may not import the process module, but that only applies to the `run_process`/`run_streaming` calls, which can stay in each wrapper's `_start`. Fix: move the logic around those calls into `agent_launch` with plain values, as `killed_at_limit` and `cleanup_argv` already are: the version reading from exit status, timed-out flag, stdout and stderr; the refusal checks; building the request from `launch`. If a shared module that itself calls the process module is wanted instead, that is a change to `tests/test_wrapper_search.py` and needs a question to the human.
    5. `src/factory/adapters/opencode_runtime.py:229` `_Step.timestamp` is set but never read; the model time comes from the events. This is dead code. Fix: remove the field.
    6. Criterion 18 added; it needs its test. The code builds error texts for `version()` (`--version failed: <stderr>`, `printed nothing`, `cannot start <executable>: <error>`), for a run whose executable cannot start, and for a state directory that cannot be written (`opencode_runtime.py:546-563`, `:651-653`). No criterion pinned them, and criterion 16's test only checks that `AgentRuntimeError` is raised. Pinning them needs no change under `src/`.
    7. Criterion 19 added; it needs its test. CLAUDE.md asks for both sides of every limit the Interface states. The "non-negative" timestamps, counts and costs are tested only on the refused side (-1 or -0.5 in criterion 11); nothing tests 0 for cost, `input` or timestamp. For example, `_model_ms` checking `started is not None` against a truthiness check is unpinned for a `step_start` at 0. Pinning it needs no change under `src/`.

    I renumbered the closing criteria: `make check` is now 20 and `docs:` is 21.

    What I chose not to raise: negative values of `output`, `reasoning`, the cache counts and the span ends. The intake asked about those, and the human chose only the four rows of criterion 11 (journal entry 4). I did not count `_RunFiles` as a copy, since its fields differ from the Claude runtime's.

    Earlier tests:
    - `tests/test_model_configuration.py`: the story names it under the feature's decision 19. The change only adds the eight `opencode_runtime` models to `EXCEPTIONS`, which is within that leave.
    - `tests/test_wrapper_search.py`: the story names it under the feature's decision 19. The change only adds `factory.adapters.opencode_runtime` to the expected importers, which is within that leave.
23. factory: started doing as self.
24. coder: Round 1. I fixed the reviewer's code findings 1 to 5. Findings 6 and 7 add criteria 18 and 19, which need only their tests, so this goes to the tester: **criterion 18** (the error texts of `version()`, of a run whose executable does not exist, and of a missing state directory) and **criterion 19** (a `step_finish` with cost 0, `input` 0 and timestamp 0, after a `step_start` at 0, is a valid step: one turn, `cost_usd` `Decimal("0")`, tokens input 0, model time 0 s). Neither needs any change under `src/`. `make check` is green (`check: green`).

    What I built:
    - **`src/factory/adapters/agent_launch.py`**: the logic both runtimes shared now lives here. It takes plain values, so the module still never imports the process module.
      - `since` (finding 1).
      - `denied_path(tool_input, keys)` (finding 2). The Claude runtime passes `("file_path", "notebook_path")`, opencode passes `("filePath",)`.
      - `call_refusal(stderr, *, printed, timed_out, os_user, starters)` (finding 3). It replaces each runtime's `_has_usable_*`, `_sudo_refusal`, `_confine_refusal`, `_check_confinement` and `_check_login`, with the same order and the same texts.
      - For finding 4:
        - `version_printed`, which reads the version from the exit status, stdout and stderr.
        - `run_launch`, which does `without_login`, merges the runtime's environment and calls `launch`.
        - `cleanup_launch`, the removal call as a `Launch`.
        - `finished_run`, which sets the duration and reaches the `AGENT_RUN` kill point.
      - `Starters`, a new frozen model holding the sudo executable, the confine executable and the login files.
    - **`src/factory/adapters/claude_runtime.py`** and **`src/factory/adapters/opencode_runtime.py`**:
      - Both now use the shared functions and keep a `Starters` in `self._starters` instead of three attributes. `ClaudeCodeRuntime`'s `sudo_executable` and `confine_executable` properties read from it.
      - Each keeps a small `_request_of(Launch, cwd) -> ProcessRequest`, its `_start`, and the `killed_at_limit` model copy. Those touch `ProcessRequest` or `ProcessResult`, which `agent_launch` may not import.
      - The opencode runtime's `_Step.timestamp` is removed (finding 5).

    Main choice: I grouped the start settings in the small `Starters` model. Without it, `call_refusal` would take seven arguments, and ruff's PLR0913 allows five. I rejected a `# noqa`, which `test_process_search` counts as a forbidden marker. I also rejected moving the shared code into a module that imports the process module: that would change `tests/test_wrapper_search.py`, and the reviewer said that needs a question.

    Two constraints from the existing tests:
    - `tests/adapters/test_claude_runtime_confinement.py` monkeypatches `claude_runtime.SHELL_EXECUTABLE` and `CLEANUP_TIME_LIMIT`. So `cleanup_launch` takes the shell and the time limit as arguments, and each runtime passes its own module's names.
    - In `run_launch`, the caller wraps the words in `confined_argv` itself, to keep the function within five arguments.

    Refactor: I read my diff once and changed `agent_launch`'s module docstring to cover the new end-of-run helpers. Nothing else needed changing.

    Description: the journal added criteria 18 and 19 and changed nothing else in the meaning of the task, so `## Description` stays as it is.

    Noticed but not touched:
    - `make duplicates` now reports 3 new similar blocks, down from 7. They are only matching call sites of the shared helpers (the `call_refusal` call, the `version_printed` call, the temporary-folder removal), each with the same keyword arguments. `_request_of` is the same 4 lines in both runtimes, because `agent_launch` may not build a `ProcessRequest`.
    - Vulture still flags `_ErrorData.status_code` (S0006 reads it) and `OpencodeRuntime` (S0008 wires it in) as unused.
25. factory: started tests as self.
26. tester: Round 1. The coder's entry 24 said criteria 18 and 19, which the reviewer added, need only their tests. I wrote those two tests and changed no existing test.

    - criterion 18: `tests/adapters/test_opencode_runtime.py::test_a_version_that_cannot_be_read_names_the_reason` has three rows. The first is exit 1 with stderr: the detail is exactly `<executable> --version failed: <stderr>`. The second prints nothing: exactly `<executable> --version printed nothing`. The third is a missing executable: the detail starts with `cannot start <executable>: ` and an error text follows.
    - criterion 18: `tests/adapters/test_opencode_runtime.py::test_a_run_that_cannot_start_names_the_reason` has two rows. The first is a missing executable: `cannot start <executable>: <error>`, and the state directory holds no file afterwards. The second is a missing state directory: `cannot write the state directory <path>: <error>`, and the stand-in is never called.
    - criterion 19: `tests/adapters/test_opencode_events.py::test_a_step_with_zero_values_is_a_valid_step` checks that each step counts as one turn with the expected `cost_usd`, `tokens.input` and model time. It has four rows. Three set one value to zero each: cost 0, `input` 0, and a timestamp of 0 for both `step_start` and `step_finish`. The fourth is the criterion's combined case: cost 0, input 0 and timestamp 0, giving `Decimal("0")`, input 0 and 0 s. These rows are the accepted side of the limits whose refused side is in criterion 11's `test_a_line_that_does_not_validate_is_skipped`. I kept that existing test as it is rather than merging the two, because its rows check that a line is skipped, not that it is a valid step.

    `<error>` is the operating system's text, so those rows check the fixed prefix and that some text follows it. They do not check the exact OS message.

    Files changed: `tests/adapters/test_opencode_runtime.py` and `tests/adapters/test_opencode_events.py`, both written by this story; I only added tests to them. I created no new files.

    `make test` is green: the code is already built, so the new tests pass rather than fail. Every module imported. `make lint` is green.

    `lint`: lint: green (0.0 s)
    `test`: test: green (40.3 s)
27. factory: started doing as self.
