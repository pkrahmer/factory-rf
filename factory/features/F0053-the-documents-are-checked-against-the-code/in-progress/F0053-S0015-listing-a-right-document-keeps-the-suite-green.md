---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 603
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T19:50:35.013865Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T19:50:35.021066Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T19:50:55.185729Z'
  stage: intake
  run: 1165b19bf69d45fca6bdd3fc38e05b1e
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T19:50:59.950898Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-06T19:52:53.080087Z'
  stage: tests
  run: a695e6f7919840baa3ae30109fd95a27
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T19:52:58.727994Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-06T19:57:11.722392Z'
  stage: doing
  run: e4a04ca884c6482da92d9d41d73b1e92
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-06T19:57:16.959789Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-06T19:58:10.001743Z'
  stage: review
  run: 3716b8331880461581ea18b12949299d
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-06T19:58:15.579394Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-11-06T19:58:40.742937Z'
  stage: doing
  run: 5c9ac453c4e84e93b1b3ff07c625b27b
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-06T19:58:45.938537Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-11-06T19:59:44.299874Z'
  stage: tests
  run: a982f14ec05d4ba5ad3e9e7e785b4c66
---

# Listing a right document keeps the suite green
## Description

The rewrite adds each document to `docs/checked-documents.txt` once it is rewritten, and a right document on the list must keep `make check` green. Today three earlier tests read the repository's own list through the `documents` copy, and each one expects a page to be unlisted. Listing `docs/operator-guide/install.md` fails two of them. The settings test expects a dropped settings row to leave the exit status as it was, and the operator guide test's `no-install-file` row gets the extra line `docs/checked-documents.txt: docs/operator-guide/install.md is no document of the check`. Listing `docs/operator-guide/README.md` fails the `no-index` row and the five rows of the suite copy test that use the `no-index` change. Listing `docs/project-guide/shared.md` fails the copies test's `unlisted-reported` row. `make documents` passes with all three listed (`documents ok`), but `make check` goes red with nine failed rows. The rewrite's first story lists `install.md`, so its docs stage would stall at once. This story makes each of these tests write the list it needs into its copy instead of reading the repository's list. Then no change to the list changes their outcome. The check, its output, the `documents` fixture and the list itself stay as they are. A wrong runnable example still fails the suite in any document.

## Interface

- `tests/support/check_documents_support.py`, new helper `write_checked_list(root: Path, paths: Sequence[str]) -> None`. It writes `docs/checked-documents.txt` under `root` with one path per line, or as an empty file when `paths` is empty, and commits it in the copy. The helper sits with the other shared helpers of that module.
- `tests/entry/test_check_documents_settings.py::test_settings_findings_are_printed_without_changing_the_exit_status`: before its first run, the test writes a list without `docs/operator-guide/install.md` through `write_checked_list`. Its name stays, because it checks an unlisted guide. The listed side is already tested in `tests/entry/test_check_documents_checked_files.py::test_a_new_finding_blocks_in_a_listed_file_and_is_reported_in_any_other`.
- `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file`: before the row's change, every row writes an empty list through `write_checked_list`. Every row keeps its id and its expected output.
- `tests/entry/test_check_documents_suite_copy.py::test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line`: the same, an empty list before the block is appended. Every row keeps its id and its expected output.
- `tests/entry/test_check_documents_copies.py`: `_append_example` writes the list for both pages through `write_checked_list`, `[LISTED]` for the listed page and `[]` for the unlisted one. Every test keeps its name and its rows.
- These are earlier tests, and the standing leave does not cover them. Feature decision 8 gives the human's leave. The leave covers the four tests above and any other earlier test whose only failure is that the repository's list names a page. Every changed test keeps its name and what it checks, and the entry names each one.
- New rows go in a new module `tests/entry/test_check_documents_any_list.py`, which uses the `documents` copy.
- No module under `src/factory/` changes, and neither do `docs/checked-documents.txt` nor the `documents` fixture.

## Acceptance criteria

1. In a `documents` copy whose `docs/checked-documents.txt` also names `docs/operator-guide/README.md`, `docs/operator-guide/install.md` and `docs/project-guide/shared.md`, committed, the four tests of the Interface pass. Each pass is checked by calling the test's own steps on that copy: the settings test's two runs give the same exit status, the `no-index` change gives exactly `docs/operator-guide/README.md: missing\n` with exit status 1, and an `echo one` / `two` example in `docs/project-guide/shared.md` is printed after the report heading with exit status 0 when the test writes an empty list. These are rows of one parametrized test, one row per listed page.
2. The failing side: in the same copy, without `write_checked_list`, the `no-index` change prints the extra line `docs/checked-documents.txt: docs/operator-guide/README.md is no document of the check`. This shows that the repository's list reaches the output and that the helper is what keeps it out.
3. `write_checked_list(root, [])` leaves `docs/checked-documents.txt` empty and `write_checked_list(root, ["docs/project-guide/style.md"])` leaves exactly `docs/project-guide/style.md\n`. After either call, `git status --porcelain` in the copy prints nothing (rows of one test).
4. Every earlier row of the four tests named in the Interface passes with today's documents and today's list, under its old id.
5. `make check` stays green.
6. docs: `docs/project-guide/shared.md`, *The settings check*: the reader learns that a settings or refusal finding blocks the command in a listed `install.md` and is only reported in an unlisted one, as for the name and example findings. The sentence that says they never change the exit status goes.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git clone -q . "$d/c" && cd "$d/c"
printf 'docs/operator-guide/README.md\ndocs/operator-guide/install.md\ndocs/project-guide/shared.md\n' >> docs/checked-documents.txt
PATH="$OLDPWD/.venv/bin:$PATH" python -m factory.entry.check_documents --root . | tail -1
PATH="$OLDPWD/.venv/bin:$PATH" python -m pytest -p no:cacheprovider -o addopts= tests/entry/test_check_documents_settings.py tests/entry/test_check_documents_operator_guide.py tests/entry/test_check_documents_copies.py tests/entry/test_check_documents_suite_copy.py 2>&1 | tail -1
```
Expect: the first command prints `documents ok (<seconds> s)`. The second prints a last line `<n> passed in <seconds>s`, with no `failed` in it. Before this story the same commands print `documents ok` and then `9 failed, 12 passed`.

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete modules and signatures: the new helper `write_checked_list(root: Path, paths: Sequence[str]) -> None` in `tests/support/check_documents_support.py`, the four earlier tests by path and name, and the new module `tests/entry/test_check_documents_any_list.py`. Nothing under `src/` changes. The leave for the earlier tests is feature decision 8.
   - Criteria: each is testable by one parametrized test. Criterion 1 has one row per listed page, criterion 2 is the failing side (the extra line appears without the helper), criterion 3 covers the helper for an empty list and for a non-empty one, plus a clean `git status`. Criterion 4 keeps the old rows and ids. The helper's behaviours (one path per line, empty file, commit) each have a criterion.
   - Smoke test: runnable. The pytest command passes `-o addopts=`, so there is no `-q` clash. Each Expect line is checkable: `documents ok`, a last line `<n> passed in`, and no `failed`. The before state is stated as `9 failed, 12 passed`.
   - Docs criterion: names what the reader must know (a settings or refusal finding blocks in a listed `install.md` and is only reported in an unlisted one). It dictates no sentences. Naming the sentence to drop is a removal of a false claim, not text to write.
   - Architecture: this is test support only, placed in `tests/support/` as CLAUDE.md requires. No test module imports another.
   - Scope: within feature decision 8 and outside the feature's "Out of scope". Route: tests, because the Interface changes tests and support code, not only documents.
4. factory: started tests as vm.
5. tester: Wrote the tests and the test helper this story needs. All of its work is under `tests/`, so the tests are green now instead of red. The new and changed tests pass in one run: `uv run pytest -q` over the five modules gave 27 passed, and `make lint` is green. No module was missing: every import resolved.

   Criteria → tests:
   - criterion 1: tests/entry/test_check_documents_any_list.py::test_a_test_that_writes_its_list_keeps_its_outcome_when_the_repository_lists_more_pages. It has one row per listed page: `install` runs the settings test's steps (same exit status for both runs), `operator-guide-index` runs the `no-index` steps (exactly `docs/operator-guide/README.md: missing\n`, exit 1), and `shared` puts an `echo one`/`two` example after the report heading (exit 0). Its fixture `listed` adds the three pages to the copy's list and commits.
   - criterion 2: tests/entry/test_check_documents_any_list.py::test_without_its_own_list_the_repository_list_reaches_the_output
   - criterion 3: tests/entry/test_check_documents_any_list.py::test_the_written_list_holds_one_path_per_line_and_is_committed (rows `empty` and `one`)
   - criterion 4: the earlier rows of the four tests, under their old names and ids:
     - tests/entry/test_check_documents_settings.py::test_settings_findings_are_printed_without_changing_the_exit_status
     - tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file
     - tests/entry/test_check_documents_suite_copy.py::test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line
     - tests/entry/test_check_documents_copies.py (`_append_example`)
   - criteria 5 and 6: `make check` and docs, no test.

   Files created: tests/entry/test_check_documents_any_list.py.

   Earlier test files changed:
   - tests/support/check_documents_support.py: new `write_checked_list`. Two constants, `CHECKED_LIST` and `INSTALL`, and `drop_settings_row` moved here.
   - tests/entry/test_check_documents_settings.py: writes an empty list first. Its private `_drop_row` moved to the support module as `drop_settings_row`, so the new module can reuse the settings test's steps. That move is under the standing leave for shared helpers.
   - tests/entry/test_check_documents_operator_guide.py and tests/entry/test_check_documents_suite_copy.py: each row writes an empty list first.
   - tests/entry/test_check_documents_copies.py: `_append_example` writes `[LISTED]` or `[]` through the helper.

   The four test changes rest on feature decision 8, as the Interface names it. Every test keeps its name, its ids and what it checks.

   Open: there is nothing for the coder to write under `src/`, and the type check was not run in this stage. The coder's `make check` covers it, and the docs criterion is left to the docs stage.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: Wrote no code. Everything this story needs is under `tests/`, and the tester already wrote it: `tests/support/check_documents_support.py` (`write_checked_list`, plus the moved `CHECKED_LIST`, `INSTALL` and `drop_settings_row`), the new `tests/entry/test_check_documents_any_list.py`, and the four changed earlier tests. The Interface says no module under `src/factory/` changes, and neither do `docs/checked-documents.txt` nor the `documents` fixture. My only step was the full `make check`, which the tester had not run (they ran only lint and the five modules). It ended `test: green (103.7 s)` and `check: green`, so `mypy --strict` passes over the new tests too.

   Main decision: I added nothing under `src/`. The alternative was to change the check so that an unlisted path in the repository's list is not reported. I rejected it because the Interface keeps the check and its output as they are, and the failing-side test (criterion 2) depends on that line appearing.

   Refactor: there is no diff of mine to refactor (`git diff main -- . ':!factory' ':!tests'` is empty). The journal did not change the meaning of the task, so the Description stays.

   Noticed but not touched: criterion 6, the change to `docs/project-guide/shared.md` *The settings check*, is open for the docs stage.

   `check`: check: green
   `duplicates`: duplicates: 6 new, 39 known, 4 gone
8. factory: started review as vm.
9. reviewer: Review, round 0. I read the work item and `git diff main...HEAD -- . ':!factory'`: six test files, nothing under `src/`. Groups 1, 2, 3 and 5 hold. Every criterion has a test that checks what the criterion says. Criterion 1 is one parametrized test with one row per listed page (`install`, `operator-guide-index`, `shared`). Criterion 2 is the run without the helper, which shows the extra list line. Criterion 3 has the rows `empty` and `one` plus a clean `git status`. Criterion 4 is the four earlier tests, which keep their names and ids. The coder's `make check` was green (journal entry 7). No `src/` change, no silencing marker and no secret. The Description, Interface and docs criterion still match what was built. The findings are all group 4: helpers copied from constants that already exist. The support module is an earlier file, and the new module is judged at round 0, so these send the story back.

   Findings:
   1. `tests/support/check_documents_support.py:32`: `CHECKED_LIST = "docs/checked-documents.txt"` copies `CHECKED_DOCUMENTS` from `src/factory/shared/domain/documents.py:564`. Fix: drop the constant. Use `CHECKED_DOCUMENTS` in `write_checked_list` and in `tests/entry/test_check_documents_any_list.py`, which imports `CHECKED_LIST`.
   2. `tests/support/check_documents_support.py:33`: `INSTALL = "docs/operator-guide/install.md"` copies `OPERATOR_INSTALL` from `src/factory/shared/domain/documents.py:25`, which `tests/support/document_texts.py` already imports. Fix: drop `INSTALL` and use `OPERATOR_INSTALL` in `drop_settings_row`.
   3. `tests/entry/test_check_documents_any_list.py:21-23`: `_INDEX = "docs/operator-guide/README.md"` copies `OPERATOR_GUIDE` (`src/factory/shared/domain/documents.py:24`). The literal `"docs/operator-guide/install.md"` in `_NEWLY_LISTED` copies `OPERATOR_INSTALL` (same module, line 25). Fix: import and use `OPERATOR_GUIDE` and `OPERATOR_INSTALL` from `factory.shared.domain.documents`.

   Earlier tests:
   - tests/entry/test_check_documents_copies.py: the human's leave, feature decision 8, named in the story's Interface.
   - tests/entry/test_check_documents_operator_guide.py: the human's leave, feature decision 8, named in the story's Interface.
   - tests/entry/test_check_documents_settings.py: the human's leave, feature decision 8, named in the story's Interface. Moving its `_drop_row` to the support module as `drop_settings_row`, unchanged, is under the standing leave to move a shared test helper.
   - tests/entry/test_check_documents_suite_copy.py: the human's leave, feature decision 8, named in the story's Interface.
   - tests/support/check_documents_support.py: none needed. The change only adds `write_checked_list` and receives the moved helper, and leaves every helper the file held as it was.
10. factory: started doing as vm.
11. coder: Round 1. All three review findings are in test files that the tester wrote in this story. I don't edit tests, so I changed nothing and am sending the story back to the tester. Nothing under `src/` changes.

    The change for the tester: in `tests/support/check_documents_support.py` and `tests/entry/test_check_documents_any_list.py`, replace the copied path constants with the ones in `factory.shared.domain.documents`. I checked that all three exist there:
    1. Drop `CHECKED_LIST` (`tests/support/check_documents_support.py:32`). Use `CHECKED_DOCUMENTS` (`src/factory/shared/domain/documents.py:564`) in `write_checked_list` and everywhere in `tests/entry/test_check_documents_any_list.py` (lines 11, 32, 101, 117).
    2. Drop `INSTALL` (`tests/support/check_documents_support.py:33`). Use `OPERATOR_INSTALL` (`documents.py:25`) in `drop_settings_row`.
    3. In `tests/entry/test_check_documents_any_list.py`, replace `_INDEX` (line 21) with `OPERATOR_GUIDE` (`documents.py:24`), and the literal `"docs/operator-guide/install.md"` in `_NEWLY_LISTED` (line 23) with `OPERATOR_INSTALL`.

    Every test keeps its name, its ids and what it checks.

    Main decision: I sent this to the tester rather than making the edits myself. The alternative, editing the tests directly, is ruled out because the coder never changes tests. These are the tester's own files from this story, so the change needs no further leave from the human.

    Noticed but not touched: `tests/support/check_documents_support.py:24-25` spells out `docs/operator-guide/` in the expected output text. That code was there before this story and the reviewer did not name it, so I left it. Criterion 6 (`docs/project-guide/shared.md`, *The settings check*) is still open for the docs stage. The journal did not change the meaning of the task, so the Description stays. I made no code change, so there was nothing to refactor and I did not run `make check` this round.
12. factory: started tests as vm.
13. tester: Approved test change, round 1. I made the change the coder's entry 11 names, which carries the reviewer's three findings from entry 9. The copied path constants now come from `factory.shared.domain.documents`:
    - `tests/support/check_documents_support.py`: I dropped `CHECKED_LIST` and `INSTALL`. `write_checked_list` now uses `CHECKED_DOCUMENTS` and `drop_settings_row` uses `OPERATOR_INSTALL`, both imported from `factory.shared.domain.documents`.
    - `tests/entry/test_check_documents_any_list.py`: I dropped `_INDEX` and use `OPERATOR_GUIDE` in its place. In `_NEWLY_LISTED`, the literal `"docs/operator-guide/install.md"` is now `OPERATOR_INSTALL`, and every use of `CHECKED_LIST` is now `CHECKED_DOCUMENTS`.

    Every test keeps its name, its ids and what it checks. No other test file changed: no other module used `CHECKED_LIST` or `INSTALL`.

    Criteria → tests (unchanged from entry 5):
    - criterion 1: tests/entry/test_check_documents_any_list.py::test_a_test_that_writes_its_list_keeps_its_outcome_when_the_repository_lists_more_pages (rows `install`, `operator-guide-index`, `shared`)
    - criterion 2: tests/entry/test_check_documents_any_list.py::test_without_its_own_list_the_repository_list_reaches_the_output
    - criterion 3: tests/entry/test_check_documents_any_list.py::test_the_written_list_holds_one_path_per_line_and_is_committed (rows `empty`, `one`)
    - criterion 4: the earlier rows of test_check_documents_settings.py::test_settings_findings_are_printed_without_changing_the_exit_status, test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file, test_check_documents_suite_copy.py::test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line and test_check_documents_copies.py, all under their old ids
    - criteria 5 and 6: `make check` and docs, no test.

    Files created this round: none. Files changed: tests/support/check_documents_support.py and tests/entry/test_check_documents_any_list.py, both written earlier in this story.

    Modules the test run could not import: none. One run over the five modules: all 27 tests passed, and `make lint` is green. I did not run the type check in this stage, so the coder's `make check` is still to come.

    Left as it was: the `docs/operator-guide/` literals in `MISSING_LINES` and the `NO_INDEX` in `test_check_documents_suite_copy.py`. They predate this story and neither the reviewer nor the coder named them.

    `lint`: lint: green (0.1 s)
