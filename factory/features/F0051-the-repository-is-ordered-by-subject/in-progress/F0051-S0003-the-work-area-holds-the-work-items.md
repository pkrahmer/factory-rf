# The work area holds the work items

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `work` area: work items, their journal, the story form, answers, decisions, send-backs, the archive and the feature acceptance. Each of its 14 modules moves from its layer package to the same layer inside `factory.work`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/work/<layer>/` (feature decision 5). No behaviour changes: every test that passed before passes after, with only its import lines and paths changed.

## Interface

New packages, each with an `__init__.py` holding a one-line docstring: `factory.work`, `factory.work.domain`, `factory.work.application`, `factory.work.adapters`; and the same folders under `tests/work/`, each with an `__init__.py`.

The moves (old → new), each file moved with `git mv`:

- `factory.domain.acceptance` → `factory.work.domain.acceptance`
- `factory.domain.answers` → `factory.work.domain.answers`
- `factory.domain.archive` → `factory.work.domain.archive`
- `factory.domain.decisions` → `factory.work.domain.decisions`
- `factory.domain.journal` → `factory.work.domain.journal`
- `factory.domain.labels` → `factory.work.domain.labels`
- `factory.domain.move_rule` → `factory.work.domain.move_rule`
- `factory.domain.send_back` → `factory.work.domain.send_back`
- `factory.domain.story_form` → `factory.work.domain.story_form`
- `factory.domain.work_item` → `factory.work.domain.work_item`
- `factory.application.acceptance` → `factory.work.application.acceptance`
- `factory.application.acceptance_reading` → `factory.work.application.acceptance_reading`
- `factory.application.work_items` → `factory.work.application.work_items`
- `factory.adapters.work_item_markdown` → `factory.work.adapters.work_item_markdown`

- No module under `src/` or `tests/` imports an old path of a moved module, and no file is left at an old path.
- `tests/test_areas.py`: the table `AREAS` gains the row of `work` with the modules above; nothing else in that module changes.
- A test module under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to `tests/work/<its layer>/` when every one of its imports from `factory` is a module of the `work` area or of an area already moved before it and at least one is of `work`.
- The leave of feature decision 5 covers every other change to tests that the move needs.

## Acceptance criteria

1. For every module of the table above (one row each), `importlib.import_module("factory.work.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` (for `handlers`, the folder) does not exist.
2. Every package of the Interface (`factory.work`, `factory.work.domain`, `factory.work.application`, `factory.work.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` has an import line that names `factory.<layer>.<name>` for a module of the table (one row per module).
4. No test module left under `tests/domain/`, `tests/application/` or `tests/adapters/` takes all its `factory` imports from `work` and the areas moved before it.
5. `make check` stays green.
6. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `work` and what it holds, in one sentence. `docs/decisions.md`: none, because the log is history and keeps the old paths.

## Smoke test

```bash
uv run python -c "import factory.work.domain.acceptance as m; print(m.__name__)"
```
Expect: `factory.work.domain.acceptance`

```bash
test -e src/factory/domain/acceptance.py && echo still there || echo moved
```
Expect: `moved`

```bash
uv run pytest tests/test_areas.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal
