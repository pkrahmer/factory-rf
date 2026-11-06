---
stage: smoke-test
blocked: null
round: 1
attempts: 1
crashes: 0
pull_request: 593
comments_read: [6684236950, 6684384956]
handed_over: null
claim:
  instance: vm
  stage: smoke-test
  started_at: '2026-11-06T12:07:56.192973Z'
  lease_duration: 60
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
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-06T11:48:21.420732Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-06T11:49:21.542563Z'
  stage: review
  run: 36e4f8716a8643ed9e62acb605de0c11
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-06T11:49:27.302967Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-11-06T11:51:49.207373Z'
  stage: docs
  run: bd4c0308c1ee4347aa4ac85600b0bf8f
- number: 12
  speaker: factory
  kind: stall
  at: '2026-11-06T11:51:49.595735Z'
  stage: docs
  run: bd4c0308c1ee4347aa4ac85600b0bf8f
  reason: check_red
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-06T11:51:57.131538Z'
  stage: docs
- number: 14
  speaker: documenter
  kind: result
  at: '2026-11-06T11:52:58.426539Z'
  stage: docs
  run: ad12674c8e4544618633fe117048c220
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-06T11:53:03.744063Z'
  stage: doing
- number: 16
  speaker: coder
  kind: result
  at: '2026-11-06T11:53:44.238654Z'
  stage: doing
  run: a1a857e8d7b642d2916639c242f57424
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-06T11:53:49.646720Z'
  stage: tests
- number: 18
  speaker: tester
  kind: question
  at: '2026-11-06T11:54:16.030113Z'
  stage: tests
  run: 1936cc9a6ea14298bcdb59b9d1b3a4a2
  blocked: question
- number: 19
  speaker: human
  kind: comment
  at: '2026-11-06T11:56:05.522798Z'
  stage: tests
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-06T11:56:08.159966Z'
  stage: tests
- number: 21
  speaker: tester
  kind: result
  at: '2026-11-06T11:56:37.291198Z'
  stage: tests
  run: 1963c68abea243f59b39e54ba90cb668
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-06T11:56:42.610835Z'
  stage: doing
- number: 23
  speaker: coder
  kind: result
  at: '2026-11-06T12:00:51.690773Z'
  stage: doing
  run: cac43530a8824a6d999023deed5e5bce
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-06T12:00:56.973958Z'
  stage: review
- number: 25
  speaker: reviewer
  kind: question
  at: '2026-11-06T12:02:22.601624Z'
  stage: review
  run: cfd8f001357540cd9df394574f96144b
  blocked: question
- number: 26
  speaker: human
  kind: comment
  at: '2026-11-06T12:04:10.400800Z'
  stage: review
- number: 27
  speaker: factory
  kind: started
  at: '2026-11-06T12:04:15.330795Z'
  stage: review
- number: 28
  speaker: reviewer
  kind: result
  at: '2026-11-06T12:05:22.429789Z'
  stage: review
  run: 9bc1ae7414be4b1193b67fbd5492be1b
- number: 29
  speaker: factory
  kind: started
  at: '2026-11-06T12:05:28.949361Z'
  stage: docs
- number: 30
  speaker: documenter
  kind: result
  at: '2026-11-06T12:07:50.726678Z'
  stage: docs
  run: 9dd97ccb37184ff690c423dca1333205
- number: 31
  speaker: factory
  kind: started
  at: '2026-11-06T12:07:56.192973Z'
  stage: smoke-test
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
5. docs: `docs/project-guide/style.md`, *Runnable examples*: the demonstration blocks are `console` blocks again and are run by `make documents`. The reader learns that a wrong example fails `make documents` only in a file listed in `docs/checked-documents.txt`, but fails the test suite in any document the check reads, so every example must be right wherever it stands. The page does not say how the tests' copies are built (that the fixture makes each copy a git repository is machinery). `docs/project-guide/shared.md`, *The document check*: none, the machinery is unchanged.

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
8. factory: started review as vm.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'`, which changes `tests/conftest.py` and adds `tests/entry/test_check_documents_copies.py`, read against the work item. Nothing changes under `src/`, as the Interface says.

   1. Acceptance criteria:
      - Criterion 1: covered by `test_a_matching_example_in_a_copied_document_gives_no_finding`, rows `unlisted` and `listed`. It commits the block and runs `main`. It then asserts that no finding appears at or after the block's line. That includes the `fixture default could not be prepared` finding that `src/factory/shared/adapters/document_examples.py:66-68` adds at the example's line. So the test catches the regression this story fixes.
      - The "every row of `test_the_operator_guide_folder_is_checked_per_file` passes" part of criterion 1 runs on the real documents. That earlier test is unchanged and green in the coder's `make check`.
      - Criterion 2: covered by `test_a_wrong_example_in_a_copied_document_fails_only_a_listed_one`, rows `unlisted-reported` (exit 0) and `listed-fails` (exit 1). It checks the message `<doc>:<n>: the example printed one`, the exit status, and which side of `Report (not checked yet):` the finding is printed on. In the listed row the exit status alone would not tell the cases apart, because the copy's name findings give exit 1 anyway. The check of the finding's position against the heading does tell them apart.
      - Criterion 3: covered by `test_the_copied_documents_are_a_clean_git_work_tree`, which checks both the `status --porcelain` output and the `rev-parse` output.
      - Criterion 4: the coder's `make check` ended `check: green` (journal entry 7).
      - Criterion 5 is left to the documenter.
   2. Architecture: only test code changes. The fixture reuses `run_git` and `commit_all` from `tests/support/git_support.py`, so it adds no new copy of a git helper.
   3. Security: no secrets, no shell command built from strings, no silencing markers.
   4. Quality:
      - The fixture's docstring is updated.
      - The private helpers `_append_block` and `_findings_from` copy no existing support helper. `line_of` in `tests/support/check_documents_support.py` does a different job: it finds the line of a given text.
      - The sides of each rule are rows of one parametrized test.
   5. Work item hygiene:
      - The Description matches what was built: the copy is now a git repository. Its last sentence, turning the style page's blocks back into `console` blocks, is the documenter's work under criterion 5.
      - The journal gives the main choices: the tester made the fixture change itself, `checked-documents.txt` is written only in the listed rows, and the ` does not exist` lines are filtered out. It also says what the coder rejected: a product-side helper.
      - The docs criterion still says what the reader must know.

   Earlier tests:
   - `tests/conftest.py` (fixture `documents`): changed under the human's leave, feature decision 6 of `feature.md` (the human, 2026-11-06), as the story's Interface cites it. The change is what that leave describes: the fixture becomes a git repository. The fixture keeps its name and returns the same folder. No other earlier test was changed.
10. factory: started docs as vm.
11. documenter: Changed one file: `docs/project-guide/style.md`, *Runnable examples*. I turned the two demonstration blocks back into `console` blocks, so `make documents` now runs them. I removed the sentence that said they were shown as `text`. I added a paragraph: the tests run a document's examples in their copies too (the `documents` fixture in `tests/conftest.py` makes each copy a git repository), so a wrong example fails the suite only in a file listed in `docs/checked-documents.txt`. In any other file it is printed under `Report (not checked yet):`.

    I read the fixture change in `tests/conftest.py` and `docs/checked-documents.txt` (style.md is listed) before writing this.

    Checks I ran:
    - `make documents` ended `documents ok (0.6 s)`. The style page's own examples now run in it.
    - `tests/entry/test_check_documents_operator_guide.py` passes.
    - I did not run `make check`, because I changed only a document. The factory runs it after this stage.

    Cross-read and found current: `docs/project-guide/shared.md`, *The document check* (the story's criterion says none is needed, and its description of the checked list matches the code).

    Stale text I noticed but did not touch: none.

    Open: I did not run the smoke test's `grep -c` on the finished file, but style.md now holds two `console` blocks.
12. factory: Stage docs stalled (attempt 1 of 2): a check is red after the stage: `check`
    src/factory/watching/application/transcripts.py         61      2     10      0    97%   91-92
    src/factory/watching/domain/board.py                    55      0      4      1    98%   77->75
    src/factory/watching/domain/machine.py                  52      3     18      5    89%   44->42, 47, 59, 77->75, 79
    src/factory/watching/domain/transcripts.py              10      2      0      0    80%   20-21
    src/factory/work/application/acceptance_reading.py     132      1     46      1    99%   239
    src/factory/work/application/work_items.py              90      2     24      2    96%   133, 169
    src/factory/work/domain/acceptance.py                  195      1     52      1    99%   367
    ------------------------------------------------------------------------------------------------
    TOTAL                                                11189     54   2250     51    99%

    157 files skipped due to complete coverage.
    Required test coverage of 90.0% reached. Total coverage: 99.22%
    ======================================================================================= short test summary info ========================================================================================
    FAILED tests/entry/test_check_documents_checked_files.py::test_todays_documents_with_the_first_list_give_a_report_and_pass - AssertionError: assert None
    make: *** [Makefile:89: test] Error 1
13. factory: started docs as vm.
14. documenter: Round 0, second docs run. I changed no file this run. The first docs run's edit to `docs/project-guide/style.md` (*Runnable examples*) is still in the working tree. It turns the two demonstration blocks back into `console` blocks and adds the paragraph that the tests run the examples in their copies too. I read that text again against the code and it is right.

    Why the check was red: the second `check` stall at entry 12 is a real failure, not a slip in the documents. `tests/entry/test_check_documents_checked_files.py::test_todays_documents_with_the_first_list_give_a_report_and_pass` fails. The pytest lines:
    - `tests/entry/test_check_documents_checked_files.py:157: in test_todays_documents_with_the_first_list_give_a_report_and_pass`
    - `E   AssertionError: assert None` (from `re.fullmatch(TIME_LINE, lines[-1])`, where `lines[-1]` is `docs/project-guide/work.md:13: factory/agents does not exist`)

    I reproduced it by hand in a copy of the repository without `.git`, with `docs/project-guide/style.md` and `docs/project-guide/glossary.md` as the checked list. `main` printed `docs/project-guide/style.md:22: fixture checkout could not be prepared` and exited 1. The test copies the tree with `shutil.copytree` and leaves out `.git` (`_NOT_COPIED`). The copy is no git repository, so the checkout fixture cannot be prepared. Now that style.md holds `console` blocks and is listed, that is a blocking finding. This is the problem the story fixes for the `documents` fixture, and this test builds its own copy without it. The coder's `make check` did not catch it because style.md still held `text` blocks then.

    Findings (the code is right, a test needs the story's change; tests are not mine to edit):
    1. `tests/entry/test_check_documents_checked_files.py:147-158`, `test_todays_documents_with_the_first_list_give_a_report_and_pass`. Its copy of the repository is not a git repository, so listed style.md's `console` blocks fail with `fixture checkout could not be prepared` and the run exits 1. The fix is a test change: make the copy a git repository with one commit of the copied files after writing the list, through `run_git` and `commit_all` of `tests/support/git_support.py` (or reuse the `documents` fixture of `tests/conftest.py`), and keep what the test checks. The Interface and feature decision 6 give the leave. The coder cannot edit tests, so it ends with `tests` and names this test, and the tester makes the change. Other tests in that file that copy the tree may need the same; the tester should check.

    Cross-read and found current: `docs/project-guide/shared.md`, *The document check* (no change needed, as the criterion says).

    Stale text noticed and not touched: none. `docs/project-guide/work.md:13` and the other `does not exist` lines are report-only findings in unlisted files, as before.

    I did not run `make check`, because I changed no file this run. I ran no `make documents` this run either, so I did not read its last line. I ran the check by hand in the repository and it ended `documents ok (0.5 s)`.
15. factory: started doing as vm.
16. coder: Round 1. I changed no code, because the documenter's finding (entry 14) can only be fixed in a test. The Interface also says no module under `src/` changes.

    I reproduced the failure on its own with `uv run pytest -q tests/entry/test_check_documents_checked_files.py`:
    - `tests/entry/test_check_documents_checked_files.py:157: AssertionError`
    - `E       AssertionError: assert None`, the value of `re.fullmatch(TIME_LINE, lines[-1])` with `lines[-1] == 'docs/project-guide/work.md:13: factory/agents does not exist'`

    Cause: `test_todays_documents_with_the_first_list_give_a_report_and_pass` builds its own copy of the repository. It copies with `shutil.copytree` and leaves out `.git` (`_NOT_COPIED`), so the copy is no git repository. The `checkout` fixture cannot be prepared there. Now that the listed `docs/project-guide/style.md` holds `console` blocks again, that gives a blocking finding, the run never prints `documents ok`, and it exits 1.

    The test change, in one sentence: in `tests/entry/test_check_documents_checked_files.py::test_todays_documents_with_the_first_list_give_a_report_and_pass`, after it writes `docs/checked-documents.txt` into the copy, make the copy a git repository with one commit of every file, through `run_git(copy, "init", "-q")` and `commit_all` of `tests/support/git_support.py`, as the `documents` fixture in `tests/conftest.py` now does, and keep the test's name and its three assertions.

    Open for the tester, the leave: F0053-S0004 wrote this test. The Interface cites feature decision 6 for the tests F0053-S0002 and F0053-S0003 wrote, and names the `tests/entry/test_check_documents*.py` files that use `documents`. This test matches that file pattern but does not use the fixture. If the tester reads decision 6 as not covering this test, the change is a question for the human. The other options I see are to have this test use the `documents` fixture's way of building a copy, or to drop the `console` blocks from style.md again, which would undo criterion 5. I would make the commit change.

    Noticed, not touched: other tests in that file that copy `ROOT` with `_NOT_COPIED` may need the same change when they list style.md. In my run, only this one failed.
17. factory: started tests as vm.
18. tester: Round 1, tests stage, in the mode for a test change the human approved. I made no change. The coder's entry 16 names the change, but no answer from the human approves it. I can't tell whether the existing leave covers it, so I am asking.

    The change entry 16 names: in `tests/entry/test_check_documents_checked_files.py::test_todays_documents_with_the_first_list_give_a_report_and_pass`, after it writes `docs/checked-documents.txt` into its copy of the repository, turn the copy into a git repository with one commit of every file. It would use `run_git(copy, "init", "-q")` and `commit_all(copy, ...)` from `tests/support/git_support.py`, the same way the `documents` fixture in `tests/conftest.py` now does. The test keeps its name and its three assertions.

    Why I stopped: F0053-S0004 wrote this test. The story's Interface cites feature decision 6 as the leave only for tests that F0053-S0002 and F0053-S0003 wrote and that use the `documents` fixture. This test was written by another story and builds its own copy with `shutil.copytree` minus `_NOT_COPIED`, without the fixture. It is not a move of a shared helper, so the standing leave in `CLAUDE.md` *Tests* does not cover it either. `CLAUDE.md` lists "change to a test you did not write beyond the standing leave" under *Not without asking*. Entry 16 raised the same doubt.

    Question for the human: may I change this test, which F0053-S0004 wrote?
    - (a) Yes, exactly as above: `git init` plus one `commit_all` of the copy after the list is written. Name and assertions stay the same. The same change would go into any other test in that file that copies `ROOT` and lists style.md (entry 16 found only this one failing). **I would choose (a).** It is the smallest change, it matches the `documents` fixture, and it keeps criterion 5.
    - (b) Yes, but the test builds its copy the way the `documents` fixture does, through a shared helper moved to `tests/support/`. That is a larger change and alters what is copied.
    - (c) No: drop the `console` blocks from `docs/project-guide/style.md` again. That undoes criterion 5.

    Criterion → test mapping: unchanged from entry 5. No test changed in this run. No files were created. No `make test` run was needed.
19. 2026-11-06 human: (a), with the human's leave: in `tests/entry/test_check_documents_checked_files.py::test_todays_documents_with_the_first_list_give_a_report_and_pass`, after the list is written, the copy becomes a git repository with one commit of every file (`run_git(copy, "init", "-q")` and `commit_all`), and the same in any other test of that file that copies the repository and fails only for this reason. Names and assertions stay. Feature decision 6 meant to cover exactly this case: any earlier test whose only failure is that its copy is no git repository.
20. factory: started tests as vm.
21. tester: Round 1, tests stage, in the mode for a test change the human approved. I made the change the human approved in entry 19 (option (a)) and the one the coder named in entry 16. Nothing else changed.

    The change is in `tests/entry/test_check_documents_checked_files.py::test_todays_documents_with_the_first_list_give_a_report_and_pass`. After the test writes `docs/checked-documents.txt` into its copy of the repository, it now runs `run_git(copy, "init", "-q")` and then `commit_all(copy, "The copied repository")`. Both come from `tests/support/git_support.py`, and the module now imports them. The copy is a git repository with one commit of every file, as the `documents` fixture in `tests/conftest.py` builds it. That lets the `checkout` fixture of the listed style.md's `console` blocks be prepared. The test keeps its name and its three assertions.

    Why: the copy was no git repository, so the listed `docs/project-guide/style.md` examples failed with `fixture checkout could not be prepared` (entries 14 and 16). Entry 19 gives the leave under feature decision 6.

    Other tests in that file: none of them copies the repository. Only this test uses `ROOT` with `_NOT_COPIED`, and every other test builds its documents with `write_documents` under `tmp_path`. So the human's "same in any other test" applies to none.

    Criterion → test mapping: unchanged from entry 5.

    Files: none created. Changed `tests/entry/test_check_documents_checked_files.py`, an earlier test file that F0053-S0004 wrote, under the human's leave in entry 19.

    Runs:
    - `uv run pytest -q tests/entry/test_check_documents_checked_files.py`: no failures (the tail showed only passing dots).
    - `make lint`: `lint: green`.
    - No module failed to import.

    `lint`: lint: green (0.2 s)
22. factory: started doing as vm.
23. coder: Round 1. I changed no code. The finding from entries 14 and 16 was a test change. The human approved it in entry 19, and the tester made it in entry 21 in `tests/entry/test_check_documents_checked_files.py`: the test's copy of the repository becomes a git repository with one commit. The Interface says no module under `src/` changes, so I had nothing to build.

    - What I built: nothing. The branch diff holds only the tester's test files (`tests/conftest.py`, `tests/entry/test_check_documents_copies.py`, `tests/entry/test_check_documents_checked_files.py`) and the documenter's change to `docs/project-guide/style.md`.
    - Main choice: I left `src/` untouched, as the Interface requires. I rejected adding a helper on the product side that makes a copy into a git repository. The tests' copies are a fixture's job, and it already does this with `run_git` and `commit_all` from `tests/support/git_support.py`.
    - Refactor: I had no diff of my own, so nothing to change.
    - Description: the journal did not change what the task means. Entry 19 only widened the leave of feature decision 6 to the S0004 test. I did not rewrite the Description.
    - Noticed but not touched: nothing new.

    `make check`: green, with `console` blocks back in `docs/project-guide/style.md` (test: green, 102.2 s, coverage 99.22 %).

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
24. factory: started review as vm.
25. reviewer: Round 1 review. I read the work item and `git diff main...HEAD -- . ':!factory'`: `docs/project-guide/style.md`, `tests/conftest.py`, `tests/entry/test_check_documents_checked_files.py` and the new `tests/entry/test_check_documents_copies.py`. Nothing under `src/` changes.

    Findings:
    1. `docs/project-guide/style.md:32` (the new paragraph under *Runnable examples*) is contradicted by the tests, and so is the reader's lesson that criterion 5 dictates. The page says: "A wrong example therefore fails the suite only in a file listed in `docs/checked-documents.txt`; in any other file it is printed under `Report (not checked yet):`."
       - Why it is false: the `documents` fixture copies no `docs/checked-documents.txt`, so in its copy no file is listed. A wrong example in an unlisted page, for example `docs/project-guide/shared.md`, therefore prints a report line `docs/project-guide/shared.md:<n>: the example printed ...` (`src/factory/entry/check_documents.py:186-189`).
       - `tests/entry/test_check_documents_operator_guide.py:89-96` compares every printed line with the expected output. It leaves out only lines that end in ` does not exist` and the report heading. That report line is kept, so the six rows with an `output` (`no-stops-section` and the rest) fail.
       - So the suite fails for a wrong example in any copied document, listed or not. A listed one also fails through `test_todays_documents_with_the_first_list_give_a_report_and_pass`.
       - The same sentence also says the fixture "makes each copy a git repository". The copy in `test_check_documents_checked_files.py:151-155` is built by that test, not by the fixture.
       - Fix: the sentence and criterion 5 must state one truth. Which truth needs the human; see the question below.

    Groups checked with no other finding:
    - 1, criteria: criterion 1 is covered by `test_a_matching_example_in_a_copied_document_gives_no_finding` (rows `unlisted` and `listed`). Criterion 2 is covered by `test_a_wrong_example_in_a_copied_document_fails_only_a_listed_one` (both sides, rows of one test). Criterion 3 is covered by `test_the_copied_documents_are_a_clean_git_work_tree`. Criterion 4: the coder's `make check` was green (entry 23).
    - 2, architecture: only tests and one document change. The fixture reuses `run_git` and `commit_all` from `tests/support/git_support.py`.
    - 3, security: no secrets, no markers, no commands built from strings.
    - 4, quality: names and docstrings are fine, and there is no copied helper.
    - 5, hygiene: the journal explains the choices, and the Description matches what was built. Criterion 5's lesson is the false statement in finding 1.
    - Documents: the other claims of the changed paragraphs hold. The `console` blocks are real, and `echo "took $((40 + 2)) s"` matches `took <seconds> s`.

    Earlier tests:
    - `tests/conftest.py` (fixture `documents`): changed under feature decision 6, as the Interface cites it, and the human's entry 19. Its name and the folder it returns stay the same.
    - `tests/entry/test_check_documents_checked_files.py` (`test_todays_documents_with_the_first_list_give_a_report_and_pass`): changed under the human's leave in entry 19. The change is exactly `git init` plus one `commit_all` after the list is written. Its name and its three assertions stay the same.

    Question for the human: criterion 5 wants the reader to learn that "a wrong example fails the suite only in a listed file". The test suite contradicts that (finding 1). Which should hold?
    - (a) Correct criterion 5 and the style page to the truth. A wrong example fails `make documents` only in a listed file. In the tests, a wrong example in any copied document fails the suite: in a listed file through the run of the real list, in any other file through the operator-guide test's line-by-line comparison of the report. No test changes. The documenter rewrites the paragraph, and the next review corrects criterion 5's wording from your answer.
    - (b) Keep criterion 5's statement and make it true. `test_the_operator_guide_folder_is_checked_per_file` would also leave out the `the example printed` report lines from its comparison. That changes a test F0053-S0002 wrote, so it needs your leave. The Description rejected that kind of filtering, though for a different problem.
    - (c) Drop the sentence about the suite from the style page and from criterion 5, and keep only that the copies are git repositories.

    I would choose (a). It is true today, needs no test change, and a suite that catches every wrong example is the stricter guard.
26. 2026-11-06 human: (a). The truth for the writer, in the style page and in criterion 5: a wrong example fails `make documents` only in a file listed in `docs/checked-documents.txt`, but it fails the test suite in any document the check reads, so every example must be right wherever it stands. Drop the sentence that the fixture makes each copy a git repository, which is machinery and belongs in `shared.md` if anywhere. No test change. The documenter rewrites the paragraph, and the next review corrects criterion 5's wording from this answer.
27. factory: started review as vm.
28. reviewer: Round 1, second review, after the human's answer in entry 26. I read the work item and `git diff main...HEAD -- . ':!factory'`. Four files changed: `docs/project-guide/style.md`, `tests/conftest.py`, `tests/entry/test_check_documents_checked_files.py` and the new `tests/entry/test_check_documents_copies.py`. Nothing under `src/` changes.

    no findings

    Corrected, as entry 26 asks ("the next review corrects criterion 5's wording from this answer"):
    - criterion 5 corrected:
      - It said: "The reader learns that a document's examples run in the tests' copies too, so a wrong example fails the suite only in a listed file."
      - It says now: "The reader learns that a wrong example fails `make documents` only in a file listed in `docs/checked-documents.txt`, but fails the test suite in any document the check reads, so every example must be right wherever it stands. The page does not say how the tests' copies are built (that the fixture makes each copy a git repository is machinery)."
      - I changed nothing else in the work item. The `shared.md`: none part is unchanged, because the human said the fixture's machinery belongs there "if anywhere".

    Left for the docs stage (the human's routing in entry 26, not a finding against the code):
    - `docs/project-guide/style.md:32` still holds the sentence finding 1 of entry 25 named. It says the fixture makes each copy a git repository, and that a wrong example fails the suite only in a listed file.
    - The documenter rewrites that paragraph from the corrected criterion 5. The tests contradict the current text: `tests/entry/test_check_documents_operator_guide.py:89-96` keeps the `the example printed` report lines of unlisted pages.
    - I end with `docs` and not `doing` because the coder cannot write documents. A `doing` would only spend the last round before the cap and leave the paragraph as it is.

    Groups checked:
    1. Criteria:
       - Criterion 1: `test_a_matching_example_in_a_copied_document_gives_no_finding`, rows `unlisted` and `listed`. The real `console` blocks in the listed style.md now run in the `documents` copy of `test_the_operator_guide_folder_is_checked_per_file`, and that test is green.
       - Criterion 2: `test_a_wrong_example_in_a_copied_document_fails_only_a_listed_one`. Both sides are rows of one test, and each row checks the message, which side of the report heading the finding stands on, and the exit status.
       - Criterion 3: `test_the_copied_documents_are_a_clean_git_work_tree`.
       - Criterion 4: the coder's `make check` was green (entry 23).
    2. Architecture: only tests and one document change. The fixture and the S0004 test reuse `run_git` and `commit_all` from `tests/support/git_support.py`.
    3. Security: no secrets, no markers, no command built from strings.
    4. Quality: there is no copied helper, and the fixture's docstring describes the new fixture.
    5. Hygiene:
       - The journal records the choices and what was rejected.
       - The Description matches what was built.
       - Criterion 5 now carries the human's truth. The Interface's sentence that names only the S0002 and S0003 tests is widened by the human's entry 19. Under my instructions I correct only the Description, so I left the Interface as it is.
    6. Documents: style.md's `console` blocks and their outputs hold (`echo "took $((40 + 2)) s"` matches `took <seconds> s`). Line 32 is the docs stage's rewrite, as above.

    Earlier tests:
    - `tests/conftest.py`, fixture `documents` (F0053-S0002): changed under feature decision 6, as the Interface cites it, and the human's entry 19. Its name stays, and it returns the same folder.
    - `tests/entry/test_check_documents_checked_files.py`, `test_todays_documents_with_the_first_list_give_a_report_and_pass` (F0053-S0004): changed under the human's leave in entry 19. The change is exactly `git init` and one `commit_all` after the list is written. Its name and its three assertions stay.
29. factory: started docs as vm.
30. documenter: Round 1, after the human's answer (a) in entry 26.

    Changed:
    - `docs/project-guide/style.md`, *Runnable examples*: I rewrote the paragraph that the reviewer's finding 1 named. It no longer says the fixture makes each copy a git repository, because that is machinery. It now says a wrong example fails `make documents` only in a file listed in `docs/checked-documents.txt` (elsewhere it is printed under `Report (not checked yet):`), and that the test suite runs the examples of every document the check reads. So a wrong example fails the suite whether its file is listed or not, and every example must be right wherever it stands.
    - I did not change the `console` blocks of the page. They already held, and `make documents` runs them.

    Checks:
    - I ran `make documents`. Its last line is `documents ok (0.6 s)`.
    - It printed one report line, `docs/project-guide/work.md:13: factory/agents does not exist`. That line is the check's existing report of an unlisted page. I did not touch it, because it is unrelated to this story.
    - I did not run `make check`, because I changed only a document.

    Cross-read and found current: the other paragraphs of `docs/project-guide/style.md`. `docs/project-guide/shared.md` needs nothing, because the machinery is unchanged (criterion 5).

    No stale text noticed beyond the `work.md:13` report above. No findings against the code.

    `check`: check: green
    `secrets`: secrets: green (0.5 s)
    `documents`: documents ok (0.6 s)
31. factory: started smoke-test as vm.
