---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 282
comments_read: []
handed_over: approval
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
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T20:06:14.663423Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T20:06:34.326227Z'
  stage: review
  run: 1031c21739e24166a306484f385d3a7e
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T20:06:54.800921Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-19T20:07:12.025881Z'
  stage: docs
  run: 20c263aa8bf2412e8247e78837f951a0
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T20:07:32.527804Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-19T20:07:55.377608Z'
  stage: smoke-test
  run: 9ecc8c50a0684191be8ca03d0c8a5df1
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
8. factory: started review as self.
9. reviewer: no findings

   I read the work item and the diff (`git diff main...HEAD -- . ':!factory'`). The diff adds 8 lines to `tests/adapters/test_opencode_left_out_tools.py` and changes nothing under `src/`.
   - Criterion 1: the four rows `skill-first`, `skill-before-two`, `skill-in-the-middle` and `notebook-edit-after-skill-refused` are in `test_skill_is_left_out_and_every_other_tool_without_an_opencode_name_is_refused`, after its three original rows.
     - The completing rows compare the whole `tools` map of the configuration with `{name: name in expected for name in OPENCODE_TOOLS}`. So they check both that the expected names are true and that every other name is false.
     - The refused row checks the exact `detail`, and checks that `read_calls` is empty, which means the stand-in was never called.
     - Read against `_tools` in `src/factory/adapters/opencode_runtime.py:271-279`: with `continue` changed to `break`, the first three rows would fail because the tools after `Skill` would be false. The fourth would fail because nothing would be refused.
     - Both Interface clauses are tested: the left-out tool in first, middle and last position, and the refused tool after a left-out tool.
     - Entry 7 records that the factory's `make check` was green.
   - Architecture and security: nothing under `src/` changed, and the diff adds no marker that silences a check.
   - Quality: the rows are part of the existing parametrized test. No new helper, no duplicated code.
   - Work item: the Description matches what was built (no code change, rows added). The coder's entry gives the main choice, leaving `_tools` as it is, and the rejected rewrite as a comprehension. Criterion 3, `docs: none`, still holds: no behaviour and no message changed.
   - The coder's entry has no `mutants` line, so there is no mutation report to read.

   Earlier tests:
   - tests/adapters/test_opencode_left_out_tools.py (M): the human's leave, `feature.md` decision 14 (S0003). Four rows were added after the three existing ones, the test keeps its name and its rows, and nothing else in the module changed.

   Notes:
   - The coder's entry records `duplicates: 5 new` with no change under `src/factory` on this branch, so those findings do not come from this story. The acceptance reviewer can look at them.
10. factory: started docs as self.
11. documenter: Files changed: none. The docs criterion is `none`: the diff only adds four rows to `tests/adapters/test_opencode_left_out_tools.py` and changes nothing under `src/`, so no behaviour or message changed.

    Cross-read and found current: `docs/project-guide/agents.md`, *The opencode runtime* (line 100). It says a tool in `LEFT_OUT_TOOLS` (`Skill`) turns on no opencode tool and is not refused, and that every other tool outside `TOOL_NAMES` raises `AgentRuntimeError`. That is the behaviour the new rows pin, for any position of `Skill`. A grep of `README.md` and `docs/operator-guide.md` found no mention of the rule that needs a change.

    Stale text noticed, not touched: `feature.md` lists only S0001 and S0002 under Stories, while its decision 14 names S0003. The intake, coder and reviewer entries already noted it. `feature.md` is the human's file, so I left it.

    No findings, and I ran no `make check`, because I changed no file.

    `check`: check: green (not run again: passed on tree 820a60a55ae9 at 2026-10-19T20:05:00Z)
    `secrets`: secrets: green (0.1 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Ran the one command block under `## Smoke test` exactly as written, from the repository root, in a fresh shell. It used its own `mktemp -d` folder with an EXIT trap that removes it. It started no server.

    Command 1 (the stand-in `opencode` script, then `OpencodeRuntime.run` with an agent whose tools are `["Skill", "Read", "Grep"]`). Exit 0.
    ```
    completed question
    ['grep', 'read']
    ```
    Met its `Expect:` line: two lines, `completed question` and `['grep', 'read']`.

    Check against the acceptance criteria:
    - Criterion 1: the smoke test agrees with it. `Skill` comes first in the list and is left out without a refusal. Both tools after it, `read` and `grep`, are turned on, and no other name in the configuration's `tools` is true. That is the behaviour the rows `skill-first`, `skill-before-two` and `skill-in-the-middle` pin. The smoke test does not exercise the refusal row (`["Skill", "NotebookEdit"]`), and nothing in it contradicts that row.
    - Criterion 2: the smoke test says nothing against `make check`. Entries 7 and 11 record it green. I did not run it myself, because this stage only runs the smoke test.
    - Criterion 3 (docs: none): nothing contradicts it. The output has no new message or behaviour.

    Findings: none.
