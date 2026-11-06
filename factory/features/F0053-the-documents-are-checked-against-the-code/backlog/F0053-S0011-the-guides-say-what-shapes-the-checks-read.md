# The guides say what shapes the checks read
<!-- proposed by feature acceptance of 2026-11-06; refine before starting -->

## Description

The rewrite feature will write the operator guide by `docs/project-guide/style.md`, but the style page does not say which shapes the settings check reads. It says that settings are tables with four columns, "name, what it does, default, example". The check compares defaults only under a header cell spelled exactly `Default`, counts a table only when its first column is `Name` or `Variable`, reads only `docs/operator-guide/install.md`, *Configuration*, and checks a refusal only in a table under the heading `The refusals` whose first column is `Refusal`. Those rules are written only in `docs/project-guide/shared.md`, *The settings check*, the machinery's page. A writer who follows the style page can write a table that the check silently skips. In addition, `README.md` describes `factory.entry.check_documents` by the checks it made before this feature. It says the documents "exist, say what v1.1 does in its own words, and name every stop", and does not name the name check, the settings check, `docs/checked-documents.txt` or the report. This story is a documents-only repair. No code changes.

## Interface

- Documents only: `docs/project-guide/style.md` and `README.md`. No module under `src/` changes.

## Acceptance criteria

1. `docs/project-guide/style.md`, the operator guide's rules: the settings rule names the header cells the settings check reads (`Name` first, `Default`), where the check reads the tables (`docs/operator-guide/install.md`, *Configuration*), and how a refusal is written so that it is checked (a table under `The refusals` whose first column is `Refusal`, the text in backticks, a `<placeholder>` for what varies). Each fact agrees with `factory.shared.domain.documents` (`_SETTINGS_FIRST_COLUMNS`, `_DEFAULT_COLUMN`, `REFUSALS_HEADING`, `_REFUSAL_FIRST_COLUMN`, `SETTINGS_SECTION`).
2. `README.md`'s sentence on `factory.entry.check_documents` names the name, settings and example checks, the checked files in `docs/checked-documents.txt`, and the report printed under `Report (not checked yet):`.
3. `make documents` ends with `documents ok (<seconds> s)`, and the style page, which is listed, gives no finding.
4. `make check` stays green.
5. docs: `docs/project-guide/style.md`: a writer of the operator guide knows the table shapes the settings check compares. `README.md`: a newcomer knows what the document check checks and that it blocks only listed files. `docs/operator-guide/`: none.

## Smoke test

```bash
grep -c "The refusals" docs/project-guide/style.md
```
Expect: a number greater than `0`

```bash
grep -c "checked-documents.txt" README.md
```
Expect: a number greater than `0`

## Journal
