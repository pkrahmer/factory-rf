---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 589
comments_read: [6681611113, 6681795743]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-06T09:48:04.374627Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T09:23:35.956444Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T09:23:35.963315Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-06T09:24:06.084697Z'
  stage: intake
  run: 4140d0a57d194ccd894297f6195a4876
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-06T09:25:56.045409Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-06T09:25:58.540243Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-06T09:26:17.282299Z'
  stage: intake
  run: adb14e06a0d04bca9410b86cb5469efd
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-06T09:26:22.445613Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-06T09:29:19.677546Z'
  stage: tests
  run: f83c76cb0fd3459f936643d8dbad3fc2
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-06T09:29:25.114973Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-06T09:35:04.710279Z'
  stage: doing
  run: 625cd5fbb848407a8376555c7bf1bda7
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-06T09:36:54.745744Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-06T09:36:57.258125Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-06T09:37:28.343874Z'
  stage: doing
  run: 5f289285080748c29677ac2d1410e235
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-06T09:37:33.617343Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-06T09:38:43.304514Z'
  stage: tests
  run: 62473c178988402288643724268f171c
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-06T09:38:48.638434Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-06T09:45:00.906417Z'
  stage: doing
  run: 3a44e0bcfd0648789a02f651c7b64d0b
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-06T09:45:06.770814Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-06T09:46:28.610405Z'
  stage: review
  run: f7a83f390392413eafca02706f74047c
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-06T09:46:34.165361Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-11-06T09:47:08.040524Z'
  stage: doing
  run: 086421699cdb48e7934d949b12ac430f
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-06T09:47:13.381244Z'
  stage: tests
- number: 23
  speaker: tester
  kind: result
  at: '2026-11-06T09:47:58.450308Z'
  stage: tests
  run: c5fc039889fb4298a4a95cbd150ef40a
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-06T09:48:04.374627Z'
  stage: doing
---

# The checks block the listed files and report on the others

## Description

The new checks (names, settings, examples) will find many faults in today's documents, and blocking on all of them at once would stop every docs stage until the whole guide is rewritten (feature decision 2). This story adds a list of checked files: a finding of the new checks in a listed file fails `make documents`; a finding in any other file is printed under a heading `Report (not checked yet):` and leaves the exit status alone. The list starts with the two pages already written in the new style, the style page and the glossary. The rewrite feature adds each file when it rewrites it, and the list is complete when every file is on it. The checks that exist today keep failing as they do for every file.

## Interface

- The list is a file, `docs/checked-documents.txt`: one document path per line, `#` for comments. At first it holds `docs/project-guide/style.md` and `docs/project-guide/glossary.md`, the two pages already written in the new style (F0052-S0003); if one of them has a blocking finding, this story fixes it in the page. It is a document file on purpose, so that a story on the docs route can add a line to it (the documenter writes `docs/*`).
- `factory.shared.domain.documents`: `read_checked_documents(text) -> list[str]` (pure; a path that is no document of the check is a finding), and the split of the findings into blocking and reported ones.
- The command prints the blocking findings first, then the report, then its last line: `documents ok (<seconds> s)` when nothing blocks (also with a report), otherwise one line per blocking finding and exit status 1.
- The name check of the first story of this feature reads three kinds of text more exactly, so that a file can be put on the list without false findings (the human, 2026-11-06, from the 149 findings on today's documents):
  - a backticked dotted name that starts with `factory.` and ends in a file extension (`.env`, `.service`, `.yml`, `.yaml`, `.json`, `.toml`, `.md`, `.txt`) is a file name, such as `factory.env`, and is not checked as a module;
  - in a pytest node id, such as `tests/a/test_b.py::test_c`, only the path before `::` is checked;
  - a text that holds `$` is a shell expression, such as `$XDG_CONFIG_HOME/kumpel/site.env`, and is not checked.
- Tests: `tests/entry/test_check_documents_checked_files.py`, and rows for the three kinds in the name check's tests.

## Acceptance criteria

1. A finding of the name, settings or example check in a file on `docs/checked-documents.txt` fails the command; the same finding in a file not on it is printed under `Report (not checked yet):` and the command ends with `documents ok` (rows of one test).
2. A finding of today's checks (a missing stop row, a missing section, an old word) fails the command for every file, as before.
3. With today's documents and the first `docs/checked-documents.txt` (the style page and the glossary), `make documents` prints a report and ends with `documents ok (<seconds> s)`.
4. `factory.env` and `factory.local.env` in backticks give no finding; `tests/x.py::test_y` gives the finding of a missing `tests/x.py` and none when it exists; `$HOME/a/b.txt` gives none (rows of the name check's test).
5. A listed path that does not exist gives one finding that fails the command; a listed path that is not a document the check reads (`docs/decisions.md`) gives one finding that fails the command (one row each).
6. A `#` line and a blank line in the list give no entry (one row).
7. The output has the blocking findings first, then the report under its heading, then nothing more (one test).
8. On the failing side the output is one line per blocking finding, then the report, no `documents ok` line, and exit status 1.
9. With nothing to report, the heading `Report (not checked yet):` is not printed (one row).
10. A backticked text that holds `$` is skipped as a whole (`$HOME/factory.nothing.here` gives none); a pytest node id without `::` is read as before; `factory.shared.domain.yml_reader` is still checked as a module and gives a finding when it does not exist (rows of the name check's test).
11. With no `docs/checked-documents.txt`, the list is empty: a finding of the name, settings or example check in any file is printed under `Report (not checked yet):`, none blocks, and the command ends with `documents ok` (one row).
12. A line for an example not run (`<document>:<line>: not run (<kind>)`) is printed in the report after the reported findings, also for a listed file, and never fails the command (rows of one test: listed and not listed).
13. `make check` stays green.
14. docs: `docs/project-guide/shared.md`: the checked files and the report. `docs/project-guide/style.md`, rule 8: a path of another repository, such as the project the factory runs on, starts with a placeholder (`<project>/factory/agents/`), and a path in the repository is written from its root (`tests/support/time_limits.py`, not `support/time_limits.py`), so that the name check reads it right. `docs/decisions.md`: an entry for feature decisions 1 to 4, naming F0053.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: 1. `read_checked_documents(text)`: "a path that is no document of the check is a finding" has no criterion for its failing side (for example a listed path that does not exist, or that is outside the checked documents such as `docs/decisions.md`). Proposed: add a criterion that such a line is a finding that fails the command. Which paths count as "no document of the check"?
   2. The same Interface line says `#` starts a comment, and blank lines are skipped. No criterion tests either. Proposed: add one (a `#` line and a blank line give no entry).
   3. The output order is stated (blocking findings first, then the report, then the last line). No criterion tests it. Proposed: add one, or drop the sentence.
   4. Also unspecified and untested: `documents ok (<seconds> s)` is stated for the passing side, but the failing side prints "one line per blocking finding" and exit status 1, and no criterion checks that the `documents ok` line is absent then. Criterion 1 covers the exit status only. Proposed: extend criterion 1 to include the one-line-per-finding output.
   5. The `Report (not checked yet):` heading when there is nothing to report: printed or omitted? Proposed: omitted. Please state it and add a criterion.
   6. The three new name-check readings each have a criterion in 4, but the edges are open. A `factory.x.y.json`-style name is a file name only with the listed extensions, so a negative row is needed (`factory.shared.domain.yml_reader` is still checked as a module). A `$` text is skipped, but is the whole backticked text skipped, or only the part after `$`? Proposed: the whole text. For `tests/x.py::test_y`, is a node id that has no `::` unchanged? Please add the rows you want.
   7. The smoke test is `uv run python -m factory.entry.check_documents | tail -1` with `Expect: documents ok`. That is runnable and the pytest `-q` rule does not apply. The smoke test is acceptable once criterion 3 is fixed.
   8. Route: the Interface changes `src/` and `tests/`, so I would route this to `tests` once the questions are answered.
4. 2026-11-06 human: 1. Yes: a listed path that does not exist, or that is not one of the documents the check reads (`README.md`, a file of `docs/operator-guide/` or of `docs/project-guide/`; so `docs/decisions.md` is a finding), gives one finding that fails the command. One row each.
   2. Yes: a `#` line and a blank line give no entry (one row).
   3. Yes, keep the sentence and test it: blocking findings first, then the report under its heading, then nothing more.
   4. Yes: on the failing side the output is one line per blocking finding (then the report), no `documents ok` line, and status 1.
   5. Omitted: with nothing to report, the heading is not printed (one row).
   6. The whole backticked text that holds `$` is skipped. A pytest node id without `::` is read as before. And yes to the negative row: `factory.shared.domain.yml_reader` is still checked as a module.
   7. The smoke test's last line carries its time: `Expect: documents ok (<seconds> s)`.
5. factory: started intake as vm.
6. intake: accepted, with the human's answers (journal entry 4) written into the story.
   - Interface: concrete. `docs/checked-documents.txt`, `factory.shared.domain.documents.read_checked_documents(text) -> list[str]`, the output order and the three name-check readings are stated. Entry 4 adds the edges: the whole backticked text that holds `$` is skipped, a node id without `::` is read as before, and `factory.shared.domain.yml_reader` is still checked as a module.
   - Criteria: each is testable by one test function. From entry 4 I added criteria 5 to 10 before the two closing ones: a listed path that does not exist, a listed path that is no document of the check, comment and blank lines, the output order, the failing-side output (no `documents ok`, status 1), the omitted heading, and the `$` and `yml_reader` rows. Criterion 1 already covers the pass and fail sides of blocking against reporting. `make check` is now 11 and `docs:` 12.
   - Smoke test: runnable, and the pytest `-q` rule does not apply. `Expect:` now reads `documents ok (<seconds> s)` (entry 4, item 7).
   - Architecture: the pure logic goes in `shared.domain`, and the command stays in `factory.entry`. That fits.
   - Scope: it is within F0053 scope, "the checked-files list and a report" (S0004). `docs/decisions.md` is not checked, as the feature's out-of-scope section says. The route is `tests`, because the Interface changes `src/` and `tests/`.
7. factory: started tests as vm.
8. tester: Wrote the tests for the checked-documents list and the report, and added the name check's rows for the three new kinds of text.

   Criterion → test:
   - criterion 1: tests/entry/test_check_documents_checked_files.py::test_a_new_finding_blocks_in_a_listed_file_and_is_reported_in_any_other (name, settings and example findings × listed and not listed)
   - criterion 2: tests/entry/test_check_documents_checked_files.py::test_a_finding_of_the_checks_of_before_fails_for_every_file (missing stop row, missing section, old word × listed and not listed)
   - criterion 3: tests/entry/test_check_documents_checked_files.py::test_todays_documents_with_the_first_list_give_a_report_and_pass (runs `main` read-only on the repository root, because the name check needs the real `src/` and `tests/`; it also checks that the list reads as exactly the style page and the glossary)
   - criterion 4: tests/shared/domain/test_document_references.py::test_named_references_finds_backticked_names_paths_and_links (new rows: `factory.env`, `factory.local.env`, `factory.x.<each listed extension>`, `tests/x.py::test_y`, `$HOME/a/b.txt`) and tests/entry/test_check_documents_checked_files.py::test_file_names_node_ids_and_shell_texts_are_read_exactly (a node id gives the finding of a missing `tests/x.py` and none once the file exists)
   - criterion 5: tests/entry/test_check_documents_checked_files.py::test_a_listed_path_that_is_no_document_of_the_check_is_one_blocking_finding (missing path; `docs/decisions.md`)
   - criterion 6: tests/entry/test_check_documents_checked_files.py::test_a_comment_line_and_a_blank_line_give_no_entry
   - criterion 7: tests/entry/test_check_documents_checked_files.py::test_the_output_is_the_blocking_findings_then_the_report_and_nothing_more
   - criterion 8: tests/entry/test_check_documents_checked_files.py::test_the_failing_side_prints_one_line_per_blocking_finding_then_the_report
   - criterion 9: tests/entry/test_check_documents_checked_files.py::test_the_report_heading_is_left_out_when_there_is_nothing_to_report
   - criterion 10: the same two tests as criterion 4 (rows `$HOME/factory.nothing.here`, `tests/x.py` without `::`, `factory.shared.domain.yml_reader` as a module, which also gives a finding at the entry level)
   - criteria 11 and 12: no test (`make check`, docs).

   Files:
   - Created `tests/entry/test_check_documents_checked_files.py`.
   - Changed `tests/shared/domain/test_document_references.py`, which an earlier story wrote. I only added rows to its parametrized name-check test, because the story's Interface names those rows ("rows for the three kinds in the name check's tests"). Existing rows are unchanged.

   Assumptions the coder should know:
   - A reported line is the finding's own text. The tests strip leading and trailing whitespace from each output line, so the report may indent its lines.
   - Every entry test writes a `docs/checked-documents.txt`. What happens when the file is missing is not specified and is not tested.
   - No test uses a skipped ("not run") example block, because the criteria do not say whether such blocks belong to the report.

   Test run: `uv run pytest -q` on the two files stopped at collection, for the right reason: `ImportError: cannot import name 'read_checked_documents' from 'factory.shared.domain.documents'`. Because the run was interrupted, the domain file's new rows did not run. A collect-only pass of that file alone collected 34 cases without error. `make lint` is green.

   Module the test run could not import: `factory.shared.domain.documents.read_checked_documents`.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: Stopped before handing forward. The code is in the working tree and the tester's two files pass (61 cases), but `make check` is red: six tests from earlier stories rule out the report heading this story's Interface requires.

    Built (not committed):
    - `src/factory/shared/domain/documents.py`:
      - The name check reads three kinds of text more exactly. A backticked text with `$` is skipped as a whole. A pytest node id is read up to its `::`. A dotted `factory.` name ending in `.env`, `.service`, `.yml`, `.yaml`, `.json`, `.toml`, `.md` or `.txt` is a file name, not a module.
      - New: `CHECKED_DOCUMENTS`, `read_checked_documents(text)`, `checked_list_findings(listed, documents)` (one blocking finding for each listed path that is not a document the check reads), the models `NewFinding` and `SplitFindings`, and `split_findings(findings, checked)`.
    - `src/factory/entry/check_documents.py`:
      - Each finding of the name, settings and example checks carries its document.
      - Blocking: today's findings, the list's findings and the new findings in listed files. They print first.
      - Then `Report (not checked yet):` and the other new findings plus the lines for examples not run. The heading is left out when the report is empty.
      - `documents ok (<s> s)` is printed only when nothing blocks; otherwise the exit status is 1.
      - A missing list file is an empty list.
    - `docs/checked-documents.txt`: the style page and the glossary. Neither has a blocking finding. On today's documents the command prints a report and ends with `documents ok (0.3 s)`.

    The contradiction (R9):
    - `tests/entry/test_check_documents_references.py::test_name_findings_follow_todays_findings_and_leave_the_exit_status[one-today]` asserts `lines[: len(lines) - len(findings)] == [today]`. The output is now `[today, "Report (not checked yet):", findings...]`.
    - `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file`, rows `no-stops-section`, `no-install-section`, `no-configuration-section`, `no-install-file` and `no-index`. Each filters out only the lines ending in ` does not exist` and compares the rest exactly. The heading line is left over, for example `E   docs/operator-guide/README.md: missing` / `E + Report (not checked yet):`.
    - Criterion 1 requires the heading whenever a finding is in a file not on the list, so no code passes both.

    Options:
    - A (my choice): the human allows the tester two changes. In the operator-guide test, also filter the line `Report (not checked yet):` before comparing. In the `one-today` row, expect `[today, "Report (not checked yet):"]` before the findings. Both tests keep their names and what they check.
    - B: change the Interface so the report has no heading (criteria 1, 7, 8 and 9 and the new tests change with it).

    Main decision: each new finding carries its document, and the list decides what blocks by document. Rejected: parsing the `doc:line:` prefix of the printed lines, which is fragile.

    Open:
    - Lines for examples not run are not findings. I put them at the end of the report, never blocking; the criteria are silent on them.
    - The refactor step is still to do.
    - I could not confirm that `docs/checked-documents.txt` lies within the coder's write paths. If it does not, the take drops it.
    - The docs criterion (12) is the documenter's.

    The factory left out changes outside the write paths: docs/checked-documents.txt.
11. 2026-11-06 human: A, with the human's leave: end with `tests`. The tester makes two changes and nothing else in those modules. In `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file`, the line `Report (not checked yet):` is also left out before the comparison. In the `one-today` row of `tests/entry/test_check_documents_references.py::test_name_findings_follow_todays_findings_and_leave_the_exit_status`, `[today, "Report (not checked yet):"]` is expected before the findings. Both keep their names and what they check, and the entry names them.
    The lines for examples not run stay at the end of the report and never block: that is right.
    `docs/checked-documents.txt` lies outside the coder's write paths, so the take dropped it, as you feared. The documenter writes it in the docs stage, with the style page and the glossary. Until then a missing list file is an empty list, as you built it. A test that needs the list writes its own under `tmp_path`.
12. factory: started doing as vm.
13. coder: No code changed this round. Following the human's answer (journal entry 11, option A), the work item goes to the tester for test changes. The code from the previous doing round is already committed in 2b6135a73 (`src/factory/shared/domain/documents.py`, `src/factory/entry/check_documents.py`).

    Test changes for the tester:
    1. In `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file`, also leave out the line `Report (not checked yet):` before the comparison. This makes rows `no-stops-section`, `no-install-section`, `no-configuration-section`, `no-install-file` and `no-index` pass.
    2. In the `one-today` row of `tests/entry/test_check_documents_references.py::test_name_findings_follow_todays_findings_and_leave_the_exit_status`, expect `[today, "Report (not checked yet):"]` before the findings.
    3. This one is the tester's own test, which entry 11 covers with "a test that needs the list writes its own under tmp_path". `tests/entry/test_check_documents_checked_files.py::test_todays_documents_with_the_first_list_give_a_report_and_pass` fails here with `FileNotFoundError: [Errno 2] No such file or directory: '/work/checkout/docs/checked-documents.txt'` at `tests/entry/test_check_documents_checked_files.py:136`. The test reads the real list, and the documenter only writes that file in the docs stage. Until then the command treats a missing list as an empty list, as built. The test needs to give the command its own list instead of the repository's. For example: build the list from `[STYLE, GLOSSARY]` and point the run at it, or copy the needed tree into `tmp_path`. If the tester sees no way to do this without a change to the code's interface, that is a question for the human.

    Main decision (from the previous round, unchanged): each new finding carries its document, and the list decides by document what blocks. Rejected: parsing the `doc:line:` prefix of the printed lines.

    Still open:
    - The refactor step is left for the next doing round, once all tests are green.
    - `docs/checked-documents.txt` and criterion 12 belong to the documenter.
14. factory: started tests as vm.
15. tester: I made the three test changes from the coder's entry 13. Changes 1 and 2 are the ones the human allowed in entry 11. Change 3 is to my own test, along the line entry 11 gave: "a test that needs the list writes its own under tmp_path". I changed no criterion's mapping. The full mapping is in entry 8; only the test for criterion 3 changed how it runs.

    Changed (earlier stories' tests, with the human's leave in entry 11):
    - `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file`: the line `Report (not checked yet):` is now also left out before the exact comparison, next to the lines ending in ` does not exist`. Nothing else in the module changed, and the test keeps its name and what it checks.
    - `tests/entry/test_check_documents_references.py::test_name_findings_follow_todays_findings_and_leave_the_exit_status`, row `one-today`: the lines before the findings must now be `[today, "Report (not checked yet):"]`. Nothing else in the module changed, and the test keeps its name and what it checks.

    Changed (my own test):
    - `tests/entry/test_check_documents_checked_files.py::test_todays_documents_with_the_first_list_give_a_report_and_pass` (criterion 3): it no longer reads the repository's `docs/checked-documents.txt`, which the documenter writes later.
      - It copies the repository's working tree into `tmp_path`. `.git`, `.venv` and the cache and report folders are left out (`_NOT_COPIED`).
      - It writes the first list (style page and glossary) into the copy and runs `main` on the copy. The name check still sees the real `src/` and `tests/`.
      - I dropped the assertion that the repository's list reads as exactly those two files. The test now supplies the list itself.
      - Its other assertions are unchanged: the report heading is there, the last line is the time line, and the exit status is 0.
      - Rejected: symlinks into the real checkout. The command's path check resolves a path and refuses targets outside the root.
      - Open: a document that names an untracked or ignored path from the left-out folders would pass on the real checkout but give a finding in the copy. Today's documents give none: the test passes.

    Files changed: the three test modules above. No file created.

    Run: `uv run pytest -q` over the three changed files passed with no failures. `make lint` is green. No module was left unimported: the code exists from the previous doing round (2b6135a73).

    `lint`: lint: green (0.2 s)
16. factory: started doing as vm.
17. coder: The tester's changes from entry 15 make the whole suite pass against the code from the first doing round (2b6135a73). I changed no behaviour this round, only did the refactor step. `make check` is green: test 104.2 s, coverage 99.22 %. The smoke test `uv run python -m factory.entry.check_documents | tail -1` prints `documents ok (0.3 s)`, run with no list file present.

    What I built (across both doing rounds):
    - `src/factory/shared/domain/documents.py`:
      - The name check reads three kinds of text more exactly. A backticked text that holds `$` is skipped as a whole. A pytest node id is read up to its `::`. A dotted `factory.` name ending in `.env`, `.service`, `.yml`, `.yaml`, `.json`, `.toml`, `.md` or `.txt` is a file name, not a module (`_is_module_name`).
      - New: `CHECKED_DOCUMENTS`, `read_checked_documents(text)`, `checked_list_findings(listed, documents)`, the models `GatedFinding` and `SplitFindings`, and `split_findings(findings, checked)`.
    - `src/factory/entry/check_documents.py`:
      - The blocking lines print first: today's findings, the list's own findings, and the name, settings and example findings in listed documents.
      - Then `Report (not checked yet):` with the other findings and the lines for examples not run. The heading is left out when there is nothing to report.
      - `documents ok (<s> s)` is printed only when nothing blocks; otherwise the exit status is 1.
      - A missing list file counts as an empty list (journal entry 11).

    Refactor: I renamed `NewFinding` to `GatedFinding`, because the name now says what the list decides about it, and rewrote its docstring to match. I renamed `_example_lines` to `_example_results`, because it now returns findings and not-run lines separately. No tests use either name. Nothing else needed changing.

    Main decision: each finding of the new checks carries its document as a field, and `split_findings` decides by document whether it blocks. Rejected: parsing the `doc:line:` prefix of the printed lines, which is fragile, and the settings findings carry no line number.

    Noticed, not touched:
    - `docs/checked-documents.txt` lies outside the coder's write paths. The documenter writes it in the docs stage, with the style page and the glossary (entry 11), together with criterion 12.
    - When I ran it in the first round, neither page had a blocking finding.
    - `_COMMENT_MARK` and `_FRAGMENT` are both `"#"`. I kept them separate on purpose because they mean different things.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
18. factory: started review as vm.
19. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (`src/factory/entry/check_documents.py`, `src/factory/shared/domain/documents.py`, one new test module and three changed ones) against the work item. Criteria 1 to 10 each have a test that checks what the criterion says. The limits the Interface states are tested on both sides: a file extension against `yml_reader`, a listed path that is a document against one that is not, `::` against no `::`, and `$` against no `$`. The architecture holds: the list and the split are pure in `shared.domain`, and the wiring is in `factory.entry`. I found no security issue: listed paths are only compared, never read. I ran `make duplicates` (6 new). None of the six is in code this diff wrote. Two are line-shift pairs that show up as both new and gone. `matches` (documents.py:768) and the `cost_records` fields come from earlier stories.

    Findings:
    1. criterion 11 added: it needs its test. `src/factory/entry/check_documents.py:_checked_documents` treats a missing `docs/checked-documents.txt` as an empty list (journal entry 11), and no criterion or test pins that. Fix: the tester adds one row in `tests/entry/test_check_documents_checked_files.py` that writes no list file and plants a name finding. The row expects the finding under the report heading, the `documents ok` line and status 0.
    2. criterion 12 added: it needs its test. `check_documents.py:main` puts the lines for examples not run at the end of the report (`reported = [*split.reported, *not_run]`), also for a listed file, and they never block (the human, entry 11). No test covers this: the tester's entry 8 says no test uses a skipped block. Fix: one parametrized test, with rows for listed and not listed, with a `console vm` block in a guide page. Each row expects the not-run line after the heading and status 0.
    3. Work item, criterion 14 (docs): since entry 11 the documenter has to write `docs/checked-documents.txt` with the style page and the glossary. The docs criterion the documenter works from does not name that file, so the file criterion 3 and the Interface rely on may never be written. Fix: add to criterion 14 that `docs/checked-documents.txt` is written with `docs/project-guide/style.md` and `docs/project-guide/glossary.md` (Interface; journal entry 11).
    4. `tests/entry/test_check_documents_checked_files.py:27`: `REPOSITORY = Path(__file__).parents[2]` is another copy of `ROOT` from `tests/support/operator_support.py:10` (also in `shipped_agents.py`, `dockerfile_support.py` and `vm_support.py`). Fix: import `ROOT` from a support module instead of defining it again.

    Earlier tests:
    - `tests/entry/test_check_documents_operator_guide.py`: the human's leave, journal entry 11. The only change is that the heading line is also filtered out. The test keeps its name and what it checks.
    - `tests/entry/test_check_documents_references.py`: the human's leave, journal entry 11. Only the `one-today` row's expectation changed.
    - `tests/shared/domain/test_document_references.py`: no leave needed. Rows were only added to the parametrized test, which the story's Interface names ("rows for the three kinds in the name check's tests"), and every existing row is unchanged.
20. factory: started doing as vm.
21. coder: No code changed this round. All four review findings (entry 19) are about tests or the work item, so the work item goes to the tester.

    For the tester:
    1. Criterion 11 needs a test. In `tests/entry/test_check_documents_checked_files.py`, add one row that writes no `docs/checked-documents.txt` and plants a name finding. The row expects the finding under `Report (not checked yet):`, the `documents ok (<seconds> s)` line and exit status 0. The code already does this: `_checked_documents` in `src/factory/entry/check_documents.py` reads a missing list as an empty one.
    2. Criterion 12 needs a test. Add one parametrized test with two rows, listed and not listed, that each put a `console vm` block in a guide page. Each row expects the `<document>:<line>: not run (<kind>)` line after the report heading, after the reported findings, and exit status 0. The code already does this: `main` builds `reported = [*split.reported, *not_run]`.
    3. Finding 4, moving a shared test helper (the standing leave in `CLAUDE.md`). `tests/entry/test_check_documents_checked_files.py:27` sets `REPOSITORY = Path(__file__).parents[2]`, which copies `ROOT` from `tests/support/operator_support.py:10`. `tests/support/shipped_agents.py`, `tests/support/dockerfile_support.py` and `tests/support/vm_support.py` hold the same `ROOT`. The test module should import `ROOT` from `tests/support/operator_support.py` and drop its own constant.

    Work item: for finding 3, I rewrote criterion 14 (docs) in `## Description`. It now names `docs/checked-documents.txt`, written with `docs/project-guide/style.md` and `docs/project-guide/glossary.md`, so the documenter writes the first list that the Interface and criterion 3 rely on (journal entry 11). The Description has no "as of" heading to update. Criteria 11 and 12 were already in the Description.

    Main decision: I sent finding 3 into the Description instead of leaving it for the documenter to infer from the journal, because the documenter works from the docs criterion. I left the code alone: findings 1 and 2 add criteria that need only their tests, and the code already does what they describe.

    Noticed, not touched: four support modules each define the same `ROOT = Path(__file__).parents[2]`. Merging them is beyond this work item.

    I did not run `make check` this round, because no code changed. It was green at the end of the last doing round (entry 17).

    The factory left out changes outside the write paths: factory/features/F0053-the-documents-are-checked-against-the-code/in-progress/F0053-S0004-the-checks-block-the-listed-files-and-report-on-the-others.md.
22. factory: started tests as vm.
23. tester: I made the three test changes the coder listed in entry 21, which come from the review findings in entry 19. All of them are in `tests/entry/test_check_documents_checked_files.py`, a module this story wrote. I changed no earlier story's test file.

    What I did:
    - criterion 11: `tests/entry/test_check_documents_checked_files.py::test_without_a_list_file_every_new_finding_is_reported_and_none_blocks`. It has one row, `no-list-file`. No `docs/checked-documents.txt` is written and a missing module name is planted in the style page. The test expects the finding after `Report (not checked yet):`, the time line last and exit status 0.
    - criterion 12: `tests/entry/test_check_documents_checked_files.py::test_an_example_not_run_is_reported_after_the_reported_findings_and_never_blocks`. It has two rows, `listed` and `not-listed`, for the style page. The style page holds a `console vm` block and the glossary holds a name finding that is reported. The test expects this order: the heading, then the glossary finding, then `<style>:<line>: not run (vm)`. It also expects the time line last and exit status 0.
    - Finding 4, moving a shared test helper under the standing leave in `CLAUDE.md`: I dropped the module's `REPOSITORY = Path(__file__).parents[2]`. The copy test for criterion 3 now uses `ROOT` from `tests/support/operator_support.py`. The test keeps its name and checks the same thing.
    - I changed `_write` so that `listed=None` writes no list file. The tests that already used it work as before.

    The mapping of criteria 1 to 10 is unchanged from entries 8 and 15.

    Files: I changed `tests/entry/test_check_documents_checked_files.py` and created no file.

    Run: `uv run pytest -q tests/entry/test_check_documents_checked_files.py` passed with no failures. The new tests pass against the existing code (2b6135a73), as entry 21 expected: criteria 11 and 12 pin behaviour that is already there. No module was left unimported. `make lint` is green.

    Open: the factory dropped the coder's rewrite of criterion 14 from entry 21, because it was outside the coder's write paths. The `## Description` still does not name `docs/checked-documents.txt` (review finding 3). I did not edit the work item's Description, since that is not the tester's job. Whoever owns the Description has to add it, or the documenter may never write the list file that criterion 3 relies on.

    `lint`: lint: green (0.1 s)
24. factory: started doing as vm.
