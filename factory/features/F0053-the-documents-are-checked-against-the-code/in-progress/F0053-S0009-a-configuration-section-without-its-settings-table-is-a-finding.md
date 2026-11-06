---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 595
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-06T12:40:47.113235Z'
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
