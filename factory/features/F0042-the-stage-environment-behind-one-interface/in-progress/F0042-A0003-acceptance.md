---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 429
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-24T23:30:30.787093Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-24T23:36:07.400567Z'
  stage: acceptance
  run: f5c6c2c224f247369f4358f5650fa682
stories: [F0042-S0001, F0042-S0002, F0042-S0003, F0042-S0004, F0042-S0005, F0042-S0006, F0042-S0007, F0042-S0008, F0042-S0009, F0042-S0010, F0042-S0011, F0042-S0012, F0042-S0013, F0042-S0014, F0042-S0015, F0042-S0016, F0042-S0017, F0042-S0018, F0042-S0019]
outcome: null
---

# Acceptance of The stage environment behind one interface

## Recommendation

**accepted.** Every scope item of `feature.md` has its story and its code. The one story the second acceptance (F0042-A0002) proposed, S0019 (every shared test helper is listed and held once), is merged and does what it said. `make check` was green as I found it, and the feature smoke test is green:

- a green and a red `container` stage run end to end;
- an `inline` stage behaves as before;
- the wiring works from the environment variables, with stand-in `zfs` and `podman`.

What is left is three trivial remarks, listed with no story. No promise is broken, and no document misleads a user.

## 1 Scope

None. The first two acceptances checked each scope item against the code. Since F0042-A0002 was merged (`8dd6b264`), `git diff --stat 8dd6b264 HEAD -- . ':!factory' ':!planning'` shows 22 files under `tests/`, `docs/project-guide/README.md` and the human's night log. Nothing under `src/` changed.

S0019 is outside the Scope list of `feature.md`, which ends at S0016, as S0017 and S0018 were. It repairs a finding of the feature's own acceptance and stays within the Goal and the Out of scope. Nothing of *Out of scope* was built:

- every v1.1 layer is still there;
- there is no `vm/`;
- no agent text changed.

Both of the human's changes are on `main` (`sync` in `Makefile` and `factory/pipeline.yml`, and the v1.2 bullet in `CLAUDE.md`). The Goal's real proof is still F0043's story 4 on the VM, as `feature.md` says.

## 2 Feature smoke test

Green. The test is one pytest module, `$TMPDIR/smoke/test_feature_smoke.py`, run on the suite's own fixtures (`-p conftest`). It has four parts:

- **A1:** a whole `container` stage through `StageRunner` (`container_support.whole_stage`), with its checks in check containers (`ContainerMakeCommands`), then the next stage's `prepare` on the same environment.
- **A2:** the same stage with a red `lint`, run in its check container.
- **A3:** an `inline` stage on the same fixtures.
- **B:** the real `read_settings` and `build_boundaries` from `FACTORY_*` variables. Stand-in `zfs` and `podman` (`zfs_support`, `podman_support`) answer, and the container preflight items of `machine_extras` run up to the agent run probe. Three faulty settings follow.

```
$ PYTHONPATH=/work/checkout/tests uv run --project /work/checkout pytest "$TMPDIR/smoke/test_feature_smoke.py" --rootdir "$TMPDIR/smoke" -c /dev/null -p conftest -s -q --no-cov -p no:cacheprovider
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s

[A1] environment: ContainerEnvironment
[A1] next stage: doing stall: None
[A1] pushed head is report commit: True
[A1] taken tests/test_a.py: True
[A1] left out notes.md: True
[A1] journal names notes.md: True
[A1] timing lines: ['2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s']
[A1] container runs: 3
[A1] host clean: True
[A1] next prepare: stray gone True, home leftover gone True, taken kept True, synced True
.2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s

[A2] stall reason: reason='check_red' attempts=1 attempts_cap=2 commit='2c39635bc6ab7d8be1cf1ca350e9621dabb24d5f' pull_request=1 note='posted' take=TakeReport(left=['factory/features/F0001-example/in-progress/F0001-S0001-first.costs.jsonl'], restored_work_item=False)
[A2] container runs: 2
[A2] taken file pushed with the stall: True
[A2] timing lines: 1, host clean: True
[A2] journal holds the lint output: True
[A2] stage after: tests, blocked: None
.
[A3] environment: InlineEnvironment
[A3] next stage: doing, pushed: True
[A3] timing lines: []
.
[B] ZfsSnapshots PodmanRuns ContainerEnvironment
[B] ClaudeCodeRuntime ContainerMakeCommands agent_home=None
[B] item token-file False None: no token file is set
[B] item podman True podman version 4.9.3
[B] item zfs True zfs-2.2.2-0ubuntu9
[B] item dataset True 
[B] item stage-image True 
[B] fault: FACTORY_AGENT_USER: is set, but the container environment runs no second user
[B] fault: FACTORY_DATASET: missing for the container environment
[B] fault: FACTORY_STAGE_ENVIRONMENT: holds docker, which is neither inline nor container
.
4 passed in 0.87s
```

What the output shows:

- **A1 is the feature's promise.**
  - The take commits the allowed file and leaves the other out, and the journal names the one left out.
  - The stage writes one timing line.
  - Three container runs: the sync, then `lint` and `test` in check containers on the taken result.
  - The host's work tree stays clean.
  - The next `prepare` removes what the agent left in the checkout and in `home/`, keeps the pushed file and syncs again.
- **A2:** a red check in its container ends as the stall `check_red`.
  - The taken file is pushed with the stall.
  - The stall writes no second timing line.
  - The make output reaches the journal.
  - The work item stays at `tests`.
- **A3:** `inline` behaves as before and writes no `stage environment:` line. That is the operator's check on `self` (the human's change 4).
- **B:** the four container items pass. `token-file` fails only because my environment set no token file. The three settings faults print the texts the operator guide gives them.

A second run with `-k a2` also printed the journal and the sidecar on the pushed head. The journal's stall entry names only the check, with no "undid" sentence, and the cost sidecar is on the head. So the `left` entry above is the factory's own sidecar, which the stall's take leaves out by design: `src/factory/application/stalls.py:84` writes the sidecar after the take, and `stage.py:262-264` drops it from an agent's entry. Not a finding.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

New since the second acceptance (S0019):

- **Tester, coder and reviewer of S0019:** `tests/application/test_stall_edges.py:44` still writes the literal `"written by the agent\n"` inside a method. The guard `tests/test_shared_stage_constants.py` counts only top-level assignments, as its criterion says, so this copy is outside its reach. It is one literal in one test. Listed, no story.
- **S0019's smoke tester:** the guide's `take_support.py` entry names the guard but not `top_level_copies`, which only the `search_support.py` entry names. Read together the two entries say it all. Listed, no story.
- **The other `"notes.md"` and `"tests/test_a.py"` literals** (my own search): `test_acceptance_closed.py:539`, `handlers/test_closed.py:238`, `handlers/test_merged.py:324`, `handlers/test_closed_send_back.py:402,425`, `test_acceptance_merged.py:357`, `domain/test_acceptance_status.py:43`, `domain/test_acceptance_facts.py:50` and `adapters/test_fake_agent_runtime.py:54,57`. Each is a call argument with its own meaning (a file the human pushes, a folder entry, a fake's write), not a copy of the stage test's agent path, and none is a top-level constant. No finding.
- **S0019, documenter:** nothing stale noticed.

Still open from the earlier acceptances, unchanged, listed with no story:

- `_is_ignoring` misreads an ignore-file path that holds a colon (`src/factory/adapters/git_cli.py:180`).
- The runtimes' parallel container branch (`make duplicates`: 11 new findings, unchanged), for F0044 to fold when the `sudo` chain goes.
- A failed `prepare` keeps the durations of the last successful one (documented).
- `wiring.py:390`, the unreachable guard for mypy. It is again the line that coverage misses.
- The dated `docs/decisions.md:166-168` "after every undo", for F0044 to revisit.

## 5 The documentation as a whole

None. Since F0042-A0002 the only document change is S0019's in `docs/project-guide/README.md`, *Shared test helpers*. I read that section from the top:

- The seven missing modules now have entries (`home_files_support.py`, `leftovers_runtime_support.py`, `leftovers_support.py`, `root_support.py`, `stall_support.py`, `time_limits.py`, `torn_record_support.py`).
- `stage_run_support.py` now names `INSIDE` and `NOTES` and their guard.
- `container_support.py` sends the reader there for `INSIDE` and `NOTES`.
- `take_support.py` names `AGENT_TEXT`'s one home and its guard.
- `search_support.py` names `modules_matching`, `modules_assigning` and `top_level_copies`.

Each entry agrees with the code: `tests/stage_run_support.py:17-18`, `tests/take_support.py`, and `tests/search_support.py:37-44`. The S0019 smoke tester's loop found no module without an entry. Nothing else in `README.md` or `docs/` changed since the second acceptance, which read them whole. Its findings were repaired by S0017 and S0019.

## 6 Decisions taken for the human

The decisions of `feature.md` (1 to 23) and the human's answers in S0001 to S0018 are listed in the first two reports (`done/F0042-A0001-acceptance.md` and `done/F0042-A0002-acceptance.md`, section 6). The human merged both, and nothing in them changed since. To accept or revisit, in short:

1. Two environments behind `StageEnvironment`, with `snapshots` and `containers` in `Boundaries`.
2. `run_agent` returns `SealedRun`.
3. The sync limit comes from the definition's `sync`: 10 minutes without it, 5 here.
4. `prepare(commit, branch)`.
5. Fetch every branch, then a checkout and a hard reset.
6. The agent files are copied in by the sync container.
7. The check container copies what differs from `HEAD`.
8. `ContainerMakeCommands` lives in `make_commands`.
9. The journal sentence stays "undid".
10. `take(stage_start, work_item_path, …)`, and `mount_point` is on the interface.
11. `launch` and `run`, with 30 s of grace.
12. The fake's path mapping.
13. `zfs diff -FH`.
14. One executable each for `FACTORY_ZFS` and `FACTORY_PODMAN`.
15. No second user under `container`, and the inline items left out.
16. `HOME=/work/home`, without the logins.
17. The errors.
18. The leaves.
19. The number.
20. S0013, the stall's take.
21. S0014, the login out of the tests.
22. Exit status 255 at podman's limit.
23. The fence, with the network kept.

From S0017 and S0018, as listed in the second report: the human's answer (a) on the S0017 smoke-test count, and the coder's practice of sending a copied-helper finding back to the tester under the standing leave.

New since then:

- **S0019, the human (entry 18), option (a):** the reviewer added `modules_assigning` to criterion 5 and to the Interface's `search_support.py` bullet, one clause each, and nothing else. This is the 14th answer of the feature.
- **S0019, tester:** gave the literal `"factory-1"` no top-level name in `test_shared_constants.py`, because the guard would count the name as a copy.
- **S0019, the renames the Interface named:** `AGENT_FILE` became `INSIDE` in `test_stall_edges.py`, docstring included, and `WRITTEN` became `INSIDE` in `test_stage_environment.py`.
- **S0019, smoke tester:** read criterion 5's "name the guard and `top_level_copies`" as met by the two entries together (see 4). The human may read it otherwise.

Earlier tests that S0019 changed, each under the standing leave to move a shared test helper. The S0019 reviewer's entries 9, 17 and 20 name all 21 files with their leave. No test was renamed, and no test now checks anything different:

- `tests/application/`: `test_after_agent.py`, `test_container_stage_checks.py`, `test_costs.py` (imports only, after the round-0 blank line was undone), `test_opening.py`, `test_stage_environment.py`, `test_stage_environment_calls.py`, `test_stage_finish.py`, `test_stage_run.py`, `test_stall_container.py`, `test_stall_edges.py`, `test_stall_environment.py`, `test_stall_labels.py`, `test_stall_reasons_recorded.py`, `test_stalls.py`, `test_undo.py`, `test_undo_nested_claude.py`.
- `tests/`: `container_support.py`, `search_support.py`, `stage_run_support.py`, `stall_support.py`, `test_shared_constants.py`.

No earlier test changed without a leave.

## 7 The slow checks

The project offers nothing beyond `make check` but the records, and `make mutants` is a sweep (check 3).

- **`make check`:** green as I found it. `make test` ran 7582 tests (0 failures, 1 skipped) in 64.7 s, with branch coverage at 99.19 %.
- **Slowest tests (JUnit):**
  - Earlier features' `ROOMY_LIMIT` waits: `tests.adapters.test_opencode_sudo_time_limit` (two rows, 11.5 s each), then `test_process_session` and `test_make_commands` rows at 10.06 s.
  - F0042's slowest are the two podman time-limit rows of `test_podman_timeout_status` (10.0 s each, deliberate waits).
  - S0019's new guard takes 0.29 to 0.39 s a row.
- **`make duplicates`:** not run by me. S0019's coder recorded `duplicates: 11 new, 36 known, 2 gone`, unchanged since the first acceptance, and nothing under `src/` changed.
- **Disk:** now `/work` 967.2 GB free and 0.5 GB used. At the previous record (`disk acceptance`, the second acceptance) it was 967.8 GB free and 0.0 GB used, so used space grew by 0.5 GB on `/work`, and free space fell by 0.6 GB on all three mounts alike (one filesystem underneath). The growth is the checkout's git-ignored `.venv` (511 MB by `du`), which existed when this record was taken. The first acceptance's record was the same 0.5 GB. The feature's changes since then are 22 test and guide files, about 0.1 MB. Nothing is left to explain.

## 8 Cost

The 19 stories cost 213 runs, 312.4 min, 1807 turns and $75.38, about $3.97 a story.

- **S0019, the one story since the second acceptance:** $2.74, 11 runs, 12.2 min. It had one rework round: the reviewer found the new guard's walk copied from `test_shared_constants.py`, plus a stray blank line, and the tester moved the walk into `search_support.modules_assigning`. It also asked the human one question, about criterion 5 not naming that helper.
- **Over the whole feature:** S0002 still stands out ($6.63, 21 runs, 31.2 min). Three review rounds each found one more coverage row of the `zfs diff` reader, and the human answered the round cap. After it come S0007 ($6.48, the container cycle itself) and S0008 ($5.78, one rework round).

Human interventions: 14 answers (13 questions and 1 round cap), 0.5 h of waiting in all. The new question (S0019, entry 17) came from my own proposal in the second acceptance. Its criterion 5 named the guide entries but could not name a helper that review later asked for, and the reviewer cannot change a criterion. S0002 needed the human most: three answers, because its Interface left the reading of `zfs` output open on several sides.

## Proposed stories

None. The remarks in 4 are one literal inside a test method, one name that one guide entry leaves to its neighbour, and the items F0044 will meet anyway. None is worth a run of its own.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed. `make check` was green as I found it: 7582 tests, coverage 99.19 %. The feature smoke test is green (4 passed).

   1. Scope: none. Every scope item has its code. Since F0042-A0002 only S0019 was merged, and it changed tests and one guide section, nothing under `src/`. S0019 repairs that acceptance's finding and stays inside the Goal. Nothing out of scope was built.
   2. Feature smoke test: green, 4 parts.
      - A green `container` stage: sync, then the take (the allowed file committed, the other left out and named in the journal), one timing line, `lint` and `test` in check containers, a clean host. The next `prepare` clears the dataset and keeps the pushed file.
      - A red `lint` in its check container stalls `check_red`, and the taken file is pushed with the stall.
      - An `inline` stage behaves as before and writes no timing line.
      - Wiring from `FACTORY_*` variables with stand-in `zfs`/`podman`: the four container preflight items pass, and the three settings faults print their texts.
   3. Mutation testing: by sweep, not run here.
   4. What the stories noticed: listed, no story.
      - One `"written by the agent\n"` literal inside a method in `test_stall_edges.py:44`.
      - The guide's `take_support.py` entry leaves `top_level_copies` to the `search_support.py` entry.
      - Items still open from earlier acceptances: `_is_ignoring` with a colon, the runtimes' parallel container branch, durations after a failed `prepare`, `decisions.md:166-168`.
   5. Documentation: none. S0019's *Shared test helpers* entries agree with the code, and no module is left without an entry.
   6. Decisions: `feature.md` decisions 1 to 23 and the earlier answers are as in the first two reports. New:
      - The human's answer (a) in S0019 on criterion 5.
      - S0019's renames `AGENT_FILE`/`WRITTEN` → `INSIDE`, as its Interface named.
      - The smoke tester's joint reading of criterion 5.
      - S0019 changed 21 earlier test files, all under the standing leave and named by the reviewer. No test changed without a leave.
   7. Slow checks: nothing beyond `make check`.
      - The slowest tests are earlier features' `ROOMY_LIMIT` waits at 11.5 s. F0042's slowest are the podman time-limit rows at 10.0 s.
      - `duplicates` was not rerun (S0019 recorded 11 new, unchanged).
      - Disk used on `/work` grew from 0.0 to 0.5 GB. That is the git-ignored `.venv` (511 MB), the same as the first acceptance's record, not the feature.
   8. Cost: $75.38, 213 runs, 312.4 min. S0019 cost $2.74, with one rework round (a copied guard walk) and one question. S0002 still stands out at $6.63 and needed the human most (3 answers). 14 answers in all, 0.5 h waited.
