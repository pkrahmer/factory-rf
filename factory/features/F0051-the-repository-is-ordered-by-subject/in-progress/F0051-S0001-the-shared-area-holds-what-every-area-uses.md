---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 556
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T00:22:36.306042Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T00:22:36.312432Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T00:22:57.151643Z'
  stage: intake
  run: b60043aa03ae4cb8903c8e448754262f
---

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

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: all 18 moves name concrete old and new dotted paths; the four new packages and their test folders are named. A pure move adds no signatures. The source files exist at the old paths (spot-checked errors, files, validation_faults).
   - Criteria: each one is testable by one parametrized test: 1 (import succeeds, old file absent, one row per module), 2 (four packages import and have a docstring), 3 (no import line names an old path, which is the failing side of the move), 4 (no test module left that should have moved), 5 and 6 (closing criteria). Note, not a question: criterion 1 says "for `handlers`, the folder", but no module in the table is named handlers or is a folder, so that clause has no effect.
   - Smoke test: the three commands are runnable and each Expect line can be checked. pyproject.toml's addopts already sets `-q`, and the pytest command passes none, so the summary line is printed and `grep -c passed` gives 1.
   - Architecture: the moves keep the layer inside `factory.shared`, which matches CLAUDE.md and feature decision 1. The wildcard import-linter contracts are set by the human at S0001's start (feature "The human's changes"). The `process.py` exception already names the new path.
   - Scope: within F0051 S0001 and decisions 1 to 5. `shared` is the area decision 2 gives it, and kill_points and kill_point_cases are in it. Nothing in Out of scope is touched.
