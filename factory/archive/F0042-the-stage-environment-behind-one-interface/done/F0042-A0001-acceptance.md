---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 424
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-24T22:03:16.911620Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-24T22:11:09.628880Z'
  stage: acceptance
  run: 34009df0969b4abcba55dbe03c5d1daf
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-24T22:13:33.589660Z'
  stage: done
stories: [F0042-S0001, F0042-S0002, F0042-S0003, F0042-S0004, F0042-S0005, F0042-S0006, F0042-S0007, F0042-S0008, F0042-S0009, F0042-S0010, F0042-S0011, F0042-S0012, F0042-S0013, F0042-S0014, F0042-S0015, F0042-S0016]
outcome: accepted
---

# Acceptance of The stage environment behind one interface

## Recommendation

**accepted with stories.** Every scope item has its story and its code. The feature smoke test is green: one whole stage of a `container` instance on the suite's fakes, through its check container and the next stage's reset, and the real wiring from `FACTORY_STAGE_ENVIRONMENT=container` with stand-in `zfs` and `podman` scripts. `make check` is green as I found it. What is left is weight-light. First, five sentences in the guides and the operator guide that were true while the stories were built and are no longer true now that S0010 wired the container instance and the human's change 1 reached `main`. Second, the stage environment's tests: they have no test of a whole stage through `ContainerMakeCommands`, and they hold copies of shared helpers. No promise of `feature.md` is broken, and no stale sentence contradicts what an operator sees.

## 1 Scope

None. I checked each Scope item of `feature.md` against the archived stories and the code:

- `snapshots`, `containers`, `domain.containers`, the two errors and the two fakes (S0001).
- `ZfsSnapshots` (S0002) and `PodmanRuns` (S0003).
- `TakeService` and `copy_changed`, and `Git.ignored` (S0004).
- `StageEnvironment`, `InlineEnvironment` and `stage_environment_of` (S0005), and `ContainerEnvironment` with its timing line (S0007).
- `sync` in the template (S0006).
- The runtimes' `container_launch` (S0008) and `ContainerMakeCommands` (S0009).
- The six settings and the wiring (S0010) and the preflight items (S0011).
- The documents (S0012), the stall's take (S0013), the conftest login fixture (S0014), `CONTAINER_KILL_STATUSES` (S0015) and the container's fence (S0016).

All the modules exist under `src/factory/`. Both of the human's changes are on `main`: `sync` in `Makefile` and `factory/pipeline.yml` (`sync: {time_limit: 5}`), and the v1.2 bullet in `CLAUDE.md`. No story went outside the scope. Nothing of *Out of scope* was built: every layer is still there, there is no `vm/`, and no agent text changed. The Goal's own proof is on the VM (F0043's story 4), and the feature says so.

## 2 Feature smoke test

The walk-through of the feature's purpose has two parts.

Part A is one stage of a `container` instance. It uses the suite's `boundaries` fixture with `FakeSnapshots`, `FakeContainerRuns` and `ContainerMakeCommands` as the project commands. The agent writes one file inside the tester's write paths and one outside them, in the dataset's checkout. The run goes through `StageRunner`, then I write leftovers on the dataset and run the next stage's `prepare`. The script was `$TMPDIR/test_feature_smoke.py`; the write guard refused my attempt to copy it into `tests/`, rightly, and it ran from the temporary folder:

```
$ cd "$d" && PYTHONPATH=/work/checkout/tests uv run --project /work/checkout pytest test_feature_smoke.py -p conftest -s -q --no-cov -p no:cacheprovider
environment: ContainerEnvironment
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s
pushed commit is branch head: True
taken tests/test_a.py: True
left out notes.md: True
journal names notes.md: True
timing lines: ['2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s']
container commands: ['/bin/sh -c cf997134f86f48f5c2e261ac3637f6de71a7ddb0', '/bin/sh -c lint', '/bin/sh -c test']
after the check, dataset holds test_a.py: True notes.md: False
host work tree clean: True
next prepare: stray gone: True home leftover gone: True taken file present: True
.
1 passed in 0.34s
```

The output shows the sync container at the stage-start commit, then the take: the allowed file was committed and the other was left out and named in the journal. Then come one timing line, the check container for `lint` and the report `test` on the rolled-back base with only the taken file, and a clean host work tree. The next `prepare` removes everything the agent left on the dataset, in the checkout and in `home/`. Git is the only state between the stages.

Part B is the real wiring. It goes from the environment variables to the boundaries and runs the four container preflight items against stand-in `zfs` and `podman` scripts that record their calls. The settings' checkout, state and agent home were redirected into `$TMPDIR`:

```
$ uv run python -I "$d/wiring_smoke.py"
ZfsSnapshots PodmanRuns ContainerEnvironment
ClaudeCodeRuntime ContainerMakeCommands None
podman True podman version 4.9.3
zfs True zfs-2.2.2-0ubuntu9
dataset True
stage-image True
FACTORY_AGENT_USER | is set, but the container environment runs no second user
podman --version
zfs --version
zfs list -H -o name tank/factory/vm
podman image exists factory-stage:1
```

Green. One gap: no test of the suite runs Part A's combination, a whole stage whose checks go through `ContainerMakeCommands`. `tests/application/test_container_environment_take.py::test_a_whole_stage_takes_the_agents_work_from_the_dataset` runs the whole stage with the host's `MakeProjectCommands`, and `tests/adapters/test_make_commands_container.py` runs the check container alone. Story F0042-S0018 pins Part A as tests.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

Still open, from the coder, reviewer and documenter entries:

- **Stale documents.** Three are left over from the build order: `docs/project-guide/processes-and-checks.md` says that this repository's `Makefile` and `factory/pipeline.yml` "do not have it yet" (line 11) and that the wiring of `ContainerMakeCommands` "is a later story; until then nothing builds it" (line 47); `docs/project-guide/stage-environment.md` says, at line 274, that the runtimes' wiring "is a later story's". Two were noticed by S0005 and S0013 and left for S0012's sweep, which did not reach them: `docs/project-guide/costs.md` ("Rewritten after every undo", lines 14 and 17) describes only the inline environment, and so does `docs/operator-guide.md` line 833 (a stall "undoes the rest"). Line 264 of `docs/project-guide/watching.md` also describes `project_commands` for the inline instance only. Story F0042-S0017.
- **Test helpers held twice.** `FIVE_MINUTES` is in `test_container_environment.py` and `test_container_environment_take.py`. `BROKEN_FRONT_MATTER` is in `test_take.py` and `test_take_edges.py`. `_without_work_item` and `_with_broken_work_item` are in `test_undo.py` and `test_take_edges.py`. `IMAGE`/`DATASET` in `tests/entry/test_wiring_stage_environment.py` repeat `podman_support.IMAGE` and `zfs_support.DATASET`. `tests/application/test_stage_environment.py` imports private helpers (`_leave`, `_without_work_item`, `_with_broken_work_item`) from other test modules (S0004, S0005 and S0007 reviewers). Story F0042-S0018.
- **`_is_ignoring`** (`src/factory/adapters/git_cli.py:180`) takes the pattern after the second colon of `git check-ignore -v`. An ignore file whose path holds a colon would make a negated pattern read as ignoring, and the take would then drop a path it should take (S0004 coder). This is rare: the ignore files are the repository's own. Listed, no story.
- **The container branch in both runtimes.** `make duplicates` reports 11 new findings. Six are similar code in `claude_runtime` and `opencode_runtime`: the container branch of `_process_request`, the leftovers property and the result reading. The S0008 reviewer accepted them, because one shared function would need seven parameters (PLR0913). The other three new ones are vulture's reports for the fakes, which only tests use. F0044 removes the `sudo` chain, which is the other half of that branch; that is the place to fold it. Listed, no story.
- **The durations after a failed `prepare`.** A failed `prepare` keeps the durations of the last successful one (S0007). This is documented, and the stage stops at the error. No story.
- **Two once-only failures.** `make types` crashed with a mypy segfault (exit 139) once each in S0004 and S0014, and neither came back. It is a tool fault, and it is here so that a third one is counted.
- **Coverage.** `wiring.py:390` is the unreachable `SettingsInvalid` guard of `_container_adapters`, there only so that mypy can narrow the types (S0010 and S0011). Accepted as is.

## 5 The documentation as a whole

I read `README.md` (its paragraph on `FACTORY_STAGE_ENVIRONMENT`), the operator guide's *Configuration*, *The project's make targets*, *The preflight's items* and *A stall*, and the whole of `docs/project-guide/stage-environment.md`. They agree with each other and with the code on:

- the cycle and the order of the preflight items: seven inline and five container items, up to twelve for a container instance with its extras, which I counted against `machine_extras`;
- the four targets and the six settings with their faults, which Part B printed word for word;
- the podman command line.

The findings are the stale sentences under 4. None of them misleads an operator about what an instance does today: they are in the agents' guide, or they are true of `inline`, which every instance runs until F0043. The decision-log entries *One snapshot instead of many layers* and *Every container runs without rights and within limits* are there, and `write-guard.md` has *The undo*. No section is missing.

## 6 Decisions taken for the human

The decisions in `feature.md`, to accept or revisit:

1. Two environments behind `StageEnvironment`, with `snapshots` and `containers` as fields of `Boundaries`.
2. `run_agent` returns `SealedRun`.
3. The sync time limit comes from the `sync` command of the pipeline definition, 10 minutes when the definition has none.
4. `prepare(commit, branch)`.
5. The sync fetches every branch, then a checkout and a hard reset, never a detached head.
6. The agent files are copied by the sync container from `FACTORY_CLAUDE_HOME`.
7. The check container copies what differs from `HEAD`.
8. `ContainerMakeCommands` is in `make_commands`.
9. The journal sentence stays "undid".
10. `take(stage_start, work_item_path, …)`, and `mount_point` is on the interface.
11. `launch` and `run`, with a grace of 30 s.
12. The path mapping of the fake.
13. `zfs diff -FH`.
14. `FACTORY_ZFS` and `FACTORY_PODMAN` are one executable each, a wrapper for `sudo`.
15. No second user under `container`, and seven inline preflight items left out.
16. The agent's environment, `HOME=/work/home`.
17. The errors.
18. The leaves.
20. S0013.
21. S0014.
22. Exit status 255 at the limit.
23. The fence, with the network kept.

The human's answers in the story journals:

- **S0001.** Four criterion additions: a `/workspace` mount is accepted; `env` is `None` or `{}`; the bounds of a timeout's duration; a deletion survives an `advance`.
- **S0002.**
  - Rows for the failed `destroy` and `snapshot`, the malformed `R` lines and `\134`.
  - An empty `zfs list` at exit 0 is `printed nothing`.
  - The round cap: continue, with "list every remaining coverage gap in one round".
- **S0003.** `ContainerLaunch.env` is `None` for podman, and the host working directory is `/`.
- **S0004.**
  - The take never writes the dataset.
  - `copy_changed` replaces a parent that is a link with a real folder, and a deletion through a linked parent removes nothing.
- **S0005.** The test module is renamed `test_stage_environment_calls.py`.
- **S0007.** `last_line` moves to `factory.domain.checks`, shared with `make_commands`. There is no home reset under `container`.
- **S0008.** The login rows, no leftovers and no temporary folder in a container, and the `version_time_limit` rows.
- **S0009.** The check container never writes `checkout/.git` or anything outside `checkout/`.
- **S0011.** `CONTAINER_TOOLS = ("git", "uv")`, with no `tool:make`.

Defaults that agents took:

- The S0008 reviewer corrected the Description so that the runtimes branch in `_process_request` rather than in `run_launch` (PLR0913). They accepted the parallel container branch in both runtimes; see 4.
- The S0013 reviewer judged a move under the standing leave that went slightly past a pure move to be within the leave: `WorkspaceRuntime` now takes its files as an argument, and `Pace` gained `take`, whose default is the old 0.25 s.

Earlier tests changed, each with its leave:

- `tests/application/test_interfaces.py`: 18 (a), (d) and (e).
- `tests/test_wrapper_search.py`: 18 (a), (b) and (c).
- `tests/application/test_git_interface.py`: 18 (d).
- `tests/application/test_after_agent.py`: 18 (e).
- `tests/test_template_makefile.py`: 18 (f) and the standing leave.
- `tests/test_claude_files.py`: 18 (f).
- `tests/application/test_stalls.py`: 18 (g2) and the standing leave.
- `tests/application/test_container_environment_take.py`: the standing leave.
- `tests/conftest.py`: 18 (i) and the standing leave, in S0011 and S0015.
- `tests/adapters/test_opencode_runtime_launch.py`: 18 (i).
- `tests/application/test_machine_checks_runtime.py`: the standing leave.
- `tests/adapters/test_podman_runs.py`: 18 (j).

The S0006 reviewer found a rename beyond the leave (`..._says_green` → `..._saysgreen_line`). It was put back: the test has its original name at `tests/test_template_makefile.py:63`. No earlier test changed without a leave.

## 7 The slow checks

The project offers nothing beyond `make check` today except the records.

- **`make duplicates`** (a record, not a check): `duplicates: 11 new, 36 known, 2 gone`. Its new findings are the similar code in the two runtimes and the fakes that only tests use (see 4). `security/duplicates-baseline.txt` was not brought up to date during the feature; that file is the human's to accept.
- **`make test`** runs 7572 tests in 67.2 s. The slowest come from earlier features: `test_opencode_sudo_time_limit` at 11.5 s and the `test_process_session` rows at about 10.1 s, all `ROOMY_LIMIT` waits. This feature's slowest is `tests/adapters/test_podman_timeout_status.py::test_podman_s_timeout_status_at_the_limit_is_a_timed_out_run[255-at-the-limit]`, 10.0 s, a deliberate wait at the limit.
- **Disk.** Now: `/work` 967.2 GB free, 0.5 GB used. At the previous record, `disk start`: 967.7 GB free, 0.5 GB used. Used space did not grow. The 0.5 GB less free space shows on all three mounts alike, so it is the shared pool, not this checkout. No growth needs explaining.

## 8 Cost

The 16 stories cost 185 runs, 282.8 min, 1615 turns and $68.22, about $4.26 a story.

- **S0002** ($6.63, 21 runs, 31.2 min) stands out. It went through three rounds of reviews, each finding one more coverage row of the `zfs diff` reader. The human answered at the round cap with "continue", and asked that every remaining gap be listed in one round.
- **S0007** ($6.48, 30.2 min) is the core of the feature, the container cycle, and had one rework round.
- **S0008** ($5.78) had a rework round on two test findings.
- **S0012** ($1.08), the documents' sweep, and **S0014** ($1.25) were the cheapest.

Human interventions: 12 questions answered, 11 of them questions and 1 a round cap, with 0.4 h of waiting in all. S0002 needed the human most, with three answers: the intake's additions, the tester's question whether an empty `zfs list` output is a fault, and the round cap. Its journal shows why: the Interface left the reading of `zfs` output open on several sides. S0004 needed two answers, the take's write rule and the rule for linked parents. Every other story needed at most one, and S0006, S0010 and S0012 to S0016 needed none.

## Proposed stories

- **F0042-S0017**, the guides say what is true after the wiring: five stale sentences in `processes-and-checks.md`, `stage-environment.md`, `watching.md`, `costs.md` and the operator guide's stall paragraph. Documents only.
- **F0042-S0018**, a whole container stage is checked in its check container, and the stage environment's tests share their helpers. It pins this report's feature smoke test as tests, and moves the copies the reviewers named under the standing leave. Tests only.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 2 stories proposed (F0042-S0017 documents, F0042-S0018 tests). `make check` was green as I found it, and the feature smoke test is green.

   1. Scope: none. Every scope item has its story and its code. Both of the human's changes are on `main`, and nothing out of scope was built.
   2. Feature smoke test: green, in two parts.
      - One whole `container` stage on the suite's fakes ran through `StageRunner` with `ContainerMakeCommands`: sync, take (the allowed file committed, the other left out and named in the journal), one timing line, the check container for `lint` and the report `test` on the base with the taken file, a clean host, and the next `prepare` clearing the dataset.
      - The real wiring from `FACTORY_STAGE_ENVIRONMENT=container`, with stand-in `zfs` and `podman` scripts, passed the four preflight items.
      - My copy of the script into `tests/` was refused by the write guard, rightly, and it ran from `$TMPDIR`. The suite has no test of this whole combination; S0018 adds one.
   3. Mutation testing: by sweep, not run here.
   4. What the stories noticed:
      - Six stale or inline-only passages in the docs (S0017).
      - Test helpers held twice, and private helpers imported across test modules (S0018).
      - Listed without a story: `_is_ignoring` misreads an ignore-file path that holds a colon; the parallel container branch in both runtimes (11 new `make duplicates` findings, for F0044 to fold); a failed `prepare` keeps the last durations; one-off mypy segfaults.
   5. Documentation: consistent with the code apart from those passages. Three still say "later story" or "not yet" after S0010 and the human's change 1. `costs.md`, `watching.md` and the operator guide's stall paragraph describe only `inline`. None misleads an operator today.
   6. Decisions: `feature.md` decisions 1 to 23 and the 12 answers in the story journals are listed in the report. Every changed earlier test had a leave. The S0006 rename beyond the leave was put back, and the S0013 reviewer judged a near-move within the standing leave, which the human may want to confirm.
   7. Slow checks: nothing beyond `make check`. `make test` ran 7572 tests in 67.2 s; this feature's slowest test is the podman 255 time-limit row at 10.0 s. `/work` used space is unchanged at 0.5 GB; the 0.5 GB drop in free space shows on the shared pool.
   8. Cost: $68.22, 185 runs, 282.8 min. S0002 stands out ($6.63, 21 runs, review findings one row at a time) and needed the human most (3 of the 12 answers, including the one round cap). 0.4 h waited.
3. factory: done (pull request merged); cost: 1 runs, 7.8 min, 50 turns, 158627 tokens in (4264081 more from cache), 35542 out, $2.83
