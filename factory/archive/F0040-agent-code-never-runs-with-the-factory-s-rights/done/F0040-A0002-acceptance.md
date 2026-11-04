---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 391
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-21T07:08:08.044625Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-21T07:13:48.485826Z'
  stage: acceptance
  run: 70bf071f57584f2b85ce15a88753d2a7
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-21T07:16:15.415177Z'
  stage: done
stories: [F0040-S0001, F0040-S0002, F0040-S0003, F0040-S0004, F0040-S0005, F0040-S0006, F0040-S0007]
outcome: accepted
---

# Acceptance of Agent code never runs with the factory's rights

## Recommendation

**accepted.** All seven stories are on `main`, every Scope item has its code, and `make check` is green. The feature smoke test ran the real `build_boundaries` with an agent user and passed. It covered a project command as that user, a command killed at its limit while another process held its output open, a sealed agent run, a refused `sudo`, and an instance with no agent user. The two stories the first acceptance proposed (S0006 docs, S0007 tests) closed what it found. The human's change 2 to `CLAUDE.md` is on `main` now (`d580a0f6`). What is left are small observations with no story (check 4), plus the operator's after-merge checks that the night log does not yet record as done.

## 1 Scope

Every Scope item is on `main`, as the first acceptance (F0040-A0001, check 1) traced symbol by symbol and caller by caller. S0006 and S0007 changed no file under `src/` (`git diff --stat` of merges `5b5ecd45` and `de4d396b`). So that trace still holds: every agent run goes through `run_sealed`, and every project command goes through `SealedProjectCommands`, now wrapped by `RecordingProjectCommands` (`src/factory/entry/wiring.py:272`). Each is reset first, and with an agent user each project command runs as that user. S0006 (docs only) is inside the Scope line "the docs from each story's docs criterion". S0007 (tests only) is inside "the tests each story names". No story built anything listed under Out of scope. The open item from the first acceptance is closed: the human's change 2 (the R12 sentence) is in `CLAUDE.md` since `d580a0f6 F0040 change 2`. Change 3, the operator's check after the rebuild: the night log records 3.3 as confirmed (`docs/runs/2026-10-12-overnight/night-log.md:940`: `~/.claude` holds only the factory's files, 116 KB). It records no result for 3.1, 3.2 or 3.4 to 3.7. Those are the operator's, and the operator guide's *Morning observations* now has a row for each (S0006). Gap: none.

## 2 Feature smoke test

The script is the first acceptance's, extended by three paths a user of the feature relies on: a command killed at its limit beside a process that keeps the output pipe open (S0001's kill, S0005's drain), a refused `sudo` (decision 4 and 11), and the default `end_leftovers` wiring. Setup: an agent user that no test runs as (`factory-test-other`); a real git checkout with a `Makefile`; an agent home under the run's temporary folder with a planted `CLAUDE.md`, an old transcript, a uv cache, a pylint cache and a login file; and a stand-in `sudo`. The stand-in records each call and then runs it, except the leftovers program, which it records and does not start: that program would end this user's own processes (`CLAUDE.md`, *Tests*). The fresh-home program ran for real, but only on the home inside the temporary folder. The `test` target starts `setsid sleep 23` (a holder of the pipe in a session of its own) and then sleeps 40 s under a 2 s limit. The script kills the holder itself afterwards.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; uv run python "$TMPDIR/smoke.py" "$d"
```

`$TMPDIR/smoke.py` (removed after the run):

```python
import os
import signal
import subprocess
import sys
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from factory.adapters.fake_hosting import FakeHostingService
from factory.application.sealed_runs import run_sealed
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, AgentRunResult
from factory.domain.errors import ProjectCommandError
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries

d = Path(sys.argv[1])
checkout = d / "checkout"
subprocess.run(["git", "init", "-q", "-b", "main", str(checkout)], check=True)
(checkout / "Makefile").write_text(
    "check:\n"
    "\t@echo \"env: token=$${FACTORY_TOKEN_FILE:-absent} home=$$HOME bytecode=$$PYTHONDONTWRITEBYTECODE link=$$UV_LINK_MODE\"\n"
    "\t@echo \"git folder mode: $$(stat -c %a .git)\"\n"
    "\t@echo \"planted CLAUDE.md: $$(test -e $$HOME/.claude/CLAUDE.md && echo present || echo gone)\"\n"
    "\t@echo \"uv cache: $$(test -e $$HOME/.cache/uv/pkg && echo kept || echo gone), pylint cache: $$(test -e $$HOME/.cache/pylint/x && echo kept || echo gone)\"\n"
    "\t@echo \"check: green (0.1 s)\"\n"
    "test:\n"
    "\t@setsid sleep 23 & echo $$! > " + str(d / "holder.pid") + "; echo started; sleep 40\n",
    encoding="utf-8",
)
for args in (["add", "Makefile"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "seed"]):
    subprocess.run(["git", "-C", str(checkout), *args], check=True)
(checkout / ".git").chmod(0o775)

home = d / "home"
for rel, text in {".claude/CLAUDE.md": "steer\n", ".claude/projects/p/t.jsonl": "{}\n", ".cache/uv/pkg": "wheel\n",
                  ".cache/pylint/x": "1\n", ".claude-token": "stand-in\n"}.items():
    (home / rel).parent.mkdir(parents=True, exist_ok=True)
    (home / rel).write_text(text, encoding="utf-8")

calls = d / "sudo.log"


def stand_in(name: str, refuse: bool) -> Path:
    sudo = d / name
    body = (
        f"#!{sys.executable}\nimport os, sys\nat = sys.argv.index('--')\nrest = sys.argv[at + 1:]\n"
        f"open({str(calls)!r}, 'a').write(' '.join(sys.argv[1:at]) + ' | ' + ' '.join(rest) + '\\n')\n"
    )
    if refuse:
        body += "sys.stderr.write('sudo: a password is required\\n'); sys.exit(1)\n"
    body += ("if 'factory.entry.leftovers' in rest:\n    sys.exit(0)  # recorded, never run: it would end this user's processes\n"
             "os.execvp(rest[0], rest)\n")
    sudo.write_text(body, encoding="utf-8")
    sudo.chmod(0o755)
    return sudo


sudo = stand_in("sudo", refuse=False)
(d / "state").mkdir()
settings = InstanceSettings(
    repository_url=str(d / "remote.git"), instance="factory-1", checkout=checkout, state_directory=d / "state",
    agent_home=home / ".claude", agent_user="factory-test-other", claude_login_file=home / ".claude-token",
    token_file=d / "hosting-token",
)
boundaries = build_boundaries(settings, "secret-token", hosting=FakeHostingService(), which=lambda name: str(sudo), confine_executable=None)

print("--- a project command, as the agent user")
result = boundaries.project_commands.run("check", time_limit=timedelta(seconds=60))
print(result.status, result.exit_status, result.targets)
print(result.output_tail.strip())
print("token in output:", "secret-token" in result.output_tail)
print("git folder mode after:", oct((checkout / ".git").stat().st_mode & 0o777))

print("--- a project command at its limit, beside a process that keeps the output open")
started = time.monotonic()
slow = boundaries.project_commands.run("test", time_limit=timedelta(seconds=2))
elapsed = time.monotonic() - started
print(slow.status, slow.exit_status, f"returned after {elapsed:.1f} s (limit 2 s, drain 5 s, holder 23 s)")
holder = int((d / "holder.pid").read_text().strip())
try:
    os.kill(holder, 0)
    print("holder still running after the call: True (the leftovers program, only recorded here, ends it in the image)")
    os.kill(holder, signal.SIGKILL)
except ProcessLookupError:
    print("holder still running after the call: False")

print("--- an agent run, after a run planted a file")
(home / ".claude" / "CLAUDE.md").write_text("steer\n", encoding="utf-8")
(home / ".claude" / "projects" / "p").mkdir(parents=True, exist_ok=True)
(home / ".claude" / "projects" / "p" / "old.jsonl").write_text("{}\n", encoding="utf-8")


def agent(request: AgentRunRequest) -> AgentRunResult:
    print("run sees CLAUDE.md:", (home / ".claude" / "CLAUDE.md").exists(), "old transcript:", (home / ".claude" / "projects" / "p" / "old.jsonl").exists(),
          "token kept:", (home / ".claude-token").exists(), "uv cache kept:", (home / ".cache" / "uv" / "pkg").exists())
    return AgentRunResult(end_reason="completed", decision="approval", entry="done", duration=timedelta(seconds=1))


request = AgentRunRequest(
    agent=AgentDefinition(name="coder", model="m", tools=[], budget_usd=Decimal(1), instructions="i"),
    prompt="p", allowed_decisions=["approval", "question"], time_limit=timedelta(minutes=1), working_directory=checkout,
)
print(run_sealed(boundaries, request, run=agent).result.decision)

print("--- the sudo calls, in order (sudo's own words | what it ran)")
for line in calls.read_text(encoding="utf-8").splitlines():
    words = line.split(" | ")
    rest = words[1].split()
    module = next((w for w in rest if w.startswith("factory.entry.")), None)
    print(words[0], "|", module or " ".join(rest[:3]) + " ... " + " ".join(rest[-3:]))

print("--- a refused sudo")
refused = build_boundaries(settings, "t", hosting=FakeHostingService(), which=lambda name: str(stand_in("sudo-refused", refuse=True)), confine_executable=None)
try:
    red = refused.project_commands.run("check", time_limit=timedelta(seconds=60))
    print("no error, a result:", red.status)
except ProjectCommandError as error:
    print("ProjectCommandError:", str(error).splitlines()[0][:140])

print("--- without an agent user")
plain = build_boundaries(settings.model_copy(update={"agent_user": None}), "t", hosting=FakeHostingService(), which=lambda name: str(sudo), confine_executable=None)
inner = vars(plain.project_commands)["_inner"]
print("agent_home:", plain.agent_home, "inner:", type(inner).__name__)
```

Output (exit 0):

```
Bytecode compiled 4164 files in 99ms
--- a project command, as the agent user
passed 0 [TargetTime(target='check', seconds=0.1)]
env: token=absent home=/tmp/factory-run-3be49f0c-5bd9-42d2-817a-b9b5381b844d/tmp.pKsOOSzGW1/home bytecode=1 link=copy
git folder mode: 755
planted CLAUDE.md: gone
uv cache: kept, pylint cache: gone
check: green (0.1 s)
token in output: False
git folder mode after: 0o755
--- a project command at its limit, beside a process that keeps the output open
time_limit None returned after 7.1 s (limit 2 s, drain 5 s, holder 23 s)
holder still running after the call: True (the leftovers program, only recorded here, ends it in the image)
--- an agent run, after a run planted a file
run sees CLAUDE.md: False old transcript: False token kept: True uv cache kept: True
approval
--- the sudo calls, in order (sudo's own words | what it ran)
-n -u factory-test-other | factory.entry.fresh_home
-n -u factory-test-other | timeout --signal=KILL 60s ... make --no-print-directory check
-n -u factory-test-other | factory.entry.leftovers
-n -u factory-test-other | factory.entry.fresh_home
-n -u factory-test-other | timeout --signal=KILL 2s ... make --no-print-directory test
-n -u factory-test-other | factory.entry.leftovers
-n -u factory-test-other | factory.entry.fresh_home
--- a refused sudo
ProjectCommandError: project command check failed: cannot reset the agent's home /tmp/factory-run-3be49f0c-5bd9-42d2-817a-b9b5381b844d/tmp.pKsOOSzGW1/home: sudo:
--- without an agent user
agent_home: None inner: MakeProjectCommands
```

Green. Each project command ran in this order: the reset, then `make` under the user's own `timeout --signal=KILL` and `env -i`, then the leftovers program. The command saw no `FACTORY_TOKEN_FILE`, saw the agent's `HOME`, `PYTHONDONTWRITEBYTECODE=1` and `UV_LINK_MODE=copy`, and found `.git` sealed (`755`, from `775`). The planted `CLAUDE.md` and the pylint cache were gone; the uv cache and the login were kept. The command killed at its 2 s limit came back as `time_limit` after 7.1 s, which is the limit plus `PIPE_DRAIN`, even though the holder would have kept the pipe open for 23 s. The leftovers program was called right after it. The agent run started after one reset and saw neither the planted file nor the old transcript. A refused `sudo` is a `ProjectCommandError`, not a red result. It fails at the reset, which comes first, so `make` never ran. Without an agent user, nothing is reset or switched. The smoke test cannot show the real `agent` user, the real `sudo` rule, the volume, the real leftovers program, or a provider-limit resume. Those are the operator's check 3 in `feature.md`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

S0006 and S0007 add nothing to what the first acceptance collected. Their coders, documenters and reviewers each wrote "none" or only pointed to the passages to change. The items still open:

- **Agent runs print uv's hardlink warning.** The S0006 smoke-tester's `uv run` (entry 13) printed the three-line `Failed to hardlink files ... set export UV_LINK_MODE=copy` warning and dismissed it. Decision 5 gives `UV_LINK_MODE=copy` to the project commands only (`src/factory/entry/wiring.py:428`). The two runtimes set `PYTHONDONTWRITEBYTECODE` and not the link mode (`claude_runtime.py:92`, `opencode_runtime.py:85`). F0027 removes `.venv` after every run, so the first `uv run` of almost every agent run syncs again and prints the warning into the agent's context. It is noise, not harm. No story: the agent run's environment is outside this feature's Scope, and the runtimes' environment tests pin the set (`SWITCHES` in `tests/adapters/test_claude_runtime.py:26`), so the change would need the human's leave. Yours to decide if agent runs should get the same switch.
- **`leftovers_command()` still starts without `-B`** (`wiring.py:305`; `fresh_home_command()` has it at `:312`). Unchanged since the first acceptance. In the image it does no harm, and the change would touch an F0027 test. Listed, no story.
- **`ProcessResult.output_abandoned` is read by no caller.** The human accepted it into `security/duplicates-baseline.txt` (night log, 04:00; `make duplicates` now prints `0 new, 38 known, 0 gone`). In the smoke test above, the abandoned pipe left no trace in the result the factory keeps. Whether the factory log should say so is still the human's question. No story.
- **Stale since F0040, in the human's files** (night log, 09:40). `CLAUDE.md`, *Tests*: the leftovers bullet's reason "(and under `make check`, the factory)" no longer holds. Since S0002 the factory's `make check` runs as the agent's user, so the program would end the check itself. F0027's `feature.md` *Out of scope* line and decision 1 are also stale. These are the human's files, so I propose no story.
- **The first acceptance's other items** (the coder cannot carry answers into the work item; in-process smoke tests for dangerous refusals; the checkout's default ACL) are unchanged and remain listed there.

## 5 Documentation as a whole

I read `README.md`, the operator guide's sections on the agent user, *Morning observations*, *A `time_limit` under `sudo`* and *The project commands run as `agent`*, the project guide's index and *Shared test helpers*, `processes-and-checks.md`, `watching.md`, and the F0040 entries of `docs/decisions.md`. S0006's corrections are in place: `processes-and-checks.md` *Rules of `run`* separates the cases with and without a user; `decisions.md` says "(`make`, as `agent` since F0040-S0002)"; both "Open:" lists carry the "closed on 2026-10-20" note; `watching.md` names the `CommandUser`. The four new *Morning observations* rows sit after "The home is fresh". S0007's two helpers are in *Shared test helpers*. The operator guide's description of the project commands (`operator-guide.md:435`) matches what the smoke test showed: the `sudo ... timeout ... env -i` start, the environment, the seal and the leftovers program. One stale sentence remains, and it is older than F0040. `docs/decisions.md:302` (the entry of 2026-10-16) still says under "Open:" that the kill of a timed-out agent under `sudo` is undecided and that "the human has not chosen". *The agent's own `timeout` kills a run under `sudo` at its time limit* (`decisions.md:396`) closed it, and the entry got no "closed by" note. F0040 did not write it, so I propose no story here. It is a one-line repair for whichever documentation story comes next. `README.md` needs nothing. No contradiction between documents and behaviour.

## 6 Decisions taken for the human

The 17 decisions of `feature.md` and the answers in S0001 to S0005's journals are listed in F0040-A0001, check 6, and stand as listed there. New since then:

1. **Decision 18** (the human, 2026-10-21): S0007's three exact assertions, beyond the standing leave. These are `LEFTOVERS_FAULT` imported in `tests/adapters/test_make_commands_user.py`, `is user` in `test_the_user_property_returns_what_the_constructor_was_given`, and `match=re.escape(refused)` in `tests/domain/test_agent_home.py`.
2. **S0006's wording:** the exact sentences and the four observation rows were set by the human when refining the story, and the night log (07:10) records three edits made at the pre-check, including a fifth stale sentence at `decisions.md:775`.
3. **S0007, tests stage:** the tester made the whole change itself and wrote no red tests, because the story adds no behaviour (entry 5). The coder changed nothing (entry 7). The reviewer accepted this split.
4. **The order** (the human, morning answers, night log 08:10): F0038 may start before F0040-S0007, and F0040's second acceptance follows S0007.

Earlier tests changed, each with its leave. From the first acceptance: `tests/entry/test_wiring.py` and `tests/test_wrapper_search.py`, both under decision 14. From S0007 (merge `de4d396b`, checked against its diff), under the standing leave to move a shared helper: `tests/adapters/test_make_commands_user.py`, `tests/adapters/test_sudo_agent_home.py`, `tests/application/test_agent_home_resets.py`, `tests/application/test_checkout_preparer_seal.py`, `tests/application/test_nested_repositories.py` and `tests/application/test_sealed_project_commands.py`. Under decision 18: the three assertions in `test_make_commands_user.py` and `tests/domain/test_agent_home.py`. The S0007 reviewer named each one (entry 9). S0006 changed no test. Finding: none.

## 7 Slow checks

The project offers nothing beyond `make check` here: no image scan or SBOM target. `make mutants` belongs to check 3. `make check` was green as I found it: `test: green (64.8 s)`, coverage 99.14 %, `check: green`. `make duplicates`: `0 new, 38 known, 0 gone`. From `.reports/junit.xml`: 6464 tests, 747.0 s summed over the workers. F0040's test modules hold 139 tests and 51.6 s, the same as at the first acceptance; S0007 only moved helpers. The slowest tests in the suite are older time-limit tests: `test_opencode_sudo_time_limit` at 11.5 s for each of two rows, and three `test_process_session` rows at 10.1 s each. Disk: now `/work` 968.2 GB free and 0.5 GB used, against 968.7 GB free and 0.5 GB used at `disk start`. Used space did not grow. The 0.5 GB less free space shows on `/work`, `/state` and `/tmp` alike, so it is the shared host disk and not this feature.

## 8 Cost

86 runs, 108.2 min, 716 turns, $27.95 for seven stories: S0001 22 runs, $7.77; S0004 14 runs, $6.12; S0003 17 runs, $5.38; S0002 14 runs, $3.88; S0005 7 runs, $2.28; S0007 6 runs, $1.66; S0006 6 runs, $0.86. The two stories since the first acceptance each took the minimum of 6 runs, with no review round and no question. Together they cost $2.52. S0001 stands out as before ($7.77, 22 runs). Its intake left four Interface rules without criteria, and three review rounds each added a criterion that needed only a test, which took it past the round cap. Human interventions: 13 questions answered (11 questions, 1 round cap, 1 crash cap), 0.3 h waited. All 13 came in S0001 to S0005; S0006 and S0007 asked none. Decision 18's leave was granted in `feature.md` before S0007 started, not as a question. S0001 needed the human most (4 of the 13): the "missing program" row, `agent` used as the "other" user in the tests, the recipe line without seconds, and the round cap (its entries 9, 15, 16 and 42). S0004 hit the crash cap: two `doing` crashes, caused by `__pycache__` folders with mode `755`.

## Proposed stories

None. The first acceptance's findings were closed by S0006 and S0007. What remains under check 4 is either outside this feature's Scope (the agent run's uv link mode), already decided by the human (`output_abandoned` in the baseline), or in the human's own files (`CLAUDE.md`, F0027's `feature.md`).

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed

   1 Scope: every Scope item is on `main`. S0006 and S0007 changed only docs and tests, so the first acceptance's trace still holds: every agent run and every project command is reset first, and with an agent user every project command runs as that user. The human's change 2 to `CLAUDE.md` is now on `main` (`d580a0f6`). The night log records the operator's check 3.3 as done; 3.1, 3.2 and 3.4 to 3.7 have no recorded result yet. Gap: none.
   2 Feature smoke test: green. I ran the real `build_boundaries` with an agent user and a stand-in `sudo`. A project command ran in the order reset, `make` (under `timeout` and `env -i`), leftovers program. It saw no token and found `.git` sealed. The planted `CLAUDE.md` and the pylint cache were gone; the uv cache and the login were kept. A command killed at its 2 s limit, beside a process holding its output open, returned `time_limit` after 7.1 s (the limit plus `PIPE_DRAIN`). A sealed agent run started in a clean home. A refused `sudo` gave a `ProjectCommandError`. Without an agent user nothing is reset or switched.
   3 Mutation testing: by sweep, not run here.
   4 What the stories noticed: S0006 and S0007 added nothing new. Still open, no story for any of them: (a) agent runs lack `UV_LINK_MODE=copy`, so uv prints its hardlink warning into the agent's context (outside this feature's scope, and the change touches a pinned runtime test). (b) `leftovers_command()` still starts without `-B`. (c) No caller reads `output_abandoned`; the human has already accepted it in the duplicates baseline. (d) Sentences made stale by F0040 in the human's own files (`CLAUDE.md`'s leftovers reason, F0027's `feature.md`).
   5 Documentation: S0006's five corrections and four *Morning observations* rows are in place, and S0007's two helpers are listed. No contradiction between docs and behaviour. One older stale "Open:" at `decisions.md:302` (the timeout under `sudo`, closed at `:396`) predates F0040, so I listed it without a story.
   6 Decisions for the human: the first acceptance's list stands. New: decision 18 (S0007's three exact assertions); S0006's wording set when the human refined it; S0007's tester made the whole change with no red tests; the human's order answer. S0007 changed earlier tests in seven files: six under the standing leave, and three assertions under decision 18 (in two files, one of them also among the six). The reviewer named each. Finding: none.
   7 Slow checks: nothing is offered beyond `make check`, which is green (test 64.8 s, coverage 99.14 %; duplicates 0 new). F0040's 139 tests take 51.6 s. Disk used did not grow; the 0.5 GB less free space is the shared host disk.
   8 Cost: 86 runs, $27.95. S0006 ($0.86) and S0007 ($1.66) each took the minimum 6 runs and asked no question. S0001 is still the dearest ($7.77, 22 runs) and needed the human most (4 of the 13 interventions). 13 questions answered (11 questions, 1 round cap, 1 crash cap); 0.3 h waited.
3. factory: done (pull request merged); cost: 1 runs, 5.6 min, 33 turns, 96424 tokens in (2114996 more from cache), 26207 out, $1.72
