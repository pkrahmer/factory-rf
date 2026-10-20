---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 345
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T09:26:39.959926Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T09:35:52.695628Z'
  stage: acceptance
  run: 1827d59f405e4efa940bf8151b4801ac
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-20T09:44:24.589649Z'
  stage: done
stories: [F0030-S0001]
outcome: accepted
---

# Acceptance of A command stopped at its time limit leaves no process running

## Recommendation

**Accepted with stories.** The goal is reached. A `Makefile` shaped like the `mutants` recipe (`timeout` without `--foreground`, output through `tee`, a stand-in for mutmut whose workers stay in the group, take a group of their own, or are orphaned) was run through the real `MakeProjectCommands.run` with an 8 s limit. It returned `time_limit` after 8.1 s, and nothing of the killed `make`'s session was left. Only the worker that called `setsid` was left, which the feature puts out of scope. `make check` is green. Two stories are proposed, neither for a broken promise. S0002 fixes a flaky git test that stalled this feature's coder once; its cause is now reproduced, and the same cause can make the known-result key stale. S0003 writes two sentences that the feature said S0001's docs criterion carried, but that criterion did not hold them.

## 1 Scope

None. Every Scope item of `feature.md` has a story and is built. `src/factory/domain/sessions.py` holds `ENDED_STATES`, `ProcessEntry`, `parse_stat` and `left_to_kill`, as S0001's Interface names them. `src/factory/adapters/process.py` replaces `_kill_group` with `_kill_session` at its three call sites: the time limit in `run_process`, and the time limit, the stop and the error in `run_streaming`. `_kill_session` kills the group first, unchanged, with `PermissionError` still raised under `sudo`. Then it kills in rounds, 0.05 s apart, until a round finds nothing (`_read_process_table`, `_kill_one` with `refused`). Both test modules exist (`tests/domain/test_sessions.py`, `tests/adapters/test_process_session.py`), and both documents were written (below). Every Out-of-scope item is untouched: the `Makefile` recipe still runs `timeout` without `--foreground`, there is no TERM before the KILL, `setsid` stays outside the rule, root's and the agent's processes go to `refused`, and `factory/pipeline.yml` is unchanged. The human's change 1 (F0024-S0005) is moot: F0024's backlog was removed in 23dc158a when mutation testing became sweeps only. The human's change 2 (the real check with mutmut) is still the human's. My check 2 used stand-ins, because no stage runs mutmut.

## 2 Feature smoke test

The walk-through of the feature's user is a project command whose recipe moves its work into a group of its own and writes through `tee`, stopped at its time limit. The command must leave nothing of its session, and the factory must go on only when that is true. Part 2 covers the second runner (`run_streaming`) at a callback's stop. I ran a script from the repository root with `uv run -q python "$TMPDIR/smoke/feature_smoke.py"`, then `ps`. The script writes, into a `tempfile.TemporaryDirectory()`, a `Makefile` with the recipe's shell settings (`SHELL := /bin/bash`, `.SHELLFLAGS := -eu -o pipefail -c`, `.ONESHELL:`) and the target `sweep`:

```make
sweep:
	temporary=$$(mktemp -d)
	trap 'rm -rf "$$temporary"' EXIT
	echo "$$temporary" > temporary.txt
	timeout 60 uv run --no-project python stand_in.py 2>&1 | tee "$$temporary/run.txt"
	echo "sweep: done"
```

`stand_in.py` writes `os.getsid(0)` to a file and forks four workers that sleep 60 s and write their pids: `same-group` (stays in `timeout`'s group), `own-group` (`os.setpgid(0, 0)`), `orphan` (forks and its parent exits), and `setsid` (`os.setsid()`). It then prints `stand-in: 4 workers started` and sleeps 60 s. The script calls `MakeProjectCommands(d).run("sweep", time_limit=timedelta(seconds=8))` and prints `command_line(result)` from `factory.domain.checks`, the journal line a reader sees. It reads each worker's `/proc/<pid>/stat`, then lists every non-zombie process of the session that `stand_in.py` reported. Part 2 calls `run_streaming` with a child that starts `sleep 60` under `process_group=0`, prints its pid and sleeps. Its callback returns `True` on the first line. The script ends by killing the `setsid` worker and removing the temporary folder the recipe left.

```
$ time uv run -q python "$TMPDIR/smoke/feature_smoke.py"; ps -eo pid,pgid,sid,stat,args | grep -E "stand_in|sleep 60|timeout 60" | grep -v grep || echo "ps: no stand-in, sleep 60 or timeout 60 left"
== 1. make sweep (timeout without --foreground, output through tee), limit 8 s
status: time_limit | exit_status: None | duration: 8.1 s
journal line: `sweep`: stand-in: 4 workers started (stopped at its time limit after 8 s)
worker same-group: gone
worker own-group: gone
worker orphan: gone
worker setsid: running (S)
left in the killed make's session: nothing
recipe's temporary folder after the kill: stays
== 2. run_streaming stopped by its callback, a grandchild in a group of its own
stopped: True | timed_out: False | returned after 0.1 s
grandchild: gone

real	0m8.274s
ps: no stand-in, sleep 60 or timeout 60 left
```

Green. Before S0001, this recipe form returned at the limit and left `timeout` and its workers running (S0001's smoke test pins that). The `setsid` worker runs on, as decision 5 and Out of scope say. The temporary folder stays because SIGKILL runs no `EXIT` trap; that is the feature's decision 13, but no document says it (check 5, S0003).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- **The flaky `tests/adapters/test_git_cli_work_tree.py::test_the_work_tree_id_is_the_tree_a_commit_records[tracked-ignored-file]`.** It failed once under `make check` and stalled the coder's first run (S0001, entry 8). The coder named a likely cause (entry 10): `GitCli.work_tree_id` copies the index with `shutil.copyfile` (`src/factory/adapters/git_cli.py:420`), which gives the copy a new modification time and so loses git's racily-clean guard. I reproduced it with plain git in a throwaway repository. With `core.trustctime false` and the file's and the index's modification times set to one past value, a same-size change written through a `copyfile` copy gave the old tree, and through a `copy2` copy the commit's tree. The same block through `GitCli` prints `False` today. The id is F0023's known-result key, so this is more than a flaky test: a stale id could reuse a passed check for a changed tree. **Proposed: S0002.**
- **The untested branches of `_kill_one` and `_read_process_table`.** The `ProcessLookupError` and `PermissionError` branches were pinned later by criteria 8 and 9. The `OSError` skip of an unreadable `/proc` folder stays untested, which the reviewer accepted (entry 20): reaching it would mean replacing `Path.read_bytes`. No story. Coverage of `process.py` and `sessions.py` is 100 % (`coverage report` after this `make check`), so a race in the suite reaches the branch, but no test pins it.
- **`# noqa: PT011` at `tests/domain/test_sessions.py:41`.** It is the only such marker under `tests/` (reviewer, entries 20 and 28). A `match=` per refused row would remove it. This is cosmetic, and a test change of another story's test needs leave. No story; it is listed here for the human.
- **An exception from `on_line` after the child was reaped** would let `_kill_session` read a session id that may be reused (coder, entry 7). Today's code cannot reach it: no line is passed after `_wait_for_exit`. No story.
- The documenter saw nothing stale (entry 30). The smoke tester raised nothing (entry 32).

## 5 Documentation

Read from the top: `README.md` and `docs/operator-guide.md` need nothing new. The operator guide's "A `time_limit` under `sudo`" and its section on the container's init still hold. `docs/project-guide/processes-and-checks.md` agrees with the code: the *Project commands* line, *Starting a process*, the new *Killing a session* and the `MUTANTS_SECONDS` bullet. The decision log's new entry and the pointer added to the entry of 2026-10-18 agree too. No contradictions, and no example that fails to run. Two gaps, neither misleading about what the factory does:
- *The temporary folder* (`processes-and-checks.md`, *Mutation testing*) says the `EXIT` trap removes the folder "also after a stop and after a failed run" and says nothing about a kill. `feature.md` (*The human's changes*, point 1; *Out of scope*) says the sentence that the folder stays after a kill is in S0001's docs criterion. It is not, and check 2 shows that the folder stays.
- The superseded entry *Mutation testing per story*, decision (4), still says the factory's kill "does not reach mutmut", with no pointer to the entry that corrects it. The entry of 2026-10-18 got such a pointer.
**Proposed: S0003**, both sentences, documents only.

## 6 Decisions taken for the human

From `feature.md`, to accept or revisit:
1. The fault lies in the factory's kill, and the recipe's `timeout` only triggers it. The fix is in `factory.adapters.process`, for every command.
2. The factory is fixed, not the recipe: the `mutants` recipe keeps `timeout` without `--foreground`.
3. The kill uses the session, not a walk of parent ids, a cgroup or a subreaper. It reads `/proc/<pid>/stat` and adds no dependency.
4. The group kill stays first, unchanged, and another user's process is not waited for (`refused`).
5. The rounds end when nothing is left, with no time limit of their own. A zombie counts as gone, and a `setsid` process stays.
6. One kill for every caller: `run_process` and `run_streaming`, git, make and both runtimes.
7. The pure part is in the domain (`factory.domain.sessions`).
8. The tests use `ROOMY_LIMIT` and `ROOMY_BOUND_SECONDS`, and read the end at once with `is_gone(pid, within=0)`.
9. No leave to change an earlier test.
10. One story.
11. The feature's number and name.
12. **Open:** `timeout --foreground` in the recipe for an acceptance's `make mutants`. It is moot now that no stage runs `make mutants`, and only sweeps by hand remain.
13. **Open:** a TERM before the KILL. Recommended and kept: KILL only. Check 2 shows its price, a recipe temporary folder left behind (S0003 documents it).
14. **Open:** does mutmut, or a test it runs, leave the session with `setsid`? This waits for the human's change 2, with real mutmut.
15. **Open:** the order with F0024-S0005. It is moot: F0024's backlog was removed (23dc158a).

From the story's journal (S0001):
- The coder made the Interface's one-line docstring of `left_to_kill` a summary line plus a sentence, because it ran past ruff's 100 columns (entry 7).
- The reviewer added criterion 8 (`PermissionError` → `refused`, entry 12) and criterion 9 (`ProcessLookupError` skipped, entry 20). Both were pinned by `monkeypatch` on `os.kill`, with no change under `src/`.
- The reviewer accepted the untested `OSError` skip of `_read_process_table` (entry 20).
- The tester merged the two `parse_stat` tests into one parametrized test, at the reviewer's request (entries 12 and 16). It joined two parameters into one (`ended`) to satisfy PLR0917 (entry 24).

Earlier tests changed: none. Each review entry (12, 20, 28) names the diff as only new test files, `tests/domain/test_sessions.py` and `tests/adapters/test_process_session.py`. Criterion 7 pins the four earlier sudo and process test files as unchanged.

## 7 Slow checks

Beyond `make check` (green, `test: green (157.8 s)`, 99.17 % coverage), the project offers `make duplicates`, `make documents` and `make mutants`. `make mutants` is not run (check 3). `make documents`: `documents ok`. `make duplicates`: `duplicates: 5 new, 33 known, 3 gone`. All five new findings are outside this feature, in `claude_runtime`/`opencode_runtime` and `clock.py`, as the reviewer noted. There is no image scan or SBOM.

From `.reports/junit.xml`: 6170 tests, 787.7 s summed over the workers. The slowest are `test_opencode_sudo_time_limit[...past-the-limit]` (11.5 s each), then a group at 10.0 to 10.1 s. F0030's ten time-limit rows of `tests/adapters/test_process_session.py` are in that group, each about 10 s by design (`ROOMY_LIMIT`). Together they add about 101 s summed, about 13 % of the suite's summed time. Their stop and raise rows take 0.1 s, and `tests/domain/test_sessions.py` takes nothing measurable. Under xdist they run in parallel, so the wall time grows far less.

Disk: `/work` 0.5 GB used, `/state` 0.0 GB and `/tmp` 0.0 GB, both at the start record and now. No growth.

## 8 Cost

One story, F0030-S0001: 15 runs, 28.6 min, 118 turns, $4.94. Human interventions: 0 questions answered, 0.0 h waited; the story never needed the human. It stands out by its runs, not its size. The code was done in the coder's first run (b54c626c), and the other runs went to:
- one stall on the flaky git test above: a second coder run ($0.23) that changed nothing;
- two rework rounds. Each review added one criterion that only needed a test (8, then 9). Each round cost a coder run that only passed the work to the tester, a tester run, a coder run that confirmed it, and a review: about $1.0 to $1.3 per round.

The reviewers' runs were the dearest single runs ($0.66, $0.58). Had intake asked for the two `os.kill` stand-in rows at the start (entry 3 accepted the branches as covered, and they were not), the story would have needed about 7 runs.

## Proposed stories

- `F0030-S0002-the-work-tree-s-id-sees-a-change-made-in-the-tick-of-the-last-index-write.md`: copy the index with its timestamps in `GitCli.work_tree_id`. This fixes the flaky test that stalled S0001, and a possibly stale known-result key. The cause is reproduced, and the story pins it with a test that does not depend on timing.
- `F0030-S0003-the-documents-say-what-the-factory-s-kill-of-make-mutants-leaves.md`: documents only. The project guide says the recipe's temporary folder stays after the factory's kill, as `feature.md` promised. The superseded decision (4) of F0024 gets a pointer to F0030's entry.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 2 stories proposed
   1. Scope: none. S0001 built every Scope item, and no Out-of-scope item was touched. The human's change 1 is moot, because F0024's backlog was removed in 23dc158a. Change 2, the real check with mutmut, is still the human's to do.
   2. Feature smoke test: green. A `Makefile` shaped like the `mutants` recipe (`timeout` without `--foreground`, output through `tee`) ran a stand-in for mutmut with workers in the same group, in a group of their own and orphaned. `MakeProjectCommands.run` with an 8 s limit returned `time_limit` after 8.1 s, and nothing of the session was left. Only the `setsid` worker kept running, which is out of scope. `run_streaming` stopped by its callback returned after 0.1 s with the grandchild gone. The recipe's temporary folder stays after the kill.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: the flaky `test_git_cli_work_tree[tracked-ignored-file]` that stalled S0001 is caused by the `shutil.copyfile` in `GitCli.work_tree_id`. Reproduced with git: `copyfile` gives the old tree, `copy2` the right one. It can also make F0023's known-result key stale (S0002). The `# noqa: PT011` and the race branches are listed, with no story.
   5. Docs: consistent with the code. One gap: no document says the recipe's temporary folder stays after the factory's kill, although `feature.md` says S0001's docs criterion carries that. Also, F0024's superseded decision (4) has no pointer to F0030's entry (S0003).
   6. Decisions: the feature's 15 decisions are listed. 12 and 15 are moot now, 13 is kept (KILL only), and 14 waits for change 2. The story's own choices are listed too: the docstring split, and criteria 8 and 9 added by the reviewer. No earlier test was changed.
   7. Slow checks: `make check` green (test 157.8 s), `documents ok`, `duplicates: 5 new` (none in this feature's files). The ten time-limit rows run about 10 s each by design, about 101 s summed. Disk did not grow.
   8. Cost: 1 story, 15 runs, 28.6 min, $4.94, no question to the human. The cost came from one stall on the flaky git test and two rework rounds that each only added a test (criteria 8 and 9).
3. factory: done (pull request merged); cost: 1 runs, 9.1 min, 40 turns, 128349 tokens in (3061508 more from cache), 34040 out, $2.32
