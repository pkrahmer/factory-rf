---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 593
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T11:40:54.929037Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T11:40:54.936100Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T11:41:12.322650Z'
  stage: intake
  run: 3db6db9d613343e99367272a983ab60b
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T11:41:17.936338Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-06T11:44:00.957162Z'
  stage: tests
  run: e8bf4ac35c474b4c98dab6cdd0925518
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T11:44:06.228679Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-06T11:48:16.019154Z'
  stage: doing
  run: 11da8432f69b4856a058affae469853b
---

# A runnable example in the documents keeps the suite green
## Description

The document check runs a document's `console` blocks (S0003, S0006), and the documenter's rules ask for every command to be shown as one (S0005). But no document can hold one today. The shared test fixture `documents` (`tests/conftest.py`) copies the real documents into a folder under `tmp_path` that is no git repository. There the `checkout` and `instance` fixtures cannot be prepared, so one `console` block in any document the check reads turns five rows of `test_the_operator_guide_folder_is_checked_per_file` red. S0003's docs stage stalled on exactly this, and `docs/project-guide/style.md` now shows its own examples as `text` blocks. The feature acceptance reproduced it: one `console` block (`$ echo hi` / `hi`) appended to `docs/project-guide/shared.md` in a clone gave `5 failed, 7 passed`. This story makes the copy a git repository with one commit of the copied files, so that both fixtures can be prepared and a real example in a real document runs in the tests as it does in `make documents`. It also turns the two demonstration blocks of the style page back into `console` blocks, so that the page's own examples are checked. The product code stays as it is. Rejected: filtering the example lines out of the earlier test's comparison, which still fails for a listed file, where a fixture that cannot be prepared blocks.

## Interface

- `tests/conftest.py`, the fixture `documents` (moved there by F0053-S0002): after copying, it makes `root` a git repository holding every copied file in one commit, through `run_git` and `commit_all` of `tests/support/git_support.py`. It keeps its name and returns the same folder.
- The tests that use `documents` (`tests/entry/test_check_documents*.py`) keep their names and what they check. A test that now needs a git repository where it changes a file (a `change` that edits a document) commits that change before it calls `main`, or the fixture's commit is enough because the checkout fixture exports the committed state. The tester names each such test.
- This changes tests that F0053-S0002 and F0053-S0003 wrote, beyond the standing leave. Feature decision 6 gives the leave.
- No module under `src/` changes.

## Acceptance criteria

1. With the fixture `documents`, a `console` block (`$ echo hi` / `hi`) appended to a copied `docs/project-guide/shared.md` and committed gives no finding for that block, and every row of `test_the_operator_guide_folder_is_checked_per_file` passes (one test, two rows: the block in an unlisted page and the block in `docs/project-guide/style.md`, which is listed).
2. A `console` block whose output differs (`$ echo one` / `two`) in the listed `docs/project-guide/style.md` of the copy fails `main` with `docs/project-guide/style.md:<line>: the example printed one` and exit status 1. The same block in an unlisted page is printed under `Report (not checked yet):`, and the exit status is 0 (rows of one test).
3. `git -C <root> status --porcelain` in the copy the fixture returns prints nothing, and `git -C <root> rev-parse --is-inside-work-tree` prints `true`.
4. `make check` stays green.
5. docs: `docs/project-guide/style.md`, *Runnable examples*: the demonstration blocks are `console` blocks again and are run by `make documents`. The reader learns that a document's examples run in the tests' copies too, so a wrong example fails the suite only in a listed file. `docs/project-guide/shared.md`, *The document check*: none, the machinery is unchanged.

## Smoke test

```bash
grep -c '^```console' docs/project-guide/style.md
```
Expect: a number greater than `0`

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

```bash
uv run pytest tests/entry/test_check_documents_operator_guide.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete pieces, the `documents` fixture in `tests/conftest.py`, `run_git` and `commit_all` in `tests/support/git_support.py` (both exist), and the `tests/entry/test_check_documents*.py` files (they exist). `src/` is unchanged and the leave for the earlier tests is given by feature decision 6.
   - Criteria: 1 and 2 are each testable by one parametrized test, and rule 2 covers both sides (listed file fails with the message and exit 1, unlisted file reports and exits 0). 3 covers both git properties of the fixture. 4 is the `make check` criterion. Each is testable without further decisions.
   - Smoke test: the three commands are runnable. The pytest command passes no `-q`, and `pyproject.toml` already sets `addopts = "-q ..."`, so `tail -1 | grep -c passed` meets the summary line. Each `Expect:` can be checked against the output.
   - Docs criterion: it names what the reader must know (the examples run in the tests' copies, and a wrong example fails the suite only in a listed file). It dictates no sentences.
   - Architecture: only test code changes. The fixture stays in `tests/conftest.py` and reuses the shared git helpers instead of a new copy.
   - Scope: it is within F0053 (runnable examples, S0003/S0006) and outside its "Out of scope". The changes to the S0002 and S0003 tests are covered by decision 6.
4. factory: started tests as vm.
5. tester: Wrote the tests for criteria 1–3. I also made the fixture change from the Interface myself, because it is test code: the coder's write paths are `src/*`, and the coder never edits tests. So these tests are **green, not red**. The coder has no code to write. Their `make check` (criterion 4) is the only thing left before docs.

   Criterion → test:
   - criterion 1: `tests/entry/test_check_documents_copies.py::test_a_matching_example_in_a_copied_document_gives_no_finding`, with the rows `unlisted` (shared.md) and `listed` (style.md). The "every row of `test_the_operator_guide_folder_is_checked_per_file` passes" part is covered by that test itself, which is unchanged and still green, and which will run style.md's real `console` blocks once the docs stage restores them.
   - criterion 2: `tests/entry/test_check_documents_copies.py::test_a_wrong_example_in_a_copied_document_fails_only_a_listed_one`, with the rows `unlisted-reported` (the finding comes after `Report (not checked yet):`, exit 0) and `listed-fails` (the finding comes before the heading, exit 1). `<line>` is matched as any number, because the criterion does not say whether it is the block's line or the command's.
   - criterion 3: `tests/entry/test_check_documents_copies.py::test_the_copied_documents_are_a_clean_git_work_tree`.
   - criterion 4: `make check`, the coder's run.

   Files:
   - Created: `tests/entry/test_check_documents_copies.py`.
   - Changed: `tests/conftest.py`. The fixture `documents` now runs `run_git(root, "init", "-q")` and `commit_all(root, ...)` after copying. It keeps its name and returns the same folder. Feature decision 6 gives the leave to change it.

   Setup choices I had to make:
   - The fixture does not copy `docs/checked-documents.txt`, so nothing is listed in the copy. For the `listed` rows the test writes a list holding only `docs/project-guide/style.md` and commits it with the block. The `unlisted` rows write no list. If I list style.md there too, its existing name findings block (the copy has no `src/` or `tests/`), and the run exits 1.
   - For the same reason, the `listed` row of criterion 2 leaves out the ` does not exist` lines before it checks the output, as the operator-guide test already does. Its exit status 1 comes from the example finding and from those name findings together.

   Earlier tests: none needed an edit. `test_the_operator_guide_folder_is_checked_per_file` and `test_settings_findings_are_printed_without_changing_the_exit_status` change files only for the name, section and settings checks, which read the root directly. The fixture's commit is enough for the examples, which run on the committed state.

   One run: `uv run pytest -q` of the new file plus the two earlier `documents` test files gave 12 passed. `make lint` is green. Every module imported; nothing was missing.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
7. coder: I wrote no code. As the Interface says, no module under `src/` changes. The tester already made the one change the story needed, the fixture `documents` in `tests/conftest.py` (`git init` plus `commit_all`, through `tests/support/git_support.py`), and wrote `tests/entry/test_check_documents_copies.py`. Both are test files, so they are outside my write paths. I ran `make check` once and it ended `check: green` (test: green, 102.6 s, coverage 99.22 %).

   - Main choice: I added nothing to `src/` to make the stage look busy. The alternative I rejected was a product-side helper that turns the copy into a git repository. The Interface rules that out ("No module under `src/` changes"), and the fixture already does it with the shared test helpers.
   - Refactor: there is no coder diff to refactor. The branch diff against main holds only the tester's two test files and the work item files.
   - Noticed, not touched: criterion 5 is still open for the docs stage. The two demonstration blocks in `docs/project-guide/style.md` are still `text` blocks, so the smoke test's `grep -c '^```console'` will report 0 until the documenter turns them back into `console` blocks. The journal did not change the meaning of the task, so I did not rewrite the Description.

   `check`: check: green
   `duplicates`: duplicates: 6 new, 39 known, 4 gone
