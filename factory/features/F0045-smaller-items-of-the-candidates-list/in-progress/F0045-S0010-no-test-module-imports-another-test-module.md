---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 475
comments_read: [6431654376]
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
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-27T01:45:00.875448Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-27T01:45:18.671775Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-27T01:45:45.701353Z'
  stage: intake
  run: f4c3eec591bc48bfaab5591b3789b2db
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-27T01:46:06.247491Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-27T01:55:08.830973Z'
  stage: tests
  run: 127170a28c334ea1b7dab4024d4afb7e
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-27T01:55:29.515593Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-27T02:01:44.084218Z'
  stage: doing
  run: a594a84fa6174914913c429ed924c3a2
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-27T02:02:04.615749Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-27T02:03:45.805921Z'
  stage: review
  run: 07af11649747455093ff72945ed9db90
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-27T02:04:06.286791Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-27T02:04:23.044716Z'
  stage: doing
  run: a307c34b81b1462fac200edc55351100
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-27T02:04:43.501437Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-27T02:11:13.603056Z'
  stage: tests
  run: 48fc0f2d68e24d62b8f5ead4ab125bbe
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-27T02:11:33.972729Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-27T02:18:08.076395Z'
  stage: doing
  run: 351b65cb3a654627a6247c76f096700a
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-27T02:18:28.895834Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-27T02:19:24.152495Z'
  stage: review
  run: 51431cc324b7436e955bffb70183a808
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-27T02:19:44.696576Z'
  stage: docs
- number: 22
  speaker: documenter
  kind: result
  at: '2026-10-27T02:20:44.641009Z'
  stage: docs
  run: b9559810c3074f3c90491e14d9502991
---

# No test module imports another test module

## Description

About forty import lines go from one module under `tests/` into a test module (F0039-A0002, note 4; thirty-nine lines in thirty-two modules on 2026-10-26, for example `from adapters.test_claude_runtime_login import BUDGET_STOP, REPLY` or `from application import test_preflight_run`). Such an import runs the other module's setup at import, ties two stories' tests together, and turns a deleted or renamed test module into failures in modules that test something else, as F0044's removals showed. This story ends it, for the tester alone: every helper, constant, class and fixture that a module imports from a test module moves into a support module (a new one named `*_support.py`) or, for a fixture, into `tests/conftest.py`, and the defining and the importing modules use it from there; a guard, `tests/test_shared_imports.py`, keeps it so (decision 7 of `feature.md`). Every test keeps its name and what it checks. What stays: every support module and shared helper module that exists, under its name (`human_clone.py`, `recording_log.py`, `source_search.py` and the others); the guards `tests/test_shared_*.py`; every test's behaviour. No module under `src/factory/` changes.

## Interface

None under `src/factory/`, `vm/`, `template/` or `claude/`. The tester changes `tests/` only:

- A test module is a module under `tests/` whose file name begins with `test_`.
- The rule the guard checks: no module under `tests/` (test modules, support modules, `conftest.py` files) imports a test module, in any of the three forms `from <path>.test_<name> import ...` or `from test_<name> import ...`; `import <path>.test_<name>` or `import test_<name>`; and `from <path> import test_<name>` (with or without `as`, on one line or in parentheses over several).
- A name that moves keeps its meaning; a private name (`_request`) may lose its leading underscore when it moves; a fixture that moves to `tests/conftest.py` keeps its name.
- The guard `tests/test_shared_imports.py` reads every `*.py` file under `tests/` with `ast` and names each import that breaks the rule as `<file>:<line>: <module>`, the line being the first line of the import statement.

Tests (the leave is decision 30 of `feature.md`): the guard `tests/test_shared_imports.py` (new); every module under `tests/` that holds such an import, and every test module it imports from, changed as the leave says. On 2026-10-26 these modules import from a test module: `tests/adapters/test_claude_runtime_api_login.py`, `test_claude_runtime_container.py`, `test_claude_runtime_denial_paths.py`, `test_claude_runtime_provider_limit.py`, `test_claude_runtime_resume_session.py`, `test_cost_records_jsonl_denials.py`, `test_cost_records_jsonl_instance.py`, `test_cost_records_jsonl_login.py`, `test_opencode_runtime_container.py`, `test_opencode_runtime_launch.py`, `test_runtime_podman_timeout_status.py`; `tests/application/test_agent_run_probe_api_login.py`, `test_cost_instance.py`, `test_interfaces.py`, `test_known_results.py`, `test_known_results_torn.py`, `test_preflight_login_line.py`, `test_preflight_stale_main_stop.py`, `test_preflight_stops_commit.py`, `test_recording_project_commands.py`, `test_tick_project_agent.py`; `tests/domain/test_contract_provider_limit.py`, `test_section_edges.py`, `test_story_form_edges.py`; `tests/entry/test_check_documents_guide_files.py`, `test_wiring_api_login.py`, `test_wiring_container_extra.py`, `test_wiring_opencode.py`, `test_wiring_stage_environment.py`; `tests/container_extra_support.py` (its `REPLY`, F0046-S0002's review), `tests/preflight_support.py` and `tests/test_time_limits.py` (it reads the stand-ins' wait constants of test modules, which then live in support modules beside the tests that use them). The tester works from `main` as S0001 to S0009 of this feature left it and names each changed module in its entry.

## Acceptance criteria

1. The rule holds (the guard, one test over every `*.py` file under `tests/`): it finds no import of a test module, and its failure message names each one as `<file>:<line>: <module>`.
2. The guard finds every form (rows of one parametrized test over the guard's own reader, given a source text): `from adapters.test_x import A`, `from test_x import A`, `import application.test_y`, `import test_y as y`, `from adapters import test_z`, `from adapters import test_z as z` and `from adapters.test_x import (\n    A,\n    B,\n)` are each found once, naming the module; `from take_support import x`, `from testing_support import x`, `import factory.application.tick` and `from adapters import support_test` are each found nowhere. Each found import reports the line of its statement's first line (the `from` or `import` line, also for the parenthesised multi-line import, where it is line 1 of that source text) and the module.
3. The failure message renders each import as `<file>:<line>: <module>` (one test over the guard's own message builder, given a source text and a file name): for the file name `tests/adapters/test_a.py` and the source text `x = 1\nfrom adapters.test_x import A\n`, the line is `tests/adapters/test_a.py:2: adapters.test_x`.
4. `make check` stays green.
5. docs: `docs/project-guide/README.md`, *Shared test helpers*: one paragraph with the rule (no module imports a test module; what two test modules share lives in a support module, a new one named `*_support.py`, or in `tests/conftest.py`), the guard `tests/test_shared_imports.py`, and one line for each support module this story added, naming what it offers. `docs/decisions.md`: a new entry "Shared test code lives outside the test modules" (F0045-S0010; F0039-A0002's note 4, decision 7 of `feature.md` with its rejected option). `docs/operator-guide.md`, `README.md`: none.

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
4. 2026-10-27 human: 1. (a) with (b): each found import reports the line of its statement's first line (the `from` or `import` line, also for a parenthesised multi-line import) and the module, and a criterion checks that the failure message renders `<file>:<line>: <module>` for a given source text and file name.
   2. Accepted as is: the guard and `make check` are the checks for those two rules.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: it names the rule, the three import forms, the guard `tests/test_shared_imports.py` (reads every `*.py` under `tests/` with `ast`) and the modules that import a test module. It now also says that the reported line is the first line of the import statement (carried in from journal entry 4).
   - Criteria: each is testable by one test function. 1 is the rule over all files. 2 is the table of forms, found and not found, and now also the reported line and module, which covers the parenthesised multi-line form. The new 3 checks that the message renders `<file>:<line>: <module>` for a given file name and source text, with a worked example. The failing side of the rule is covered by 1, 2 and 3. The moves keep names and meaning by the leave in decision 30, and `make check` is the check for that, as the human accepted in entry 4, point 2.
   - Smoke test: both commands are runnable. The grep expects `0`. The pytest command passes no `-q` and `addopts` already sets one, so the `N passed in` line exists, and its Expect says `1`.
   - Architecture: the story changes `tests/` only, with support modules named `*_support.py` and fixtures in `conftest.py`. That matches CLAUDE.md's Tests section and puts nothing under `src/factory/`.
   - Scope: S0010 of F0045, decisions 7 and 30 of `feature.md`. The leave for the tests is given and nothing is in "Out of scope".

   Carried in from the human's entry 4, answer 1 ((a) with (b)):
   - Criterion 2: each found import reports the line of its statement's first line and the module.
   - New criterion 3, before the two closing ones: the failure message renders `<file>:<line>: <module>`. The closing criteria are now 4 (`make check`) and 5 (`docs:`).
   - Interface: the line of the guard's message is the statement's first line.

   Answer 2 (the guard and `make check` are the only checks for a moved fixture keeping its name and a private name losing its underscore) needed no edit.
7. factory: started tests as vm.
8. tester: Wrote the guard. Moved everything that modules under `tests/` imported from test modules into support modules, under the leave in decision 30. No module under `src/factory/` changed.

   Criteria → tests:
   - criterion 1: tests/test_shared_imports.py::test_no_module_under_tests_imports_a_test_module
   - criterion 2: tests/test_shared_imports.py::test_the_guard_finds_every_form_of_a_test_module_import (parametrized: the seven found forms, multi-line parenthesised one included, and the four not found)
   - criterion 3: tests/test_shared_imports.py::test_the_guard_names_each_import_by_file_line_and_module
   - criterion 4: `make check`, no test of its own
   - criterion 5: docs, for the documenter

   The guard's reader is `imported_test_modules(source) -> list[tuple[int, str]]`, giving the first line of the statement and the module. Its message builder is `import_messages(file, source)`. Both live in the guard module itself, so no module imports them.

   Files created (all under `tests/`, each named after what it now holds):
   - `agent_login_support.py`: API_LOGIN, SUBSCRIPTION, _utf_16
   - `claude_reply_support.py`: LOGIN, REPLY, BUDGET_STOP
   - `claude_resume_support.py`: LIMIT, _reply, _budget_reply, _request, _runtime, _after
   - `cost_records_support.py`: COMPLETED_LINE, REQUIRED, STARTED_AT, STARTED_AT_TEXT, STARTED_LINE, _completed, _started
   - `probe_login_support.py`: HINT, LOGIN_FILE
   - `cost_image_support.py`: _launch, _settings and the constants they use
   - `git_interface_support.py`: OPERATIONS
   - `hosting_interface_support.py`: OPERATIONS
   - `known_results_support.py`: TIME_LIMIT, DEFINITION_YAML, Rig, _answering, _result, _rig
   - `agent_definition_support.py`: BACKLOG_PATH, COMPLETED, STORY
   - `contract_login_support.py`: SCHEMAS, _committed, _values
   - `sections_support.py`: TICKS
   - `story_form_support.py`: FORM, SMOKE, _state
   - `check_documents_support.py`: MISSING_LINES
   - `wiring_login_support.py`: the wiring tests' REPLY
   - `opencode_events_support.py`: WAIT_SECONDS
   - `opencode_resume_support.py`: WAIT_SECONDS
   - `test_shared_imports.py`: the guard

   Existing support module extended: `preflight_support.py` now holds IMAGE, OTHER_IMAGE, MAKEFILE, ROLES, TOOLS, RecordingWhich, RecordingCommands, Rig and the fixtures `rig` and `red_main`, which `test_preflight_run.py` held before. I updated its docstring.

   The fixtures stayed out of `tests/conftest.py`. They went into `preflight_support.py` instead, and each test module that uses them binds them with `rig = preflight_support.rig`, the pattern those modules already used. A root conftest fixture named `rig` would reach every module, and two other rigs exist under that name.

   Private names kept their underscore, which the Interface allows.

   Earlier test modules changed:
   - tests/adapters: test_agent_launch_login, test_claude_runtime_login, test_claude_runtime_resume, test_cost_records_jsonl, test_opencode_events, test_opencode_resume_session, test_claude_runtime_api_login, test_claude_runtime_container, test_claude_runtime_denial_paths, test_claude_runtime_provider_limit, test_claude_runtime_resume_session, test_cost_records_jsonl_denials, test_cost_records_jsonl_instance, test_cost_records_jsonl_login, test_opencode_runtime_container, test_opencode_runtime_launch, test_runtime_podman_timeout_status
   - tests/application: test_agent_run_probe_login, test_cost_image, test_git_interface, test_hosting_interface, test_known_results, test_preflight_run, test_tick_agent_definition, test_agent_run_probe_api_login, test_cost_instance, test_interfaces, test_known_results_torn, test_preflight_login_line, test_preflight_stale_main_stop, test_preflight_stops_commit, test_recording_project_commands, test_tick_project_agent
   - tests/domain: test_contract_login, test_sections, test_story_form, test_contract_provider_limit, test_section_edges, test_story_form_edges
   - tests/entry: test_check_documents, test_wiring_login, test_check_documents_guide_files, test_wiring_api_login, test_wiring_container_extra, test_wiring_opencode, test_wiring_stage_environment
   - tests/ root: container_extra_support.py, preflight_support.py, test_time_limits.py

   Every test kept its name and what it checks.

   Run:
   - `make lint` and `make types` are green. I ran the types check too, since every module exists in this story.
   - The first smoke grep gives 0.
   - The single `make test` run had two failures: test_contract_login::test_the_committed_cost_record_schema_lists_the_optional_login and test_contract_provider_limit::test_the_committed_schemas_list_provider_limit_at_version_1_2, both with `FileNotFoundError: /work/src/factory/contract/...`. The cause was that `SCHEMAS` moved up one folder but its `__file__`-relative path did not. I fixed it to `Path(__file__).parent.parent`. Per the stage rules I did not re-run the tests, so this fix is unconfirmed until the factory's `make test`.

   No module failed to import. The guard tests pass already, since this story's work is the move itself, which the tester does. Nothing is left for the coder to implement.

   `lint`: lint: green (0.2 s)
   `test`: test: green (166.3 s)
9. factory: started doing as vm.
10. coder: Built nothing: this story changes `tests/` only, and the tester's entry has already done the whole move. The guard `tests/test_shared_imports.py` exists, the shared names are in the new `*_support.py` modules, and `tests/preflight_support.py` is extended. Nothing is left for the coder to do. Under the Interface no module under `src/factory/` changes, and `git diff main -- src` is empty.

    Checked:
    - `make check` is green: every target, then `test: green (166.5 s)` and `check: green` at 99.57 % coverage. This confirms the tester's fix to the `SCHEMAS` path in `tests/contract_login_support.py` (`Path(__file__).parent.parent`), which the tester had not re-run.
    - The first smoke grep returns `0`.
    - The working tree is clean, with nothing of mine to commit.

    Main choice: change no code and hand forward. The alternative I rejected was touching the tester's support modules (for example, dropping the leading underscore from the moved private names, which the Interface allows but does not require). That would be a test change, which is the tester's alone. No diff, so no refactoring.

    Noticed but did not touch:
    - The fixtures `rig` and `red_main` went into `tests/preflight_support.py`, and the modules that use them rebind them (`rig = preflight_support.rig`). The Interface says "or, for a fixture, into `tests/conftest.py`". The tester explains why they did not use conftest: a root fixture named `rig` would clash with the two other rigs. The reviewer should judge whether this meets the Interface.
    - The journal changed the Description only through intake, which already rewrote it. I rewrote nothing.

    `check`: check: green
    `duplicates`: duplicates: 2 new, 42 known, 0 gone
11. factory: started review as vm.
12. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (tests only, nothing under `src/`) against the work item.

    **Group 1 holds:**
    - Criterion 1 is `test_no_module_under_tests_imports_a_test_module`.
    - Criterion 2 is the parametrized `test_the_guard_finds_every_form_of_a_test_module_import`. It has all seven found forms, the parenthesised one reported at line 1 among them, and all four rows that must not be found: `testing_support` and `support_test` cover both sides of the `test_` prefix rule.
    - Criterion 3 is `test_the_guard_names_each_import_by_file_line_and_module`, with the exact example line.
    - The journal records `check: green` after the coder (entry 10).

    **Groups 2 and 3 hold:** the change is tests only, with no silencing marker.

    **Group 4 (quality) fails.** At round 0 a copied helper in a test file the diff adds is a finding.

    Findings:
    1. `tests/cost_image_support.py:21-71`: `WORK_ITEM`, `BRANCH`, `BACKLOG_PATH`, `PATH`, `STORY`, `CREATED` and `CREATED_LINE` are copies of `tests/stage_run_support.py:19-22,33,53-54`. All seven values are equal, and the module already imports `ENVIRONMENT, INSTANCE` from `stage_run_support`. Fix: import them from `stage_run_support` and delete the copies.
    2. `tests/agent_definition_support.py:7-36`: `BACKLOG_PATH` and `STORY` are copies of `stage_run_support.BACKLOG_PATH` and `stage_run_support.STORY` (equal values). Fix: `test_tick_agent_definition.py` and `test_tick_project_agent.py` take both from `stage_run_support`, and the support module keeps only `COMPLETED`.
    3. `tests/wiring_login_support.py:5` `REPLY` and `tests/claude_reply_support.py:8` `REPLY` are copies of `tests/adapters/claude_stand_in.py:16` `REPLY` (the same JSON). Fix: delete `wiring_login_support.py` and drop `REPLY` from `claude_reply_support.py`. The modules that import either use `adapters.claude_stand_in.REPLY` instead (the wiring tests, `container_extra_support.py`, `test_runtime_podman_timeout_status.py` and the claude runtime login, api-login and container tests). `claude_reply_support` keeps `LOGIN` and `BUDGET_STOP`.

    Points I looked at and did not count as findings:
    - The fixtures `rig` and `red_main` went into `preflight_support.py`, not `tests/conftest.py`. The Interface allows a support module as well ("moves into a support module ... or, for a fixture, into `tests/conftest.py`"), and `preflight_support` already held the fixture `failed_once` in the same pattern.
    - `opencode_events_support.py` and `opencode_resume_support.py` each hold `WAIT_SECONDS = 30`. The Interface asks for them "in support modules beside the tests that use them", and `test_time_limits.py` keeps one row for each. Merging them would change those rows.

    Earlier tests (item 6). Every file below was changed under the human's leave, decision 30 of `feature.md`, which the story names. Each change only moves names into a support module, or switches the import to one. No test was renamed and none changed what it checks.
    - tests/adapters/test_agent_launch_login.py: decision 30
    - tests/adapters/test_claude_runtime_api_login.py: decision 30
    - tests/adapters/test_claude_runtime_container.py: decision 30
    - tests/adapters/test_claude_runtime_denial_paths.py: decision 30
    - tests/adapters/test_claude_runtime_login.py: decision 30
    - tests/adapters/test_claude_runtime_provider_limit.py: decision 30
    - tests/adapters/test_claude_runtime_resume.py: decision 30
    - tests/adapters/test_claude_runtime_resume_session.py: decision 30
    - tests/adapters/test_cost_records_jsonl.py: decision 30
    - tests/adapters/test_cost_records_jsonl_denials.py: decision 30
    - tests/adapters/test_cost_records_jsonl_instance.py: decision 30
    - tests/adapters/test_cost_records_jsonl_login.py: decision 30
    - tests/adapters/test_opencode_events.py: decision 30
    - tests/adapters/test_opencode_resume_session.py: decision 30
    - tests/adapters/test_opencode_runtime_container.py: decision 30
    - tests/adapters/test_opencode_runtime_launch.py: decision 30
    - tests/adapters/test_runtime_podman_timeout_status.py: decision 30
    - tests/application/test_agent_run_probe_api_login.py: decision 30
    - tests/application/test_agent_run_probe_login.py: decision 30
    - tests/application/test_cost_image.py: decision 30
    - tests/application/test_cost_instance.py: decision 30
    - tests/application/test_git_interface.py: decision 30
    - tests/application/test_hosting_interface.py: decision 30
    - tests/application/test_interfaces.py: decision 30
    - tests/application/test_known_results.py: decision 30
    - tests/application/test_known_results_torn.py: decision 30
    - tests/application/test_preflight_login_line.py: decision 30
    - tests/application/test_preflight_run.py: decision 30
    - tests/application/test_preflight_stale_main_stop.py: decision 30
    - tests/application/test_preflight_stops_commit.py: decision 30
    - tests/application/test_recording_project_commands.py: decision 30
    - tests/application/test_tick_agent_definition.py: decision 30
    - tests/application/test_tick_project_agent.py: decision 30
    - tests/container_extra_support.py: decision 30
    - tests/domain/test_contract_login.py: decision 30
    - tests/domain/test_contract_provider_limit.py: decision 30
    - tests/domain/test_section_edges.py: decision 30
    - tests/domain/test_sections.py: decision 30
    - tests/domain/test_story_form.py: decision 30
    - tests/domain/test_story_form_edges.py: decision 30
    - tests/entry/test_check_documents.py: decision 30
    - tests/entry/test_check_documents_guide_files.py: decision 30
    - tests/entry/test_wiring_api_login.py: decision 30
    - tests/entry/test_wiring_container_extra.py: decision 30
    - tests/entry/test_wiring_login.py: decision 30
    - tests/entry/test_wiring_opencode.py: decision 30
    - tests/entry/test_wiring_stage_environment.py: decision 30
    - tests/preflight_support.py: decision 30
    - tests/test_time_limits.py: decision 30

    Every fix is a test change, so it is the tester's (R9). It falls under decision 30 and the standing leave for shared helpers.
13. factory: started doing as vm.
14. coder: Round 1: changed no code. All three of the reviewer's findings in entry 12 are changes to tests. They fall under decision 30 of `feature.md` and the standing leave for shared helpers, so they are the tester's (R9).

    Changes for the tester, as entry 12 names them:
    1. `tests/cost_image_support.py`: delete the copies of `WORK_ITEM`, `BRANCH`, `BACKLOG_PATH`, `PATH`, `STORY`, `CREATED` and `CREATED_LINE`, and import them from `tests/stage_run_support.py`.
    2. `tests/agent_definition_support.py`: drop `BACKLOG_PATH` and `STORY`, so the module keeps only `COMPLETED`. `test_tick_agent_definition.py` and `test_tick_project_agent.py` take `BACKLOG_PATH` and `STORY` from `stage_run_support`.
    3. Delete `tests/wiring_login_support.py` and drop `REPLY` from `tests/claude_reply_support.py`, which keeps `LOGIN` and `BUDGET_STOP`. Every module that imported either `REPLY` uses `adapters.claude_stand_in.REPLY` instead. These are the wiring tests, `container_extra_support.py`, `test_runtime_podman_timeout_status.py`, and the claude runtime login, api-login and container tests.

    Main choice: send the work item to the tester and leave the support modules alone. I rejected applying the fixes myself because the coder never edits tests.

    Nothing under `src/factory/` changes, so there was nothing to refactor. The journal did not change the Description, which the intake already rewrote.
15. factory: started tests as vm.
16. tester: Round 1, an approved test change. I made the three changes from the coder's entry 14, which carries the reviewer's findings in entry 12, under decision 30 of `feature.md` and the standing leave for shared helpers. Each change only removes a copied helper and imports the shared one. No test was renamed and none checks anything different. The guard tests did not change.

    1. `tests/cost_image_support.py`: removed the copies of `WORK_ITEM`, `BRANCH`, `BACKLOG_PATH`, `PATH`, `STORY`, `CREATED` and `CREATED_LINE`. It now imports them from `tests/stage_run_support.py`. I also dropped the two imports that were no longer used (`branch_name`, `JournalRecord`).
    2. `tests/agent_definition_support.py`: removed `BACKLOG_PATH` and `STORY`, so only `COMPLETED` is left, and updated its docstring. `tests/application/test_tick_agent_definition.py` and `tests/application/test_tick_project_agent.py` now take `BACKLOG_PATH` and `STORY` from `stage_run_support`.
    3. Deleted `tests/wiring_login_support.py`, and removed `REPLY` from `tests/claude_reply_support.py`, which keeps `LOGIN` and `BUDGET_STOP` (docstring updated). These modules now import `REPLY` from `adapters.claude_stand_in`:
       - `tests/entry/test_wiring_login.py`, `test_wiring_api_login.py`, `test_wiring_container_extra.py`, `test_wiring_stage_environment.py`
       - `tests/container_extra_support.py` (as `CLAUDE_REPLY`)
       - `tests/adapters/test_runtime_podman_timeout_status.py`, `test_claude_runtime_login.py`, `test_claude_runtime_api_login.py`, `test_claude_runtime_container.py`

    Criteria → tests (unchanged since entry 8):
    - criterion 1: tests/test_shared_imports.py::test_no_module_under_tests_imports_a_test_module
    - criterion 2: tests/test_shared_imports.py::test_the_guard_finds_every_form_of_a_test_module_import
    - criterion 3: tests/test_shared_imports.py::test_the_guard_names_each_import_by_file_line_and_module
    - criterion 4: `make check`
    - criterion 5: docs, for the documenter

    No files created this round; one deleted (`tests/wiring_login_support.py`). Every module imported.

    Run: `make lint` is green. One run of `make test` was green: `test: green (167.0 s)`, coverage 99.57 %.

    `lint`: lint: green (0.2 s)
    `test`: test: green (166.7 s)
17. factory: started doing as vm.
18. coder: Round 1: I changed no code. This story changes `tests/` only. The tester made all three fixes from the reviewer's entry 12, which entry 14 carried over, and they are in place:
    - `tests/cost_image_support.py` takes the shared constants from `tests/stage_run_support.py`.
    - `tests/agent_definition_support.py` keeps only `COMPLETED`.
    - `tests/wiring_login_support.py` is deleted, and `tests/claude_reply_support.py` keeps only `LOGIN` and `BUDGET_STOP`, so `REPLY` comes from `adapters.claude_stand_in`.

    `git diff main -- src` is empty.

    Checked:
    - `make check` is green: every target, then `test: green (166.6 s)` and `check: green`.
    - The first smoke grep returns `0`.
    - The working tree is clean. I had nothing to refactor.

    Main choice: hand forward with no change of my own. I rejected touching the support modules any further (for example, dropping the leading underscore from the moved private names, which the Interface allows but does not require), because that is a test change and the tester's alone.

    Noticed but did not touch: my first `make check` run stopped at `make types` with `make: *** [Makefile:38: types] Error 139`. That is a segfault in the mypy process, and it printed no type error. Run on its own right after, `make types` was green ("Success: no issues found in 788 source files"), and the next full `make check` was green. It looks like a one-off crash of the tool, not something this story caused.

    The journal did not change the Description beyond what intake already rewrote.

    `check`: check: green
    `duplicates`: duplicates: 2 new, 42 known, 0 gone
19. factory: started review as vm.
20. reviewer: Round 1. I reviewed `git diff main...HEAD -- . ':!factory'` against the work item. The diff changes only `tests/`; `git diff main...HEAD -- src vm template claude` is empty.

    no findings

    - Group 1 holds. Criterion 1 is `tests/test_shared_imports.py::test_no_module_under_tests_imports_a_test_module`. Criterion 2 is the parametrized `test_the_guard_finds_every_form_of_a_test_module_import`: it has all seven found forms, the parenthesised one reported at line 1 among them, and the four rows that must not be found, so both sides of the `test_` prefix rule are covered. Criterion 3 is `test_the_guard_names_each_import_by_file_line_and_module`, with the exact example line from the criterion. The reader `imported_test_modules` uses `ast` and reports `node.lineno`, which is the statement's first line, as the Interface says. The journal records `check: green` after the coder (entry 18).
    - Groups 2 and 3 hold: the change is tests only, with no silencing marker.
    - Group 4 holds. The three round-0 findings (entry 12) are fixed, as the tester's entry 16 says:
      - `tests/cost_image_support.py` imports `WORK_ITEM`, `BRANCH`, `BACKLOG_PATH`, `PATH`, `STORY`, `CREATED` and `CREATED_LINE` from `stage_run_support`.
      - `tests/agent_definition_support.py` keeps only `COMPLETED`.
      - `tests/wiring_login_support.py` is deleted, and `REPLY` now comes from `adapters.claude_stand_in`, whose value I checked is the same JSON.
    - Group 5 holds. The journal explains the main choice and what was rejected: the fixtures `rig` and `red_main` went to `preflight_support.py` rather than `tests/conftest.py`, to avoid a root `rig` clashing with the other two rigs. The Description and the docs criterion match what was built.

    Earlier tests (item 6). For every changed file I compared the `def test_` names on `main` with those on the branch, and they are the same in each. Each change only moves names into a support module or switches the import to one. Every file below was changed under the human's leave, decision 30 of `feature.md`, which the story names (the round-1 helper removals also fall under the standing leave for shared helpers):
    - tests/adapters/test_agent_launch_login.py: decision 30
    - tests/adapters/test_claude_runtime_api_login.py: decision 30
    - tests/adapters/test_claude_runtime_container.py: decision 30
    - tests/adapters/test_claude_runtime_denial_paths.py: decision 30
    - tests/adapters/test_claude_runtime_login.py: decision 30
    - tests/adapters/test_claude_runtime_provider_limit.py: decision 30
    - tests/adapters/test_claude_runtime_resume.py: decision 30
    - tests/adapters/test_claude_runtime_resume_session.py: decision 30
    - tests/adapters/test_cost_records_jsonl.py: decision 30
    - tests/adapters/test_cost_records_jsonl_denials.py: decision 30
    - tests/adapters/test_cost_records_jsonl_instance.py: decision 30
    - tests/adapters/test_cost_records_jsonl_login.py: decision 30
    - tests/adapters/test_opencode_events.py: decision 30
    - tests/adapters/test_opencode_resume_session.py: decision 30
    - tests/adapters/test_opencode_runtime_container.py: decision 30
    - tests/adapters/test_opencode_runtime_launch.py: decision 30
    - tests/adapters/test_runtime_podman_timeout_status.py: decision 30
    - tests/application/test_agent_run_probe_api_login.py: decision 30
    - tests/application/test_agent_run_probe_login.py: decision 30
    - tests/application/test_cost_image.py: decision 30
    - tests/application/test_cost_instance.py: decision 30
    - tests/application/test_git_interface.py: decision 30
    - tests/application/test_hosting_interface.py: decision 30
    - tests/application/test_interfaces.py: decision 30
    - tests/application/test_known_results.py: decision 30
    - tests/application/test_known_results_torn.py: decision 30
    - tests/application/test_preflight_login_line.py: decision 30
    - tests/application/test_preflight_run.py: decision 30
    - tests/application/test_preflight_stale_main_stop.py: decision 30
    - tests/application/test_preflight_stops_commit.py: decision 30
    - tests/application/test_recording_project_commands.py: decision 30
    - tests/application/test_tick_agent_definition.py: decision 30
    - tests/application/test_tick_project_agent.py: decision 30
    - tests/container_extra_support.py: decision 30
    - tests/domain/test_contract_login.py: decision 30
    - tests/domain/test_contract_provider_limit.py: decision 30
    - tests/domain/test_section_edges.py: decision 30
    - tests/domain/test_sections.py: decision 30
    - tests/domain/test_story_form.py: decision 30
    - tests/domain/test_story_form_edges.py: decision 30
    - tests/entry/test_check_documents.py: decision 30
    - tests/entry/test_check_documents_guide_files.py: decision 30
    - tests/entry/test_wiring_api_login.py: decision 30
    - tests/entry/test_wiring_container_extra.py: decision 30
    - tests/entry/test_wiring_login.py: decision 30
    - tests/entry/test_wiring_opencode.py: decision 30
    - tests/entry/test_wiring_stage_environment.py: decision 30
    - tests/preflight_support.py: decision 30
    - tests/test_time_limits.py: decision 30
21. factory: started docs as vm.
22. documenter: Round 1. I wrote the documentation the docs criterion asks for. I changed documents only, so I did not run `make check`. `make documents` printed `documents ok`.

    Files changed:
    - `docs/project-guide/README.md`, *Shared test helpers*: a paragraph with the rule (no module imports a test module; shared code goes in a `*_support.py` module or `tests/conftest.py`) and the guard `tests/test_shared_imports.py`. It lists the new support modules, one line each: agent_definition, agent_login, check_documents, claude_reply, claude_resume, contract_login, cost_image, cost_records, git_interface, hosting_interface, known_results, opencode_events, opencode_resume, probe_login, sections and story_form. The list follows the files as they are now: `agent_definition_support.py` holds only `COMPLETED`, `claude_reply_support.py` holds `LOGIN` and `BUDGET_STOP`, and `wiring_login_support.py` is gone. I also rewrote the `preflight_support.py` line, which still said it held only `fail_once` and `failed_once`. It now lists the rig, the constants and the fixtures `rig` and `red_main`.
    - `docs/decisions.md`: a new entry, "Shared test code lives outside the test modules". It has the decision, the reason, the rejected `*_support.py`-only rule from the candidates list, and why `rig` and `red_main` stayed out of `conftest.py`.

    Cross-read and found current: `README.md` and `docs/operator-guide.md` (the criterion says none; nothing in the diff touches them), and the project guide index lines outside *Shared test helpers*. The `conftest.py` line is unchanged, since the story added no fixture there. I checked every module name and constant I wrote against the files on the branch.

    Stale text I saw and did not touch: nothing found. The diff changes `tests/` only, and `git diff main...HEAD -- src` shows no change, so no code finding.

    `check`: check: green (not run again: passed on tree 457615391f27 at 2026-10-27T02:15:10Z)
    `secrets`: secrets: green (1.7 s)
    `documents`: documents ok
