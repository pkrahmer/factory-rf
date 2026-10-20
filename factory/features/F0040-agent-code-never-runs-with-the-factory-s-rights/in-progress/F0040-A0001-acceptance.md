---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 366
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T22:33:51.657887Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T22:42:46.715609Z'
  stage: acceptance
  run: 035e5b461c4c4381abb2d0b8e5245434
stories: [F0040-S0001, F0040-S0002, F0040-S0003, F0040-S0004, F0040-S0005]
outcome: null
---

# Acceptance of Agent code never runs with the factory's rights

## Recommendation

**accepted with stories.** All five stories are on `main`, and every Scope item has its code. `make check` is green. The feature's smoke test passed: it ran the real `build_boundaries` with an agent user, then one project command and one sealed agent run. The command ran through `sudo` as that user, with only the allowed environment and the seal held, between a fresh-home reset and the leftovers program, and the agent run started in a home without the planted files. Two findings are worth stories, and neither is a broken promise. Four older sentences in the docs still describe the time before F0040, and the operator guide lacks the after-merge checks that `feature.md` asks for (S0006). The reviewers left test notes that nobody acted on (S0007). Two things are open and stay with the human: their change 2 to `CLAUDE.md` (the R12 sentence, due after S0004's merge) is not on `main` yet, and the operator's real check after the rebuild is still to do.

## 1 Scope

Every Scope bullet of `feature.md` has its code on `main`. I checked each named symbol in `src/factory`: `CommandUser` and `MakeProjectCommands.user` (`adapters/make_commands.py`); `SealedProjectCommands` with its `home` (`application/sealed_runs.py`); `project_command_environment`, `FRESH_HOME_MODULE`, `UV_CACHE_FOLDER`, `fresh_home_command`, `agent_home_of` (`entry/wiring.py`); `Boundaries.agent_home`; `inside_home`, `kept_paths`, `fate`, `removed_when_empty` and `FRESH_HOME_PREFIX` (`domain/agent_home.py`), with `settings.py` using `inside_home`; `own_entry` and `clear_home` (`adapters/home_files.py`); `entry/fresh_home.py`; `AgentHome`; `SudoAgentHome` and `FRESH_HOME_TIME_LIMIT`; `LOGIN_STATE_FILE` in both runtimes; and `PIPE_DRAIN` with `ProcessResult.output_abandoned` (`adapters/process.py`). No story goes outside the scope, and no Out-of-scope item was built. I followed every caller to check the Goal ("no code an agent wrote runs as `factory`, and no run inherits the home"). The only callers of `agent_runtime.run` are `run_sealed` (`application/stage.py:112`, the preflight probe at `application/preflight.py:251`) and `PatientRuns`, which runs inside `run_sealed`. The only callers of `project_commands.run` are `KnownResults._run` and the preflight's `lint` (`preflight.py:526`). With an agent user, both reach `SealedProjectCommands` (`wiring.py:341-362`). So every agent run and every project command is reset first, and every project command runs as the agent. `preflight.py:408` (`agent_runtime.version()`) is a version call, not a run, and is outside the rule. Gap: none. Open, and the human's: change 2 of *The human's changes* (the R12 sentence in `CLAUDE.md`, due after S0004's merge) is not on `main`. `CLAUDE.md`'s R12 bullet has no "every project command runs as the agent's user too", and `git log -- CLAUDE.md` ends at `4e210df9 F0040 change 1`. Change 3, the operator's check after the rebuild, is still to do.

## 2 Feature smoke test

What a user of the feature relies on, end to end, through the real wiring. The script takes an instance with an agent user (`factory-test-other`, a user no test runs as), a real git checkout with a `Makefile`, an agent home under the run's temporary folder with a planted `CLAUDE.md`, an old transcript, a uv cache, a pylint cache and a login file, and a stand-in `sudo` that records each call. The stand-in runs every call, except the leftovers program: it records that call and does not start it, because the leftovers program would end this user's own processes (`CLAUDE.md`, *Tests*). The script builds the boundaries with `build_boundaries`, runs `check` through `boundaries.project_commands`, runs an agent run through `run_sealed` after a run "planted" files again, and then builds the boundaries without an agent user. The fresh-home program ran for real, but only on the home inside the temporary folder.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
cat > "$d/smoke.py" <<'EOF'
import subprocess
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from factory.adapters.fake_hosting import FakeHostingService
from factory.application.sealed_runs import run_sealed
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, AgentRunResult
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
    "\t@echo \"check: green (0.1 s)\"\n",
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
sudo = d / "sudo"
sudo.write_text(
    f"#!{sys.executable}\nimport os, sys\nat = sys.argv.index('--')\nrest = sys.argv[at + 1:]\n"
    f"open({str(calls)!r}, 'a').write(' '.join(sys.argv[1:at]) + ' | ' + ' '.join(rest) + '\\n')\n"
    "if 'factory.entry.leftovers' in rest:\n    sys.exit(0)  # recorded, never run: it would end this user's processes\n"
    "os.execvp(rest[0], rest)\n",
    encoding="utf-8",
)
sudo.chmod(0o755)
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

print("--- an agent run, after a run planted a file")
(home / ".claude" / "CLAUDE.md").write_text("steer\n", encoding="utf-8")
(home / ".claude" / "projects" / "p").mkdir(parents=True)
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
    print(words[0], "|", module or " ".join(rest[:4]) + " ... " + " ".join(rest[-3:]))

print("--- without an agent user")
plain = build_boundaries(settings.model_copy(update={"agent_user": None}), "t", hosting=FakeHostingService(), which=lambda name: str(sudo), confine_executable=None)
print("agent_home:", plain.agent_home, "inner:", type(vars(plain.project_commands)["_inner"]).__name__)
EOF
uv run python "$d/smoke.py" "$d" 2>&1
```

Output (exit 0):

```
Bytecode compiled 4164 files in 80ms
--- a project command, as the agent user
passed 0 [TargetTime(target='check', seconds=0.1)]
env: token=absent home=/tmp/factory-run-936598dd-5441-44b1-aa4e-c700c8fe0805/tmp.bXimf6Qkow/home bytecode=1 link=copy
git folder mode: 755
planted CLAUDE.md: gone
uv cache: kept, pylint cache: gone
check: green (0.1 s)
token in output: False
git folder mode after: 0o755
--- an agent run, after a run planted a file
run sees CLAUDE.md: False old transcript: False token kept: True uv cache kept: True
approval
--- the sudo calls, in order (sudo's own words | what it ran)
-n -u factory-test-other | factory.entry.fresh_home
-n -u factory-test-other | timeout --signal=KILL 60s env ... make --no-print-directory check
-n -u factory-test-other | factory.entry.leftovers
-n -u factory-test-other | factory.entry.fresh_home
--- without an agent user
agent_home: None inner: MakeProjectCommands
```

Green. For a project command, the reset came first, then `make` under the user's own `timeout` with `env -i`, then the leftovers program. The command saw no `FACTORY_TOKEN_FILE`, saw the agent's `HOME`, `PYTHONDONTWRITEBYTECODE=1` and `UV_LINK_MODE=copy`, and found `.git` sealed (`755`, from `775`). The planted `CLAUDE.md` and the pylint cache were gone; the uv cache and the login were kept. The agent run was reset once before it started (no `CLAUDE.md`, no old transcript), and the kept paths stayed. Without an agent user nothing is reset or switched. The agent run's own leftovers call is missing from the log because the script passed `run=` in place of the runtime. That call is F0027's, and the runtimes' tests cover it. The smoke test cannot show the real `agent` user, the real `sudo` rule, the volume or a provider-limit resume. Those are the operator's check 3 in `feature.md`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- **`leftovers_command()` starts without `-B`** (S0004 coder, entry 21; S0004 documenter, entry 36). `src/factory/entry/wiring.py:307-309` gives `[sys.executable, "-I", "-m", "factory.entry.leftovers"]`, while `fresh_home_command()` got `-B` after the human's notes (S0004 entries 14 and 15: `-I` ignores `PYTHONDONTWRITEBYTECODE`). `docs/project-guide/watching.md:264` and `docs/operator-guide.md:127` describe it the same way. In the image the interpreter is `/opt/factory/.venv/bin/python`, built as root, so `agent` cannot write bytecode beside it, and no test starts the real `leftovers_command()` (`tests/entry/test_leftovers.py:213` already uses `-I -B`). No story: the harm needs a factory run from a checkout as the agent, and the change touches `tests/entry/test_wiring_leftovers.py`, an F0027 test, which would need the human's leave. Yours to decide if you want the two commands to match.
- **Test notes the reviewers left to the acceptance** (S0001 entry 48; S0002 entry 27; S0003 entry 31): a fourth and a fifth local stand-in `sudo` (`tests/adapters/test_make_commands_user.py:33`, `tests/adapters/test_sudo_agent_home.py:31`); `RecordingLog` imported from another test module by three modules; `LEFTOVERS_FAULT` restated in a test (`test_make_commands_user.py:22`); `.user` compared with `==` where criterion 8 says "is" (`:305`); `match=refused` read as a regular expression (`tests/domain/test_agent_home.py:86`). → proposed S0007. The two `home` fixtures (S0003 reviewer) differ: one builds the files and the other does not. They stay. The inline `ProcessResult` builders (S0004 entries 31 and 34) stay a note, as the human answered in entry 32.
- **Stale doc sentences** (S0001 documenter, entry 50: the "every process of its session is killed" rule; plus what I found under check 5). → proposed S0006.
- **`make duplicates`: 6 new, 33 known, 3 gone** (S0002 entry 10, S0003, S0004, S0005; I reran it). One finding is F0040's: vulture marks `ProcessResult.output_abandoned` (`process.py:53`) as unused, because no caller under `src/` reads it, only the tests. As built, nothing in the factory log says that a call's output was abandoned. That matches decision 17 ("every caller keeps its rules"), but the operator cannot see it either. Yours to decide whether a log line is wanted; I propose no story. The other five (four runtime similarities, `ManualWaiter`) and the three gone entries of `security/duplicates-baseline.txt` are older than F0040, and the baseline is the human's file.
- **The coder cannot carry the human's answers into the work item** (S0001 entries 15 and 22; S0004 entries 17 and 21; this led to S0004's question in entry 31). It is a pipeline matter (`factory/`, the write paths), not this feature's, and is listed here for the human.
- **A smoke test must not ask for a real run of the fresh-home program on `/`** (S0003 entries 35, 36 and 38): the session's permission classifier refused it, and the human accepted an in-process check. The story is archived. This is a lesson for drafting smoke tests: run a dangerous refusal in-process.
- **The checkout's default ACL** (S0004 entry 15): the human gave the checkout's folders a default ACL that keeps new entries group-writable, after two crashes of `doing` in which `git clean -X` failed on `__pycache__` folders with mode `755`. That is a change on the machine, outside the repository. See check 6.
- Not taken up: S0001's coder noted that the Description and criteria 1 and 9 still had their old wording (entry 22). The story is archived, and its tests follow the answers. S0003's coder noted that a home that cannot be listed records its fault under `.`. No criterion covers that, and it does no harm. S0005's documenter called the operator guide's intro paragraph "one very long status list". That is not F0040's.

## 5 Documentation as a whole

I read `README.md`, `docs/operator-guide.md` (*The agent runs as a second user*, *The home is cleared before every run*, *The project commands run as `agent`*, *Morning observations*), `docs/project-guide/processes-and-checks.md`, `agents.md`, `watching.md` and the F0040 entries of `docs/decisions.md`. The new sections agree with each other and with the code. The operator guide's reset command (`-I -B`), the kept paths and the two error texts match `SudoAgentHome` and `agent_home_of`. What the stories left behind:

- `docs/project-guide/processes-and-checks.md:48` (*Rules of `run`*): "a command ended by the `time_limit` ... every process of its session is killed". This holds without a user. With a user, the user's own `timeout` kills `make`'s group and the leftovers program ends the rest (*Running as another user*, in the same file).
- `docs/decisions.md:463`: "A project command's git (`make` as `factory`) does read it". Since S0002 `make` runs as `agent`.
- `docs/decisions.md:398` (F0012-S0025): its "Open:" says the files the agent may add to `~/.claude` stay writable "and `claude` reads them (a user `CLAUDE.md`, skills)". S0004 closed this, but only the entry of 2026-10-16 got its "closed by" note.
- `docs/project-guide/watching.md:264`: `leftovers_command()` goes to "every agent runtime". It also goes to the project commands' `CommandUser`.
- Missing: the operator's checks 3.1, 3.2, 3.5 and 3.7 of `feature.md` (a stage's `make` runs as `agent`, no `cannot reset` in the log, the shared `.venv` stays group-writable, a check at its limit leaves no `agent` process) are in `feature.md` only. The operator guide's *Morning observations* has the fresh-home row (3.3) and the token row (3.4), but not these four.

None of these misleads a user about what the factory does to their token or their home. They are older sentences that no story's docs criterion reached. → proposed S0006. `README.md` needs nothing: nothing a newcomer runs has changed.

## 6 Decisions taken for the human

From `feature.md` (decisions 1 to 17 and *The human's answers*), to accept or revisit:

1. The project commands run as `agent` through `sudo`, `timeout` and `env -i`, without `factory-confine` (decision 1, answer A).
2. `launch` and the leftovers helpers are reused, not copied (2).
3. The kill at the limit is the agent's own `timeout`; the factory's kill waits 30 s more (3).
4. A refused `sudo` is a `ProjectCommandError`, not a red check (4).
5. The command's environment is the agent run's plus `PYTHONDONTWRITEBYTECODE=1` and `UV_LINK_MODE=copy` (5; question B, answer A).
6. The agent's own login files stay readable by project commands (6).
7. Each project command runs with the git folder sealed (7).
8. A fresh home by clearing before each stage run and each project command, not a new `HOME` (8, answer A).
9. Kept: the logins and **uv's package cache, a channel from one run to the next check that the human accepted** (9, answer B, against the pre-check).
10. The reset comes before, not after, so the last transcript stays until the next run or command (10).
11. A failed reset stops the run with `AgentRuntimeError` (11).
12. The image, entrypoint, compose file, sudoers and volume stay unchanged (12).
13. The program decides by ownership and has no default home (13).
14. Two one-line leaves on earlier tests (14).
15. The leftovers program runs after every project command (16, question A, answer A).
16. A call reads its output for at most 5 s after its own process ended, for every call (17, question D, answer B, against the pre-check).
17. `FRESH_HOME_TIME_LIMIT` stays 60 s. The stated worst case is docs 64 of 60 minutes of the lease (question C, answer A).

From the stories' journals:

- S0001 entry 4: criterion 9's rows (refusal wins over a leftovers fault; failed; refused) and the reuse of `leftovers_fault` as F0027 tests it. Entry 9: the "missing program" row means "the leftovers call cannot be started". Entry 16: the tests use `OTHER_USER` as the other user (the stages run as `agent`), and criterion 1's recipe ends `check: green (0.1 s)`; `target_times` is unchanged. Entry 42 (round cap): go on, fix only the `run` docstring, and leave the reviewer's notes to the acceptance.
- S0002 entry 4: an inner `ValueError` row; "or the removal" dropped; `check_seal` before the removal. Entry 19: the story's own wiring test looks up concrete classes (`type-abstract`).
- S0003 entry 4: three new criteria (a `../x` state file, the modes of other users' entries kept, a foreign file in an owned folder). Entry 17: `--home //` and `--home /home/..` are refused. Entry 36: an in-process check replaces the smoke test's real run on `/`.
- S0004 entry 4: five intake answers (the failure line, the `Launch` fields with 90 s, the opencode row, the `SUDO_EXECUTABLE` row, GNU `timeout` at `/usr/bin/timeout`). Entries 14 and 15: the fresh-home program starts with `-I -B`, and the checkout's folders now carry a default ACL (a change on the machine, outside git; worth recording in the operator guide if it is to survive a rebuild of the volume). Entry 32: the reviewer may add `-B` in the work item's five places.
- S0005 entry 4: five intake answers (a limit during the drain is `timed_out`; `on_line` and the last line; a stop and a raise beside a holder; no separate 0.05 s test; the no-limit row for `run_streaming`).

Earlier tests changed, each with its leave: `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` (S0003, decision 14) and `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module` (S0004, decision 14). I checked the merge diffs of the five pull requests (`d41e5c2d`, `e1e91b99`, `97876aae`, `42fadf84`, `76192dfd`). No other existing file under `tests/` is modified; everything else under `tests/` is new. Finding: none.

## 7 Slow checks

The project offers nothing beyond `make check` here: no image scan or SBOM target (the Makefile's targets are `check lint types layers sast secrets licenses test duplicates documents mutants`). `make mutants` belongs to check 3. `make check` was green as I found it (`test: green (62.0 s)`, coverage 99.14 %, `check: green`). From `.reports/junit.xml`: 6403 tests, 737.6 s summed over the workers. F0040's eight new test modules hold 170 tests and 51.5 s. Their slowest are `test_make_commands_user::test_the_factory_s_own_kill_waits_the_grace_beyond_the_limit` (5.0 s), `test_process_drain::test_the_read_after_the_kill_is_bounded_by_the_drain[holder]` (5.0 s) and `test_make_commands_user::...followed_by_the_leftovers_program[time-limit]` (3.0 s). The suite's slowest tests are older time-limit tests (`test_opencode_sudo_time_limit` 11.5 s, `test_process_session` 10.1 s). Disk: now `/work` 968.7 GB free and 0.0 GB used, against 968.9 GB free and 0.5 GB used at the previous record (`disk start`). Nothing grew. The 0.2 GB less free space is the shared host disk (`/work`, `/state` and `/tmp` show the same free figure). The 0.5 GB that `/work` no longer uses fits the `.venv` that F0027 removes after a run. The feature's own disk effect, the first reset emptying `claude-home` (about 222 MB on `self`), is not on these lines. It is the operator's check 3.3.

## 8 Cost

74 runs, 97.4 min, 641 turns, $25.43 for five stories: S0001 22 runs, $7.77; S0004 14 runs, $6.12; S0003 17 runs, $5.38; S0002 14 runs, $3.88; S0005 7 runs, $2.28. Two stories stand out:

- **S0001**, the dearest, and the one that needed the human most (4 of the 13 interventions). Its intake left four Interface rules without criteria. Its tester could not write the "missing program" row without choosing what it meant. Its coder found the tests used `agent` as the "other" user while the stages themselves run as `agent`, and found that a recipe line without seconds gives no target (entry 15). After that, three review rounds each added a criterion that needed only a test, which took it past the round cap (entry 41). One `doing` run crashed (entry 13).
- **S0004** crashed twice in `doing` (entries 10 and 12), which hit the crash cap. A test child started with `-I` and without `-B` wrote `__pycache__` with mode `755` into `src/`, and the restore's `git clean -X` failed. The human repaired it and added a default ACL.

The pattern across S0001, S0003 and S0004 is a reviewer adding a criterion that only needs its test, which costs a doing → tests → doing → review loop each time. That was 3, 2 and 1 extra rounds. Human interventions: 13 questions answered (11 questions, 1 round cap, 1 crash cap): S0001 4, S0003 3, S0004 3, S0002 2, S0005 1. The stories waited 0.3 h for them in total.

## Proposed stories

- `backlog/F0040-S0006-the-documents-say-that-project-commands-run-as-the-agent-and-how-to-check-it.md`: corrects the four sentences that still describe project commands run as `factory` and a home that keeps planted files, and adds four of the operator's after-merge checks to the *Morning observations* (checks 4 and 5).
- `backlog/F0040-S0007-the-tests-of-the-agent-s-user-share-their-stand-in-sudo-and-recording-log.md`: moves the two new stand-in `sudo` scripts and `RecordingLog` to shared modules under the standing leave, and makes three assertions exact under a leave the human would grant when refining (check 4, the reviewers' notes).

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 2 stories proposed (F0040-S0006, F0040-S0007).

   1 Scope: every Scope item is on `main`. Every agent run (`run_sealed`) and every project command (`SealedProjectCommands`) is reset first, and with an agent user every project command runs as that user. No story goes outside the scope. Open, both the human's: change 2 to `CLAUDE.md` (the R12 sentence) is not on `main` yet, and the operator's check 3 after the rebuild is still to do.
   2 Feature smoke test: green. I ran the real `build_boundaries` with an agent user and a stand-in `sudo`, then one project command and one sealed agent run. The `sudo` calls came in the order fresh_home, `make ... check` (under `timeout` and `env -i`), leftovers, fresh_home. The command saw no `FACTORY_TOKEN_FILE` and found `.git` sealed. The planted `CLAUDE.md`, the old transcript and the pylint cache were gone; the uv cache and the login were kept. Without an agent user nothing is reset or switched.
   3 Mutation testing: by sweep, not run here.
   4 What the stories noticed: the reviewers' test notes were left to the acceptance (two more local stand-in `sudo` scripts, `RecordingLog` imported across test modules, `LEFTOVERS_FAULT` restated, `==` for `is`, `match` without `re.escape`), so I proposed S0007. `leftovers_command()` still starts without `-B`; it does no harm in the image, so it is listed with no story. `output_abandoned` is read by no caller, so it never reaches the log; that is listed for the human. The coder cannot write the work item, which is a pipeline matter for the human.
   5 Documentation: the new sections agree with the code. Four older sentences still describe the time before F0040 (`processes-and-checks.md:48`, `decisions.md:463`, the "Open:" in `decisions.md:398`, `watching.md:264`). The operator's after-merge checks 3.1, 3.2, 3.5 and 3.7 are not in the *Morning observations*. Proposed S0006.
   6 Decisions for the human: the feature's 17 decisions and the answers in the story journals are gathered in one list. Two earlier tests were changed, both under decision 14's leave (`tests/entry/test_wiring.py`, `tests/test_wrapper_search.py`); no other earlier test file was modified. Also listed: the default ACL on the checkout, a change the human made on the machine (S0004 entry 15).
   7 Slow checks: none offered beyond `make check`, which is green (test 62.0 s, coverage 99.14 %). F0040's 170 new tests take 51.5 s, the slowest 5.0 s. Disk: `/work` uses 0.0 GB against 0.5 GB at `disk start`, and nothing grew that the feature does not explain.
   8 Cost: 74 runs, $25.43. The dearest story was S0001 ($7.77, 22 runs: 4 of the 13 human interventions, the round cap and 1 crash). S0004 hit the crash cap: two crashes of `doing` from `__pycache__` with mode 755. Reviewers adding criteria that only needed a test cost 6 extra rounds across three stories. 13 questions answered (11 questions, 1 round cap, 1 crash cap); the stories waited 0.3 h.
