---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 558
comments_read: [6647217933]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-05T01:40:37.024813Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T01:30:42.907085Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T01:30:42.914340Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-05T01:31:01.535266Z'
  stage: intake
  run: 383f628a60eb4660ab6a3731e3c3b398
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-05T01:38:56.739185Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-05T01:38:59.126382Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-05T01:39:17.476226Z'
  stage: intake
  run: d2f740c301a64b8ba5bf665f4dacc5e0
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-05T01:39:22.530581Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-05T01:40:31.695373Z'
  stage: tests
  run: e27f1848590449218b893d5f81600b43
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-05T01:40:37.024813Z'
  stage: doing
---

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

1. For every module of the table above (one row each), `importlib.import_module("factory.work.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` does not exist. `AREAS` of `tests/test_areas.py` has a `work` key whose modules are exactly the 14 of the table.
2. Every package of the Interface (`factory.work`, `factory.work.domain`, `factory.work.application`, `factory.work.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` has an import line that names `factory.<layer>.<name>` for a module of the table (one row per module), in each form `imports()` of `tests/source_search.py` reads: `import factory.x.y`, `from factory.x.y import z` and `from factory.x import y`.
4. No test module left under `tests/domain/`, `tests/application/` or `tests/adapters/` takes all its `factory` imports from `work` and the areas moved before it (`shared` and `hosting`).
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

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: 1. Interface rule without a criterion: "`tests/test_areas.py`: the table `AREAS` gains the row of `work` with the modules above". No criterion tests it. The smoke test only counts a passing run, which passes without the row. Suggest a criterion such as "`AREAS` has a `work` key whose modules are exactly the 14 of the table".
   2. Interface rule without a criterion: the folders `tests/work/`, `tests/work/domain/`, `tests/work/application/` and `tests/work/adapters/` each get an `__init__.py`. Criterion 2 covers only the four `src` packages. Suggest adding the four test packages to criterion 2, or a separate criterion.
   3. Interface rule without a criterion: the new `src` packages' `__init__.py` holds a one-line docstring. Criterion 2 only says "has a docstring", not one line. Say whether one line is to be tested.
   4. Criterion 1 says "for `handlers`, the folder", but the table has no `handlers` module. This looks like a leftover from another story. Please remove it or say what it means.
   5. Criterion 4 and the Interface rule on test moves depend on "areas moved before it". Say which areas those are when this story runs: S0001 (`shared`) and S0002 (`hosting`) only, or also S0013's nothing. Name them, so the test can compute the set.
   6. Criterion 3 should say that it covers both `import factory.x.y` and `from factory.x import y` forms. As written, "an import line that names `factory.<layer>.<name>`" misses `from factory.domain import journal`.
   Format check passed. The architecture and scope fit F0051 (decisions 1 to 5, and the map to `work`). With these answered I would accept.
4. 2026-11-05 human: Answers of the human:

   1. Yes, as you suggest: criterion 1 also says that `AREAS` has a `work` key whose modules are exactly the 14 of the table.
   2. No criterion. The four test packages are structure; pytest's collection of same-named test modules already fails without them.
   3. "Has a docstring" is enough; one line is not tested.
   4. A leftover: remove "for `handlers`, the folder" from criterion 1. Only S0007 moves `handlers`.
   5. The areas moved before this story are `shared` (S0001) and `hosting` (S0002). S0013 moved nothing.
   6. Yes, both forms: `import factory.x.y`, `from factory.x.y import z` and `from factory.x import y`, as S0001's test already reads them with `imports()` from `tests/source_search.py`.

   These answers hold for S0004 to S0007 as well; feature decision 8 records them.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: names 4 new packages and 14 concrete old → new module moves, each a `git mv`. The `AREAS` row rule now has a criterion (see below).
   - Criteria: each is testable by one test function. I carried in the human's answers from journal entry 4. Criterion 1 now also says `AREAS` has a `work` key whose modules are exactly the 14 of the table (answer 1). I removed the "for `handlers`, the folder" leftover (answer 4). Criterion 3 now names the three import forms that `imports()` of `tests/source_search.py` reads (answer 6). Criterion 4 names the earlier areas as `shared` and `hosting` (answer 5). I added no criterion for the test packages' `__init__.py` files (answer 2) and none for a one-line docstring (answer 3). Each rule has its failing side: criteria 1 and 3 check that the old path is gone, and criterion 4 checks that no test module is left behind.
   - Smoke test: the three commands are runnable. Each `Expect:` line is checkable. The pytest command passes no `-q`, and I did not check the pytest configuration's `addopts`. The `tail -1 | grep -c passed` expectation needs a summary line, so the tester should confirm `addopts` doesn't set `-qq`.
   - Architecture: each module moves to the same layer inside `factory.work`, which fits the areas-with-layers design (feature decisions 1, 2 and 4). No re-export is left.
   - Scope: within F0051 and not in its "Out of scope". The tester's leave is feature decision 5, and the standing answers are decision 8.
7. factory: started tests as vm.
8. tester: I added the `work` row to the table `AREAS` in `tests/test_areas.py`. It holds the 14 modules of the Interface's table, in that order. Nothing else in the module changed, as the Interface asks. The tests S0001 and S0002 wrote are generic over `AREAS`, so the new row gives each criterion its cases for `work`:

   - criterion 1: tests/test_areas.py::test_a_moved_module_imports_from_its_area_and_is_gone_from_its_layer, one row per module, ids `work.<layer>.<name>`. The "exactly the 14" part is the `work` row of `AREAS` itself. I wrote no separate test that compares the table with a copy of itself.
   - criterion 2: tests/test_areas.py::test_an_area_package_imports_and_has_a_docstring, rows `factory.work`, `factory.work.domain`, `factory.work.application`, `factory.work.adapters`.
   - criterion 3: tests/test_areas.py::test_no_file_imports_a_moved_module_from_its_old_path, one row per module. It uses `imports()` of `tests/source_search.py`, which covers all three import forms.
   - criterion 4: tests/test_areas.py::test_no_test_module_stays_in_its_layer_folder_when_all_it_imports_has_moved. `_in_a_moved_area` now counts the `work` modules, under their new and old paths, beside `shared` and `hosting`. tests/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own also checks the test modules that move to `tests/work/`.
   - criterion 5: `make check`, run by the coder and the factory; no test function.
   - criterion 6: docs stage; no test function.

   Files created: none. Changed: tests/test_areas.py, the row only. This module was written by S0001 and S0002 of this feature; the Interface orders this change and feature decision 5 covers it.

   Run: `uv run pytest -q tests/test_areas.py` fails on the `work` rows. Only the last five lines were printed: all five are `work` rows of the old-path test, which fails because files still import the old paths. The test runner could not import these modules: `factory.work.domain.acceptance`, `factory.work.domain.answers`, `factory.work.domain.archive`, `factory.work.domain.decisions`, `factory.work.domain.journal`, `factory.work.domain.labels`, `factory.work.domain.move_rule`, `factory.work.domain.send_back`, `factory.work.domain.story_form`, `factory.work.domain.work_item`, `factory.work.application.acceptance`, `factory.work.application.acceptance_reading`, `factory.work.application.work_items`, `factory.work.adapters.work_item_markdown`, and the packages `factory.work`, `factory.work.domain`, `factory.work.application`, `factory.work.adapters`. `make lint`: green.

   Open: on the intake's note about `addopts` and `-qq` in the smoke test's pytest command: following the stage's rule against reading tool configuration, I did not check it.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
