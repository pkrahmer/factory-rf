---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 595
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-06T12:33:57.193526Z'
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
