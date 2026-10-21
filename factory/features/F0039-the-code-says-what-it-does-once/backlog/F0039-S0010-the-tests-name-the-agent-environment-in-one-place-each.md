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
