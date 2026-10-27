---
stage: intake
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 475
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-27T01:42:18.405875Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-27T01:42:18.411472Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-27T01:42:40.718406Z'
  stage: intake
  run: 5339f737007d4e17a62fa87fd1252819
  blocked: question
---

# No test module imports another test module

## Description

About forty import lines go from one module under `tests/` into a test module (F0039-A0002, note 4; thirty-nine lines in thirty-two modules on 2026-10-26, for example `from adapters.test_claude_runtime_login import BUDGET_STOP, REPLY` or `from application import test_preflight_run`). Such an import runs the other module's setup at import, ties two stories' tests together, and turns a deleted or renamed test module into failures in modules that test something else, as F0044's removals showed. This story ends it, for the tester alone: every helper, constant, class and fixture that a module imports from a test module moves into a support module (a new one named `*_support.py`) or, for a fixture, into `tests/conftest.py`, and the defining and the importing modules use it from there; a guard, `tests/test_shared_imports.py`, keeps it so (decision 7 of `feature.md`). Every test keeps its name and what it checks. What stays: every support module and shared helper module that exists, under its name (`human_clone.py`, `recording_log.py`, `source_search.py` and the others); the guards `tests/test_shared_*.py`; every test's behaviour. No module under `src/factory/` changes.

## Interface

None under `src/factory/`, `vm/`, `template/` or `claude/`. The tester changes `tests/` only:

- A test module is a module under `tests/` whose file name begins with `test_`.
- The rule the guard checks: no module under `tests/` (test modules, support modules, `conftest.py` files) imports a test module, in any of the three forms `from <path>.test_<name> import ...` or `from test_<name> import ...`; `import <path>.test_<name>` or `import test_<name>`; and `from <path> import test_<name>` (with or without `as`, on one line or in parentheses over several).
- A name that moves keeps its meaning; a private name (`_request`) may lose its leading underscore when it moves; a fixture that moves to `tests/conftest.py` keeps its name.
- The guard `tests/test_shared_imports.py` reads every `*.py` file under `tests/` with `ast` and names each import that breaks the rule as `<file>:<line>: <module>`.

Tests (the leave is decision 30 of `feature.md`): the guard `tests/test_shared_imports.py` (new); every module under `tests/` that holds such an import, and every test module it imports from, changed as the leave says. On 2026-10-26 these modules import from a test module: `tests/adapters/test_claude_runtime_api_login.py`, `test_claude_runtime_container.py`, `test_claude_runtime_denial_paths.py`, `test_claude_runtime_provider_limit.py`, `test_claude_runtime_resume_session.py`, `test_cost_records_jsonl_denials.py`, `test_cost_records_jsonl_instance.py`, `test_cost_records_jsonl_login.py`, `test_opencode_runtime_container.py`, `test_opencode_runtime_launch.py`, `test_runtime_podman_timeout_status.py`; `tests/application/test_agent_run_probe_api_login.py`, `test_cost_instance.py`, `test_interfaces.py`, `test_known_results.py`, `test_known_results_torn.py`, `test_preflight_login_line.py`, `test_preflight_stale_main_stop.py`, `test_preflight_stops_commit.py`, `test_recording_project_commands.py`, `test_tick_project_agent.py`; `tests/domain/test_contract_provider_limit.py`, `test_section_edges.py`, `test_story_form_edges.py`; `tests/entry/test_check_documents_guide_files.py`, `test_wiring_api_login.py`, `test_wiring_container_extra.py`, `test_wiring_opencode.py`, `test_wiring_stage_environment.py`; `tests/container_extra_support.py` (its `REPLY`, F0046-S0002's review), `tests/preflight_support.py` and `tests/test_time_limits.py` (it reads the stand-ins' wait constants of test modules, which then live in support modules beside the tests that use them). The tester works from `main` as S0001 to S0009 of this feature left it and names each changed module in its entry.

## Acceptance criteria

1. The rule holds (the guard, one test over every `*.py` file under `tests/`): it finds no import of a test module, and its failure message names each one as `<file>:<line>: <module>`.
2. The guard finds every form (rows of one parametrized test over the guard's own reader, given a source text): `from adapters.test_x import A`, `from test_x import A`, `import application.test_y`, `import test_y as y`, `from adapters import test_z`, `from adapters import test_z as z` and `from adapters.test_x import (\n    A,\n    B,\n)` are each found once, naming the module; `from take_support import x`, `from testing_support import x`, `import factory.application.tick` and `from adapters import support_test` are each found nowhere.
3. `make check` stays green.
4. docs: `docs/project-guide/README.md`, *Shared test helpers*: one paragraph with the rule (no module imports a test module; what two test modules share lives in a support module, a new one named `*_support.py`, or in `tests/conftest.py`), the guard `tests/test_shared_imports.py`, and one line for each support module this story added, naming what it offers. `docs/decisions.md`: a new entry "Shared test code lives outside the test modules" (F0045-S0010; F0039-A0002's note 4, decision 7 of `feature.md` with its rejected option). `docs/operator-guide.md`, `README.md`: none.

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

1. 2026-10-27 human: created.
2. factory: started intake as vm.
3. intake: 1. Criterion 2 does not test the `<file>:<line>: <module>` format that the Interface and criterion 1 promise. Criterion 2 only says each form is "found once, naming the module". Nothing fixes what the guard's reader returns (a file, a line and a module?), and nothing checks that the line is right, for example for the parenthesised multi-line `from adapters.test_x import (\n A,\n B,\n)`, where the line could be the `from` line or a name's line. Two testers would read this differently and both would pass. Options: (a) add to criterion 2 that each found import reports its line (the line of the `from` or `import` statement) and the module, and add a criterion that the failure message renders `<file>:<line>: <module>` for a given source text and file name. (b) Say that the line is the statement's first line. I would choose (a) with (b).
   2. Smaller point: the Interface says a moved fixture "keeps its name", and a moved private name "may lose its underscore". No criterion covers either. If the guard and `make check` are meant to be the only checks, please say so. I would accept that as is, and this is not blocking.

   Everything else is fine, so only question 1 blocks acceptance.
   - The format check passed.
   - The Interface names the modules and the rule.
   - The architecture and scope fit `feature.md` (S0010, decisions 7 and 30, and the leave is given).
   - The smoke tests are runnable. `-q` is already set in `addopts`, and the second smoke test passes none, so its `passed in` line exists.
   - The failing side of the rule is covered by criterion 1.
