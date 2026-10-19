# The opencode runtime leaves out Skill wherever it stands in an agent's tools

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0022's mutation run left one mutant alive in the code the feature itself wrote: in `factory.adapters.opencode_runtime._tools`, the `continue` that skips a tool of `LEFT_OUT_TOOLS` can become `break` and every test still passes. Every test of the rule lists `Skill` last (`["Read", "Skill"]`, `["Skill"]`, the seven shipped agents, whose `tools` end with `Skill`), so a loop that stopped at `Skill` looks the same. A project agent (S0001) may list its tools in any order. With `tools: [Skill, Read, Bash]` under opencode, a broken skip would turn on no tool after `Skill`: the run would start with no `read` and no `bash`, and no refusal would say so. This story pins the rule for any position of the left-out tool. It changes no code: today's runtime already does it. A tool outside `TOOL_NAMES` after `Skill` is still refused.

## Interface

No module under `src/factory/` changes. The behaviour pinned is that of `OpencodeRuntime.run` in `factory.adapters.opencode_runtime` (adapters), as it is:

- A tool in `LEFT_OUT_TOOLS` turns on no name of `OPENCODE_TOOLS` and is not refused, wherever it stands in the agent's `tools`. Every tool before and after it is mapped through `TOOL_NAMES` as if it were absent.
- A tool outside both `TOOL_NAMES` and `LEFT_OUT_TOOLS` raises `AgentRuntimeError` `the opencode runtime has no tool for <tool>` before anything starts, also when it stands after a left-out tool.

Tests (the tester writes them): four rows added to `test_skill_is_left_out_and_every_other_tool_without_an_opencode_name_is_refused` in `tests/adapters/test_opencode_left_out_tools.py` (F0022-S0002's), with the stand-in and builders it already imports. The test keeps its name and its three rows. The leave for this change is the feature's decision 14 (S0003).

## Acceptance criteria

1. The opencode runtime with the stand-in, an agent whose tools are (rows): `["Skill", "Read"]` completes, and the configuration's `tools` are true for `read` alone; `["Skill", "Read", "Bash"]` completes with `read` and `bash` true and every other name of `OPENCODE_TOOLS` false; `["Read", "Skill", "Grep"]` completes with `read` and `grep` true and the rest false; `["Skill", "NotebookEdit"]` raises `AgentRuntimeError` with the detail `the opencode runtime has no tool for NotebookEdit`, and the stand-in is never called.
2. `make check` stays green.
3. docs: none. No behaviour and no message changes, and `docs/project-guide/agents.md` (*The opencode runtime*) already says that a tool in `LEFT_OUT_TOOLS` turns on no opencode tool.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir "$d/work" "$d/state"
cat > "$d/opencode" <<'EOF'
#!/bin/sh
cp "$OPENCODE_CONFIG" "$(dirname "$0")/config.json"
cat <<'LINES'
{"type":"step_start","timestamp":1000,"sessionID":"ses_smoke","part":{"type":"step-start"}}
{"type":"text","timestamp":1900,"sessionID":"ses_smoke","part":{"type":"text","text":"<factory-result>\ndecision: question\nentry:\nThe smoke entry.\n</factory-result>"}}
{"type":"step_finish","timestamp":2000,"sessionID":"ses_smoke","part":{"type":"step-finish","reason":"stop","cost":0.01,"tokens":{"input":1,"output":1}}}
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
agent = AgentDefinition(name="coder", model="sonnet", tools=["Skill", "Read", "Grep"], budget_usd=Decimal("1"), instructions="Smoke.")
request = AgentRunRequest(agent=agent, prompt="Smoke.", allowed_decisions=["question"], time_limit=timedelta(seconds=60), working_directory=d / "work", environment={"PATH": "/usr/bin:/bin"})
result = OpencodeRuntime(str(d / "opencode"), d / "state", models={"sonnet": "anthropic/claude-sonnet-5-5"}).run(request)
config = json.loads((d / "config.json").read_text(encoding="utf-8"))
print(result.end_reason, result.decision)
print(sorted(name for name, on in config["agent"]["factory-coder"]["tools"].items() if on))
EOF
```
Expect: two lines, `completed question`, `['grep', 'read']`

## Journal

