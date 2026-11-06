---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 589
comments_read: [6681611113]
handed_over: null
claim: null
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
11. `make check` stays green.
12. docs: `docs/project-guide/shared.md`: the checked files and the report. `docs/project-guide/style.md`, rule 8: a path of another repository, such as the project the factory runs on, starts with a placeholder (`<project>/factory/agents/`), and a path in the repository is written from its root (`tests/support/time_limits.py`, not `support/time_limits.py`), so that the name check reads it right. `docs/decisions.md`: an entry for feature decisions 1 to 4, naming F0053.

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
