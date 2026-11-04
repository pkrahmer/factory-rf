# The hosting area holds git and the hosting service

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `hosting` area: git, the hosting service, pushes, the hand-over and the opening of pull requests. Each of its 11 modules moves from its layer package to the same layer inside `factory.hosting`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/hosting/<layer>/` (feature decision 5). No behaviour changes: every test that passed before passes after, with only its import lines and paths changed.

## Interface

New packages, each with an `__init__.py` holding a one-line docstring: `factory.hosting`, `factory.hosting.domain`, `factory.hosting.application`, `factory.hosting.adapters`; and the same folders under `tests/hosting/`, each with an `__init__.py`.

The moves (old → new), each file moved with `git mv`:

- `factory.domain.git` → `factory.hosting.domain.git`
- `factory.domain.hosting` → `factory.hosting.domain.hosting`
- `factory.domain.hand_over` → `factory.hosting.domain.hand_over`
- `factory.domain.post_texts` → `factory.hosting.domain.post_texts`
- `factory.application.git` → `factory.hosting.application.git`
- `factory.application.hosting` → `factory.hosting.application.hosting`
- `factory.application.pushes` → `factory.hosting.application.pushes`
- `factory.application.opening` → `factory.hosting.application.opening`
- `factory.adapters.git_cli` → `factory.hosting.adapters.git_cli`
- `factory.adapters.pygithub_hosting` → `factory.hosting.adapters.pygithub_hosting`
- `factory.adapters.fake_hosting` → `factory.hosting.adapters.fake_hosting`

- No module under `src/` or `tests/` imports an old path of a moved module, and no file is left at an old path.
- `tests/test_areas.py`: the table `AREAS` gains the row of `hosting` with the modules above; nothing else in that module changes.
- A test module under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to `tests/hosting/<its layer>/` when every one of its imports from `factory` is a module of the `hosting` area or of an area already moved before it and at least one is of `hosting`.
- The leave of feature decision 5 covers every other change to tests that the move needs.

## Acceptance criteria

1. For every module of the table above (one row each), `importlib.import_module("factory.hosting.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` (for `handlers`, the folder) does not exist.
2. Every package of the Interface (`factory.hosting`, `factory.hosting.domain`, `factory.hosting.application`, `factory.hosting.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` has an import line that names `factory.<layer>.<name>` for a module of the table (one row per module).
4. No test module left under `tests/domain/`, `tests/application/` or `tests/adapters/` takes all its `factory` imports from `hosting` and the areas moved before it.
5. `make check` stays green.
6. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `hosting` and what it holds, in one sentence. `docs/decisions.md`: none, because the log is history and keeps the old paths.

## Smoke test

```bash
uv run python -c "import factory.hosting.domain.git as m; print(m.__name__)"
```
Expect: `factory.hosting.domain.git`

```bash
test -e src/factory/domain/git.py && echo still there || echo moved
```
Expect: `moved`

```bash
uv run pytest tests/test_areas.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal
