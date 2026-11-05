---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 557
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T01:05:48.014859Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T01:05:48.021384Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T01:06:11.767541Z'
  stage: intake
  run: 5e6779303a574eaf999e8c8cb8ee7694
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T01:06:17.478196Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-05T01:06:58.805963Z'
  stage: tests
  run: 74f5c749261c455c83c99263b55e3599
---

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

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: concrete. It names 11 old to new module paths, 4 new source packages and the matching test packages, and says `AREAS` in `tests/test_areas.py` gains a `hosting` row. `tests/test_areas.py` exists (from S0001) and `src/factory/shared` exists.
   - Criteria: each can be tested by one parametrized test.
     - Criterion 1 has one row per module, with the import succeeding and the old file absent. Criterion 2 covers the 4 package imports and docstrings. Criterion 3 is a source scan of import lines, one row per module. Criterion 4 is a scan of the left-over test modules.
     - The rules have their failing side: the old path must not exist (criterion 1) and no import of an old path may remain (criterion 3). Criterion 5 is `make check`. Criterion 6 is docs.
     - Minor note: criterion 1 says "for `handlers`, the folder", but no table row is a folder and `src/factory/handlers` does not exist. I read it as a leftover. The tester should ignore it, and I did not turn it into a question.
   - Smoke test: the three commands are runnable. pyproject's `addopts` already sets `-q`, and the pytest command passes none, so the summary line exists and `grep -c passed` gives `1`. Each `Expect:` can be checked against the output.
   - Architecture: matches `CLAUDE.md` and feature decisions 1 to 4. Each module keeps its layer inside `factory.hosting`, and the layer rule is covered by the import-linter contracts that S0001 set.
   - Scope: within F0051's scope (S0002, the hosting area). The story changes no behaviour, and the test moves rest on the leave of feature decision 5. Nothing in it is out of scope.
4. factory: started tests as vm.
5. tester: Added the `hosting` row to the `AREAS` table in `tests/test_areas.py`: the 11 modules of the Interface, as `<layer>.<name>`. I changed nothing else in the module, as the Interface says. The parametrized tests that S0001 wrote are driven by that table, so the new row gives each hosting module and package its own test case:
   - criterion 1: tests/test_areas.py::test_a_moved_module_imports_from_its_area_and_is_gone_from_its_layer (one row per module, `hosting.<layer>.<name>`)
   - criterion 2: tests/test_areas.py::test_an_area_package_imports_and_has_a_docstring (rows `factory.hosting`, `factory.hosting.domain`, `factory.hosting.application`, `factory.hosting.adapters`)
   - criterion 3: tests/test_areas.py::test_no_file_imports_a_moved_module_from_its_old_path (one row per module)
   - criterion 4: tests/test_areas.py::test_no_test_module_stays_in_its_layer_folder_when_all_it_imports_has_moved. It counts `hosting` and `shared`, by old or new path, as moved. Separately, test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own will check every test module the coder moves to `tests/hosting/`.
   - criterion 5: `make check`, run by the factory; no test of its own.
   - criterion 6: docs; no test.

   Files changed: tests/test_areas.py. No files created.

   The test run failed for the right reasons. The import cases fail because the `factory.hosting.*` modules and packages do not exist yet. The old-path import cases fail because those paths are still imported. The run printed failures and no collection errors, so the test module itself imports fine. Modules the runner could not import: `factory.hosting` and its subpackages and the 11 moved modules; these are imported inside the tests, not at collection.

   `make lint`: green.

   Note: criterion 1 says "for `handlers`, the folder", but no row of the table is a folder. The existing test already checks both the `.py` file and a folder at the old path, so no question is needed.

   `lint`: lint: green (0.2 s)
