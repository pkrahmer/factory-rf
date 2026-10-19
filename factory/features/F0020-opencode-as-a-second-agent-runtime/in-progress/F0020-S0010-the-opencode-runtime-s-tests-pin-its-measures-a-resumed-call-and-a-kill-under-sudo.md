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
  started_at: '2026-10-19T18:52:33.936980Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T18:52:33.928949Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T18:52:33.936980Z'
  stage: intake
---

# The opencode runtime's tests pin its measures, a resumed call and a kill under sudo

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0020's mutation run left 64 mutants of `factory.adapters.opencode_runtime` alive. They show what the opencode runtime does today and what no test would notice breaking:

- a result entry of several lines keeps its line breaks;
- a result block whose second line is not `entry:` is no result;
- the model time takes off every tool call of a step, not only the last;
- a failed tool call that is not a denial does not hide the denials after it;
- a resumed call keeps every word of the first call before `--session`;
- under an agent user, a call that the inner `timeout` kills at its limit ends `time_limit` and keeps its session and login;
- with the write guard's wrapper set, the run's temporary folder is gone after the run.

Each of these is a line of the feature's promise (decisions 7, 8, 11 and 18), and the opencode runtime is the module the feature is about. This story writes the tests and changes no code. The Claude Code runtime's tests already pin the same behaviour on its side.

## Interface

No module under `src/factory/` changes. The behaviour pinned is that of `OpencodeRuntime.run` and `parse_result_block` in `factory.adapters.opencode_runtime` (adapters), as they are:

- `parse_result_block(text, allowed_decisions)`: the entry is the block's lines after `entry:`, joined with `\n` and stripped. The block is `None` unless its first line starts with `decision:` and its second line is exactly `entry:`.
- `model_duration` sums each step's span (its `step_start` to its `step_finish`, by line order) less the spans of every `tool_use` event between them. A `tool_use` before the first `step_start` adds nothing.
- `permission_denials` lists every `tool_use` event with `status` `error` whose error contains `permission` or `denied`, in any case (`DENIAL_PATTERN`), in line order, whatever events come between them.
- The words of a resumed call are the first call's words, then `--session <id>`, then the prompt: `run --format json --auto --model <model> --agent factory-<name> --session <id> <prompt>`. This holds for the budget's own resume (prompt `FINISH_MESSAGE`) and for a request with `resume_session`.
- With `os_user` set, a call whose exit status is in `KILL_STATUSES` and whose duration reached its time limit ends `time_limit`. It keeps the `session` of its events and the `login` the shell reported.
- With a confine executable set, the run's temporary folder is removed after each call, as the agent user under `sudo` when one is set, also after a died or killed call.

Tests (the tester writes them), all new modules that use the stand-in and the event builders of `tests/adapters/opencode_stand_in.py`, imported, not copied:

- `tests/adapters/test_opencode_measures.py` (criteria 1 to 3);
- `tests/adapters/test_opencode_resumed_words.py` (criterion 4);
- `tests/adapters/test_opencode_sudo_time_limit.py` (criterion 5, with a stand-in `sudo` as `tests/adapters/test_claude_runtime_sudo_time_limit.py` uses for the Claude Code runtime);
- `tests/adapters/test_opencode_confinement.py` (criterion 6, with `CONFINE` and with the stand-in `write_confine` of `tests/confine_support.py`, as `tests/adapters/test_claude_runtime_confinement.py` uses them; the test makes the layout's `state` folder, since the runtime does not).

No earlier test changes.

## Acceptance criteria

1. `parse_result_block`, one parametrized test:
   - the text `<factory-result>` / `decision: question` / `entry:` / `First line.` / (empty) / `Third line.` / `</factory-result>`, with `question` allowed, gives `("question", "First line.\n\nThird line.")`;
   - the same block with `note:` in place of `entry:` gives `None`;
   - a block whose first line is `question` (no `decision: ` label) and whose second line is `entry:` gives `None`.
2. `model_duration`, one parametrized test:
   - one step from `step_start` at 1000 to `step_finish` at 2000, with two `tool_use` events between them spanning 1100–1200 and 1300–1500, gives 700 ms;
   - the same events after a `tool_use` spanning 0–400 that comes before the `step_start` also give 700 ms.
3. `permission_denials`: a run with a `tool_use` of `status` `error` whose error is `exit 1`, followed by a `tool_use` refused with `permission denied by rule git push*`, lists exactly one denial, the second, with detail `{"command": "git push"}`. A row with the two events in the other order lists the same one denial.
4. The second call's words, one parametrized test:
   - a run stopped at its budget (one `step_finish` of cost 1.2 against a budget of 1, session `ses_a`, the builders' `SESSION`) and resumed: the arguments the stand-in records for the second call are exactly `run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_a <FINISH_MESSAGE>`;
   - a request with `resume_session` `ses_r` and prompt `Go on.`: the arguments the stand-in records are exactly `run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_r Go on.`.
5. As agent user `agent` with a stand-in `sudo`: a stand-in that prints a `step_start` (session `ses_a`, the builders' `SESSION`) and then sleeps past a time limit of 3 seconds ends `time_limit`, with `session` `ses_a` and `login` `api_key` when the API login file holds a key. The elapsed time stays below 20 seconds. A row whose stand-in exits 137 at once, before its time limit, ends `died`.
6. With the write guard's wrapper `factory-confine` (`CONFINE` of `tests/confine_support.py`, which makes the run's temporary folder) and the layout's temporary root, the root is empty after the run, in three rows: a completed run, a run whose stand-in exits 1 without events (`died`), and a run past a time limit of 3 seconds (`time_limit`). With the agent user `agent`, a stand-in `sudo` and the stand-in confine executable of `write_confine`, the last call the stand-in `sudo` records is `-n -u agent -- /bin/sh -c`, then `CLEANUP_SCRIPT`, `factory-cleanup` and `<temporary root>/factory-run-<run>`, `<run>` being the id in the name of the configuration file the call was given (`opencode-<run>.json`).
7. `make check` stays green.
8. docs: none. The behaviour is already described in `docs/project-guide/agents.md` (*The opencode runtime*) and `docs/operator-guide.md` (*Running on opencode*). The documenter checks that those passages say each of the six rules above, and adds the one that is missing.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir "$d/work" "$d/state"
cat > "$d/opencode" <<'EOF'
#!/bin/sh
here=$(dirname "$0")
n=$(cat "$here/count" 2>/dev/null || echo 0); n=$((n + 1)); echo "$n" > "$here/count"
printf '%s\n' "$*" >> "$here/arguments"
case "$n" in
1)
  printf '%s\n' '{"type":"step_start","timestamp":1000,"sessionID":"ses_s","part":{"type":"step-start"}}' '{"type":"tool_use","timestamp":1150,"sessionID":"ses_s","part":{"type":"tool","tool":"bash","state":{"status":"error","input":{"command":"false"},"error":"exit 1","time":{"start":1100,"end":1200}}}}' '{"type":"tool_use","timestamp":1500,"sessionID":"ses_s","part":{"type":"tool","tool":"bash","state":{"status":"error","input":{"command":"git push"},"error":"permission denied by rule git push*","time":{"start":1300,"end":1500}}}}' '{"type":"step_finish","timestamp":2000,"sessionID":"ses_s","part":{"type":"step-finish","cost":1.2,"tokens":{"input":1,"output":1}}}'
  sleep 30 ;;
*)
  printf '%s\n' '{"type":"text","timestamp":3050,"sessionID":"ses_s","part":{"type":"text","text":"<factory-result>\ndecision: question\nentry:\nFirst line.\n\nThird line.\n</factory-result>"}}' '{"type":"step_start","timestamp":3000,"sessionID":"ses_s","part":{"type":"step-start"}}' '{"type":"step_finish","timestamp":3100,"sessionID":"ses_s","part":{"type":"step-finish","cost":0.1,"tokens":{"input":1,"output":1}}}' ;;
esac
EOF
chmod +x "$d/opencode"
uv run -q python - "$d" <<'EOF'
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.agent_launch import FINISH_MESSAGE
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest

d = Path(sys.argv[1])
agent = AgentDefinition(name="coder", model="anthropic/claude-sonnet-5-5", tools=["Bash"], budget_usd=Decimal("1"), instructions="Smoke.")
request = AgentRunRequest(agent=agent, prompt="Smoke.", allowed_decisions=["question"], time_limit=timedelta(seconds=120), working_directory=d / "work", environment={"PATH": "/usr/bin:/bin"})
result = OpencodeRuntime(str(d / "opencode"), d / "state").run(request)
print(result.end_reason, repr(result.entry), result.model_duration.total_seconds(), [denial.detail for denial in result.permission_denials])
print((d / "arguments").read_text(encoding="utf-8").splitlines()[1].removesuffix(" " + FINISH_MESSAGE))
EOF
```
Expect: two lines, `completed 'First line.\n\nThird line.' 0.8 ['{"command": "git push"}']` and `run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_s`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
