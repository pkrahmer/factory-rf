---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 559
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T02:13:20.633087Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T02:13:20.639563Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T02:13:39.485040Z'
  stage: intake
  run: 642d092507c9489ab4a4e99520322e98
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T02:13:44.797849Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-05T02:14:39.046659Z'
  stage: tests
  run: 4132ed73d1ae4447964fec777cb9f15d
---

# The agents area holds the agent runs

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `agents` area: agent runs, the two runtimes, prompts, write paths, tool uses, provider limits and tokens. Each of its 19 modules moves from its layer package to the same layer inside `factory.agents`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/agents/<layer>/` (feature decision 5). No behaviour changes: every test that passed before passes after, with only its import lines and paths changed.

## Interface

New packages, each with an `__init__.py` holding a one-line docstring: `factory.agents`, `factory.agents.domain`, `factory.agents.application`, `factory.agents.adapters`; and the same folders under `tests/agents/`, each with an `__init__.py`.

The moves (old → new), each file moved with `git mv`:

- `factory.domain.agent_runs` → `factory.agents.domain.agent_runs`
- `factory.domain.died_runs` → `factory.agents.domain.died_runs`
- `factory.domain.opencode_provider` → `factory.agents.domain.opencode_provider`
- `factory.domain.prompts` → `factory.agents.domain.prompts`
- `factory.domain.provider_limits` → `factory.agents.domain.provider_limits`
- `factory.domain.tokens` → `factory.agents.domain.tokens`
- `factory.domain.tool_uses` → `factory.agents.domain.tool_uses`
- `factory.domain.write_paths` → `factory.agents.domain.write_paths`
- `factory.application.agent_runtime` → `factory.agents.application.agent_runtime`
- `factory.application.project_agents` → `factory.agents.application.project_agents`
- `factory.application.provider_limits` → `factory.agents.application.provider_limits`
- `factory.application.tokens` → `factory.agents.application.tokens`
- `factory.application.write_paths` → `factory.agents.application.write_paths`
- `factory.adapters.agent_files` → `factory.agents.adapters.agent_files`
- `factory.adapters.agent_launch` → `factory.agents.adapters.agent_launch`
- `factory.adapters.claude_runtime` → `factory.agents.adapters.claude_runtime`
- `factory.adapters.opencode_runtime` → `factory.agents.adapters.opencode_runtime`
- `factory.adapters.fake_agent_runtime` → `factory.agents.adapters.fake_agent_runtime`
- `factory.adapters.oauth_token` → `factory.agents.adapters.oauth_token`

- No module under `src/` or `tests/` imports an old path of a moved module, and no file is left at an old path.
- `tests/test_areas.py`: the table `AREAS` gains the row of `agents` with the modules above; nothing else in that module changes.
- A test module under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to `tests/agents/<its layer>/` when every one of its imports from `factory` is a module of the `agents` area or of an area already moved before it and at least one is of `agents`.
- The leave of feature decision 5 covers every other change to tests that the move needs.

## Acceptance criteria

1. `AREAS` in `tests/test_areas.py` has this story's area as a key whose modules are exactly those of the table above; and for every module of the table (one row each), `importlib.import_module("factory.agents.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` does not exist.
2. Every package of the Interface (`factory.agents`, `factory.agents.domain`, `factory.agents.application`, `factory.agents.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` imports `factory.<layer>.<name>` of a module of the table, in any form (`import factory.<layer>.<name>`, `from factory.<layer>.<name> import x`, `from factory.<layer> import <name>`; one row per module).
4. No test module left under `tests/domain/`, `tests/application/` or `tests/adapters/` takes all its `factory` imports from `agents` and the areas moved before it.
5. `make check` stays green.
6. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `agents` and what it holds, in one sentence. `docs/decisions.md`: none, because the log is history and keeps the old paths.

## Smoke test

```bash
uv run python -c "import factory.agents.domain.agent_runs as m; print(m.__name__)"
```
Expect: `factory.agents.domain.agent_runs`

```bash
test -e src/factory/domain/agent_runs.py && echo still there || echo moved
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
   - Interface: the four new packages and the 19 moves are listed old to new with concrete module paths. The rules (no old path, no re-export, which test modules move) are stated and each has a criterion.
   - Criteria: 1 (AREAS row, import of each new path, old file gone, one row per module), 2 (packages import and have a docstring), 3 (no old import, one row per module, in the three forms of feature decision 8) and 4 (no test module left that takes all its imports from agents and earlier areas) are each testable by one test function. 5 and 6 are the closing criteria. Both sides of every rule are covered: the new path exists and the old one does not, and an old import is absent. Feature decision 8 supplies the standing answers on the AREAS key, the untested `__init__.py` files and docstring form, which areas count as "moved before", and the import forms.
   - Smoke test: the three commands are runnable and each Expect line can be checked against the output. The pytest command passes no `-q`, and `pyproject.toml`'s `addopts` already sets one, so `tail -1` shows the "N passed" summary line.
   - Architecture: the move keeps each module in its own layer inside `factory.agents`, so the layer rule holds. It matches feature decisions 1 to 4 and 7.
   - Scope: this is the agents area of S0004 in the feature's stories list, and it changes no behaviour. `docs/decisions.md` is untouched, as the feature's out-of-scope list requires. No test that another story wrote is changed beyond the leave in feature decision 5.
4. factory: started tests as vm.
5. tester: Added the `agents` row to `AREAS` in `tests/test_areas.py`, holding the 19 modules of the Interface's table. That was the only change. The test functions already in that module are parametrized over `AREAS`, so they now cover the new area and I wrote no new functions. This matches the Interface's rule that nothing else in that module changes.

   - criterion 1: tests/test_areas.py::test_a_moved_module_imports_from_its_area_and_is_gone_from_its_layer (one row per module, ids `agents.<layer>.<name>`). The key and its module list are the new `AREAS["agents"]` entry.
   - criterion 2: tests/test_areas.py::test_an_area_package_imports_and_has_a_docstring (rows `factory.agents`, `factory.agents.adapters`, `factory.agents.application`, `factory.agents.domain`)
   - criterion 3: tests/test_areas.py::test_no_file_imports_a_moved_module_from_its_old_path (one row per module; `source_search.imports` covers the three import forms)
   - criterion 4: tests/test_areas.py::test_no_test_module_stays_in_its_layer_folder_when_all_it_imports_has_moved. tests/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own checks the moved test modules under `tests/agents/` once they exist.
   - criteria 5 and 6: the closing ones (`make check` stays green, docs), not tested here.

   Files: I created none. I changed tests/test_areas.py, which an earlier story of this feature wrote; feature decision 5 covers that change, and the Interface names it.

   Run of `uv run pytest -q tests/test_areas.py`: the new rows fail for the right reason. The `factory.agents.*` modules cannot be imported yet (ModuleNotFoundError), and the old paths are still imported from `src/` and `tests/`. The runner could not import `factory.agents`, `factory.agents.domain`, `factory.agents.application`, `factory.agents.adapters`, or any of the 19 modules under them. `make lint` is green.

   `lint`: lint: green (0.2 s)
