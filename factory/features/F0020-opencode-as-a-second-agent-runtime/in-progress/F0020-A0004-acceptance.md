---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 341
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T07:10:04.912019Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T07:14:36.497543Z'
  stage: acceptance
  run: 38ae93fa682041f897f42ac3a356dd7e
stories: [F0020-S0001, F0020-S0002, F0020-S0003, F0020-S0004, F0020-S0005, F0020-S0006, F0020-S0007, F0020-S0008, F0020-S0010, F0020-S0011, F0020-S0012, F0020-S0013, F0020-S0014, F0020-S0015, F0020-S0016]
outcome: null
---

# Acceptance of opencode as a second agent runtime

## Recommendation

**accepted.** This fourth acceptance covers the two stories the third one proposed. S0015 (docs only) brought *The agent runs as a second user* into line with the API login and opencode's run file. S0016 (tests only) moved the opencode stand-in's reply and waiting steps into `tests/adapters/opencode_stand_in.py`, with a structural test that keeps them there. `make check` is green as I found it, and the feature's smoke test is green end to end on opencode. What is left is one inline copy of the waiting step written with a literal `30`, a one-line command template, and the human's own open items. None of these is a broken promise or worth a run of its own, so I propose no story.

## 1 Scope

None. Every Scope item tagged S0001 to S0008 was built (`done/F0020-A0001-acceptance.md`, section 1), and S0010 to S0014 stayed inside the Scope (the second and third acceptances). The two new stories stay inside it too:

- S0015 changes `docs/operator-guide.md` only: two paragraphs of *The agent runs as a second user*, 2 lines in and 2 out (smoke tester, entry 13).
- S0016 changes 11 files under `tests/` and adds `tests/test_opencode_shared_steps.py`. It changes nothing under `src/`, and decision 19 names its leave for the waiting step.

The goal is reached by the code, as section 2 shows: an instance on opencode instead of Claude Code, on an API key, behind a gateway's spend limit, with the pipeline's rules still in `claude/agents/*.md`. Its real test is the paid todo demo on opencode (the human's change 6), which is the human's to start. S0009 (`FACTORY_SPEND_WINDOW`) was dropped by the human on 2026-10-19 (decision 15) and is not a gap. One correction from the earlier acceptances still stands: decision 15 says S0009's file "lies in `deferred/` beside `backlog/`", but the feature folder has no `deferred/`. The *Stories* list already says the draft is kept at the tag `planning-history-2026-10-19`. Correcting decision 15's sentence is the human's edit of `feature.md`.

## 2 Feature smoke test

This is the operator's walk-through, as in the third acceptance: an instance put on opencode with an API key, behind a gateway's spend limit, through `read_settings`, `build_boundaries` and `PatientRuns`. `opencode` is a stand-in that plays opencode's events: no paid call, no `sudo`, no confinement. I extended the stand-in for S0015's claims. Every call now also records the name of the file `OPENCODE_CONFIG` names and that file's mode, beside the key it received.

1. The first call streams a 150 000-byte `tool_use` event. On standard error it prints a `4281` line, which is no limit, then a 428 line naming 7 minutes.
2. The resumed call prints a 428 line without a newline on standard error, closes that stream and sleeps. The line names no wait, so the 5-minute cool-down applies.
3. The next call runs past what is left of the budget, with a `git push` refused, so the runtime resumes it once with the finish message.
4. The last call ends with a multi-line entry.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/work" "$d/home/.claude" "$d/state/runs"
printf 'sk-ant-smoke\n' > "$d/api-key"
printf '%s' '{"permissions":{"deny":["Bash(git push:*)"]}}' > "$d/home/.claude/settings.json"
cat > "$d/opencode" <<'EOF'
#!/bin/sh
here=$(dirname "$0")
n=$(cat "$here/count" 2>/dev/null || echo 0); n=$((n + 1)); echo "$n" > "$here/count"
printf '%s|key=%s|config=%s|mode=%s\n' "$*" "${ANTHROPIC_API_KEY:-none}" "$(basename "$OPENCODE_CONFIG" | sed 's/-[0-9a-f]*\.json$/-<run>.json/')" "$(stat -c %a "$OPENCODE_CONFIG")" >> "$here/calls"
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
    head, *rest = call.split("|")
    print(head[:110], "|", "|".join(rest))
print(sorted(p.name for p in (d / "state" / "runs").iterdir()))
for value in ("claude", "codex"):
    try:
        s = read_settings({**environ, "FACTORY_AGENT_RUNTIME": value})
        print(value, type(build_boundaries(s.model_copy(update={"checkout": d / "checkout", "state_directory": d / "state", "agent_home": d / "home" / ".claude"}), "", hosting=FakeHostingService(), confine_executable=None).agent_runtime).__name__)
    except SettingsInvalid as error:
        print("refused:", error)
EOF
```

Output (green). My `sed` trimmed only the last group of the run's UUID, so part of each id still shows:

```text
OpencodeRuntime anthropic/claude-sonnet-5-5 428 0:05:00
completed approval 'Built it.\n\nNothing open.' 2.35 3 api_key ses_walk True
['{"command": "git push"}']
[420.0, 300.0]
provider limit: coder waits 420 s before it resumes ses_walk
provider limit: coder waits 300 s before it resumes ses_walk
run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder Build it. | key=sk-ant-smoke|config=opencode-f3bcc14a-7a8d-4e9a-b4a2-<run>.json|mode=640
run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_walk The prov | key=sk-ant-smoke|config=opencode-360e4ab5-d7c3-45ba-8d2d-<run>.json|mode=640
run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_walk The prov | key=sk-ant-smoke|config=opencode-dbf9aa44-45da-434c-b29f-<run>.json|mode=640
run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_walk Finish n | key=sk-ant-smoke|config=opencode-dbf9aa44-45da-434c-b29f-<run>.json|mode=640
[]
claude ClaudeCodeRuntime
refused: FACTORY_AGENT_RUNTIME: holds codex, which is neither claude nor opencode
```

What the output shows:

- The `4281` line was passed over. The 428 line gave its named wait of 420 s, and the 428 line without a newline stopped its call at once and fell back to the 300 s cool-down.
- The budget resume came with the finish message. The run cost the sum of its calls ($0.25 + $2.00 + $0.10) and took under 25 s, although every limited call sleeps 30 s.
- The 150 000-byte event passed whole, the denial was read, and the multi-line entry kept its blank line.
- Two of S0015's corrected claims hold. Under opencode, `ANTHROPIC_API_KEY` reaches every call from the API login file. Each run has its own `opencode-<run>.json` at mode `0640`. Each `PatientRuns` resume is a new run with a new file, and the runtime's own budget resume reuses its run's file. `/state/runs` is empty afterwards.
- `claude` gives the Claude Code runtime, and `codex` is refused.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

From every entry of S0015 and S0016. The earlier acceptances' lists (their section 4) stand for S0001 to S0014.

- **S0016's tester, coder, reviewer and documenter** all noted the same thing. `tests/adapters/test_opencode_runtime.py:218` keeps an inline waiting step, `Step(stdout_before_wait=stdout(step_start()), wait_seconds=30)`. The Interface did not name it, and nobody moved it. `WAIT_SECONDS` is `30` (`tests/adapters/opencode_stand_in.py:26`), so this is the same step as `WAITING`, written with a literal. The new structural test searches for the text `wait_seconds=WAIT_SECONDS` and cannot see it. A later change to `WAITING` would leave this row playing the old step. The standing leave of `CLAUDE.md` covers moving it, since it is a copy of a shared helper. The row is `timed-out` of the parametrized test around line 215. It is one line and does not test anything wrong today, so I propose no story. It can go with the next tests-stage change to that module. I list it under 6 for the human.
- **S0015's documenter** did not reread `docs/project-guide/agents.md` and relied on the reviewer's checks instead. I checked the claims myself (section 5): they hold.
- **S0015's smoke tester**: the mode `0640` that criterion 3 asked for is not repeated in the opencode sentence; the paragraph's next sentence covers every run file. That is a fair reading, and no finding.
- **`make duplicates`**: both coder entries say `5 new, 33 known, 3 gone`, unchanged since the second acceptance. Neither story changed `src/`. The second acceptance explained the five new findings and the three stale baseline lines. Updating `security/duplicates-baseline.txt` is still the human's edit.
- **S0015's intake, tester, coder and reviewer**, and **S0016's intake and smoke tester**: nothing.

## 5 The documentation as a whole

I read *The agent runs as a second user* in `docs/operator-guide.md` in full and checked S0015's sentences against the code:

- `SWITCHES` and `CONFIG_VARIABLE` are at `src/factory/adapters/opencode_runtime.py:74,79` and `src/factory/adapters/claude_runtime.py:88,97`, with `_config_folder` at `:541`.
- `login_argv` is at `src/factory/adapters/agent_launch.py:116`.
- The opencode runtime builds its `LoginFiles` from the API file alone (`opencode_runtime.py:571`), so "under opencode, only the API login file counts" holds.

The section now agrees with the guide's own login-shell points, with `docs/project-guide/agents.md` and with section 2's output. `uv run python -m factory.entry.check_documents` prints `documents ok`. S0016 touched no document. Its documenter grepped `README.md` and `docs/` for the moved names and found `agents.md:138` still true.

One small remark, not a contradiction. The command template in the same section's second paragraph shows the login shell's words as `factory-login <login file> claude ...`. With an API key, `login_argv` puts `--api-login <file>` before the subscription file (`API_LOGIN_OPTION`, `agent_launch.py:50`). The template is illustrative, and the prose right after it now names both files. No story.

I did not rerun the other sections the earlier acceptances read; S0015 and S0016 did not touch them. The only example I ran is the feature smoke test above.

## 6 Decisions taken for the human

**From `feature.md`, decisions 1 to 23.** Decision 19 gained S0016's leave (the human, 2026-10-20). The rest are unchanged since the first acceptance, which lists them one by one (its section 6).

**Still the human's to do or decide:**

- change 4, cross-checking `factory-guard`'s refusals against the kernel's;
- change 6, the paid todo-demo run on opencode;
- the correction of decision 15's `deferred/` sentence (section 1);
- the stale lines of the duplicates baseline (section 4);
- whether `test_opencode_runtime.py:218`'s literal waiting step is moved to `WAITING` with a later tests-stage change, or left as it is (section 4). I would leave it until that module is next touched.

**Answers and defaults recorded in the journals since the third acceptance.** Neither story asked a question. Two choices were made without asking:

- S0015's documenter kept mode `0640` out of the opencode sentence, because the next sentence covers every run file.
- S0016's tester made the whole move in the tests stage, so the coder had nothing to build. That follows `CLAUDE.md`: only the tester moves a shared helper. The tester also left the literal `wait_seconds=30` step alone.

**Earlier tests changed, each with its leave.** No change without a named leave was found.

- S0016 changed ten earlier test modules and the shared `tests/adapters/opencode_stand_in.py`. The reviewer's entry 9 names each file with its leave:
  - the standing leave of `CLAUDE.md` for the copies of the reply, in `test_opencode_confinement.py`, `test_opencode_left_out_tools.py`, `test_opencode_provider_limit.py`, `test_opencode_resumed_words.py`, `test_opencode_runtime.py`, `test_opencode_runtime_folders.py`, `test_opencode_runtime_launch.py` and `tests/entry/test_wiring_opencode.py`;
  - decision 19 (S0016) for the waiting step, in `test_opencode_confinement.py`, `test_opencode_provider_limit.py` and `test_opencode_limit_wait_on_stderr.py`.
  The tester's entry 5 reports 86 test ids before and after, in identical sorted lists.
- S0015 changed no test.

## 7 The slow checks

The project offers nothing beyond `make check` apart from `make mutants` (check 3): no image scan and no SBOM.

`make check` was green as I found it (`check: green`, coverage 99.16 %). `make test` took 56.9 s for 6124 tests (549.9 s of test time across the workers). The slowest tests, from `.reports/junit.xml`:

- `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` (5.1 s);
- `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` (5.0 s);
- `test_opencode_sudo_time_limit::...[status-1-past-the-limit]` and `[sigkill-past-the-limit]` (4.5 s each);
- `test_round_cap_answer::test_an_answer_at_the_round_cap_starts_the_count_of_rounds_over` (4.4 s).

All five wait past a limit by design. S0016's two new rows take 0.02 s each. The wall time grew from 39.5 s at the third acceptance. Part of the growth is 108 more tests, most of them from other features merged since. The rest may be load on the machine; one run cannot separate the two.

**Disk.** Now (`disk acceptance`): `/work` 970.7 GB free, 0.5 GB used; `/state` 970.7 GB free, 0.0 GB used; `/tmp` 970.7 GB free, 0.0 GB used. At the previous record (`disk start`): 970.0 GB free on each, with the same used figures. Used space did not grow, and free space rose by 0.7 GB. No growth to explain.

## 8 Cost

The stories cost 163 runs, 205.1 min, 1433 turns and $56.87. Per story, from the sidecars and the journals' closing entries:

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
| S0015 | 6 | $0.86 | 3.0 |
| S0016 | 6 | $1.27 | 4.8 |

**The two stories since the third acceptance** cost 12 runs and $2.13 together. Each went through every stage once, with no question and no rework round. S0016 cost more than S0015 because its tester made the whole move. S0004 ($10.01) and S0005 (21 runs) still stand out, for the reasons the first acceptance gave. The third acceptance cost $1.93. The three earlier acceptances proposed seven of the fifteen stories (S0010 to S0016), which cost 48 runs and $9.37 of the $56.87.

**Human interventions:** 13 questions answered (12 questions, 1 round cap), and the stories waited 0.3 h for them. That is unchanged since the third acceptance: S0015 and S0016 asked nothing. By story: S0003 1, S0004 3, S0005 3 (one of them the round cap), S0007 2, S0008 2, S0010 1, S0013 1. S0004 and S0005 needed the human most, three times each:

- S0004 for two secrets-detector stops that no agent could clear;
- S0005 for an earlier test that the contract's version rise broke, and for the round cap.

## Proposed stories

None. The only item left that a story could take is the literal waiting step at `tests/adapters/test_opencode_runtime.py:218` (section 4). It is one line that tests nothing wrong today, which is too little for a run of its own, so I list it under 6 for the human.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed

   This fourth acceptance covers S0015 (docs only) and S0016 (tests only), the two stories the third acceptance proposed. Both did what they set out to do. `make check` is green as I found it (coverage 99.16 %), and the feature's smoke test is green end to end on opencode. What is left is one line in a test and the human's own open items, too little for a story, so I propose none.

   1. Scope: no gap. S0015 changed two paragraphs of `docs/operator-guide.md`, and S0016 changed test helpers only; neither touched `src/`. S0009 was dropped by the human (decision 15). That decision's sentence about a `deferred/` folder, which the feature folder does not have, is the human's to correct.
   2. Feature smoke test: green. An opencode instance on an API key went through `read_settings`, `build_boundaries` and `PatientRuns`:
      - The `4281` line was passed over, the 428 line naming 7 minutes gave a 420 s wait, and the 428 line without a newline fell back to the 300 s cool-down.
      - The budget resume came with the finish message, and the run ended `completed` at $2.35 with login `api_key`.
      - S0015's two corrected claims hold: `ANTHROPIC_API_KEY` reached every call, and each run had its own `opencode-<run>.json` at mode `0640`, removed afterwards.
      - `claude` gives the Claude Code runtime, and `codex` is refused.
   3. Mutation testing: by sweep, not run here.
   4. What the stories noticed: four of S0016's stages noticed one leftover inline waiting step, at `tests/adapters/test_opencode_runtime.py:218`. It uses a literal `wait_seconds=30`, which equals `WAITING`, so the structural test cannot see it. It is one line and tests nothing wrong today, so it gets no story and is listed for the human. `make duplicates` is unchanged at 5 new, 33 known, 3 gone; updating its baseline is the human's edit.
   5. Documentation: *The agent runs as a second user* now agrees with the code and with section 2's output, and `check_documents` prints `documents ok`. A small remark, not a contradiction: the section's command template shows only the subscription form of the login shell's words.
   6. Decisions: decisions 1 to 23 stand, and decision 19 gained S0016's leave. Still the human's to do or decide:
      - the human's change 4 (the `factory-guard` cross-check) and change 6 (the paid todo-demo run);
      - the `deferred/` sentence in decision 15;
      - the stale lines of the duplicates baseline;
      - the literal waiting step.
      Neither story asked a question. S0016's ten earlier test modules each name their leave in the reviewer's entry 9 (the standing leave or decision 19), with 86 test ids before and after.
   7. Slow checks: there is nothing beyond `make check`. `make test` took 56.9 s for 6124 tests. The slowest, 4.4 s to 5.1 s, wait past a limit by design. Used disk did not grow against `disk start`.
   8. Cost: 163 runs, 205.1 min, $56.87 in all. S0015 and S0016 cost 12 runs and $2.13, with no question and no rework. The seven stories the acceptances proposed (S0010 to S0016) cost $9.37. 13 questions were answered (12 questions, 1 round cap), and the stories waited 0.3 h, unchanged since the third acceptance. S0004 and S0005 needed the human most, three times each.
