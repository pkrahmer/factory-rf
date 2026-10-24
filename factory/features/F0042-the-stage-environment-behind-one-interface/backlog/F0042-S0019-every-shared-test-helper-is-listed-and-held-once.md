# Every shared test helper is listed and held once

<!-- proposed by feature acceptance of 2026-10-24; refine before starting -->

## Description

The project guide's *Shared test helpers* list (`docs/project-guide/README.md`) is where a tester looks before writing a helper: "Every module `tests/*.py` whose name does not start with `test_`". Seven such modules have no entry. One is F0042's own (`stall_support.py`, S0013). The other six are older: `home_files_support.py`, `leftovers_runtime_support.py`, `leftovers_support.py`, `root_support.py`, `time_limits.py` and `torn_record_support.py`. Three stage-test values are still assigned at top level in many test modules, although each already has a shared home or is a copy of one: the agent's text `"written by the agent\n"` (10 modules, `take_support.py` among them), the path `"tests/test_a.py"` (6 modules, under the names `INSIDE`, `WRITTEN` and `AGENT_FILE`) and the path `"notes.md"` (7 modules). F0042's tests added six of those copies: `stall_support.py`, `test_stage_environment.py`, `test_stage_environment_calls.py` and `test_stall_container.py`. This story moves each value to one module, guards that it stays there as `tests/test_shared_constants.py` already guards the instance name, and completes the list. It works under `CLAUDE.md`'s standing leave to move a shared test helper. Every earlier test keeps its name and checks the same thing. Nothing under `src/` changes. It is for the testers and reviewers of later stories, who otherwise copy these values again.

## Interface

None under `src/factory/`: the tester's work and the documenter's only.

- `tests/take_support.py` stays the one home of `AGENT_TEXT = "written by the agent\n"`.
- `tests/stage_run_support.py` becomes the one home of `INSIDE = "tests/test_a.py"` and `NOTES = "notes.md"`. Today `tests/container_support.py` holds them. `stage_run_support.py` imports neither `take_support` nor `container_support`, so no import cycle arises. Under `mypy --strict` (no implicit re-export), a test module that imports `INSIDE` or `NOTES` imports them from `stage_run_support`.
- `tests/search_support.py` gains the guard's reader. Today `tests/test_shared_constants.py` holds it as `instance_copies`; the standing leave moves it here, and `test_shared_constants.py` uses it from here:

  ```python
  def top_level_copies(source: str, value: str) -> list[str]:
      """The names that a top-level assignment in `source` gives the string `value`."""
  ```

- `tests/test_shared_stage_constants.py` (new) is the guard. It has one parametrized test whose rows are the three values. For each value, the modules under `tests/` that assign it at top level, under any name, are exactly its home.
- The earlier modules that hold a copy import the value from its home and drop their copy, under the standing leave. A module that names the value differently (`WRITTEN`, `AGENT_FILE`) uses the home's name in its place. No test is renamed.

## Acceptance criteria

1. `tests/test_shared_stage_constants.py` passes. Under `tests/`, `"written by the agent\n"` is assigned at top level only in `take_support.py`, and `"tests/test_a.py"` and `"notes.md"` only in `stage_run_support.py`. With a second top-level assignment of any of the three values added to any test module, under any name, its row fails and names that module.
2. `top_level_copies` counts a plain and an annotated top-level assignment, under any name. It counts no assignment of another value, no name used as a value, and no assignment inside a function or a class: the same seven rows as `tests/test_shared_constants.py::test_the_guard_counts_a_top_level_assignment_of_the_instance_name`, whose test keeps its name and its rows.
3. Every test that existed before this story still exists under its name and passes. The tester's entry names each earlier test file it changed.
4. `make check` stays green.
5. docs: in `docs/project-guide/README.md`, *Shared test helpers*, the documenter adds one entry each for `home_files_support.py`, `leftovers_runtime_support.py`, `leftovers_support.py`, `root_support.py`, `stall_support.py`, `time_limits.py` and `torn_record_support.py`, each from its module's docstring and its public names. The `stage_run_support.py` entry gains `INSIDE` and `NOTES`, and the `container_support.py` entry no longer claims them. The `take_support.py` and `search_support.py` entries name the guard `tests/test_shared_stage_constants.py` and `top_level_copies`. Afterwards every module `tests/*.py` whose name does not start with `test_` has an entry.

## Smoke test

```bash
uv run pytest tests/test_shared_stage_constants.py tests/test_shared_constants.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: 1

```bash
grep -rlE '^[A-Za-z_]+(: str)? = "(written by the agent\\n|tests/test_a\.py|notes\.md)"$' tests | sort
```
Expect: two lines, `tests/stage_run_support.py` and `tests/take_support.py`.

```bash
for f in tests/*.py; do b=$(basename "$f"); case "$b" in test_*|__init__.py) continue;; esac; grep -q "\`$b\`" docs/project-guide/README.md || echo "$b"; done | wc -l
```
Expect: 0

## Journal
