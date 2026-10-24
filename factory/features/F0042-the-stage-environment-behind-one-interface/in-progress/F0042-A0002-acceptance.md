---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 427
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-24T22:52:32.850660Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-24T23:00:00.958116Z'
  stage: acceptance
  run: 8ea81bb1fa1a4e60a278ff501387b86d
stories: [F0042-S0001, F0042-S0002, F0042-S0003, F0042-S0004, F0042-S0005, F0042-S0006, F0042-S0007, F0042-S0008, F0042-S0009, F0042-S0010, F0042-S0011, F0042-S0012, F0042-S0013, F0042-S0014, F0042-S0015, F0042-S0016, F0042-S0017, F0042-S0018]
outcome: null
---

# Acceptance of The stage environment behind one interface

## Recommendation

**accepted.** Every scope item of `feature.md` has its story and its code. The two stories that the first acceptance (F0042-A0001) proposed, S0017 (the stale guide sentences) and S0018 (the whole container stage through its check container), are merged and do what they said. `make check` was green as I found it, and the feature smoke test is green: a green and a red `container` stage end to end, an `inline` stage as before, and the wiring from the environment variables with stand-in `zfs` and `podman`. What is left is test hygiene and one incomplete index in the agents' guide, both covered by one proposed story. No promise is broken, and no document misleads a user.

## 1 Scope

None. The first acceptance checked each scope item against the code (its section 1), and nothing under `src/factory/` changed since: S0017 changed five documents only, and S0018 changed only tests and two guide files (its coder's `git diff main -- src` was empty). S0017 and S0018 lie outside the Scope list of `feature.md`, which ends at S0016. Each stays within the feature's Goal and its Out of scope, and each repairs a finding of the feature's own acceptance. Nothing of *Out of scope* was built: every v1.1 layer is still there, there is no `vm/`, and no agent text changed. Both of the human's changes are on `main` (`sync` in `Makefile:27` and `factory/pipeline.yml:16`, and the v1.2 bullet in `CLAUDE.md`). The Goal's real proof is still F0043's story 4 on the VM, as `feature.md` says.

## 2 Feature smoke test

Green. It is one pytest module run from `$TMPDIR` on the suite's own fixtures (`-p conftest`), and it has four parts:

- A1: a whole `container` stage through `StageRunner`, its checks in check containers (`ContainerMakeCommands`), then the next stage's `prepare`.
- A2: the same stage with a red `lint`, run in its check container.
- A3: an `inline` stage on the same fixtures.
- B: the real `read_settings` and `build_boundaries` from `FACTORY_*` variables. Stand-in `zfs` and `podman` scripts record their calls, and the container preflight items run up to the agent run probe.

```
$ cd "$TMPDIR/smoke" && PYTHONPATH=/work/checkout/tests uv run --project /work/checkout pytest test_feature_smoke.py -p conftest -s -q --no-cov -p no:cacheprovider
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s

[A1] environment: ContainerEnvironment
[A1] decision: doing stall: None
[A1] pushed head is report commit: True
[A1] taken tests/test_a.py : True
[A1] left out notes.md : True
[A1] journal names notes.md : True
[A1] timing lines: ['stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s']
[A1] containers: ['472f67ca98d1', 'lint', 'test']
[A1] host clean: True
[A1] next prepare: stray gone True home leftover gone True taken kept True
.2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s

[A2] stall reason: check_red
[A2] containers: ['562df7b09659', 'lint']
[A2] taken file pushed with the stall: True
[A2] timing lines: 1 host clean: True
[A2] journal tail:    make: *** [Makefile:5: lint] Error 1
.
[A3] environment: InlineEnvironment
[A3] decision: doing pushed: True
[A3] timing lines: []
.
[B] ZfsSnapshots PodmanRuns ContainerEnvironment
[B] ClaudeCodeRuntime ContainerMakeCommands None
[B] item token-file False None: no token file is set
[B] item podman True podman version 4.9.3
[B] item zfs True zfs-2.2.2-0ubuntu9
[B] item dataset True 
[B] item stage-image True 
[B] zfs calls: [['--version'], ['list', '-H', '-o', 'name', 'tank/factory/vm']]
[B] podman calls: [['--version'], ['image', 'exists', 'factory-stage:1']]
[B] fault: FACTORY_AGENT_USER: is set, but the container environment runs no second user
[B] fault: FACTORY_DATASET: missing for the container environment
[B] fault: FACTORY_STAGE_ENVIRONMENT: holds docker, which is neither inline nor container
.
4 passed in 0.88s
```

(The label `decision:` prints `StageReport.next_stage`; my first run asked for a field `decision` that `StageReport` does not have, a fault of my script, not of the code.)

What the output shows:

- A1 is the feature's promise. The sync container runs at the stage-start commit. The take commits the allowed file and leaves the other out, naming it in the journal. One timing line is written. The checks `lint` and `test` run in containers on the taken result, the host's work tree stays clean, and the next `prepare` removes what the agent left in the checkout and in `home/`.
- A2: a red check in its container ends as the stall `check_red`. The taken file is pushed with the stall, the stall writes no second timing line, and the make output reaches the journal.
- A3: `inline` behaves as before and writes no `stage environment:` line, which is the operator's check on `self` (the human's change 4).
- B: the four container items pass. `token-file` fails only because my environment set no token file. The three settings faults print their operator-guide texts.

The suite now pins A1 itself (`tests/application/test_container_stage_checks.py`, S0018: 5 tests, each about 0.5 s), and A2 is pinned with the host's commands (`tests/application/test_stall_container.py`).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

New since the first acceptance:

- **S0017 documenter: `docs/decisions.md:166-168`** ("rewritten from memory after every undo, in `AfterAgent.process` and in `StallService.stall`"). This is the dated decision of 2026-10-14 and true of its time. The decision log's later entry *One snapshot instead of many layers* records that the take stands in for the undo under `container`. I checked the code: the rewrite does follow the take, at `src/factory/application/stage.py:219-221` and `src/factory/application/stalls.py:82-85`, so `costs.md`'s new bullet *Rewritten after every take* is true. Listed, no story: F0044, which removes the undo, is the place to revisit that entry.
- **S0018 coder:** the tester changed four test files that the Interface did not name (`test_stall_container.py`, `test_nested_repositories.py`, `test_podman_timeout_status.py`, `test_podman_runs_results.py`). The reviewer confirmed each was under the standing leave and that no test was renamed. Settled.
- **S0018 reviewer and tester:** two separate test functions share one check function rather than being one parametrized test, so that both test names stay. Accepted by the reviewer. No story.
- **S0018 documenter:** they did not check the other entries of the *Shared test helpers* list. I did. Seven modules at the root of `tests/` have no entry, one of them F0042's own (`stall_support.py`, S0013, whose docs criterion should have named it). And three stage-test values are still copied: `"written by the agent\n"` in 10 modules, `"tests/test_a.py"` in 6 and `"notes.md"` in 7. Six of those copies are in F0042's modules (`stall_support.py`, `test_stage_environment.py`, `test_stage_environment_calls.py`, `test_stall_container.py`), beside the shared ones in `take_support.py` and `container_support.py`. S0018 moved the copies the reviewers had named, and these were not named. Story F0042-S0019.

Still open from the first acceptance, unchanged, listed without a story:

- `_is_ignoring` misreads an ignore-file path that holds a colon (`src/factory/adapters/git_cli.py:180`).
- The parallel container branch in both runtimes: `make duplicates` still reports 11 new findings, for F0044 to fold when the `sudo` chain goes.
- A failed `prepare` keeps the durations of the last successful one (documented).
- `wiring.py:390` is the unreachable guard for mypy (it is the line coverage misses in my run too).
- The one-off mypy segfaults (S0004 and S0014). There was none since.

## 5 The documentation as a whole

S0017 made the six passages that the first acceptance found true:

- `processes-and-checks.md` now says that this repository has `sync`, and that `build_boundaries` builds `ContainerMakeCommands`.
- `stage-environment.md` says that the runtimes are wired with `PodmanRuns`.
- `watching.md` gives both `project_commands` chains.
- `costs.md` has *Rewritten after every take*.
- The operator guide's stall note says "leaves out the rest" for both environments.

A search of `README.md`, `docs/` and `docs/project-guide/` for "later story", "not yet" and "until then" finds no F0042 sentence left. The other hits are dated decision entries and operator states that are true. S0018's additions to *Wiring and tests* in `stage-environment.md` and to the helper list name the files and helpers as they are. `README.md`'s paragraph on `FACTORY_STAGE_ENVIRONMENT` agrees with what the smoke test printed. One finding: *Shared test helpers* in `docs/project-guide/README.md` promises an entry for every non-test module at the root of `tests/`, and seven are missing (see 4). The list misleads no user, but it misleads the tester it exists for, which is how copies arise. Story F0042-S0019 completes it.

## 6 Decisions taken for the human

The decisions of `feature.md` (1 to 23, numbered as there) and the human's answers in S0001 to S0016 are listed in full in the first acceptance's report (`done/F0042-A0001-acceptance.md`, section 6). The human merged that report, and nothing in them changed since. To accept or revisit, in short:

1. Two environments behind `StageEnvironment`, with `snapshots` and `containers` in `Boundaries`.
2. `run_agent` returns `SealedRun`.
3. The sync limit comes from the definition's `sync`: 10 minutes without it, 5 here.
4. `prepare(commit, branch)`.
5. Fetch every branch, then a checkout and a hard reset, never a detached head.
6. The agent files are copied in by the sync container.
7. The check container copies what differs from `HEAD`.
8. `ContainerMakeCommands` lives in `make_commands`.
9. The journal sentence stays "undid".
10. `take(stage_start, work_item_path, …)`, and `mount_point` is on the interface.
11. `launch` and `run`, with 30 s of grace.
12. The fake's path mapping.
13. `zfs diff -FH`.
14. One executable each for `FACTORY_ZFS` and `FACTORY_PODMAN`, with a wrapper for `sudo`.
15. No second user under `container`, and the inline items left out.
16. `HOME=/work/home`, without the logins.
17. The errors.
18. The leaves.
19. The number.
20. S0013, the stall's take.
21. S0014, the login out of the tests.
22. Exit status 255 at podman's limit.
23. The fence, with the network kept.

New since then:

- **S0017, the human (entry 14), option (a):** the pointer "(see *Rewritten after every take*)" at `costs.md:14` stays, and the smoke test's `Expect: 1` is read as "at least 1". This is the 13th question of the feature.
- **S0017, smoke tester:** `docs/decisions.md:166-168` is not rewritten (see 4).
- **S0018, coder:** a reviewer finding that is a copied test helper goes back to the tester under the standing leave, not to the human. The coder named the move, and the tester made exactly that move.

Earlier tests that S0018 changed, each under the standing leave to move a shared test helper. The S0018 reviewer's entry names all 17 files with their leave, and no test was renamed:

- `tests/adapters/test_podman_runs_results.py`, `tests/adapters/test_podman_timeout_status.py`
- `tests/application/test_container_environment.py`, `test_container_environment_take.py`, `test_nested_repositories.py`, `test_sealed_runs.py`, `test_sealed_runs_runner.py`, `test_stage_environment.py`, `test_stall_container.py`, `test_take.py`, `test_take_edges.py`, `test_undo.py`
- `tests/entry/test_wiring_stage_environment.py`
- `tests/container_support.py`, `tests/sealed_run_support.py`, `tests/take_support.py`, `tests/undo_support.py`

S0017 changed no test. No earlier test changed without a leave. The earlier changes of S0001 to S0016 are listed in the first report, each with its leave.

## 7 The slow checks

The project offers nothing beyond `make check` but the records, and `make mutants` is a sweep (check 3).

- **`make check`:** green as I found it. `make test` ran 7578 tests in 65.6 s, with branch coverage at 99.19 %.
- **Slowest tests (JUnit):**
  - Earlier features' `ROOMY_LIMIT` waits: `tests.adapters.test_opencode_sudo_time_limit` (two rows, 11.5 s each) and four `test_process_session` rows (10.1 s each).
  - F0042's slowest is still the podman 255 time-limit row (10.0 s, a deliberate wait).
  - S0018's new tests take 0.48 to 0.60 s each.
- **`make duplicates`:** I did not run it. S0018's coder recorded `duplicates: 11 new, 36 known, 2 gone`, the same as at the first acceptance, and nothing under `src/` changed since. `security/duplicates-baseline.txt` is still the human's to bring up to date.
- **Disk:** now `/work` 967.8 GB free and 0.0 GB used. At the previous record (`disk acceptance`, the first acceptance) it was 967.2 GB free and 0.5 GB used. Used space shrank by 0.5 GB, and free space grew by 0.6 GB on all three mounts alike. There is no growth to explain.

## 8 Cost

The 18 stories cost 202 runs, 300.1 min, 1733 turns and $72.64, about $4.04 a story. The two stories since the first acceptance:

- **S0017:** $1.06, 7 runs, 3.8 min, documents only. The cheapest of the feature.
- **S0018:** $3.35, 10 runs, 13.6 min. One rework round: the reviewer found the whole-stage fixture copied from `test_container_environment_take.py`, the coder sent it back to the tester under the standing leave, and the tester moved it into `container_support.whole_stage`.

Over the whole feature, S0002 still stands out ($6.63, 21 runs, 31.2 min): three review rounds found one more coverage row of the `zfs diff` reader each time, and the human answered the round cap. Then come S0007 ($6.48, the container cycle itself) and S0008 ($5.78, a rework round).

Human interventions: 13 questions answered (12 questions and 1 round cap), with 0.4 h of waiting in all. The one new question was S0017's smoke-test count, a fault of the proposed story's `Expect:` line that I wrote in the first acceptance: it counted the bullet's new title once and did not allow for the pointer that names it. The smoke test of S0019 counts files and modules, not occurrences in prose. S0002 needed the human most: three answers, because its Interface left the reading of `zfs` output open on several sides.

## Proposed stories

- **F0042-S0019, every shared test helper is listed and held once.** The *Shared test helpers* list gains the seven modules it is missing (one of them F0042's `stall_support.py`). The three stage-test values copied across 16 modules (six of the copies F0042's) each move to one home, under the standing leave. A guard keeps them there, as `test_shared_constants.py` does for the instance name. Tests and the guide only.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 1 story proposed (F0042-S0019: every shared test helper is listed and held once). `make check` was green as I found it: 7578 tests, coverage 99.19 %. The feature smoke test is green.

   1. Scope: none. Every scope item has its code, and nothing under `src/` changed since the first acceptance. S0017 and S0018 repair that acceptance's findings and stay inside the Goal. Nothing out of scope was built.
   2. Feature smoke test: green, 4 passed.
      - A green `container` stage: sync, take (the allowed file committed, the other left out and named in the journal), one timing line, `lint` and `test` in check containers, a clean host, and the next `prepare` clearing the dataset.
      - A red `lint` in its check container stalls `check_red`, with the taken file pushed.
      - An `inline` stage behaves as before and writes no timing line.
      - The wiring from `FACTORY_*` variables with stand-in `zfs` and `podman`: the four container items pass and the settings faults print their texts.
   3. Mutation testing: by sweep, not run here.
   4. What the stories noticed:
      - Seven non-test modules under `tests/` have no entry in the *Shared test helpers* list, one of them F0042's `stall_support.py`. Three stage-test values are copied across 16 modules, six of the copies in F0042's modules. This is S0019.
      - Listed with no story: the dated `decisions.md:166-168` "after every undo" (the code rewrites the sidecar after the take), and the items still open from the first acceptance (`_is_ignoring`, the runtimes' parallel container branch, the durations after a failed `prepare`).
   5. Documentation: the six stale passages are fixed and no "later story" sentence is left. The only gap is the incomplete helper index in `docs/project-guide/README.md`; it does not mislead a user. It goes to S0019.
   6. Decisions: `feature.md` decisions 1 to 23 and the answers of S0001 to S0016, as in the first report. New: the human's answer (a) in S0017 on the smoke test's count. S0018 changed 17 earlier test files, all under the standing leave. No test changed without a leave.
   7. Slow checks: nothing beyond `make check`. The slowest tests are earlier features' `ROOMY_LIMIT` waits at 11.5 s; F0042's slowest is the podman 255 row at 10.0 s. `make duplicates` was not rerun (S0018 recorded 11 new, unchanged). Disk used on `/work` shrank from 0.5 to 0.0 GB, so there is no growth to explain.
   8. Cost: $72.64, 202 runs, 300.1 min. S0017 cost $1.06 and S0018 $3.35, with one rework round for a copied fixture. S0002 still stands out at $6.63 and needed the human most (3 answers). 13 questions answered, 0.4 h waited. The new one came from my own `Expect:` count in the S0017 story the first acceptance proposed.
