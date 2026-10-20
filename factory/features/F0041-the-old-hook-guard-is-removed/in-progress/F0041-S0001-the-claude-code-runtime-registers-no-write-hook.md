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
  started_at: '2026-10-20T10:02:54.035685Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T10:02:54.030477Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T10:02:54.035685Z'
  stage: intake
---

# The Claude Code runtime registers no write hook

## Description

Since F0019 every agent run starts through `factory-confine`, and the kernel refuses every write outside the run's write paths, tool paths and temporary folder. `ClaudeCodeRuntime` still registers the older hook beside it: for a request with guard settings it writes `guard-<session>.json` (the `GuardSettings`, with the run's temporary folder when confined) and `hooks-<session>.json` (a `PreToolUse` hook on `Edit|Write` whose command is `factory-guard --settings <guard file>`), and passes `--settings <hooks file>` to `claude`. F0019's cross-check of 2026-10-19 found that the hook refused nothing the kernel allows (the feature's goal). This story stops registering it: the runtime writes no guard or hooks file and passes no `--settings`, with or without guard settings, confined or not. The request's guard settings still build the kernel's rules (`run_confinement`), unchanged, and the undo after the run is unchanged. The rule R14 of the seven shipped agents loses the clause that names the hook (the feature's decision 7), so no agent reads about a hook that no longer runs. A Claude Code run is then guarded as an opencode run is today. The command `factory-guard`, its adapter, `GUARD_COMMAND` and the preflight's search for it stay until S0002; the documents change in S0003 (decision 1).

## Interface

`src/factory/adapters/claude_runtime.py` (`adapters`):

- Removed: `GUARDED_TOOLS`, `_hook_settings`, the fields `guard` and `hooks` of `_RunFiles` (and their paths in `_RunFiles.of` and `_RunFiles.remove`), `ClaudeCodeRuntime._guard_settings`, and the import of `GUARD_COMMAND`.
- `_arguments(request, new_session, files)` adds no `--settings`, whatever `request.guard` is. Every other flag and its order stay as they are.
- `ClaudeCodeRuntime._write_files(request, files)` writes `instructions-<session>.md` always and `confine-<session>.json` when `confine_executable` is set, each with `RUN_FILE_MODE`, and nothing else.
- `request.guard` still reaches `run_confinement` (through `device_confinement`) exactly as today.
- `SWITCHES` keeps its three entries; its comment says that Python started by the agent would otherwise leave bytecode in the working copy (it no longer names a hook).
- `__all__` is unchanged.

`claude/agents/acceptance-reviewer.md`, `coder.md`, `documenter.md`, `intake.md`, `reviewer.md`, `smoke-tester.md`, `tester.md`: in the line that starts `R14. `, the words `a hook also refuses an edit outside the write paths, ` are deleted, so the line holds "the kernel refuses every other write, by any tool and any command you run, and the factory undoes any other write after the stage." and is otherwise unchanged.

Unchanged: `factory.adapters.claude_guard`, `factory.entry.guard`, `GUARD_COMMAND`, `factory.application.preflight`, `factory.adapters.opencode_runtime`, `factory.adapters.agent_launch`.

Tests (the tester writes them):

- `tests/adapters/test_claude_runtime_no_hook.py` (new): criterion 1, with `write_stand_in`, `read_calls` and `Step` from `tests/adapters/claude_stand_in.py` and `Layout`, `confined_runtime` and `run_request` from `tests/confine_support.py`.
- `tests/test_claude_agent_no_hook.py` (new): criterion 5's second half, over `SHIPPED_NAMES` and `agent_body` from `tests/shipped_agents.py`.
- Changed under the leave of the feature's decision 9: `tests/adapters/test_claude_runtime.py` (`RUN_FILES`, `test_call_passes_every_flag_in_order`, `test_call_sees_instructions_guard_and_hooks_files` renamed `test_call_sees_the_instructions_file_and_no_guard_or_hooks_file`), `tests/adapters/test_claude_runtime_resume.py` (`RUN_FILES`, and `test_resumed_call_sees_the_same_run_files_and_none_is_left` expects `len(first.files) == 1`), `tests/adapters/test_claude_runtime_login.py` (`test_the_login_stands_in_no_argument_no_run_file_and_no_result` expects `len(claude_call.files) == 1`), `tests/adapters/test_claude_runtime_file_modes.py` (`test_the_files_of_a_run_are_0640_when_the_agent_starts`, row `with-guard`), `tests/adapters/claude_stand_in.py` (the `--settings` block), `tests/test_claude_agent_refusal.py` (`_WRITE_PATHS_RULE`); deleted: `tests/adapters/test_claude_runtime_guard_temporary.py`.

## Acceptance criteria

1. No run registers a hook (rows of one parametrized test, the stand-in at `layout.stand_in`, the request `run_request(layout)`): unconfined (`ClaudeCodeRuntime(str(claude), layout.state)`) with its guard settings, unconfined with `guard` set to `None`, and confined through `confined_runtime(layout, claude)` with its guard settings. In each row the stand-in's one call has no `--settings` among its arguments, no key of the call's `files` has a file name that starts with `guard-` or `hooks-`, and the run ends `completed`. (A confined request without guard settings may write nothing and ends `died`, as `tests/adapters/test_claude_runtime_confinement.py` already pins.)
2. The flags keep their order without `--settings` (`test_call_passes_every_flag_in_order`, a request with guard settings): the arguments are exactly `-p`, `Stage: doing`, `--model`, `sonnet`, `--effort`, `high`, `--tools`, `Read,Edit`, `--session-id`, `<session>`, `--append-system-prompt-file`, `<state>/instructions-<session>.md`, `--permission-mode`, `auto`, `--permission-prompts`, `none`, `--strict-mcp-config`, `--max-budget-usd`, `3`, `--output-format`, `json`, `--json-schema`, `<schema>`.
3. The call sees its instructions and nothing of the hook (`test_call_sees_the_instructions_file_and_no_guard_or_hooks_file`, rows `state` and `state dir`): `call.files[<state>/instructions-<session>.md]` is the agent's instructions, and neither `<state>/guard-<session>.json` nor `<state>/hooks-<session>.json` is a key of `call.files`.
4. The run's files at the agent's start (`test_the_files_of_a_run_are_0640_when_the_agent_starts`): with guard settings and without, the state directory holds exactly the prefixes `["instructions-"]`, each file with mode `0640`.
5. R14 names no hook: in each of the seven shipped agents the `## Rules` section holds, as one line, the R14 text of `_WRITE_PATHS_RULE` with "the kernel refuses every other write, by any tool and any command you run, and the factory undoes any other write after the stage." (rows over `SHIPPED_NAMES`); and the word `hook` occurs nowhere in any shipped agent's body (rows over `SHIPPED_NAMES`).
6. `make check` stays green.
7. docs: none. S0003 rewrites every passage on the hook once S0002 has removed it whole (the feature's decision 1).

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/work/src"
cat > "$d/claude" <<EOF
#!/bin/sh
printf '%s\n' "\$@" > "$d/work/src/arguments"
ls "$d/state" > "$d/work/src/files"
if echo x > "$d/work/outside.txt" 2>/dev/null; then echo written > "$d/work/src/outside"; else echo refused > "$d/work/src/outside"; fi
printf '{"type":"result","subtype":"success","is_error":false,"structured_output":{"decision":"question","entry":"e"}}'
EOF
chmod +x "$d/claude"
uv run python - "$d" <<'EOF'
import shutil
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, GuardSettings

d = Path(sys.argv[1])
work = d / "work"
agent = AgentDefinition(name="coder", model="sonnet", tools=["Read"], budget_usd=Decimal(1), instructions="x")
guard = GuardSettings(root=work, write_paths=["src/*"], protected_paths=[])
request = AgentRunRequest(agent=agent, prompt="Stage: doing", allowed_decisions=["question"], time_limit=timedelta(seconds=60), working_directory=work, environment={"PATH": "/usr/bin:/bin"}, guard=guard)
for confined in (False, True):
    options = {"confine_executable": shutil.which("factory-confine"), "temporary_root": d / "tmp"} if confined else {}
    (d / "tmp").mkdir(exist_ok=True)
    result = ClaudeCodeRuntime(str(d / "claude"), d / "state", **options).run(request)
    arguments = (work / "src" / "arguments").read_text(encoding="utf-8").splitlines()
    files = sorted(name.split("-")[0] for name in (work / "src" / "files").read_text(encoding="utf-8").split())
    outside = (work / "src" / "outside").read_text(encoding="utf-8").strip()
    print("confined" if confined else "unconfined", "--settings" in arguments, " ".join(files), outside, result.end_reason)
    (work / "outside.txt").unlink(missing_ok=True)
EOF
```
Expect: two lines, `unconfined False instructions written completed` and `confined False confine instructions refused completed` (no `--settings` and no guard or hooks file in either run; in the confined run the kernel alone refuses the write to the checkout's root; before this story the lines were `unconfined True guard hooks instructions written completed` and `confined True confine guard hooks instructions refused completed`)

```bash
grep -c -F 'a hook also refuses' claude/agents/*.md | grep -c ':0$'
```
Expect: `7`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
