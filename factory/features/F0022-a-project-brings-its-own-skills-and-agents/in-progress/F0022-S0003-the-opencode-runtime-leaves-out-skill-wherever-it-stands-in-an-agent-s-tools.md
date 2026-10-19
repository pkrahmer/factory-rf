---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 282
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T20:00:31.550273Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T20:00:31.557402Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T20:00:54.381978Z'
  stage: intake
  run: 701a7f5b432245e79369f604e8fad06e
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T20:01:14.832998Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T20:03:38.600971Z'
  stage: tests
  run: a1e63e1787f94130be9c664c9bb1b4b5
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T20:03:59.395139Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T20:05:53.863283Z'
  stage: doing
  run: 2f9b6a748428411aa7df308893c98022
---

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

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: no source change. It names `OpencodeRuntime.run` and `LEFT_OUT_TOOLS` in `factory.adapters.opencode_runtime`. I checked `_tools` (lines 272-280). It does `continue` for a left-out tool, maps the others through `TOOL_NAMES`, and raises `the opencode runtime has no tool for <tool>` for an unknown one. This is the behaviour the story describes. Both Interface clauses (left out wherever it stands; refused when it follows a left-out tool) have a criterion.
   Criteria: criterion 1 has four rows, and each can be checked by one parametrized test function. Three rows cover the left-out tool in first and middle position, with the exact true and false tool sets. The fourth covers the failing side: `["Skill", "NotebookEdit"]` is refused with the exact detail, and the stand-in is never called. The existing test `test_skill_is_left_out_and_every_other_tool_without_an_opencode_name_is_refused` in `tests/adapters/test_opencode_left_out_tools.py` has the three rows and the structure the story expects: a str expected value for refusal, a set otherwise. The leave to change it is decision 14 (S0003). Criterion 2 is `make check`. Criterion 3 is `docs: none`, with a reason given.
   Smoke test: the commands run against the stand-in `opencode` script and print two lines. The Expect line is exact (`completed question`, `['grep', 'read']`).
   Architecture: no change. The adapter layer is untouched and the tests sit in `tests/adapters/`.
   Scope: within F0022 (decisions 11 and 14). It is not in Out of scope, and it adds no new behaviour.
   Open note, not a question: `feature.md` lists only S0001 and S0002 under Stories, but its decision 14 already names S0003, so I take that as the human's intent.
4. factory: started tests as self.
5. tester: Added the four rows criterion 1 asks for to the existing parametrized test. The test keeps its name and its three original rows; the leave for changing it is the feature's decision 14 (S0003). Each new row uses the stand-in and builders the module already imports.
   - criterion 1: tests/adapters/test_opencode_left_out_tools.py::test_skill_is_left_out_and_every_other_tool_without_an_opencode_name_is_refused, new rows `skill-first` (`["Skill", "Read"]` → `read` only), `skill-before-two` (`["Skill", "Read", "Bash"]` → `read`, `bash`), `skill-in-the-middle` (`["Read", "Skill", "Grep"]` → `read`, `grep`), `notebook-edit-after-skill-refused` (`["Skill", "NotebookEdit"]` → `AgentRuntimeError` with `the opencode runtime has no tool for NotebookEdit`, and no stand-in call). The completing rows check that every other name of `OPENCODE_TOOLS` is false.
   - criterion 2: `make check` is checked by the factory, not by a test. `make lint` is green.
   - criterion 3: docs: none, so there is no test.
   Files: changed tests/adapters/test_opencode_left_out_tools.py, which was written by another story (F0022-S0002). Created no new files.
   Modules the test run could not import: none. The new tests are green from the start, not red: the story changes no code, so they pin what the code already does (`make test` green). This means no red specification is handed to the coder. Against the `break` mutant, all four new rows would fail: the first three because tools after `Skill` would be false, the fourth because nothing would be refused.

   `lint`: lint: green (0.0 s)
   `test`: test: green (46.8 s)
6. factory: started doing as self.
7. coder: Built nothing, as the story asks: the Interface says no module under `src/factory/` changes. The tester's four new rows in `tests/adapters/test_opencode_left_out_tools.py` (`skill-first`, `skill-before-two`, `skill-in-the-middle`, `notebook-edit-after-skill-refused`) already pass against the current `_tools` in `src/factory/adapters/opencode_runtime.py`. That function skips a tool of `LEFT_OUT_TOOLS` with `continue` and refuses an unknown tool wherever it stands.
   Main choice: leave the source untouched. I rejected rewriting `_tools`, for example as a comprehension over the tools that are not left out, so that the `break` mutant could not occur at all. That would be a restructuring the story does not ask for. The new rows already kill that mutant, as the tester's entry explains.
   Refactor: there is no diff of mine to refactor; the working tree holds only the factory's costs sidecar.
   `make check`: check: green (test: green, 42.6 s).
   Description: no journal entry changed the meaning of the task, so it stays as written.
   Noticed, not touched: as the intake noted, `feature.md` lists only S0001 and S0002 under Stories, while its decision 14 names S0003.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
