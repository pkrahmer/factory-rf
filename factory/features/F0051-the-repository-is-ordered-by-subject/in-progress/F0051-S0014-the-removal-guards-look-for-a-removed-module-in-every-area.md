---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 569
comments_read: [6655308033]
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-05T10:26:00.799088Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T10:04:26.886302Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T10:04:26.893023Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-05T10:04:43.081601Z'
  stage: intake
  run: c90591e296a5478990f69f403ce0f823
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-05T10:10:37.889770Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-05T10:10:40.711139Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-05T10:11:00.627662Z'
  stage: intake
  run: 5470464d0bd74e9cb4c999c09dd224bc
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-05T10:11:05.796252Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-05T10:12:49.778482Z'
  stage: tests
  run: be08bf6d9d64469789ac49bcc5e72ef9
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-05T10:12:55.292394Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-05T10:17:59.295994Z'
  stage: doing
  run: 8b2cb2c3f7c84af4a95ee1b08dc98aad
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-05T10:18:04.751264Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-05T10:19:17.141812Z'
  stage: review
  run: c38b47396dec4d2a813edd457b63720a
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-05T10:19:22.826277Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-05T10:19:42.376480Z'
  stage: doing
  run: 786b0fc3bc264cf98ec798b3824d67f6
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-05T10:19:48.007426Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-11-05T10:20:42.499442Z'
  stage: tests
  run: 1c8794ab8ec54f178d76292f3a65740d
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-05T10:20:48.068027Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-11-05T10:25:54.884780Z'
  stage: doing
  run: bcbf6cc941a04f95bf0a2f1965ca289b
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-05T10:26:00.799088Z'
  stage: review
---

# The removal guards look for a removed module in every area
<!-- proposed by feature acceptance of 2026-11-05; refine before starting -->

## Description

Earlier features removed modules: the sessions, the sealed runs, the agent home, the hook guard, the kernel guard, the leftovers program, the undo and the mutation report. Each removal has a guard that asserts the module is gone. The guards name these modules at their old layer paths, for example `factory.adapters.landlock`. Since F0051 removed the packages `factory.domain`, `factory.application` and `factory.adapters`, those paths cannot exist any more, so every such guard passes by construction. A removed module brought back inside an area, such as `factory.agents.adapters.landlock`, would pass them all. This story gives the guards back their rule. A shared test helper finds a module named at an old layer path in any area, and the guards use it in place of `module_exists`. Each guard keeps its name, its rows and the module names it lists. A new guard over the tests catches a call that passes an old layer path to `module_exists`. No module under `src/` changes. The changes to the guards are changes to tests other stories wrote, so they need the human's leave in `feature.md` before the story starts.

## Interface

`tests/support/module_names.py` (the shared helpers of `tests/support/`) gains two functions:

```python
def module_exists_anywhere(module: str) -> bool:
    """Whether `module` can be found at its path or, named at an old layer path, in any area."""

def names_the_module_anywhere(names: Collection[str], module: str) -> bool:
    """Whether `names` holds `module` or, for an old layer path, the same module in any area."""
```

- An old layer path is `factory.<layer>.<rest>` with `<layer>` one of `domain`, `application` or `adapters`, and `<rest>` one or more dotted names.
- The areas are read from the tree: every package folder directly under `src/factory/` except `entry` and `contract`. There is no table of areas.
- `module_exists_anywhere(module)` is true when `module_exists(module)` is true. For an old layer path, it is also true when `module_exists` finds `factory.<area>.<layer>.<rest>` for any area. Any other name is found only at its own path.
- `names_the_module_anywhere(names, module)` is true when `module` is in `names`. For an old layer path, it is also true when `names` holds `factory.<area>.<layer>.<rest>` for any area. A name that only begins with the same text (`...landlock_extra`) or sits in another layer does not count.
- The guards that change, each keeping its name, rows and listed names, with the leave the human gives in `feature.md`:
  - `tests/guards/test_docker_path_removed.py` (`_sessions_module_is_gone`)
  - `tests/guards/test_checkout_hygiene_removed.py` (`sealed_runs`)
  - `tests/guards/test_home_reset_removed.py`
  - `tests/guards/test_hook_removed.py`
  - `tests/guards/test_kernel_guard_removed.py`
  - `tests/guards/test_leftovers_program_removed.py`
  - `tests/guards/test_undo_removed.py`
  - `tests/entry/test_mutation_report_removed.py`

  These call `module_exists_anywhere` where they called `module_exists`. In each of them, every call changes, the ones for names outside the old layers too (`factory.entry.guard` in `test_hook_removed.py`), since `module_exists_anywhere` finds such a name only at its own path. `tests/guards/test_wrapper_out_of_the_call_path.py` and `tests/pipeline/application/test_stall_environment.py::test_the_stall_module_imports_no_name_of_the_undo` compare imports through `names_the_module_anywhere`.
- New test modules: `tests/guards/test_module_names.py` (the helpers, criteria 1 and 2) and `tests/guards/test_removal_guards_search.py` (criterion 3).
- No module under `src/` changes.

## Acceptance criteria

1. `module_exists_anywhere` gives, one row each:
   - `factory.domain.errors` → `True` (found as `factory.shared.domain.errors`)
   - `factory.adapters.process` → `True`
   - `factory.domain.no_such_module` → `False`
   - `factory.shared.domain.errors` → `True`
   - `factory.shared.domain.no_such_module` → `False`
   - `factory.entry.run` → `True`
   - `factory.entry.confine` → `False`
   - `factory.contract.errors` → `False` (`contract` is not a layer, and no area is tried)
2. `names_the_module_anywhere` gives, one row each:
   - `({"factory.agents.adapters.landlock"}, "factory.adapters.landlock")` → `True`
   - `({"factory.adapters.landlock"}, "factory.adapters.landlock")` → `True`
   - `({"factory.agents.adapters.landlock_extra"}, "factory.adapters.landlock")` → `False`
   - `({"factory.agents.domain.landlock"}, "factory.adapters.landlock")` → `False`
   - `({"factory.entry.confine"}, "factory.entry.confine")` → `True`
   - `({"factory.pipeline.entry.confine"}, "factory.entry.confine")` → `False`
   - `(set(), "factory.application.undo")` → `False`
3. No module under `tests/` that holds a string literal of an old layer path calls `module_exists`. Such a module calls `module_exists_anywhere` instead. Rows on parsed source:
   - A source with `module_exists(name)` and the literal `"factory.adapters.landlock"` is caught.
   - A source with `module_exists_anywhere(name)` and the same literal is not caught.
   - A source with `module_exists("factory.entry.confine")` and no old layer path is not caught.
   - The whole of `tests/` today gives an empty list. A module whose old-path literals are made-up names for a search, such as `tests/guards/test_hosting_search.py`, calls no `module_exists` and is not caught.
4. `make check` stays green.
5. docs: `docs/project-guide/README.md`, *Shared test helpers*: one sentence. A guard that a module stays removed names the module at the path it had and checks it with `module_exists_anywhere` of `tests/support/module_names.py`, so that the module is not found in any area either. `README.md`, the operator guide and `docs/decisions.md`: none, because nothing the operator does changes.

## Smoke test

```bash
uv run python -c "import sys; sys.path.insert(0, 'tests'); from support.module_names import module_exists_anywhere as f; print(f('factory.domain.errors'), f('factory.adapters.landlock'))" 2>/dev/null
```
Expect: `True False`

```bash
uv run pytest tests/guards/test_module_names.py tests/guards/test_removal_guards_search.py tests/guards/test_kernel_guard_removed.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

```bash
grep -lw module_exists tests/guards/test_kernel_guard_removed.py tests/guards/test_docker_path_removed.py tests/guards/test_undo_removed.py | wc -l
```
Expect: `0`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: 1. Leave missing from `feature.md`. The story changes ten tests that other stories wrote: the eight removal guards, `tests/guards/test_wrapper_out_of_the_call_path.py` and `tests/pipeline/application/test_stall_environment.py::test_the_stall_module_imports_no_name_of_the_undo`. It says the human gives the leave in `feature.md`, but *The human's changes* has no entry for S0014. Decision 5's leave covers only the move stories' testers (S0001 to S0007) and only the old-layout guards. Without the leave this story cannot start, per CLAUDE.md's "Not without asking". Options: (a) you add an entry under *The human's changes* ("At S0014's start: the tester may change the named guards and tests to call `module_exists_anywhere` and `names_the_module_anywhere`, nothing else in them"), and the story runs again unchanged; (b) you give the leave in your answer here and I carry it into the story. I would choose (a).

   2. Format check: passed. Nothing to add. I checked the Interface, criteria, smoke test, architecture and scope only up to this blocker, so I will redo them with your answer.
4. 2026-11-05 human: Answer of the human:

   **(a).** `feature.md` on `main` now has the entry under *The human's changes*: "At S0014's start: a leave for its tester: the eight removal guards it names, `tests/guards/test_wrapper_out_of_the_call_path.py` and `tests/pipeline/application/test_stall_environment.py::test_the_stall_module_imports_no_name_of_the_undo` may change to call `module_exists_anywhere` and `names_the_module_anywhere`, nothing else in them; each test keeps its name and what it checks." Go on with the intake.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: `tests/support/module_names.py` exists and holds `module_exists`. The story adds `module_exists_anywhere(module: str) -> bool` and `names_the_module_anywhere(names: Collection[str], module: str) -> bool`, with signatures, the old-layer-path definition, how areas are read (package folders under `src/factory/` except `entry` and `contract`) and both sides of each rule. All ten changed tests are named.
   - Criteria: criteria 1 and 2 are tables with one row each, and each is a single parametrized test. They cover both sides (found or not found, the `_extra` prefix, another layer, `entry`, `contract`). Criterion 3 has rows on parsed source, caught and not caught, plus the whole of `tests/`. Criteria 4 and 5 are the two closing ones. The human's leave for the ten tests (journal 4) is in `feature.md` under *The human's changes*, which I read.
   - Smoke test: the commands are runnable. `pyproject.toml` sets `addopts = "-q ..."` and the pytest command passes no `-q`, so `tail -1` shows the summary line that `grep -c passed` counts. Each `Expect:` can be checked against the output: `True False`, `1` and `0`.
   - Architecture: only helpers under `tests/support/` and guards under `tests/guards/` change. Nothing under `src/` changes. The new test modules sit in the right folders, and nothing imports a `test_*.py` module.
   - Scope: S0014 is listed in `feature.md` (from A0001), and it changes no behaviour or module name. The story's goal sits inside the feature's goal (an ordered repository, guards kept true), and no *Out of scope* item is touched.
7. factory: started tests as vm.
8. tester: Wrote the tests for every criterion. I also wrote the two helpers the Interface adds to `tests/support/module_names.py` and changed the ten earlier tests the story names. All of these are under `tests/`, and only the tester's write paths cover `tests/*`, so the coder could not write any of them. Because of that, the new tests are green, not red. Nothing under `src/` changes, so the coder only needs to run `make check`.

   Criterion → test:
   - criterion 1: tests/guards/test_module_names.py::test_a_module_is_found_at_its_path_or_from_an_old_layer_path_in_any_area (8 rows)
   - criterion 2: tests/guards/test_module_names.py::test_a_set_of_names_holds_a_module_at_its_path_or_from_an_old_layer_path_in_any_area (7 rows)
   - criterion 3, rows on parsed source: tests/guards/test_removal_guards_search.py::test_a_module_that_names_an_old_layer_path_calls_module_exists_anywhere (3 rows)
   - criterion 3, the whole of `tests/`: tests/guards/test_removal_guards_search.py::test_no_test_module_looks_for_an_old_layer_path_only_at_that_path
   - criteria 4 and 5: no test (`make check`, docs).

   Files created: tests/guards/test_module_names.py, tests/guards/test_removal_guards_search.py.

   Shared helper: tests/support/module_names.py gains `module_exists_anywhere`, `names_the_module_anywhere` and `areas()`. `areas()` reads the package folders directly under `src/factory/` and leaves out `entry` and `contract`; there is no table of areas. A private `_in_every_area` turns an old layer path (`factory.<domain|application|adapters>.<rest>`) into the same module in each area, and returns nothing for any other name. That is why `factory.contract.errors` and `factory.entry.*` are looked for only at their own path. The search guard counts a string literal as an old layer path when it fully matches `factory.(domain|application|adapters)(.name)+`, and counts a call to `module_exists` whether it is a bare name or an attribute.

   Earlier test files I changed, under the leave in `feature.md` (*The human's changes*, "At S0014's start"). Every test keeps its name, its rows and its listed names:
   - `module_exists` became `module_exists_anywhere`, every call and the import, in: tests/guards/test_docker_path_removed.py, test_checkout_hygiene_removed.py, test_home_reset_removed.py, test_hook_removed.py (including `factory.entry.guard`), test_kernel_guard_removed.py, test_leftovers_program_removed.py, test_undo_removed.py, and tests/entry/test_mutation_report_removed.py. ruff format re-wrapped the lines that became too long.
   - tests/guards/test_wrapper_out_of_the_call_path.py: the import check now goes through `names_the_module_anywhere` instead of `_imports(...) & GUARD_IMPORTS`. The skip of `GUARD_MODULES` by its own names is unchanged, because the leave covers only the helper calls.
   - tests/pipeline/application/test_stall_environment.py::test_the_stall_module_imports_no_name_of_the_undo: `"factory.application.undo" not in imported` became `not names_the_module_anywhere(imported, "factory.application.undo")`.

   Run: one `uv run pytest -q` over the two new modules, the ten changed tests and the wrapper guard. All passed and nothing failed to import. `make lint` is green. `mypy --strict` also passes on the helper, the two new modules and the wrapper guard; the other changed files were not type-checked, which the coder's `make check` covers.

   Open: nothing.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: I built nothing. The story changes no module under `src/` (see its Interface), and the tester already wrote everything under `tests/`: the two helpers in `tests/support/module_names.py`, the two new guard modules and the ten earlier tests the leave covers. My write paths don't include `tests/`, so I changed none of it.

    What I did: I ran `make check` on the committed tree. It ended with `check: green` (`test: green (131.1 s)`, coverage 99.26 %).

    Main choice: I left the tree as I found it. The alternative I rejected was moving or reworking the helpers, which is the tester's work. `git diff main -- . ':!factory' ':!tests'` is empty, so the refactor step had nothing of mine to review.

    Description: the journal did not change what the task means. The human's answer (entry 4) only added the leave to `feature.md`.

    Noticed, not touched: `tests/guards/test_wrapper_out_of_the_call_path.py` still skips `GUARD_MODULES` by their exact names, as the tester's entry says. The leave covers only the helper calls, so I left it.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 40 known, 3 gone
11. factory: started review as vm.
12. reviewer: Review of `git diff main...HEAD -- . ':!factory'` (round 0). Nothing under `src/` changes; every change is under `tests/`. Groups 1, 2, 3 and 5 are clean:
    - Criterion 1 has its 8 rows and criterion 2 its 7 rows, each as one parametrized test.
    - Criterion 3 has its 3 parsed-source rows plus the whole-of-`tests/` test.
    - `make check` after the coder was green (journal 10).
    - Nothing touches the architecture or security, and the Description matches what was built.

    The findings are all in group 4. They are about test quality, and at round 0 they still send the work item back. All of them are the tester's to fix: every path is under `tests/`.

    Findings:
    1. `tests/support/module_names.py:30` (`areas()`): `Path(factory.__file__).parent` is a second copy of `SRC` in `tests/support/source_search.py:8`. Fix: import `SRC` from `support.source_search` and iterate over it.
    2. `tests/guards/test_removal_guards_search.py:25-31` (`_holds_an_old_layer_path`): it walks the tree for string constants again, which copies `string_literals` in `tests/support/source_search.py:39`. Fix: `any(OLD_LAYER_PATH.fullmatch(text) for text in string_literals(tree))`.
    3. `tests/guards/test_removal_guards_search.py:9`: `TESTS = Path(__file__).resolve().parents[1]` copies `TESTS` in `tests/support/search_support.py:7`. Fix: import it from `support.search_support`.
    4. Two definitions of "old layer path" that do not agree:
       - `tests/guards/test_removal_guards_search.py:10` uses the regex `OLD_LAYER_PATH`, which requires identifiers.
       - `tests/support/module_names.py:10,39-42` uses `LAYERS` with the length check in `_in_every_area`, which accepts any non-empty part.
       
       Fix: one public predicate in `tests/support/module_names.py` (for example `is_old_layer_path(name: str) -> bool`, built on `LAYERS`). `_in_every_area` and the search guard both use it, and the regex goes.

    Notes:
    - `tests/guards/test_module_names.py`: the zero side of the Interface's limit "`<rest>` one or more dotted names" has no row. The code handles it as the Interface says (`len(parts) < 3` at `tests/support/module_names.py:41`). The missing row is `"factory.domain"` → `False` in criterion 1's table (and `({"factory.shared.domain"}, "factory.domain")` → `False` in criterion 2's).
    - `tests/guards/test_removal_guards_search.py`: the same zero side of the old-path literal has no row. The regex's `+` (line 10) handles it. The missing row is `'NAME = "factory.adapters"\nmodule_exists(name)\n'` → not caught.

    Earlier tests (item 6), changed under the human's leave in `feature.md` (*The human's changes*, "At S0014's start", journal entry 4). Each only swaps `module_exists` for `module_exists_anywhere`, or swaps the set comparison for `names_the_module_anywhere`, and each test keeps its name and rows:
    - `tests/entry/test_mutation_report_removed.py`: human's leave (journal 4)
    - `tests/guards/test_checkout_hygiene_removed.py`: human's leave (journal 4)
    - `tests/guards/test_docker_path_removed.py`: human's leave (journal 4)
    - `tests/guards/test_home_reset_removed.py`: human's leave (journal 4)
    - `tests/guards/test_hook_removed.py`: human's leave (journal 4); ruff format re-wrapped some lines
    - `tests/guards/test_kernel_guard_removed.py`: human's leave (journal 4)
    - `tests/guards/test_leftovers_program_removed.py`: human's leave (journal 4)
    - `tests/guards/test_undo_removed.py`: human's leave (journal 4)
    - `tests/guards/test_wrapper_out_of_the_call_path.py`: human's leave (journal 4)
    - `tests/pipeline/application/test_stall_environment.py`: human's leave (journal 4); only `test_the_stall_module_imports_no_name_of_the_undo` changes
    - `tests/support/module_names.py`: none needed. It is a support module, not a test; it only gains the helpers the Interface names plus a longer module docstring, and `has_name` and `module_exists` are unchanged.
13. factory: started doing as vm.
14. coder: Round 1: I changed no code. Every finding in the review (journal 12) is in files the tester wrote in this story, all under `tests/`, and my write paths don't cover `tests/`. Nothing under `src/` changes, so all four findings go to the tester.

    The tester makes these changes, as the reviewer proposed:
    1. `tests/support/module_names.py` (`areas()`): import `SRC` from `support.source_search` and iterate over it, in place of `Path(factory.__file__).parent`.
    2. `tests/guards/test_removal_guards_search.py` (`_holds_an_old_layer_path`): use `string_literals` of `support.source_search` (`any(is_old_layer_path(text) for text in string_literals(tree))`) in place of its own walk over the tree.
    3. `tests/guards/test_removal_guards_search.py`: import `TESTS` from `support.search_support` in place of `Path(__file__).resolve().parents[1]`.
    4. Add one public predicate `is_old_layer_path(name: str) -> bool` to `tests/support/module_names.py`, built on `LAYERS`. `_in_every_area` and the search guard both use it, and the regex `OLD_LAYER_PATH` goes.

    The reviewer also noted that the zero side of "`<rest>` one or more dotted names" has no row. These rows are optional, and they are the tester's to add: `"factory.domain"` → `False` in criterion 1's table, `({"factory.shared.domain"}, "factory.domain")` → `False` in criterion 2's, and `'NAME = "factory.adapters"\nmodule_exists(name)\n'` → not caught in criterion 3's parsed-source rows.

    Main choice: I handed forward with `tests` rather than `question`. These are helper copies and one definition in the tester's own new files, inside this story. They need no new leave.

    Description: the journal did not change what the task means.

    Not run: `make check`. I changed nothing, and the tester's change comes back through doing.
15. factory: started tests as vm.
16. tester: Round 1, an approved test change: I made the four changes the coder's entry 14 names, which come from the reviewer's findings in entry 12, and added the three optional zero-side rows. Every file I touched is one I wrote in this story.

    Changes:
    1. `tests/support/module_names.py`, `areas()`: it now iterates over `SRC`, imported from `support.source_search`. `Path(factory.__file__).parent` and the `factory` and `Path` imports are gone.
    2. `tests/guards/test_removal_guards_search.py`, `_holds_an_old_layer_path`: it is now `any(is_old_layer_path(text) for text in string_literals(tree))`, with `string_literals` from `support.source_search`.
    3. `tests/guards/test_removal_guards_search.py`: `TESTS` is imported from `support.search_support`. The local `Path(__file__).resolve().parents[1]` is gone.
    4. `tests/support/module_names.py` has a new public `is_old_layer_path(name: str) -> bool`, built on `LAYERS`. It is true for `factory.<layer>.<rest>` when the name has at least three parts, its layer is in `LAYERS` and every part of `<rest>` is an identifier. `_in_every_area` and the search guard both use it, and the regex `OLD_LAYER_PATH` and the `re` import are gone. The identifier check comes from the old regex. The old `all(parts[2:])` only rejected empty parts, so now the two places agree.

    Zero-side rows the reviewer noted, all with id `layer-alone`:
    - criterion 1: `"factory.domain"` → False
    - criterion 2: `({"factory.shared.domain"}, "factory.domain")` → False
    - criterion 3, parsed-source rows: `'NAME = "factory.adapters"\nmodule_exists(name)\n'` → not caught

    Criterion → test (the test names are unchanged):
    - criterion 1: tests/guards/test_module_names.py::test_a_module_is_found_at_its_path_or_from_an_old_layer_path_in_any_area
    - criterion 2: tests/guards/test_module_names.py::test_a_set_of_names_holds_a_module_at_its_path_or_from_an_old_layer_path_in_any_area
    - criterion 3: tests/guards/test_removal_guards_search.py::test_a_module_that_names_an_old_layer_path_calls_module_exists_anywhere and ::test_no_test_module_looks_for_an_old_layer_path_only_at_that_path

    Files changed: tests/support/module_names.py, tests/guards/test_module_names.py, tests/guards/test_removal_guards_search.py. I created no new files and changed no earlier story's test.

    Run: one `uv run pytest -q` over the two guard modules, the ten earlier tests that use the helpers and the wrapper guard. All passed and nothing failed to import. `make lint` is green, and `mypy --strict` passes on the three changed files.

    Open: nothing.

    `lint`: lint: green (0.2 s)
17. factory: started doing as vm.
18. coder: Round 1: I built nothing. The tester's round-1 changes (journal 16) settle every finding in the review (journal 12). Those changes are: `SRC` from `support.source_search` in `areas()`, `string_literals` and `TESTS` reused in `tests/guards/test_removal_guards_search.py`, one `is_old_layer_path` in `tests/support/module_names.py` in place of the regex, and the three zero-side rows. All of them are under `tests/`, which is outside my write paths. Nothing under `src/` changes, as the Interface says.

    What I did: I ran `make check` on the committed tree. It ended with `check: green` (`test: green (131.9 s)`, coverage 99.26 %).

    Main choice: I handed forward to review unchanged. The alternative I rejected was going over the tester's helpers again, which is not mine to change. `git diff main -- . ':!factory' ':!tests'` and `git status --short` are both empty, so the refactor step had nothing to change.

    Description: the journal did not change what the task means.

    Noticed, not touched: nothing new.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 5 new, 40 known, 3 gone
19. factory: started review as vm.
