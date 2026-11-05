---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 561
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-05T03:13:53.348965Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T03:13:30.662144Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T03:13:30.668826Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T03:13:48.450409Z'
  stage: intake
  run: 3718a90250ba441da93dbc470520fb46
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T03:13:53.348965Z'
  stage: tests
---

# The machine area holds containers, images and disks

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `machine` area: containers, images, the stage environment, snapshots, disks, the preflight, the project's commands and the machine's power. Each of its 24 modules moves from its layer package to the same layer inside `factory.machine`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/machine/<layer>/` (feature decision 5). No behaviour changes: every test that passed before passes after, with only its import lines and paths changed.

## Interface

New packages, each with an `__init__.py` holding a one-line docstring: `factory.machine`, `factory.machine.domain`, `factory.machine.application`, `factory.machine.adapters`; and the same folders under `tests/machine/`, each with an `__init__.py`.

The moves (old → new), each file moved with `git mv`:

- `factory.domain.containers` → `factory.machine.domain.containers`
- `factory.domain.disk` → `factory.machine.domain.disk`
- `factory.domain.preflight` → `factory.machine.domain.preflight`
- `factory.domain.command_records` → `factory.machine.domain.command_records`
- `factory.domain.stage_layer` → `factory.machine.domain.stage_layer`
- `factory.application.containers` → `factory.machine.application.containers`
- `factory.application.disk_records` → `factory.machine.application.disk_records`
- `factory.application.images` → `factory.machine.application.images`
- `factory.application.machine_stop_exit` → `factory.machine.application.machine_stop_exit`
- `factory.application.preflight` → `factory.machine.application.preflight`
- `factory.application.project_commands` → `factory.machine.application.project_commands`
- `factory.application.stage_environment` → `factory.machine.application.stage_environment`
- `factory.application.snapshots` → `factory.machine.application.snapshots`
- `factory.adapters.podman_images` → `factory.machine.adapters.podman_images`
- `factory.adapters.podman_runs` → `factory.machine.adapters.podman_runs`
- `factory.adapters.fake_containers` → `factory.machine.adapters.fake_containers`
- `factory.adapters.fake_images` → `factory.machine.adapters.fake_images`
- `factory.adapters.fake_snapshots` → `factory.machine.adapters.fake_snapshots`
- `factory.adapters.copy_snapshots` → `factory.machine.adapters.copy_snapshots`
- `factory.adapters.zfs_snapshots` → `factory.machine.adapters.zfs_snapshots`
- `factory.adapters.disk_space` → `factory.machine.adapters.disk_space`
- `factory.adapters.make_commands` → `factory.machine.adapters.make_commands`
- `factory.adapters.power_off` → `factory.machine.adapters.power_off`
- `factory.adapters.preflight_stamp_file` → `factory.machine.adapters.preflight_stamp_file`

- No module under `src/` or `tests/` imports an old path of a moved module, and no file is left at an old path.
- `tests/test_areas.py`: the table `AREAS` gains the row of `machine` with the modules above; nothing else in that module changes.
- A test module under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to `tests/machine/<its layer>/` when every one of its imports from `factory` is a module of the `machine` area or of an area already moved before it and at least one is of `machine`.
- The tester makes every test change the move needs in its first run, before the code moves: it rewrites every import of a moved module under `tests/`, moves the test modules with `git mv`, creates the test packages and changes the guards that pin the old layout, under the leave of feature decision 5. The coder changes only `src/`: its write paths do not hold `tests/`, so a test change it makes is dropped.
- The package docstrings are exactly: `factory.machine`: "The machine area: containers, images, snapshots, disks and the preflight."; each layer package: "The machine area's <layer> layer." (with `domain`, `application` or `adapters`).

## Acceptance criteria

1. `AREAS` in `tests/test_areas.py` has this story's area as a key whose modules are exactly those of the table above; and for every module of the table (one row each), `importlib.import_module("factory.machine.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` does not exist.
2. Every package of the Interface (`factory.machine`, `factory.machine.domain`, `factory.machine.application`, `factory.machine.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` imports `factory.<layer>.<name>` of a module of the table, in any form (`import factory.<layer>.<name>`, `from factory.<layer>.<name> import x`, `from factory.<layer> import <name>`; one row per module).
4. No test module left under `tests/domain/`, `tests/application/` or `tests/adapters/` takes all its `factory` imports from `machine` and the areas moved before it.
5. `make check` stays green.
6. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `machine` and what it holds, in one sentence. `docs/decisions.md`: none, because the log is history and keeps the old paths.

## Smoke test

```bash
uv run python -c "import factory.machine.domain.containers as m; print(m.__name__)"
```
Expect: `factory.machine.domain.containers`

```bash
test -e src/factory/domain/containers.py && echo still there || echo moved
```
Expect: `moved`

```bash
uv run pytest tests/test_areas.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names 4 new packages with exact docstrings and 24 concrete old→new module moves (5 domain, 8 application, 11 adapters, which matches the Description's count). The tester's and coder's split of work follows feature decision 5.
   - Criteria: each is testable by one parametrized test (one row per module for 1 and 3). Criterion 1 includes the AREAS key per decision 8. This is a pure move with no new rules, so there is no failing side to cover. Criterion 4 gives the rule for which test modules move.
   - Smoke test: three commands are runnable. The pytest one passes no `-q` and relies on the project's addopts; its `tail -1 | grep -c passed` expectation (`1`) is checkable. The other two Expect lines are exact outputs.
   - Architecture: modules go to the machine area with their layers inside, as feature decisions 1 and 2 say. The moves stay inside the layer rules. No re-export is left behind (decision 4).
   - Scope: the story is inside F0051 scope (S0006 in the story list). It changes no behaviour or names, and it leaves docs/decisions.md alone. I did not open the source tree to confirm that each of the 24 old modules exists.
4. factory: started tests as vm.
