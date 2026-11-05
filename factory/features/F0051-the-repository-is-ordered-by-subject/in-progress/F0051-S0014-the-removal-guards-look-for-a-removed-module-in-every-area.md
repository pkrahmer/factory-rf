---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 569
comments_read: [6655308033]
handed_over: null
claim: null
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
