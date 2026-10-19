---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 304
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-19T23:48:40.568999Z'
  lease_duration: 60
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
