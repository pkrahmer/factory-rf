---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 563
comments_read: [6649815295]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T04:33:54.248583Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T04:33:54.255697Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-05T04:34:15.903571Z'
  stage: intake
  run: 8ff0f9d70dbd4873b3c98284e47b9c77
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-05T04:38:07.659435Z'
  stage: intake
---

# The root of `tests/` holds only its folders

## Description

After the seven moves, `tests/` mirrors the areas, but its root still holds about 200 modules: 73 `*_support.py` helpers, 13 other shared helpers (`human_clone.py`, `recording_log.py`, `source_search.py` and the rest) and 117 test modules, most of them structural guards and tests of the shell scripts and the agent files. This story sorts the root into folders by kind, so that a reader finds a helper or a guard without scrolling (F0051 candidates, item 41). The shared helpers go into a package `tests/support/`; the structural guards (the searches over the source, the `*_removed` tests, the `test_shared_*` and `test_no_*` guards, `test_layers.py` and `test_areas.py`) go into `tests/guards/`; the tests of the operator's scripts go into `tests/operator/`, those of `vm/` into `tests/vm/`, those of the agent files under `claude/` into `tests/agent_files/`; every other root test module goes to `tests/<area>/<layer>/` of the module it imports most. `tests/conftest.py` stays at the root. No test changes beyond its place and its import lines.

## Interface

- New packages, each with an `__init__.py` holding a one-line docstring: `tests/support/`, `tests/guards/`, `tests/operator/`, `tests/vm/`, `tests/agent_files/`.
- Every module at the root of `tests/` other than `conftest.py` moves with `git mv` to one of these folders or to an area's folder, by the rules of the Description; a helper is imported as `support.<name>` (for example `from support.bill_support import completed_records`).
- A guard that reads files by a path relative to its own file (for example `Path(__file__).parent`) keeps reading the same files after its move.
- The leave of feature decision 5 covers the changes; a change that `pyproject.toml` needs (a test path of `[tool.mutmut]`, a path of mypy or pytest) is the human's, asked for with a question.

## Acceptance criteria

1. The root of `tests/` holds exactly `conftest.py` and folders; every folder is a package with an `__init__.py`.
2. Every module that was a shared helper at the root (one row each, from `git show origin/main:tests` before the story) is importable as `support.<name>` and exists nowhere else.
3. No module under `tests/` imports a shared helper by its old bare name (`from bill_support import ...`, `import human_clone`).
4. Every test of the suite before this story still runs: the count of collected tests (`pytest --collect-only -q`, its last line) is the same as on `origin/main` before the story, which the tester writes into its entry.
5. `make check` stays green.
6. docs: `docs/project-guide/README.md`'s section *Shared test helpers* says that the helpers live in `tests/support/` and names the other folders of `tests/` and what each holds. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none.

## Smoke test

```bash
find tests -maxdepth 1 -type f -name '*.py' | sed 's#^tests/##'
```
Expect: `conftest.py`

```bash
uv run python -c "import sys; sys.path.insert(0, 'tests'); import support.bill_support as m; print(m.__name__)"
```
Expect: `support.bill_support`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed, so there are no findings from it):

   1. Criterion 2 and the Description do not say which root modules are "shared helpers". The Description counts 73 `*_support.py` and "13 other shared helpers (`human_clone.py`, `recording_log.py`, `source_search.py` and the rest)", but it names only three. The criterion says "one row each", and a test needs the exact list. Please list the 13 by name, or define the rule that selects them, for example "every root module without a `test_` prefix". My choice: that rule, which also covers `module_names.py`, `time_limits.py` and the other non-test modules.

   2. The Description and the Interface state placement rules that no criterion tests. These are: structural guards go to `tests/guards/`, tests of the operator's scripts go to `tests/operator/`, tests of `vm/` go to `tests/vm/`, tests of the agent files go to `tests/agent_files/`, and every other test module goes to the area and layer of the module it imports most. Criterion 1 only checks that the root is clean. Two coders could scatter modules differently and both pass. Please add criteria, or a table of module to folder as the move stories have. My choice: a table in the story with one row per root test module, and a criterion that each module sits in its row's folder. The "imports most" rule is otherwise a judgement call for many modules.

   3. The Interface says "A guard that reads files by a path relative to its own file keeps reading the same files after its move", and the Description says "No test changes beyond its place and its import lines". Neither has a criterion. A moved guard with `Path(__file__).parent` would pass while it reads the wrong folder (and so checks nothing). Please add a criterion. My choice: for each guard in the table that uses `__file__`, a test that the path it resolves is the same directory as before.

   4. Criterion 4 is not testable by a test function. The count of collected tests is compared with `origin/main`, and "the tester writes into its entry" is a report, not a test. Please say how it is checked. My choice: keep it as the tester's recorded figure, and add a criterion that the set of test function names is unchanged. That needs a stored list, which seems heavy. Please confirm which you want.

   5. `import support.<name>` and the smoke test's `sys.path.insert(0, 'tests')` assume `tests/` is on the import path. A new package named `tests/operator` or `tests/vm` could clash with other names once `tests/` is on `sys.path`. The story says a `pyproject.toml` change is the human's. Is `tests/` already on pytest's `pythonpath`, so that `from support.bill_support import ...` works under `make test` and `mypy --strict`? If not, please say that the human adds it at the story's start, as the feature's *The human's changes* says it will for "a path that `pyproject.toml` needs".
4. 2026-11-05 human: Answers of the human:

   1. **The rule, as you propose:** a shared helper is every module at the root of `tests/` whose name does not start with `test_`, except `conftest.py`. Criterion 2's rows come from that rule.

   2. **Rules by name, not a table**, and one criterion for them. Each root test module goes, by the first rule that fits:
      - `tests/guards/`: `test_*_search.py`, `test_*_removed.py`, `test_shared_*.py`, `test_no_*.py`, `test_suite_*.py`, `test_layers.py`, `test_areas.py`, `test_test_names.py`, `test_tests_run_under_the_starting_umask.py` and `test_model_configuration.py`;
      - `tests/operator_scripts/` (not `operator`: a package named `operator` on `sys.path` would hide the standard library's `operator`): `test_operator_*.py` and any other test of files under `operator/`;
      - `tests/vm/`: `test_vm_*.py`, `test_stage_image*.py` and any other test of files under `vm/`;
      - `tests/agent_files/`: `test_claude_*.py`, `test_shipped_agents*.py`, `test_template_*.py` and any other test of files under `claude/` or `template/`;
      - every other root test module: `tests/<area>/<layer>/` of the module it imports most, or `tests/entry/` when that is an entry module.
      New criterion: every module whose name fits one of the patterns above sits in that pattern's folder (one row per pattern). For the "imports most" ones, the tester lists module and folder in its entry and the reviewer checks the list; no criterion.

   3. **No criterion.** The tester lists, in its entry, every moved module that builds a path from `__file__`, with the change it made (for example `parent` to `parents[1]`); the reviewer checks those lines. Criterion 4's unchanged count of passing tests is the backstop.

   4. **Keep the recorded figure.** The tester writes the count of collected tests before and after into its entry; the reviewer compares. No stored list.

   5. **No `pyproject.toml` change is needed.** `tests/` has no `__init__.py`, so pytest's rootdir import puts `tests/` on `sys.path`, and mypy names `tests/support/x.py` as `support.x`, as it names today's root helpers. The one clash is `operator`, hence answer 2's `tests/operator_scripts/`. If a check still needs a path, ask again.

   The Description's and Interface's `tests/operator/` reads `tests/operator_scripts/` from here on.
