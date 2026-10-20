---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 361
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T19:43:10.693946Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T19:49:12.389059Z'
  stage: acceptance
  run: 14b086e6da5949b7a09a176a610b971a
stories: [F0027-S0001, F0027-S0002, F0027-S0003, F0027-S0004, F0027-S0005, F0027-S0006]
outcome: null
---

# Acceptance of Nothing a run leaves behind reaches the checks

## Recommendation

**accepted.** Both routes into the checks are closed, and the feature smoke test shows it through the real wiring. A run that returned leaves no ignored path. A run as another user starts the real leftovers program from `/` and fails closed. The tick's restore removes what a raised run left behind, including what the branch's own `.gitignore` hid. The three stories that F0027-A0001 proposed did what it asked: test children no longer write bytecode (`make check` here left no folder the factory could not remove), the documents say what an unremovable path does, and the tests share their constants. `make check` is green. The one finding is small: the decision log lacks the feature's decision 7. It gets one documentation story.

## 1 Scope

None. Every Scope line has its story. F0027-A0001 checked S0001 to S0003 against their code: the twelve source files they changed are exactly the Scope's, and that still holds. S0004 to S0006 were added to `feature.md`'s story list, and each stays inside the Scope's lines on tests and documents. Their merges (#358, #359, #360) change only these files:
- S0004: eleven files under `tests/` and `docs/decisions.md`.
- S0005: `docs/operator-guide.md`, `docs/project-guide/watching.md` and `docs/decisions.md`.
- S0006: eight files under `tests/`, plus `docs/project-guide/write-guard.md`, where the documenter fixed a stale line.

None of them changes `src/`. No story touches an Out of scope item. `factory/pipeline.yml` has no `kept_ignored` key (decision 3, answer B). The goal is reached as far as the stories can reach it. The human's change 4 is still open: the real `kill(-1)` as `agent` in the image, and the rebuild cost. No journal records it.

## 2 Feature smoke test

The user's walk-through, from F0027-A0001, with one step added for S0004. The script runs:
- the real leftovers program, refused by its guards;
- the tests' shared helpers starting a child with an emptied environment under umask `022`;
- an agent run through the real wiring (`build_boundaries` with stand-in `sudo` and `claude`, no confinement wrapper, the real `leftovers_command()` and the real `factory.entry.leftovers`), which hides files in every ignored place the feature names. It runs first as the factory's own user (no program is due), then as another user (the program is due, and refuses, because the stand-in `sudo` does not switch users);
- one real `Tick.run()`, which restores the checkout;
- a count of the folders in this checkout, after this stage's `make check`, that the factory's removal could not take.

The program is never run as the user it names, and `signal_every_other` is never called (`CLAUDE.md`, *Tests*).

Command: `bash $TMPDIR/smoke/feature_smoke.sh`, with this script:

````bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
cd /work/checkout
echo "== the real program, as a user it does not run as, and without arguments"
uv run -q python -I -B -m factory.entry.leftovers --user factory-smoke-nobody; echo "status $?"
uv run -q python -I -B -m factory.entry.leftovers; echo "status $?"
echo "== a test child of the shared helpers, with an emptied environment, under umask 022"
uv run -q python -B - "$d" <<'EOF'
import os, subprocess, sys
from pathlib import Path
sys.path.insert(0, "tests")
from confine_support import write_script
from process_support import python_argv
d = Path(sys.argv[1]) / "children"; d.mkdir()
(d / "standin.py").write_text("x = 1\n", encoding="utf-8")
os.umask(0o022)
subprocess.run([str(write_script(d / "child", "import standin\n"))], cwd=d, env={}, check=True)
subprocess.run(python_argv("import standin"), cwd=d, env={}, check=True)
print("bytecode written by the helpers' children:", (d / "__pycache__").exists())
EOF
echo "== a run, its leftovers and the restore, through the real wiring"
uv run -q python -B - "$d" <<'EOF'
import json, os, pwd, shutil, subprocess, sys
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
echo "== what the factory's removal meets in this checkout after this stage's make check"
echo "folders without group write: $(find . -path ./.git -prune -o -type d ! -perm -g+w -print | wc -l)"
````

Output (`script status 0`):

```
== the real program, as a user it does not run as, and without arguments
factory-leftovers: runs as agent, not factory-smoke-nobody
status 1
factory-leftovers: usage: python -m factory.entry.leftovers --user <name>
status 1
== a test child of the shared helpers, with an emptied environment, under umask 022
bytecode written by the helpers' children: False
== a run, its leftovers and the restore, through the real wiring
leftovers command: True
own user: completed | run in checkout
  left: ['.gitignore', 'src/.gitignore', 'src/mod.py', 'src/new.py']
another user: raised: cannot end the agent's processes: factory-leftovers: runs as agent, not factory-smoke-agent | run in checkout; program in /
  left: ['.gitignore', '.venv/lib/standin.pth', 'src/.gitignore', 'src/__pycache__/mod.cpython-312.pyc', 'src/mod.py', 'src/new.py', 'src/x.dat', 'tests/hidden/.gitignore', 'tests/hidden/conftest.py']
2026-10-20T19:46:34Z discarded uncommitted changes: src/new.py
tick: stopped=None event=idle
  after the restore: ['.gitignore', 'src/mod.py']
== what the factory's removal meets in this checkout after this stage's make check
folders without group write: 0
```

Green. What each part shows:
- A run that returned leaves only the tracked files and the visible new `src/new.py`. The `.pth`, the `.pyc`, the hidden `tests/hidden/conftest.py` and `src/x.dat` (hidden by the branch's `src/.gitignore`) are gone before any check.
- A run as another user starts the real program from `/`. When the program fails, the run fails closed, and its ignored files wait for the restore.
- The restore removes them on the branch, before the switch to `main`, and logs only the visible change.
- New since F0027-A0001: a child started by `write_script` or `python_argv`, with no `PYTHONDONTWRITEBYTECODE`, writes no `__pycache__`.
- After this stage's own `make check`, run as `agent`, no folder in the checkout lacks group write. `git clean -n -ffdX` lists only `.venv/`, the tool caches and `.reports/`. So the next restore can remove everything. That is the opposite of F0027-A0001's two crashes.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

For S0001 to S0003, see F0027-A0001, section 4. Its three proposals became S0004 to S0006 and are built. What it left unproposed still stands:
- the runtimes' near-copies (`_end_leftovers`, `due_leftovers_launch`, `call_refusal`, `version_printed`);
- `REPLY` and `_head`, copies older than F0027;
- the two test names the human kept;
- the flaky `work_tree_id` row, which belongs to F0030-S0002.

From S0004 to S0006:
- S0004, Description: "about twenty argv lists in `tests/` start `sys.executable` without `-B`, in an environment that keeps the variable", and no check guards them. I checked them here. The only `env={}` in `tests/` outside `test_test_children.py` are expected values in `tests/adapters/test_agent_launch.py:55` and `:70`, which start nothing. Every interpreter child that is really started either inherits the environment or sets `PYTHONDONTWRITEBYTECODE` (`tests/test_tests_umask.py:52`). The `-I` command in `tests/entry/test_wiring_leftovers.py:14` is compared, not run. No risk today; not proposed.
- S0004, tester: every change was a test change, so the coder built nothing. The same holds for S0005 (documents only) and S0006. Each of the three still paid for a coder run of $0.14 to $0.17 (`.costs.jsonl`). This is a property of the pipeline, not of this feature; not proposed.
- S0006, documenter entry 11: fixed `docs/project-guide/write-guard.md:180`, which now names `ROOT`. A cross-read fix, not a finding.
- S0005 and S0006: the coders and reviewers noticed nothing else.

## 5 The documentation as a whole

I read the feature's passages in `docs/operator-guide.md` (the ignored-state paragraph at line 78, *The end of the agent's processes* at line 127, the `umask=0002` bullet at line 140 and the `checkout_restore_failed` row at line 858), in `docs/project-guide/` (`watching.md` *Restore* and *Boundaries*, `write-guard.md`, `git-and-hosting.md` *Restoring the checkout*, `agents.md` *Ending the agent's leftover processes*) and the three entries in `docs/decisions.md`. They agree with each other and with the code. F0027-A0001's three findings are repaired by S0005: the crash before the stop and the repair, bytecode as the cause, `UV_COMPILE_BYTECODE` in the decision log, the `umask=0002` bullet and the `build_boundaries` signature. `make documents`: `documents ok`. `README.md` does not name this feature, which is right for the newcomer.

F0027-A0001 left one check open: whether the decision log carries the reasons of the feature's decisions. I checked it here.
- Decisions 2, 5, 6, 8, 9, 10, 11 and 12 are in the three entries or in the guide. Decision 6's symbolic links and its `0555` folder are in `git-and-hosting.md`.
- Decision 7 is in none of them. The S0003 entry's date line names "the feature's decisions 2 and 4 to 7", but no line says that an agent can un-ignore a path inside its write paths, or why that is accepted with no rule added. Proposed as S0007.
- Decision 4 is there only as "costs one download after an image rebuild". That is not wrong, and the cost itself is the human's change 4, step 4, to measure. Not proposed.

## 6 Decisions taken for the human

Open in `feature.md`, built as recommended, for the human to accept or revisit:
- Decision 2: ignored state is removed, not verified (A).
- Decision 4: the removal's cost (accept). F0027-A0001 saw about 3.6 min for an agent-side `.venv` build before F0040. One reading from this stage, which is not a measurement: `.venv` was there when this run began. It was built as `factory` at 19:43:09 (`pyvenv.cfg`), and its first and last `dist-info` folders are 0.1 s apart. This stage's `make check` reused it. The human's change 4, step 4, is still the measurement.
- Decision 8: the kill ends every process of the agent's user (A).
- Decision 11: a failure fails closed (A). Since S0004, the usual cause of such a failure, a test child's bytecode, is gone.
- Decisions 5, 6, 7, 9, 10, 12 and 19, "as built". Decision 3 was answered B (2026-10-19). The human's answers of 2026-10-20: no S0005 of round 1, F0030 first with its reader reused, and F0040 for uv's cache.
- Change 5: the `Makefile`'s `UV_COMPILE_BYTECODE := 1` (fd0fcd0b) stays. S0005 records it as the human's quick fix, and S0004 removed the cause. Whether to keep it now is the human's call.

Answers and defaults in the stories: for S0001 to S0003, see F0027-A0001, section 6. Then:
- S0004, entry 4: (a), the matcher rows build the shebang text from pieces; and "same path" means `directory / "sudo"`.
- S0004, tester default: the new test's `subprocess.run` carries `# noqa: S603` with its reason, as seven earlier test modules do. That is a ruff marker on a test, not one of the markers `CLAUDE.md` reserves for `src/`.
- S0005, S0006: no questions.

Earlier tests changed, each with its leave. For S0001 to S0003, see F0027-A0001. I checked the rest against the merges' file lists:
- S0004: `tests/confine_support.py`, `tests/process_support.py`, `tests/adapters/test_claude_runtime_os_user.py`, `tests/adapters/claude_stand_in.py`, `tests/adapters/opencode_stand_in.py`, `tests/adapters/test_claude_runtime_file_modes.py`, `tests/adapters/test_claude_runtime_provider_limit.py`, `tests/git_support.py`, `tests/adapters/test_git_cli_branches.py` and `tests/adapters/test_git_cli_writing.py`, all under decision 16's S0004 line, as the reviewer (entry 12) confirmed.
- S0006: `tests/test_process_search.py` under decision 16's S0006 line. `tests/adapters/test_git_cli_ignored.py`, `tests/application/test_sealed_runs_ignored.py`, `tests/application/test_tick_ignored.py`, `tests/domain/test_leftovers.py`, `tests/entry/test_leftovers.py`, `tests/git_support.py` and `tests/leftovers_support.py` under the standing leave to move a shared helper, as the reviewer (entry 9) confirmed.
- S0005: none.

No earlier test changed without a leave.

## 7 The slow checks

Nothing runs beyond `make check` today except two records:
- `make documents`: `documents ok`.
- `make duplicates`: `5 new, 33 known, 3 gone`, the same as at F0027-A0001. Two of the five are F0027's runtime near-copies (`_end_leftovers`, `due_leftovers_launch`), two are older runtime similarities, and one is `ManualWaiter`. The baseline is the human's file.

`make check`, run here: `check: green`, `test: green (59.2 s)`, coverage 99.17 %, with 6,286 cases totalling 688 s across the workers. The slowest tests in `.reports/junit.xml` are not F0027's: the `tests.adapters.test_opencode_sudo_time_limit` rows take 11.5 s and the `tests.adapters.test_process_session` rows take 10.1 s. F0027's test modules, `test_test_children` included, hold 115 cases that take 4.4 s together. The slowest are `test_process_search::test_no_module_uses_another_route_to_a_process` (0.36 s) and `test_stage_run_ignored::test_the_checks_do_not_see_what_the_agent_hid[in-write-path]` (0.32 s).

Disk: `/work` now has 968.1 GB free and 0.5 GB used, against 969.1 GB free and 0.5 GB used at the previous record (`disk start`). Used space did not change; the 0.5 GB is this checkout's `.venv` (511 MB). Free space fell 1.0 GB. `/state` and `/tmp` show the same free space, so they share one host file system, and the fall lies outside the measured folders. The feature's changes do not explain it: S0004 to S0006 change only tests and documents. Another instance's F0040-S0002 started on `main` meanwhile (fafec202), which is a likely cause. I did not verify it.

## 8 Cost

57 runs, 90.8 min, 451 turns, $17.62. By story:

| Story | Cost | Runs | Minutes |
|---|---|---|---|
| S0001 | $3.99 | 13 | 23.0 |
| S0002 | $5.21 | 11 | 27.0 |
| S0003 | $4.99 | 14 | 26.1 |
| S0004 | $1.44 | 7 | 6.0 |
| S0005 | $0.99 | 6 | 4.6 |
| S0006 | $1.01 | 6 | 4.1 |

S0002 stands out by dollars: its coder tried two refused routes past ruff's `PLR0913` before asking (F0027-A0001, section 8). The three follow-up stories cost $3.44 together, a fifth of the feature. Each was a single pass with no rework round. $0.44 of that went to coder runs that had nothing to build (section 4).

Human interventions: 5 questions answered, all of cause `question`, and 1.2 h waited. Four of them belong to S0001 to S0003. S0004's intake asked the fifth: criterion 3's scan would have found its own matcher rows (entry 3). S0003 needed the human most, with two questions: a missing criterion for a symbolic link, and a test written against an error text pinned elsewhere.

Not in the stories' line: F0027-A0001 cost $3.89, two crashes and one `crash_cap` answer, all from the bytecode folder that S0004 removed. This acceptance has had no crash.

## Proposed stories

- `backlog/F0027-S0007-the-decision-log-says-why-an-un-ignored-path-is-accepted.md`: the decision log's entry on removing ignored paths gains the feature's decision 7: an agent can un-ignore a path in its write paths, and that is accepted with no rule, because the path then shows in the diff. Documents only; `factory-check-story`: ok.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 1 story proposed (F0027-S0007)
   1 Scope: none. F0027-A0001 already matched S0001 to S0003's source files to the Scope. S0004 to S0006 change only `tests/` and `docs/` (merges #358 to #360), inside the Scope's lines on tests and documents. The human's change 4 (the real `kill(-1)` in the image, the rebuild cost) is still not recorded in any journal.
   2 Feature smoke test: green. It used the real wiring, the real leftovers program (which refused under its guards), `run_sealed` and one real `Tick.run()`. A run that returned left no ignored path. A run as another user started the program from `/` and failed closed. The restore removed what the branch's `.gitignore` hid. The shared test helpers' children wrote no `__pycache__` with an emptied environment under umask 022. After this stage's own `make check`, no folder in the checkout lacks group write.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: S0004's unchecked argv lists without `-B` are no risk today. Every child the tests actually start keeps or sets `PYTHONDONTWRITEBYTECODE`, and the two `env={}` hits are expected values that start nothing. Each of the three follow-up stories paid for a coder run with nothing to build ($0.44 in all), which is a property of the pipeline. F0027-A0001's unproposed items still stand.
   5 Docs: consistent, and `make documents` is ok. S0005 repaired every finding of F0027-A0001. Finding: the decision log does not carry the feature's decision 7 (an agent can un-ignore a path in its write paths, accepted with no rule). Proposed as S0007. Decision 4's cost is the human's change 4 to measure, so no story for it.
   6 Decisions: decisions 2, 4, 8 and 11 are open and built as recommended; change 5's `UV_COMPILE_BYTECODE` is now a quick fix whose cause S0004 removed, and keeping it is the human's call. The story answers are listed, including S0004's single question. Every earlier test change has its leave (decision 16's S0004 and S0006 lines, or the standing leave), and none lacks one.
   7 Slow checks: `make check` is green (test 59.2 s, coverage 99.17 %). The slowest tests are not F0027's (11.5 s and 10.1 s). F0027's 115 cases take 4.4 s. `make duplicates` reports 5 new, unchanged since F0027-A0001. Used disk is unchanged at 0.5 GB (`.venv`). Free space fell 1.0 GB on the shared host file system, which the feature does not explain (likely F0040-S0002 running meanwhile; not verified).
   8 Cost: $17.62 over 57 runs. S0002 was the dearest ($5.21), and the three follow-ups cost $3.44 with no rework. There were 5 questions over 1.2 h, and S0003 needed the human most (2 questions). Not in that line: F0027-A0001's $3.89 and its two crashes, whose cause S0004 removed.
   Set aside: a compound shell command that wrote the smoke script was refused by the permission prompt, so I wrote the script with the write tool into `$TMPDIR` instead. A later `rm` of that script was refused the same way; it stays in `$TMPDIR`, which the factory removes. `factory-check-story` says ok for S0007.
