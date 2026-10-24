---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 428
comments_read: [6390818287]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T23:02:13.608910Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T23:02:13.614741Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-24T23:02:33.982843Z'
  stage: intake
  run: d968c5251dfd47df86c98016d4746881
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T23:02:54.198541Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-24T23:06:53.511056Z'
  stage: tests
  run: a839b0968ece4c62a59790172bcff844
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-24T23:07:14.559563Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-24T23:10:07.112263Z'
  stage: doing
  run: 1677168628f94905b35a5c1c82efc8af
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-24T23:10:27.827705Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-24T23:11:36.345017Z'
  stage: review
  run: 8bd782ead82344338a9fc2d5bdc16641
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-24T23:11:57.861363Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-24T23:12:14.521763Z'
  stage: doing
  run: 5c658bcb9d5e4345923024151f917426
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-24T23:12:35.002829Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-24T23:15:33.659693Z'
  stage: tests
  run: faf38bf8c4ad48cea84507d958122f38
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-24T23:15:54.523733Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-24T23:18:41.062677Z'
  stage: doing
  run: 76d8c2f96e4a4484a23bf706c97a92bb
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-24T23:19:01.557148Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: question
  at: '2026-10-24T23:20:06.070554Z'
  stage: review
  run: 2ee9a41559fd4a83b95abe22e4adf320
  blocked: question
- number: 18
  speaker: human
  kind: comment
  at: '2026-10-24T23:22:26.255146Z'
  stage: review
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-24T23:22:44.176618Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-10-24T23:23:17.502729Z'
  stage: review
  run: 55e10946fb58483a85277181322abf1a
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-24T23:23:37.884971Z'
  stage: docs
- number: 22
  speaker: documenter
  kind: result
  at: '2026-10-24T23:24:16.530955Z'
  stage: docs
  run: efb8851d14f7402d878c07852ebac167
---

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

  It also gains `modules_assigning(value: str) -> list[str]`, the sorted modules under `tests/` that assign `value` at top level; both guards call it, and a later guard calls `modules_assigning` instead of walking the modules again.

- `tests/test_shared_stage_constants.py` (new) is the guard. It has one parametrized test whose rows are the three values. For each value, the modules under `tests/` that assign it at top level, under any name, are exactly its home.
- The earlier modules that hold a copy import the value from its home and drop their copy, under the standing leave. A module that names the value differently (`WRITTEN`, `AGENT_FILE`) uses the home's name in its place. No test is renamed.

## Acceptance criteria

1. `tests/test_shared_stage_constants.py` passes. Under `tests/`, `"written by the agent\n"` is assigned at top level only in `take_support.py`, and `"tests/test_a.py"` and `"notes.md"` only in `stage_run_support.py`. With a second top-level assignment of any of the three values added to any test module, under any name, its row fails and names that module.
2. `top_level_copies` counts a plain and an annotated top-level assignment, under any name. It counts no assignment of another value, no name used as a value, and no assignment inside a function or a class: the same seven rows as `tests/test_shared_constants.py::test_the_guard_counts_a_top_level_assignment_of_the_instance_name`, whose test keeps its name and its rows.
3. Every test that existed before this story still exists under its name and passes. The tester's entry names each earlier test file it changed.
4. `make check` stays green.
5. docs: in `docs/project-guide/README.md`, *Shared test helpers*, the documenter adds one entry each for `home_files_support.py`, `leftovers_runtime_support.py`, `leftovers_support.py`, `root_support.py`, `stall_support.py`, `time_limits.py` and `torn_record_support.py`, each from its module's docstring and its public names. The `stage_run_support.py` entry gains `INSIDE` and `NOTES`, and the `container_support.py` entry no longer claims them. The `take_support.py` and `search_support.py` entries name the guard `tests/test_shared_stage_constants.py` and `top_level_copies`; the `search_support.py` entry names `modules_matching`, `modules_assigning` and `top_level_copies`, and says that a later guard calls `modules_assigning` instead of walking the modules again. Afterwards every module `tests/*.py` whose name does not start with `test_` has an entry.

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

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: no `src/` change, which the story says. It names concrete test modules and one signature: `top_level_copies(source: str, value: str) -> list[str]` in `tests/search_support.py`. It also names the homes of the three values (`take_support.py`, `stage_run_support.py`), the new guard module and the import rule under `mypy --strict`. I checked the repo: `instance_copies` is in `tests/test_shared_constants.py:11` and `INSIDE`/`NOTES` are in `tests/container_support.py:37-38`. `stall_support.py` also holds `INSIDE` and `AGENT_TEXT` copies. All of this matches the Description.
   Criteria: each is testable by one test function. 1 is the parametrized guard with three rows, and a failing row names the module. 2 pins `top_level_copies` to the same seven rows as the existing instance-name test. 3 and 4 are the usual ones. 5 is the documenter's list. The Interface states two behaviours, "assignment under any name" and "no import cycle". Criteria 1 and 2 cover the first. The second is a structural note that the import system enforces, so it needs no criterion.
   Smoke test: the commands are runnable. The project's pytest config sets `-q` in `addopts` and the first command passes none, so `tail -1` gives the `N passed in Xs` summary line that the grep and the Expect: 1 can match. The second command expects exactly two files, which is checkable. The third counts the modules without an entry and expects 0.
   Architecture: the work stays in `tests/`, uses the standing leave to move shared helpers, and matches the CLAUDE.md test layout. Nothing under `src/` changes.
   Scope: it fits F0042's "the tests each story names" and breaks none of its Out of scope items. It changes earlier tests only under the standing leave, and criterion 3 requires the tester to name each earlier test file it changed.
4. factory: started tests as self.
5. tester: This story's work is all in the tests (no `src/` change), so I did the moves myself under CLAUDE.md's standing leave to move a shared test helper. Nothing is left red for the coder: `make test` is green (one run, last line `test: green (74.6 s)`) and `make lint` is green. I skipped the type check, as the stage says.

   Criteria → tests:
   - criterion 1: tests/test_shared_stage_constants.py::test_a_shared_stage_value_is_assigned_only_in_its_home. It has three rows: agent-text → `take_support.py`, inside → `stage_run_support.py`, notes → `stage_run_support.py`. Each row compares the sorted list of modules with a top-level copy to `[home]`, so if a second copy appears the failure diff names its module.
   - criterion 2: tests/test_shared_constants.py::test_the_guard_counts_a_top_level_assignment_of_the_instance_name. The name and its seven rows are unchanged; it now calls `top_level_copies(source, "factory-1")` from `tests/search_support.py`.
   - criterion 3: no test renamed or removed; the whole `make test` run is green. The earlier test files I changed are listed below.
   - criterion 4: this is the factory's `make check`. Lint and tests are green.
   - criterion 5: docs, the documenter's work; no test.

   Created: tests/test_shared_stage_constants.py.

   Moves:
   - Moved `instance_copies` out of tests/test_shared_constants.py into tests/search_support.py as `top_level_copies(source, value)`, which takes any string. `test_the_instance_name_is_assigned_in_one_module` uses it with the literal `"factory-1"`. I did not give that literal a top-level name, because the guard would then count the name as a copy.
   - Added `INSIDE` and `NOTES` to tests/stage_run_support.py. `AGENT_TEXT` stays in tests/take_support.py.

   Earlier test files changed under the standing leave (each drops its copy and imports from the value's home; no test renamed or changed in what it checks):
   - tests/container_support.py (`INSIDE` and `NOTES` now imported from stage_run_support)
   - tests/stall_support.py (`INSIDE` and `AGENT_TEXT`)
   - tests/test_shared_constants.py
   - tests/search_support.py
   - tests/stage_run_support.py
   - tests/application/test_costs.py
   - tests/application/test_undo_nested_claude.py
   - tests/application/test_opening.py
   - tests/application/test_after_agent.py
   - tests/application/test_stall_edges.py (`AGENT_FILE` renamed to `INSIDE`, docstring included)
   - tests/application/test_stage_environment_calls.py
   - tests/application/test_stage_finish.py
   - tests/application/test_undo.py
   - tests/application/test_stage_run.py
   - tests/application/test_stage_environment.py (`WRITTEN` renamed to `INSIDE`)
   - tests/application/test_stall_labels.py
   - tests/application/test_stall_reasons_recorded.py
   - tests/application/test_stall_container.py
   - Import lines only, because the names left `container_support`/`stall_support`, which under mypy's no implicit re-export would no longer supply them: tests/application/test_container_stage_checks.py, tests/application/test_stalls.py, tests/application/test_stall_environment.py

   Left as they are:
   - `tests/application/test_stall_edges.py` still writes the literal `"written by the agent\n"` inside a method. The criteria count only top-level assignments.
   - `test_stall_edges.py` keeps its own `WRITTEN = "written-by-lint.txt"`, which is a different value.

   Modules the test run could not import: none.

   Not mine: the work item's `.costs.jsonl` sidecar shows as modified in the working tree. That is the factory's change, not mine.

   `lint`: lint: green (0.5 s)
   `test`: test: green (65.5 s)
6. factory: started doing as self.
7. coder: Built nothing. The Interface puts no work under `src/factory/`, and the tester already made every move under the standing leave. `make test` showed no failing test to work against. `git diff main -- src` is empty, and I wrote no file.

   Main choice: I left the tree as the tester committed it and changed none of their moves. The alternative was to tidy their test modules in the refactor step. I rejected it because the coder never edits tests (R9). The tester's diff is not mine to refactor, so the refactor step had nothing to change.

   Checked: `make check` is green (last lines `test: green (67.6 s)` and `check: green`, total coverage 99.19 %). The smoke test's second command lists exactly `tests/stage_run_support.py` and `tests/take_support.py`.

   Noticed, not touched:
   - The third smoke command will pass only after the documenter adds the seven *Shared test helpers* entries (criterion 5).
   - The work item's `.costs.jsonl` sidecar shows as modified in the working tree. That is the factory's change.

   `check`: check: green
   `duplicates`: duplicates: 11 new, 36 known, 2 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (22 files under `tests/`, nothing under `src/`) against the work item, going through the checklist in order.

   Group 1, acceptance criteria: passes. Criterion 1 is tested by `tests/test_shared_stage_constants.py::test_a_shared_stage_value_is_assigned_only_in_its_home`. It has three rows and asserts `copies == [home]`, so a second copy fails and the diff names its module. Criterion 2 is tested by `tests/test_shared_constants.py::test_the_guard_counts_a_top_level_assignment_of_the_instance_name`, which keeps its name and its seven rows and now calls `search_support.top_level_copies`. Criterion 3: no test was renamed or removed. Criterion 4: per journal entry 7, the factory's `make check` after the coder was green. The Interface rule "`stage_run_support.py` imports neither `take_support` nor `container_support`" holds: `tests/stage_run_support.py:1-14` imports neither. mypy's no-implicit-re-export rule covers the import-home rule.

   Group 2, architecture: passes; nothing under `src/` changed. Group 3, security: passes; no markers, secrets or new baseline entries.

   Group 4, quality: fails, and this is round 0, so it sends the work item back.

   Findings:
   1. `tests/test_shared_stage_constants.py:9,21-25` copies existing code instead of reusing it. `TESTS = Path(__file__).parent` is the `search_support.TESTS` the module already imports from. The `sorted(path.relative_to(TESTS).as_posix() for path in TESTS.rglob("*.py") if top_level_copies(...))` walk is copied from `tests/test_shared_constants.py:13-17`, and both have the same shape as `search_support.modules_matching`. Fix: add one helper beside `modules_matching` in `tests/search_support.py` (for example `modules_assigning(value: str) -> list[str]`, using its `TESTS`). Both guards should call it, and the new module should drop its own `TESTS` and walk. The standing leave covers the change to `test_shared_constants.py`, as long as its test keeps its name and what it checks. This is the tester's change.
   2. `tests/application/test_costs.py:79` adds a blank line between `EARLIER` and `FAILED_REASONS`. That change does not move anything, so it is outside the standing leave. Fix: remove the added blank line (tester).

   Earlier tests changed (item 6), all modified (`M`):
   - tests/application/test_after_agent.py: standing leave (AGENT_TEXT imported from take_support)
   - tests/application/test_container_stage_checks.py: standing leave (import home of INSIDE/NOTES)
   - tests/application/test_costs.py: standing leave for INSIDE/AGENT_TEXT; the blank line is beyond it (finding 2)
   - tests/application/test_opening.py: standing leave (NOTES)
   - tests/application/test_stage_environment.py: standing leave; `WRITTEN` → `INSIDE` as the story's Interface states
   - tests/application/test_stage_environment_calls.py: standing leave (AGENT_TEXT)
   - tests/application/test_stage_finish.py: standing leave (AGENT_TEXT)
   - tests/application/test_stage_run.py: standing leave (INSIDE, NOTES, AGENT_TEXT)
   - tests/application/test_stall_container.py: standing leave (NOTES, import homes)
   - tests/application/test_stall_edges.py: standing leave; `AGENT_FILE` → `INSIDE` (docstring included) as the story's Interface states
   - tests/application/test_stall_environment.py: standing leave (import home of INSIDE)
   - tests/application/test_stall_labels.py: standing leave (NOTES)
   - tests/application/test_stall_reasons_recorded.py: standing leave (NOTES)
   - tests/application/test_stalls.py: standing leave (import homes of INSIDE/AGENT_TEXT)
   - tests/application/test_undo.py: standing leave (AGENT_TEXT)
   - tests/application/test_undo_nested_claude.py: standing leave (AGENT_TEXT)
   - tests/container_support.py: standing leave (INSIDE/NOTES moved to stage_run_support)
   - tests/search_support.py: standing leave (`instance_copies` moved here as `top_level_copies`)
   - tests/stage_run_support.py: standing leave (becomes home of INSIDE/NOTES)
   - tests/stall_support.py: standing leave (INSIDE/AGENT_TEXT copies dropped)
   - tests/test_shared_constants.py: standing leave (uses `top_level_copies` from search_support; test names and rows unchanged)

   Not a finding, left open: `tests/application/test_stall_edges.py:44` still writes the literal `"written by the agent\n"` inside a method. The criteria count only top-level assignments.
10. factory: started doing as self.
11. coder: Built nothing and changed no file. Both findings in the reviewer's entry 9 are changes to tests, and the coder never edits tests (R9). The story's Interface puts no work under `src/factory/`, so no code change answers either finding. Because I changed nothing, I did not run `make check` this round.

    The test changes the tester should make:
    1. In `tests/search_support.py`, add one helper beside `modules_matching` that walks `TESTS` and returns the sorted module paths with a top-level copy of a value (for example `modules_assigning(value: str) -> list[str]`, built on `top_level_copies`). Then have `tests/test_shared_stage_constants.py` use it and drop its own `TESTS = Path(__file__).parent` and its walk (lines 9 and 21-25). Have `tests/test_shared_constants.py` use it too, in place of its copied walk (lines 13-17). The standing leave covers this. Both tests keep their names and check the same thing.
    2. In `tests/application/test_costs.py:79`, remove the blank line that was added between `EARLIER` and `FAILED_REASONS`.

    Main choice: I end with `tests` and name the changes, rather than `question`. Finding 1 is a shared-helper move, which CLAUDE.md's standing leave gives to the tester without asking. Finding 2 undoes a whitespace change that this story's own tester made. Neither needs the human's word.

    Noticed, not touched: `tests/application/test_stall_edges.py:44` still writes the literal `"written by the agent\n"` inside a method. The reviewer called it not a finding, because the criteria count only top-level assignments. The work item's `.costs.jsonl` sidecar shows as modified in the working tree; that change is the factory's.
12. factory: started tests as self.
13. tester: I made the two test changes that the coder's entry 11 lists. Both come from the reviewer's findings in entry 9. Finding 1 is a shared-helper move under CLAUDE.md's standing leave. Finding 2 undoes a whitespace change that this story's own tester made in round 0.

    Changes:
    1. `tests/search_support.py`: added `modules_assigning(value: str) -> list[str]` next to `modules_matching`. It walks `TESTS` and returns the sorted module paths that hold a top-level copy of `value`, using `top_level_copies`.
       - `tests/test_shared_stage_constants.py` now calls it. Its own `TESTS = Path(__file__).parent` and its directory walk are gone.
       - `tests/test_shared_constants.py` (an earlier test file, changed under the standing leave) now calls it in place of its copied walk.
       - Both tests keep their names and check the same thing. `test_the_guard_counts_a_top_level_assignment_of_the_instance_name` keeps its seven rows and still calls `top_level_copies`.
    2. `tests/application/test_costs.py`: removed the blank line I had added between `EARLIER` and `FAILED_REASONS`. That file's diff against main now holds only the import move.

    Criteria → tests (unchanged from entry 5):
    - criterion 1: tests/test_shared_stage_constants.py::test_a_shared_stage_value_is_assigned_only_in_its_home
    - criterion 2: tests/test_shared_constants.py::test_the_guard_counts_a_top_level_assignment_of_the_instance_name
    - criterion 3: no test renamed or removed. The earlier test files this round changed are `tests/test_shared_constants.py`, `tests/search_support.py` and `tests/application/test_costs.py`. Entry 5 lists the full set.
    - criterion 4: `make check`, which the factory runs.
    - criterion 5: the documenter's work; no test.

    Files created this round: none. Modules the test run could not import: none.

    `make test`: `test: green (65.9 s)`. `make lint`: green. My first lint run failed with E501 because the new docstring was too long, so I shortened it.

    `lint`: lint: green (0.6 s)
    `test`: test: green (64.8 s)
14. factory: started doing as self.
15. coder: Built nothing and changed no file. This is round 1. The reviewer's two findings in entry 9 were both changes to tests. The tester made them in entry 13: `modules_assigning` in `tests/search_support.py`, which both guards now use, and the extra blank line taken out of `tests/application/test_costs.py`. That leaves no finding for the coder. The Interface puts no work under `src/factory/`, and `git diff main -- src` is empty.

    Main choice: I hand the tester's round-1 changes to review as they are. The alternative was to refactor them, and I rejected it because the coder never edits tests (R9). With no diff of my own, the refactor step had nothing to change.

    Checked: `make check` is green. Its last lines are `test: green (65.5 s)` and `check: green`, with total coverage at 99.19 %.

    Noticed, not touched:
    - `tests/application/test_stall_edges.py:44` still writes the literal `"written by the agent\n"` inside a method. The reviewer already ruled it not a finding, because the criteria count only top-level assignments.
    - The third smoke command will pass only after the documenter adds the *Shared test helpers* entries (criterion 5).
    - The work item's `.costs.jsonl` sidecar shows as modified in the working tree. That is the factory's change.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 11 new, 36 known, 2 gone
16. factory: started review as self.
17. reviewer: Question for the human. Should criterion 5 also name `modules_assigning`? It is the one gap left, and no stage that `doing` reaches can close it.

    I reviewed `git diff main...HEAD -- . ':!factory'`: 22 files, all under `tests/`, nothing under `src/`. I checked it against the work item.

    - **Group 1, acceptance criteria: passes.**
      - Criterion 1: `tests/test_shared_stage_constants.py::test_a_shared_stage_value_is_assigned_only_in_its_home` has three rows and asserts `modules_assigning(value) == [home]`. A second copy anywhere fails the row, and the failure diff names that module.
      - Criterion 2: `tests/test_shared_constants.py::test_the_guard_counts_a_top_level_assignment_of_the_instance_name` keeps its name and its seven rows. It now calls `top_level_copies(source, "factory-1")`.
      - Criterion 3: no test was renamed or removed.
      - Criterion 4: the factory's `make check` after the coder was green (entry 15).
      - The Interface rule holds: `tests/stage_run_support.py:1-14` imports neither `take_support` nor `container_support`.
    - **Group 2, architecture:** passes.
    - **Group 3, security:** passes. No markers, no secrets, no baseline entries.
    - **Group 4, quality:** passes. Both round-0 findings are fixed. `tests/search_support.py:37-44` `modules_assigning` is now the one walk, and both guards use it. `tests/application/test_costs.py` now changes only its imports.
    - **Group 5, work item hygiene: one gap.**
      - The round-1 fix added `modules_assigning(value)` to `tests/search_support.py`. That is the helper a later guard should call instead of copying the walk again, which is what this story exists to prevent.
      - Criterion 5 tells the documenter that the `search_support.py` entry names `top_level_copies` and the guard. It does not mention `modules_assigning`, and neither does the Interface. So the guide entry written from criterion 5 can leave it out (today the entry at `docs/project-guide/README.md:60` names only `modules_matching`).
      - My role may correct only the Description, not a criterion. The coder cannot write the work item. Sending this back with `doing` would only produce a question one round later.

    Options:
    - (a) The human allows me to add `modules_assigning` to criterion 5 and to the Interface's `search_support.py` bullet. I would then end with `docs`.
    - (b) Leave criterion 5 as it is and trust the documenter to list the module's public names.
    - (c) The human amends criterion 5 themselves.

    I would choose (a): it is one clause, and with it the guide lists the helper the story built.

    Earlier tests changed (item 6), all status `M`:
    - tests/application/test_after_agent.py: standing leave (`AGENT_TEXT` from take_support)
    - tests/application/test_container_stage_checks.py: standing leave (import home of `INSIDE`/`NOTES`)
    - tests/application/test_costs.py: standing leave (`INSIDE`, `AGENT_TEXT`; imports only)
    - tests/application/test_opening.py: standing leave (`NOTES`)
    - tests/application/test_stage_environment.py: standing leave; `WRITTEN` → `INSIDE`, as the Interface states
    - tests/application/test_stage_environment_calls.py: standing leave (`AGENT_TEXT`)
    - tests/application/test_stage_finish.py: standing leave (`AGENT_TEXT`)
    - tests/application/test_stage_run.py: standing leave (`INSIDE`, `NOTES`, `AGENT_TEXT`)
    - tests/application/test_stall_container.py: standing leave (`NOTES`, import homes)
    - tests/application/test_stall_edges.py: standing leave; `AGENT_FILE` → `INSIDE`, docstring included, as the Interface states
    - tests/application/test_stall_environment.py: standing leave (import home of `INSIDE`)
    - tests/application/test_stall_labels.py: standing leave (`NOTES`)
    - tests/application/test_stall_reasons_recorded.py: standing leave (`NOTES`)
    - tests/application/test_stalls.py: standing leave (import homes of `INSIDE`/`AGENT_TEXT`)
    - tests/application/test_undo.py: standing leave (`AGENT_TEXT`)
    - tests/application/test_undo_nested_claude.py: standing leave (`AGENT_TEXT`)
    - tests/container_support.py: standing leave (`INSIDE`/`NOTES` moved to stage_run_support)
    - tests/search_support.py: standing leave (`instance_copies` moved here as `top_level_copies`, and the shared walk as `modules_assigning`)
    - tests/stage_run_support.py: standing leave (now the home of `INSIDE`/`NOTES`)
    - tests/stall_support.py: standing leave (`INSIDE`/`AGENT_TEXT` copies dropped)
    - tests/test_shared_constants.py: standing leave (uses search_support; test names and rows unchanged)

    Notes:
    - `tests/test_shared_stage_constants.py`: nothing to note.
18. 2026-10-24 human: (a). You may add `modules_assigning` to criterion 5 and to the Interface's `search_support.py` bullet, one clause each, saying that the guide's `search_support.py` entry names `modules_matching`, `modules_assigning` and `top_level_copies`, and that a later guard calls `modules_assigning` instead of walking the modules again. Nothing else in the criteria changes. Then end with `docs`.
19. factory: started review as self.
20. reviewer: No findings. I followed the human's answer in entry 18, option (a), and made only the two changes it allows.

    What I did:
    - I checked the diff again. Since entry 17 the only new commit is the merge of `origin/main`, and it brought only `docs/runs/2026-10-12-overnight/night-log.md` onto the branch.
    - `git diff --stat main...HEAD -- . ':!factory'` lists the same 22 files under `tests/` and nothing under `src/`.
    - `tests/test_shared_stage_constants.py` still asserts `modules_assigning(value) == [home]` for each of its three rows.
    - `modules_assigning` is still at `tests/search_support.py:37-44`.
    - I ran smoke command 2 on the merged tree. It lists exactly `tests/stage_run_support.py` and `tests/take_support.py`.
    - Groups 1 to 5 pass, as entry 17 found. The gap entry 17 raised is closed by the edits below.

    Work item edits allowed by entry 18 (nothing else changed):
    - Interface, `search_support.py` bullet: added one clause. `tests/search_support.py` also gains `modules_assigning(value: str) -> list[str]`, the sorted modules under `tests/` that assign `value` at top level. Both guards call it, and a later guard calls `modules_assigning` instead of walking the modules again.
    - Criterion 5: added one clause. The guide's `search_support.py` entry names `modules_matching`, `modules_assigning` and `top_level_copies`, and says that a later guard calls `modules_assigning` instead of walking the modules again.

    Rejected: `doing`. No finding is left for the coder or the tester.

    Earlier tests changed (item 6), all status `M`:
    - tests/application/test_after_agent.py: standing leave (`AGENT_TEXT` now imported from take_support)
    - tests/application/test_container_stage_checks.py: standing leave (import home of `INSIDE`/`NOTES`)
    - tests/application/test_costs.py: standing leave (imports only)
    - tests/application/test_opening.py: standing leave (`NOTES`)
    - tests/application/test_stage_environment.py: standing leave; `WRITTEN` → `INSIDE`, as the Interface states
    - tests/application/test_stage_environment_calls.py: standing leave (`AGENT_TEXT`)
    - tests/application/test_stage_finish.py: standing leave (`AGENT_TEXT`)
    - tests/application/test_stage_run.py: standing leave (`INSIDE`, `NOTES`, `AGENT_TEXT`)
    - tests/application/test_stall_container.py: standing leave (`NOTES`, import homes)
    - tests/application/test_stall_edges.py: standing leave; `AGENT_FILE` → `INSIDE`, docstring included, as the Interface states
    - tests/application/test_stall_environment.py: standing leave (import home of `INSIDE`)
    - tests/application/test_stall_labels.py: standing leave (`NOTES`)
    - tests/application/test_stall_reasons_recorded.py: standing leave (`NOTES`)
    - tests/application/test_stalls.py: standing leave (import homes of `INSIDE`/`AGENT_TEXT`)
    - tests/application/test_undo.py: standing leave (`AGENT_TEXT`)
    - tests/application/test_undo_nested_claude.py: standing leave (`AGENT_TEXT`)
    - tests/container_support.py: standing leave (`INSIDE`/`NOTES` moved to stage_run_support)
    - tests/search_support.py: standing leave (`instance_copies` moved here as `top_level_copies`, and the shared walk as `modules_assigning`)
    - tests/stage_run_support.py: standing leave (now the home of `INSIDE`/`NOTES`)
    - tests/stall_support.py: standing leave (`INSIDE`/`AGENT_TEXT` copies dropped)
    - tests/test_shared_constants.py: standing leave (uses search_support; its test names and rows are unchanged)

    Notes:
    - none.
21. factory: started docs as self.
22. documenter: No findings. The diff has no change under `src/`, and the code matches the Interface and the criteria.

    Changed (one file, `docs/project-guide/README.md`, *Shared test helpers*):
    - Added entries for `home_files_support.py`, `leftovers_runtime_support.py`, `leftovers_support.py`, `root_support.py`, `stall_support.py`, `time_limits.py` and `torn_record_support.py`. Each is written from the module's docstring and public names. The smoke-test loop for criterion 5 now prints no missing module.
    - `stage_run_support.py` entry: added `INSIDE` and `NOTES`, and said that `test_shared_stage_constants.py` guards them. It also says a test module imports them from `stage_run_support.py` and not from `container_support.py`.
    - `container_support.py` entry: no longer claims `INSIDE` and `NOTES`. It says `stage_run_support.py` holds them.
    - `take_support.py` entry: gave `AGENT_TEXT` its value and named the guard `tests/test_shared_stage_constants.py` as the check that the value stays in this one module.
    - `search_support.py` entry: now names `modules_matching`, `modules_assigning` and `top_level_copies`. It says that `test_shared_constants.py` and `test_shared_stage_constants.py` call them, and that a later guard calls `modules_assigning` instead of walking the modules again.

    Cross-read and found current: the rest of the guide's index and the *Shared test helpers* intro. The intro already says `tests/test_shared_*.py` guard shared helpers. No document names `instance_copies` any more.

    I did not run `make check`, because I changed only documents. I did not run the smoke-test commands that run pytest. I only ran the missing-entry loop, which came out empty.

    Nothing stale noticed that is unrelated to this story.

    `check`: check: green (not run again: passed on tree ae650560410b at 2026-10-24T23:17:23Z)
    `secrets`: secrets: green (1.1 s)
    `documents`: documents ok
