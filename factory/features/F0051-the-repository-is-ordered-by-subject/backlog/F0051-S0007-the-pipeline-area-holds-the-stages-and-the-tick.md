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
