---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 371
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T23:26:26.606687Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T23:30:34.007509Z'
  stage: acceptance
  run: e662c42e2d144e9a83cad24a2b5a2f81
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-20T23:31:54.908360Z'
  stage: done
stories: [F0030-S0001, F0030-S0002, F0030-S0003]
outcome: accepted
---

# Acceptance of A command stopped at its time limit leaves no process running

## Recommendation

**Accepted.** The whole now does what `feature.md` promised. When a project command is stopped at its time limit, none of the processes in its session are left running, and the factory goes on only once they are gone. The feature smoke test below checks this end to end through `MakeProjectCommands.run` and `run_streaming`, and S0002's fix of the work tree's id holds through the real `GitCli`. `make check` is green. Both stories the first acceptance (F0030-A0001) proposed are built as written. No finding is of any weight, so no story is proposed.

## 1 Scope

None. `feature.md`'s Scope now lists three stories, and each is built and archived:
- **S0001, the kill.** `src/factory/domain/sessions.py` holds `ProcessEntry`, `parse_stat` and `left_to_kill`. `_kill_session` in `src/factory/adapters/process.py` runs at all three call sites (the time limit, a stop by the callback and an error of the callback). F0030-A0001 judged this in full. It is unchanged since, apart from `read_process_table` becoming public, which another feature's leftovers program reuses.
- **S0002, the work tree's id.** `GitCli.work_tree_id` copies the index with `shutil.copy2` (`src/factory/adapters/git_cli.py:427`), and the comment above the call says why. The new test module is `tests/adapters/test_git_cli_work_tree_tick.py`.
- **S0003, documents only.** It changes `docs/project-guide/processes-and-checks.md` (*The temporary folder*) and `docs/decisions.md` (the pointer in decision (4) of *Mutation testing per story*, and the sentence on tests that mutmut runs). Nothing under `src/` or `tests/` changed.

Every Out-of-scope item is untouched:
- The `Makefile`'s `mutants` recipe still runs `timeout` without `--foreground`.
- There is no TERM before the KILL.
- A process that calls `setsid` stays outside the kill.
- Another user's processes go to `refused`.
- `factory/pipeline.yml` was not changed by any story.

Both of the human's changes are settled. Change 1 (F0024-S0005) became moot when F0024's backlog was removed (23dc158a). Change 2, the real check with mutmut, was done on 2026-10-20 and answered decision 14 (S0003's Description).

## 2 Feature smoke test

From a user's side, the feature has two promises:
- A project command whose recipe moves its work into a group of its own, and writes through `tee`, leaves nothing of its session when it is stopped at its time limit. This is checked for `make` (part 1) and for the streaming runner stopped by its callback (part 2).
- The id of the work tree, which keys the known results, sees a change made in the tick of the last index write (part 3, S0002).

I ran the script from the repository root and then ran `ps`.

The script writes the following into a `tempfile.TemporaryDirectory()`. First, a `Makefile` with the shell settings of the `mutants` recipe (`SHELL := /bin/bash`, `.SHELLFLAGS := -eu -o pipefail -c`, `.ONESHELL:`) and this target:

```make
sweep:
	temporary=$$(mktemp -d)
	trap 'rm -rf "$$temporary"' EXIT
	echo "$$temporary" > temporary.txt
	timeout 60 uv run --no-project python stand_in.py 2>&1 | tee "$$temporary/run.txt"
	echo "sweep: done"
```

Second, `stand_in.py`. It records its session id and forks four workers that each sleep 60 s:
- `same-group` stays in `timeout`'s group;
- `own-group` calls `setpgid(0, 0)`;
- `orphan`'s parent exits;
- `setsid` calls `setsid()`.

It then prints one line and sleeps.

Part 1 calls `MakeProjectCommands(d).run("sweep", time_limit=8 s)` and prints `command_line(result)`. It then reads each worker's `/proc/<pid>/stat` and lists every non-zombie process still in the session. Part 2 calls `run_streaming` with a child that starts `sleep 60` under `process_group=0` and prints its pid; the callback stops on that first line. Part 3 makes a repository with `core.trustctime false`, commits `kept.log` through `GitCli.commit`, and rewrites the file to the same size. It sets the modification times of the file and of `.git/index` to one past value, then compares `work_tree_id()` with `HEAD^{tree}` after the next commit. The script ends by killing the `setsid` worker and removing the folder the recipe left behind.

```
$ time uv run -q python "$TMPDIR/smoke/feature_smoke.py"; ps -eo pid,pgid,sid,stat,args | grep -E "stand_in|sleep 60|timeout 60" | grep -v grep || echo "ps: no stand-in, sleep 60 or timeout 60 left"
== 1. make sweep (timeout without --foreground, output through tee), limit 8 s
status: time_limit | journal line: `sweep`: stand-in: 4 workers started (stopped at its time limit after 8 s)
worker same-group: gone
worker own-group: gone
worker orphan: gone
worker setsid: running (S)
left in the killed make's session: nothing
recipe's temporary folder after the kill: stays
== 2. run_streaming stopped by its callback, a grandchild in a group of its own
stopped: True | timed_out: False | returned after 0.1 s
grandchild: gone
== 3. the work tree's id after a same-size change in the tick of the last index write
work_tree_id equals the next commit's tree: True

real	0m8.362s
user	0m0.454s
sys	0m0.237s
ps: no stand-in, sleep 60 or timeout 60 left
```

Green. Only the `setsid` worker runs on, which Out of scope and decision 5 allow. The recipe's temporary folder stays, and S0003's paragraph now says exactly that. Part 3 printed `False` before S0002 (F0030-A0001, check 4).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

None of weight.
- **S0002.** The coder noticed nothing beyond the docs criterion. The reviewer and the documenter had no remarks, and the documenter found nothing stale.
- **S0003.** The tester and the coder noted that the phrase `runs on until it ends by itself` has no grep in the smoke test. It is in the text (`docs/project-guide/processes-and-checks.md:224`), and `make documents` passed. The documenter found nothing stale.
- **Carried over from F0030-A0001, each still without a story.**
  - The `# noqa: PT011` at `tests/domain/test_sessions.py:56` is cosmetic. A second one at `tests/adapters/test_process_table.py:42` comes from another feature.
  - A `ValueError` from `read_process_table` on an unreadable status line would leave `_kill_session` partway through. The kernel's own `stat` text is always readable, so no story.
- **One for the human, raised by S0003's text.** Decision 14's answer stands: a process that one of mutmut's tests starts in a session of its own outlives a kill of `make` by up to 60 s. Today only the human's sweeps run mutmut, outside the factory, so this costs at most a minute of a stray `claude` stand-in. A test-side fix would need leave to change another story's test (`tests/adapters/test_claude_runtime.py`). No story is proposed, because the human decided "documented only".

## 5 Documentation

None that misleads. I read `README.md`, `docs/operator-guide.md` and `docs/project-guide/processes-and-checks.md` against each other and against the code:
- *Killing a session*, the `MUTANTS_SECONDS` bullet and *The temporary folder* agree with each other and with the code.
- The row for `work_tree_id` in `docs/project-guide/git-and-hosting.md` matches `src/factory/adapters/git_cli.py:427`.
- `docs/decisions.md` has the entries *A command stopped at its time limit loses every process of its session* (line 900) and *The work tree's id copies the index with its timestamps* (line 970). Decision (4) of *Mutation testing per story* now points to the first of these (line 814).
- `README.md` needs nothing, and `make documents` prints `documents ok`. No example fails to run: S0003's two greps print `1`, and S0002's smoke block is part 3 above.

One fine point, not a finding. *The temporary folder* describes a kill by the factory without `FACTORY_AGENT_USER`. Under `sudo`, the agent's own `timeout` kills at the limit, and the leftovers program then also ends a process that one of mutmut's tests started in a session of its own. *The leftovers* in the same file (line 24) and its *Known limits* (line 137) both say so. No stage runs `make mutants` through the factory now, so the paragraph cannot mislead anyone.

## 6 Decisions taken for the human

From `feature.md` (F0030-A0001 already listed decisions 1 to 11 in full): the fault is in the kill, not the recipe; the fix is in the factory; the kill uses the session read from `/proc`; the group kill comes first and `refused` is not waited for; the rounds have no time limit; one kill serves every caller; the pure part is in the domain; the tests use `ROOMY_LIMIT` and `is_gone(pid, within=0)`; no leave to change earlier tests; one story; the number and the name. The open ones now stand as follows:
- **12.** `timeout --foreground` in the recipe: moot, because no stage runs `make mutants`.
- **13.** A TERM before the KILL: still open. The feature keeps KILL only, and the price, a leftover temporary folder, is now documented (S0003).
- **14.** Does a process leave the session? Answered by the human on 2026-10-20: one of mutmut's tests does. It is documented only, with no code story (S0003).
- **15.** The order with F0024-S0005: moot (23dc158a).

From the journals of S0002 and S0003:
- **S0002 scope.** Intake asked whether S0002 belonged to F0030 (entry 3). The human answered (a) and added S0002 and S0003 to `feature.md`'s Stories and Scope on `main` (entry 4).
- **S0002 coder (entry 10).** The coder used `copy2` and rejected `copyfile` followed by `copystat` or `os.utime`, which does the same in two steps.
- **S0002 decision log.** The decision log rejects `git read-tree HEAD` and `update-index --really-refresh`, because either would rehash every file on every call.
- **S0003 coder (entry 7).** The coder left both documents to the docs stage instead of writing criterion 3's text.

Earlier tests changed: none. S0002's reviewer (entry 12) names only the new file `tests/adapters/test_git_cli_work_tree_tick.py` (status `A`). S0003's reviewer (entry 9) found no test file in the diff.

## 7 Slow checks

Beyond `make check` (green, `test: green (63.2 s)`, 99.14 % coverage), the project offers these checks:
- `make documents`: `documents ok`.
- `make duplicates`: `duplicates: 6 new, 33 known, 3 gone`. None of the six new findings is in this feature's code. Four are similar code shared by `claude_runtime` and `opencode_runtime`. One is `ManualWaiter` in `clock.py`. One is `output_abandoned` at `process.py:53`, introduced by F0040-S0005 (7d5e4108), not by F0030.
- `make mutants`: not run (check 3).
- No image scan and no SBOM.

From `.reports/junit.xml`: 6407 tests, 729.0 s summed over the workers.
- The slowest tests are the two `test_opencode_sudo_time_limit[...past-the-limit]` rows at 11.5 s each, then a group at about 10.1 s.
- F0030's `tests/adapters/test_process_session.py` has 12 tests that sum to 100.4 s (`ROOMY_LIMIT` by design), about 14 % of the summed time. Its rows lead that 10.1 s group.
- `tests/domain/test_sessions.py` (24 tests) takes 0.0 s, and S0002's two rows take 0.1 s.

Disk: at the previous record (`disk start`), `/work` had 0.5 GB used. Now (`disk acceptance`) it has 0.0 GB used, and `/state` and `/tmp` show 0.0 GB at both. No growth.

## 8 Cost

The three stories took 28 runs, 36.2 min and 181 turns, with 678696 tokens in (3413226 more from cache) and 73820 out, for $6.73:
- **S0001:** 15 runs, 28.6 min, $4.94. It stands out, for the reasons F0030-A0001 gave: one stall on the flaky git test that S0002 then fixed, and two rework rounds that each only added a test.
- **S0002:** 7 runs, 4.7 min, $0.99. The extra run is a second intake, after its question.
- **S0003:** 6 runs, 2.8 min, $0.80. About $0.26 of that went to the tester and the coder confirming that a documents-only story changes nothing under `src/` or `tests/`. The pipeline gives such a story no shorter path.

Human interventions: one question was answered (cause: question), and the stories waited 0.0 h for it. It was S0002's intake question (entry 3), asked because the acceptance had proposed the story outside `feature.md`'s Scope. The human answered in about a minute by widening `feature.md`. S0002 is therefore the story that needed the human most.

The first acceptance, F0030-A0001 ($2.32), is not part of this sum.

## Proposed stories

None. No finding calls for a change. The remarks under 4 and 5 are cosmetic or already decided by the human.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed. I couldn't remove my smoke script and report draft from the run's temporary folder (the rm was denied), so they stay there until the factory removes that folder after the run.
   1. Scope: no finding. All three stories are built and archived: S0001 (the kill of the whole session), S0002 (`work_tree_id` copies the index with `shutil.copy2`) and S0003 (documents only). No out-of-scope item was touched. The human's change 1 is moot, and change 2 (the real check with mutmut) was done on 2026-10-20 and answered decision 14.
   2. Feature smoke test: green.
      - `MakeProjectCommands.run` on a target shaped like the mutants recipe (`timeout` without `--foreground`, output through `tee`) with an 8 s limit returned `time_limit` after 8.1 s. Its workers in the same group, in their own group and orphaned were all gone, and nothing was left in the session. Only the worker that called `setsid` ran on, which is out of scope. The recipe's temporary folder stays, as S0003's paragraph now says.
      - `run_streaming` stopped by its callback returned after 0.1 s, and its grandchild was gone.
      - `work_tree_id` saw a same-size change made in the tick of the last index write (`True`).
   3. Mutation testing: by sweep, not run here.
   4. Noticed: none of weight. S0002 and S0003 raised nothing. Two items carry over from A0001 without a story: a cosmetic `# noqa: PT011`, and a `ValueError` the kill cannot reach in practice. A process that one of mutmut's tests starts in its own session can outlive the kill by up to 60 s; that stays documented only, as the human decided for decision 14.
   5. Docs: they agree with each other and with the code, and `make documents` is ok. One fine point, not a finding: *The temporary folder* describes the kill without `sudo`, and under `sudo` the leftovers program also ends that test's process (lines 24 and 137 of the same file).
   6. Decisions: the feature's decisions 1 to 11 are listed. Decisions 12 and 15 are moot, 13 stays at KILL only, and 14 was answered by the human. From the journals: S0002's scope question was answered (a), `copy2` was chosen over `copyfile` plus `copystat`, and `read-tree` and `--really-refresh` were rejected. No earlier test was changed.
   7. Slow checks: `make check` green (test 63.2 s, 99.14 % coverage) and `documents ok`. `duplicates` reports 6 new, none of them in F0030's code (`output_abandoned` comes from F0040-S0005). `test_process_session` takes 100.4 s summed by design, about 14 % of the suite. Disk did not grow (/work 0.5 GB used at the start, 0.0 GB now).
   8. Cost: 28 runs, 36.2 min, $6.73. S0001 stands out ($4.94, 15 runs, a stall and two rework rounds). S0002 cost $0.99 and S0003 $0.80; about $0.26 of S0003 went to tester and coder runs that confirmed a no-op. One question was answered (S0002's intake scope question), with 0.0 h waited, so S0002 needed the human most.
3. factory: done (pull request merged); cost: 1 runs, 4.1 min, 22 turns, 74513 tokens in (1143128 more from cache), 16111 out, $1.15
