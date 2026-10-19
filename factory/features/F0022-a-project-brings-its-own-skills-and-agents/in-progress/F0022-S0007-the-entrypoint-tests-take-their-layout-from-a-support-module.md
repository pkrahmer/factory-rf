---
stage: tests
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 304
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T23:48:02.775730Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T23:48:02.782503Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T23:48:19.691179Z'
  stage: intake
  run: c3da9f350a024dc5a78ae27a146f781b
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T23:48:40.568999Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T23:51:11.795297Z'
  stage: tests
  run: f87e82b61e41442f8745d4a2eed1c954
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T23:51:32.670300Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T23:53:22.145701Z'
  stage: doing
  run: 21d52952865743fba045932c744cb832
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T23:53:43.017934Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T23:54:22.068497Z'
  stage: review
  run: 8001e0460f66400d901e3e72b34c0cca
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T23:54:42.605637Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-19T23:54:56.737608Z'
  stage: doing
  run: 48c3dc4f5be848bbbe1db70d5b025e69
---

# The entrypoint tests take their layout from a support module

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0022-S0005 moved the entrypoint's `layout` fixture into `tests/conftest.py` as `image_layout`. The fixture's class stayed in a test module: the conftest imports `from test_entrypoint import Layout as ImageLayout`. The coder of S0005 (entries 7 and 15) and its reviewer (entries 9 and 17) each noted this and left it to a later story. Two more test modules also import from that test module:
- `tests/test_agent_home_ownership.py` imports `AGENT_TEXT` and `Layout`.
- `tests/test_entrypoint_skills.py` imports `Layout` and the private `_texts`.

So every test session imports `test_entrypoint` through the conftest. A rename in that test module breaks the whole suite at collection, and a private helper is used across modules. S0005's own `test_the_image_layout_fixture_returns_the_entrypoints_layout` pins the conftest's import line word for word.

This story moves the shared parts to a support module, `tests/entrypoint_support.py`, and the importers follow. Every earlier test keeps its name and checks the same thing. Nothing under `src/` changes.

## Interface

No module under `src/factory/` changes.

Tests. The tester makes the moves under the standing leave of `CLAUDE.md` (*Tests*); the one change of a check needs the leave below.
- `tests/entrypoint_support.py` (new) holds:
  - `Layout`, with every constant it uses (`ROOT`, `ENTRYPOINT`, `SYSTEM_PATH`, `AGENT_TEXT`, `SETTINGS_TEXT`), each exactly as `tests/test_entrypoint.py` holds it today;
  - `STAMP`, `STAMPED`;
  - `texts(output: str) -> list[str]`, today's `_texts` under a public name, with the same body.
- `tests/test_entrypoint.py`, `tests/test_agent_home_ownership.py` and `tests/test_entrypoint_skills.py` import what they use from `entrypoint_support`. None keeps its own copy, and no module under `tests/` imports from `test_entrypoint`. In `test_a_missing_image_file_ends_the_run_with_one_line_before_the_instance`, the local variable `texts` is renamed `lines`, because it would shadow the imported `texts` (`UnboundLocalError`); the test checks the same thing.
- `tests/conftest.py`: the import becomes `from entrypoint_support import Layout as ImageLayout`. The `image_layout` fixture is otherwise unchanged.
- `tests/test_entrypoint_support.py` (new): the one test of criterion 2. It leaves itself out of its search, as `tests/test_shared_test_helpers.py` does, and changes no earlier test.
- `tests/test_shared_test_helpers.py` (F0022-S0005's): in `test_the_image_layout_fixture_returns_the_entrypoints_layout`, the expected import line becomes `"from entrypoint_support import Layout as ImageLayout\n"`. The test keeps its name, and nothing else in the module changes. This is a change of what an earlier test checks, so it needs the human's leave: a bullet for S0007 in decision 14 of `feature.md`, added before the story starts.

## Acceptance criteria

1. Every test function of the five changed test modules keeps its name and its parametrize ids. The modules are `tests/test_entrypoint.py`, `tests/test_agent_home_ownership.py`, `tests/test_entrypoint_skills.py`, `tests/test_shared_test_helpers.py`, and `tests/conftest.py` through its fixture users. `pytest --collect-only` lists the same test ids for them before and after the change.
2. One test in `tests/test_entrypoint_support.py`, over every `*.py` under `tests/`: `class Layout:` is defined in exactly two modules, `tests/confine_support.py` (the confinement tests' own layout, which this story leaves as it is) and `tests/entrypoint_support.py`; no module contains `from test_entrypoint import`; and `def _texts(output` appears in no module (`tests/application/test_tick.py` keeps its own `_texts(lines`).
3. `tests/conftest.py` holds the line `from entrypoint_support import Layout as ImageLayout`. `test_the_image_layout_fixture_returns_the_entrypoints_layout` passes against it and would fail against the old line.
4. `make check` stays green.
5. docs: none. No behaviour changes, and no document names these test helpers.

## Smoke test

```bash
grep -rlF --include='*.py' 'class Layout:' tests | sort
```
Expect: two lines, `tests/confine_support.py` and then `tests/entrypoint_support.py`

```bash
grep -rlF 'from test_entrypoint import' tests | wc -l
```
Expect: `0`

```bash
uv run pytest tests/test_entrypoint.py tests/test_agent_home_ownership.py tests/test_entrypoint_skills.py tests/test_shared_test_helpers.py >/dev/null 2>&1; echo "exit $?"
```
Expect: `exit 0`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules and contents: `tests/entrypoint_support.py` (`Layout` with its five constants, `STAMP`, `STAMPED`, `texts(output: str) -> list[str]` with `_texts`'s body), the three importers, the conftest import line, the `texts`→`lines` rename that avoids the `UnboundLocalError`, and the one changed check in `tests/test_shared_test_helpers.py`. No `src/` change. The leave for that check is present as the S0007 bullet in decision 14 of `feature.md`. Its quoted line has a real line break where the story writes `\n`; the story's `"...ImageLayout\n"` is the reading to use.
   Criteria: 1 is checkable by comparing `pytest --collect-only` ids before and after. 2 is one test with both sides: `class Layout:` in exactly the two named modules, no `from test_entrypoint import`, no `def _texts(output`, with the `tests/application/test_tick.py` exception stated. 3 pins the import line, and the old line must fail it. 4 is `make check`. 5 is docs: none. Every Interface rule has a criterion on both sides.
   Smoke test: three commands (a grep with sort, a grep with a count, a pytest run with its exit code). All are runnable, and each Expect line is checkable: two sorted paths, `0`, `exit 0`.
   Architecture: tests-only change that follows the CLAUDE.md standing leave on shared helpers (support module at the `tests/` root, tester makes the move). The layers are untouched.
   Scope: it stays inside the feature's "tests named in decision 14" scope. It is not in the feature's Stories list, but decision 14 already names S0007, so I took that as the human's intent. Nothing in "Out of scope" is touched.
4. factory: started tests as self.
5. tester: I made the moves the Interface names, under the standing leave in CLAUDE.md (*Tests*), and changed the one check that has the S0007 leave in decision 14. Nothing under `src/` changed.

   Criteria → tests:
   - criterion 1: no new test. Before and after the move I compared the ids from `pytest --collect-only -q` for tests/test_entrypoint.py, tests/test_agent_home_ownership.py, tests/test_entrypoint_skills.py and tests/test_shared_test_helpers.py: the same 27 ids. conftest's `image_layout` fixture is unchanged apart from its import.
   - criterion 2: tests/test_entrypoint_support.py::test_the_entrypoint_layout_lives_in_its_support_module_alone
   - criterion 3: tests/test_shared_test_helpers.py::test_the_image_layout_fixture_returns_the_entrypoints_layout. It keeps its name; its expected line is now `"from entrypoint_support import Layout as ImageLayout\n"`, so it would fail against the old conftest line.
   - criterion 4: `make check`, the coder's check.
   - criterion 5: docs: none.

   Files created:
   - tests/entrypoint_support.py: `ROOT`, `ENTRYPOINT`, `STAMP`, `STAMPED`, `SYSTEM_PATH`, `AGENT_TEXT`, `SETTINGS_TEXT` and `Layout`, all exactly as they were in test_entrypoint.py; also `texts(output: str) -> list[str]`, the old `_texts` body under a public name.
   - tests/test_entrypoint_support.py: the one test. It leaves itself out of the search, and its search texts are split.

   Earlier test files changed:
   - Under the standing leave: tests/test_entrypoint.py (its own copies removed, imports now from `entrypoint_support`; in `test_a_missing_image_file_ends_the_run_with_one_line_before_the_instance` the local `texts` is renamed `lines`), tests/test_agent_home_ownership.py and tests/test_entrypoint_skills.py (imports), tests/conftest.py (import line; ruff re-sorted it into the import block).
   - Under the human's leave in decision 14: tests/test_shared_test_helpers.py, the one expected line.

   Run: `make test` → `test: green (37.8 s)`. These are not red tests: in this story the tester does the move itself, so the coder has nothing to implement beyond confirming `make check`. `make lint` → green. The test run imported every module. I did not run the type check (stage rule).

   Open: none.

   `lint`: lint: green (0.0 s)
   `test`: test: green (38.8 s)
6. factory: started doing as self.
7. coder: I built nothing, and that matches the Interface: this story changes only tests, and the tester made every move. No module under `src/factory/` changes, and I changed no file.

   I checked the result:
   - `make check` is green and ends with `check: green`. The test target reports `test: green (37.7 s)` with 99.13 % coverage.
   - The first smoke command, the grep for `class Layout:`, finds two modules: `tests/confine_support.py` and `tests/entrypoint_support.py`.
   - The second smoke command finds `from test_entrypoint import` in no module (`0`).
   - `git diff main` outside `factory/` touches only the seven test files named in entry 5.

   Main choice: I left the tester's move exactly as it is. The alternative I rejected was tidying the moved helpers in `tests/entrypoint_support.py` during the refactor step. The coder never edits tests (R9), so there was nothing of mine to refactor.

   Noticed, not touched: none.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (seven test files, nothing under `src/`) against the work item. Group 1 holds. Criterion 1: the tester compared the collected ids before and after (entry 5). Every test function and parametrize id in the diff keeps its name. Criterion 2 is tested by `tests/test_entrypoint_support.py::test_the_entrypoint_layout_lives_in_its_support_module_alone`, which checks all three conditions. Criterion 3 is the changed expected line in `tests/test_shared_test_helpers.py`, which would fail against the old conftest line. The coder's `make check` was green (entry 7). Groups 2 and 3 hold: no layer, wrapper or security change, and no silencing marker. `tests/entrypoint_support.py` matches the removed code of `tests/test_entrypoint.py` line for line, and `_texts` is now `texts` with the same body. Group 4 fails:

   1. `tests/test_entrypoint_support.py:9` (`_containing`, with its `TESTS` and `THIS` constants): this is a second copy of `_writing` in `tests/test_shared_test_helpers.py:13` (with `TESTS`/`THIS` at lines 8–10). Both do the same thing: rglob `*.py` under `tests`, leave out the calling module, and return the sorted relative paths of the files that match. The only difference is a substring test instead of a regex. Fix: under the standing leave, the tester moves this search to one shared module at the `tests/` root, for example `tests/search_support.py`. The function takes the module to leave out as an argument. Both test modules then use it, the new test with `re.escape` of its texts or a substring mode. `test_each_shared_helper_is_written_in_one_module` and its ids stay as they are, and so does what it checks.

   Rejected: counting the three asserts in the one criterion-2 test as separate sides of one rule. Criterion 2 asks for exactly one test holding all three conditions.

   Earlier tests:
   - `tests/conftest.py`: standing leave to move a shared test helper (import line only; the `image_layout` fixture is unchanged).
   - `tests/test_entrypoint.py`: standing leave to move a shared test helper (copies removed and imports from `entrypoint_support`). The local `texts`→`lines` rename in `test_a_missing_image_file_ends_the_run_with_one_line_before_the_instance` follows from the move; the story's Interface names it, and the test checks the same thing.
   - `tests/test_agent_home_ownership.py`: standing leave to move a shared test helper (import line only).
   - `tests/test_entrypoint_skills.py`: standing leave to move a shared test helper (import and `_texts`→`texts` calls).
   - `tests/test_shared_test_helpers.py`: the human's leave, the S0007 bullet in decision 14 of `feature.md`. Only the one expected line changed.
10. factory: started doing as self.
11. coder: Round 1: the reviewer's only finding (entry 9) is about test code. I changed no file, because the coder never edits tests (R9). The fix is a test-helper move under the standing leave in `CLAUDE.md` (*Tests*), so the tester makes it.

    Move for the tester: `_containing` in `tests/test_entrypoint_support.py:9` duplicates `_writing` in `tests/test_shared_test_helpers.py:13`, along with their `TESTS`/`THIS` constants. Both functions rglob `*.py` under `tests`, leave out the calling module, and return the sorted relative paths of the files that match. Move that search to one shared module at the `tests/` root, for example `tests/search_support.py`. The shared function takes the module to leave out as an argument and a regex pattern. `tests/test_entrypoint_support.py` then calls it with `re.escape` of its three split texts. `tests/test_shared_test_helpers.py` uses it in place of `_writing`. `test_each_shared_helper_is_written_in_one_module` and `test_the_entrypoint_layout_lives_in_its_support_module_alone` keep their names, their ids and what they check. The new support module's own source must not hold the searched texts unsplit.

    Main choice: I hand back with `tests` and leave the code unchanged. The alternative I rejected was making the move myself: the coder never changes a test, even under the standing leave, which belongs to the tester.

    Noticed, not touched: nothing else. Nothing under `src/` changes in this story, and `make check` was green after round 0 (entry 7).
