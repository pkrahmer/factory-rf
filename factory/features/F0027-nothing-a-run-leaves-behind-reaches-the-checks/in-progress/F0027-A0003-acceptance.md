---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 374
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T23:50:12.391432Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T23:54:02.588733Z'
  stage: acceptance
  run: 60340e761e5d421cb87eeb9742b7b99f
stories: [F0027-S0001, F0027-S0002, F0027-S0003, F0027-S0004, F0027-S0005, F0027-S0006, F0027-S0007]
outcome: null
---

# Acceptance of Nothing a run leaves behind reaches the checks

## Recommendation

**accepted.** Since F0027-A0002 one story was added: S0007, which A0002 proposed. It put the feature's decision 7 into the decision log, and this acceptance checks that bullet against git's real behaviour. The feature smoke test from A0002 is still green on today's `main`, which includes F0040's project commands running as `agent`. `make check` is green. The human's change 4, steps 1 to 3, is recorded as met in the night log. Nothing of weight is open, so no story is proposed. The stale wording listed under sections 4 and 6 is in the human's own files.

## 1 Scope

None. F0027-A0001 and F0027-A0002 matched S0001 to S0006 against every Scope line, and that still holds. S0007 changed only `docs/decisions.md` (merge #373; `git diff --name-only origin/main -- src tests` gave `0` in its smoke test), which is within the Scope's line on documents. No story touches an Out of scope item.

One remark for the human: `feature.md`'s *Stories* list still ends at S0006, and S0007 is not on it. That file is the human's. The goal is reached as far as stories can reach it. The human's change 4, steps 1 to 3 (the real `kill(-1)` as `agent` in the image, the refusal as `factory`, and no agent process between stages), is recorded as met in `docs/runs/2026-10-12-overnight/night-log.md:895`. A0002 overlooked that record. Step 4, the `check` durations, is still unmeasured: the night log says the `Makefile`'s change to `--dist worksteal` at the same time blurs the comparison.

## 2 Feature smoke test

This is the user's walk-through from F0027-A0002, section 2, unchanged, run against today's `main`. It runs:
- the real leftovers program, which its guards refuse;
- a child started by the shared test helpers, with an emptied environment, under umask `022`;
- an agent run through the real wiring (`build_boundaries` with a stand-in `sudo` and a stand-in `claude`, the real `leftovers_command()`), which hides files in every ignored place the feature names, first as the factory's own user and then as another user;
- one real `Tick.run()`;
- a count of the folders the removal could not take after this stage's `make check`.

One step is new for S0007. It checks the decision-log bullet that S0007 added (an agent can un-ignore a path) against `GitCli.remove_ignored()` on a real repository. The program is never run as the user it names, and `signal_every_other` is never called.

The command extracts the script from A0002's report, which is archived on `main`, and runs it:

```bash
awk '/^````bash$/{f=1;next} /^````$/{f=0} f' factory/features/F0027-nothing-a-run-leaves-behind-reaches-the-checks/done/F0027-A0002-acceptance.md > "$TMPDIR/smoke/feature_smoke.sh"
bash "$TMPDIR/smoke/feature_smoke.sh"; echo "script status $?"
```

Output:

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
2026-10-20T23:51:55Z discarded uncommitted changes: src/new.py
tick: stopped=None event=idle
  after the restore: ['.gitignore', 'src/mod.py']
== what the factory's removal meets in this checkout after this stage's make check
folders without group write: 0
script status 0
```

The new step, for S0007's bullet. Command: `uv run -q python -B "$TMPDIR/smoke/unignore.py"`, with this script:

```python
import subprocess, sys, tempfile
from pathlib import Path
from factory.adapters.git_cli import GitCli
with tempfile.TemporaryDirectory() as t:
    r = Path(t)
    g = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *a], cwd=r, check=True, capture_output=True, text=True).stdout
    g("init", "-q")
    (r / ".gitignore").write_text(".venv/\n__pycache__/\n")
    (r / "src").mkdir(); (r / "src" / "m.py").write_text("x = 1\n")
    g("add", "-A"); g("commit", "-q", "-m", "base")
    (r / "src" / ".gitignore").write_text("!__pycache__/\n")
    (r / "src" / "__pycache__").mkdir(); (r / "src" / "__pycache__" / "m.pyc").write_text("standin\n")
    (r / ".venv" / "lib").mkdir(parents=True); (r / ".venv" / ".gitignore").write_text("!*\n"); (r / ".venv" / "lib" / "s.pth").write_text("import os\n")
    GitCli(r).remove_ignored()
    print("left:", sorted(p.relative_to(r).as_posix() for p in r.rglob("*") if p.is_file() and ".git" not in p.relative_to(r).parts[:1]))
    print("git status (what the commit and the diff see):", g("status", "--porcelain", "-uall").split("\n")[:-1])
```

Output (`status 0`):

```
left: ['.gitignore', 'src/.gitignore', 'src/__pycache__/m.pyc', 'src/m.py']
git status (what the commit and the diff see): ['?? src/.gitignore', '?? src/__pycache__/m.pyc']
```

Green. The six results A0002 read off the main script all hold unchanged:
- a run that returned leaves no ignored path;
- a run as another user starts the real program from `/` and fails closed;
- the restore removes what the branch's own `.gitignore` hid;
- the helpers' children write no bytecode;
- after this stage's `make check`, every folder in the checkout is group-writable. Since F0040 that `make check` runs as `agent`.

The new step bears out the decision-log bullet. The `.pyc` that `src/.gitignore` un-ignores is kept and shows in `git status`, so it would show in the commit and the diff. The `!*` in `.venv/.gitignore` has no effect, because git does not read the rules of an ignored folder: the `.pth` and that `.gitignore` are both removed.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

For S0001 to S0006, see F0027-A0001 and F0027-A0002, section 4. Their unproposed items still stand: the runtimes' near-copies, the older copies `REPLY` and `_head`, the two test names the human kept, and the flaky `work_tree_id` row of F0030-S0002.

From S0007:
- Tester (entry 5), coder (entry 7) and smoke tester: nothing noticed. The coder again paid for a run with nothing to build ($0.13). That is a property of the pipeline, as A0002 said.
- Documenter (entry 11): added a sentence the criterion did not ask for: "A later story that finds an un-ignored file in a diff should not add a rule for it without asking." The smoke tester judged that it contradicts nothing, and I agree. It is noted here because it was the documenter's own choice.
- Reviewer (entry 9): the coder's `duplicates: 6 new` does not come from S0007. I traced the sixth: it is `output_abandoned` in `src/factory/adapters/process.py:53`, from F0040-S0005, not from F0027.

Seen by me, in the human's files, from the order of the features: F0040 made every project command run as `agent`. That makes three sentences stale, as F0040's own pre-check (`planning/overnight/precheck/F0040-feature-1.md`, item 4) foresaw:
- the reason in parentheses in `CLAUDE.md`'s bullet on `factory.entry.leftovers`, "(and under `make check`, the factory)", where under `make check` that user is now `agent`;
- `feature.md`'s *Out of scope* line, which says the checks run as `factory` with a uv cache in `/home/factory`;
- decision 1 of `feature.md`, which says the same.

The rule in that `CLAUDE.md` bullet is still right. Only its reason is out of date. These files are the human's, so no story is proposed.

## 5 The documentation as a whole

None of weight. I read the feature's passages again:
- in `docs/operator-guide.md`: the ignored-state paragraph at line 78, *The end of the agent's processes*, the `umask=0002` bullet, and *The project commands run as `agent`* (F0040), which states that the leftovers program follows every project command too;
- in `docs/decisions.md`: the three F0027 entries, now including S0007's `Accepted:` bullet, and F0040-S0002's entry.

They agree with each other and with the code. Section 2's new step bears out the new bullet. `make documents`: `documents ok`. `README.md` does not name the feature, which is right for a newcomer.

One sentence is narrow but not wrong. Line 78 says "a project command an agent runs must leave its ignored files group-writable". Since F0040, the factory's own checks also run as `agent`, under `sudo`'s umask `0002` and with `PYTHONDONTWRITEBYTECODE=1`, so the rule covers every project command. The next section of the same guide says so. This belongs to a pass that brings the documents up to date across features, such as the human's F0038 in `planning/`, and does not need a story of its own here.

## 6 Decisions taken for the human

These are open in `feature.md` and were built as recommended, for the human to accept or revisit:
- Decision 2: ignored state is removed, not verified (A).
- Decision 4: the cost of the removal (accept). Step 4 of change 4 has not measured it yet (section 1). This stage's `make check` built `.venv` anew (511 MB, section 7) and its `test` target took 63.6 s. That is one reading, not a comparison.
- Decision 8: the kill ends every process of the agent's user (A). Change 4, steps 1 to 3, confirmed it in the image.
- Decision 11: a failure fails closed (A).
- Decision 7, accepted with no rule: since S0007 it is recorded in the decision log, and section 2 confirms it.
- Decisions 5, 6, 9, 10, 12 and 19: as built.
- Change 5: the `Makefile`'s `export UV_COMPILE_BYTECODE := 1` (line 15) is still there. S0004 removed its cause, and F0040 now passes `PYTHONDONTWRITEBYTECODE=1` to every project command. Whether to keep it is still the human's call.
- New here: the stale reason in the `CLAUDE.md` bullet, and the stale out-of-scope line and decision 1 in `feature.md` (section 4). Whether to update them is the human's call.

For the answers and defaults in S0001 to S0006, see F0027-A0001 and F0027-A0002, section 6. S0007 asked no question and took no default.

Earlier tests changed: S0007 changed none. Its reviewer (entry 9) confirmed that "no test file on `main` is changed, renamed or deleted". For S0001 to S0006, every change has its leave (A0001, A0002). No earlier test was changed without a leave.

## 7 The slow checks

Beyond `make check`, the project offers only two records today:
- `make documents`: `documents ok`.
- `make duplicates`: `6 new, 33 known, 3 gone`. Five of the new ones are the same as at A0002. The sixth, `output_abandoned`, is F0040-S0005's (section 4).

`make check`, run here: `check: green`, `test: green (63.6 s)`, coverage 99.14 %. `.reports/junit.xml` holds 6,407 cases, which take 729 s in all across the workers. The slowest are not F0027's: two rows of `tests.adapters.test_opencode_sudo_time_limit` at 11.5 s, and `tests.adapters.test_process_session` at 10.1 s. F0027's modules (those named `*leftovers*`, `*_ignored` and `test_test_children`) hold 103 cases that take 3.7 s. The slowest of them is `test_stage_run_ignored::test_the_checks_do_not_see_what_the_agent_hid[in-write-path]`, at 0.28 s.

Disk: `/work` used went from 0.0 GB to 0.5 GB since the previous record (`disk acceptance`), and its free space fell by the same 0.5 GB. `/state` and `/tmp` show no use. The feature explains the growth: the restore at the start of this stage removed every ignored path, so this stage's `make check` built the checkout's `.venv` anew (`du -sh .venv`: 511 MB). Nothing else grew.

## 8 Cost

The stories cost 63 runs, 94.7 min, 479 turns and $18.40, against $17.62 over 57 runs at A0002. The difference is exactly S0007: 6 runs, 3.9 min, $0.78, one pass with no rework round and no question. S0002 is still the most expensive story ($5.21): its coder tried two routes past ruff's `PLR0913` that were refused before asking (A0001, section 8). The four follow-up stories (S0004 to S0007) cost $4.22 together. S0005 to S0007 changed only documents or tests, and each paid for a coder run with nothing to build.

Human interventions: 5 questions answered, all of cause `question`, and 1.2 h waited, unchanged since A0002, since S0007 asked none. S0003 needed the human most, with two questions: a missing criterion for a symbolic link, and a test written against an error text that was pinned elsewhere.

Not in the stories' line: F0027-A0001 cost $3.89 with two crashes, and F0027-A0002 cost $2.18. This acceptance has had no crash.

## Proposed stories

None. The only items left are wording in the human's own files (`CLAUDE.md`, `feature.md`; sections 4 and 6), and one narrow but not wrong sentence in the operator guide that a pass bringing the documents up to date can take (section 5).

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed
   1 Scope: none. S0007 changed only `docs/decisions.md` (merge #373), which is within the Scope's line on documents. `feature.md`'s *Stories* list (the human's file) does not name S0007. The human's change 4, steps 1 to 3, is recorded as met (`docs/runs/2026-10-12-overnight/night-log.md:895`). Step 4, the `check` durations, is still unmeasured.
   2 Feature smoke test: green. I reran A0002's script unchanged on today's `main`, where F0040's project commands run as `agent`. A run that returned left no ignored path. A run as another user started the real program from `/` and failed closed. The restore removed what the branch's `.gitignore` hid. The helpers' children wrote no bytecode, and after `make check` every folder was group-writable. A new step checked S0007's bullet against `GitCli.remove_ignored()`: the un-ignored `.pyc` is kept and shows in `git status`, and a `!*` inside the ignored `.venv/` has no effect.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: in S0007 the documenter added an extra sentence ("ask before adding a rule"), which contradicts nothing. The sixth new `duplicates` finding (`output_abandoned`) comes from F0040-S0005, not F0027. F0040 made three sentences in the human's files stale: the reason in `CLAUDE.md`'s leftovers bullet ("under `make check`, the factory"), and `feature.md`'s *Out of scope* line and decision 1, which say the checks run as `factory`. No story, since those files are the human's.
   5 Docs: consistent, and `make documents` is ok. One sentence at `docs/operator-guide.md:78` is narrow but not wrong ("a project command an agent runs"; since F0040 every project command runs as `agent`). A pass that brings the documents up to date can take it.
   6 Decisions: decisions 2, 4, 8 and 11 are still open, built as recommended. Decision 7 is now recorded and confirmed by the smoke test. Keeping `UV_COMPILE_BYTECODE` (change 5) and updating the stale wording in `CLAUDE.md` and `feature.md` are the human's calls. S0007 changed no earlier test, and no test was changed without a leave.
   7 Slow checks: `make check` is green (test 63.6 s, coverage 99.14 %). The slowest tests are not F0027's (11.5 s and 10.1 s). F0027's 103 cases take 3.7 s. `make duplicates` reports 6 new, 33 known, 3 gone. Disk on `/work` grew by 0.5 GB. That is the checkout's `.venv` (511 MB), built anew by this stage's `make check` after the restore removed the ignored paths, which the feature explains.
   8 Cost: $18.40 over 63 runs. The rise of $0.78 since A0002 is S0007 alone, one pass with no question. S0002 is still the most expensive story ($5.21), and S0004 to S0007 together cost $4.22. There were 5 questions over 1.2 h, unchanged, and S0003 needed the human most (2 questions).
