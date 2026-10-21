---
stage: done
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 381
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T00:47:26.670498Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T00:47:26.677128Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T00:47:48.881702Z'
  stage: intake
  run: 737513a1564340a4abcab8444892885f
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T00:48:10.376349Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T00:51:52.394871Z'
  stage: tests
  run: b0d0d5193cbc45098cd67bdddeba7a5c
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T00:52:12.854963Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T00:54:46.952099Z'
  stage: doing
  run: d2ec16e2db904ea1a1e14e2cf161ca11
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T00:55:07.493708Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T00:56:15.236026Z'
  stage: review
  run: 2e0c131db96c41ccbf557a0a35119599
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-21T00:56:35.682518Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-21T00:56:48.516936Z'
  stage: doing
  run: b777015f9d904d198f81a067d26fcc08
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-21T00:57:09.158215Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-21T00:59:44.809840Z'
  stage: tests
  run: 82145ff46827403f89b7ac28dc36d1f1
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-21T01:00:05.980896Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-21T01:02:39.576125Z'
  stage: doing
  run: 154e15e8f6a343fe9b7c1eea2885c3be
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-21T01:03:00.114601Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-10-21T01:03:34.188785Z'
  stage: review
  run: 3549052bf48e4ce5b9c2aad2ff618cb2
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-21T01:03:54.547530Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-10-21T01:04:13.358259Z'
  stage: docs
  run: eada2bdc778346ee8503535eb11e4eae
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-21T01:04:34.102271Z'
  stage: smoke-test
- number: 21
  speaker: smoke-tester
  kind: result
  at: '2026-10-21T01:05:01.146117Z'
  stage: smoke-test
  run: 5e25b9757db74d6396d914453d56a061
- number: 22
  speaker: factory
  kind: done
  at: '2026-10-21T01:06:20.712895Z'
  stage: approval
---

# The tests read the pipeline definition and the factory log from one place each

## Description

Sixteen test modules define `_definition(boundaries)` with the body of the `definition` fixture of `tests/conftest.py`, `return boundaries.pipeline_reader.parse(PIPELINE_YAML)`, and five define `_log_lines(tmp_path)` with the body of `log_support.log_lines`. `tests/test_shared_fixtures.py` looks only for the spelling `def definition(boundaries: Boundaries)`, so it finds none of them, and every new module copies its neighbour. This story, the tester's under the standing leave of `CLAUDE.md` (*Tests*), adds one shared function for the definition, `pipeline_definition` in a new `tests/definition_support.py`, which the `definition` fixture calls too; replaces the sixteen copies with it (or with the fixture) and the five copies with `log_support.log_lines`; and adds a guard that finds a copy by its body under any name (the feature's decision 5). Every earlier test keeps its name and checks the same thing. Unchanged: the variants with other parameters or another definition, and `tests/test_shared_fixtures.py`. No module under `src/factory/` changes; the coder has nothing to build. The other copied helpers are S0003's.

## Interface

No module under `src/factory/` changes.

`tests/definition_support.py` (new):

```python
def pipeline_definition(boundaries: Boundaries) -> PipelineDefinition:
    """Return the test remote's pipeline definition, read through the boundaries' reader."""
```

- It returns `boundaries.pipeline_reader.parse(PIPELINE_YAML)` (`PIPELINE_YAML` from `git_support`).

`tests/conftest.py`: the `definition` fixture keeps its name, signature and docstring and returns `pipeline_definition(boundaries)`.

The modules whose `_definition(boundaries: Boundaries) -> PipelineDefinition` is removed, its calls becoming `pipeline_definition(boundaries)` or the `definition` fixture: `tests/application/handlers/test_closed.py`, `tests/application/handlers/test_hand_over.py`, `tests/application/handlers/test_run.py`, `tests/application/test_after_agent.py`, `tests/application/test_board_reader.py`, `tests/application/test_no_state_refusals.py`, `tests/application/test_question_causes_recorded.py`, `tests/application/test_stall_labels.py`, `tests/application/test_stalls.py`, `tests/application/test_tick_stale_branch.py`, `tests/application/test_watcher.py`, `tests/application/test_work_items.py`, `tests/entry/test_watch.py`, `tests/entry/test_wiring_acceptance.py`, `tests/entry/test_wiring_handlers.py` and `tests/entry/test_wiring_human_handlers.py`.

The modules whose `_log_lines(tmp_path: Path)` is removed, its calls becoming `log_lines(tmp_path)` from `log_support`: `tests/application/test_pipeline_loading.py`, `tests/application/test_pipeline_loading_yaml_fault.py`, `tests/application/test_stop_records_service.py`, `tests/application/test_tick_disk.py` and `tests/application/test_tick_stale_branch.py`. A module constant such as `LOG` stays while another line uses it.

Left as they are: the `_definition` helpers with a text parameter or another definition (`test_claims.py`, `handlers/test_closed_send_back.py`, `test_task.py`, `test_stage_finish.py`, `handlers/test_comment_handler.py`, `handlers/test_lookups.py`, `handlers/test_questions.py`), the inline reads of the definition inside other functions, and `_log_lines(state_directory)` of `tests/entry/test_run.py`.

`tests/test_shared_definition.py` (new), the guard:

- A copy of the definition is a function at the top level of a module whose body, a leading docstring left aside, is the one statement `return boundaries.pipeline_reader.parse(PIPELINE_YAML)`, compared as `ast.unparse` prints it, whatever the function's name.
- A copy of the log reading is a function at the top level of a module named `log_lines` or `_log_lines` whose only parameter is `tmp_path`.
- The guard reads every `*.py` file under `tests/` (the guard's own module included), parsed with `ast`.

## Acceptance criteria

1. `pipeline_definition(boundaries)` equals the `definition` fixture's value for the same `boundaries`, and its `acceptance_stage` is `acceptance`.
2. Each shared reading is written in one module (rows of one parametrized test): the modules under `tests/` that hold a copy of the definition are exactly `["definition_support.py"]`; those that hold a copy of the log reading are exactly `["log_support.py"]` (paths relative to `tests/`, sorted).
3. The guard finds a copy by its body, under any name, and nothing else (rows of one parametrized test, each a source text the guard's functions read): `def _definition(boundaries: Boundaries) -> PipelineDefinition:\n    return boundaries.pipeline_reader.parse(PIPELINE_YAML)\n` is a copy of the definition; `def read_it(boundaries):\n    """Read it."""\n    return boundaries.pipeline_reader.parse(PIPELINE_YAML)\n` is one; `def _definition(boundaries, text):\n    return boundaries.pipeline_reader.parse(text)\n` is not; `def _log_lines(tmp_path):\n    return []\n` is a copy of the log reading; `class Rig:\n    def log_lines(self):\n        return []\n` is not; `def _log_lines(state_directory):\n    return []\n` is not.
4. Every earlier test keeps its name and checks the same thing: the tests that `pytest --collect-only` lists in the twenty modules the Interface names are, after the story, the same ids as before it, and all of them pass.
5. The guard's limits hold on their refused side too (further rows of the parametrized test of criterion 3): `def _definition(boundaries):\n    boundaries.reset()\n    return boundaries.pipeline_reader.parse(PIPELINE_YAML)\n` is not a copy of the definition (a body of more than the one statement); `class Rig:\n    def definition(self, boundaries):\n        return boundaries.pipeline_reader.parse(PIPELINE_YAML)\n` is not (not at the top level of the module); `def _log_lines(tmp_path, name):\n    return []\n` is not a copy of the log reading (`tmp_path` is not its only parameter).
6. `make check` stays green.
7. docs: `docs/project-guide/README.md`, *Shared test helpers*: one line for the new module in the list, in its alphabetical place after `crash_support.py`, in the form of the other lines: `` - `definition_support.py`: `pipeline_definition`, the test remote's pipeline definition read through the boundaries' reader, which the `definition` fixture returns too, for helpers that take no fixtures. `` `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, nothing an operator or a newcomer sees changes and no decision is taken.

## Smoke test

```bash
uv run python - <<'PY'
import ast
from pathlib import Path
body = "return boundaries.pipeline_reader.parse(PIPELINE_YAML)"
found = set()
for path in Path("tests").rglob("*.py"):
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.FunctionDef):
            rest = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
            if (len(rest) == 1 and ast.unparse(rest[0]) == body) or (node.name in ("log_lines", "_log_lines") and [a.arg for a in node.args.args] == ["tmp_path"]):
                found.add(path.as_posix())
print(sorted(found))
PY
```
Expect: one line, `['tests/definition_support.py', 'tests/log_support.py']` (before the story it lists 22 modules, `tests/conftest.py` among them)

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
TMPDIR="$d" uv run pytest --no-header --tb=short -p no:cacheprovider tests/test_shared_definition.py tests/test_shared_fixtures.py tests/application/test_board_reader.py tests/application/test_tick_disk.py > "$d/out" 2>&1
echo "exit $?"
```
Expect: one line, `exit 0`

```bash
grep -c '^- `definition_support.py`: `pipeline_definition`' docs/project-guide/README.md
```
Expect: one line, `1` (before the story, `0`)

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules and one signature (`tests/definition_support.py::pipeline_definition(boundaries: Boundaries) -> PipelineDefinition`, body given, `PIPELINE_YAML` from `git_support`). It names the `definition` fixture's change, all sixteen `_definition` modules, the five `_log_lines` modules, the variants left alone, and the guard's three rules (body match via `ast.unparse` with a leading docstring ignored, the `log_lines`/`_log_lines` rule with `tmp_path` as only parameter, every `*.py` under `tests/`). No `src/` change, so the coder has nothing to build.
   Criteria: each testable by one test function. 1 compares the function with the fixture and checks `acceptance_stage`. 2 gives exact module lists as parametrized rows. 3 has six rows covering both sides of each guard rule (a different name, a docstring, a text parameter, a class method, `state_directory`). 4 is checked by comparing `--collect-only` ids and passing. Criteria 5 and 6 are the closing ones. Every rule in the Interface has a criterion on the failing side.
   Smoke test: runnable. The first block is a Python snippet over `tests/` with a single-line `Expect:`. The second runs pytest with no `-q`, and `pyproject.toml` `addopts` already sets `-q`. It only checks `exit 0`, so no summary line is needed. The third is a grep with `Expect: 1`. All three expectations can be checked against the output. I confirmed `tests/log_support.py` and `tests/git_support.py` exist, and that the docs line comes after `crash_support.py` (line 35) in the project guide.
   Architecture: tests only, under the standing leave in `CLAUDE.md` (*Tests*) for moving shared helpers, which the tester makes. The new helper is a module at the `tests/` root, and the guard is a test at the root. The layers are untouched.
   Scope: within the feature's scope (S0002). The variants with a text parameter or another definition, `tests/entry/test_run.py::_log_lines(state_directory)` and `tests/test_shared_fixtures.py` stay, as the feature's *Out of scope* and decision 5 say. The S0003 helpers are left out. The docs criterion names only the project guide, as decision 5 asks.
4. factory: started tests as self.
5. tester: I wrote the guard and moved the copied helpers under the standing leave in `CLAUDE.md` (*Tests*), as the Description gives this story to the tester. No module under `src/factory/` changes, so the tests pass now and are not red. The coder has nothing to build.

   Criteria → tests:
   - criterion 1: tests/test_shared_definition.py::test_the_shared_definition_is_the_fixtures_definition
   - criterion 2: tests/test_shared_definition.py::test_each_shared_reading_is_written_in_one_module (rows `definition`, `log`)
   - criterion 3: tests/test_shared_definition.py::test_the_guard_finds_a_copy_by_its_body_and_nothing_else (six rows: the-definition-copy, the-definition-under-another-name, a-definition-of-another-text, the-log-reading-copy, a-method-named-log-lines, a-log-reading-of-another-folder)
   - criterion 4: no test function. It compares test ids before and after the story, so I checked it in this stage. `pytest --collect-only -o addopts="" -q` over the twenty modules listed 229 ids before the change and the same 229 after (`diff` empty). `make test` passed afterwards: `test: green (61.3 s)`, coverage 99.14 %.
   - criterion 5: `make check`, the factory's gate. `make lint` is green. I skipped the type check as the stage says.
   - criterion 6: docs, the documenter's.

   Files created: `tests/definition_support.py` (`pipeline_definition`) and `tests/test_shared_definition.py` (the guard, with `_copies_the_definition` and `_copies_the_log_reading` over `ast`).

   Earlier test files changed under the standing leave. Each test keeps its name and checks the same thing:
   - `tests/conftest.py`: the `definition` fixture now returns `pipeline_definition(boundaries)`.
   - `_definition` removed and its calls changed to `pipeline_definition(boundaries)` in:
     - tests/application/handlers/test_closed.py
     - tests/application/handlers/test_hand_over.py
     - tests/application/handlers/test_run.py
     - tests/application/test_after_agent.py
     - tests/application/test_board_reader.py
     - tests/application/test_no_state_refusals.py
     - tests/application/test_question_causes_recorded.py
     - tests/application/test_stall_labels.py
     - tests/application/test_stalls.py
     - tests/application/test_tick_stale_branch.py
     - tests/application/test_watcher.py
     - tests/application/test_work_items.py
     - tests/entry/test_watch.py
     - tests/entry/test_wiring_acceptance.py
     - tests/entry/test_wiring_handlers.py
     - tests/entry/test_wiring_human_handlers.py
   - `_log_lines` removed and its calls changed to `log_support.log_lines` in:
     - tests/application/test_pipeline_loading.py
     - tests/application/test_pipeline_loading_yaml_fault.py
     - tests/application/test_stop_records_service.py
     - tests/application/test_tick_disk.py
     - tests/application/test_tick_stale_branch.py
   - The module constant `LOG` in test_pipeline_loading.py and test_pipeline_loading_yaml_fault.py was removed, because no other line used it any more. `ruff --fix` then removed the imports that had become unused.

   Left alone, as the Interface says:
   - the `_definition` variants with a text parameter or another definition (test_stage_finish.py reads `DEFINITION_YAML`)
   - `tests/entry/test_run.py::_log_lines(state_directory)`
   - `tests/test_shared_fixtures.py`

   Modules the test run could not import: none.

   `lint`: lint: green (0.6 s)
   `test`: test: green (60.4 s)
6. factory: started doing as self.
7. coder: Nothing to build. The Description and Interface say no module under `src/factory/` changes; the tester made the whole change under the standing leave in `CLAUDE.md` (*Tests*): `tests/definition_support.py`, `tests/test_shared_definition.py`, the `definition` fixture in `tests/conftest.py` and the twenty test modules the Interface names. I left the working tree as the tester's commit has it. The only modified file is the work item's `.costs.jsonl` sidecar, which belongs to the factory.

   Main choice: change nothing. I rejected going over the tester's files for polish, because the coder never edits tests (R9) and none of them fails or contradicts the Interface.

   Refactor: my diff against main under `src/` is empty, so there was nothing to change.

   Description: no journal entry changed the meaning of the task, so I did not rewrite it.

   Noticed but not touched: nothing.

   `make check`: check: green (test: green (61.3 s), coverage 99.14 %).

   `check`: check: green
   `duplicates`: duplicates: 0 new, 38 known, 0 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (24 files under `tests/`, nothing under `src/`) against the work item. The changes to the twenty modules are mechanical. Each removes `_definition` or `_log_lines` and its now-unused imports (`LOG` too, where no line used it any more), and each call is changed to `pipeline_definition(boundaries)` or `log_lines(tmp_path)`. No `def test_` line is added, removed or renamed. `tests/definition_support.py` and the `definition` fixture match the Interface. The guard in `tests/test_shared_definition.py` matches the Interface's three rules. Criteria 1 to 3 each have their test. The coder's `make check` was green (journal entry 7: `check: green`, `duplicates: 0 new`). Criterion 4 has no test: it compares ids from before and after the story, and the tester checked it in their stage (229 ids, diff empty). That is acceptable for this kind of criterion.

   Findings:
   1. criterion 5 added: it needs its test. `tests/test_shared_definition.py::test_the_guard_finds_a_copy_by_its_body_and_nothing_else` leaves three limits the Interface states untested on their refused side. (a) A body holding the statement plus another one: "the one statement". (b) A method whose body is the definition statement: "at the top level", tested only for the log rule. (c) `_log_lines(tmp_path, name)`: "whose only parameter is `tmp_path`". The guard's code already refuses all three (`len(rest) == 1`, `_functions` reads only top-level nodes, the parameter list must equal `["tmp_path"]`), so nothing under `src/` changes. Fix: the tester adds the three rows that criterion 5 names to that parametrized test.

   Earlier tests changed (all under the standing leave to move a shared test helper in `CLAUDE.md` *Tests*: each change only moves the helper to the shared place, and every test keeps its name and what it checks):
   - tests/conftest.py: standing leave (the `definition` fixture now returns `pipeline_definition(boundaries)`).
   - tests/application/handlers/test_closed.py: standing leave.
   - tests/application/handlers/test_hand_over.py: standing leave.
   - tests/application/handlers/test_run.py: standing leave.
   - tests/application/test_after_agent.py: standing leave.
   - tests/application/test_board_reader.py: standing leave.
   - tests/application/test_no_state_refusals.py: standing leave.
   - tests/application/test_pipeline_loading.py: standing leave.
   - tests/application/test_pipeline_loading_yaml_fault.py: standing leave.
   - tests/application/test_question_causes_recorded.py: standing leave.
   - tests/application/test_stall_labels.py: standing leave.
   - tests/application/test_stalls.py: standing leave.
   - tests/application/test_stop_records_service.py: standing leave.
   - tests/application/test_tick_disk.py: standing leave.
   - tests/application/test_tick_stale_branch.py: standing leave.
   - tests/application/test_watcher.py: standing leave.
   - tests/application/test_work_items.py: standing leave.
   - tests/entry/test_watch.py: standing leave.
   - tests/entry/test_wiring_acceptance.py: standing leave.
   - tests/entry/test_wiring_handlers.py: standing leave.
   - tests/entry/test_wiring_human_handlers.py: standing leave.

   Considered and not raised: the walk over `tests/` in `test_each_shared_reading_is_written_in_one_module` is similar to `_defining` in `tests/test_shared_fixtures.py`. But that test takes a predicate rather than a regex, and the story leaves `test_shared_fixtures.py` unchanged. `tests/source_search.py` reads `src/factory`, not `tests/`, so the guard copies no shared helper. I did not run `make check`.
10. factory: started doing as self.
11. coder: Round 1: the reviewer's latest entry (finding 1) adds criterion 5, and it needs only its test. I changed no code and no test, and nothing under `src/factory/` changes. The working tree is as the tester's commit left it.

    Criterion 5 needs three new rows in `tests/test_shared_definition.py::test_the_guard_finds_a_copy_by_its_body_and_nothing_else`, each a refused case:
    - `def _definition(boundaries):\n    boundaries.reset()\n    return boundaries.pipeline_reader.parse(PIPELINE_YAML)\n` is not a copy of the definition, because its body holds more than the one statement.
    - `class Rig:\n    def definition(self, boundaries):\n        return boundaries.pipeline_reader.parse(PIPELINE_YAML)\n` is not a copy, because it is not at the top level of the module.
    - `def _log_lines(tmp_path, name):\n    return []\n` is not a copy of the log reading, because `tmp_path` is not its only parameter.

    Main choice: send the work item to the tester with the criterion named. I rejected adding the rows myself, because the coder never edits tests (R9).

    Description: the reviewer already added criterion 5 before the closing ones, and nothing else changed the meaning of the task, so I did not rewrite it.

    Noticed but not touched: nothing. I did not run `make check`, because I made no change.
12. factory: started tests as self.
13. tester: This round I made only the test change the coder's entry 11 names. Criterion 5, which the reviewer added, needed only its test. I added three rows to `tests/test_shared_definition.py::test_the_guard_finds_a_copy_by_its_body_and_nothing_else`. Each is a case the guard must refuse, and each row's source text is the one criterion 5 gives:
    - `a-definition-of-more-than-one-statement`: `boundaries.reset()` comes before the definition statement, so the body has more than one statement. Expected: not a copy of the definition and not a copy of the log reading.
    - `a-method-reading-the-definition`: `class Rig` with the method `definition(self, boundaries)` returning the definition statement, so it is not at the top level. Expected: neither kind of copy.
    - `a-log-reading-of-more-than-the-folder`: `_log_lines(tmp_path, name)`, so `tmp_path` is not the only parameter. Expected: neither kind of copy.

    I changed no other test and no other file. The guard's code already refuses these three cases, so the new rows pass now and are not red. Nothing under `src/factory/` changes.

    Criteria → tests:
    - criterion 1: tests/test_shared_definition.py::test_the_shared_definition_is_the_fixtures_definition
    - criterion 2: tests/test_shared_definition.py::test_each_shared_reading_is_written_in_one_module (rows `definition` and `log`)
    - criterion 3: tests/test_shared_definition.py::test_the_guard_finds_a_copy_by_its_body_and_nothing_else (its first six rows)
    - criterion 4: no test function. It compares test ids from before and after the story, which the tester checked in entry 5 (229 ids, no difference). This round adds no test to those twenty modules.
    - criterion 5: tests/test_shared_definition.py::test_the_guard_finds_a_copy_by_its_body_and_nothing_else (the three new rows above)
    - criterion 6: `make check`, which the factory runs as its gate.
    - criterion 7: docs, which the documenter writes.

    Files created: none this round. I changed `tests/test_shared_definition.py`, a test this story wrote.

    Modules the test run could not import: none.

    `test`: test: green (62.0 s), coverage 99.14 %
    `lint`: lint: green (0.2 s)

    `lint`: lint: green (0.6 s)
    `test`: test: green (60.8 s)
14. factory: started doing as self.
15. coder: Round 1: the reviewer's finding 1 asked for test rows for criterion 5. The tester added those three rows to `tests/test_shared_definition.py::test_the_guard_finds_a_copy_by_its_body_and_nothing_else` in entry 13, so the coder has nothing left to do for that finding. Nothing under `src/factory/` changes (`git diff main --stat -- src` is empty). The working tree is as the tester's commit left it. The only modified file is the work item's `.costs.jsonl` sidecar, which is the factory's.

    Main choice: change nothing and hand the work item to review. I rejected touching the tester's rows or the guard, because the coder never edits tests (R9) and nothing in them contradicts the Interface.

    Refactor: my diff has nothing in it, so there was nothing to refactor.

    Description: criterion 5 is already in the Description, before the closing criteria. No other journal entry changed the meaning of the task, so I did not rewrite it.

    Noticed but not touched: nothing.

    `make check`: check: green (test: green (61.5 s), coverage 99.14 %).

    `check`: check: green
    `duplicates`: duplicates: 0 new, 38 known, 0 gone
16. factory: started review as self.
17. reviewer: Round 1 review of `git diff main...HEAD -- . ':!factory'`: 23 files, all under `tests/`. Nothing under `src/` changed.

    What I checked:
    - `tests/definition_support.py::pipeline_definition` matches the Interface.
    - The `definition` fixture in `tests/conftest.py` keeps its name, signature and docstring and now returns `pipeline_definition(boundaries)`. `PIPELINE_YAML` is still imported there because line 225 uses it.
    - The five `_log_lines(tmp_path)` copies that were removed had the same body as `log_support.log_lines`: the same path `state/factory.log`, an empty list when the file is missing, and `splitlines`. The `LOG` constants that were removed were only used inside those copies.
    - Not one `def test_`, `assert` or `@pytest` line was removed except where `_definition(boundaries)` or `_log_lines(tmp_path)` became `pipeline_definition(boundaries)` or `log_lines(tmp_path)`.
    - The guard in `tests/test_shared_definition.py` implements the Interface's three rules. They are: top-level functions only, through `ast.parse(...).body`; a leading docstring ignored and `len(rest) == 1` compared via `ast.unparse`; the parameter list exactly `["tmp_path"]`; every `*.py` under `tests/` through `rglob`.
    - Criteria 1, 2, 3 and 5 each have their test. Criterion 5's three rows on the refused side, which the round-0 finding asked for, are now in the parametrized test (`a-definition-of-more-than-one-statement`, `a-method-reading-the-definition`, `a-log-reading-of-more-than-the-folder`), so every limit the Interface states is tested on both sides.
    - Criterion 4 has no test of its own: it compares test ids before and after the story. The tester checked it in entry 5 (229 ids, no difference), and the round-0 review accepted that.
    - The factory's `make check` after the coder was green (entry 15: `check: green`, `duplicates: 0 new`).
    - The Description and the docs criterion match what was built.

    no findings

    Earlier tests changed. All 21 are under the standing leave to move a shared test helper (`CLAUDE.md` *Tests*): each change only moves `_definition` or `_log_lines` to its shared place, and every test keeps its name and what it checks.
    - tests/conftest.py: standing leave
    - tests/application/handlers/test_closed.py: standing leave
    - tests/application/handlers/test_hand_over.py: standing leave
    - tests/application/handlers/test_run.py: standing leave
    - tests/application/test_after_agent.py: standing leave
    - tests/application/test_board_reader.py: standing leave
    - tests/application/test_no_state_refusals.py: standing leave
    - tests/application/test_pipeline_loading.py: standing leave
    - tests/application/test_pipeline_loading_yaml_fault.py: standing leave
    - tests/application/test_question_causes_recorded.py: standing leave
    - tests/application/test_stall_labels.py: standing leave
    - tests/application/test_stalls.py: standing leave
    - tests/application/test_stop_records_service.py: standing leave
    - tests/application/test_tick_disk.py: standing leave
    - tests/application/test_tick_stale_branch.py: standing leave
    - tests/application/test_watcher.py: standing leave
    - tests/application/test_work_items.py: standing leave
    - tests/entry/test_watch.py: standing leave
    - tests/entry/test_wiring_acceptance.py: standing leave
    - tests/entry/test_wiring_handlers.py: standing leave
    - tests/entry/test_wiring_human_handlers.py: standing leave

    Notes:
    - tests/test_shared_definition.py::test_each_shared_reading_is_written_in_one_module: the walk over `tests/` is similar to `_defining` in `tests/test_shared_fixtures.py`. That file is left unchanged on purpose, as the Description says, and the guard tests by a predicate, not a regex.

    I did not run `make check`.
18. factory: started docs as self.
19. documenter: Docs, round 1.

    Changed:
    - `docs/project-guide/README.md`, *Shared test helpers*: added the line for `definition_support.py` (`pipeline_definition`) after `crash_support.py`, in the form of the other lines and with the wording from the docs criterion. The grep from the smoke test now prints `1`.

    Cross-read and found current:
    - `docs/project-guide/README.md`: the `conftest.py` line already describes `definition` as the remote's parsed pipeline definition, and the `log_support.py` line already names `log_lines`.
    - `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: nothing in them touches the tests, and the criterion says none. I searched `docs/` and `README.md` for `_definition(` and `_log_lines`: no hits.

    Diff against the code: the diff holds only files under `tests/` (23 files, nothing under `src/`). It matches the Interface, so I have no findings for the coder.

    Stale text I noticed that is not mine to fix: none.

    I did not run `make check`, because I changed only a document; the factory's checks run after this stage.

    `check`: check: green (not run again: passed on tree 2f849da5ea4a at 2026-10-21T01:01:27Z)
    `secrets`: secrets: green (1.1 s)
    `documents`: documents ok
20. factory: started smoke-test as self.
21. smoke-tester: I ran the three smoke-test commands from the repository root, in order and exactly as written. All three met their `Expect:` line, and the run contradicted no acceptance criterion. I fixed nothing.

    **Command 1: the AST scan for copies of the definition and the log reading.** It met its expectation of one line, `['tests/definition_support.py', 'tests/log_support.py']`. The first `uv run` built `.venv`, and that printed setup lines before the result line:
    ```
    Using CPython 3.12.15 interpreter at: /usr/local/bin/python3.12
    Creating virtual environment at: .venv
    warning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.
             If the cache and target directories are on different filesystems, hardlinking may not be supported.
             If this is intentional, set `export UV_LINK_MODE=copy` or use `--link-mode=copy` to suppress this warning.
    Installed 106 packages in 79ms
    Bytecode compiled 4164 files in 360ms
    ['tests/definition_support.py', 'tests/log_support.py']
    ```
    The setup lines come from uv's first run in a fresh checkout, not from the scan.

    **Command 2: pytest on the guard, the shared-fixtures test, `test_board_reader.py` and `test_tick_disk.py`.** It met its expectation of `exit 0`:
    ```
    exit 0
    ```
    The command writes pytest's output to a file, so I also printed the file's tail in the same shell; it ended with `28 passed in 1.47s`.

    **Command 3: grep for the project-guide line.** It met its expectation of `1`:
    ```
    1
    ```

    **Criteria check.** The smoke test contradicts none of the criteria:
    - Criterion 2: command 1 found exactly the two shared modules.
    - Criteria 3 and 5: the guard's tests passed.
    - Criterion 7: the docs line is present.
    - Criterion 1: `tests/conftest.py:219` returns `pipeline_definition(boundaries)` from the `definition` fixture.

    The smoke test did not cover two criteria: criterion 4 (that test ids are the same before and after across the twenty modules) and criterion 6 (`make check`). I did not run either; the factory runs the stage's checks itself.

    Findings: none.
22. factory: done (pull request merged); cost: 10 runs, 9.6 min, 70 turns, 224614 tokens in (1430984 more from cache), 25569 out, $2.36
