---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 356
comments_read: [6297132845]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T15:38:05.333239Z'
  stage: acceptance
- number: 2
  speaker: factory
  kind: crash
  at: '2026-10-20T16:44:35.650555Z'
  stage: acceptance
- number: 3
  speaker: factory
  kind: started
  at: '2026-10-20T16:44:37.093008Z'
  stage: acceptance
- number: 4
  speaker: factory
  kind: crash
  at: '2026-10-20T17:25:59.173641Z'
  stage: acceptance
- number: 5
  speaker: factory
  kind: question
  at: '2026-10-20T17:25:59.173641Z'
  stage: acceptance
  blocked: crash_cap
- number: 6
  speaker: human
  kind: comment
  at: '2026-10-20T17:36:15.127696Z'
  stage: acceptance
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-20T17:36:33.162209Z'
  stage: acceptance
- number: 8
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T17:51:37.137138Z'
  stage: acceptance
  run: b641dae061b1465989087dcd733646d9
- number: 9
  speaker: factory
  kind: done
  at: '2026-10-20T17:52:58.014459Z'
  stage: done
stories: [F0027-S0001, F0027-S0002, F0027-S0003]
outcome: accepted
---

# Acceptance of Nothing a run leaves behind reaches the checks

## Recommendation

**accepted with stories.** Both routes into the checks are closed, and the real wiring shows it end to end. After a call as another user the runtime starts the leftovers program from `/`, and that program refuses before its first signal when it does not run as the user it names. A run that returned leaves no ignored path. The tick's restore removes what a raised run left, including a file hidden by the branch's own `.gitignore`. `make check` is green. The findings are of weight but no broken promise. In practice the removal turned an agent-made bytecode folder into two crashes of this very acceptance and a repository stop, and the operator guide does not say so. That gives one test story, one documentation story and one small story of test hygiene.

## 1 Scope

None. Every Scope line has its story, and the code the stories name exists as their Interfaces say. S0001: `ProcessEntry.uid` and `parse_stat(..., *, uid)` in `src/factory/domain/sessions.py`; `read_process_table`, `own_identity` and `signal_every_other` in `src/factory/adapters/process.py`; the new `src/factory/domain/leftovers.py` and `src/factory/entry/leftovers.py`. S0002: `Starters.leftovers`, `leftovers_due`, `leftovers_launch`, `leftovers_fault` and `LEFTOVERS_TIME_LIMIT` in `agent_launch`; the keyword `leftovers` in both runtimes, run after the call and before the temporary folder's removal; `leftovers_command()` and `build_boundaries(..., end_leftovers=True)`. S0003: `Git.remove_ignored()` and `GitCli.remove_ignored()` (`clean --quiet --force --force -d -X`), called in `run_sealed` after the `try`/`finally` and in `Tick._restore_checkout` between `reset_to("HEAD")` and the switch to `main`. The source files the three stories' commits changed on `origin/main` are exactly these twelve, and nothing outside the Scope. No story touches an Out of scope item. S0004 was withdrawn by decision 3 (answer B), and `factory/pipeline.yml` has no `kept_ignored`. The goal is reached as far as the stories can reach it. The human's change 4 (the real `kill(-1)` as `agent` in the image, and the rebuild cost) is the human's and is recorded in no journal yet.

## 2 Feature smoke test

The user's walk-through: an agent run through the real wiring (`build_boundaries` with stand-in `sudo` and `claude`, no confinement wrapper, the real `leftovers_command()` and the real `factory.entry.leftovers`) hides files in every ignored place the feature names. First as the factory's own user (no program is due), then as another user (the program is due, and refuses, because the stand-in `sudo` does not switch users). Then one real `Tick.run()` restores the checkout. The program is never run as the user it names, and `signal_every_other` is never called (`CLAUDE.md`, *Tests*).

Command: `bash feature_smoke.sh`, from a temporary folder, with this script:

````bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
cd /work/checkout
echo "== the real program, as a user it does not run as, and without arguments"
uv run -q python -I -B -m factory.entry.leftovers --user factory-smoke-nobody; echo "status $?"
uv run -q python -I -B -m factory.entry.leftovers; echo "status $?"
echo "== a run, its leftovers and the restore, through the real wiring"
uv run -q python -B - "$d" <<'EOF'
import dataclasses, json, os, pwd, shutil, subprocess, sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from factory.adapters.fake_hosting import FakeHostingService
from factory.application.sealed_runs import run_sealed
from factory.application.tick import Tick
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest
from factory.domain.errors import AgentRuntimeError
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import agent_run_environment, build_boundaries, handler_factory, production_environment

d = Path(sys.argv[1])
repo = Path("/work/checkout")


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args], cwd=cwd, check=True, capture_output=True)


def script(name: str, body: str) -> Path:
    path = d / "bin" / name
    path.parent.mkdir(exist_ok=True)
    path.write_text(f"#!{sys.executable} -B\n{body}", encoding="utf-8")
    path.chmod(0o755)
    return path


def files(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.relative_to(root).parts[0] not in {".git", "factory", "claude"})


git(d, "init", "-q", "--bare", "--initial-branch=main", "remote.git")
git(d, "clone", "-q", str(d / "remote.git"), "human")
human = d / "human"
(human / ".gitignore").write_text(".venv/\n__pycache__/\n", encoding="utf-8")
(human / "src").mkdir()
(human / "src" / "mod.py").write_text("x = 1\n", encoding="utf-8")
shutil.copytree(repo / "factory", human / "factory", ignore=shutil.ignore_patterns("features"))
(human / "factory" / "features").mkdir()
(human / "factory" / "features" / ".gitkeep").write_text("", encoding="utf-8")
shutil.copytree(repo / "claude", human / "claude")
git(human, "add", "-A"); git(human, "commit", "-q", "-m", "base"); git(human, "push", "-q", "origin", "main")
git(human, "switch", "-q", "-c", "work-item/F9999-S0001")
(human / "src" / ".gitignore").write_text("x.dat\n", encoding="utf-8")
git(human, "add", "-A"); git(human, "commit", "-q", "-m", "branch"); git(human, "push", "-q", "origin", "work-item/F9999-S0001")
git(d, "clone", "-q", str(d / "remote.git"), "checkout")
checkout = d / "checkout"
git(checkout, "switch", "-q", "work-item/F9999-S0001")
shutil.copytree(repo / "claude" / "agents", d / "agents-home" / "agents")

reply = json.dumps({"type": "result", "subtype": "success", "is_error": False, "num_turns": 1, "total_cost_usd": 0.1, "duration_ms": 100, "usage": {"input_tokens": 1, "output_tokens": 1}, "permission_denials": [], "structured_output": {"decision": "doing", "entry": "Done."}})
writes = {".venv/lib/standin.pth": "import os\n", "src/__pycache__/mod.cpython-312.pyc": "standin\n", "tests/hidden/.gitignore": "*\n", "tests/hidden/conftest.py": "standin\n", "src/x.dat": "hidden by the branch\n", "src/new.py": "y = 2\n"}
claude = script("claude", f"from pathlib import Path\nfor name, text in {writes!r}.items():\n    p = Path(name); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)\nprint({reply!r})\n")
sudo = script("sudo", f"import os, sys\nrest = sys.argv[sys.argv.index('--') + 1:]\nopen({str(d / 'sudo.log')!r}, 'a').write(('program' if 'factory.entry.leftovers' in rest else 'run') + ' in ' + ('/' if os.getcwd() == '/' else 'checkout' if os.getcwd() == {str(checkout)!r} else os.getcwd()) + '\\n')\nos.execvp(rest[0], rest)\n")
settings = InstanceSettings(repository_url="https://github.com/example/project.git", instance="self", checkout=checkout, state_directory=d / "state", agent_home=d / "agents-home", claude_executable=str(claude))
boundaries = build_boundaries(settings, "unused", hosting=FakeHostingService(), which={"sudo": str(sudo)}.get, confine_executable=None)
print("leftovers command:", boundaries.agent_runtime.leftovers == [sys.executable, "-I", "-m", "factory.entry.leftovers"])
agent = AgentDefinition(name="coder", model="sonnet", tools=["Read"], budget_usd=Decimal("1"), instructions="Write.")
own = pwd.getpwuid(os.getuid()).pw_name
for label, user in [("own user", own), ("another user", "factory-smoke-agent")]:
    (d / "sudo.log").write_text("", encoding="utf-8")
    request = AgentRunRequest(agent=agent, prompt="Stage: doing", allowed_decisions=["doing", "question"], time_limit=timedelta(seconds=30), working_directory=checkout, environment={"HOME": str(d)}, os_user=user)
    try:
        outcome = run_sealed(boundaries, request).result.end_reason
    except AgentRuntimeError as error:
        outcome = f"raised: {error.detail}"
    print(f"{label}: {outcome} | {'; '.join((d / 'sudo.log').read_text().splitlines())}")
    print(f"  left: {files(checkout)}")
environment = agent_run_environment(settings, production_environment())
outcome = Tick(boundaries, settings.instance, handler_factory(boundaries, settings.instance, environment)).run()
print(f"tick: stopped={outcome.stopped} event={outcome.event.kind if outcome.event else None}")
print(f"  after the restore: {files(checkout)}")
EOF
````

Output:

```
== the real program, as a user it does not run as, and without arguments
factory-leftovers: runs as agent, not factory-smoke-nobody
status 1
factory-leftovers: usage: python -m factory.entry.leftovers --user <name>
status 1
== a run, its leftovers and the restore, through the real wiring
leftovers command: True
own user: completed | run in checkout
  left: ['.gitignore', 'src/.gitignore', 'src/mod.py', 'src/new.py']
another user: raised: cannot end the agent's processes: factory-leftovers: runs as agent, not factory-smoke-agent | run in checkout; program in /
  left: ['.gitignore', '.venv/lib/standin.pth', 'src/.gitignore', 'src/__pycache__/mod.cpython-312.pyc', 'src/mod.py', 'src/new.py', 'src/x.dat', 'tests/hidden/.gitignore', 'tests/hidden/conftest.py']
2026-10-20T17:44:30Z discarded uncommitted changes: src/new.py
tick: stopped=None event=idle
  after the restore: ['.gitignore', 'src/mod.py']
```

Green. A returned run leaves only tracked files and the visible new `src/new.py`. The `.pth`, the `.pyc`, the hidden `tests/hidden/conftest.py` and `src/x.dat` (hidden by the branch's `src/.gitignore`) are gone before any check. A run as another user starts the real program from `/`. A fault of that program fails the run closed, and its ignored files wait for the restore. The restore removes them on the branch, before the switch to `main`, and logs only the visible change (decision 5). The first run of the script stopped at `pipeline_definition_invalid` because the stand-in agent home had no `agents/`; the script above gives it one. The real `kill(-1)` as `agent` is the human's change 4.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- The human, in this report's journal (entry 6): three test helper lines start the checkout's Python without `-B` under the tests' umask `022`: `tests/adapters/test_claude_runtime_os_user.py:81`, `tests/confine_support.py:114` and `tests/process_support.py:29`. An env-less child of today's `write_script` writes `__pycache__` (checked here: `True`). Proposed as S0004.
- S0001, coder entries 14, 18 and 22, tester entry 12, reviewer entry 24, documenter entry 26: `tests/test_process_search.py` pins `main`'s `noqa: PLR0913` at the literal line `32`, while it finds every other entry's line by search. Proposed as S0006.
- S0001, reviewer entry 24: `Identity(uid=0, user="root", pid=11)` is built three times. S0003, reviewer entry 27: `CLEAN` is defined twice (and `tests/application/test_tick_ignored.py:83` spells it a third time). Proposed as S0006.
- S0001, coder entries 7, 10 and 14: two test names no longer match their sets (`test_only_the_three_wrappers_import_the_process_module`, `test_the_only_suppression_markers_are_the_four_in_the_process_wrapper`). The human decided they stay (entry 8). Not proposed.
- S0002, coder entries 7, 10, 14 and 18, reviewer entry 20: `_end_leftovers`, `_remove_temporary_folder` and `_request_of` are near-copies in the two runtimes. `make duplicates` reports `5 new, 33 known, 3 gone`: four are runtime similarities, the fifth `ManualWaiter` in `adapters/clock.py`. Only the 8-line `_end_leftovers` is F0027's. Not proposed: merging the runtimes' shared code is a restructuring beyond this feature, for the human to start if wanted.
- S0002, reviewer entry 20: a `noqa: PLR0913` in `tests/adapters/test_opencode_runtime_leftovers.py:59`, and `BUDGET_STOP` and `REPLY` imported from other stories' test modules. `REPLY` is defined five times across the suite, which is older and broader than F0027. Not proposed.
- S0003, coder entry 21: `_head` near-copies with other signatures in six earlier test modules. Reviewer entry 27: `_status` in `test_git_cli_ignored.py` differs on purpose. Not proposed.
- S0003, coder entries 17, 21 and 25: the flaky row `tests/adapters/test_git_cli_work_tree.py::test_the_work_tree_id_is_the_tree_a_commit_records[edited-untracked-deleted]`. It is already owned by F0030-S0002 in F0030's backlog.
- S0001, documenter entry 26: the title of `docs/project-guide/write-guard.md` does not name its new section, left as the human wrote it. S0002, documenter entry 22: the operator guide's opening paragraph does not mention this feature. Not proposed, both minor.

## 5 The documentation as a whole

The three stories' texts agree with each other and with the code: the order call, program, removal, refusal, fault (`docs/project-guide/agents.md`, *Ending the agent's leftover processes*, and the operator guide's *The end of the agent's processes*), the restore's order (`watching.md`, *The tick*, step 3), and `remove_ignored()` in `git-and-hosting.md`. `make documents`: `documents ok`. Findings:

- Missing: what an ignored path the factory cannot remove does after an agent run. `run_sealed` raises `GitError`, the stage ends without a result, the restore stops every tick with `checkout_restore_failed`, and after the repair the factory records a crash and reruns. This happened twice to this acceptance (journal entries 2 to 6). The guide names only `checkout_restore_failed`, not the crash, not the repair, and not bytecode as the usual cause. Its paragraph under *The project's make targets* says only that "a stricter umask" makes the removal fail, and the `Makefile`'s new `UV_COMPILE_BYTECODE=1` (fd0fcd0b) has no decision entry.
- Stale: the operator guide's `umask=0002` bullet under *The one `sudo` rule* names the restore as `git reset --hard`, `git clean -fd`, without `git clean -X`. `docs/project-guide/watching.md` gives `build_boundaries(settings, token, *, hosting=None, end_leftovers=True)` without `which` and `confine_executable`.
- Not checked by me: whether the decisions entries of S0002 and S0003 carry every reason of the feature's decisions 2 and 4 to 12. Both documenters wrote them without `feature.md` and asked the human to check the wording (S0002 entry 22, S0003 entry 29).

Proposed as S0005. None of these misleads a user about what the feature does.

## 6 Decisions taken for the human

Open in `feature.md`, built as recommended, for the human to accept or revisit:
- Decision 2: ignored state is removed, not verified (A).
- Decision 4: the cost of the removal (accept). One reading from this run: this stage's first `make check`, as `agent`, built `.venv` from 17:37:38 (`pyvenv.cfg`) to 17:41:15 (its last `dist-info`), about 3.6 min, not "a matter of seconds". The human's answer "F0040 keeps uv's cache outside the fresh home" points at the cause. Change 4, step 4, is still the measurement.
- Decision 8: the kill ends every process of the agent's user (A).
- Decision 11: a failure fails closed (A). Seen in practice: an unremovable ignored path after a run costs the stage's work as a crash, and twice reached `crash_cap` here.
- Decisions 5, 6, 7, 9, 10, 12 and 19, "as built". Decision 3 was answered B (2026-10-19). The human's answers of 2026-10-20: no S0005 (F0033 settled the modes), F0030 first with its reader reused, and F0040 for uv's cache.

Answers and defaults in the stories:
- S0001, entry 8: (a) for both. `factory.entry.leftovers` joins the expected set of `test_wrapper_search.py`, and one `noqa: PLR0913` is allowed on `main`'s `def` line. Default: the tester wrote the line as the literal `32` (entry 12), not by search (S0006). The tester renamed the merged test `test_only_a_user_s_name_starts_the_rounds` (entry 20, the story's own test).
- S0002, entry 8: (a). The human added `"src/factory/entry/wiring.py" = ["PLR0913"]` to `pyproject.toml` (52cfe595). Defaults: the coder added `due_leftovers_launch` and `LEFTOVERS_FAULT` beyond the Interface (entry 7); the reviewer added criterion 11 (entry 12).
- S0003, entry 4: (a), the symbolic link row of criterion 1. Entry 11: (a), `assert error.value.detail == "boom"`. Default: the tester added `assert isinstance(error.value, AgentRuntimeError)` beside the approved line for `mypy --strict` (entry 15), in the story's own test.
- S0004 and S0006 here each need a leave in decision 16 before they start.

Earlier tests changed, each with its leave (checked against `git log --name-status` of the stories' commits):
- S0001: `tests/domain/test_sessions.py` and `tests/entry/test_wiring.py` (decision 16); `tests/test_wrapper_search.py` and `tests/test_process_search.py` (the human, entry 8, recorded in decision 16).
- S0002: none.
- S0003: `tests/application/test_git_interface.py`, `tests/application/test_interfaces.py` and `tests/application/test_tick.py` (decision 16). Under the standing leave to move a shared helper: `tests/adapters/test_git_cli_nested.py`, `tests/adapters/test_git_cli_restoring.py`, `tests/application/test_nested_repositories.py`, `tests/application/test_sealed_runs.py`, `tests/application/test_sealed_runs_runner.py` and `tests/git_support.py`.

No earlier test changed without a leave.

## 7 The slow checks

Nothing beyond `make check` today except two records: `make documents` (`documents ok`) and `make duplicates` (`5 new, 33 known, 3 gone`, none in F0027's code but the runtime near-copies under 4). `make check`, run here: `check: green`, `test: green (59.3 s)`, coverage 99.17 %. The slowest tests in `.reports/junit.xml` are not F0027's: `tests.adapters.test_opencode_sudo_time_limit` rows at 11.5 s and `tests.adapters.test_process_session` rows at 10.1 s. F0027's 105 test cases take 3.7 s together; the slowest are the two rows of `test_stage_run_ignored::test_the_checks_do_not_see_what_the_agent_hid` at 0.33 s and 0.30 s. After the checks, no folder of `agent` in the checkout lacked group write, so the next restore can remove everything. Disk: `/work` 969.3 GB free and 0.0 GB used now, against 969.8 GB free and 0.4 GB used at the previous acceptance record. The drop in used space is the feature's own doing: the restore removed the ignored state before this stage. The 0.5 GB less free space lies outside the measured folders. The feature's changes do not explain it, and the two rebuilds of `self` during F0027 (night log) are a likely cause I did not verify.

## 8 Cost

38 runs, 76.1 min, 346 turns, $14.19: S0001 $3.99 (13 runs, 23.0 min), S0002 $5.21 (11 runs, 27.0 min), S0003 $4.99 (14 runs, 26.1 min). S0002 stands out by dollars with the fewest runs. Its tester ($1.03, 20 turns) and its first coder run ($1.09, 24 turns) were the two dearest runs of the feature: the coder met ruff's `PLR0913` on `build_boundaries` and tried a write to `pyproject.toml` (refused) and a `noqa` (red in `test_process_search.py`) before asking (entry 7). S0003 has the most runs: two questions and one review round of copied test helpers. Human interventions: 4 questions answered (all of cause `question`), 1.1 h waited. S0003 needed the human most, with two of the four. Its journal shows why: a criterion the intake found missing (the symbolic link, entry 3), and a test the tester wrote against `str(error)` while `AgentRuntimeError`'s text was pinned elsewhere (entry 10). The stories' line does not count this acceptance: two crashes and one `crash_cap` answer from the agent-made bytecode folder (journal entries 2 to 6), plus the agent-side `.venv` build of about 3.6 min in this run (under 6).

## Proposed stories

- `backlog/F0027-S0004-the-tests-start-their-own-python-children-without-bytecode.md`: `write_script` and `python_argv` start their child with `-B`, and the stand-in `sudo` uses `write_script`. This is the cause of this acceptance's two crashes, which the human named.
- `backlog/F0027-S0005-the-documents-say-what-an-ignored-path-the-factory-cannot-remove-does.md`: the operator guide says what an unremovable ignored path does (a crash, then `checkout_restore_failed`), how to repair it, and bytecode as its cause. The decision log records `UV_COMPILE_BYTECODE=1`, and two stale lines are fixed.
- `backlog/F0027-S0006-the-feature-s-tests-share-their-constants-and-find-the-marker-s-line.md`: `CLEAN` and the root `Identity` move to the shared support modules, and `test_process_search.py` finds `main`'s marker line by search instead of the literal `32`.

## Journal

1. factory: started acceptance as self.
2. factory: crash 1: the run of stage acceptance ended without a result. Its work is discarded back to commit 8c406d04d470c9c11a83352556d4dc5a9a91f306.
3. factory: started acceptance as self.
4. factory: crash 2: the run of stage acceptance ended without a result. Its work is discarded back to commit 9f6ba8ae52f9f4c39614d79f16de7ec7b29fab24.
5. factory: Stage acceptance crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied into the journal). Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.
6. 2026-10-20 human: Rerun (2026-10-20). Both crashes were the restore's `git clean -X` failing on `.venv/lib/python3.12/site-packages/__pycache__/`, written 755 by a test child of the reviewer's `make check` (three test helpers start the checkout's Python without `-B` under the tests' umask 022). `main` now exports `UV_COMPILE_BYTECODE=1` in the `Makefile` (fd0fcd0b), so uv writes that bytecode group-writable at its sync. Note it as a finding: the three helper lines (`tests/adapters/test_claude_runtime_os_user.py:81`, `tests/confine_support.py:114`, `tests/process_support.py:29`) still lack `-B`.
7. factory: started acceptance as self.
8. acceptance-reviewer: accepted with stories; 3 stories proposed (F0027-S0004 to S0006)
   1 Scope: none. Every Scope line has its story. The twelve source files the stories changed are exactly the Scope's. S0004 was withdrawn by decision 3. The human's change 4 is not yet recorded.
   2 Feature smoke test: green. It used the real `build_boundaries` and the real leftovers program (which refused under a stand-in `sudo`), `run_sealed`, and one real `Tick.run()`. A returned run leaves no ignored path, a run as another user starts the program from `/` and fails closed, and the restore removes what the branch's `.gitignore` hid before the switch to `main`.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: the three test helpers without `-B`, which the human named (S0004); the literal line `32` in `test_process_search.py`, and `CLEAN` and the root `Identity` built twice or more (S0006). Not proposed: the runtime near-copies (`make duplicates` 5 new), the test names the human kept, and `REPLY` and `_head` copies older than F0027. The flaky `work_tree_id` row is already F0030-S0002's.
   5 Docs: consistent across the stories, and `make documents` is ok. Missing: what an unremovable ignored path does (a crash of the stage, then `checkout_restore_failed`, and the repair), bytecode as its cause, and a decision entry for `UV_COMPILE_BYTECODE`. Two stale lines (the `umask=0002` bullet, the `build_boundaries` signature in `watching.md`). All in S0005.
   6 Decisions: decisions 2, 4, 8 and 11 are open and built as recommended. This run's agent-side `.venv` build took about 3.6 min, which is evidence for decision 4. The story answers and defaults are listed. Every earlier test change has its leave (decision 16, the human's answers or the standing leave), none without one. S0004 and S0006 each need a leave in decision 16.
   7 Slow checks: `make check` is green (test 59.3 s, 99.17 %). The slowest tests are not F0027's (11.5 s and 10.1 s); F0027's 105 cases take 3.7 s. Disk used fell from 0.4 GB to 0.0 GB, which the removal explains. Free space fell 0.5 GB, which the feature does not explain (likely the image rebuilds, not verified).
   8 Cost: $14.19 over 38 runs. S0002 was dearest ($5.21), mostly from the coder's two refused routes past `PLR0913` before asking. There were 4 questions over 1.1 h, and S0003 needed the human most (2 questions). Not in that count: this acceptance's 2 crashes and its `crash_cap` answer.
   Set aside: `sed -i` on the report was refused by the write guard (its temporary file), so I made that edit with the edit tool. The stories' forms pass `factory-check-story`. No folder the factory cannot remove is left in the checkout.
9. factory: done (pull request merged); cost: 1 runs, 15.0 min, 63 turns, 173845 tokens in (7126326 more from cache), 53503 out, $3.89
