---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 279
comments_read: [6274821134]
handed_over: null
claim: null
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
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-19T18:52:57.471973Z'
  stage: intake
  run: 9d0bec5d8afa4c7792e39adcbfc114b0
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-19T18:54:15.537321Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-19T18:54:33.792706Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-19T18:54:56.744121Z'
  stage: intake
  run: da70974357284d00babbdff386044130
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-19T18:55:18.335098Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-19T18:59:50.703288Z'
  stage: tests
  run: badbf64777e04dc884bd2152e65d8d7f
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
   - a block whose first line is `question` (no `decision: ` label) and whose second line is `entry:` gives `None`;
   - a block whose second line is `entry: First line.` gives `None`;
   - a block whose entry is padded with blank lines and spaces around `First line.` gives `("question", "First line.")`.
2. `model_duration`, one parametrized test:
   - one step from `step_start` at 1000 to `step_finish` at 2000, with two `tool_use` events between them spanning 1100–1200 and 1300–1500, gives 700 ms;
   - the same events after a `tool_use` spanning 0–400 that comes before the `step_start` also give 700 ms.
3. `permission_denials`: a run with a `tool_use` of `status` `error` whose error is `exit 1`, followed by a `tool_use` refused with `permission denied by rule git push*`, lists exactly one denial, the second, with detail `{"command": "git push"}`. A row with the two events in the other order lists the same one denial. Further rows: a `tool_use` of `status` `error` whose error holds only `permission`, one whose error holds only `denied`, and one whose error is `Permission Denied`, are each listed as a denial; a `tool_use` whose `status` is not `error` although its text contains `denied` is not listed.
4. The second call's words, one parametrized test:
   - a run stopped at its budget (one `step_finish` of cost 1.2 against a budget of 1, session `ses_a`, the builders' `SESSION`) and resumed: the arguments the stand-in records for the second call are exactly `run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_a <FINISH_MESSAGE>`;
   - a request with `resume_session` `ses_r` and prompt `Go on.`: the arguments the stand-in records are exactly `run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_r Go on.`.
5. As agent user `agent` with a stand-in `sudo`: a stand-in that prints a `step_start` (session `ses_a`, the builders' `SESSION`) and then sleeps past a time limit of 3 seconds ends `time_limit`, with `session` `ses_a` and `login` `api_key` when the API login file holds a key. The elapsed time stays below 20 seconds. A row whose stand-in exits 137 at once, before its time limit, ends `died`. A row whose stand-in is killed with exit status `-9` past the time limit ends `time_limit`; a row whose stand-in exits 1 after the time limit is reached ends `died`.
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
3. intake: Format check passed. Questions, each a clause of the Interface with no criterion of its own (so a mutant on it would survive again):

   1. `permission_denials` (Interface, `DENIAL_PATTERN` = `permission|denied`, any case): criterion 3 plays only the lowercase text `permission denied by rule git push*`, which holds both words. Nothing tests that an error with only `permission` is a denial, that one with only `denied` is a denial, that the match is case-insensitive (`Permission Denied`), or that a `tool_use` whose `status` is not `error` but whose error text contains `denied` is not listed. Proposed: add rows to criterion 3 for each of the four.
   2. `KILL_STATUSES` is `{137, -9}` (`agent_launch.py:32`). Criterion 5 tests only 137, and only on the side "exits at once, before its time limit → `died`". Nothing tests `-9` as a kill status, nor the side "exit status not in `KILL_STATUSES` (e.g. 1) after the time limit is reached → not `time_limit`". Proposed: add a row with exit status `-9` ending `time_limit`, and a row that exits 1 after the limit and does not end `time_limit` (name the expected end reason).
   3. `parse_result_block`: "the second line is exactly `entry:`". Criterion 1 tests `note:` only; a second line such as `entry: text` or ` entry:` (the "exactly" side) has no row, and neither does the "stripped" clause (an entry with leading or trailing blank lines or spaces around the entry). Proposed: add rows for `entry: First line.` giving `None` and for an entry padded with blank lines giving the stripped text.
   4. Criterion 6 gives the cleanup under `sudo` only for the confine-and-agent-user case. The Interface says "as the agent user under `sudo` when one is set", which implies the other side (confine set, no `os_user`: the folder is removed without `sudo`). The no-sudo rows cover this only for the three end reasons. I judge this side covered; no change needed unless you want an explicit assertion that `sudo` is not called.

   The smoke test is runnable and its `Expect:` line checks out against the stand-in (0.8 s = 1000 − 100 − 200 plus 100; the first call's cost of 1.2 passes the budget of 1). The Interface, architecture (adapters-only, tests only, no `src` change) and scope (within the feature's S0004/S0006 behaviour, nothing in Out of scope) are fine apart from the questions above.
4. 2026-10-19 human: 1. Yes, add the rows to criterion 3 as you propose: an error with only `permission`, one with only `denied`, the case-insensitive `Permission Denied`, each listed as a denial; and a `tool_use` whose `status` is not `error` although its text contains `denied`, not listed.
   2. Yes: a row with exit status `-9` past the limit ending `time_limit`, and a row that exits 1 after the limit is reached ending `died` (`agent_launch.py:315`: a status outside `KILL_STATUSES` is never `time_limit`; with no result block the run is `died`).
   3. Yes: `entry: First line.` as the second line gives `None`, and an entry padded with blank lines and spaces gives the stripped text.
   4. No change; the no-sudo rows cover that side.
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete. It names `OpencodeRuntime.run` and `parse_result_block` in `factory.adapters.opencode_runtime`, the constants `DENIAL_PATTERN`, `KILL_STATUSES` and `FINISH_MESSAGE`, the exact argument words of a resumed call, and the four new test modules. No `src` change.
   - Criteria: I carried the human's answers (journal 4, items 1 to 3) into the story; the wording is mine, the content is theirs.
     - Criterion 1 gained a row for `entry: First line.` as the second line (gives `None`) and a row for an entry padded with blank lines and spaces (gives the stripped text).
     - Criterion 3 gained rows for an error with only `permission`, one with only `denied`, and `Permission Denied`, each listed; and a non-error `tool_use` whose text contains `denied`, not listed.
     - Criterion 5 gained a `-9` row past the limit (ends `time_limit`) and a row that exits 1 after the limit (ends `died`).
     - Item 4 of the human's answer changed nothing: the no-sudo rows of criterion 6 cover that side.
     - Every Interface rule now has a criterion on both its passing and failing side. Each criterion is one test function, or one parametrized test.
   - Smoke test: runnable. The stand-in `opencode` plays two calls. The first costs 1.2 against a budget of 1, so the runtime stops it and resumes with `--session ses_s`. The `Expect:` line is checkable against the output: 0.8 s model time (1000 less 100 less 200, plus 100), one denial `{"command": "git push"}`, and the resumed words.
   - Architecture: tests only, in the adapters mirror under `tests/adapters/`. The stand-in and the builders in `opencode_stand_in.py` and `confine_support.py` are imported, not copied. No layer is touched.
   - Scope: within F0020's S0004 and S0006 behaviour and decisions 7, 8, 11 and 18. Nothing in "Out of scope". No earlier test changes.
7. factory: started tests as self.
8. tester: Wrote the tests for criteria 1 to 6. They import the stand-in, the event builders and the confine helpers rather than copying them. No earlier test file changed.

   Mapping:
   - criterion 1: tests/adapters/test_opencode_measures.py::test_a_result_block_keeps_its_entry_s_lines_and_needs_both_labels (rows: lines-kept, no-entry-label, no-decision-label, entry-on-its-label, padded)
   - criterion 2: tests/adapters/test_opencode_measures.py::test_the_model_time_takes_off_every_tool_call_of_its_step (rows: two-tool-calls, tool-call-before-the-step; both expect exactly 700 ms)
   - criterion 3: tests/adapters/test_opencode_measures.py::test_every_refused_tool_call_is_a_denial_and_no_other (rows: failure-then-denial, denial-then-failure, permission, denied, any-case, not-an-error)
   - criterion 4: tests/adapters/test_opencode_resumed_words.py::test_a_resumed_call_keeps_every_word_of_the_first_before_its_session (rows: budget-resume, resume-session)
   - criterion 5: tests/adapters/test_opencode_sudo_time_limit.py::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login (rows: killed-at-the-limit, 137-at-once, sigkill-past-the-limit, status-1-past-the-limit; time limit 3 s, elapsed below 20 s)
   - criterion 6: tests/adapters/test_opencode_confinement.py::test_through_the_wrapper_the_temporary_root_is_empty_after_the_run (rows: completed, died, time-limit, through the real `CONFINE`) and tests/adapters/test_opencode_confinement.py::test_with_an_agent_user_the_temporary_folder_is_removed_through_sudo (stand-in `write_confine` and stand-in `sudo`)

   Files created: the four test modules above.

   How the tests are built:
   - **Criterion 5, the `-9` and exit-1 rows.** These rows need an exit status that arrives after the limit, and the real inner `timeout` would kill the call at the limit first. So both rows use a local stand-in `sudo` (`ENDING_SUDO`) that runs nothing. It prints a `step_start`, waits 4.5 s (past the 3 s limit, inside the 30 s grace `sudo` calls get) and then kills itself with SIGKILL or exits 1. The other two rows use the existing `_write_sudo` of `test_claude_runtime_os_user`, which runs the real `timeout` chain.
   - **Criterion 5, session and login.** Only the killed-at-the-limit row checks `session` (`ses_a`) and `login` (`api_key`), as the criterion says. The other rows check only their end reason.
   - **Criterion 6.** The test makes the layout's `state` folder itself. The run id comes from the `OPENCODE_CONFIG` file name the stand-in recorded.

   Test run: one `make test`, which ended `test: green`. Since the story changes no code, all the new tests pass, as expected; none fail. No module was missing at import. `make lint` is green. I also ran `make types`, which is green.

   Open: none.

   `lint`: lint: green (0.0 s)
   `test`: test: green (52.5 s)
