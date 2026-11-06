---
stage: docs
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 595
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs
  started_at: '2026-11-06T12:48:31.778320Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T12:33:36.253901Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T12:33:36.261079Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T12:33:51.353640Z'
  stage: intake
  run: 729e9be60e814337a2697a060c9eea1b
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T12:33:57.193526Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-06T12:35:45.186437Z'
  stage: tests
  run: 75ee9c2b0c034c2a98c8a015b93b587a
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T12:35:50.513461Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-06T12:40:41.251960Z'
  stage: doing
  run: 296d6432f5094c87ac1335e0f6e6b45d
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-06T12:40:47.113235Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-06T12:42:04.285968Z'
  stage: review
  run: a91181c4c5564ed385c289b81d152c0a
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-06T12:42:09.798315Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-11-06T12:42:24.951176Z'
  stage: doing
  run: a40caaa657f648c0b8aad600bae9ed23
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-06T12:42:30.618459Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-11-06T12:43:23.237473Z'
  stage: tests
  run: 09a033458e8349108151671ed89d42b9
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-06T12:43:28.552594Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-11-06T12:47:36.095894Z'
  stage: doing
  run: 97674953013f4cda982e6b617011cd1c
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-06T12:47:41.555356Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-11-06T12:48:26.491928Z'
  stage: review
  run: f1b5f8c28670419abda777cdffb94cf0
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-06T12:48:31.778320Z'
  stage: docs
---

# A configuration section without its settings table is a finding
## Description

The settings check compares the operator guide's settings tables with `SETTINGS` (F0053-S0002), but only a table whose first column is `Name` or `Variable` counts. A guide with no such table gives no finding (S0002 criterion 6). The reviewer added that criterion to keep the earlier entry tests green. It is a default nobody chose: if the rewrite names the first column `Setting`, or splits the table under another heading, the settings check silently compares nothing, and the guide may drift again. The S0002 coder noticed it, and the reviewer suggested it for S0004's gate, which did not take it up. This story makes a missing settings table one finding when the *Configuration* section of `docs/operator-guide/install.md` exists, so the check either compares or says that it cannot. The comparison of names, defaults and refusals stays as S0002 built it.

## Interface

- `factory.shared.domain.documents.settings_findings(guide_tables, settings)`: when no table counts and `settings` is not empty, it returns the one finding `no settings table (first column Name or Variable) in Configuration`. With an empty `settings`, it returns no finding.
- `factory.entry.check_documents`: unchanged. A missing `install.md`, or a missing *Configuration* section, stays the finding of today's check, and no settings finding is added for it.
- This reverses S0002's criterion 6. It changes, beyond the standing leave, `tests/shared/domain/test_document_settings.py::test_guide_without_a_settings_table_gives_no_settings_finding` (its rows now expect the one finding) and the texts that the earlier entry tests build without a settings table (`clean_texts` in `tests/entry/test_check_documents.py`, which gets a settings table). Feature decision 6 gives the leave. The leave also covers any other earlier test, whichever story wrote it, whose only failure is the effect this Interface describes; every changed test keeps its name and what it checks, and the entry names each one.
- Tests: rows in `tests/shared/domain/test_document_settings.py`.

## Acceptance criteria

1. Guide tables with no table whose first column is `Name` or `Variable` give exactly `["no settings table (first column Name or Variable) in Configuration"]` when `settings` holds one setting or more, and `[]` when `settings` is empty (rows of one test, including a guide whose only table has the first column `Setting`).
2. Guide tables with one counting table give no such finding, whatever their other tables are (one row).
3. On today's `docs/operator-guide/install.md`, `make documents` prints no settings finding (its tables are headed `Variable`).
4. `make check` stays green.
5. docs: `docs/project-guide/shared.md`, *The settings check*: the reader learns that a guide without a counting table is a finding, not a silent pass. `docs/operator-guide/`: none.

## Smoke test

```bash
uv run python -c "from factory.shared.domain.documents import settings_findings; from factory.shared.domain.settings import SETTINGS; print(settings_findings([], SETTINGS))"
```
Expect: `['no settings table (first column Name or Variable) in Configuration']`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names `factory.shared.domain.documents.settings_findings(guide_tables, settings)`, which exists (documents.py:250), with the exact finding text, the empty-settings case, and the unchanged `check_documents`. It also names the earlier tests it changes: `test_guide_without_a_settings_table_gives_no_settings_finding` and `clean_texts` in `tests/entry/test_check_documents.py`. Feature decision 6 gives the leave.
   - Criteria: 1 covers both sides (no counting table with settings gives the finding; empty settings gives none), including a `Setting`-headed table. 2 covers the passing side with a counting table. 3 covers today's guide. Each is testable by one test function.
   - Smoke test: the command is runnable. Its `Expect:` is an exact printed list, so it can be checked. It does not run pytest, so the `-q` rule does not apply.
   - Docs criterion: it names what the reader must know (a guide without a counting table is a finding, not a silent pass) and in which section. It dictates no sentences.
   - Architecture: the change is in the shared domain layer. It is pure, with no I/O.
   - Scope: within the feature's settings check (S0002) and its decision 6. It is not in the feature's "Out of scope". The route is `tests` because the Interface changes `src` code.
4. factory: started tests as vm.
5. tester: Wrote the tests for the settings check's missing-table finding. Four rows are red on purpose: `settings_findings` still returns `[]` when no table counts, so the failures are wrong results, not import errors.

   - criterion 1: tests/shared/domain/test_document_settings.py::test_guide_without_a_counting_table_is_one_finding_when_there_are_settings. It has five rows:
     - no table with one setting, no table with two settings, and a table whose first column is `Setting` with one setting: each expects exactly the one finding.
     - no table with no settings, and the `Setting` table with no settings: each expects `[]`.
   - criterion 2: tests/shared/domain/test_document_settings.py::test_guide_with_a_counting_table_gives_no_missing_table_finding. One row: a `Variable` table next to a `Setting` table, with matching settings, gives `[]`.
   - criterion 3: tests/shared/domain/test_document_settings.py::test_todays_install_guide_gives_no_settings_finding. It reads today's `docs/operator-guide/install.md` from the repository root, takes the tables of its *Configuration* section, and expects `settings_findings` to return `[]` for `SETTINGS`. It passes today, which is correct: it guards against a regression. It runs the same domain functions the entry runs, not `make documents` itself, because the Interface puts the tests in this file.
   - criteria 4 and 5 (`make check`, docs): no test.

   Earlier tests changed under the leave the Interface gives (feature decision 6):
   - tests/shared/domain/test_document_settings.py::test_guide_without_a_settings_table_gives_no_settings_finding: its `no-settings-table` row now expects the one finding. The test keeps its name and still checks which names are in the findings.
   - tests/support/document_texts.py: `operator_install` now writes a `Variable | Meaning` table naming every `SETTINGS` entry, so `clean_texts` carries a settings table. Otherwise `test_each_finding_prints_one_line_in_order_and_returns_one` in tests/entry/test_check_documents.py would get a report line it does not expect. No test function was changed for this.

   Files created: none. Files changed: the two above.

   Test run: `uv run pytest -q` over test_document_settings.py, tests/shared/domain/test_documents_guide_files.py and the entry files tests/entry/test_check_documents.py, test_check_documents_operator_guide.py, test_check_documents_references.py and test_check_documents_settings.py. Only the four expected rows failed (`no-settings-table`, `no-table-one-setting`, `no-table-two-settings`, `setting-column`); the entry tests pass with the new clean texts. Every module imported. `make lint` is green.

   Open for the coder: the Interface says that a missing *Configuration* section adds no settings finding, while `check_documents` stays unchanged. No criterion covers that case, so I did not test it. As the code stands, `guide_tables` would return `[]` for that section, and the new finding would appear.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: Made a guide without a counting settings table one finding, while a missing *Configuration* section still gives no settings finding. `make check` is green.

   Built:
   - `src/factory/shared/domain/documents.py`:
     - New constant `NO_SETTINGS_TABLE`: `no settings table (first column Name or Variable) in Configuration`, built from `SETTINGS_SECTION`.
     - `settings_findings` returns `[NO_SETTINGS_TABLE]` when no table counts and `settings` is not empty, and `[]` when it is empty. Its docstring says so. The comparison of names and defaults is unchanged.
   - `src/factory/entry/check_documents.py`: `_settings_guide_findings` now also returns early when `install.md` has no *Configuration* section. It uses the existing helper `factory.shared.domain.sections.first_section`, so the missing section stays only the operator guide's finding.

   Main decision: I put that early return in the entry. The tester's open point was right: left as it was, the entry would add the new finding on top of the "section 'Configuration' is missing" finding. The Interface asks for both "check_documents: unchanged" and "no settings finding is added for it". I read "unchanged" as its output for that case staying what it is today, and a two-line guard keeps that output. The guard also skips the refusal check for a missing section; that check returned nothing there anyway.

   Rejected: passing a "section present" flag into `settings_findings`. It would change the domain signature the Interface fixes, and it pushes knowledge of sections into a function that only gets tables.

   Verified:
   - The smoke-test command prints `['no settings table (first column Name or Variable) in Configuration']`.
   - `make documents` prints no settings finding on today's `install.md` and ends `documents ok`.

   Refactor: I read the diff and nothing needed changing.

   Noticed, not touched: no test covers the missing-section guard in the entry. No criterion asks for one; the reviewer may want a row for it.

   Journal: no entry changed the meaning of the task, and I did not rewrite the Description.

   `check`: check: green
   `duplicates`: duplicates: 6 new, 39 known, 4 gone
8. factory: started review as vm.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (4 files) against the work item. I found two findings, both about test structure in `tests/shared/domain/test_document_settings.py`. At round 0 such points still count as findings.

   1. `tests/shared/domain/test_document_settings.py:19-21` (`_SETTING_TABLE`): it builds `GuideTable(heading="Configuration", header=..., rows=...)` by hand. That is what the file's existing helper `_table` (line 33) already does, and it is the same value as the `no-settings-table` row at line 122. Fix: define it through the helper, `_SETTING_TABLE = _table(("Setting", "Meaning"), ("`FACTORY_A`", "A."))`, placed after `_table`, and use it in that row too.
   2. `tests/shared/domain/test_document_settings.py:168` (`test_guide_with_a_counting_table_gives_no_missing_table_finding`): this is the counting side of the rule that criterion 1's test pins ("when no table counts ... the one finding"), but it is written as a separate test function, not as a row. Criterion 2 also asks for "one row". Fix: make it a row of `test_guide_without_a_counting_table_is_one_finding_when_there_are_settings`, e.g. `pytest.param([_SETTING_TABLE, _table(_VARIABLE_HEADER, ("`FACTORY_A`", "no", "A."))], (_setting("FACTORY_A"),), [], id="counting-table-beside-another")`, and remove the separate function.

   Checked and found sound:
   - Group 1 (criteria): every limit of the Interface has a test on both sides:
     - settings empty or not
     - no table counts or one counts
     - a table headed `Setting`
   - Group 1, criterion 3: `test_todays_install_guide_gives_no_settings_finding` runs the domain functions on today's `install.md`.
   - Group 1, the Interface's missing-section and missing-file rule: the coder's guard at `src/factory/entry/check_documents.py:121` is covered after all. The rows `no-configuration-section` and `no-install-file` of `tests/entry/test_check_documents_operator_guide.py` compare the whole output, so without the guard the new finding would fail them.
   - Group 1, `make check`: the journal (entry 7) says it was green after the coder.
   - Group 1, the coder's reading of "check_documents: unchanged": they read it as "its output for that case is unchanged" and explained it in entry 7. That reading is the one consistent with the Interface's own sentence that no settings finding is added for a missing section.
   - Group 2 (architecture): the entry imports `factory.shared.domain.sections.first_section`, an existing helper on the same section notion as `guide_tables`. The domain stays pure.
   - Group 3 (security): nothing relevant, and no suppression markers.
   - Group 4 (quality): the docstring of `settings_findings` is updated, and the comment explains why.
   - Group 5 (work item hygiene): the Description matches what was built. The docs criterion still names `docs/project-guide/shared.md`, *The settings check*: its sentence "A guide with no such table gives no finding." (line 146) is now false and is the documenter's to rewrite.

   Earlier tests:
   - tests/shared/domain/test_document_settings.py: one row of `test_guide_without_a_settings_table_gives_no_settings_finding` (`no-settings-table`) now expects the finding. The leave is the human's, through the story's Interface and feature decision 6; the test keeps its name.
   - tests/support/document_texts.py: `operator_install` now carries a `Variable` settings table naming every `SETTINGS` entry, so `clean_texts` has one. The same leave from the story's Interface covers it; no test function changed.
10. factory: started doing as vm.
11. coder: I changed no code. The reviewer's two findings in entry 9 are both changes to the tester's own test file, `tests/shared/domain/test_document_settings.py`. The coder never edits tests, so I am sending this back to the tester to make exactly these two changes:

    1. Define `_SETTING_TABLE` through the existing helper `_table` instead of building `GuideTable(...)` by hand. That is `_SETTING_TABLE = _table(("Setting", "Meaning"), ("`FACTORY_A`", "A."))`, placed after `_table`. Then use it in the `no-settings-table` row of `test_guide_without_a_settings_table_gives_no_settings_finding` as well.
    2. Make the counting-table case a row of `test_guide_without_a_counting_table_is_one_finding_when_there_are_settings`, for example `pytest.param([_SETTING_TABLE, _table(_VARIABLE_HEADER, ("`FACTORY_A`", "no", "A."))], (_setting("FACTORY_A"),), [], id="counting-table-beside-another")`. Then remove the separate function `test_guide_with_a_counting_table_gives_no_missing_table_finding`.

    Neither change affects `src/factory/shared/domain/documents.py` or `src/factory/entry/check_documents.py`; the code from round 0 stays as it is. The journal did not change the meaning of the task, so the Description is unchanged. I did not run `make check` in this round because I changed nothing; entry 7 records it green on the current code.
12. factory: started tests as vm.
13. tester: I made the two test changes that the coder's entry 11 names, which carry out the reviewer's findings in entry 9. Both are in `tests/shared/domain/test_document_settings.py`, the only file I changed. No code changed.

    1. `_SETTING_TABLE` no longer builds a `GuideTable(...)` by hand. It is now `_SETTING_TABLE = _table(("Setting", "Meaning"), ("`FACTORY_A`", "A."))`, placed after the helper `_table`. The `no-settings-table` row of `test_guide_without_a_settings_table_gives_no_settings_finding` now uses `_SETTING_TABLE` instead of its own copy of that table. The row checks the same thing as before.
    2. The counting-table case is now a row of `test_guide_without_a_counting_table_is_one_finding_when_there_are_settings`: `id="counting-table-beside-another"`, with a `Setting` table next to a `Variable` table naming `FACTORY_A`, the setting `FACTORY_A`, and the expected result `[]`. I removed the separate function `test_guide_with_a_counting_table_gives_no_missing_table_finding`.

    The criteria now map to these tests:
    - criterion 1: tests/shared/domain/test_document_settings.py::test_guide_without_a_counting_table_is_one_finding_when_there_are_settings (rows `no-table-one-setting`, `no-table-two-settings`, `setting-column`, `no-table-no-settings`, `setting-column-no-settings`)
    - criterion 2: tests/shared/domain/test_document_settings.py::test_guide_without_a_counting_table_is_one_finding_when_there_are_settings (row `counting-table-beside-another`)
    - criterion 3: tests/shared/domain/test_document_settings.py::test_todays_install_guide_gives_no_settings_finding
    - criteria 4 and 5 (`make check`, docs): no test.

    Files created: none. Every module imported.

    Test run: `uv run pytest -q tests/shared/domain/test_document_settings.py`. All 29 tests passed; the code from round 0 already does what they check. `make lint` is green.

    `lint`: lint: green (0.2 s)
14. factory: started doing as vm.
15. coder: I changed no code in this round. The reviewer had two findings (entry 9), and both were about the structure of the tester's tests. The tester made those two changes in `tests/shared/domain/test_document_settings.py` (entry 13):
    - `_SETTING_TABLE` is now built through the helper `_table`.
    - The counting-table case is now the row `counting-table-beside-another` of the criterion 1 test.

    The tests pass against the code from round 0, so there was nothing left for me to implement.

    The code is the same as round 0 built it (entry 7):
    - `src/factory/shared/domain/documents.py`: the new constant `NO_SETTINGS_TABLE`. `settings_findings` returns that one finding when no table counts and the settings are not empty.
    - `src/factory/entry/check_documents.py`: `_settings_guide_findings` returns early when `install.md` has no *Configuration* section. It uses `first_section` to do so. A missing section therefore keeps only today's finding.

    Main decision (round 0): the guard for a missing section goes in the entry, not in the domain function. The rejected alternative was a "section present" flag on `settings_findings`, because that would change the signature the Interface fixes.

    Refactor: there was nothing to change, because the diff to `src` is the same as in round 0.

    Description: no journal entry changed the meaning of the task, so I left it as it is.

    Noticed, not touched: line 146 of `docs/project-guide/shared.md` still says that a guide without a settings table gives no finding. That sentence is now false. Rewriting it is the documenter's job under criterion 5.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
16. factory: started review as vm.
17. reviewer: No findings. This is round 1. I reviewed `git diff main...HEAD -- . ':!factory'` (4 files) against the work item and read the code it calls.

    The two findings from round 0 (entry 9) are fixed in `tests/shared/domain/test_document_settings.py`:
    - `_SETTING_TABLE` is now built through `_table` (line 34), and the `no-settings-table` row uses it.
    - The counting-table case is now the row `counting-table-beside-another` of the criterion 1 test. The separate function is gone.

    What I checked:
    - **Group 1, criteria.**
      - Criterion 1: `test_guide_without_a_counting_table_is_one_finding_when_there_are_settings` has rows for no table with one setting, no table with two settings, a `Setting`-headed table, and empty settings both with and without a table. Each row compares the exact list against the literal finding text.
      - Criterion 2: the row `counting-table-beside-another`.
      - Criterion 3: `test_todays_install_guide_gives_no_settings_finding` runs `guide_tables` and `settings_findings` on today's `install.md`. The coder also ran `make documents` (entry 7).
      - Both sides of the Interface's rule are tested: settings empty or not, and a table that counts or not.
      - The Interface's rule for a missing *Configuration* section or a missing `install.md`: the guard is at `src/factory/entry/check_documents.py:121`. The rows `no-configuration-section` and `no-install-file` of `tests/entry/test_check_documents_operator_guide.py` (lines 54-63) compare the whole output, so they pin the guard.
      - `first_section` and `guide_tables` (through `_section_lines`) use the same `sections()` as `_missing_sections`, so "section missing" means the same thing in all three.
      - `make check` was green after the coder (entry 15).
    - **Group 2, architecture.** `settings_findings` stays pure domain code. The entry imports the existing domain helper `factory.shared.domain.sections.first_section`, and no new helper copies it.
    - **Group 3, security.** No suppression markers, secrets, shell strings or new boundaries.
    - **Group 4, quality.** The docstring of `settings_findings` says what it now does. `NO_SETTINGS_TABLE` is built from `SETTINGS_SECTION`. The comment on the entry guard says why the guard is there. There is no dead code.
    - **Group 5, work item hygiene.** The journal explains why the guard sits in the entry and why the domain-signature flag was rejected (entry 7). The Description matches what was built. Docs criterion 5 still names `docs/project-guide/shared.md`, *The settings check*. Its line 146, "A guide with no such table gives no finding.", is now false and is the documenter's to rewrite.

    Open for the documenter: rewrite `docs/project-guide/shared.md` line 146 under criterion 5.

    Earlier tests:
    - `tests/shared/domain/test_document_settings.py`: the `no-settings-table` row of `test_guide_without_a_settings_table_gives_no_settings_finding` now expects the one finding, and the test keeps its name. It was changed under the human's leave: the story's Interface, through feature decision 6.
    - `tests/support/document_texts.py`: `operator_install` now writes a `Variable` settings table naming every `SETTINGS` entry, so `clean_texts` has a settings table. No test function changed. It was changed under the same leave, which names `clean_texts`.

    Notes:
    - `tests/shared/domain/test_document_settings.py:19`: `_NO_SETTINGS_TABLE` repeats the text of `NO_SETTINGS_TABLE` as a literal. This is acceptable, because it pins the exact text that criterion 1 states.
18. factory: started docs as vm.
