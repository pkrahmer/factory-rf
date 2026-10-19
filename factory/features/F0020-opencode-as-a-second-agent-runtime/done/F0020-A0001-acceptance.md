---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 261
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T11:38:51.847921Z'
  stage: acceptance
- number: 2
  speaker: factory
  kind: crash
  at: '2026-10-19T11:40:09.775849Z'
  stage: acceptance
- number: 3
  speaker: factory
  kind: started
  at: '2026-10-19T11:40:11.219658Z'
  stage: acceptance
- number: 4
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T12:27:50.650147Z'
  stage: acceptance
  run: ee7366eee62f45499e8e4880e375268b
- number: 5
  speaker: factory
  kind: done
  at: '2026-10-19T12:29:09.380026Z'
  stage: done
stories: [F0020-S0001, F0020-S0002, F0020-S0003, F0020-S0004, F0020-S0005, F0020-S0006, F0020-S0007, F0020-S0008]
outcome: accepted
---

# Acceptance of opencode as a second agent runtime

## Recommendation

**accepted with stories.** Every scope item that was not deferred was built and is reachable from the real entry points. The feature's smoke test runs on opencode with an API key, through a provider limit, the wait and the resume by session, and it is green. `make check` is green. The findings are gaps in the tests and in the docs, not broken promises:

- the streaming read and the opencode runtime have survivors on behaviour the feature relies on (a long output, a resumed call's words, the kill under `sudo`, a multi-line entry);
- the operator guide still speaks of the runtime as Claude Code alone in six older passages, the pins above all.

`make mutants` did not finish (see 3), so the score covers 62 % of the feature's mutants.

## 1 Scope

None of weight. Every item of the Scope tagged S0001 to S0008 has its story in `done/` and its code under `src/factory/`:

- `adapters/agent_launch.py`, `adapters/opencode_runtime.py`, `domain/provider_limits.py` and `application/provider_limits.py` exist;
- `process.run_streaming` exists, and so do `Waiter`, `SleepingWaiter` and `ManualWaiter`, `PatientRuns` in the stage launch, and the settings `FACTORY_API_LOGIN_FILE`, `FACTORY_PROVIDER_LIMIT_*`, `FACTORY_AGENT_RUNTIME` and `FACTORY_OPENCODE*`;
- the image installs `opencode-ai@${OPENCODE_VERSION}` (1.19.3) and sets the version and the three model ids, and `image/compose.yml` chooses the runtime and the build per compose call.

No story went outside the Scope.

The S0009 items (`domain/spend.py`, `spend_records`, `FACTORY_SPEND_WINDOW`) are deferred by decision 15 and are not a gap. One inaccuracy: `feature.md` says S0009's file "lies in `deferred/` beside `backlog/`". No such folder exists in the feature. The file is `planning/overnight/stories/F0020-opencode-as-a-second-agent-runtime/deferred/F0020-S0009-...md`, in the human's planning folder.

**Numbering collision.** The prompt gave F0020-S0009 as the next free number, so the stories proposed here start there. They collide with that deferred S0009, and the human renumbers one or the other.

The goal's real test, the todo demo on opencode through the API (change 6), is the human's and outside every story (decision 20).

## 2 Feature smoke test

The walk-through of an operator who puts an instance on opencode with an API key, behind a spend limit:

1. the settings choose `FACTORY_AGENT_RUNTIME=opencode`, the image's model ids and a key file;
2. `build_boundaries` wires the opencode runtime;
3. a stage's run through `PatientRuns` hits a 428 that names a 7-minute wait, waits it out on a manual waiter and resumes the session;
4. the run ends `completed` with the costs of both calls summed and the login `api_key`.

The script also shows the default runtime and a refused one. `opencode` is a stand-in that plays opencode's events, so no paid call is made and no confinement or `sudo` is used.

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
case "$n" in
1)
  printf '%s\n' '{"type":"step_start","timestamp":1000,"sessionID":"ses_walk","part":{"type":"step-start"}}' '{"type":"step_finish","timestamp":1100,"sessionID":"ses_walk","part":{"type":"step-finish","cost":0.25,"tokens":{"input":10,"output":5}}}' '{"type":"error","timestamp":1200,"sessionID":"ses_walk","error":{"name":"APIError","data":{"message":"spend limit reached, try again in 7 minutes","statusCode":428}}}'
  sleep 30 ;;
*)
  printf '%s\n' '{"type":"step_start","timestamp":2000,"sessionID":"ses_walk","part":{"type":"step-start"}}' '{"type":"text","timestamp":2050,"sessionID":"ses_walk","part":{"type":"text","text":"<factory-result>\ndecision: approval\nentry:\nBuilt it.\n</factory-result>"}}' '{"type":"step_finish","timestamp":2100,"sessionID":"ses_walk","part":{"type":"step-finish","cost":0.5,"tokens":{"input":20,"output":7}}}' ;;
esac
EOF
chmod +x "$d/opencode"
uv run -q python - "$d" <<'EOF'
import sys
import time
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
from dataclasses import replace
boundaries = replace(built, waiter=waiter, clock=clock, log=log)
print(type(boundaries.agent_runtime).__name__, settings.opencode_models["sonnet"], settings.provider_limit.status)
agent = AgentDefinition(name="coder", model="sonnet", tools=["Read", "Bash"], budget_usd=Decimal("2"), instructions="Build it.")
request = AgentRunRequest(agent=agent, prompt="Build it.", allowed_decisions=["approval", "question"], time_limit=timedelta(seconds=120), working_directory=d / "work", environment={"PATH": "/usr/bin:/bin"})
started = time.monotonic()
result = PatientRuns(boundaries).run(request)
print(result.end_reason, result.decision, result.entry, result.cost_usd, result.login, result.session, time.monotonic() - started < 25)
print([w.total_seconds() for w in waiter.waits], log.lines)
for call in (d / "calls").read_text(encoding="utf-8").splitlines():
    print(call)
print(sorted(p.name for p in (d / "state" / "runs").iterdir()))
EOF
```

Output (green):

```text
OpencodeRuntime anthropic/claude-sonnet-5-5 428
completed approval Built it. 0.75 api_key ses_walk True
[420.0] ['provider limit: coder waits 420 s before it resumes ses_walk']
run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder Build it.|key=sk-ant-smoke|config=yes
run --format json --auto --model anthropic/claude-sonnet-5-5 --agent factory-coder --session ses_walk The provider's spend limit stopped your run. Continue the work where you stopped, then end as your instructions say.|key=sk-ant-smoke|config=yes
[]
```

What the output shows:

- the key reached both calls through the login shell;
- each call saw its per-run configuration;
- the resume carried `--session ses_walk` and the continue prompt;
- the run's files in `/state/runs` were removed.

The default and the refusal, run the same way:

```text
claude ClaudeCodeRuntime
refused: FACTORY_AGENT_RUNTIME: holds codex, which is neither claude nor opencode
```

**Setup note.** `FACTORY_OPENCODE_MODELS` has no default in the code, only in the image and the compose file. Without it, the alias `sonnet` stops the run before it starts, as decision 9 says. The script passes the image's value.

## 3 Mutation score

The run is incomplete. `make mutants` (FEATURE `F0020`, 22 modules) ran four times; each was stopped at 540 s:

- **Run 1** spent its 540 s on mutmut's stats and clean-test phases (`⠇ Running clean tests mutants: stopped after 540 s`).
- **Run 2** reached `3091/14920 🎉 2941 🫥 0 ⏰ 3 🤔 0 🙁 147`.
- **Runs 3 and 4** made no progress at all. Both ended at the same line, `⠧ 3091/14920  🎉 2941 🫥 0  ⏰ 3  🤔 0  🙁 147  🔇 0  🧙 0mutants: stopped after 540 s; the results below are partial, run it again to go on`.

So mutmut stalls on a mutant that never ends, and its CPU-time limit does not catch it. 1875 of the feature's modules' 4966 mutants stay `not checked`, among them `process._start`, `run_process` and `_kill_group`, and much of `agent_launch`, `claude_runtime`, `stage` and `journal`. Finding out which mutant hangs, and capping a mutant's wall time, is a change to `Makefile` or `[tool.mutmut]`. Both are the human's, so this is a note, not a story.

**Score on what was checked:** 2941 killed of 3091 (95.1 %), 147 survived, 3 timed out (`_Watch._stop_at_limit` 1, `ClaudeCodeRuntime.version` 4 and 7).

Survivors by group, from `uv run mutmut show` of each:

- **`process._LineReader.read_ready`** (3), and `_read_until_end` (1, equivalent). `+= chunk` → `= chunk` on both `read_bytes` and `_pending` survives. No test streams more than one 64 KiB read, or a line that arrives in two reads. The opencode result is parsed from that `stdout`. → **S0009**.
- **`opencode_runtime`** (64). The groups:
  - `_opencode_argv`: `arguments += ["--session", …]` → `=` survives, so a resumed call that lost `run --format json --model --agent` would pass. S0006's smoke test checks only the tail.
  - `_call`: the `killed_at_limit` path under `sudo` (exit 137 read as `time_limit`) is unpinned (8 mutants), and so is `_remove_temporary_folder`'s argument (3).
  - `parse_result_block`: an entry of several lines joined with `\n`, and a second line other than `entry:`.
  - `_model_ms`: `tools += span` → `=`, two tool calls in one step.
  - `_denials`: `continue` → `break`, a non-denial error before a denial.
  - `_result`: `login` on a timed-out call.

  → **S0010**. The rest of this module's survivors are equivalent or unreachable:
  - `_end_reason`'s `time_limit` branch cannot be reached, because `_result` returns first on `timed_out`, so its two string mutants cannot die;
  - `_resume`'s `left <= 0` branch, on both runtimes (9 + 11), needs a budget stop after the time limit has already passed, which a stand-in cannot arrange without an injectable clock;
  - `__init__`, `_span_ms`, `_steps`, `_answer` and `_limit_message` have `and`/`or` swaps on `None` checks that a valid event never reaches;
  - `_write_files` and `_deny_list` have encoding mutants (`"UTF-8"`, `None`).
- **`claude_runtime`** (15): `_resume` without time left (equivalent, see above), `_resume_arguments`'s `format(..., "f")` (equal for these budgets), `version`'s error text. No story.
- **`domain`**:
  - `provider_limits.named_wait`: `> 0` → `> 1`, a named wait of a fraction of a second up to 1 s, not tested;
  - `agent_runs.resumed_result`: the key `"session"` misspelt in one `update`; a resumed result whose second call ended `time_limit` is not checked for its session;
  - `settings._opencode_model`: `partition` → `rpartition` (a model with a second `=` or `/`), and the ceiling's message text;
  - `settings._holds_password`, `_repository_url` and `_name` (16) and `contract` (3) are earlier features' code.

  Small; listed for the human, no story.
- **`application`, `entry`, `post_texts`**:
  - `preflight._opencode_login_hint`: the fallback `the factory user` is unpinned under opencode;
  - `wiring.build_boundaries`, `_agent_runtime`, `machine_log`, `read_hosting_token` and `repository_name`: arguments passed but never compared; `_agent_runtime`'s `sudo_executable` can be dropped from the opencode runtime unnoticed;
  - `stage._stall`, `_stall_red` and `_description`, and `post_texts`: earlier features' code.

  No story: the wiring survivors are the "built once, read nowhere" kind earlier acceptances accepted.

## 4 What the stories noticed

Collected from the coder, reviewer, tester and documenter entries of S0001 to S0008:

- **Owned by the proposed stories.** The operator guide's *Update the pins* and *The machine's image* name no opencode pin. The S0008 documenter saw this and left it. → S0011.
- **Shared code between the runtimes.** `make duplicates` still reports similar blocks between `claude_runtime` and `opencode_runtime`: the `call_refusal` call, `cleanup_launch`, `version_printed`, the confine branch and `_request_of`. `_resume` has the same shape in both. S0004's review cut 7 blocks to 3. The rest cannot move into `agent_launch` while `tests/test_wrapper_search.py` forbids it to import the process module (decision 4). That is the human's call, not a story here.
- **Smaller code notes.** `_Watch.stopped_by` is typed `EndReason | None` but only holds `budget` or `provider_limit` (S0006, every later entry). `request_home` in `agent_launch` is public but no Interface names it (S0002). These are small notes, not stories.
- **mutmut's left-out structural tests.** `tests/test_agent_launch_search.py` reads the source and may belong on mutmut's left-out list in `pyproject.toml` (S0002, open in four entries). It did not show in this run, which killed nothing it should not have. Human's file.
- **Test notes.**
  - `tests/adapters/test_make_commands.py::test_output_tail_keeps_the_last_thirty_lines[30-1]` failed once under parallel workers (S0006) and has not been seen failing since.
  - The rows `500` and `1428` of `tests/adapters/test_opencode_provider_limit.py` assert `<= 1` call where they could assert one (S0006 reviewer).
  - The error reply is written twice: `_error_reply` and `ERROR_REPLY` (S0005 reviewer).
  - Five test modules still define their own `COMPOSE`: `test_claude_token_mount`, `test_compose_init`, `test_compose_project`, `test_image_credentials` and `test_token_folder` (S0008).

  The tester can move these under the standing leave in any later story.
- **`docs/decisions.md`.** Older entries name `_resumed_result` and the old private helpers (S0002 documenter). This is history and should stay.
- **Pipeline observation, outside F0020.** In S0005 the human answered the round-cap question with "the tester writes the test for criterion 19" (entry 33). The factory sent the work item to review instead of tests (entry 34). The reviewer found the test still missing (entry 35), which cost one more coder and tester round. The factory resumes a round-cap answer at the stage that asked, not at the one the answer names. That is a matter for a factory feature, not this one.
- **Secrets detector.** detect-secrets flagged the literal `"ANTHROPIC_API_KEY"` as a key in a test (S0004, entry 10). It flagged the same quote again in the coder's own journal (entry 17), which only the human could reword. Agents that quote a flagged line in their entry trip `make secrets` on the work item itself. This is a note for the agent files or a later story, not F0020's.

## 5 The documentation as a whole

Read from the top: `README.md`, `docs/operator-guide.md` (configuration, *The agent runtime* to *The machine's image*, the preflight's items) and `docs/project-guide/agents.md`, `processes-and-checks.md` and `watching.md`. The project guide's opencode sections in `agents.md` agree with the code and with each other. The operator guide's new sections are correct: *A provider's spend limit*, *The wait*, *An opencode run's budget* and *Running on opencode*. The older passages still speak of one runtime:

- *The agent runtime* opens with "The factory runs each agent as a `claude -p` call" (line 82).
- The configuration table calls `FACTORY_CLAUDE` "The agent runtime's executable" and `FACTORY_CLAUDE_VERSION` "The version of the agent runtime the image pins".
- *The kernel refuses every other write* names `~/.claude` as "the runtime's own folder", with nothing on opencode's three folders.
- *The machine's image* names Claude Code, `uv` and the Debian tools as pinned, not opencode.
- *Update the pins* has no line for `OPENCODE_VERSION`, though *Running on opencode* says "Change both together, as for Claude Code (see "Update the pins")". It does not say that the compose defaults of `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS` must move with it.
- The preflight's closing paragraph names only the three `FACTORY_CLAUDE*` variables to check first.

None of these contradicts the behaviour in a way that breaks an instance. An operator who updates the opencode pin from the guide would, though, miss the compose defaults, and the preflight would then fail on the version. → **S0011**.

Also seen, not a story:

- `docs/project-guide/processes-and-checks.md:57` names "F0020-S0004" in running text.
- `docs/project-guide/write-guard.md` does not mention opencode. `agents.md` covers the runtime's folders.

I did not rerun the stories' examples one by one. The feature smoke test above runs the documented path on its own.

## 6 Decisions taken for the human

**From `feature.md`**, decisions 1 to 23, to accept or revisit as a whole:

- the API key wins over the token, and the key file is always mounted (1);
- the factory never reads the key (2);
- the login in force is taken from the shell's report (3);
- `agent_launch` holds what the runtimes share, and `resumed_result` lies in the domain (4);
- one process module streams, with one `Popen` (5);
- opencode's agent is generated per run from the shipped agent files (6);
- a strict `<factory-result>` block (7);
- opencode's measures from `step_finish`, an unknown cost for a cut step (8);
- Claude Code's aliases mapped by `FACTORY_OPENCODE_MODELS`, and no effort passed (9);
- opencode's own three folders, `snapshot: false`, `share: disabled`, `autoupdate: false` and `--auto` (10);
- the factory's own budget stop, one resume at a quarter (11);
- the limit recognized by a status setting and an optional message expression (12);
- `provider_limit` keeps the session; `resume_session` instead of a new operation (13);
- `PatientRuns` waits in the application layer, the claim stays held, and a stall at the ceiling (14; the human said yes on 2026-10-18);
- the spend window deferred (15; the human said not yet);
- the runtime per instance (16; the human said yes);
- opencode from npm at a pin, and the build chosen per compose call (17);
- F0019's kernel guard for opencode, no plugin (18);
- the test leaves (19);
- stand-ins only, no paid call (20);
- the gateway's base URL out of scope (21);
- the template and demo changes are the human's (22);
- one contract version raised twice, `1.0` → `1.1` → `1.2` (23).

The human's changes 1 to 7 are listed there too. Change 4 (the cross-check of `factory-guard`'s refusals against the kernel's after S0008) and change 6 (the paid todo-demo run) are still due by the human's hand.

**Answers and defaults recorded in the journals:**

- S0003: five intake answers, among them that a stop drops lines already read in the same chunk and that standard output alone covers a raising callback.
- S0004: five intake answers (more event-validation rows; a `step_finish` with no `step_start` adds 0 and still counts as a turn; "between" goes by line order; rules file `0640`; `--version` without login words; the runtime does not create its state directory). Then (a): the test keys are the constants. Then (a): the human reworded the journal quote, with no baseline entry.
- S0005: three intake answers. Then (a): a leave for `tests/domain/test_contract_login.py`. Then the round-cap answer: one more round, tests only.
- S0007: two intake answers (whole seconds in the log; criterion 9's budget and time). Then (a): the ceiling row's waits are `600 × 3 + 0.7`.
- S0008: (a) `installed_models` in the agents' name order, with the tester's two smaller readings accepted. Then (a): the test writes `settings.json`, the opencode runtime stays fail-closed on a missing settings file, plus two type fixes in its own tests.

**Earlier tests changed, each with its leave.** No change without a named leave was found.

- `tests/test_compose.py` and `tests/domain/test_contract.py` (S0001, decision 19); `tests/test_compose.py` again (S0008, the standing leave: `COMPOSE` and the `service` fixture moved to `tests/compose_support.py` and `tests/conftest.py`).
- `tests/adapters/test_claude_runtime_login.py`, `test_claude_runtime_sudo_time_limit.py` and `tests/conftest.py` (S0001, standing leave: one `Recorder` in `tests/run_process_recorder.py`).
- `tests/test_agent_run_request_search.py` (S0002, standing leave: `reads_os_environ` into `tests/source_search.py`).
- `tests/adapters/test_process.py` (S0003, standing leave: `_python` → `tests/process_support.python_argv`).
- `tests/test_wrapper_search.py` and `tests/test_model_configuration.py` (S0004, decision 19).
- `tests/domain/test_agent_runs.py` and `tests/domain/test_contract.py` (S0005, decision 19); `tests/domain/test_contract_login.py` (S0005, the human's leave in its journal entry 9).
- The earlier `tests/domain/test_settings*.py` modules (S0008, standing leave: `BASE` into `tests/settings_support.py`).

## 7 The slow checks

Beyond `make check` and `make mutants` the project offers no slow check (no image scan, no SBOM). Today that means nothing more to run.

`make check` was green as found. `make test` took 43.7 s for 5662 tests (459.5 s of test time across the workers). The slowest tests, from `.reports/junit.xml`:

- `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` (5.0 s);
- `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` (5.0 s);
- the two `test_fault_paths_7_to_13::test_acceptance_container_lost_in_review_reruns_once_and_books_result` rows (3.6 s and 3.5 s).

The first two are this feature's time-limit tests and wait out a real limit by design.

**Disk.** Now: `/work` 980.0 GB free, 0.5 GB used; `/state` 980.0 GB free, 0.0 GB used; `/tmp` 980.0 GB free, 0.0 GB used. At the previous record (`disk start`), the same to the tenth. No growth to explain. `mutants/` holds 55 MB and is a working folder outside the record.

## 8 Cost

The stories cost 115 runs, 172.2 min, 1166 turns and $47.50. Per story (runs, dollars, agent minutes) from the sidecars:

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

Every run ended `completed`.

**S0004 stands out**, at a fifth of the feature's dollars, with 8 doing runs. Its journal says why:

- it was the largest story (the whole opencode runtime);
- `make secrets` was red twice: first on the literal key name in a test, then on the coder's own journal quoting that line, which only the human could reword;
- a review round asked to move the duplicated launch code into `agent_launch`.

**S0005 ran the most runs** (21). It was sent back three times past its `round_cap`, and after the human's answer the factory went to review instead of tests (see 4).

**Human interventions.** 11 questions answered (10 questions, 1 round cap), 0.3 h waited. By story: S0003 1, S0004 3, S0005 3, S0007 2, S0008 2. S0004 and S0005 needed the human most:

- S0004 for two secrets-detector stops that no agent could clear;
- S0005 for an earlier test the version rise broke (`test_contract_login.py`, not named under decision 19) and for the round cap.

## Proposed stories

- `F0020-S0009-run-streaming-keeps-a-long-output-and-a-line-split-across-reads.md`: pins the two surviving `+=` of `_LineReader.read_ready`. The opencode result is parsed from a stream longer than one read. Tests only.
- `F0020-S0010-the-opencode-runtime-s-tests-pin-its-measures-a-resumed-call-and-a-kill-under-sudo.md`: pins the opencode runtime's survivors that carry the feature's decisions 7, 8, 11 and 18:
  - a resumed call's whole words;
  - the kill under `sudo`;
  - the temporary folder's removal;
  - a multi-line entry, the model time over several tool calls, and denials after an ordinary error.

  Tests only.
- `F0020-S0011-the-operator-guide-names-opencode-wherever-it-names-the-runtime.md`: corrects the six operator-guide passages that speak of Claude Code alone, among them the pins of opencode in *Update the pins*. Docs only.

These start at the prompt's next free number, F0020-S0009, which collides with the deferred S0009 in `planning/`. The human renumbers.

## Journal

1. factory: started acceptance as self.
2. factory: crash 1: the run of stage acceptance ended without a result. Its work is discarded back to commit 2631cce9e6bc3622b657e6b3ef44a32cc4992514.
3. factory: started acceptance as self.
4. acceptance-reviewer: accepted with stories; 3 stories proposed; make mutants 2941/3091 (partial: 3091 of the feature modules' 4966 mutants checked, 147 survived, 3 timed out)

   Every scope item of S0001 to S0008 is built and the feature smoke test is green. The findings are gaps in the tests and the operator guide, not broken promises.

   1. Scope: no gap. The S0009 items are deferred by decision 15. `feature.md` says S0009's file lies in `deferred/` beside `backlog/`, but it is in `planning/overnight/stories/...`, and its number collides with the proposed S0009.
   2. Feature smoke test: green. An opencode instance on an API key through settings, `build_boundaries` and `PatientRuns` hits a 428 that names a wait. It waits 420 s on the manual waiter, resumes with `--session`, and ends `completed` at $0.75 with login `api_key`. The run files are removed. The default runtime is `claude`, and `codex` is refused.
   3. Mutation score: 95.1 % on what was checked. Four `make mutants` runs stopped at 540 s. Runs 3 and 4 made no progress past 3091/14920, so mutmut is stuck on a mutant that never ends; fixing that is a change to the Makefile or pyproject, which are the human's. The survivors fall into two groups: `run_streaming`'s `+=` on its read buffers (S0009), and the opencode runtime's resume words, kill under sudo, folder removal, multi-line entry, tool spans and denials (S0010). The rest are equivalent, unreachable, or earlier features' code.
   4. What the stories noticed: the opencode pins missing from the operator guide (S0011). Duplicate blocks between the two runtimes remain, held back by the wrapper-search test (the human's call). Also open: test-helper copies, a possibly flaky make-commands row, and `_Watch.stopped_by`'s type. Outside F0020: a round-cap answer naming the tester restarted S0005 at review, and an agent's journal quote can trip `make secrets` on its own work item.
   5. Documentation: six older passages of the operator guide still describe Claude Code as the only runtime, and *Update the pins* has no opencode pin or compose defaults (S0011). The project guide is consistent.
   6. Decisions: feature decisions 1 to 23 and the human's answers in S0003, S0004, S0005, S0007 and S0008 are listed. Every changed earlier test has a named leave (decision 19, the standing leave, or S0005's entry 9). Human changes 4 and 6 are still the human's to do.
   7. Slow checks: there are none beyond make check and make mutants. `make check` was green (43.7 s test run; slowest tests 5.0 s, the time-limit tests). Disk is unchanged since `disk start`.
   8. Cost: 115 runs, 172.2 min, $47.50. S0004 cost the most ($10.01, 19 runs): the whole runtime, two secrets stops and a duplication round. S0005 had the most runs (21) and hit the round cap. The human answered 11 questions (10 questions and 1 round cap) and the stories waited 0.3 h; S0004 and S0005 needed the human 3 times each.
5. factory: done (pull request merged); cost: 1 runs, 47.6 min, 68 turns, 178287 tokens in (7313068 more from cache), 53042 out, $3.95
