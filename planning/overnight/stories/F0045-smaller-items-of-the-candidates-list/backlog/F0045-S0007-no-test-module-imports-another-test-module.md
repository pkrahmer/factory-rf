# No test module imports another test module

## Description

About seventy imports go from one module under `tests/` into a test module (F0039-A0002, note 4, counted about forty-five; seventy-three import lines on 2026-10-24, for example `from adapters.test_claude_runtime_login import BUDGET_STOP, REPLY` or `from application.test_preflight_run import RecordingCommands`). Such an import runs the other module's tests' setup at import, ties two stories' tests together, and turns a deleted or renamed test module into failures in modules that test something else (F0044 deletes several such modules). This story ends it, for the tester alone: every helper, constant, class and fixture that a module imports from a test module moves into a support module (a new one named `*_support.py`) or, for a fixture, into `tests/conftest.py`, and the defining and the importing modules use it from there; a guard, `tests/test_shared_imports.py`, keeps it so (decision 7 of `feature.md`). Every test keeps its name and what it checks. What stays: every support module and shared helper module that exists, under its name (`human_clone.py`, `recording_log.py`, `source_search.py` and the others); the six guards `tests/test_shared_*.py`; every test's behaviour. No module under `src/factory/` changes.

## Interface

None under `src/factory/`, `vm/`, `template/` or `claude/`. The tester changes `tests/` only:

- A test module is a module under `tests/` whose file name begins with `test_`.
- The rule the guard checks: no module under `tests/` (test modules, support modules, `conftest.py` files) imports a test module, in any of the three forms `from <path>.test_<name> import ...` or `from test_<name> import ...`, `import <path>.test_<name>` or `import test_<name>`, and `from <path> import test_<name>` (with or without `as`, on one line or in parentheses over several).
- A name that moves keeps its meaning; a private name (`_request`, `_sudo_calls`) may lose its leading underscore when it moves; a fixture that moves to `tests/conftest.py` keeps its name.
- The guard `tests/test_shared_imports.py` reads every `*.py` file under `tests/` with `ast` and names each import that breaks the rule as `<file>:<line>: <module>`.

Tests (the leave is decision 22 of `feature.md`): the guard `tests/test_shared_imports.py` (new); every module under `tests/` that holds such an import today, and every test module it imports from, changed as the leave says. On 2026-10-24 these import from test modules: `tests/adapters/test_claude_runtime_api_login.py`, `test_claude_runtime_container.py`, `test_claude_runtime_denial_paths.py`, `test_claude_runtime_login.py`, `test_claude_runtime_no_hook.py`, `test_claude_runtime_provider_limit.py`, `test_claude_runtime_resume_session.py`, `test_cost_records_jsonl_denials.py`, `test_cost_records_jsonl_instance.py`, `test_cost_records_jsonl_login.py`, `test_opencode_runtime.py`, `test_opencode_runtime_container.py`, `test_opencode_runtime_launch.py`, `test_runtime_podman_timeout_status.py`; `tests/application/test_agent_run_probe_api_login.py`, `test_cost_instance.py`, `test_interfaces.py`, `test_known_results.py`, `test_known_results_torn.py`, `test_preflight_login_line.py`, `test_preflight_stale_main_stop.py`, `test_preflight_stops_commit.py`, `test_recording_project_commands.py`, `test_tick_project_agent.py`; `tests/domain/test_contract_provider_limit.py`, `test_section_edges.py`, `test_story_form_edges.py`; `tests/entry/test_check_documents_guide_files.py`, `test_wiring_api_login.py`, `test_wiring_login.py`, `test_wiring_opencode.py`, `test_wiring_provider_limit.py`, `test_wiring_stage_environment.py`; `tests/test_time_limits.py` (it reads the stand-ins' `WAIT_SECONDS` and `PAST_LIMIT_SECONDS` of four test modules, which then live in support modules beside the tests that use them); and `tests/preflight_support.py`; F0044 deletes or changes some of them and their sources (among them `tests/adapters/test_claude_runtime_os_user.py`, which sixteen of them import), so the tester works from `main` as F0044 and S0001 to S0006 of this feature left it and names each changed module in its entry.

## Acceptance criteria

1. The rule holds (the guard, one test over every `*.py` file under `tests/`): it finds no import of a test module, and its failure message would name each one as `<file>:<line>: <module>`.
2. The guard finds every form (rows of one parametrized test over the guard's own reader, given a source text): `from adapters.test_x import A`, `from test_x import A`, `import application.test_y`, `import test_y as y`, `from adapters import test_z`, and `from adapters.test_x import (\n    A,\n    B,\n)` are each found once, naming the module; `from take_support import x`, `from testing_support import x`, `import factory.application.tick` and `from adapters import support_test` are each found nowhere.
3. `make check` stays green.
4. docs: `docs/project-guide/README.md`, *Shared test helpers*: one paragraph with the rule (no module imports a test module; what two test modules share lives in a support module, a new one named `*_support.py`, or in `tests/conftest.py`), the guard `tests/test_shared_imports.py`, and one line for each support module this story added, naming what it offers. `docs/decisions.md`: a new entry "Shared test code lives outside the test modules" (F0045-S0007; F0039-A0002's note 4, decision 7 of `feature.md` with its rejected option). `docs/operator-guide.md`, `README.md`: none.

## Smoke test

```bash
grep -rnE '^[[:space:]]*(from[[:space:]]+([A-Za-z_][A-Za-z0-9_]*\.)*test_[A-Za-z0-9_]*[[:space:]]+import|import[[:space:]]+([A-Za-z_][A-Za-z0-9_]*\.)*test_[A-Za-z0-9_]*|from[[:space:]]+[A-Za-z_][A-Za-z0-9_.]*[[:space:]]+import[[:space:]]+\(?[[:space:]]*test_)' tests --include='*.py' | wc -l
```
Expect: `0`

```bash
uv run pytest tests/test_shared_imports.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

## Journal
