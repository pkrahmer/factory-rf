---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 300
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T23:20:01.115626Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T23:27:39.825829Z'
  stage: acceptance
  run: 58eaed07411143c8b07b723b48ca2114
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-19T23:28:59.429083Z'
  stage: done
stories: [F0020-S0001, F0020-S0002, F0020-S0003, F0020-S0004, F0020-S0005, F0020-S0006, F0020-S0007, F0020-S0008, F0020-S0010, F0020-S0011, F0020-S0012, F0020-S0013, F0020-S0014]
outcome: accepted
---

# Acceptance of opencode as a second agent runtime

## Recommendation

**accepted with stories.** This third acceptance covers the two stories the second one proposed: S0013 (tests only) and S0014 (docs only). Both did what they set out to do. `make check` is green, and the feature's smoke test is green end to end on opencode, including the two paths S0013 pinned: a limit line on standard error that names a wait, and a stop on a stream's last line without a newline.

What is left is small, and no promise is broken. *The agent runs as a second user* in the operator guide still describes the login shell as Claude-only and subscription-only. That contradicts the guide's own list of login-shell points and the code. Nine test modules still copy the opencode stand-in's reply, which S0013 moved into one place for its own module only. I propose one docs-only story and one tests-only story for these.

## 1 Scope

None. Every Scope item tagged S0001 to S0008 was built, as the first acceptance (`done/F0020-A0001-acceptance.md`) found, and S0010 to S0012 stayed inside the Scope (`done/F0020-A0002-acceptance.md`). The two new stories also stay inside the Scope:

- S0013 adds two test modules, `tests/adapters/test_opencode_limit_wait_on_stderr.py` and `tests/adapters/test_process_streaming_last_line.py`. It adds `REPLY` to `tests/adapters/opencode_stand_in.py` and one sentence to `docs/project-guide/processes-and-checks.md`. It changes nothing under `src/`.
- S0014 changes `docs/operator-guide.md` only, in its three named passages.

The goal (an instance on opencode instead of Claude Code, under an API key and a gateway's spend limit, with the pipeline unchanged) is reached by the code, as section 2 shows. Its real test is the todo demo on opencode through the API (the human's change 6), which is the human's to run. S0009 (`FACTORY_SPEND_WINDOW`) is still deferred by decision 15 and is not a gap. One correction stands from the earlier acceptances: `feature.md` says S0009's file lies in `deferred/` beside `backlog/`. The feature folder has no `deferred/`, and I found no S0009 file in the checkout outside `mutants/`, a working folder that is not tracked. Correcting that sentence is the human's edit of `feature.md`.

## 2 Feature smoke test

This is the operator's walk-through: an instance put on opencode with an API key, behind a gateway's spend limit, through the real wiring and `PatientRuns`. The steps:

1. The settings choose `FACTORY_AGENT_RUNTIME=opencode` with the image's model ids and a cool-down of 5 minutes, and `build_boundaries` wires the runtime.
2. The first call streams a `tool_use` event of 150 000 bytes. On standard error it prints a line with status `4281`, which is no limit, then a 428 line that names "7 minutes".
3. The resumed call prints a 428 line on standard error without a newline, closes standard error and sleeps with standard output open. That is S0013's last-line stop: the line names no wait, so the cool-down applies.
4. The next resume runs past the budget that is left, with a `git push` refused, so the runtime resumes once more with the finish message.
5. The run ends with a multi-line entry.

`opencode` is a stand-in that plays opencode's events: no paid call, no `sudo`, no confinement.

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
  echo "HTTP 4281 Precondition Required, retry after 99 seconds" >&2
  echo "HTTP 428 Precondition Required: try again in 7 minutes" >&2
  sleep 30 ;;
2)
  printf '%s\n' '{"type":"step_start","timestamp":2000,"sessionID":"ses_walk","part":{"type":"step-start"}}'
  printf '%s' "HTTP 428 Precondition Required" >&2
  exec 2>&-
  sleep 30 ;;
3)
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
from factory.domain.settings import SettingsInvalid, read_settings
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
    "FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES": "5",
    "FACTORY_OPENCODE_MODELS": "opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,haiku=anthropic/claude-haiku-5-5",
}
settings = read_settings(environ).model_copy(update={"checkout": d / "checkout", "state_directory": d / "state", "agent_home": d / "home" / ".claude"})
built = build_boundaries(settings, "", hosting=FakeHostingService(), confine_executable=None)
clock = ManualClock(datetime(2026, 10, 19, tzinfo=UTC))
waiter = ManualWaiter(clock)
log = Lines()
boundaries = replace(built, waiter=waiter, clock=clock, log=log)
print(type(boundaries.agent_runtime).__name__, settings.opencode_models["sonnet"], settings.provider_limit.status, settings.provider_limit.cooldown)
agent = AgentDefinition(name="coder", model="sonnet", tools=["Skill", "Read", "Bash"], budget_usd=Decimal("2"), instructions="Build it.")
request = AgentRunRequest(agent=agent, prompt="Build it.", allowed_decisions=["approval", "question"], time_limit=timedelta(seconds=120), working_directory=d / "work", environment={"PATH": "/usr/bin:/bin"})
started = time.monotonic()
result = PatientRuns(boundaries).run(request)
print(result.end_reason, result.decision, repr(result.entry), result.cost_usd, result.turns, result.login, result.session, round(time.monotonic() - started, 1) < 25)
print([denial.detail for denial in result.permission_denials])
print([w.total_seconds() for w in waiter.waits])
for line in log.lines:
    print(line)
for call in (d / "calls").read_text(encoding="utf-8").splitlines():
    print(call[:150])
print(sorted(p.name for p in (d / "state" / "runs").iterdir()))
for value in ("claude", "codex"):
    try:
        s = read_settings({**environ, "FACTORY_AGENT_RUNTIME": value})
        print(value, type(build_boundaries(s.model_copy(update={"checkout": d / "checkout", "state_directory": d / "state", "agent_home": d / "home" / ".claude"}), "", hosting=FakeHostingService(), confine_executable=None).agent_runtime).__name__)
    except SettingsInvalid as error:
        print("refused:", error)
EOF
```

Output (green):

```text
OpencodeRuntime anthropic/claude-sonnet-5-5 428 0:05:00
completed approval 'Built it.\n\nNothing open.' 2.35 3 api_key ses_walk True
['{"command": "git push"}']
[420.0, 300.0]
provider limit: coder waits 420 s before it resumes ses_walk
provider limit: coder waits 300 s before it resumes ses_walk
run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder Build it.|key=sk-ant-smoke|config=yes
run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_walk The provider's spend limit stopped your run. Con
run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_walk The provider's spend limit stopped your run. Con
run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_walk Finish now: give your decision (question if the
[]
claude ClaudeCodeRuntime
refused: FACTORY_AGENT_RUNTIME: holds codex, which is neither claude nor opencode
```

What the output shows:

- The `4281` line was passed over, and the 428 line on standard error gave its named wait of 420 s (S0013's criterion 1).
- The 428 line without a newline, on a standard error that was then closed, stopped the call at once while standard output stayed open (S0013's criterion 2). It named no wait, so `PatientRuns` waited the 300 s cool-down.
- The third call ran over the $1.75 that was left, so the runtime resumed it once with the finish message. The run cost the sum of its calls ($0.25 + $2.00 + $0.10), and it took under 25 s although every limited call sleeps 30 s.
- The 150 000-byte event passed whole, the denial was read, and the multi-line entry kept its blank line. The API key reached all four calls, and the run's files were removed.
- `claude` gives the Claude Code runtime, and `codex` is refused.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

From the intake, tester, coder, reviewer, documenter and smoke-tester entries of S0013 and S0014. The earlier acceptances' lists (their section 4) stand for S0001 to S0012.

- **S0014's documenter**: in *The agent runs as a second user*, the login shell is described only for the Claude login. S0014's smoke tester repeated the point. Reading the section, I found two more Claude-only points in it: the switches that `env -i` lets through, and the files of a run. → **S0015**.
- **S0013's reviewer (round 0 finding, notes 1 and 2) and coder (entries 14 and 18)**: the opencode stand-in's reply constant is copied in the earlier modules, and the waiting step is written inline in three. A search finds the reply in nine modules (seven under `tests/adapters/`, one under `tests/entry/`, and the shared `opencode_stand_in.py` itself) and the waiting step in three. → **S0016**.
- **S0013's reviewer, note 2**: in `tests/adapters/test_process_streaming_last_line.py`, the `no-stop` row does not check `timed_out` or the elapsed time. Its child exits at once, so a call that reached the 30 s limit would show `exit_status` `None` and fail anyway. Small, no story.
- **S0013's coder**: nobody checked that the new tests kill the two mutants they were written for, because no stage runs `make mutants`. That is left to the human's next sweep. The reviewer argued for each mutant (entry 20) that the test would fail.
- **`make duplicates`**: every coder entry of S0013 and S0014 said `5 new, 33 known, 3 gone`, the same as at the second acceptance, and neither story changed `src/`. The second acceptance explained the five findings (F0020's two runtimes' shared blocks and `ManualWaiter`) and the three stale baseline lines. Updating the baseline is still the human's edit.
- **The first acceptances' note on private sudo helpers** (`_write_sudo` and `_sudo_calls`, imported from `tests/adapters/test_claude_runtime_os_user.py` by three opencode modules): about forty test modules import names from another test module, so this is the project's idiom, not F0020's alone. No story.
- **S0014's tester, coder and reviewer**: nothing.

## 5 The documentation as a whole

I read `README.md`, `docs/operator-guide.md` (its opening paragraph, *The agent runtime* with its login points, *The agent runs as a second user*, *`factory-guard` on the agent run's `PATH`*, *Running on opencode*), `docs/project-guide/agents.md` (*The shared launch module*, *The opencode runtime*) and the `run_streaming` section of `docs/project-guide/processes-and-checks.md`. `uv run python -m factory.entry.check_documents` prints `documents ok`.

S0014's three passages now agree with the code. The opening paragraph names both runtimes. The second-user section says the chain starts `opencode run` under opencode. The guard section says an opencode run registers no hook, while `agent-environment` checks the `PATH` under either runtime (`machine_extras` in `src/factory/entry/wiring.py`). S0013's sentence on a stop on a last line agrees with `process._LineReader`.

The guide contradicts itself in one place. The `sudo` paragraph of *The agent runs as a second user* says:

- `env -i` lets through "the runtime's three switches and, from the login shell, `CLAUDE_CODE_OAUTH_TOKEN`";
- "The login shell is there only when `FACTORY_CLAUDE_LOGIN_FILE` is set".

The guide's own list of login-shell points under *The agent runtime* says the shell also starts with `FACTORY_API_LOGIN_FILE` set and then hands over `ANTHROPIC_API_KEY`. `agents.md` says the same, and adds that an opencode run's login comes from the API file alone, with one switch and `OPENCODE_CONFIG` (`SWITCHES` and `CONFIG_VARIABLE` in `src/factory/adapters/opencode_runtime.py`). The paragraph on the files of a run names only Claude Code's `instructions-`, `guard-` and `hooks-` files, not opencode's `opencode-<run>.json`.

Read alone, the section tells an operator of an opencode instance on an API key that no key reaches the agent. The sections an operator configures from are correct: the settings table, *The agent's API key* and *Running on opencode*. → **S0015**.

The only example I ran is the feature smoke test above. The guides' other examples were not rerun.

## 6 Decisions taken for the human

**From `feature.md`, decisions 1 to 23**, unchanged since the first acceptance, which lists them one by one (its section 6). The human's changes 4 (cross-checking `factory-guard`'s refusals against the kernel's) and 6 (the paid todo-demo run on opencode) are still to be done by the human. So is the correction of S0009's place in `feature.md` (section 1).

**Answers and defaults recorded in the journals since the second acceptance:**

- S0013, intake question (journal entry 3): the Interface's "the status as a whole number" had no failing side. The human answered (a) in entry 4: a row `HTTP 4281 Precondition Required, retry after 120 seconds` that ends `completed` with `limit_wait` `None`. Intake carried it into criterion 1, and the tester built it as row `4281`.
- S0013's tester chose not to give criterion 2's table a separate `then` column (ruff's PLR0917). The test picks sleep or exit from the `stopped` column instead.
- S0014: no question, and no default taken.

**Earlier tests changed, each with its leave.** No change without a named leave was found.

- S0013: `REPLY` was added to the shared helper `tests/adapters/opencode_stand_in.py` and taken from there by the new module. This was under the standing leave of `CLAUDE.md`, named in the coder's entry 14, the tester's entry 16 and the reviewer's entry 20. No earlier test module changed.
- S0014 changed no test (reviewer's entry 9: the diff outside `factory/` was empty at review).
- The lists for S0001 to S0012 are the earlier acceptances'.

## 7 The slow checks

The project offers nothing beyond `make check`, apart from `make mutants` (check 3): no image scan and no SBOM.

`make check` was green as found (`check: green`, coverage 99.13 %). `make test` took 39.5 s for 6016 tests (438.6 s of test time across the workers). The slowest tests, from `.reports/junit.xml`:

- `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` (5.0 s);
- `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` (5.0 s);
- `test_opencode_sudo_time_limit::...[status-1-past-the-limit]` and `[sigkill-past-the-limit]` (4.5 s each), which wait past a 3 s limit by design.

S0013's eight new rows take 0.01 s to 0.03 s each.

**Disk.** Now: `/work` 970.3 GB free, 0.5 GB used; `/state` 970.3 GB free, 0.0 GB used; `/tmp` 970.3 GB free, 0.0 GB used. At the previous record (`disk acceptance`) the figures were the same to the tenth. No growth.

## 8 Cost

The stories cost 151 runs, 197.2 min, 1366 turns and $54.74. Per story, from the sidecars:

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
| S0013 | 11 | $2.17 | 7.4 |
| S0014 | 6 | $0.93 | 2.4 |

Every run of S0013 and S0014 ended `completed`.

**The two stories since the second acceptance** cost 17 runs and $3.10 together. S0013 took 11 runs for a tests-only story:

- a second intake run after its question;
- a review round for a copied reply constant, which went from the coder to the tester (`tests`, R9) and back to the coder.

That round is the copy S0016 now proposes to remove everywhere. S0014 went through each stage once. S0004 ($10.01) and S0005 (21 runs) still stand out, for the reasons the first acceptance gave. The second acceptance cost $2.74.

**Human interventions:** 13 questions answered (12 questions, 1 round cap), and the stories waited 0.3 h for them, the same as at the second acceptance to the tenth. The one new question is S0013's intake question on the whole-number rule. By story:

| Story | Questions |
|---|---|
| S0003 | 1 |
| S0004 | 3 |
| S0005 | 3 (one of them the round cap) |
| S0007 | 2 |
| S0008 | 2 |
| S0010 | 1 |
| S0013 | 1 |

S0004 and S0005 needed the human most, three times each:

- S0004 for two secrets-detector stops that no agent could clear;
- S0005 for an earlier test that the contract's version rise broke, and for the round cap.

## Proposed stories

- `F0020-S0015-the-second-user-section-names-the-api-login-and-opencode-s-run-files.md`: docs only. It corrects the two paragraphs of *The agent runs as a second user* that S0014's documenter noticed. They name the login shell, its variable and the switches for Claude Code on the subscription only, which contradicts the guide's own login-shell points. They also name only Claude Code's run files.
- `F0020-S0016-the-opencode-tests-take-their-reply-and-waiting-steps-from-the-stand-in-module.md`: tests only, under the standing leave. It moves the opencode stand-in's reply (nine copies) and waiting step (three) into `tests/adapters/opencode_stand_in.py`, and adds a structural test that keeps each in one place. That copy cost S0013 a review round.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 2 stories proposed

   This acceptance covers S0013 (tests only) and S0014 (docs only), the two stories the second acceptance proposed. Both did what they set out to do. `make check` is green as I found it, and the feature's smoke test is green end to end on opencode. What is left: the operator guide's second-user section still describes the login shell for Claude Code on the subscription only, which contradicts the guide's own login-shell points and the code (S0015). And nine test modules still copy the opencode stand-in's reply (S0016).

   1. Scope: no gap. S0013 adds two test modules and S0014 changes only the operator guide, both inside the Scope, and neither changed `src/`. S0009 is still deferred (decision 15). `feature.md` still says its file lies in `deferred/`, which the feature folder does not have; correcting that is the human's edit.
   2. Feature smoke test: green. An opencode instance on an API key goes through the settings, `build_boundaries` and `PatientRuns`, and streams a 150 000-byte event. A `4281` line on standard error is passed over. A 428 line naming 7 minutes gives a wait of 420 s. A 428 line on standard error without a newline, with that stream then closed, stops the call at once; it names no wait, so the 300 s cool-down applies. The budget resume and the finish message follow. The run ends `completed` at $2.35 with a multi-line entry, one denial and login `api_key`, and leaves no run files. `claude` gives the Claude Code runtime and `codex` is refused.
   3. Mutation testing: by sweep, not run here.
   4. What the stories noticed: S0014's documenter found that the second-user section describes the login shell for the Claude login only (S0015, with two more Claude-only points I found there). S0013's coder and reviewer found the reply constant and the waiting step copied across the opencode tests (S0016). The `no-stop` row checks no `timed_out` (small, no story). `make duplicates` is unchanged at 5 new, 33 known, 3 gone; the baseline is the human's. The private sudo helpers are imported the way about forty test modules import names, so they get no story.
   5. Documentation: S0014's three passages and S0013's sentence agree with the code, and `check_documents` prints `documents ok`. In *The agent runs as a second user*, the login shell is said to start only with `FACTORY_CLAUDE_LOGIN_FILE` and to hand over only `CLAUDE_CODE_OAUTH_TOKEN`, with Claude Code's switches and run files. That contradicts the guide's own login-shell points and `agents.md` (S0015). The settings table and the API-key and opencode sections an operator configures from are correct.
   6. Decisions: decisions 1 to 23 are unchanged, and the human's changes 4 and 6 are still to be done. New: S0013's intake answer (a), the `4281` row for the whole-number rule, and its tester's choice to drop the separate `then` column. Earlier tests: S0013 added `REPLY` to the shared `opencode_stand_in.py` under the standing leave, named by the coder, tester and reviewer. No change without a leave was found.
   7. Slow checks: nothing beyond `make check`. `make test` took 39.5 s for 6016 tests. The slowest are the 5.0 s time-limit tests and the two 4.5 s sudo rows, which wait on purpose. Disk is unchanged against the previous record to the tenth.
   8. Cost: 151 runs, 197.2 min, $54.74 in all. S0013 and S0014 together cost 17 runs and $3.10. S0013 took 11 runs: a second intake run after its question, and a review round for the copied reply constant. S0004 ($10.01) and S0005 (21 runs) still stand out. 13 questions were answered (12 questions, 1 round cap), and the stories waited 0.3 h. The one new question was S0013's intake question. S0004 and S0005 needed the human most, three times each.
3. factory: done (pull request merged); cost: 1 runs, 7.6 min, 39 turns, 98065 tokens in (2690168 more from cache), 30504 out, $1.93
