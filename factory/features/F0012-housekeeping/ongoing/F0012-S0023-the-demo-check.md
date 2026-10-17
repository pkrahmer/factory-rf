---
stage: accept
pr: 173
blocked: null
comments_seen: 2
round: 3
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
6. coder: coder (round 1): I changed no code. Both findings from the review are missing test rows. The code in `src/factory/entry/check_demos.py` already gives the expected finding for both cases: `_is_feature_file` needs exactly `parts[1] == "feature.md"`, and `_is_backlog_story` needs a name ending in `.md` directly under `backlog/`. Every other file under `features/` is reported as "not a feature file or a backlog story".
      - Test change for the tester: in `tests/entry/test_check_demos.py::test_a_file_that_is_no_feature_file_or_backlog_story_is_a_finding`, add two rows, each expecting `demo/todo/<path>: not a feature file or a backlog story`:
        - `features/F0001-x/backlog/notes.txt`, a file in `backlog/` that does not end in `.md`
        - `features/F0001-x/notes.md`, a file directly in a feature folder that is not `feature.md`
      - These rows cover the refused side of two Interface rules that criterion 8 does not name. The test was not wrong, only incomplete. The reviewer asked for a `tests` outcome naming these rows, so I did not ask a question first.
      - Nothing else is open from round 1. `make check` was green at 8450e2d, and the tree is unchanged since then.
7. tester: tester (approved test change, from entry 6): added two rows to `tests/entry/test_check_demos.py::test_a_file_that_is_no_feature_file_or_backlog_story_is_a_finding`, and changed nothing else. Each row expects `demo/todo/<path>: not a feature file or a backlog story`:
      - `features/F0001-x/backlog/notes.txt` (id `backlog-file-not-md`): a file in `backlog/` without the `.md` ending.
      - `features/F0001-x/notes.md` (id `feature-folder-file-not-feature-md`): a file directly in a feature folder that is not `feature.md`.
      Why: the reviewer's findings 1 and 2 in entry 5. These rows test the refused side of the two Interface rules for files under `features/`, which criterion 8 does not name.
      `make test`: test: green (30.8 s). The coder's existing code already gives these findings.
      `make lint`: lint: green (0.0 s)

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (30.5 s)
8. coder: coder (round 1, after the tester's change in entry 7): I changed no code. The review's two findings (entry 5) were test rows that were missing. The tester added both rows to `tests/entry/test_check_demos.py::test_a_file_that_is_no_feature_file_or_backlog_story_is_a_finding`: `backlog-file-not-md` and `feature-folder-file-not-feature-md`. They pass against the existing `_is_backlog_story` and `_is_feature_file` in `src/factory/entry/check_demos.py`, which was built at 4f8ca43 and refactored at 8450e2d. The working tree was clean when this stage started, and `make check` is green on it. There was nothing to refactor this round. Nothing is open apart from the documents for criterion 16, which belong to the documenter.

      `make check`: check: green

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
9. reviewer: reviewer (round 1, after entries 6–8): groups 1 to 3 pass. Group 4 (quality) has one finding.
      1. `src/factory/entry/check_story.py:_check`: the new branch `if folder == "backlog": return backlog_story_findings(...)` does exactly what the fallthrough `[*check_story_place(...), *_form_findings(reader, text, form, folder)]` already does when `folder == "backlog"`. Deleting the branch changes no behaviour, so it is redundant code. It also leaves the place-then-form composition written twice in one module (once in `backlog_story_findings`, once in `_check`). Fix: write one private helper, for example `_story_findings(reader, path, text, form, folder, *, feature_file_exists)`, that holds the composition. `backlog_story_findings` returns it with `folder="backlog"`, and `_check` calls it for every folder with no branch. That way demo stories and `factory-check-story` still share one code path, which is what the Interface is after. The alternative is to keep `_check` calling `backlog_story_findings` for backlog stories and drop the duplicated list from it. Either way, `tests/entry/test_check_story.py` must keep passing unchanged.
      What holds:
      - Group 1: criteria 1–14 each have a test that checks what the criterion says. The two rows added in entry 7 cover the refused side of the `feature.md` rule and the `.md` rule (the earlier findings 1 and 2). Both sides of the index rule are tested: `` `other/` `` and a bare `todo`. The coder's entry 8 reports `make check` green.
      - Group 2: `check_demos` is in `factory.entry` and gets both readers from the wiring. `build_pipeline_definition_reader()` is a justified, logged deviation, because `test_wiring.py` lets only the wiring import adapters. No layer rule is broken.
      - Group 3: no shell, no secrets, no suppression markers. `PipelineDefinitionInvalid` is the only error `RuamelPipelineDefinitionReader.parse` raises, so catching only that is complete.
      I did not reach group 5 (ticket hygiene), because the role skill stops at the first failing group.
10. coder: coder (round 2): fixed the one finding from entry 9. `src/factory/entry/check_story.py` now builds the place-then-form findings in one place only.
       - New private `_story_findings(reader, story, form)` returns the place findings and then the form findings. Its input `_Story` is a small private frozen model with `path`, `text`, `folder` and `feature_file_exists`, next to the existing `_Read`.
       - `backlog_story_findings` calls it with `folder="backlog"`, and its public signature is unchanged.
       - `_check` calls it for every folder. The redundant `if folder == "backlog"` branch is gone.
       - Main decision: I took the reviewer's first option, so demo stories and `factory-check-story` share one code path. A plain 6-argument helper broke ruff's PLR0913 limit, and `src` has no suppressions, so I put the arguments in a model instead of adding a `noqa`. I rejected the reviewer's second option (calling `backlog_story_findings` from `_check`): started stories would still need their own place-then-form list.
       - Commits: cea1e90 is the helper. Its own `make check` was red (lint, PLR0913) because my pipe hid the exit status, and it was committed anyway. 4b9cbcf fixes it with the `_Story` model. `make check` is green at 4b9cbcf.
       - Behaviour is unchanged and no tests were touched. `tests/entry/test_check_story.py` and `tests/entry/test_check_demos.py` pass.
       - Still open: the documents for criterion 16, which belong to the documenter.

       `make check`: check: green

    `make check`: check: green
    `make duplicates`: duplicates: 0 new, 39 known, 0 gone
11. reviewer: reviewer (round 2, after entry 10): groups 1 to 3 pass. Group 4 (quality) has one finding.
       1. `src/factory/entry/check_demos.py:70` (`_story_findings`) assembles the project path by hand as `f"{FEATURES_DIRECTORY}/{feature}/{_BACKLOG}/{story}"`, with its own `_BACKLOG = "backlog"` constant at line 23. `factory.domain.paths.work_item_path(feature_directory, folder, file_name)` already builds exactly this path, and `"backlog"` is already a `LifecycleFolder` value. CLAUDE.md counts a second copy of an existing helper as a finding. Fix: call `work_item_path(feature, "backlog", story)`. Keep `_BACKLOG` only for the folder-name test in `_is_backlog_story`, or type it as `LifecycleFolder` so that both uses share the domain's literal. Behaviour does not change, and no test changes.
       What holds:
       - Entry 9's finding is fixed. `check_story.py:_story_findings` is now the one place that composes place findings and then form findings. `backlog_story_findings` and `_check` both call it, and the redundant `backlog` branch is gone. The public signatures are as the Interface states.
       - The `_Story` model avoids a `noqa` for PLR0913. It is private, frozen and forbids extra keys, which is acceptable.
       - Group 1: the tests are unchanged since round 1's review (the last test commit is 25890db). The coder's entry 10 reports `make check` green at 4b9cbcf.
       - Groups 2 and 3: nothing has changed since entry 9.
       I did not reach group 5 (ticket hygiene).

    This story has now been sent back 3 times, more than 2. What should happen? Answer with a comment; close the pull request to discard the story.
12. human (pull request comment, 2026-10-17): Go forward: the story passes review as it is. The second assembly of the backlog path in `check_demos.py` (instead of `work_item_path(feature, "backlog", story)`) is left for now and recorded as a FEATURE decision for a later fix; behaviour does not change.
13. reviewer: reviewer (round 3, after the human's answer in entry 12): no findings. The story goes forward to docs.
       - Following entry 12, the finding in entry 11 is not a finding this round. That finding was the second assembly of the backlog path at `src/factory/entry/check_demos.py:70`, where `work_item_path(feature, "backlog", story)` already exists. The human leaves it as it is and records it as a FEATURE decision for a later fix. Behaviour does not change.
       - No code or test has changed since the round-2 review: the last code commit is 4b9cbcf and the last test commit is 25890db. Groups 1 to 4 therefore stand as entries 9 and 11 found them. In group 4, only the deferred point was open, and I found nothing new on reading the full diff again.
       - Group 5 (ticket hygiene), which earlier rounds did not reach, holds:
         - The log names the main decision: demo stories go through the story check's `backlog_story_findings` and `finding_line`, so `check_demos` has no story logic of its own. It also names what was rejected: calling `check_story_place`/`check_story_form` directly, and keeping the `backlog` branch in `_check`.
         - `Assignment` matches what was built.
         - The one deviation from the Interface's wording is logged in entry 4 with its reason. The pipeline definition reader comes from the new `build_pipeline_definition_reader()` in `src/factory/entry/wiring.py`, not from `RuamelPipelineDefinitionReader()` directly, because `tests/entry/test_wiring.py` lets only the wiring import adapters. The reader and its behaviour are the same.
         - Criterion 16 still describes what the documenter must write: the README pointer, the project guide's *The demos*, and the decision log entry that the code knows no demo by name.
       - Open: the documents for criterion 16 (documenter), and the deferred `work_item_path` reuse (the human's FEATURE decision). I did not run `make check`. The coder's entry 10 reports it green at 4b9cbcf.
14. documenter: docs (round 3): wrote the documents for criterion 16. I changed no code, so I did not run `make check`; the factory's run after this stage is the gate.
    - `README.md`: the "Where to look next" list now names `demo/` and `python -m factory.entry.check_demos`, and says `make check` runs the same check through `tests/test_demos.py`.
    - `docs/project-guide.md`: new section *The demos*. It covers the layout of a demo (`README.md`, `project/` with the pipeline definition and the story form, `features/` with `feature.md` and `backlog/` stories) and the index line. It lists the rules of the check in the Interface's order, says that stories are checked as backlog stories at the path they will have in the project through `backlog_story_findings` and `finding_line`, and says that `make check` runs it through `tests/test_demos.py`.
    - `docs/decisions.md`: new entry *The demo check knows no demo by name*, with the reasons and what was rejected (a table of demos; a second copy of the story check).
    - Run: `uv run python -m factory.entry.check_documents` prints `documents ok`, and `uv run python -m factory.entry.check_demos` prints `demos ok`.
    - Cross-read against the diff and found current: the operator guide's description of `factory-check-story`, and *The form check of a story* and *The check command* in the project guide. Behaviour is the same for the existing commands.
    - Code vs. docs: the code matches the Interface, with the logged deviation that the pipeline definition reader comes from `build_pipeline_definition_reader()` in the wiring; the guide says so. No findings.
    - Seen and not touched: the second assembly of the backlog path in `check_demos.py`, in place of `work_item_path`. The human deferred it in entry 12, so it is not documented as a defect.

    `make check`: check: green
    `make documents`: documents ok
15. demo: demo (round 3): I ran both demo commands from the repository root, in order and exactly as written. Both met their `Expect:` lines. There are no findings.

    1. `uv run python -m factory.entry.check_demos; echo "status $?"`
    ```
    demos ok
    status 0
    ```
    Met: the two lines are `demos ok` and `status 0`.

    2. `uv run pytest --no-header -p no:cacheprovider tests/entry/test_check_demos.py tests/test_demos.py`
    ```
    .......................                                                  [100%]
    23 passed in 0.08s
    ```
    Met: the last line is `23 passed in 0.08s`, with no `failed`, `error` or `skipped` count.

    Checked against the acceptance criteria: this repository has no `demo/` folder yet (`ls demo` reports that it does not exist). So command 1 is criterion 1 run on the real root: no finding, `demos ok`, exit 0. It is also criterion 14: the `--root` default is the current directory, and the root is the repository root. This fits the Assignment ("Until step 2 there is no demo, and the check passes"). Command 2 runs the tests for criteria 1–14, and all of them pass. The demo contradicts no criterion. I did not run `make check` (criterion 15) or `make documents` (part of criterion 16); the factory runs `make check` itself, and entry 14 reports both green.

    Open, from earlier entries and not a demo finding: in entry 12 the human deferred reusing `work_item_path` in `src/factory/entry/check_demos.py` to a later fix.
