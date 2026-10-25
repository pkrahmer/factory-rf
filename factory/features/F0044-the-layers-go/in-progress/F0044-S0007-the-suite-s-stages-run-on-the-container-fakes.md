---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 450
comments_read: [6400499867]
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-25T16:59:44.386559Z'
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
---

# The suite's stages run on the container fakes

## Description

The suite runs a stage, a tick or a world of ticks on the `boundaries` fixture of `tests/conftest.py` and on the world of `tests/proof_support.py`, and both describe an `inline` instance: no snapshots, no containers, the agent's scripted writes in the factory's own checkout and the undo after them. Once the inline environment goes (S0008), every stage runs through `ContainerEnvironment`, so the suite must run its stages there first, on the fakes F0042 built: `FakeSnapshots` on a folder and `FakeContainerRuns`, which play the sync container as a child process on the host. This story moves the suite: the two places that build the suite's boundaries give them a dataset under `tmp_path` with an empty base, the remote every test copies holds a `Makefile` whose `sync` succeeds, and an agent's request names the dataset's checkout as its working directory whenever the boundaries hold snapshots, so `FakeAgentRuntime` writes where a real agent writes and the take brings the result in (decision 9 of `feature.md`). The tests that pin what only the inline environment does (the undo of the agent's writes in the factory's own checkout, the undo of what a red check wrote) are replaced by what the container environment does. What stays: the inline environment itself and its setting, until S0008; `MakeProjectCommands` as the suite's project commands on the host checkout (decision 3); every test of the stage protocol, the claims, the decisions and the stalls, with its name and what it checks.

## Interface

`factory.application.task.StageTask` and `factory.application.preflight._probe_request` (`application`): the request's `working_directory` is `boundaries.snapshots.mount_point / "checkout"` when `boundaries.snapshots` is set, and `boundaries.checkout` otherwise.

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
3. The working directory (rows of one parametrized test over `StageTask` and the probe's request): with the fixture's snapshots it is `<tmp_path>/workspace/checkout`; with `snapshots` `None` it is the host checkout.
4. A whole stage on the fixture (one test through `StageRunner`, a tester's stage whose scripted run writes `tests/test_new.py` and `src/forbidden.py` and decides `doing`, the checks' `Makefile` pushed with `sync`, `lint` and `check` targets that pass): the result commit on the branch holds `tests/test_new.py` and not `src/forbidden.py`; the entry's closing paragraph names `src/forbidden.py`; the factory log holds one line whose text after its timestamp begins `stage environment: reset`; the host checkout's work tree after the stage equals the result commit.
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
