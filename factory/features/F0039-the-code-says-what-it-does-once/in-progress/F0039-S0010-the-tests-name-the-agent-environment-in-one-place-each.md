---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 405
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T12:20:20.801190Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T12:20:20.807064Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T12:20:43.208639Z'
  stage: intake
  run: cdf9869216c24b08826789beb26bffd1
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T12:21:04.523855Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T12:27:27.559987Z'
  stage: tests
  run: ed9a2106b514449abffbc43e759bd15a
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T12:27:49.893700Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T12:30:26.804301Z'
  stage: doing
  run: fe65e51765ba4c55aaf2384065454cbf
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T12:30:47.906583Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T12:31:49.411035Z'
  stage: review
  run: 52b7d9d8dc9843f1a4c75f808cde3ba9
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-21T12:32:10.464059Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-21T12:32:45.919158Z'
  stage: docs
  run: 9bd3645416ff43c2896838489db79c16
---

# The tests name the agent environment in one place each

## Description

Twenty test modules define a top-level `ENVIRONMENT` constant (the environment a test hands to the stage runner or the handler factory) that has the same value as another module's. Eleven modules assign `{"PATH": "/usr/local/bin:/usr/bin", "HOME": "/home/factory"}`: `tests/stage_run_support.py`, which already shares it, and ten copies. Ten modules assign `{"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}` and no shared module holds it. Two modules import the constant from another test module: `tests/application/test_tick_project_agent.py` from `application.test_tick_agent_definition` and `tests/application/test_sealed_runs_runner.py` from `application.test_sealed_runs`. That is the same kind of copy that F0039-S0009 removed for `INSTANCE`, whose Description left the `ENVIRONMENT` constants to a later story. This story moves them under the standing leave of `CLAUDE.md` (*Tests*), which names constants. `stage_run_support.ENVIRONMENT` is the one definition of the first value. `wiring_support.ENVIRONMENT` (new) is the one definition of the second, which the handler and wiring tests pass. Every other module imports the constant from its shared module, and a guard finds a new copy by its value. The tester does the work: no module under `src/factory/` changes and the coder has nothing to build. Unchanged: every `ENVIRONMENT` with a value no other module assigns (in `probe_support.py`, `test_wiring_*` and others), and the pair `{"PATH": "/opt/guard", "HOME": "/home/factory"}` in `tests/application/test_task.py` and `tests/application/test_task_acceptance.py`. That pair has two copies and no shared module of the task tests, so it is left to the human. The many other imports from one test module into another (about forty-five lines) are also left to the human.

A check on the work, not a criterion: the tester lists the `pytest --collect-only` ids of the modules the Interface names before and after the move (in `$TMPDIR`), says in the journal that they match, and the reviewer confirms it.

## Interface

No module under `src/factory/` changes.

`tests/stage_run_support.py`: `ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin", "HOME": "/home/factory"}` stays. The modules whose top-level assignment of that value is removed and that import `ENVIRONMENT` from `stage_run_support` instead: `tests/application/test_after_agent.py`, `tests/application/test_cost_image.py`, `tests/application/test_costs.py`, `tests/application/test_nested_repositories.py`, `tests/application/test_sealed_runs.py`, `tests/application/test_stage_finish.py`, `tests/application/test_stage_launch.py`, `tests/application/test_stage_run_acceptance.py`, `tests/application/test_stall_labels.py`, `tests/application/test_stalls.py`.

`tests/wiring_support.py`: gains `ENVIRONMENT = {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}`. The modules whose top-level assignment of that value is removed and that import `ENVIRONMENT` from `wiring_support` instead: `tests/acceptance_walk.py`, `tests/application/handlers/test_run.py`, `tests/application/test_tick_agent_definition.py`, `tests/entry/test_run.py`, `tests/entry/test_wiring_acceptance.py`, `tests/entry/test_wiring_constants.py`, `tests/entry/test_wiring_handlers.py`, `tests/entry/test_wiring_human_handlers.py`, `tests/entry/test_wiring_recovery.py`, `tests/entry/test_wiring_recovery_expired.py`.

- `tests/application/test_tick_project_agent.py` imports `ENVIRONMENT` from `wiring_support`, and `tests/application/test_sealed_runs_runner.py` imports it from `stage_run_support`. Their other imports from those test modules stay. `mypy --strict` refuses an import of a name that a module only imported itself.
- No import cycle is added. `stage_run_support` imports `git_support` and `human_clone` only, and `wiring_support` imports no test module; both keep doing so.

`tests/test_shared_environments.py` (new), the guard:

```python
SHARED: dict[str, dict[str, str]]  # module, relative to tests/ -> the environment it shares, imported from it


def environment_copies(source: str, environment: Mapping[str, str]) -> list[str]:
    """The names that a top-level assignment in `source` gives a dict literal equal to `environment`."""
```

- `SHARED` is `{"stage_run_support.py": stage_run_support.ENVIRONMENT, "wiring_support.py": wiring_support.ENVIRONMENT}`. The values are imported, never written again in the guard.
- An assignment counts at the top level of a module, plain (`=`) or annotated, when its value is a dict literal whose `ast.literal_eval` equals `environment`, whatever the name and the order of the keys.
- An assignment inside a function or a class, a dict with another key or another value, a name as the value (`ENVIRONMENT = OTHER`) or a call (`dict(PATH=..., HOME=...)`) does not count.
- The guard reads every `*.py` file under `tests/`.

The earlier test this story changes beyond the standing leave (decision 14): `tests/test_shared_bodies.py::test_no_test_module_holds_a_copy` decides a defining module by its path relative to `tests/`, not by its file name.

## Acceptance criteria

1. Each shared environment is assigned in one module (rows of one parametrized test over `SHARED`, paths relative to `tests/`, sorted). Row `stage_run_support.py`: its value is `{"PATH": "/usr/local/bin:/usr/bin", "HOME": "/home/factory"}`, and the modules for which `environment_copies` of that value is not empty are exactly `["stage_run_support.py"]`. Row `wiring_support.py`: its value is `{"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}`, and those modules are exactly `["wiring_support.py"]`.
2. The guard counts a top-level assignment of the value under any name and nothing else (rows of one parametrized test, each a source text read by `environment_copies` against `{"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}`). `ENVIRONMENT = {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}\n` → `["ENVIRONMENT"]`. The same under the name `HANDLER_ENV` → `["HANDLER_ENV"]`. The same annotated `ENVIRONMENT: dict[str, str] = ...` → `["ENVIRONMENT"]`. The same with `HOME` first → `["ENVIRONMENT"]`. `ENVIRONMENT = {"PATH": "/opt/guard", "HOME": "/home/factory"}\n` → `[]`. The value with one more key `"LANG": "C.UTF-8"` → `[]`. `ENVIRONMENT = OTHER\n` → `[]`. `ENVIRONMENT = dict(PATH="/opt/scripts:/usr/bin:/bin", HOME="/home/factory")\n` → `[]`. The plain assignment inside `def f():` → `[]`. The plain assignment inside `class C:` → `[]`.
3. The bodies guard decides a defining module by its path relative to `tests/`, not by its file name (decision 14): in `tests/test_shared_bodies.py::test_no_test_module_holds_a_copy`, a module counts as defining a shared helper when `path.relative_to(TESTS).as_posix()` is one of `SHARED`'s values. The test keeps its name and its ids, and passes for every module of today.
4. `make check` stays green.
5. docs: `docs/project-guide/README.md`, *Shared test helpers*: the `stage_run_support.py` line also names `ENVIRONMENT`, the environment the stage-run tests pass. The `wiring_support.py` line names `ENVIRONMENT`, the environment the handler and wiring tests pass. One of the two lines says that `tests/test_shared_environments.py` fails on another top-level assignment of either value. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none. Nothing an operator or a newcomer sees changes, and no decision is taken.

## Smoke test

```bash
for v in '"/usr/local/bin:/usr/bin"' '"/opt/scripts:/usr/bin:/bin"'; do grep -rlF --include='*.py' "ENVIRONMENT = {\"PATH\": $v, \"HOME\": \"/home/factory\"}" tests | sort; done
```
Expect: two lines, `tests/stage_run_support.py` then `tests/wiring_support.py` (before the story, 21 lines, and `tests/wiring_support.py` not among them)

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
TMPDIR="$d" uv run pytest --no-header --tb=short -p no:cacheprovider tests/test_shared_environments.py tests/application/test_tick_project_agent.py tests/application/test_sealed_runs_runner.py tests/entry/test_wiring_constants.py tests/application/test_stalls.py > "$d/out" 2>&1
echo "exit $?"
```
Expect: one line, `exit 0`

```bash
grep -c '^- `\(stage_run_support\|wiring_support\).py`:.*`ENVIRONMENT`' docs/project-guide/README.md
```
Expect: one line, `2` (before the story, `0`)

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: concrete. It names the two shared modules (`tests/stage_run_support.py`, `tests/wiring_support.py`) and the ten importing modules for each value. It names the two cross-imports and the guard `tests/test_shared_environments.py` with `SHARED` and `environment_copies(source, environment) -> list[str]`. It also names the one earlier test changed (`test_no_test_module_holds_a_copy`). It states that no module under `src/` changes. `tests/test_shared_bodies.py` already has `SHARED` with values that are file names and a `path.name in SHARED.values()` check at line 153, so the change in criterion 3 is a real one.
   - Criteria: each is testable by one parametrized test function with no further decisions. Criterion 1 covers both shared values with exact module lists. Criterion 2 has ten rows, covering the counted forms (any name, annotated, key order) and each refused form (other value, extra key, name, call, function scope, class scope). Criterion 3 covers the relative-path rule of decision 14. Each rule in the Interface has a criterion for its failing side. `make check` and `docs:` are last.
   - Smoke test: the grep loop, the pytest run and the docs grep are runnable. The pytest command passes no `-q`, and `pyproject.toml` `addopts` already sets `-q`. Each `Expect:` is checkable against the output: line counts, `exit 0`, and `2`. The docs regex matches the existing `- \`name.py\`:` line form in `docs/project-guide/README.md`.
   - Architecture: the changes are test-only, in shared modules at the `tests/` root, under the standing leave for constants in `CLAUDE.md`. `stage_run_support` and `wiring_support` keep their import limits. The one change to an earlier test has the human's leave in decision 14.
   - Scope: within F0039 (the tests' copies of shared helpers). It touches no `src/` file, no out-of-scope item, and none of the 'Unchanged' constants it lists. The documenter's work is limited to the project guide.
4. factory: started tests as self.
5. tester: Tests written and the move done. This story is all tester work, so the tests are green, not red: no module under `src/factory/` changes and the coder has nothing to build.

   Mapping:
   - criterion 1: tests/test_shared_environments.py::test_each_shared_environment_is_assigned_in_one_module (rows `stage_run_support.py`, `wiring_support.py`)
   - criterion 2: tests/test_shared_environments.py::test_the_guard_counts_a_top_level_assignment_of_the_environment (10 rows: plain, other-name, annotated, home-first, other-value, one-more-key, name-as-value, a-call, in-function, in-class)
   - criterion 3: tests/test_shared_bodies.py::test_no_test_module_holds_a_copy, which now checks `path.relative_to(TESTS).as_posix() in SHARED.values()` instead of `path.name` (decision 14). Its name and ids are unchanged.
   - criterion 4: no test of its own; `make check` was run and is green (lint, types, layers, sast, secrets, licenses, test).
   - criterion 5 (docs): for the documenter, no test.

   Files created: tests/test_shared_environments.py.
   Files changed:
   - tests/wiring_support.py gains `ENVIRONMENT`.
   - These ten modules lost their own `ENVIRONMENT` and import it from `stage_run_support`: test_after_agent, test_cost_image, test_costs, test_nested_repositories, test_sealed_runs, test_stage_finish, test_stage_launch, test_stage_run_acceptance, test_stall_labels, test_stalls (all under tests/application/).
   - These ten modules import it from `wiring_support`: tests/acceptance_walk.py, tests/application/handlers/test_run.py, tests/application/test_tick_agent_definition.py, tests/entry/test_run.py, tests/entry/test_wiring_acceptance.py, tests/entry/test_wiring_constants.py, tests/entry/test_wiring_handlers.py, tests/entry/test_wiring_human_handlers.py, tests/entry/test_wiring_recovery.py, tests/entry/test_wiring_recovery_expired.py.
   - tests/application/test_tick_project_agent.py now imports `ENVIRONMENT` from `wiring_support`, and tests/application/test_sealed_runs_runner.py from `stage_run_support`. Their other imports stay.
   - This was done under the standing leave in CLAUDE.md for constants. The one change beyond that leave is test_shared_bodies.py (decision 14).

   Modules the test runner could not import: none. `make test` passed, so nothing fails before implementation.

   Collect-only check: I listed the `pytest --collect-only` ids of the 21 named test modules plus tests/test_shared_bodies.py, before and after the move ($TMPDIR/before has 871, $TMPDIR/after has 872). They match except for one new id, `tests/test_shared_bodies.py::test_no_test_module_holds_a_copy[test_shared_environments.py]`, which is the bodies guard's row for the new module.

   Two choices inside the Interface, open for the reviewer to judge:
   - A top-level dict that holds a name, such as `{"PATH": PATH, ...}` in tests/application/test_opencode_item.py, makes `ast.literal_eval` raise. `environment_copies` counts it as no copy, so the guard can read every file under tests/.
   - The guard's own cases read against an environment returned by a fixture, not a top-level constant. A top-level constant would be a copy that the guard finds in its own file.
   - The function's docstring is shortened from the Interface's wording to "The top-level names that `source` assigns a dict literal equal to `environment`." The original wording ran past ruff's 100-character line limit (E501).

   Smoke test 1: run by hand, it prints the two expected lines (tests/stage_run_support.py, then tests/wiring_support.py).

   `lint`: lint: green (0.6 s)
   `test`: test: green (61.7 s)
6. factory: started doing as self.
7. coder: Nothing to build. The Interface says no module under `src/factory/` changes, and the tester already did the whole move: `tests/wiring_support.py` gained `ENVIRONMENT`, the twenty modules import it, `tests/test_shared_environments.py` is the new guard, and `tests/test_shared_bodies.py` now finds a defining module by its relative path. I confirmed that `git diff main -- src` is empty and ran `make check` in the foreground: `test: green (62.3 s)`, `check: green`.

   Main choice: I left the working tree as the tester left it. I rejected touching anything under `src/` or `tests/`, because the coder never edits tests and the story has no code to add.

   Refactor: my own diff is empty, so there is nothing to refactor.

   The journal did not change what the task means, so the Description stays as it is.

   Noticed and not touched: the tester's three choices inside the Interface, which their entry leaves for the reviewer:
   - `ast.literal_eval` failing on a dict that holds a name counts as no copy.
   - The guard's cases take their environment from a fixture.
   - The docstring is shortened because of E501.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 38 known, 0 gone
8. factory: started review as self.
9. reviewer: no findings

   What I checked:
   - Criterion 1: `tests/test_shared_environments.py::test_each_shared_environment_is_assigned_in_one_module`. It has two rows over `SHARED`, and the paths are relative to `tests/` and sorted. It checks both the shared value and the exact list of modules that hold it. `SHARED` imports its values from `stage_run_support` and `wiring_support`. A grep of `tests/` finds only `tests/stage_run_support.py:21` and `tests/wiring_support.py:9` for the two values. The `/opt/guard` pair, `probe_support.py`, `test_opencode_item.py` and `test_agent_launch.py` keep their own values, as the Description says.
   - Criterion 2: `test_the_guard_counts_a_top_level_assignment_of_the_environment`. Its ten rows are exactly the criterion's ten cases: plain, other name, annotated, home first, other value, one more key, name as value, call, in a function, in a class. The rows read `environment_copies` against a fixture that returns the stated value. A top-level constant would be a copy, and the guard would find it in its own file.
   - `_literal` treats a dict that holds a name (`{"PATH": PATH}`) as no copy. That matches the Interface ("a dict literal whose `ast.literal_eval` equals"), and it lets the guard read every file, `test_opencode_item.py:14` among them.
   - Criterion 3: `tests/test_shared_bodies.py:153` now compares `path.relative_to(TESTS).as_posix()` with `SHARED.values()`. The test name and the parametrization are unchanged. Every value of `SHARED` is a module at the `tests/` root, so the result is the same for every module of today.
   - Criterion 4: the coder's entry 7 records `check: green` and `duplicates: 0 new`.
   - Criterion 5 is the documenter's.
   - Collect-only check: the tester's `$TMPDIR` lists are gone with their run. I confirmed by reading instead. Outside the new module, the diff adds or removes no `def`, `@pytest` or `pytest.param` line, so no test id changes. The only change to collection is the bodies guard's automatic new row for `test_shared_environments.py`, which matches what entry 5 reports. `pytest --collect-only` over the 22 changed test modules collects at HEAD without error.
   - Architecture and security: nothing under `src/` changes, and no marker or baseline entry is added. `wiring_support` still imports no test module. `stage_run_support` gains no import.
   - Hygiene: the Description, the Interface and the docs criterion match what was built. The tester's entry names its choices: the literal_eval fallback, the fixture, and the docstring shortened for E501. The shortened docstring keeps the meaning of the Interface's wording.

   Earlier tests (each was already on `main` and changed here):
   - tests/acceptance_walk.py: standing leave to move a shared test helper (its `ENVIRONMENT` moved to `wiring_support`)
   - tests/application/handlers/test_run.py: standing leave (`ENVIRONMENT` from `wiring_support`)
   - tests/application/test_after_agent.py: standing leave (`ENVIRONMENT` from `stage_run_support`)
   - tests/application/test_cost_image.py: standing leave (`ENVIRONMENT` from `stage_run_support`)
   - tests/application/test_costs.py: standing leave (`ENVIRONMENT` from `stage_run_support`)
   - tests/application/test_nested_repositories.py: standing leave (`ENVIRONMENT` from `stage_run_support`)
   - tests/application/test_sealed_runs.py: standing leave (`ENVIRONMENT` from `stage_run_support`)
   - tests/application/test_sealed_runs_runner.py: standing leave (now imports `ENVIRONMENT` from `stage_run_support` instead of `application.test_sealed_runs`)
   - tests/application/test_stage_finish.py: standing leave (`ENVIRONMENT` from `stage_run_support`)
   - tests/application/test_stage_launch.py: standing leave (`ENVIRONMENT` from `stage_run_support`)
   - tests/application/test_stage_run_acceptance.py: standing leave (`ENVIRONMENT` from `stage_run_support`)
   - tests/application/test_stall_labels.py: standing leave (`ENVIRONMENT` from `stage_run_support`)
   - tests/application/test_stalls.py: standing leave (`ENVIRONMENT` from `stage_run_support`)
   - tests/application/test_tick_agent_definition.py: standing leave (`ENVIRONMENT` from `wiring_support`)
   - tests/application/test_tick_project_agent.py: standing leave (now imports `ENVIRONMENT` from `wiring_support` instead of `application.test_tick_agent_definition`)
   - tests/entry/test_run.py: standing leave (`ENVIRONMENT` from `wiring_support`)
   - tests/entry/test_wiring_acceptance.py: standing leave (`ENVIRONMENT` from `wiring_support`)
   - tests/entry/test_wiring_constants.py: standing leave (`ENVIRONMENT` from `wiring_support`)
   - tests/entry/test_wiring_handlers.py: standing leave (`ENVIRONMENT` from `wiring_support`)
   - tests/entry/test_wiring_human_handlers.py: standing leave (`ENVIRONMENT` from `wiring_support`)
   - tests/entry/test_wiring_recovery.py: standing leave (`ENVIRONMENT` from `wiring_support`)
   - tests/entry/test_wiring_recovery_expired.py: standing leave (`ENVIRONMENT` from `wiring_support`)
   - tests/wiring_support.py: standing leave (the shared place gains `ENVIRONMENT`; nothing else changes)
   - tests/test_shared_bodies.py: the human's leave, F0039 `feature.md` decision 14 (only `test_no_test_module_holds_a_copy` changes, to the relative-path rule; its name and ids are kept)
10. factory: started docs as self.
11. documenter: Docs written for the docs criterion; no findings.

    Files changed (one, `docs/project-guide/README.md`, *Shared test helpers*):
    - The `stage_run_support.py` line now also names `ENVIRONMENT`, the environment the stage-run tests pass. I narrowed the guard sentence on that line: `tests/test_shared_constants.py` fails on another top-level assignment of the instance name. Before, "that value" would have read as covering `ENVIRONMENT` too.
    - The `wiring_support.py` line now names `ENVIRONMENT`, the environment the handler and wiring tests pass. It says that `tests/test_shared_environments.py` fails on another top-level assignment of either `ENVIRONMENT` value (this one or `stage_run_support.py`'s).

    I ran the docs grep from the smoke test; it prints `2` (before the story, `0`). I did not run `make check`, because I changed only a document and the factory's checks run right after this stage.

    Cross-read and found current:
    - The rest of `docs/project-guide/README.md`.
    - `README.md`.
    - `docs/operator-guide.md`.
    - `docs/decisions.md`. Its only `ENVIRONMENT` hit (line 484) is `ALLOWED_ENVIRONMENT_NAMES`, which is unrelated.
    - `docs/project-guide/watching.md`. Its text on the agent run's environment is about `agent_environment` in `src/`, which this story does not touch.

    The diff outside `factory/` and `docs/` is test-only, and no module under `src/` changed, so the cross-read found no stale name or example.

    Stale text I noticed and did not touch: none that this story touches. The night log in `docs/runs/` is the human's.

    `check`: check: green (not run again: passed on tree 26c265259365 at 2026-10-21T12:29:13Z)
    `secrets`: secrets: green (1.2 s)
    `documents`: documents ok
