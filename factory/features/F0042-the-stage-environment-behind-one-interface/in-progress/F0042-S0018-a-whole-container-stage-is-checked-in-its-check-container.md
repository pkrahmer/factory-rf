# A whole container stage is checked in its check container, and the stage environment's tests share their helpers

<!-- proposed by feature acceptance of 2026-10-24; refine before starting -->

## Description

F0042's promise is the whole cycle of a `container` stage: the reset, the sync container, the base moved, the agent on the dataset, the take, the checks in a check container on the taken result, and nothing left for the next stage. Each piece has its tests, but no test runs them together. `tests/application/test_container_environment_take.py` runs a whole stage with the host's `MakeProjectCommands`, and `tests/adapters/test_make_commands_container.py` runs the check container alone. The feature's acceptance ran the combination once, as a script, and it was green. This story pins it as tests, so that a later change, F0044's removal of the layers above all, cannot break the joint unseen. The behaviour exists, so these tests are expected to pass when they are written; a red one is a fault of the feature, and the tester ends with `question` naming it.

The story also moves the copies of shared test helpers that the feature's reviewers named, under the standing leave of `CLAUDE.md`. Nothing under `src/` changes.

## Interface

None under `src/factory/`. The tester writes:

- `tests/application/test_container_stage_checks.py` (new): a whole stage through `StageRunner` on the `boundaries` fixture. The boundaries hold `FakeSnapshots` and `FakeContainerRuns` from `container_support.container_dataset`, `ContainerMakeCommands(snapshots, containers, git, checkout=boundaries.checkout)` as `project_commands`, and `container_support.WorkspaceRuntime` as the agent runtime. The story is opened with `stage_run_support.open_story`, a `Makefile` of `stage_makefile()` plus a `sync` target that writes the git-ignored marker `.synced`, and it runs under `PIPELINE_YAML`, where the `tests` stage checks `lint` and reports `test`.
- Moves under the standing leave, each earlier test keeping its name and what it checks:
  - `FIVE_MINUTES` goes once into `tests/container_support.py`, used by `test_container_environment.py` and `test_container_environment_take.py`.
  - `BROKEN_FRONT_MATTER` goes once into `tests/take_support.py`, used by `test_take.py` and `test_take_edges.py`.
  - `_without_work_item` and `_with_broken_work_item` go once into `tests/undo_support.py`, without the leading underscore, used by `test_undo.py`, `test_take_edges.py` and `test_stage_environment.py`.
  - `tests/entry/test_wiring_stage_environment.py` uses `podman_support.IMAGE` and `zfs_support.DATASET` in place of its own copies.
  - `tests/application/test_stage_environment.py` imports no name that starts with `_` from another test module. Where it needs `_leave` of `test_sealed_runs.py`, that helper moves to a shared module under `tests/`.

## Acceptance criteria

1. In the whole stage, the agent writes `tests/test_a.py` (inside the tester's write paths) and `notes.md` (outside them) into the dataset's checkout. Afterwards:
   - the pushed commit is the remote branch's head;
   - it holds `tests/test_a.py` with the agent's text and no `notes.md`;
   - the pushed work item's journal names `notes.md`;
   - the factory log holds exactly one line with `stage environment:`;
   - the host's `git status` lists no change.
2. In the same stage, `FakeContainerRuns.calls` holds exactly three calls, in this order. The first is the sync container's, whose last word is the stage-start commit. The second is a check container whose last word is `lint`. The third is a check container whose last word is `test`. After the stage, the dataset's checkout holds `tests/test_a.py` and no `notes.md`: the check ran on the rolled-back base with the taken file.
3. After that stage, the test writes `stray.txt` into the dataset's checkout and `leftover` into the dataset's `home/`. It then calls `prepare` of a new `ContainerEnvironment` on the same fakes, at the head of the remote branch. Each row of a parametrized test checks one result: `stray.txt` is gone; `home/leftover` is gone; `tests/test_a.py` is present with the agent's text.
4. The helper moves:
   - `FIVE_MINUTES`, `BROKEN_FRONT_MATTER`, `def _without_work_item`, `def _with_broken_work_item` and `IMAGE = "factory-stage:1"` are each defined at most once under `tests/`;
   - `tests/application/test_stage_environment.py` has no `import _` of a name from another test module;
   - every earlier test keeps its name, and the tester's entry names each earlier test file it changed.
5. `make check` stays green.
6. docs: `docs/project-guide/stage-environment.md`, *Wiring and tests*, names `tests/application/test_container_stage_checks.py` as the whole stage through the check container. `docs/project-guide/README.md`, *Shared test helpers*, names the helpers that moved, with their new homes.

## Smoke test

```bash
uv run pytest tests/application/test_container_stage_checks.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

```bash
grep -rlE '^(FIVE_MINUTES|BROKEN_FRONT_MATTER) = ' tests | wc -l; grep -rlE '^def _?(without_work_item|with_broken_work_item)\(' tests | wc -l; grep -rl '^IMAGE = "factory-stage:1"' tests | wc -l
```
Expect: three lines, `2`, `1`, `1`

## Journal
