---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 281
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T19:18:02.950126Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T19:53:43.591707Z'
  stage: acceptance
  run: a93fa77b95bc4ed98e016530f9c08f4c
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-19T20:00:12.583756Z'
  stage: done
stories: [F0020-S0001, F0020-S0002, F0020-S0003, F0020-S0004, F0020-S0005, F0020-S0006, F0020-S0007, F0020-S0008, F0020-S0010, F0020-S0011, F0020-S0012]
outcome: accepted
---

# Acceptance of opencode as a second agent runtime

## Recommendation

**accepted.** This second acceptance covers the three stories the first one proposed (S0010, S0011, S0012) on top of S0001 to S0008. All three did what they set out to do:

- the survivors they targeted in `process._LineReader` and `opencode_runtime` are now killed;
- the six operator-guide passages are corrected;
- `make check` is green, and the feature's smoke test is green end to end on opencode.

What is left is small. Two survivors on the path a provider limit takes (a wait named on standard error, a stop on a stream's last line) are untested, though the code is right. Three operator-guide passages still speak only of Claude Code. I propose one tests-only story and one docs-only story for these. `make mutants` stayed partial after three runs (935 of 4985 mutants not checked), as in the first acceptance.

## 1 Scope

None. Every Scope item tagged S0001 to S0008 was built, as the first acceptance (`done/F0020-A0001-acceptance.md`) found. The three new stories stay inside the Scope:

- S0010 adds tests only, against `opencode_runtime` (decisions 7, 8, 11 and 18);
- S0011 changes `docs/operator-guide.md` only;
- S0012 adds tests only, against `process.run_streaming` (decision 5), with one sentence in `docs/project-guide/processes-and-checks.md`.

None of them changed code under `src/`.

S0009 (`FACTORY_SPEND_WINDOW`, `domain/spend.py`) is still deferred by decision 15 and is not a gap. Two points from the first acceptance stand:

- `feature.md` says S0009's file lies in `deferred/` beside `backlog/`, but it lies in `planning/`;
- the goal's real test, the todo demo on opencode through the API (change 6), is the human's.

The first acceptance's proposals took S0009 to S0011 and were renumbered S0010 to S0012 when merged. The deferred S0009 keeps its number.

## 2 Feature smoke test

The operator's walk-through: an instance put on opencode with an API key, behind a spend limit, with a long event stream. The steps:

1. The settings choose `FACTORY_AGENT_RUNTIME=opencode` with the image's model ids, and `build_boundaries` wires the runtime.
2. A stage's run through `PatientRuns` streams a `tool_use` event of 150 000 bytes (more than two 64 KiB reads).
3. The gateway's 428 arrives on standard error and names a wait of 120 s. The run waits it out on a manual waiter and resumes the session.
4. The resume passes the budget that is left, so the runtime stops at the budget and resumes once with the finish message. A `git push` is refused along the way.
5. The run ends with a result block whose entry has several lines.

The agent lists `Skill` first among its tools. `opencode` is a stand-in that plays opencode's events: no paid call, no `sudo`, no confinement.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/work" "$d/home/.claude" "$d/state/runs"
printf 'sk-ant-smoke\n' > "$d/api-key"
printf '%s' '{"permissions":{"deny":["Bash(git push:*)"]}}' > "$d/home/.claude/settings.json"
cat > "$d/opencode" <<'EOF'
#!/bin/sh
here=$(dirname "$0")
n=$(cat "$here/count" 2>/dev/null || echo 0); n=$((n + 1)); echo "$n" > "$here/count"
printf '%s|key=%s|config=%s\n' "$*" "${ANTHROPIC_API_KEY:-none}" "$(test -f "$OPENCODE_CONFIG" && echo yes || echo no)" >> "$here/calls"
big=$(head -c 150000 /dev/zero | tr '\0' 'y')
case "$n" in
1)
  printf '%s\n' '{"type":"step_start","timestamp":1000,"sessionID":"ses_walk","part":{"type":"step-start"}}'
  printf '{"type":"tool_use","timestamp":1150,"sessionID":"ses_walk","part":{"type":"tool","tool":"bash","state":{"status":"completed","input":{"command":"cat big"},"output":"%s","time":{"start":1100,"end":1200}}}}\n' "$big"
  printf '%s\n' '{"type":"step_finish","timestamp":1300,"sessionID":"ses_walk","part":{"type":"step-finish","cost":0.25,"tokens":{"input":10,"output":5}}}'
  echo "AI_APICallError: 428 spend limit reached, retry after 120 seconds" >&2
  sleep 30 ;;
2)
  printf '%s\n' '{"type":"step_start","timestamp":2000,"sessionID":"ses_walk","part":{"type":"step-start"}}' '{"type":"tool_use","timestamp":2150,"sessionID":"ses_walk","part":{"type":"tool","tool":"bash","state":{"status":"error","input":{"command":"git push"},"error":"permission denied by rule git push*","time":{"start":2100,"end":2200}}}}' '{"type":"step_finish","timestamp":2500,"sessionID":"ses_walk","part":{"type":"step-finish","cost":2.0,"tokens":{"input":20,"output":7}}}'
  sleep 30 ;;
*)
  printf '%s\n' '{"type":"step_start","timestamp":3000,"sessionID":"ses_walk","part":{"type":"step-start"}}' '{"type":"text","timestamp":3050,"sessionID":"ses_walk","part":{"type":"text","text":"<factory-result>\ndecision: approval\nentry:\nBuilt it.\n\nNothing open.\n</factory-result>"}}' '{"type":"step_finish","timestamp":3100,"sessionID":"ses_walk","part":{"type":"step-finish","cost":0.1,"tokens":{"input":3,"output":2}}}' ;;
esac
EOF
chmod +x "$d/opencode"
uv run -q python - "$d" <<'EOF'
import sys
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.clock import ManualClock, ManualWaiter
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.machine import FactoryLog
from factory.application.provider_limits import PatientRuns
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from factory.domain.settings import read_settings
from factory.entry.wiring import build_boundaries


class Lines(FactoryLog):
    def __init__(self) -> None:
        self.lines: list[str] = []

    def line(self, text: str) -> None:
        self.lines.append(text)


d = Path(sys.argv[1])
environ = {
    "FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "walk",
    "FACTORY_AGENT_RUNTIME": "opencode", "FACTORY_OPENCODE": str(d / "opencode"),
    "FACTORY_API_LOGIN_FILE": str(d / "api-key"),
    "FACTORY_OPENCODE_MODELS": "opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,haiku=anthropic/claude-haiku-5-5",
}
settings = read_settings(environ).model_copy(update={"checkout": d / "checkout", "state_directory": d / "state", "agent_home": d / "home" / ".claude"})
built = build_boundaries(settings, "", hosting=FakeHostingService(), confine_executable=None)
clock = ManualClock(datetime(2026, 10, 19, tzinfo=UTC))
waiter = ManualWaiter(clock)
log = Lines()
boundaries = replace(built, waiter=waiter, clock=clock, log=log)
print(type(boundaries.agent_runtime).__name__, settings.opencode_models["sonnet"], settings.provider_limit.status)
agent = AgentDefinition(name="coder", model="sonnet", tools=["Skill", "Read", "Bash"], budget_usd=Decimal("2"), instructions="Build it.")
request = AgentRunRequest(agent=agent, prompt="Build it.", allowed_decisions=["approval", "question"], time_limit=timedelta(seconds=120), working_directory=d / "work", environment={"PATH": "/usr/bin:/bin"})
started = time.monotonic()
result = PatientRuns(boundaries).run(request)
print(result.end_reason, result.decision, repr(result.entry), result.cost_usd, result.turns, result.login, result.session, time.monotonic() - started < 25)
print([denial.detail for denial in result.permission_denials])
print([w.total_seconds() for w in waiter.waits], log.lines)
for call in (d / "calls").read_text(encoding="utf-8").splitlines():
    print(call)
print(sorted(p.name for p in (d / "state" / "runs").iterdir()))
EOF
```

Output (green):

```text
OpencodeRuntime anthropic/claude-sonnet-5-5 428
completed approval 'Built it.\n\nNothing open.' 2.35 3 api_key ses_walk True
['{"command": "git push"}']
[120.0] ['provider limit: coder waits 120 s before it resumes ses_walk']
run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder Build it.|key=sk-ant-smoke|config=yes
run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_walk The provider's spend limit stopped your run. Continue the work where you stopped, then end as your instructions say.|key=sk-ant-smoke|config=yes
run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_walk Finish now: give your decision (question if the work is not done) and your entry.|key=sk-ant-smoke|config=yes
[]
```

What the output shows:

- the long event line passed through the stream whole;
- the 428 on standard error gave the named wait of 120 s, not the cool-down;
- `PatientRuns` resumed the session with the continue prompt;
- the resume ran over the $1.75 that was left, so the runtime stopped it and resumed once more with the finish message;
- the cost is the sum of the three calls ($0.25 + $2.00 + $0.10);
- the denial was read, the multi-line entry kept its blank line, the key reached every call, and the run files were removed.

The default runtime and a refused one, run the same way:

```text
claude ClaudeCodeRuntime
refused: FACTORY_AGENT_RUNTIME: holds codex, which is neither claude nor opencode
```

## 3 Mutation score

The run is partial. `make mutants` (acceptance branch, 22 modules, 4985 mutants) ran three times, and each was stopped after 540 s. Their last lines:

```text
mutants: partial, 3762 killed, 148 survived, 3 timed out, 0 without tests, 1072 not checked, 0 other of 4985 mutant(s) in 22 module(s) (stopped after 540 s)
mutants: partial, 3788 killed, 151 survived, 3 timed out, 0 without tests, 1043 not checked, 0 other of 4985 mutant(s) in 22 module(s) (stopped after 540 s)
mutants: partial, 3896 killed, 151 survived, 3 timed out, 0 without tests, 935 not checked, 0 other of 4985 mutant(s) in 22 module(s) (stopped after 540 s)
```

**Score on what was checked:** 3896 killed of 4050 (96.2 %), with 151 survived and 3 timed out. The 3 timeouts are the same as in the first acceptance: `_Watch._stop_at_limit` 1 and `ClaudeCodeRuntime.version` 4 and 7.

Unlike in the first acceptance, every run made progress. The not-checked mutants went from 1875 then to 935 now, about 100 fewer per run. So more acceptance runs would finish the list. Making each run reach further is a change to `Makefile` or `[tool.mutmut]`, which are the human's.

**What the stories since the first acceptance killed.** The first acceptance's two groups are gone:

- `_LineReader.read_ready`'s two `+= chunk` mutants (S0012);
- the opencode runtime's 64 survivors: the resumed call's words, the kill under `sudo`, the folder removal, the multi-line entry, the model time over several tool calls, and denials after an ordinary error (S0010). 26 remain.

None of these stories changed code, so no coder entry carries a mutation line, and no review passed on a group as a note.

**Survivors by group** (`uv run mutmut show` of each in the opencode runtime, process and the feature's domain and application code):

- **New, a story (S0013).** These lie on the path a provider limit takes:
  - `opencode_runtime._Watch.on_line`: `_stop_at_limit(line)` → `_stop_at_limit(None)`. A limit line on standard error that names a wait is never tested for its `limit_wait`; the only test plays a line with no wait.
  - `process._LineReader.read_ready`: the `return True` after `_pass_last_line` → `False`. A stop on a stream's last line without a newline is not tested.

  The code is right in both cases (see 2, and S0013's smoke test, which I ran: `provider_limit 0:02:00` and a stop within a second).
- **New, a note.** `opencode_runtime._tools`: `continue` → `break`. An agent whose `tools` list `Skill` before other tools would lose those tools. Every shipped agent lists `Skill` last, and `tests/adapters/test_opencode_left_out_tools.py` has a row `read-and-skill` but no row with `Skill` first. One row in that module, which another story wrote, so it needs the human's leave.
- **Equivalent or unreachable, as the first acceptance judged.**
  - `opencode_runtime`: `_resume` 11 (the `left <= 0` branch needs a clock); `_end_reason` 2 (its `time_limit` branch is unreachable); `_span_ms`, `_steps`, `_answer`, `_read`, `_denials` 3 and `__init__` (`and`/`or` swaps on `None` checks that a valid event never reaches); `_write_files` and `_deny_list` (encoding); `parse_result_block` 2 (`len(block) < 2` → `<= 2`/`< 3`, where a two-line block has a blank entry and is refused anyway); `_model_ms` (`tools = 0` → `1`); `_result` (the sum's `Decimal(0)` start); `_call` (`timed_out=None`); `_limit_wait` (`or` → `and`).
  - `process._read_until_end` (`return False, True` → `False, False`).
  - `claude_runtime` 16: `_resume` without time left, `_resume_arguments`' formatting, the `version` error text, and the encoding in `_write_files`.
- **Small, listed in the first acceptance and still open; no story.**
  - `provider_limits.named_wait` (`> 0` → `> 1`);
  - `agent_runs.resumed_result` (the key `"session"` misspelt);
  - `settings._opencode_model` (`partition` → `rpartition`; this shows only on `a=b=c/d` or `a/b/`);
  - `preflight._opencode_login_hint`'s fallback `the factory user`;
  - `wiring._agent_runtime` dropping `sudo_executable`.
- **Earlier features' code, outside F0020.**
  - in `settings`: `_holds_password` 7, `_repository_url` 6, `_name` 3 and `read_setting_file` 2;
  - `contract` 3;
  - `stage.run`, `finish`, `_stall`, `_stall_red`, `_commit_and_push`, `_masked`, `_moved` and `__init__`, mostly `require_state(..., None)` and arguments never compared;
  - `journal` 4, `post_texts` 4, `clock._refuse_negative` 1, `cost_records_jsonl._refuse_constant` 1;
  - the rest of `wiring` and `preflight`.

## 4 What the stories noticed

From the coder, reviewer, tester, documenter and smoke-tester entries of S0010, S0011 and S0012. The first acceptance's list (its section 4) stands for S0001 to S0008.

- **S0011's documenter** left three Claude-only passages of the operator guide: the opening paragraph's "the `claude -p` runtime", *The agent runs as a second user* (its `sudo` chain ends in `claude`), and *`factory-guard` on the agent run's `PATH`* (the hook, with nothing on opencode). Its smoke tester named the same passages. The documenter also named the `claude-home` volume text, which describes Claude Code's own volume correctly. → **S0014**.
- **S0010's coder and reviewer** saw that `test_opencode_sudo_time_limit.py` and `test_opencode_confinement.py` import the private `_write_sudo` and `_sudo_calls` from `tests/adapters/test_claude_runtime_os_user.py`, as two earlier opencode test modules already did. Moving them to a shared module is the tester's standing leave in any later story that touches them. No story of its own.
- **S0010's reviewer**: `_runtime` in `test_opencode_confinement.py` builds the runtime in two branches that differ in one argument. This is small and inside a new test module.
- **`make duplicates`** after every coder of S0010 to S0012 said `5 new, 33 known, 3 gone`, and the reviewers rightly said the findings were not their diffs'. I ran it: all five are F0020's.
  - Four are similar blocks between `claude_runtime` and `opencode_runtime` (`call_refusal`, `cleanup_launch`, `version_printed`, the confine branch). The first acceptance said why they stay (decision 4: `agent_launch` may not import the process module).
  - One is `ManualWaiter`, which vulture calls unused at 60 % because only tests and wiring by name use it.

  The three `gone` entries (`ManualClock`, `advance`, `work_item_markdown`'s `data`) are stale lines of `security/duplicates-baseline.txt`. Accepting the five and dropping the three is the human's edit of the baseline.
- **S0012** noticed nothing.

## 5 The documentation as a whole

I read `README.md`, `docs/operator-guide.md` (configuration, *The agent runtime* through *The machine's image*, the preflight's items) and `docs/project-guide/` (`agents.md`, `processes-and-checks.md`, `write-guard.md`).

S0011's six passages now agree with *Running on opencode* and with the code. `README.md` names both runtimes. `docs/project-guide/processes-and-checks.md` no longer names a story in its running text (a note of the first acceptance). `agents.md` now states the six rules S0010 pinned.

Left over, none of them contradicts the behaviour in a way that breaks an instance:

- The operator guide's opening paragraph lists "the `claude -p` runtime" among the built parts, and not opencode's.
- *The agent runs as a second user* shows only the chain that ends in `claude`. Under opencode the same chain starts `opencode run`.
- *`factory-guard` on the agent run's `PATH`* does not say that an opencode run registers no hook. Yet the item `agent-environment` checks `factory-guard` on the `PATH` under either runtime (`factory.entry.wiring.machine_extras` adds it unconditionally). An operator of an opencode instance may wonder why a Claude Code hook must be on the `PATH`.

→ **S0014**.

`docs/project-guide/write-guard.md` does not name opencode. It describes the confinement generically (`extras`, "the runtime's own paths"), and `agents.md` names opencode's folders, so this is not a gap.

The examples I ran are the feature smoke test above and the smoke tests of the two proposed stories. I did not rerun every example of the guides.

## 6 Decisions taken for the human

**From `feature.md`, decisions 1 to 23**, unchanged since the first acceptance, which lists them one by one (its section 6). The human's changes 4 (the cross-check of `factory-guard`'s refusals against the kernel's) and 6 (the paid todo-demo run on opencode) are still due by the human's hand.

**Answers and defaults recorded in the journals since the first acceptance:**

- S0010, intake question, answered in journal entry 4. All four answers were carried into the story:
  1. three more denial rows (`permission` alone, `denied` alone, `Permission Denied`) and a non-error `tool_use` that is not a denial;
  2. a `-9` row past the limit ending `time_limit`, and an exit-1 row past the limit ending `died`;
  3. `entry: First line.` as the second line gives `None`, and a padded entry gives the stripped text;
  4. no explicit no-`sudo` assertion.
- S0011 and S0012: no question; the intake accepted both as written.

**Earlier tests changed, each with its leave.** No change without a named leave was found.

- S0012: `Recorder` moved from `tests/adapters/test_process_streaming.py` to `tests/process_support.py`, and the first module imports it. This was under the standing leave of `CLAUDE.md`, named in the story's Interface and in the tester's and reviewer's entries.
- S0010 and S0011 changed no earlier test (S0010's reviewer read `git diff --name-status`: added files only).
- The list for S0001 to S0008 is the first acceptance's.

## 7 The slow checks

The project offers nothing beyond `make check` and `make mutants` (no image scan, no SBOM).

`make check` was green as found. `make test` took 54.0 s for 5974 tests (635.0 s of test time across the workers). The slowest tests, from `.reports/junit.xml`:

- `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` (5.0 s);
- `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` (5.0 s);
- `test_fault_paths_7_to_13::test_acceptance_container_lost_in_review_reruns_once_and_books_result[accepted]` (5.0 s);
- S0010's two rows `test_opencode_sudo_time_limit::...[sigkill-past-the-limit]` and `[status-1-past-the-limit]` (4.5 s each). They wait 4.5 s past a 3 s limit by design.

**Disk.** Now: `/work` 977.0 GB free, 0.5 GB used; `/state` 977.0 GB free, 0.0 GB used; `/tmp` 977.0 GB free, 0.0 GB used. At the previous record (`disk acceptance`, the first acceptance's): 977.2 GB free and the same use, to the tenth.

The 0.2 GB less free space is not in any of the three folders' use. It is the shared host file system, and `mutants/` (59 MB, a working folder) accounts for part of it. No growth the feature does not explain.

## 8 Cost

The stories cost 134 runs, 187.4 min, 1280 turns and $51.64. Per story, from the sidecars:

| Story | Runs | Dollars | Minutes |
|---|---|---|---|
| S0001 | 11 | $5.84 | 16.8 |
| S0002 | 10 | $3.16 | 10.6 |
| S0003 | 11 | $2.77 | 11.8 |
| S0004 | 19 | $10.01 | 37.5 |
| S0005 | 21 | $8.43 | 31.6 |
| S0006 | 15 | $5.43 | 23.3 |
| S0007 | 14 | $5.10 | 16.9 |
| S0008 | 14 | $6.75 | 23.9 |
| S0010 | 7 | $2.33 | 7.8 |
| S0011 | 6 | $0.85 | 3.6 |
| S0012 | 6 | $0.96 | 3.8 |

Every run ended `completed`.

**The three stories since the first acceptance** cost 19 runs and $4.14 together, each with one round and no rework. S0010 is the largest of them ($2.33): four test modules and one intake question. S0004 ($10.01, the whole runtime and two secrets stops) and S0005 (21 runs, past its round cap) still stand out for the reasons the first acceptance gave. The first acceptance itself cost $3.95.

**Human interventions:** 12 questions answered (11 questions, 1 round cap), and the stories waited 0.3 h for them. The one new question is S0010's intake question, answered within two minutes. By story:

| Story | Questions |
|---|---|
| S0003 | 1 |
| S0004 | 3 |
| S0005 | 3 |
| S0007 | 2 |
| S0008 | 2 |
| S0010 | 1 |

S0004 and S0005 needed the human most:

- S0004 for two secrets-detector stops that no agent could clear;
- S0005 for an earlier test the contract's version rise broke, and for the round cap.

## Proposed stories

- `F0020-S0013-a-limit-s-wait-on-standard-error-and-a-stop-on-a-stream-s-last-line-are-pinned.md`: tests only. It pins the two new survivors on the path of a provider limit:
  - the wait a limit line on opencode's standard error names becomes `limit_wait` (decision 12);
  - `run_streaming` stops at once on a stream's last line without a newline.
- `F0020-S0014-the-operator-guide-s-last-claude-only-passages-name-opencode.md`: docs only. It corrects the three operator-guide passages that S0011's documenter left: the opening paragraph, *The agent runs as a second user* and *`factory-guard` on the agent run's `PATH`*.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 2 stories proposed; make mutants 3896/4050 (partial: 935 of 4985 not checked after three runs, 151 survived, 3 timed out)

   The three stories since the first acceptance (S0010, S0011, S0012) did what they set out to do. Their targeted survivors are now killed, and the six passages of the operator guide are corrected. `make check` is green, and the feature smoke test is green end to end on opencode. What is left: two small test gaps on the path a provider limit takes, and three operator-guide passages that still speak only of Claude Code.

   1. Scope: no gap. S0010 and S0012 add tests and S0011 changes docs, all inside the Scope; none changed `src/`. S0009 is still deferred (decision 15), and `feature.md` still places its file in `deferred/` when it lies in `planning/`.
   2. Feature smoke test: green. An opencode instance on an API key goes through the settings, `build_boundaries` and `PatientRuns`. It streams a 150 000-byte event and hits a 428 on standard error, waits out the named 120 s and resumes the session. The resume passes the budget that is left, so the runtime stops it and resumes once more. The run ends `completed` at $2.35 with a multi-line entry, one denial and login `api_key`, and leaves no run files. The default runtime is `claude`, and `codex` is refused.
   3. Mutation score: 96.2 % on what was checked, partial after three runs. Unlike in the first acceptance, each run made progress (1875 → 935 not checked). S0010 and S0012 killed the first acceptance's two groups. New groups: a wait named on opencode's standard error is untested, and so is a stop on a stream's last line without a newline (S0013). `_tools` with `Skill` listed first is a note. The rest is equivalent, small and already listed, or earlier features' code.
   4. What the stories noticed: S0011's documenter left three Claude-only passages (S0014). The opencode tests import private sudo helpers from a Claude Code test module (the tester's standing leave). `make duplicates` shows 5 new findings, all F0020's (the runtimes' shared blocks, `ManualWaiter`), and 3 stale baseline lines; the baseline is the human's.
   5. Documentation: S0011's passages agree with the code, and `README.md` names both runtimes. Three passages still speak only of Claude Code: the guide's opening paragraph, *The agent runs as a second user*, and *factory-guard on the agent run's PATH* (whose item `agent-environment` is checked under either runtime) (S0014). None of them misleads an operator into a broken instance.
   6. Decisions: decisions 1 to 23 are unchanged, and the human's changes 4 and 6 are still due. New: S0010's four intake answers. Earlier tests changed: S0012 moved `Recorder` to `tests/process_support.py` under the standing leave, named in its story. No change without a leave was found.
   7. Slow checks: none beyond `make check` and `make mutants`. `make test` took 54.0 s for 5974 tests. The slowest are the 5.0 s time-limit tests and S0010's two 4.5 s sudo rows, which wait on purpose. Disk: free space is down 0.2 GB on the shared host file system, with no growth in the folders' use; `mutants/` holds 59 MB.
   8. Cost: 134 runs, 187.4 min, $51.64. S0010 to S0012 cost 19 runs and $4.14, each with one round and no rework. S0004 ($10.01) and S0005 (21 runs) still stand out, as the first acceptance said. The human answered 12 questions (11 questions, 1 round cap) and the stories waited 0.3 h. The one new question was S0010's intake question, answered within two minutes. S0004 and S0005 needed the human most, three times each.
3. factory: done (pull request merged); cost: 1 runs, 35.6 min, 52 turns, 132583 tokens in (4354534 more from cache), 40549 out, $2.74
