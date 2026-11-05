# The shared area holds what every area uses

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `shared` area: what every other area uses: errors, times, identifiers, paths, settings, the records contract, the document and duplicate checks, the kill points of the fault tests, the file ports, the clock, atomic files and processes. Each of its 18 modules moves from its layer package to the same layer inside `factory.shared`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/shared/<layer>/` (feature decision 5). As the first move, it also writes the guard that every later move extends: `tests/test_areas.py`, with one table of every area's modules. No behaviour changes: every test that passed before passes after, with only its import lines and paths changed.

## Interface

New packages, each with an `__init__.py` holding a one-line docstring: `factory.shared`, `factory.shared.domain`, `factory.shared.application`, `factory.shared.adapters`; and the same folders under `tests/shared/`, each with an `__init__.py`.

The moves (old → new), each file moved with `git mv`:

- `factory.domain.errors` → `factory.shared.domain.errors`
- `factory.domain.times` → `factory.shared.domain.times`
- `factory.domain.identifiers` → `factory.shared.domain.identifiers`
- `factory.domain.paths` → `factory.shared.domain.paths`
- `factory.domain.settings` → `factory.shared.domain.settings`
- `factory.domain.printed_lines` → `factory.shared.domain.printed_lines`
- `factory.domain.contract` → `factory.shared.domain.contract`
- `factory.domain.duplicates` → `factory.shared.domain.duplicates`
- `factory.domain.sections` → `factory.shared.domain.sections`
- `factory.domain.documents` → `factory.shared.domain.documents`
- `factory.domain.kill_points` → `factory.shared.domain.kill_points`
- `factory.domain.kill_point_cases` → `factory.shared.domain.kill_point_cases`
- `factory.application.files` → `factory.shared.application.files`
- `factory.adapters.clock` → `factory.shared.adapters.clock`
- `factory.adapters.atomic_file` → `factory.shared.adapters.atomic_file`
- `factory.adapters.process` → `factory.shared.adapters.process`
- `factory.adapters.printed_output` → `factory.shared.adapters.printed_output`
- `factory.adapters.validation_faults` → `factory.shared.adapters.validation_faults`

- No module under `src/` or `tests/` imports an old path of a moved module, and no file is left at an old path.
- `tests/test_areas.py` (new): a table `AREAS` from each area's name to its modules as `<layer>.<name>`, filled for `shared`, and parametrized tests over it, as criteria 1 to 3 say. Later moves add their rows to this table and change nothing else in it.
- A test module under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to `tests/shared/<its layer>/` when every one of its imports from `factory` is a module of the `shared` area or of an area already moved before it and at least one is of `shared`.
- The leave of feature decision 5 covers every other change to tests that the move needs.

## Acceptance criteria

1. For every module of the table above (one row each), `importlib.import_module("factory.shared.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` (for `handlers`, the folder) does not exist.
2. Every package of the Interface (`factory.shared`, `factory.shared.domain`, `factory.shared.application`, `factory.shared.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` has an import line that names `factory.<layer>.<name>` for a module of the table (one row per module).
4. No test module left under `tests/domain/`, `tests/application/` or `tests/adapters/` takes all its `factory` imports from `shared` and the areas moved before it.
5. `make check` stays green.
6. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `shared` and what it holds, in one sentence. `docs/decisions.md`: none, because the log is history and keeps the old paths.

## Smoke test

```bash
uv run python -c "import factory.shared.domain.errors as m; print(m.__name__)"
```
Expect: `factory.shared.domain.errors`

```bash
test -e src/factory/domain/errors.py && echo still there || echo moved
```
Expect: `moved`

```bash
uv run pytest tests/test_areas.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal
