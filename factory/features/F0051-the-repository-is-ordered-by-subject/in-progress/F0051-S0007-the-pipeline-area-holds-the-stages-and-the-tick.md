---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 562
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-05T03:40:07.227126Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T03:39:39.403589Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T03:39:39.410082Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T03:40:02.178460Z'
  stage: intake
  run: 9b3d0beebc6e43e9be5a6a06cc886dad
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T03:40:07.227126Z'
  stage: tests
---

# The pipeline area holds the stages and the tick

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `pipeline` area: the pipeline definition, stages, checks, events, the tick, the scheduler and dispatcher, the handlers, claims, leases, stops, stalls, recovery and `Boundaries`. Each of its 27 modules moves from its layer package to the same layer inside `factory.pipeline`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/pipeline/<layer>/` (feature decision 5). It is the last move: afterwards `src/factory/` holds only the seven areas, `entry/` and `contract/`; the old layer packages `factory.domain`, `factory.application` and `factory.adapters` are gone, and every test module still left under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to the area of the module it imports most. No behaviour changes: every test that passed before passes after, with only its import lines and paths changed.

## Interface

New packages, each with an `__init__.py` holding a one-line docstring: `factory.pipeline`, `factory.pipeline.domain`, `factory.pipeline.application`, `factory.pipeline.adapters`; and the same folders under `tests/pipeline/`, each with an `__init__.py`.

The moves (old → new), each file moved with `git mv`:

- `factory.domain.checks` → `factory.pipeline.domain.checks`
- `factory.domain.evaluation` → `factory.pipeline.domain.evaluation`
- `factory.domain.events` → `factory.pipeline.domain.events`
- `factory.domain.fault_paths` → `factory.pipeline.domain.fault_paths`
- `factory.domain.known_results` → `factory.pipeline.domain.known_results`
- `factory.domain.lease` → `factory.pipeline.domain.lease`
- `factory.domain.pipeline_definition` → `factory.pipeline.domain.pipeline_definition`
- `factory.domain.recovery` → `factory.pipeline.domain.recovery`
- `factory.domain.stop_table` → `factory.pipeline.domain.stop_table`
- `factory.domain.stops` → `factory.pipeline.domain.stops`
- `factory.domain.tick_status` → `factory.pipeline.domain.tick_status`
- `factory.application.boundaries` → `factory.pipeline.application.boundaries`
- `factory.application.claims` → `factory.pipeline.application.claims`
- `factory.application.dispatcher` → `factory.pipeline.application.dispatcher`
- `factory.application.handlers` → `factory.pipeline.application.handlers` (a package)
- `factory.application.idle_shutdown` → `factory.pipeline.application.idle_shutdown`
- `factory.application.known_results` → `factory.pipeline.application.known_results`
- `factory.application.pipeline_loading` → `factory.pipeline.application.pipeline_loading`
- `factory.application.recovery` → `factory.pipeline.application.recovery`
- `factory.application.scheduler` → `factory.pipeline.application.scheduler`
- `factory.application.stage` → `factory.pipeline.application.stage`
- `factory.application.stalls` → `factory.pipeline.application.stalls`
- `factory.application.stops` → `factory.pipeline.application.stops`
- `factory.application.take` → `factory.pipeline.application.take`
- `factory.application.task` → `factory.pipeline.application.task`
- `factory.application.tick` → `factory.pipeline.application.tick`
- `factory.adapters.pipeline_yaml` → `factory.pipeline.adapters.pipeline_yaml`

- No module under `src/` or `tests/` imports an old path of a moved module, and no file is left at an old path.
- `tests/test_areas.py`: the table `AREAS` gains the row of `pipeline` with the modules above; nothing else in that module changes.
- Every test module still under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to `tests/<area>/<its layer>/` of the area of the module it imports most; the three folders are then removed.
- The tester makes every test change the move needs in its first run, before the code moves: it rewrites every import of a moved module under `tests/`, moves the test modules with `git mv`, creates the test packages and changes the guards that pin the old layout, under the leave of feature decision 5. The coder changes only `src/`: its write paths do not hold `tests/`, so a test change it makes is dropped.
- The recipe the earlier moves used, so that no run needs to read their journals: one `sed -E` over `src/` and `tests/` that rewrites `factory\.(domain|application|adapters)\.(<the names of the table>)` to `factory.pipeline..`; then the `from factory.<layer> import a, b` lines that mix moved and unmoved names, split by hand; then `ruff check --fix` and `ruff format`. `handlers` is a package: its submodules `factory.application.handlers.<name>` follow with it.
- The package docstrings are exactly: `factory.pipeline`: "The pipeline area: the pipeline definition, the stages, the tick and its handlers."; each layer package: "The pipeline area's <layer> layer." (with `domain`, `application` or `adapters`).

## Acceptance criteria

1. `AREAS` in `tests/test_areas.py` has this story's area as a key whose modules are exactly those of the table above; and for every module of the table (one row each), `importlib.import_module("factory.pipeline.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` (for `handlers`, the folder) does not exist.
2. Every package of the Interface (`factory.pipeline`, `factory.pipeline.domain`, `factory.pipeline.application`, `factory.pipeline.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` imports `factory.<layer>.<name>` of a module of the table, in any form (`import factory.<layer>.<name>`, `from factory.<layer>.<name> import x`, `from factory.<layer> import <name>`; one row per module).
4. `tests/domain/`, `tests/application/` and `tests/adapters/` do not exist.
5. `src/factory/` holds exactly `__init__.py`, the seven area packages, `entry/` and `contract/`; `factory.domain`, `factory.application` and `factory.adapters` cannot be imported.
6. `make check` stays green.
7. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `pipeline` and what it holds, in one sentence. `docs/decisions.md`: none, because the log is history and keeps the old paths.

## Smoke test

```bash
uv run python -c "import factory.pipeline.domain.checks as m; print(m.__name__)"
```
Expect: `factory.pipeline.domain.checks`

```bash
test -e src/factory/domain/checks.py && echo still there || echo moved
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
   - Interface: concrete. It gives 27 old → new module paths (11 domain, 15 application including the `handlers` package, 1 adapter), the four new packages with exact docstrings, and the test folders. The `AREAS` change is named. The recipe and the tester/coder split are stated.
   - Criteria: each is testable by one parametrized test function. 1 has a row per module, covers the key and exact module set of `AREAS` (standing answer 8), and has both sides: the new path imports and the old path does not exist. 2 checks the four packages import and have a docstring. 3 has one row per module and covers all three import forms. 4 and 5 are existence and absence checks, with the old layer packages not importable. 6 and 7 are the closing criteria. The docstring text and the `__init__.py` files are not tested, per standing answer 8, so I did not ask for criteria for them.
   - Smoke test: runnable. The pytest line passes no `-q` and `pyproject.toml` `addopts` already sets one `-q`, so the summary line exists and `grep -c passed` gives 1. Each `Expect:` can be checked against the output.
   - Architecture: matches `CLAUDE.md`. Each layer stays inside `factory.pipeline` and keeps its name and content, with no re-export left behind. `Layers` losing the optional old layers and `make areas` are the human's changes at S0007's start and merge, not this story's scope.
   - Scope: within F0051 (S0007 in the feature's list, the pipeline area last). It touches none of the feature's out-of-scope items and changes no behaviour. The names `known_results`, `recovery` and `stops` exist in both the domain and application layers, and each is listed in its own layer, so there is no ambiguity.
4. factory: started tests as vm.
