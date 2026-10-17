---
stage: doing
pr: 173
blocked: null
comments_seen: 0
round: 1
attempts: 0
---
# The demo check

## Assignment (as of log entry 1)

v1.1 ships its demos in `demo/`, one folder per demo, because there will be demos of different kinds of project (the human's word, "The demo, shipped with v1.1"). The first, the to-do service of v1's run 4, is written by hand in step 2 and is the input of the todo run. A demo that no test reads goes stale as v1.1 changes: its stories stop passing the story check, its pipeline definition stops loading. This story builds the check every demo must pass and runs it in `make check` over this repository's `demo/`: each demo folder holds its three parts, each of its stories passes v1.1's story check as a backlog story at the path it will have in the project, its `project/factory/pipeline.yml` passes the pipeline definition reader, and the index `demo/README.md` names it. A demo's name is its folder; nothing in the code knows the list. Until step 2 there is no demo, and the check passes. The index is the human's file (change H6, after this story), because no write path covers `demo/`.

## Interface

`src/factory/entry/check_demos.py` (new):

```python
def check_demos(root: Path) -> list[str]:
    """The findings of every demo under `root / "demo"`, one line each, in path order."""

def main(argv: Sequence[str] | None = None) -> int:
    """Print `demos ok` and return 0, or print one line per finding and return 1."""
```

`main` takes `--root <path>` (default: the current directory) and passes `argv` to `argparse` as given. `check_demos` finds, in this order:

- No `demo/` folder under `root`: no finding.
- `demo/` without a file `README.md`: `demo/README.md: missing`.
- Every folder `demo/<name>/` (files directly under `demo/` other than `README.md`, and folders whose name starts with `.`, are skipped), in name order:
  - `demo/README.md` has no line that holds `` `<name>/` ``: `demo/README.md: names no demo '<name>'`.
  - each of `README.md` (a file), `project/` and `features/` (folders) that is missing: `demo/<name>: missing <part>` (`missing README.md`, `missing project/`, `missing features/`). Without `project/`, nothing under it and no story is checked; without `features/`, no story is checked.
  - `project/factory/pipeline.yml` missing: `demo/<name>: missing project/factory/pipeline.yml`; present but refused by `RuamelPipelineDefinitionReader().parse`: `demo/<name>/project/factory/pipeline.yml: <the fault>`.
  - `project/factory/story-form.md` missing: `demo/<name>: missing project/factory/story-form.md` (then no story is checked).
  - every file under `features/`, in path order: it must be `features/<feature>/feature.md` or `features/<feature>/backlog/<story>.md`; any other file gives `demo/<name>/features/<rest>: not a feature file or a backlog story`. A backlog story is checked as the factory checks it on `main`: `check_story_place("factory/features/<feature>/backlog/<story>.md", feature_file_exists=<features/<feature>/feature.md exists>)`, then its text read with `FrontmatterWorkItemReader().parse_specification` and `check_story_form(<document>, <the story form>, folder="backlog")`; a `WorkItemFormatError` of the reader is one finding with its fault. Each finding is `demo/<name>/features/<rest>: <message>`, or `demo/<name>/features/<rest>:<line>: <message>` when the finding has a line.

The story part is the story check's own: `factory.entry.check_story` gains `backlog_story_findings(reader: WorkItemReader, path: str, text: str, form: str, *, feature_file_exists: bool) -> list[FormFinding]`, the place findings of `path` and then the form findings of `text` read as a specification (a `WorkItemFormatError` of the reader is one finding with its fault), and `finding_line(path: str, finding: FormFinding) -> str`, `<path>: <message>` or `<path>:<line>: <message>`. `factory-check-story` uses both for a backlog story and `check_demos` for every demo story; the reader is `build_work_item_reader()` of `factory.entry.wiring`. The tests of `tests/entry/test_check_story.py` still pass unchanged.

Tests: `tests/entry/test_check_demos.py` (criteria 1 to 13, with demos written into `tmp_path`, the pipeline definition `PIPELINE_YAML` and the form `STORY_FORM` of `tests/git_support.py`, and story texts that pass that form); `tests/test_demos.py` (criterion 14), which runs `main(["--root", <the repository root>])` and expects 0, so `make check` checks every demo.

## Acceptance criteria

1. A root without `demo/` gives no finding, and `main` prints `demos ok` and returns 0.
2. A complete demo `todo` (its `README.md`; `project/factory/pipeline.yml` = `PIPELINE_YAML`; `project/factory/story-form.md` = `STORY_FORM`; `features/F0001-x/feature.md`; one valid backlog story `features/F0001-x/backlog/F0001-S0001-first.md`) with an index that holds `` `todo/` `` gives no finding.
3. Without the index file: `demo/README.md: missing`; with an index that does not name the demo: `demo/README.md: names no demo 'todo'`.
4. A demo without its `README.md`, without `project/` or without `features/` gives exactly the one finding `demo/todo: missing README.md`, `demo/todo: missing project/` or `demo/todo: missing features/` respectively. Three rows of one parametrized test.
5. A demo whose pipeline definition holds a repeated key gives one finding that starts with `demo/todo/project/factory/pipeline.yml: not valid YAML`; one without the file gives `demo/todo: missing project/factory/pipeline.yml`.
6. A demo without the story form gives `demo/todo: missing project/factory/story-form.md` and no finding of its stories.
7. A backlog story without its `## Smoke test` section gives the finding the story check gives for it, prefixed `demo/todo/features/F0001-x/backlog/F0001-S0001-first.md`; a story `F0002-S0001-other.md` in the folder of `F0001-x` gives the place finding `the story F0002-S0001 is in the directory of feature F0001`; a feature folder without `feature.md` gives the finding that the feature file is missing.
8. A file `features/F0001-x/in-progress/F0001-S0002-y.md` or `features/notes.txt` gives `... : not a feature file or a backlog story`. Two rows of one parametrized test.
9. Two demos `a` and `b`, each with one finding, give `a`'s findings before `b`'s; `main` prints each finding on its own line and returns 1.
10. A file `demo/notes.txt` and a folder `demo/.cache/` holding a file, beside the complete demo `todo` of criterion 2, give no finding: neither is a demo, and the index need not name them.
11. Within one demo the story findings come in path order, and a finding with a line carries it: with `features/F0001-x/backlog/F0001-S0001-first.md` carrying the journal entry `1. 2026-10-17 human: created.` and `features/F0001-x/backlog/F0001-S0002-second.md` without its `## Smoke test`, the findings are exactly `demo/todo/features/F0001-x/backlog/F0001-S0001-first.md:<n>: a backlog story carries no journal entries`, `<n>` the line of that entry in the file, then `demo/todo/features/F0001-x/backlog/F0001-S0002-second.md: missing section: ## Smoke test`.
12. A backlog story whose text starts with front matter that is not valid YAML (`---\na: [\n---\n`) gives exactly one finding for that story, `demo/todo/features/F0001-x/backlog/F0001-S0001-first.md: front matter is not valid YAML`.
13. `main([])`, run with the current directory at a root whose complete demo `todo` has no index, prints `demo/README.md: missing` and returns 1: the root defaults to the current directory.
14. `main(["--root", <the repository root>])` returns 0 (this repository's `demo/`, whatever it holds).
15. `make check` stays green.
16. docs: the README's pointer list names `demo/` and `python -m factory.entry.check_demos`; the project guide gets a section *The demos*: the layout of a demo (its three parts and what `project/` and `features/` hold), the rules of the check, that `make check` runs it through `tests/test_demos.py`, and that a demo's stories are backlog stories checked at the path they will have in the project; the decision log records that the code knows no demo by name. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -m factory.entry.check_demos; echo "status $?"
```
Expect: two lines, `demos ok` and `status 0`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/entry/test_check_demos.py tests/test_demos.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: `check_demos` and `main` in `factory.entry.check_demos` have concrete signatures. `backlog_story_findings` and `finding_line` are added to `factory.entry.check_story`. The names it relies on exist: `check_story_place`, `check_story_form`, `FormFinding`, `WorkItemFormatError`, `parse_specification` and `build_work_item_reader`. I did not check `RuamelPipelineDefinitionReader` or the existing `check_story` module.
   - Criteria: criteria 1 to 14 are each one test, and every Interface rule has both sides covered. No `demo/` and an empty `demo/` give no finding (1, 10). A missing index and an index that does not name the demo each give a finding (3). Missing parts, a missing pipeline file and a missing form each give a finding (4 to 6). Stray files give a finding (8). The skipped entries, `demo/notes.txt` and `demo/.cache/`, are in 10. Ordering is in 9 and 11, a reader fault in 12, and the default root in 13. Criteria 15 and 16 are the closing two.
   - Demo: both commands are runnable. The first has an `Expect:` of `demos ok` and `status 0`. The second expects a last line of `<n> passed` with no failed, error or skipped count. Both can be checked against the output.
   - Architecture: the new module is in `factory.entry`, a command and not wiring of tools. It reuses the domain checks and the reader that `wiring` builds, and adds no helper of its own because `check_story` supplies the shared ones. It stays within the layer rules.
   - Scope: the story falls under FEATURE.md item 1.7, "the demo check and its test in make check (S0023)". The index README is left to the human's H6, as the feature says.
3. tester: red on purpose. `make test` stops with collection errors (ImportError) in both new modules because `factory.entry.check_demos` does not exist yet. `make lint` is green. I skipped the type check, as this stage's skill says to.
   - criterion 1: tests/entry/test_check_demos.py::test_a_root_without_demos_gives_no_finding
   - criterion 2: tests/entry/test_check_demos.py::test_a_complete_demo_named_in_the_index_gives_no_finding
   - criterion 3: tests/entry/test_check_demos.py::test_a_missing_index_is_a_finding, ::test_an_index_that_does_not_name_the_demo_is_a_finding. This is two rules, so two tests. The index in the second test names `` `other/` `` and holds a bare `todo` without the backticks and slash.
   - criterion 4: tests/entry/test_check_demos.py::test_a_missing_part_of_a_demo_is_the_one_finding, with three rows: readme, project and features.
   - criterion 5: tests/entry/test_check_demos.py::test_a_pipeline_definition_with_a_repeated_key_is_a_finding (the test adds `attempts_cap: 3` to `PIPELINE_YAML`, so the key appears twice), ::test_a_missing_pipeline_definition_is_a_finding
   - criterion 6: tests/entry/test_check_demos.py::test_without_the_story_form_no_story_is_checked. The story in this test also lacks its Smoke test, so it would give a finding if it were checked.
   - criterion 7: tests/entry/test_check_demos.py::test_a_story_without_its_smoke_test_gives_the_story_check_finding, ::test_a_story_in_the_folder_of_another_feature_gives_the_place_finding, ::test_a_feature_folder_without_its_feature_file_gives_the_place_finding. The last one expects the exact message of `check_story_place`: `the feature file feature.md is missing in factory/features/F0001-x`.
   - criterion 8: tests/entry/test_check_demos.py::test_a_file_that_is_no_feature_file_or_backlog_story_is_a_finding, with two rows: started-story and loose-file.
   - criterion 9: tests/entry/test_check_demos.py::test_findings_of_two_demos_come_in_name_order_and_main_prints_them. Demo `a` has no `features/` and demo `b` has no `README.md`.
   - criterion 10: tests/entry/test_check_demos.py::test_a_loose_file_and_a_hidden_folder_under_demo_are_no_demos
   - criterion 11: tests/entry/test_check_demos.py::test_story_findings_come_in_path_order_and_carry_their_line. The expected line is that entry's line in the file text.
   - criterion 12: tests/entry/test_check_demos.py::test_a_story_with_front_matter_that_is_not_yaml_is_one_finding
   - criterion 13: tests/entry/test_check_demos.py::test_the_root_defaults_to_the_current_directory, using `monkeypatch.chdir`.
   - criterion 14: tests/test_demos.py::test_the_shipped_demos_pass_the_demo_check, run on the repository root, which is `Path(__file__).parents[1]`.
   Files created: tests/entry/test_check_demos.py and tests/test_demos.py.
   Module the runner could not import: `factory.entry.check_demos`.
   There are no separate tests of `backlog_story_findings` or `finding_line` in `factory.entry.check_story`. The criteria reach them only through `check_demos`, and the existing tests in tests/entry/test_check_story.py stay unchanged, as the Interface requires.

   `make lint`: lint: green (0.0 s)
   `make test`: ERROR tests/test_demos.py - ImportError while importing test module '/work/fa...
4. coder: the demo check is built and `make check` is green. All tests in tests/entry/test_check_demos.py and tests/test_demos.py pass, and tests/entry/test_check_story.py passes without changes.
      - `src/factory/entry/check_demos.py` (new): `check_demos(root)` and `main(argv)`, with `--root` defaulting to the current directory. The checks run in the order the Interface gives: no `demo/`, a missing index, then each demo folder in name order. Loose files and hidden folders are skipped. For each demo it checks that the index names it, its three parts, `project/factory/pipeline.yml` and `project/factory/story-form.md`. Then it reads every file under `features/` in path order. Each backlog story is checked at `factory/features/<feature>/backlog/<story>.md`, and any other file is "not a feature file or a backlog story". The paths come from the constants in `factory.domain.paths`.
      - `src/factory/entry/check_story.py`: adds `backlog_story_findings` (the place findings, then the form findings of the text read as a specification; a `WorkItemFormatError` becomes one finding) and `finding_line`. `factory-check-story` now uses both for backlog stories. Started stories go through the same path as before.
      - `src/factory/entry/wiring.py`: adds `build_pipeline_definition_reader()`. The Interface names `RuamelPipelineDefinitionReader().parse`, but `tests/entry/test_wiring.py` allows only the wiring to import adapters in the entry layer. So `check_demos` gets the reader from the wiring, the same way it gets `build_work_item_reader()`. The reader and its behaviour are unchanged.
      - Main decision: check_demos holds no story logic of its own. Story findings come from the story check's `backlog_story_findings` and `finding_line`, so a demo story and `factory-check-story` give the same findings. I rejected calling `check_story_place`/`check_story_form` directly from check_demos, because that would be a second copy of `_form_findings`.
      - Refactor (8450e2d): the demo check now uses one constant for `README.md`. It had both an `_INDEX` constant and a bare literal for the same name.
      - Noticed: `uv run python -m factory.entry.check_demos` prints `demos ok` because the repository has no `demo/` yet. `make duplicates`: 0 new, 39 known, 0 gone. Docs (criterion 16) are left to the documenter.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: Group 1 (acceptance criteria) fails. Following the role skill, I stopped there and did not report later groups.
   1. `tests/entry/test_check_demos.py::test_a_file_that_is_no_feature_file_or_backlog_story_is_a_finding`: no row has a file in `backlog/` that does not end in `.md`. So removing `parts[2].endswith(".md")` from `src/factory/entry/check_demos.py:_is_backlog_story` would still pass every test. Fix: add a row `features/F0001-x/backlog/notes.txt` that expects `... : not a feature file or a backlog story`.
   2. Same test: no row has a file directly in a feature folder that is not `feature.md`. So `src/factory/entry/check_demos.py:_is_feature_file` could ignore the file name (`parts[1] == FEATURE_FILE_NAME`) and every test would still pass. Fix: add a row `features/F0001-x/notes.md` that expects `... : not a feature file or a backlog story`.
   This is a gap in the story, not a fault of the tester. The Interface's rule says a file must be `features/<feature>/feature.md` or `features/<feature>/backlog/<story>.md`, but criterion 8 names only two of its refused cases (a wrong lifecycle folder and a loose file). The `.md` ending and the `feature.md` name have no criterion for their refused side. Both rows are changes to a test the coder did not write, so the coder should end with `tests` and name these two rows for the tester. The code itself already gives the expected findings.
   Everything else in group 1 holds:
   - Criteria 1–14 each have a test that checks what the criterion says.
   - The coder's entry reports `make check` green.
   - The deviation from the Interface is justified and logged: the pipeline definition reader comes through `build_pipeline_definition_reader()` in the wiring, because `test_wiring.py` lets only the wiring import adapters.
