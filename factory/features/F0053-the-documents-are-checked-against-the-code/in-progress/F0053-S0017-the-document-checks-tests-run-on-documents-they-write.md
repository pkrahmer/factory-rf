---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 606
comments_read: [6695295968, 6695615126]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T20:53:15.111571Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T20:53:15.118416Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-06T20:53:33.150269Z'
  stage: intake
  run: c1038a76837244ee9914156042a2648e
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-06T20:57:25.533995Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-06T20:57:28.136936Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-06T20:57:50.290016Z'
  stage: intake
  run: 73753c31dd2447658e9b68c610703d3f
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-06T20:57:55.535565Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-06T21:03:36.319382Z'
  stage: tests
  run: 02f9739596c94ef699951f25502c6230
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-06T21:03:41.547198Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-06T21:06:15.532935Z'
  stage: doing
  run: 54516e30c89e4f878643217754ebebaf
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-06T21:08:06.087939Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-06T21:08:08.597254Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-06T21:08:26.997429Z'
  stage: doing
  run: 21d2ee3a3ec04722be27fa3904dfeb97
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-06T21:08:32.548119Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-06T21:09:28.244344Z'
  stage: tests
  run: 60f2fee00b534d52acb07e097bb43c15
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-06T21:09:33.724382Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-06T21:15:42.984747Z'
  stage: doing
  run: 20c8a464ef5b41749012cbd051b38706
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-06T21:15:48.207991Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-06T21:17:44.863387Z'
  stage: review
  run: 14462b901df54777bf65a2c0f5a4647c
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-06T21:17:50.141407Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-11-06T21:18:18.066127Z'
  stage: doing
  run: c9039e501e7a418dbff3f77926aceb59
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-06T21:18:23.371459Z'
  stage: tests
- number: 23
  speaker: tester
  kind: result
  at: '2026-11-06T21:19:54.528627Z'
  stage: tests
  run: 42ba2f2f8d084aaebebfe25235bc622f
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-06T21:19:59.708017Z'
  stage: doing
- number: 25
  speaker: coder
  kind: result
  at: '2026-11-06T21:24:25.467868Z'
  stage: doing
  run: bdfd60b6d1cb4c88b8547942be67bb58
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-06T21:24:30.955077Z'
  stage: review
- number: 27
  speaker: reviewer
  kind: result
  at: '2026-11-06T21:25:50.719749Z'
  stage: review
  run: 6d9b2e37e9ef47c9b81197c0d421c1bb
- number: 28
  speaker: factory
  kind: started
  at: '2026-11-06T21:25:55.907291Z'
  stage: docs
- number: 29
  speaker: documenter
  kind: result
  at: '2026-11-06T21:28:56.462184Z'
  stage: docs
  run: 4ebca3dc58ca4113a3b6ec26519bff5f
- number: 30
  speaker: factory
  kind: started
  at: '2026-11-06T21:29:01.731821Z'
  stage: smoke-test
- number: 31
  speaker: smoke-tester
  kind: result
  at: '2026-11-06T21:29:31.856669Z'
  stage: smoke-test
  run: 0e635cd1b0bd43ff89b4a3b221980034
---

# The document check's tests run on documents they write

## Description

The tests of the document check run `factory.entry.check_documents` on copies of the repository's real documents and its real `docs/checked-documents.txt`, and compare the exact output. That couples them to today's content in two ways. First, every runnable example in the real documents runs once in each of these tests, about 27 cases, so `make check` grows with every example the rewrite adds, although `make documents` is kept out of `make check` on purpose. Second, a change to a real document or to the real list can break a test that has nothing to do with it: four acceptances of this feature each found one more such case (S0014, S0015, S0016). This story makes the check's tests write the documents they need. A support module writes the smallest documents the check accepts, built from the same tables in the code that the check reads, and each test adds the one block, row, page or list line its rule needs. No test reads or copies the real documents or the real list any more, and no real example runs in `make check`. The real documents are checked by `make documents` alone, which runs in every docs stage, so a code change that breaks a document is still caught there. Every behaviour the replaced tests checked keeps a test. The check itself, its output and the real documents stay as they are. The structural guards that read the real guide folders (`tests/guards/test_project_guide_files.py`, `tests/guards/test_operator_guide_files.py`) run no examples and stay as they are.

## Interface

- `tests/support/minimal_documents_support.py` (new):

  ```python
  def minimal_documents(root: Path) -> Path:
      """A git repository at `root`, in one commit, with the smallest documents the check accepts."""

  def add_and_commit(root: Path, files: Mapping[str, str]) -> None:
      """Write `files` (path relative to `root`, text) into the repository and commit them."""
  ```

  - `minimal_documents` writes `README.md`, the operator guide's index and every file of `OPERATOR_GUIDE_FILES`, the project guide's index and its area pages, and an empty `docs/checked-documents.txt`. Every name the check requires (the sections, the stops, the kill points, the fault-injection paths, the settings table rows of `SETTINGS`, the index lines) is taken from the code's own tables, not written as a literal, so the minimal documents follow the code.
  - On the repository it writes, `main(["--root", str(root)])` prints exactly one line, `documents ok (<seconds> s)`, and returns 0. The documents hold no runnable example.
  - `add_and_commit` leaves `git status --porcelain` empty.
- The test modules of the check that run on copies today (`tests/entry/test_check_documents_any_list.py`, `test_check_documents_checked_files.py`, `test_check_documents_copies.py`, `test_check_documents_operator_guide.py`, `test_check_documents_settings.py`, `test_check_documents_suite_copy.py`, `test_check_documents_todays_names.py`) run on `minimal_documents` instead. A test whose rule still applies keeps its name. A test that only checked the coupling (for example that the repository's list reaches the output, or that the copy holds the tracked files) goes, and the entry names it.
- Each of these behaviours keeps one test on minimal documents: a finding blocks in a listed page and is reported in an unlisted one; the output order and the report heading; a page listed once more gives no second finding; a skipped block (`vm`, `github`, `model`, `suite`) adds only its `not run` line; a `checkout` example reads a tracked file; an `instance` example runs in a valid instance; a wrong example blocks a listed page and is reported in an unlisted one; a dropped settings row gives its finding; a missing operator-guide file or section gives its finding.
- The fixtures `tracked_files` and `documents` of `tests/conftest.py` and the module `tests/support/documents_copy_support.py` go when nothing uses them any more.
- `tests/guards/test_document_tests_write_their_documents.py` (new): no module under `tests/entry/` that imports `factory.entry.check_documents` names `support.operator_support.ROOT`, `tracked_files`, `documents_copy_support` or the path `docs/checked-documents.txt` of the repository.
- These are earlier tests of this feature. Feature decision 10 gives the human's leave: the tester may change, merge or remove the tests and fixtures named above, and any other earlier test whose only failure is that it no longer runs on a copy of the real documents. Every behaviour of the list above keeps a test, and the entry names each test it changed, merged or removed, with the test that now covers it.
- No module under `src/factory/` changes.

## Acceptance criteria

1. `minimal_documents(tmp_path / "root")` gives a repository on which `main(["--root", ...])` prints only `documents ok (<seconds> s)` and returns 0, and whose `git status --porcelain` is empty.
2. The minimal documents follow the code: with one more stop, kill point or setting added to the code's table in a test (through `monkeypatch`), `minimal_documents` still gives a repository that passes (one row each).
3. Each behaviour listed in the Interface has a test on minimal documents that checks its passing and its failing side (rows of one parametrized test where they share a rule). Two behaviours have the passing side only: a page listed once more gives no second finding (rows: a page listed once and a page listed twice, both with one finding) and a skipped block adds only its `not run` line (one row each for `vm`, `github`, `model` and `suite`).
4. The guard of the Interface passes, and fails on a test module written under `tmp_path` that names each of `support.operator_support.ROOT`, `tracked_files`, `documents_copy_support` and the repository's `docs/checked-documents.txt` (one row for each of the four).
5. No test module under `tests/entry/` that tests `check_documents` runs it on a path outside `tmp_path`, checked by the guard of criterion 4. The entry reports the `make test` time before and after the story; that is no criterion.
6. After `add_and_commit(root, {...})` the `git status --porcelain` is empty and every written file is tracked (rows: a file in an existing folder, a file in a new subfolder).
7. `make check` stays green.
8. docs: `docs/project-guide/shared.md`, the document check: the reader learns that its tests run on minimal documents written from the code's tables, how a test adds what its rule needs, and that the real documents are checked only by `make documents` in the docs stages. `docs/project-guide/style.md`, *Runnable examples*: the reader learns that a wrong example blocks `make documents` in a listed file and is reported in any other, and that the test suite does not run the documents' examples. `docs/decisions.md`: one entry. It says that the check's tests run on documents they write. The reason: `make check` must not grow with the documents, and a rewrite of a document must not break a test. Rejected: copies of the real documents with one repair per page, since four acceptances each found one more coupling.

## Smoke test

```bash
grep -rlE "tracked_files|documents_copy_support|operator_support import ROOT" tests/entry | wc -l
```
Expect: `0`

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed, so there are no form findings):

   1. The Interface says `add_and_commit` "leaves `git status --porcelain` empty", but criterion 1 checks the status only for `minimal_documents`. No criterion tests `add_and_commit`. Please add one, with a passing case and a case that adds a file in a new subfolder. I would choose a criterion saying that after `add_and_commit(root, {...})` the status is empty and the new file is tracked.

   2. Criterion 5 is not testable by one test function. "Under their usual time" has no number, and "the `make test` time before and after" is a measurement for the entry, not something a test can check. Please split it into two parts. (a) A testable criterion. I would choose this: "the document check's tests do not run the real documents' examples", checked by a guard or test that fails if a module under `tests/entry/` that tests `check_documents` runs on a path outside `tmp_path`. (b) A note that the entry reports the `make test` times, not as a criterion. If you keep the `sleep 30` check, please give it a bound, for example "finishes within `ROOMY_BOUND_SECONDS`", and say which test module shows it.

   3. Criterion 4 covers the guard's failing side only for `support.operator_support.ROOT`. The Interface's rule names four things: `ROOT`, `tracked_files`, `documents_copy_support` and the path `docs/checked-documents.txt`. Please say that the failing-side test has one row for each of the four. I would choose that.

   4. Criterion 3 asks for "a test for each behaviour listed", with the passing and failing sides. But the Interface list has no failing side for some behaviours: "a page listed once more gives no second finding" and "a skipped block adds only its `not run` line". Please say what the failing side is for each, or say that the criterion applies to the passing side only for them. For the skipped block, I would choose one row for each of `vm`, `github`, `model` and `suite`.
4. 2026-11-06 human: 1. Yes: after `add_and_commit(root, {...})` the status is empty and every written file is tracked; rows for a file in an existing folder and one in a new subfolder.
   2. Split as you propose, and drop the `sleep 30` check. (a) Criterion 5 becomes: no test module under `tests/entry/` that tests `check_documents` runs it on a path outside `tmp_path`, checked by the guard of criterion 4 (which already refuses the names that lead to the real repository). (b) The entry reports the `make test` time before and after; that is no criterion.
   3. Yes: the guard's failing side has one row for each of the four names (`support.operator_support.ROOT`, `tracked_files`, `documents_copy_support`, the repository's `docs/checked-documents.txt`).
   4. For those two, criterion 3 covers the passing side only. The skipped block gets one row each for `vm`, `github`, `model` and `suite`; the page listed once more gets a row for a page listed once and a page listed twice, both with one finding.
5. factory: started intake as vm.
6. intake: accepted, with the human's answers (journal entry 4) carried into the story. In the criteria I changed: criterion 3 now says which two behaviours have the passing side only, with their rows. Criterion 4 has one row for each of the four names. Criterion 5 is replaced by "no `check_documents` test module under `tests/entry/` runs it outside `tmp_path`, checked by the guard", and the `make test` time is reported in the entry, not as a criterion; the `sleep 30` check is dropped. A new criterion 6 tests `add_and_commit`. The closing two criteria are now 7 (`make check`) and 8 (`docs:`). The Description needed no change.
   - Interface: concrete. It names `tests/support/minimal_documents_support.py` with the signatures of `minimal_documents` and `add_and_commit`, the seven test modules, the fixtures and support module to remove, and the guard module. No `src/factory` module changes.
   - Criteria: each is testable by one test function, with rows where the sides differ. Each Interface behaviour has a criterion, and each rule has both sides except the two the human marked as passing-side only. "Follows the code" is criterion 2.
   - Smoke test: both commands are runnable (`grep ... | wc -l` expects `0`; `check_documents | tail -1` expects `documents ok (<seconds> s)`). Neither runs pytest, so the `-q` rule does not apply.
   - Docs criterion: it names what the reader must know in `shared.md`, `style.md` and `decisions.md`, including the decision's reason and the rejected option. It does not dictate sentences.
   - Architecture: tests and support modules sit under `tests/`, as `CLAUDE.md` says. The guard goes in `tests/guards/`. The `tests/conftest.py` fixtures go as `CLAUDE.md` allows.
   - Scope: it is inside feature decision 10, which gives the human's leave to change, merge or remove the named earlier tests and fixtures. It is not in "Out of scope". The route is `tests`, because the Interface changes test paths.
7. factory: started tests as vm.
8. tester: Tests written. No module under `src/factory/` changes in this story, so the new and rewritten tests already pass. The support module they call sits under `tests/`, which is my write path, so I wrote it. The coder still has the `docs:` criterion and `make check`, and must report the `make test` time before and after the story. I did not measure that time.

   Criterion → test:
   - criterion 1: tests/entry/test_check_documents_minimal.py::test_the_minimal_documents_pass_the_check_in_a_clean_work_tree
   - criterion 2: tests/entry/test_check_documents_minimal.py::test_the_minimal_documents_follow_one_more_row_of_the_codes_tables (rows stop, kill-point, setting, each set through `monkeypatch` on `factory.shared.domain.documents` or `factory.shared.domain.settings`)
   - criterion 3, one test per behaviour, all on minimal documents:
     - a finding blocks in a listed page and is reported in an unlisted one: test_check_documents_checked_files.py::test_a_new_finding_blocks_in_a_listed_file_and_is_reported_in_any_other
     - the output order and the report heading: test_check_documents_checked_files.py::test_the_output_is_the_blocking_findings_then_the_report_and_nothing_more and ::test_the_report_heading_is_left_out_when_there_is_nothing_to_report
     - a page listed once more gives no second finding: test_check_documents_any_list.py::test_a_page_listed_once_more_gives_no_second_finding (rows listed-once and twice)
     - a skipped block adds only its `not run` line: test_check_documents_suite_copy.py::test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line (rows vm, github, model, suite, and wrong). It now compares the exact output.
     - a `checkout` example reads a tracked file: test_check_documents_suite_copy.py::test_an_example_reads_a_file_git_tracks_in_the_repository (rows tracked-file and missing-file)
     - an `instance` example runs in a valid instance: test_check_documents_copies.py::test_an_instance_example_runs_in_a_valid_instance (new; rows matching and wrong)
     - a wrong example blocks a listed page and is reported in an unlisted one: test_check_documents_copies.py::test_a_wrong_example_in_a_copied_document_fails_only_a_listed_one
     - a dropped settings row gives its finding: test_check_documents_settings.py::test_settings_findings_are_printed_without_changing_the_exit_status
     - a missing operator-guide file or section gives its finding: test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file
   - criterion 4: tests/guards/test_document_tests_write_their_documents.py::test_no_document_check_test_names_the_repositorys_documents (passing side) and ::test_a_document_check_test_that_names_the_repositorys_documents_is_found (one row for each of the four names, on a module written under `tmp_path`)
   - criterion 5: the same guard, test_no_document_check_test_names_the_repositorys_documents
   - criterion 6: tests/entry/test_check_documents_minimal.py::test_added_files_are_committed_and_tracked (rows existing-folder and new-subfolder)
   - criteria 7 and 8: no test (`make check` and the docs belong to the coder and the documenter)

   Files created:
   - tests/support/minimal_documents_support.py: `minimal_documents` and `add_and_commit`. The settings rows, stop rows, sections, kill-point and fault-path rows are read when the function is called from `factory.shared.domain.documents` and `.settings`. The area pages come from the folders of the `factory` package. `add_and_commit` commits only when the work tree changed.
   - tests/entry/test_check_documents_minimal.py
   - tests/guards/test_document_tests_write_their_documents.py

   Earlier tests changed under the leave of feature decision 10:
   - tests/conftest.py: the fixtures `tracked_files` and `documents` are removed. The new fixture `minimal` (minimal documents under `tmp_path`) replaces them.
   - tests/support/documents_copy_support.py: deleted.
   - test_check_documents_copies.py, _settings.py, _operator_guide.py: they now run on `minimal`, and every test keeps its name. The listed page is now `machine.md`, because the minimal documents have no `style.md`. The dropped setting is `SETTINGS[0]` instead of the literal `FACTORY_ZFS`.
   - test_check_documents_todays_names.py: it writes the text into a minimal document instead of reading the repository's documents. Same test name.
   - test_check_documents_checked_files.py: `_write` now builds the minimal documents and adds the test's files through `add_and_commit`.
   - test_check_documents_suite_copy.py: rewritten on `minimal`.
   - test_check_documents_any_list.py: rewritten.

   Tests removed or renamed, with what covers them now:
   - any_list::test_a_test_that_writes_its_list_keeps_its_outcome_when_the_repository_lists_more_pages (only the coupling): its three outcomes are covered by the settings, operator_guide and copies tests.
   - any_list::test_without_its_own_list_the_repository_list_reaches_the_output (only the coupling): removed.
   - any_list::test_listing_the_three_pages_names_each_once_whatever_the_list_already_names (it tested a helper of the repository's list): removed.
   - any_list::test_a_page_the_repository_list_already_names_is_reported_once_unless_appended_again: replaced by test_a_page_listed_once_more_gives_no_second_finding.
   - any_list: the two tests of the written list are kept and run on `minimal`.
   - checked_files::test_todays_documents_with_the_first_list_give_a_report_and_pass (it used the copy of `ROOT`): covered by ::test_without_a_list_file_every_new_finding_is_reported_and_none_blocks and ::test_an_example_not_run_is_reported_after_the_reported_findings_and_never_blocks.
   - copies::test_the_copied_documents_are_a_clean_git_work_tree: covered by minimal::test_the_minimal_documents_pass_the_check_in_a_clean_work_tree.
   - suite_copy::test_the_copy_holds_the_tracked_files_and_nothing_untracked and ::test_two_copies_of_the_session_repository_are_separate (only the coupling): removed.
   - suite_copy::test_an_example_reads_the_tracked_files_of_the_repository: renamed to test_an_example_reads_a_file_git_tracks_in_the_repository. The story's smoke test greps `tests/entry` for `tracked_files` without word boundaries, and the old name would make it print 1.

   Runs:
   - Every module the test run needed imported; none was missing.
   - I ran pytest on the changed test modules and the new guard. After two fixes to my own tests (a `StopRow` built without its required `test` field, and an off-by-one in the wrong-example row), all passed.
   - `make lint` is green.
   - The smoke grep prints 0.
   - I skipped the type check, as the stage says.

   Open:
   - I set aside nothing of a skill.
   - The listed rewrite of the Interface was clear enough that I needed no interpretation.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: Question: the tester's tests fail `make types`, and the only code fix would break the Interface's "No module under `src/factory/` changes". I stopped before writing any code. The working tree is unchanged.

    What I ran:
    - `make test` is green (105.1 s, coverage 99.20 %). That is the "after" time. I did not measure a "before" time, because that needs a run on `main`.
    - `make check` stops at `make types` with 7 errors in two of the tester's files. Each error reads like this: `Module "factory.shared.domain.documents" does not explicitly export attribute "STOP_TABLE"  [attr-defined]`.
      - `tests/support/minimal_documents_support.py`: lines 38 (`documents.STOP_TABLE`), 43 (`documents.KILL_POINT_CASES`) and 44 (`documents.FAULT_PATHS`).
      - `tests/entry/test_check_documents_minimal.py`: lines 35, 36, 40 and 41 (`documents.STOP_TABLE` and `documents.KILL_POINT_CASES`, read in `_one_more_stop` and `_one_more_kill_point`).

    Why: `factory.shared.domain.documents` imports these three tables from `factory.pipeline.domain.stop_table`, `factory.shared.domain.kill_point_cases` and `factory.pipeline.domain.fault_paths`. It does not re-export them, so `mypy --strict` refuses `documents.<name>`. The test still has to patch the name inside `documents`, because the check reads `documents`' own copy of each name.

    Options:
    A. The tester changes the two files. They read the tables from the modules that define them (`stop_table.STOP_TABLE`, `kill_point_cases.KILL_POINT_CASES`, `fault_paths.FAULT_PATHS`). They keep `monkeypatch.setattr(documents, "STOP_TABLE", ...)` and `monkeypatch.setattr(documents, "KILL_POINT_CASES", ...)`, with the name as a string, which mypy accepts. Nothing in `src/` changes, and the tests check the same things.
    B. I re-export the three names in `src/factory/shared/domain/documents.py` (`from ... import STOP_TABLE as STOP_TABLE`, and the same for the other two). That is a one-line change per name, but it goes against the Interface's "No module under `src/factory/` changes".

    I would choose A. With your answer I end with `tests`, naming that change, and the tester makes it. Then I finish `make check` and the refactor step. The `docs:` criterion is the documenter's.

    Noticed and left alone: the tester's entry says it skipped the type check, which is how these errors reached this stage.
11. 2026-11-06 human: A: end with `tests`. The tester reads the three tables from the modules that define them and keeps patching the names inside `documents` with `monkeypatch.setattr(documents, "STOP_TABLE", ...)`, the name as a string. Nothing in `src/` changes. The tests are the tester's own, so no leave is needed.
12. factory: started doing as vm.
13. coder: The human answered option A (journal entry 11), so I wrote no code and the working tree is unchanged. The change for the tester, as the human set it: in `tests/support/minimal_documents_support.py` (lines 38, 43, 44) and `tests/entry/test_check_documents_minimal.py` (lines 35, 36, 40, 41, in `_one_more_stop` and `_one_more_kill_point`), read `STOP_TABLE`, `KILL_POINT_CASES` and `FAULT_PATHS` from the modules that define them (`factory.pipeline.domain.stop_table`, `factory.shared.domain.kill_point_cases`, `factory.pipeline.domain.fault_paths`), not from `factory.shared.domain.documents`. Keep patching the names inside `documents` with `monkeypatch.setattr(documents, "STOP_TABLE", ...)` and `monkeypatch.setattr(documents, "KILL_POINT_CASES", ...)`, the name given as a string. This fixes the 7 `attr-defined` errors from `make types`. Nothing in `src/` changes.

    After this change, `make check` must be green. The tester should also run `make types` on these two files, because skipping it is how these errors reached the doing stage. When the work item comes back, I will run `make check`, do the refactor step, and report the `make test` time. Last run, after the story: 105.1 s. There is no before time yet, because that needs a run on `main`.
14. factory: started tests as vm.
15. tester: I made the test change the human approved in entry 11, as entry 13 describes it. Nothing under `src/` changed.

    Files changed (both are my own tests from this story):
    - `tests/support/minimal_documents_support.py`: `STOP_TABLE`, `KILL_POINT_CASES` and `FAULT_PATHS` are now read from the modules that define them: `factory.pipeline.domain.stop_table`, `factory.shared.domain.kill_point_cases` and `factory.pipeline.domain.fault_paths`. They are no longer read through `factory.shared.domain.documents`.
    - `tests/entry/test_check_documents_minimal.py`: `_one_more_stop` and `_one_more_kill_point` build the extended table from the defining module. They still patch the name inside `documents` with `monkeypatch.setattr(documents, "STOP_TABLE", ...)` and `monkeypatch.setattr(documents, "KILL_POINT_CASES", ...)`, the name given as a string.

    One addition beyond the literal wording, needed to keep the test checking the same thing: each helper also patches the same extended table into its defining module (`monkeypatch.setattr(stop_table, "STOP_TABLE", ...)` and `monkeypatch.setattr(kill_point_cases, "KILL_POINT_CASES", ...)`). The support module now reads the defining modules. Without this second patch, the minimal documents would not contain the added row, while the check, which reads `documents`' copy, would expect it. Then `test_the_minimal_documents_follow_one_more_row_of_the_codes_tables[stop]` and `[kill-point]` would fail for a reason in the test, not in the code. Test names and what they check are unchanged.

    Criterion mapping: unchanged from my earlier entry.

    Runs:
    - `uv run pytest -q tests/entry/test_check_documents_minimal.py tests/support/minimal_documents_support.py`: 6 passed. Every module imported; none was missing.
    - `make lint`: green.
    - `make types`: green (1029 source files). That clears the 7 `attr-defined` errors the coder reported.

    I set aside no skill step.

    `lint`: lint: green (0.1 s)
16. factory: started doing as vm.
17. coder: I wrote no code, and the working tree is unchanged. Nothing under `src/factory/` changes in this story. The tests and the support module (`tests/support/minimal_documents_support.py`, `tests/entry/test_check_documents_minimal.py`, `tests/guards/test_document_tests_write_their_documents.py` and the rewritten `tests/entry/test_check_documents_*.py`) are the tester's. The tester made the type fix the human chose in entry 11 (entry 15). This round, all I had to do was run `make check` and the refactor step.

    - `make check`: green. The test step reports `test: green (106.7 s)` and coverage of 99.20 %.
    - Refactor: I had no diff of my own to read, so nothing changed.
    - `make test` time, before and after the story (asked for in the Description, not a criterion):
      - After the story: 106.7 s in this run's `make check`, and 105.1 s in entry 10.
      - Before the story: no `make check` figure. I ran the plain pytest suite (`-n auto --dist worksteal`, no coverage) on a temporary `--shared` clone of the local `main` branch. That branch's tip is `4d108428c`, which already holds this story's tests, so the figure does not show the time before them. That run took 87 s. Two tests in `tests/hosting/adapters/test_instance_fixture.py` failed there (the rows `healthy` and `a-wrong-instance-name-is-refused` of `test_the_commands_of_a_block_on_the_instance_print_what_a_valid_instance_prints`). They are likely caused by running from a clone with `PYTHONPATH`, outside the project's environment, not by the code. They pass in `make check` here.
      - A second measurement on `origin/main` and on the branch with the same method was refused at the permission prompt, so I have no like-for-like "before" figure. Whoever needs it can run `make test` on `main` against `make test` on this branch.
    - Main choice: I left the code alone and made no `src/` change, as the Interface says (option A, which the human chose). Rejected: re-exporting `STOP_TABLE`, `KILL_POINT_CASES` and `FAULT_PATHS` from `factory.shared.domain.documents`.
    - Open: criterion 8 (`docs:` in `docs/project-guide/shared.md`, `docs/project-guide/style.md` and `docs/decisions.md`) is the documenter's.
    - Noticed and not touched: the local `main` branch in the checkout ends at a journal commit of this work item (`4d108428c`), not at a clean `main`.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
18. factory: started review as vm.
19. reviewer: Review, round 0. I read the work item, the diff's stat and name-status, and the whole diff of `tests/`. Nothing under `src/` or the documents changed. I checked the diff against `src/factory/shared/domain/documents.py`, `src/factory/entry/check_documents.py` and `tests/support/document_texts.py`. The tests read the tables when they run: `documents.py` looks up `STOP_TABLE`, `KILL_POINT_CASES` and `FAULT_PATHS` as module globals inside its functions, and `check_documents.py:126` reads `settings.SETTINGS`. So criterion 2's `monkeypatch` rows really test what they say. Every criterion from 1 to 6 has its test, and the coder's `make check` was green (journal entry 17). Two findings send the work item back.

    Findings:
    1. `tests/support/minimal_documents_support.py:16-46` copies existing helpers in `tests/support/document_texts.py`:
       - `_page` copies `_document`.
       - `_settings_rows` copies `SETTINGS_TABLE` (the same text).
       - `_stops` copies the rows of `operator_stops`.
       - `_project_guide` copies the rows of `project_guide`.
       - `_texts` copies `clean_texts`, plus the area pages and the list.

       The copy exists because `document_texts` binds `STOP_TABLE`, `KILL_POINT_CASES`, `FAULT_PATHS` and `SETTINGS` when it is imported, so a monkeypatch does not reach it.

       Fix: make `document_texts` read the tables through their modules when it is called (`stop_table.STOP_TABLE`, `settings.SETTINGS`, and so on). Then build `minimal_documents` from `clean_texts()`, adding only the area pages and the empty `docs/checked-documents.txt`. If the tester finds that changing `document_texts` (another story's support module) is beyond feature decision 10, that is a question to the human, not a reason to keep the copy.
    2. `tests/guards/test_document_tests_write_their_documents.py:14` misses a parenthesized import. The `ROOT` pattern `from support\.operator_support import [^\n]*\bROOT\b` does not match `from support.operator_support import (\n    ROOT,\n)`, which is the form ruff format writes once an import gets long. A module importing `ROOT` that way would pass the guard of criteria 4 and 5.

       Fix: let the pattern match across the parentheses, for example `import \(?[^)]*?\bROOT\b` with re.S on that pattern. Add a row with the parenthesized form to `test_a_document_check_test_that_names_the_repositorys_documents_is_found`.

    Earlier tests that the diff changes, renames or deletes, with the leave each was changed under. Each is the human's leave: feature decision 10, which the story names in its Interface, given for the modules, fixtures and support module listed there:
    - `tests/conftest.py`: the fixtures `tracked_files` and `documents` are removed, and `minimal` is added.
    - `tests/entry/test_check_documents_any_list.py`: three coupling tests are removed and named in entry 8. `test_a_page_the_repository_list_already_names_is_reported_once_unless_appended_again` is replaced by `test_a_page_listed_once_more_gives_no_second_finding`.
    - `tests/entry/test_check_documents_checked_files.py`: `test_todays_documents_with_the_first_list_give_a_report_and_pass` is removed, and entry 8 names the tests that now cover it.
    - `tests/entry/test_check_documents_copies.py`: `test_the_copied_documents_are_a_clean_git_work_tree` is removed, and criterion 1's test now covers it.
    - `tests/entry/test_check_documents_operator_guide.py`: it runs on `minimal`.
    - `tests/entry/test_check_documents_settings.py`: it runs on `minimal`.
    - `tests/entry/test_check_documents_suite_copy.py`: two coupling tests are removed. `test_an_example_reads_the_tracked_files_of_the_repository` is renamed to `test_an_example_reads_a_file_git_tracks_in_the_repository`, for the smoke test's grep, as entry 8 says.
    - `tests/entry/test_check_documents_todays_names.py`: it runs on `minimal`.
    - `tests/support/documents_copy_support.py`: deleted.

    Nothing else is open. Criterion 8 (`docs:`) is the documenter's.
20. factory: started doing as vm.
21. coder: Round 1. I wrote no code, and the working tree is unchanged. Both of the reviewer's findings (entry 19) are changes to tests and support modules under `tests/`, and the coder never edits tests (R9). So I am sending them to the tester as the reviewer wrote them:

    1. Remove the copied helpers from `tests/support/minimal_documents_support.py`. The copies are `_page`, `_settings_rows`, `_stops`, `_project_guide` and `_texts`, which duplicate `tests/support/document_texts.py`. To do that, `document_texts` has to read `STOP_TABLE`, `KILL_POINT_CASES`, `FAULT_PATHS` and `SETTINGS` from their modules each time it is called, not bind them at import. Then `minimal_documents` can be built from `clean_texts()`, plus the area pages and the empty `docs/checked-documents.txt`. `document_texts` is another story's support module. If the tester decides that changing it goes beyond feature decision 10, that is a question for the human, not a reason to keep the copy.
    2. Fix the `ROOT` pattern in `tests/guards/test_document_tests_write_their_documents.py:14`. Today it only matches an import on a single line, so a parenthesized import (`from support.operator_support import (\n    ROOT,\n)`) gets past the guard. Make it match across the parentheses, for example `import \(?[^)]*?\bROOT\b` with `re.S`. Also add a parenthesized-import row to `test_a_document_check_test_that_names_the_repositorys_documents_is_found`.

    Main choice: I left the code alone. Nothing under `src/factory/` changes in this story, and neither finding needs a source change. Rejected: making the fixes myself. Both are test changes, which belong to the tester.

    Checks: I did not run `make check` or `make test` this round, because I changed no file. The last `make check`, in entry 17, was green, with `make test` at 106.7 s. When the work item comes back I will run `make check` and do the refactor step.

    Noticed and not touched: on line 14 I confirmed that the `ROOT` pattern ends at the first newline (`[^\n]*`), so finding 2 is real. Criterion 8 (`docs:`) is the documenter's.
22. factory: started tests as vm.
23. tester: Mode: a test change the human approved. I made both changes that the coder's entry 21 passes on from the reviewer's findings in entry 19. No new test function. No criterion's test changed its name.

    1. The copied helpers are gone.
       - `tests/support/document_texts.py` (another story's support module) now reads the code's tables from their modules when it is called, not when it is imported: `stop_table.STOP_TABLE`, `kill_point_cases.KILL_POINT_CASES`, `fault_paths.FAULT_PATHS` and `settings.SETTINGS`.
       - The module constant `SETTINGS_TABLE` became the private `_settings_table()`. No other module imported it.
       - Every builder keeps its name and signature, and gives the same text when nothing is monkeypatched. So every earlier test that uses it checks the same thing.
       - Leave: the standing leave of `CLAUDE.md` *Tests* (one shared place, no copy), as the reviewer asked.
       - `tests/support/minimal_documents_support.py` lost `_page`, `_settings_rows`, `_install`, `_stops` and `_project_guide`. `_texts()` is now `clean_texts()` plus one page per area under `docs/project-guide/` and the empty `docs/checked-documents.txt`.
    2. The guard in `tests/guards/test_document_tests_write_their_documents.py` now finds an import of `ROOT` in parentheses. The `ROOT` pattern is now `from support\.operator_support import (?:\([^)]*|[^\n(]*)\bROOT\b`. I chose this over the reviewer's suggestion because it needs no `re.S`: inside the parentheses it reaches across lines, outside them it stays on one line.
       - `test_a_document_check_test_that_names_the_repositorys_documents_is_found` now takes `(name, naming)`. It has one row per name, as before, plus the row `parenthesized-ROOT` (`from support.operator_support import (\n    OTHER,\n    ROOT,\n)`).

    Criterion → test (unchanged from entry 15, with the guard's added row):
    - criterion 1: tests/entry/test_check_documents_minimal.py::test_the_minimal_documents_pass_the_check_in_a_clean_work_tree
    - criterion 2: tests/entry/test_check_documents_minimal.py::test_the_minimal_documents_follow_one_more_row_of_the_codes_tables
    - criterion 3: the rewritten tests/entry/test_check_documents_*.py modules, as mapped in entry 8
    - criterion 4: tests/guards/test_document_tests_write_their_documents.py::test_no_document_check_test_names_the_repositorys_documents and ::test_a_document_check_test_that_names_the_repositorys_documents_is_found
    - criterion 5: tests/guards/test_document_tests_write_their_documents.py::test_no_document_check_test_names_the_repositorys_documents
    - criterion 6: tests/entry/test_check_documents_minimal.py::test_added_files_are_committed_and_tracked

    Files changed: tests/support/document_texts.py, tests/support/minimal_documents_support.py, tests/guards/test_document_tests_write_their_documents.py. No file created.

    Runs:
    - `uv run pytest -q` on the guard and on `tests/entry/test_check_documents_minimal.py`: all passed, and every module imported. I did not run the other modules that use `document_texts` in this stage; the coder's `make check` covers them.
    - `make lint`: green, after ruff fixed the import order in `document_texts.py`.
    - Type check skipped, as the stage says.

    Open: criterion 8 (`docs:`) is the documenter's.

    `lint`: lint: green (0.2 s)
24. factory: started doing as vm.
25. coder: Round 1, after the tester's changes. I wrote no code, and the working tree holds only the tester's work. Nothing under `src/factory/` changes in this story. The tester made both of the reviewer's findings from entry 19, as entry 21 passed them on (entry 23):
    - `tests/support/document_texts.py` now reads the code's tables through their modules each time it is called, and `tests/support/minimal_documents_support.py` builds its documents from `clean_texts()`. The copied helpers are gone.
    - The `ROOT` pattern in `tests/guards/test_document_tests_write_their_documents.py` now also matches an import in parentheses, and the guard's test has a row for that form.

    - `make check`: green. The test step reports `test: green (106.3 s)`, with coverage at 99.20 %.
    - Refactor: I have no diff of my own to read, so I changed nothing.
    - `make test` time: 106.3 s after the story, which is the same as the 106.7 s in entry 17. Entry 17 also explains why I have no like-for-like figure for before the story.
    - Main choice: I left `src/` untouched, as the Interface says. Rejected: making the test fixes myself. That is the tester's work (R9).
    - Open: criterion 8 (`docs:`) is the documenter's.
    - Noticed and not touched: nothing new.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
26. factory: started review as vm.
27. reviewer: Review, round 1. I read the work item, the diff's stat and name-status, and the whole diff under `tests/`. Nothing under `src/` and no document changed. I checked the diff against `src/factory/shared/domain/documents.py` and `src/factory/entry/check_documents.py`.

    Both findings from round 0 (entry 19) are fixed:
    - Finding 1, the copied helpers. `tests/support/minimal_documents_support.py` now builds its documents from `clean_texts()` of `tests/support/document_texts.py`. It adds only one page per area and the empty `docs/checked-documents.txt`. `document_texts` now reads `stop_table.STOP_TABLE`, `kill_point_cases.KILL_POINT_CASES`, `fault_paths.FAULT_PATHS` and `settings.SETTINGS` when it is called, so the `monkeypatch` rows of criterion 2 reach the texts. `SETTINGS_TABLE` is gone and no other module imported it. `tests/entry/test_check_documents_checked_files.py:31` has its own local constant of that name.
    - Finding 2, the guard. The `ROOT` pattern in `tests/guards/test_document_tests_write_their_documents.py:14-17` now reaches across lines inside the parentheses, and the guard's test has the row `parenthesized-ROOT`.

    Criteria 1 to 6 each have their test, as mapped in entries 8 and 23. Every behaviour in the Interface's list has a test on `minimal`, with both sides where the story asks for both. The skipped-block test and the page-listed-again test now compare the exact output. Criterion 5's guard covers every `check_documents` module under `tests/entry/`. The one call without `--root`, `tests/entry/test_check_documents.py:68` (`main([])`), first runs `chdir` into `tmp_path`. The smoke test's grep finds nothing in `tests/entry`. The coder's `make check` was green (entry 25). The Description and the docs criterion match what was built.

    no findings

    Earlier tests that the diff changes or deletes, and the leave each was changed under:
    - `tests/conftest.py`: the human's leave, feature decision 10, named in the story's Interface. The fixtures `tracked_files` and `documents` are removed and `minimal` is added.
    - `tests/entry/test_check_documents_any_list.py`: the human's leave, feature decision 10. The tests that only checked the coupling are removed and named in entry 8.
    - `tests/entry/test_check_documents_checked_files.py`: the human's leave, feature decision 10.
    - `tests/entry/test_check_documents_copies.py`: the human's leave, feature decision 10.
    - `tests/entry/test_check_documents_operator_guide.py`: the human's leave, feature decision 10.
    - `tests/entry/test_check_documents_settings.py`: the human's leave, feature decision 10.
    - `tests/entry/test_check_documents_suite_copy.py`: the human's leave, feature decision 10. One test is renamed for the smoke test's grep, as entry 8 says.
    - `tests/entry/test_check_documents_todays_names.py`: the human's leave, feature decision 10.
    - `tests/support/documents_copy_support.py` (deleted): the human's leave, feature decision 10.
    - `tests/support/document_texts.py`: the standing leave to move a shared test helper (`CLAUDE.md` *Tests*). The shared module now reads the code's tables when called, so that it can replace the copy in the new support module. Every builder keeps its name and signature, and gives the same text when nothing is patched, so every earlier test that uses it checks the same thing.
28. factory: started docs as vm.
29. documenter: Round 1, docs stage. I read the story, the tests the diff changes (`tests/support/minimal_documents_support.py`, `document_texts.py`, the guard, `tests/conftest.py`) and the four documents. Nothing under `src/` changed, so I found no contradiction between code and Interface.

    Files changed:
    - `docs/project-guide/shared.md`: the paragraph about tests on the `documents` copy is replaced by a new section *How the check is tested*. It says the tests run on minimal documents built from the code's tables, how a test adds what its rule needs (`add_and_commit`, `append_block`, `write_checked_list`, `drop_settings_row`), that the real documents are checked only by `make documents` in the docs stages, and what the guard refuses.
    - `docs/project-guide/style.md`, *Runnable examples*: the sentence that said the suite runs every document's examples on a copy (the `documents` fixture) is replaced. It now says the suite runs none of them. A wrong example blocks `make documents` in a listed file and is reported in any other (that sentence stays). I added "listed or not" to the closing sentence of that paragraph.
    - `docs/project-guide/README.md`: it lists `support/minimal_documents_support.py` and the fixture `minimal`. It adds `clean_texts` to `document_texts` and notes that the builders read the code's tables when called. It no longer calls the list or the block in `check_documents_support` a "copy's".
    - `docs/decisions.md`: new entry "The check's tests run on documents they write", with Decision, Why and Rejected, all taken from the docs criterion.

    Checks: `make documents` ends with `documents ok (0.6 s)`. I changed only documents, so I did not run `make check`, as the stage says. The new section has no runnable example. I named code from the files on the branch.

    Cross-read and found current: `docs/project-guide/glossary.md`, `work.md`, `hosting.md`, `machine.md`, `agents.md`, `pipeline.md`, `watching.md`, the operator guide and the README. None of them names `tracked_files`, `documents_copy_support` or the `documents` fixture. A grep of `docs/` and the README finds no other mention of those.

    Stale text I saw and left alone (unrelated to this story): `make documents` prints existing report lines for names that do not exist: `machine.md:264`, `:298`, `:362` and `work.md:13`. They never block.

    No findings.

    `check`: check: green
    `secrets`: secrets: green (1.9 s)
    `documents`: documents ok (0.6 s)
30. factory: started smoke-test as vm.
31. smoke-tester: Smoke test, round 1. I ran both commands under `## Smoke test` from the repository root, exactly as written and in order. Nothing was fixed.

    Command 1: `grep -rlE "tracked_files|documents_copy_support|operator_support import ROOT" tests/entry | wc -l`
    ```
    0
    ```
    Expect: `0`. Met.

    Command 2: `uv run python -m factory.entry.check_documents | tail -1`
    ```
    Bytecode compiled 4164 files in 49ms
    documents ok (0.6 s)
    ```
    The first line is uv's own message on standard error; the pipe's last line is `documents ok (0.6 s)`, and check_documents exited with 0. Expect: `documents ok (<seconds> s)`. Met.

    Against the acceptance criteria:
    - `tests/support/minimal_documents_support.py` and `tests/guards/test_document_tests_write_their_documents.py` exist.
    - `tests/support/documents_copy_support.py` is gone, and `tests/conftest.py` no longer defines `tracked_files` or `documents` (Interface).
    - No module under `src/` differs from `origin/main`.
    - For criterion 8, `docs/project-guide/shared.md` has the section on how the check is tested (minimal documents built from the code's tables, tests that add what their rule needs, the real documents checked only by `make documents`). `docs/project-guide/style.md`, *Runnable examples*, says a wrong example blocks in a listed file, is reported in any other, and that the test suite runs none of the documents' examples. `docs/decisions.md` has the entry "The check's tests run on documents they write".
    - Command 1 is consistent with criterion 5.
    - The smoke test contradicts no criterion. Criteria 1–4 and 6–7 are left to the tests and to the factory's `make check`; I did not run them here.

    Findings: none.
