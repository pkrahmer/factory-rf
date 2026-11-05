---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-05T04:33:54.255697Z'
  lease_duration: 60
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
