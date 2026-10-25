---
stage: doing
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 450
comments_read: [6400499867, 6400543008, 6400918653]
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-25T17:39:14.214151Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T16:45:06.311238Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T16:45:06.317881Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T16:45:29.744802Z'
  stage: intake
  run: dd80478fad82462fbe470d924f9dc08b
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T16:45:50.059670Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-25T16:54:42.969470Z'
  stage: tests
  run: c20c8ec4912e4df2ad6882dab6d83047
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-25T16:55:03.653078Z'
  stage: doing
- number: 7
  speaker: coder
  kind: question
  at: '2026-10-25T16:58:09.605102Z'
  stage: doing
  run: 268b795735e64c40895917e16ad7d267
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-10-25T16:59:26.473260Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-25T16:59:44.386559Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-25T17:00:03.808635Z'
  stage: doing
  run: 7f3ac9a6c8a24b6c98d4c72e6112efa8
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-25T17:00:25.513950Z'
  stage: tests
- number: 12
  speaker: tester
  kind: question
  at: '2026-10-25T17:02:32.230901Z'
  stage: tests
  run: 940819d58b8f439d8ae1d7f4901b0b51
  blocked: question
- number: 13
  speaker: human
  kind: comment
  at: '2026-10-25T17:03:16.908562Z'
  stage: tests
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-25T17:03:34.962810Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-10-25T17:06:19.608558Z'
  stage: tests
  run: 601be3e5782c417ab40f16a2ca00aca0
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-25T17:06:40.281564Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-10-25T17:09:43.637355Z'
  stage: doing
  run: 88c6409104af43e39f73dbdbbd376c11
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-25T17:10:04.257330Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-10-25T17:12:23.613387Z'
  stage: review
  run: 44f3f759e2914f7dbd4c98a44b4cad12
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-25T17:12:44.141580Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-10-25T17:13:05.541717Z'
  stage: doing
  run: d100284f41fb40d08fedfaf6e0600d74
- number: 22
  speaker: factory
  kind: started
  at: '2026-10-25T17:13:25.897029Z'
  stage: tests
- number: 23
  speaker: tester
  kind: result
  at: '2026-10-25T17:16:31.387150Z'
  stage: tests
  run: 7516dd843e2e4527a062564e37c522c3
- number: 24
  speaker: factory
  kind: started
  at: '2026-10-25T17:16:52.219264Z'
  stage: doing
- number: 25
  speaker: coder
  kind: result
  at: '2026-10-25T17:19:54.729791Z'
  stage: doing
  run: 2c7da41e2f754b4785b7d97b914883ec
- number: 26
  speaker: factory
  kind: started
  at: '2026-10-25T17:20:16.016038Z'
  stage: review
- number: 27
  speaker: reviewer
  kind: result
  at: '2026-10-25T17:21:59.740354Z'
  stage: review
  run: 6d9893adf3214096b7a4de44d7e00f3f
- number: 28
  speaker: factory
  kind: started
  at: '2026-10-25T17:22:20.262979Z'
  stage: docs
- number: 29
  speaker: documenter
  kind: result
  at: '2026-10-25T17:23:06.999669Z'
  stage: docs
  run: 87b93692d8a8456a9f1b05f5b757c5be
- number: 30
  speaker: factory
  kind: started
  at: '2026-10-25T17:23:27.345649Z'
  stage: smoke-test
- number: 31
  speaker: smoke-tester
  kind: result
  at: '2026-10-25T17:25:22.159915Z'
  stage: smoke-test
  run: a8314285eaa746b7aa3e604c044ae507
- number: 32
  speaker: factory
  kind: started
  at: '2026-10-25T17:25:42.650939Z'
  stage: doing
- number: 33
  speaker: coder
  kind: question
  at: '2026-10-25T17:26:22.266905Z'
  stage: doing
  run: 6c7c083e47ba4907aed7ce7ee4c87487
  blocked: question
- number: 34
  speaker: human
  kind: comment
  at: '2026-10-25T17:38:56.365356Z'
  stage: doing
- number: 35
  speaker: factory
  kind: started
  at: '2026-10-25T17:39:14.214151Z'
  stage: doing
---

# The suite's stages run on the container fakes

## Description

The suite runs a stage, a tick or a world of ticks on the `boundaries` fixture of `tests/conftest.py` and on the world of `tests/proof_support.py`, and both describe an `inline` instance: no snapshots, no containers, the agent's scripted writes in the factory's own checkout and the undo after them. Once the inline environment goes (S0008), every stage runs through `ContainerEnvironment`, so the suite must run its stages there first, on the fakes F0042 built: `FakeSnapshots` on a folder and `FakeContainerRuns`, which play the sync container as a child process on the host. This story moves the suite: the two places that build the suite's boundaries give them a dataset under `tmp_path` with an empty base, the remote every test copies holds a `Makefile` whose `sync` succeeds, and an agent's request names the dataset's checkout as its working directory whenever the boundaries hold snapshots, so `FakeAgentRuntime` writes where a real agent writes and the take brings the result in (decision 9 of `feature.md`). The tests that pin what only the inline environment does (the undo of the agent's writes in the factory's own checkout, the undo of what a red check wrote) are replaced by what the container environment does. What stays: the inline environment itself and its setting, until S0008; `MakeProjectCommands` as the suite's project commands on the host checkout (decision 3); every test of the stage protocol, the claims, the decisions and the stalls, with its name and what it checks.

## Interface

`factory.application.task.TaskComposer` and `factory.application.preflight._probe_request` (`application`): the request's `working_directory` is `boundaries.snapshots.mount_point / "checkout"` when `boundaries.snapshots` is set, and `boundaries.checkout` otherwise.

- A real runtime in a container ignores it (the container's working directory is `/work/checkout`); the host-side process of a container call starts there, which exists after `prepare`.

Tests (the leave is decision 23 of `feature.md`, with the list its pre-check added, and answer 29 (a)):

- `tests/git_support.py`: `REMOTE_FILES` gains `"Makefile"` with a target `sync` whose recipe is `@:` (it prints nothing and succeeds). Every stage and every probe on the fixture runs `prepare`, whose sync runs `make sync`, so every `Makefile` a test pushes before one gains the same target `sync` with the recipe `@:`: `stage_makefile` of `tests/stage_run_support.py`, `PASSING_MAKEFILE` of `tests/proof_support.py`, `_makefile` of `tests/application/test_costs.py`, `tests/application/test_stage_finish.py` and `tests/application/test_stall_labels.py`, `MAKEFILE` of `tests/application/test_cost_image.py`, `tests/application/test_preflight_run.py` and `tests/application/test_tick_preflight.py`, and the pushed `Makefile` of `tests/application/test_agent_run_probe.py::test_the_probe_runs_once_for_each_image_build`, `tests/entry/test_wiring_run.py::test_build_tick_runs_one_stage_in_the_production_environment_under_its_instance` and `tests/entry/test_wiring_extras.py::test_a_tick_stops_on_a_failed_extra_and_otherwise_probes_in_the_stages_environment`. `whole_stage` of `tests/container_support.py` keeps its own `sync` after `stage_makefile()` (make takes the last recipe).
- `tests/conftest.py`: the fixture `boundaries` gives `snapshots=FakeSnapshots(<tmp_path>/workspace, <tmp_path>/workspace-base)` and `containers=FakeContainerRuns(<tmp_path>/workspace)`, the base made empty first as `container_dataset` of `tests/container_support.py` makes it (that helper may then take the fixture's fakes, under the standing leave); `project_commands` stays `MakeProjectCommands` on the host checkout.
- `tests/proof_support.py`: the world's `Boundaries(...)` the same, and `_outside_writes_undone` reads that a write outside the write paths is not in the result commit (taken out, not undone).
- `tests/application/test_stall_edges.py::test_a_red_check_stall_undoes_what_the_check_wrote` and `tests/application/test_stall_environment.py::test_a_finisher_built_without_an_environment_undoes_what_a_red_check_wrote` are deleted (a check's files stay in its container; `tests/application/test_stall_container.py` pins the take of a stall).
- `tests/application/test_after_agent.py::test_a_file_written_outside_the_write_paths_is_undone_and_reported`, `::test_undone_paths_are_named_in_a_last_paragraph_of_the_entry`, `::test_the_own_cost_record_file_is_not_named_as_undone`, `tests/application/test_costs.py::test_the_sidecar_is_written_again_after_the_undo`, `::test_an_agent_inside_its_write_paths_is_not_told_of_the_sidecar_undo`, `tests/application/test_stage_finish.py::test_the_checks_see_the_work_tree_after_the_undo`, `tests/application/test_stalls.py::test_a_stall_keeps_the_writes_inside_the_write_paths_and_drops_the_rest`, `tests/test_kill_points.py::test_a_died_run_loses_its_writes_outside_the_write_paths`: the scripted writes reach the dataset and the take leaves out what the role may not write; each passes unchanged on the fixture (the pre-check's run) and keeps its name and what it checks of the result commit, the work tree and the entry.
- `tests/application/test_task.py::test_the_request_carries_the_agent_checkout_and_guard_without_os_user`: the working directory is the dataset's checkout; `tests/application/test_stage_launch.py::test_the_runtime_receives_the_request_with_the_guard_and_the_draft_number`: the same.
- `tests/application/test_stage_environment_calls.py::test_a_stage_built_without_an_environment_runs_the_inline_one` and `tests/application/test_stall_environment.py::test_a_stall_built_without_an_environment_undoes_inline_as_before`: they replace the fixture's fakes with `None` (`dataclasses.replace`) to reach the inline environment, until S0008 deletes them.
- `tests/application/test_stage_environment.py`: its five tests replace the fixture's fakes with `None`, until S0008 deletes the module.
- What only the inline environment has, an agent's own commit or a branch it leaves in the factory's checkout, stays in the dataset on the fakes. These tests replace the fixture's fakes with `None` (`dataclasses.replace(boundaries, snapshots=None, containers=None)`) to reach the inline environment, keeping their names and assertions, until S0008: `tests/application/test_stage_run.py::test_a_run_adds_exactly_one_commit_of_its_own`, `tests/application/test_stalls.py::test_the_agents_own_commit_stays_below_the_one_stall_commit`, `tests/application/test_stalls.py::test_an_agent_that_left_the_branch_is_brought_back_and_its_other_branch_kept`, `tests/application/test_stall_edges.py::test_a_stall_after_the_agent_left_drops_its_commit_on_the_branch`, and `tests/application/test_stage_environment_calls.py::test_after_the_agent_the_environment_takes_and_its_report_closes_the_entry` (its stand-in environment takes nothing from the dataset).
- Setup only, each keeping its name and what it checks: `tests/application/test_agent_run_probe.py::test_the_probe_runs_the_coder_on_a_small_budget_with_the_question_alone` reads the dataset's checkout as the working directory; `tests/application/test_agent_run_probe.py::test_the_probe_runs_once_for_each_image_build` and `tests/application/test_agent_run_probe_project_agent.py::test_the_probe_runs_the_project_coder` bring the host's `main` to `origin/main` before the probe (the sync fetches only the host's branches); `tests/application/test_stage_provider_limit.py::test_a_stage_whose_limit_outlasts_the_ceiling_stalls_with_its_note` keeps the fixture's `agent_home` in its settings (the sync copies it).
- The pre-check ran the whole suite on a copy with these changes; nothing else failed. An earlier test not named here that fails only because the `boundaries` fixture and the world run on `FakeSnapshots` and `FakeContainerRuns`, or the remote holds a `Makefile`, may be changed so that it runs on them, keeping its name and what it checks (answer 29 (a) of `feature.md`); the tester names each such test in its entry, and the reviewer checks each against this rule.

## Acceptance criteria

1. The fixture (one test): `boundaries.snapshots` is a `FakeSnapshots` whose `mount_point` is `<tmp_path>/workspace`, `boundaries.containers` a `FakeContainerRuns`, `stage_environment_of(boundaries)` a `ContainerEnvironment`, and `reset()` on the fresh fixture raises nothing (the base exists).
2. The remote (one test): the `main` of the `remote` fixture holds a `Makefile`, and `make -s sync` in a clone of it exits 0 and prints nothing.
3. The working directory (rows of one parametrized test over `TaskComposer` and the probe's request): with the fixture's snapshots it is `<tmp_path>/workspace/checkout`; with `snapshots` `None` it is the host checkout.
4. A whole stage on the fixture (one test through `StageRunner`, a tester's stage whose scripted run writes `tests/test_new.py` and `src/forbidden.py` and decides `doing`, the checks' `Makefile` pushed with `sync`, `lint` and `check` targets that pass): the result commit on the branch holds `tests/test_new.py` and not `src/forbidden.py`; the entry's paragraph that names what was left out, before the checks' lines, names `src/forbidden.py`; the factory log holds one line whose text after its timestamp begins `stage environment: reset`; the host checkout's work tree after the stage equals the result commit.
5. A died run (one test through `StageRunner`, a scripted run that writes `src/forbidden.py` and ends `died`): the stall commit holds no `src/forbidden.py` and the stall entry is the factory's.
6. The world (one test over `tests/proof_support.py`): a story walked from intake to approval in the world reaches approval with every stage's timing line in the factory log, and no stage's result commit holds a path its role may not write.
7. `make check` stays green.
8. docs: `docs/project-guide/README.md`, *Shared test helpers*: the `boundaries` fixture describes a `container` instance on `FakeSnapshots` and `FakeContainerRuns`, the remote's `Makefile` with `sync`, and the `container_support.py` line names what it still offers; `docs/project-guide/stage-environment.md`, *The fakes*: the suite's stages run on them, and the request's working directory is the dataset's checkout; *Wiring and tests*: the `boundaries` fixture holds the fakes and `container_dataset` takes them from it; `docs/project-guide/README.md`, *Kill points*: the stall condition says that writes outside the write paths are left out, not undone. `docs/decisions.md`: none (decision 9 of `feature.md` is a test fixture, the entry "One snapshot instead of many layers" covers it). `README.md`, `docs/operator-guide.md`: none.

## Smoke test

```bash
uv run pytest tests/application/test_stage_run.py tests/application/test_after_agent.py tests/application/test_stalls.py tests/test_kill_points.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

```bash
grep -c '"Makefile"' tests/git_support.py; grep -c 'FakeSnapshots(' tests/conftest.py
```
Expect: two lines: `1`; `1`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete places (`factory.application.task.StageTask`, `factory.application.preflight._probe_request`) with the rule for the working directory (dataset checkout when snapshots are set, host checkout otherwise). It also names the exact test files, helpers and fixtures to change, and the pre-check's list (decision 36 of `feature.md`) is in it.
   Criteria: each is testable by one test or one parametrized test. Criterion 1 is the fixture, 2 the remote's `Makefile` and its silent `sync`, 3 the working directory on both sides (snapshots set and `None`), 4 a whole stage, 5 a died run, 6 the world. 7 and 8 are the closing criteria. The Interface's only behaviour comment, "a real runtime ignores the working directory", changes nothing observable. Every rule has both sides: the working directory has two rows, and the stage with a forbidden path has the kept `tests/test_new.py` and the left-out `src/forbidden.py`.
   Smoke test: both commands are runnable. pytest's `addopts` already sets `-q` and the command passes none, so the `N passed in` summary line the first `Expect:` greps for is printed. The second command's two counts are checkable.
   Architecture: the change is in tests, fixtures and the request's working directory, in `application`. It uses the F0042 fakes and adds no interface, no layer break, and no new dependency.
   Scope: it matches S0007 in `feature.md`. The inline environment stays until S0008, and the leaves are those of decision 23, answer 29 (a) and decision 36. Nothing is in "Out of scope".
4. factory: started tests as self.
5. tester: Tests for the criteria (they fail until the request's `working_directory` is the dataset's checkout):
   criterion 1: tests/test_suite_fixtures.py::test_the_boundaries_fixture_runs_its_stages_in_containers_on_the_fakes
   criterion 2: tests/test_suite_fixtures.py::test_the_remotes_makefile_has_a_silent_sync_that_succeeds
   criterion 3: tests/application/test_stage_on_container_fakes.py::test_the_request_works_in_the_datasets_checkout_when_the_boundaries_hold_snapshots (four rows: stage or probe, with snapshots or without)
   criterion 4: tests/application/test_stage_on_container_fakes.py::test_a_whole_stage_on_the_fixture_takes_the_allowed_writes_and_leaves_out_the_rest
   criterion 5: tests/application/test_stage_on_container_fakes.py::test_a_died_run_on_the_fixture_stalls_without_its_writes_outside_the_write_paths
   criterion 6: tests/test_suite_fixtures.py::test_a_story_walks_to_approval_in_the_world_on_the_container_fakes. Every stage's run also writes `forbidden.txt` at the root, which no role may write; the test checks that the branch head at approval does not hold it.
   criteria 7, 8: no test (`make check`, docs).

   Interpretation, for the reviewer: the Interface names `factory.application.task.StageTask`, which does not exist. `TaskComposer` in `task.py` composes the stage's request, so the stage row of criterion 3 calls `TaskComposer.compose`.

   Files created: tests/test_suite_fixtures.py, tests/application/test_stage_on_container_fakes.py.

   Shared setup changed as the Interface says:
   - tests/git_support.py: `SYNC_TARGET`, and `REMOTE_FILES` gains `Makefile`.
   - tests/conftest.py: `boundaries` gets `FakeSnapshots` and `FakeContainerRuns` through the new helper `fake_dataset`.
   - tests/container_support.py: `fake_dataset`; `container_dataset` now takes the fixture's fakes and removes the base for `with_base=False`; new helper `inline_boundaries`.
   - tests/proof_support.py: the world gets `fake_dataset(root)`. `_outside_writes_undone` reads only the stall commit. `PASSING_MAKEFILE` gains `sync`.
   - tests/stage_run_support.py: `stage_makefile` gains `sync`.
   - The other Makefiles the Interface lists gained `sync:\n\t@:`.
   - Deleted: the red-check undo tests in test_stall_edges.py and test_stall_environment.py.
   - `inline_boundaries` added to the tests the Interface lists: test_stage_run, test_stalls (×2), test_stall_edges, test_stall_environment, and test_stage_environment_calls (×2). In test_stage_environment.py it is in five tests; `test_run_agent_returns_the_runs_result` stays on the fixture because its container rows use `container_dataset`, and its inline row builds `InlineEnvironment` directly.
   - test_task and test_stage_launch: the working directory is the dataset's checkout.
   - test_agent_run_probe and test_agent_run_probe_project_agent: the probe test reads the dataset's checkout, and the two others check out `main` at `origin/main` before the probe.
   - test_stage_provider_limit: keeps the fixture's `agent_home` in its settings.

   Earlier tests changed under answer 29 (a), names and checks unchanged:
   - tests/application/test_cost_image.py `_launch`: puts the fixture's `agent_home` into the settings. The sync copies the agent home, and `_settings` named the default `/home/agent`, so the sync failed with "cp: cannot open '/home/agent/.claude/...': Permission denied". This also fixes tests/application/test_cost_instance.py, which uses `_launch`.
   - tests/test_kill_points.py (via `fake_dataset`): `restart` built the dataset again and failed with "FileExistsError: ... workspace-base". `fake_dataset` now keeps a base an earlier start of the same instance left.

   The one `make test` run came before three fixes: `exist_ok` for the base, the `_launch` settings, and dropping `inline_boundaries` from `test_run_agent_returns_the_runs_result`. In that run the new tests failed with wrong results (the working directory was still the host checkout). The named setup tests (test_task, test_stage_launch, the probe test) and the take tests the Interface lists (test_after_agent, test_costs, test_stage_finish, test_stalls) failed too. Three failures I could not explain without running again:
   - tests/application/test_after_agent.py::test_a_body_edit_is_kept_only_where_the_role_may_write_the_work_item[tests-False]
   - three tests in tests/test_fault_paths.py: test_docs_finding_tick_killed_after_move_back_push_counts_round_once_and_next_stage_starts, test_intake_edge_case_question_killed_between_commit_and_push_reruns_intake_and_posts_once, test_intake_question_tick_killed_during_intake_run_reruns_free_and_asks_once
   I expect them to go green with the working-directory change. The fault-path tests build the world, so the base `FileExistsError` may also be the cause. If any stays red after the coder's change, it is an answer 29 (a) case for the tester, and the coder should not edit it.

   Modules the test runner could not import: none; every module imported.

   `make lint`: green.

   `lint`: lint: green (0.3 s)
   `test`: FAILED tests/application/test_after_agent.py::test_undone_paths_are_named_in_a_last_paragraph_of_the_entry[two-undone] - AssertionError: assert 'tests written.' == 'tests writte...md, src/b.py.'
6. factory: started doing as self.
7. coder: Stopped with the code done and two of the tester's new tests red. I believe both tests are wrong, not the code, and the coder may not change tests.

   Built: `src/factory/application/take.py` has a new `agent_working_directory(boundaries)`. It returns `snapshots.mount_point / MOUNTED_CHECKOUT` when `boundaries.snapshots` is set and `boundaries.checkout` otherwise. `TaskComposer.compose` (`src/factory/application/task.py`) and `_probe_request` (`src/factory/application/preflight.py`) both call it. I put it beside `MOUNTED_CHECKOUT`, which the take and `MakeProjectCommands` already use for the dataset's checkout. The alternative I rejected was to compute it in each of the two places, which would make two copies. `make lint`, `make types` and `make layers` are green. In `make test`, every test passes except these two:

   1. `tests/test_suite_fixtures.py::test_a_story_walks_to_approval_in_the_world_on_the_container_fakes` fails with `AssertionError: F0001-S0001 did not reach approval in 20 ticks`. I traced it tick by tick. Intake passes, then the tests stage stalls twice with `check_red` and blocks on `attempts_cap`. The cause: the remote's `Makefile` from `REMOTE_FILES` holds only `sync`, so the tests stage's `make lint` has no target. The world's other walks pass because `drive` in `tests/proof_support.py` pushes `PASSING_MAKEFILE` first, and this test never does. No code change makes `make lint` pass without a `lint` target.
      Options: (a) the test pushes `PASSING_MAKEFILE` to `main` (`world.human.push_file`) before `start_story`, as `drive` does; (b) the test walks with `drive`. I would choose (a): it keeps the test's own loop and its `forbidden.txt` check.

   2. `tests/application/test_stage_on_container_fakes.py::test_a_whole_stage_on_the_fixture_takes_the_allowed_writes_and_leaves_out_the_rest` fails at `tests/application/test_stage_on_container_fakes.py:113`: `E AssertionError: assert 'src/forbidden.py' in '`lint`: lint done\n`test`: test done'`. The take works: the commit holds `tests/test_new.py` and not `src/forbidden.py`. But the finisher has always appended the checks' command lines as the entry's last paragraph (`_with_command_lines` in `src/factory/application/stage.py`), after the paragraph that names the paths left out. On inline as on the fakes, the paragraph that names `src/forbidden.py` is the next-to-last one.
      Options: (a) the test looks for `src/forbidden.py` in the paragraph before the checks' lines, or in any paragraph of the entry; (b) the code moves the left-out paragraph after the checks' lines, which would change the entry layout of every stage, beyond this story. I would choose (a). Criterion 4's "closing paragraph" would then read "the paragraph that names what was left out, before the checks' lines".

   Once the answer is in, I would end with `tests` and name these two changes.

   Noticed, not touched: the tester's entry says the Interface's `factory.application.task.StageTask` does not exist; `TaskComposer` is the class that composes the request, and I changed that one. Step 4's refactor has not happened yet; the diff is only these three files.
8. 2026-10-25 human: Both (a), as you propose; end with `tests` and name the two changes:
   1. `tests/test_suite_fixtures.py::test_a_story_walks_to_approval_in_the_world_on_the_container_fakes` pushes `PASSING_MAKEFILE` to `main` (`world.human.push_file`) before `start_story`, as `drive` does, and keeps its own loop and its `forbidden.txt` check.
   2. `tests/application/test_stage_on_container_fakes.py::test_a_whole_stage_on_the_fixture_takes_the_allowed_writes_and_leaves_out_the_rest` looks for `src/forbidden.py` in the paragraph that names what was left out, before the checks' command lines. Criterion 4's "closing paragraph" reads "the paragraph that names what was left out, before the checks' lines". The entry layout stays as it is.
   Both are new tests of this story, under the leave of answer 29 (a) and decision 36.
9. factory: started doing as self.
10. coder: The human's answer (entry 8) calls for two test changes. I changed no code in this run. The code from the last doing run is committed and stays as it is: `agent_working_directory` in `src/factory/application/take.py`, called from `src/factory/application/task.py` and `src/factory/application/preflight.py`.

    Tester, please make exactly these two changes:
    1. `tests/test_suite_fixtures.py::test_a_story_walks_to_approval_in_the_world_on_the_container_fakes`: push `PASSING_MAKEFILE` to `main` with `world.human.push_file` before `start_story`, as `drive` does. Keep the test's own loop and its `forbidden.txt` check.
    2. `tests/application/test_stage_on_container_fakes.py::test_a_whole_stage_on_the_fixture_takes_the_allowed_writes_and_leaves_out_the_rest`: look for `src/forbidden.py` in the paragraph that names what was left out, which comes before the checks' command lines, instead of in the entry's last paragraph. The entry layout stays as it is.

    The answer also rewords criterion 4: "closing paragraph" now means "the paragraph that names what was left out, before the checks' lines". The work item is outside the coder's write paths, so I left `## Description` as it is.

    Still open: step 4's refactor of my diff happens when the work item comes back to doing, together with the `make check` run that needs the two changed tests green.
11. factory: started tests as self.
12. tester: I made both changes the human approved in entry 8, and one of the two tests is still red, for a reason the approved change does not cover.

    Changes made, exactly as approved:
    1. `tests/test_suite_fixtures.py::test_a_story_walks_to_approval_in_the_world_on_the_container_fakes` now pushes `PASSING_MAKEFILE` to `main` with `world.human.push_file` before `start_story`. `PASSING_MAKEFILE` is added to the import from `proof_support`. The test's own loop and its `forbidden.txt` check are unchanged. The push is never empty, because the remote's `Makefile` holds only `SYNC_TARGET`.
    2. `tests/application/test_stage_on_container_fakes.py::test_a_whole_stage_on_the_fixture_takes_the_allowed_writes_and_leaves_out_the_rest` now looks for `src/forbidden.py` in the paragraph before the checks' command lines (`split("\n\n")[-2]`). Before, it looked in the last paragraph. The checks' lines form a single paragraph.

    `make test` (one run): every test passes except
    `FAILED tests/test_suite_fixtures.py::test_a_story_walks_to_approval_in_the_world_on_the_container_fakes - AssertionError: assert ['intake', 't...ke-test', ...] == ['intake', 't... 'smoke-test']`
    I ran that one test alone with `--tb=short` to see the full message:
    `tests/test_suite_fixtures.py:78`
    `E   AssertionError: ... Left contains one more item: 'approval'`
    With the Makefile in place, the walk now reaches the end. The state's `stage` becomes `approval` one tick before `handed_over` is `approval`, so the loop records `approval` as a stage it walked and queues one more run for it. The fault is in the test's loop, not in the code. `make lint`: green.

    Question: how should the loop treat the tick where the stage is already `approval` but the handover has not happened yet?
    (a) The loop does not record `approval` in `walked`: `if stage not in walked and stage != "approval":`. The expected list stays `intake … smoke-test`, and the test still waits for `handed_over == "approval"`.
    (b) The expected list gains `"approval"` at the end.
    I would choose (a). The criterion names the stages walked to approval, and approval is where the walk ends, not a stage the agent runs. I tried (a) on that single test and it passed. I then restored the file, so the working tree holds only the two approved changes.

    Files changed: tests/test_suite_fixtures.py, tests/application/test_stage_on_container_fakes.py.
13. 2026-10-25 human: (a). The loop does not record `approval` in `walked` (`if stage not in walked and stage != "approval":`); the expected list stays `intake … smoke-test`, and the test still waits for `handed_over == "approval"`. Approval is where the walk ends, not a stage an agent runs.
14. factory: started tests as self.
15. tester: I made the one test change the human approved in entry 13, answer (a).

    Change: in `tests/test_suite_fixtures.py::test_a_story_walks_to_approval_in_the_world_on_the_container_fakes`, the loop's guard is now `if stage not in walked and stage != "approval":`. This means `approval` is never recorded as a walked stage. The expected list is still `intake … smoke-test`, and the loop still ends only when `handed_over == "approval"`. Nothing else changed in the test. The two changes from entry 12 (the `PASSING_MAKEFILE` push, and the `split("\n\n")[-2]` paragraph in `tests/application/test_stage_on_container_fakes.py`) were already committed and stay as they are.

    Files changed: tests/test_suite_fixtures.py.

    `make test` (one run): test: green (69.4 s), coverage 99.55 %. `make lint`: green.

    Modules the test runner could not import: none.

    Still open: the coder's step-4 refactor and the full `make check` run (entry 10).

    `lint`: lint: green (0.3 s)
    `test`: test: green (72.9 s)
16. factory: started doing as self.
17. coder: The tester made the three test changes the human approved (entries 8 and 13). `make check` is green with them: test: green (70.7 s), coverage 99.55 %, check: green. No code changed in this run.

    Built (in the earlier doing run, committed): `agent_working_directory(boundaries)` in `src/factory/application/take.py`. It returns `boundaries.snapshots.mount_point / MOUNTED_CHECKOUT` when the boundaries hold snapshots, and `boundaries.checkout` otherwise. `TaskComposer.compose` (`src/factory/application/task.py`) and `_probe_request` (`src/factory/application/preflight.py`) both use it for the request's `working_directory`.

    Main choice: one helper beside `MOUNTED_CHECKOUT`, which the take and `MakeProjectCommands` already use for the dataset's checkout. I rejected writing the condition separately in the task and in the probe, because that would leave two copies of the same rule.

    Refactor (step 4): I read the diff (three files, about ten lines). It has no duplication or dead code and nothing unclear in its names, so I changed nothing.

    What the journal changed: criterion 4's "closing paragraph" now means "the paragraph that names what was left out, before the checks' lines" (entry 8). In the world test, approval is where the walk ends, not a walked stage (entry 13). The work item is outside the coder's write paths, so `## Description` still has the old wording.

    Noticed, not touched: the Interface names `factory.application.task.StageTask`, which does not exist. The class that composes the request is `TaskComposer`, and that is the one I changed.

    `check`: check: green
    `duplicates`: duplicates: 7 new, 34 known, 4 gone
18. factory: started review as self.
19. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (3 files under `src/`, 26 under `tests/`) against the work item. Groups 1 and 2 pass, group 3 fails.

    Group 1: every criterion has a test that checks what the criterion says. The Interface's one rule, the working directory, is tested on both sides as four rows of one parametrized test. Entry 17 records `check: green`. For criterion 4, the clean `status()` together with the kept and missing files pins that the work tree equals the result commit. For criterion 6, `forbidden.txt` is written at every stage, and no take deletes a path its role may not write, so checking the head at approval covers every stage's result commit.

    Group 2: `agent_working_directory` in `factory.application.take` is used by `task.py` and `preflight.py`. It stays inside `application` and adds no interface or tool.

    Findings:
    1. `tests/test_suite_fixtures.py:3`: `import subprocess  # noqa: S404` adds a marker that silences a check. `CLAUDE.md` allows `# noqa: S404` only on the import in `src/factory/adapters/process.py` ("and nothing else"), and no reason is given beside it. The other tests import `subprocess` without a marker (`tests/test_layers.py:4`, `tests/domain/test_journal.py:4`). Fix: drop the marker. The `# noqa: S603, S607` at line 50 is already covered by the per-file ignore for `tests/**`, so it can go too.
    2. `tests/application/test_cost_image.py`, `_launch`: the two lines added for `agent_home` sit above the function's docstring. The docstring is now a bare string expression, not a docstring. Fix: move the comment and the two lines below the docstring.
    3. `tests/application/test_stall_edges.py:29` and `tests/application/test_stall_environment.py:55`: `WRITTEN = "written-by-lint.txt"` is now dead. Only the two red-check tests this story deleted used it. Fix: delete both constants together with the tests.

    Earlier tests (status M):
    - tests/application/test_agent_run_probe.py: the human's leave, named in the Interface (decision 23, answer 29 (a)).
    - tests/application/test_agent_run_probe_project_agent.py: the human's leave, named in the Interface.
    - tests/application/test_cost_image.py: the human's leave, `MAKEFILE` named in the Interface. The `_launch` settings fall under answer 29 (a) (tester's entry 5). Moving the docstring goes beyond that leave (finding 2).
    - tests/application/test_costs.py: the human's leave, `_makefile` named in the Interface.
    - tests/application/test_preflight_run.py: the human's leave, `MAKEFILE` named in the Interface.
    - tests/application/test_stage_environment.py: the human's leave, the Interface's five tests.
    - tests/application/test_stage_environment_calls.py: the human's leave, both tests named in the Interface.
    - tests/application/test_stage_finish.py: the human's leave, `_makefile` named in the Interface.
    - tests/application/test_stage_launch.py: the human's leave, named in the Interface.
    - tests/application/test_stage_provider_limit.py: the human's leave, named in the Interface.
    - tests/application/test_stage_run.py: the human's leave, named in the Interface.
    - tests/application/test_stall_edges.py: the human's leave, the deletion and `inline_boundaries` named in the Interface. The leftover constant is finding 3.
    - tests/application/test_stall_environment.py: the human's leave, the deletion and `inline_boundaries` named in the Interface. The leftover constant is finding 3.
    - tests/application/test_stall_labels.py: the human's leave, `_makefile` named in the Interface.
    - tests/application/test_stalls.py: the human's leave, both tests named in the Interface.
    - tests/application/test_task.py: the human's leave, named in the Interface.
    - tests/application/test_tick_preflight.py: the human's leave, `MAKEFILE` named in the Interface.
    - tests/conftest.py: the human's leave, the `boundaries` fixture named in the Interface.
    - tests/container_support.py: the human's leave (the Interface lets `container_dataset` take the fixture's fakes) and the standing leave for the shared helpers `fake_dataset` and `inline_boundaries`.
    - tests/entry/test_wiring_extras.py: the human's leave, named in the Interface.
    - tests/entry/test_wiring_run.py: the human's leave, named in the Interface.
    - tests/git_support.py: the human's leave, `REMOTE_FILES` named in the Interface.
    - tests/proof_support.py: the human's leave, the world, `PASSING_MAKEFILE` and `_outside_writes_undone` named in the Interface.
    - tests/stage_run_support.py: the human's leave, `stage_makefile` named in the Interface.
20. factory: started doing as self.
21. coder: All three of the reviewer's findings in entry 19 are in test files, so I changed no code in this run. The code from the earlier doing run stays as committed: `agent_working_directory` in `src/factory/application/take.py`, which `src/factory/application/task.py` and `src/factory/application/preflight.py` call.

    Tester, please make exactly these three changes. I checked that each one is still in the working tree as entry 19 describes it.
    1. `tests/test_suite_fixtures.py`: drop `# noqa: S404` from the `import subprocess` on line 3. Also drop `# noqa: S603, S607  (fixed command, no input)` from the `subprocess.run(` call on line 48, since the per-file ignore for `tests/**` already covers it. Then run `make lint` to confirm both lines pass without the markers.
    2. `tests/application/test_cost_image.py`, `_launch`: move the comment and the two lines that put the fixture's `agent_home` into the settings (lines 73–75) below the function's docstring. The docstring is line 76 and should again be the first statement. This fixes your own addition, so it stays within the leave of answer 29 (a).
    3. `tests/application/test_stall_edges.py:29` and `tests/application/test_stall_environment.py:55`: delete the constant `WRITTEN = "written-by-lint.txt"`. Its only users were the red-check tests this story deleted.

    What the journal changed: nothing new since entry 17. Criterion 4's "closing paragraph" reading (entry 8) and the walk ending at approval (entry 13) still stand. The work item is outside my write paths, so `## Description` keeps the old wording.

    Noticed, not touched: the Interface names `factory.application.task.StageTask`, which does not exist. `TaskComposer` is the class that composes the request.
22. factory: started tests as self.
23. tester: I made the three test changes the coder listed in entry 21 to fix the reviewer's findings in entry 19. I changed nothing else.

    1. `tests/test_suite_fixtures.py`: I took `# noqa: S404` off `import subprocess` and `# noqa: S603, S607  (fixed command, no input)` off the `subprocess.run(` call. CLAUDE.md allows those markers only in `src/factory/adapters/process.py`, and the per-file ignore for `tests/**` already covers this file. `make lint` passes without them.
    2. `tests/application/test_cost_image.py`, `_launch`: the docstring is the first statement again. The comment and the two lines that put the fixture's `agent_home` into the settings now come right after it. This fixes my own addition, so it stays within answer 29 (a).
    3. `tests/application/test_stall_edges.py` and `tests/application/test_stall_environment.py`: I deleted the unused constant `WRITTEN = "written-by-lint.txt"`. Only the two red-check tests this story deleted used it.

    Each test keeps its name and checks the same thing. The criterion → test mapping is unchanged from the earlier tests entries.

    Files changed: tests/test_suite_fixtures.py, tests/application/test_cost_image.py, tests/application/test_stall_edges.py, tests/application/test_stall_environment.py. Files created: none.

    `make lint`: lint: green (0.7 s). `make test` (one run): test: green (72.5 s), coverage 99.55 %.

    Modules the test runner could not import: none.

    Still open: the coder's `make check` run on these changes.

    `lint`: lint: green (0.2 s)
    `test`: test: green (74.1 s)
24. factory: started doing as self.
25. coder: Round 1. The reviewer's three findings (entry 19) were all in test files, and the tester fixed them in entry 23. The fixes: the `noqa` markers are gone from `tests/test_suite_fixtures.py`, the `_launch` docstring in `tests/application/test_cost_image.py` is the first statement again, and the dead `WRITTEN` constants are deleted from `tests/application/test_stall_edges.py` and `tests/application/test_stall_environment.py`. I changed no code in this run. With those changes in place, `make check` is green: test: green (71.1 s), coverage 99.55 %, check: green.

    Built (in an earlier doing run, already committed): `agent_working_directory(boundaries)` in `src/factory/application/take.py`. It returns `boundaries.snapshots.mount_point / MOUNTED_CHECKOUT` when the boundaries hold snapshots, and `boundaries.checkout` otherwise. `TaskComposer.compose` (`src/factory/application/task.py`) and `_probe_request` (`src/factory/application/preflight.py`) use it for the request's `working_directory`.

    Main choice: one helper beside `MOUNTED_CHECKOUT`, which the take and `MakeProjectCommands` already use. I rejected writing the condition separately in the task and in the probe, because that would leave two copies of one rule.

    Refactor: entry 17 already covered it, and the source diff has not changed since. Nothing to change.

    What the journal changed: criterion 4's "closing paragraph" now means "the paragraph that names what was left out, before the checks' lines" (entry 8). In the world test, approval is where the walk ends, not a walked stage (entry 13). The work item is outside my write paths, so `## Description` keeps the old wording.

    Noticed, not touched: the Interface names `factory.application.task.StageTask`, which does not exist. `TaskComposer` is the class that composes the request.

    `check`: check: green
    `duplicates`: duplicates: 7 new, 34 known, 4 gone
26. factory: started review as self.
27. reviewer: Round 1. I reviewed `git diff main...HEAD -- . ':!factory'` (3 files under `src/`, 26 under `tests/`) against the work item.

    What I checked:
    - The three findings of entry 19 are fixed. `tests/test_suite_fixtures.py` has no `noqa` markers. The docstring of `_launch` in `tests/application/test_cost_image.py` is its first statement again. Both `WRITTEN` constants are gone, and the import of `stage_makefile` that only they used is gone too.
    - Group 1: criteria 1 to 6 each have a test that checks what the criterion says. The Interface's one rule (the working directory) is covered by four rows of one parametrized test. Entry 25 records `check: green`. The Interface states no limits.
    - Group 2: `agent_working_directory` sits in `factory.application.take` beside `MOUNTED_CHECKOUT`, and `task.py` and `preflight.py` use it. No layer is crossed and no tool is called. No other copy of the rule exists in `src/factory`: `make_commands.py` and the take use `mount_point / MOUNTED_CHECKOUT` with their own snapshots, not the boundaries.
    - Group 3: no secrets, no silencing markers, no string-built shell commands.
    - Group 4: I ran `make duplicates` and got `7 new, 34 known, 4 gone`. None of the new findings is in a file this diff changes (they are in `claude_runtime`/`opencode_runtime`, `podman_runs`/`zfs_snapshots` and the fakes' dead-code entries).
    - Group 5: the `## Description` matches what was built. The docs criterion names what the documenter must write.

    no findings

    description corrected: Interface `factory.application.task.StageTask` -> `factory.application.task.TaskComposer`. No `StageTask` exists; `TaskComposer` in `task.py` composes the request, and the tester and coder noted this in entries 5, 7, 17, 21 and 25.
    description corrected: criterion 3 "over `StageTask` and the probe's request" -> "over `TaskComposer` and the probe's request".
    description corrected: criterion 4 "the entry's closing paragraph names `src/forbidden.py`" -> "the entry's paragraph that names what was left out, before the checks' lines, names `src/forbidden.py`" (the human's answer, entry 8).

    Earlier tests (status M):
    - tests/application/test_agent_run_probe.py: the human's leave, named in the Interface (decision 23, answer 29 (a)).
    - tests/application/test_agent_run_probe_project_agent.py: the human's leave, named in the Interface.
    - tests/application/test_cost_image.py: the human's leave (`MAKEFILE` is named in the Interface); the `agent_home` lines in `_launch` fall under answer 29 (a), as the tester's entry 5 names them.
    - tests/application/test_costs.py: the human's leave, `_makefile` named in the Interface.
    - tests/application/test_preflight_run.py: the human's leave, `MAKEFILE` named in the Interface.
    - tests/application/test_stage_environment.py: the human's leave, the Interface's five tests.
    - tests/application/test_stage_environment_calls.py: the human's leave, both tests named in the Interface.
    - tests/application/test_stage_finish.py: the human's leave, `_makefile` named in the Interface.
    - tests/application/test_stage_launch.py: the human's leave, named in the Interface.
    - tests/application/test_stage_provider_limit.py: the human's leave, named in the Interface.
    - tests/application/test_stage_run.py: the human's leave, named in the Interface.
    - tests/application/test_stall_edges.py: the human's leave (the deletion and `inline_boundaries` are named in the Interface); the dead constant and import are removed with the deleted test.
    - tests/application/test_stall_environment.py: the human's leave (the deletion and `inline_boundaries` are named in the Interface); the dead constant is removed with the deleted test.
    - tests/application/test_stall_labels.py: the human's leave, `_makefile` named in the Interface.
    - tests/application/test_stalls.py: the human's leave, both tests named in the Interface.
    - tests/application/test_task.py: the human's leave, named in the Interface.
    - tests/application/test_tick_preflight.py: the human's leave, `MAKEFILE` named in the Interface.
    - tests/conftest.py: the human's leave, the `boundaries` fixture named in the Interface.
    - tests/container_support.py: the human's leave (`container_dataset` takes the fixture's fakes), and the standing leave for the shared helpers `fake_dataset` and `inline_boundaries`.
    - tests/entry/test_wiring_extras.py: the human's leave, named in the Interface.
    - tests/entry/test_wiring_run.py: the human's leave, named in the Interface.
    - tests/git_support.py: the human's leave, `REMOTE_FILES` named in the Interface.
    - tests/proof_support.py: the human's leave (the world, `PASSING_MAKEFILE` and `_outside_writes_undone` are named in the Interface).
    - tests/stage_run_support.py: the human's leave, `stage_makefile` named in the Interface.

    Notes:
    - tests/test_suite_fixtures.py:64: the test writes the literal `"stage environment: reset"`, while `tests/application/test_stage_on_container_fakes.py` keeps the same text as the constant `RESET_PREFIX`. One shared constant would serve both.
    - tests/test_suite_fixtures.py:40: the walk's loop repeats most of `drive` in `tests/proof_support.py`. It differs only in recording the walked stages and in the extra `forbidden.txt` write.
28. factory: started docs as self.
29. documenter: Round 1, docs. I read the story, the diff (3 files under `src/`, 26 under `tests/`) and the project guide. No findings: the code matches the Interface, with one exception (the second item under "Stale text I noticed"). I changed only documents, so I did not run `make check`; the factory's check after this stage decides. I ran no examples, because I wrote none.

    Files changed:
    - `docs/project-guide/README.md`, *Shared test helpers*, `conftest.py` line:
      - `remote` now says `main` holds a `Makefile` whose `sync` is `@:`.
      - `boundaries` now describes a `container` instance on `FakeSnapshots` and `FakeContainerRuns` over `<tmp_path>/workspace` with an empty base. It says the project commands stay `MakeProjectCommands` on the host checkout.
    - `docs/project-guide/README.md`, `container_support.py` line:
      - It now lists `fake_dataset`, `inline_boundaries` and the new meaning of `container_dataset` (it takes the fixture's fakes).
    - `docs/project-guide/README.md`, `git_support.py` line:
      - It now says `REMOTE_FILES` holds a `Makefile` with `sync`, and that a test pushing its own `Makefile` gives it the same target.
    - `docs/project-guide/README.md`, *Kill points*:
      - The stall condition "writes outside the write paths undone" now says they are left out of the result commit: the take does not copy them, and nothing is undone.
    - `docs/project-guide/stage-environment.md`, *The fakes*:
      - A new paragraph says the suite's stages run on the fakes. It explains that the request's working directory is the dataset's checkout when snapshots are set (`agent_working_directory`, used by `TaskComposer` and the probe). It also says a real runtime in a container ignores the field.
    - `docs/project-guide/stage-environment.md`, *Wiring and tests*:
      - It now says the `boundaries` fixture holds the fakes and `container_dataset` takes them from it.

    Cross-read and found current:
    - `docs/decisions.md`, `docs/operator-guide.md` and the top-level `README.md`. The criterion says none for these, and nothing in the diff touches them.
    - `docs/project-guide/write-guard.md`. It describes the inline undo, which still exists until S0008.

    Stale text I noticed and did not touch:
    - `docs/project-guide/stages.md:245` and `:291`, and `docs/project-guide/costs.md:17`, describe the undo and the take as inline-first. They are still true for the inline environment, which S0008 removes, so S0008's docs should rewrite them.
    - The Interface in the story names `factory.application.task.StageTask`, which does not exist. The reviewer already corrected it to `TaskComposer`.
    - The reviewer's two notes on the tests (a shared constant for `"stage environment: reset"`, and the walk loop in `tests/test_suite_fixtures.py` repeating `drive`) are not documentation, so I left them.

    `check`: check: green (not run again: passed on tree 4426094bb51c at 2026-10-25T17:18:35Z)
    `secrets`: secrets: green (1.3 s)
    `documents`: documents ok
30. factory: started smoke-test as self.
31. smoke-tester: I ran the two smoke-test commands as written, from the repository root. I fixed nothing.

    Command 1:
    ```bash
    uv run pytest tests/application/test_stage_run.py tests/application/test_after_agent.py tests/application/test_stalls.py tests/test_kill_points.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
    ```
    ```
    1
    ```
    It met `Expect: 1`. When I ran it without the grep, the last line was `128 passed in 40.55s`.

    Command 2:
    ```bash
    grep -c '"Makefile"' tests/git_support.py; grep -c 'FakeSnapshots(' tests/conftest.py
    ```
    ```
    1
    0
    ```
    It did not meet `Expect: two lines: 1; 1`. The second line is `0`.

    What I saw: the `boundaries` fixture in `tests/conftest.py` (line 238) calls `snapshots, containers = fake_dataset(tmp_path)`. The helper `fake_dataset` in `tests/container_support.py` (lines 89-98) builds `FakeSnapshots(workspace, base)` and `FakeContainerRuns(workspace)`. So the fixture does sit on `FakeSnapshots` at `<tmp_path>/workspace` with an empty base at `<tmp_path>/workspace-base`, and the Interface allows the helper to share them. But the literal `FakeSnapshots(` the smoke test greps for is not in `tests/conftest.py`.

    I read the acceptance criteria again. The first command's suite passes, and nothing I saw contradicts criteria 1 to 6. The finding is only that command 2's output does not match its `Expect:` line.

    Findings:
    1. Command: `grep -c '"Makefile"' tests/git_support.py; grep -c 'FakeSnapshots(' tests/conftest.py`. Expected: `1` and `1`. Observed: `1` and `0`. The fixture builds `FakeSnapshots` through `fake_dataset` of `tests/container_support.py`, not with a direct call in `tests/conftest.py`. The criterion this touches is the Interface's `tests/conftest.py` line, that the fixture "gives `snapshots=FakeSnapshots(<tmp_path>/workspace, <tmp_path>/workspace-base)`". As far as I can see, criterion 1's behaviour holds. There are two ways to close this:
       - (a) the fixture calls `FakeSnapshots(...)` itself;
       - (b) the human changes the smoke test's expectation to allow the helper.

       Choosing between them is not this stage's call.
32. factory: started doing as self.
33. coder: Round 2. The smoke tester's one finding (entry 31) is about a test file and the work item's smoke test, not about code. I changed no code in this run. The code stays as committed: `agent_working_directory` in `src/factory/application/take.py`, which `src/factory/application/task.py` and `src/factory/application/preflight.py` call.

    The finding: smoke command 2, `grep -c 'FakeSnapshots(' tests/conftest.py`, prints `0` where `1` is expected. The behaviour holds. The `boundaries` fixture (`tests/conftest.py:238`) calls `fake_dataset(tmp_path)` of `tests/container_support.py`, and `fake_dataset` builds `FakeSnapshots(<tmp_path>/workspace, <tmp_path>/workspace-base)` with the empty base. The world in `tests/proof_support.py:159` calls the same helper, and `tests/test_kill_points.py` relies on it keeping a base that an earlier start left. Criterion 1's test passes, and so does the whole of `make check` (entry 25).

    Question: which side should change?
    (a) The tester changes `tests/conftest.py` so the fixture calls `FakeSnapshots(...)` and `FakeContainerRuns(...)` itself, as the Interface's conftest line words it. This puts a second copy of `fake_dataset`'s body in `conftest.py` (directory creation and both constructors). Either the world keeps the helper, so there are two copies of one setup, which the reviewer counts as a finding. Or `fake_dataset` is changed to take the fixture's line, which is more test churn for the sake of a grep.
    (b) The smoke test's second command is reworded to check what the fixture actually does. For example: `grep -c '"Makefile"' tests/git_support.py; grep -c 'fake_dataset(tmp_path)' tests/conftest.py; grep -c 'FakeSnapshots(' tests/container_support.py`, expecting `1`; `1`; `1`. The Interface's conftest line would read "gives the fakes of `fake_dataset` (`FakeSnapshots(<tmp_path>/workspace, <tmp_path>/workspace-base)` and `FakeContainerRuns(<tmp_path>/workspace)`)". The work item is outside my write paths, so this is your edit, or the reviewer's.
    I would choose (b). It keeps one place that builds the suite's dataset, and the smoke test was written before the helper existed. If you choose (a), I will end with `tests` and name the change for the tester.

    Noticed, not touched: the reviewer's notes in entry 27, a shared constant for `"stage environment: reset"` and the walk loop in `tests/test_suite_fixtures.py` that repeats `drive`. Both are in tests.
34. 2026-10-25 human: (b). Keep the one place that builds the suite's dataset (`fake_dataset` in `tests/container_support.py`). The work item changes, not the tests:
    - The Interface's conftest line reads: "gives the fakes of `fake_dataset` (`FakeSnapshots(<tmp_path>/workspace, <tmp_path>/workspace-base)` and `FakeContainerRuns(<tmp_path>/workspace)`)".
    - Smoke command 2 becomes `grep -c '"Makefile"' tests/git_support.py; grep -c 'fake_dataset(tmp_path)' tests/conftest.py; grep -c 'FakeSnapshots(' tests/container_support.py`, with `Expect: three lines: 1; 1; 1`.
    The human does not push to the work-item branch, so the reviewer makes these two text edits to the work item (the reviewer may correct the work item's text, F0034). End with `review`.
35. factory: started doing as self.
