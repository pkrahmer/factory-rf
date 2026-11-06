---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 597
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-06T13:12:48.989697Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T13:09:43.717251Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T13:09:43.724652Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T13:10:02.971236Z'
  stage: intake
  run: 06d5f702d1f54155bde6f14630985d05
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T13:10:07.953319Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-06T13:12:43.284873Z'
  stage: docs-only
  run: cc7b78e5c8824540bb043504053f901c
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T13:12:48.989697Z'
  stage: docs-review
---

# The guides say what shapes the checks read
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

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names only `docs/project-guide/style.md` and `README.md`, both paths the documenter may write; no module under `src/` changes, so the route is docs-only.
   - Criteria: criterion 1 names the facts to check against the code (header cells `Name` and `Default`, the install.md *Configuration* section, `The refusals` with first column `Refusal`, backticked text, `<placeholder>`). I confirmed `_SETTINGS_FIRST_COLUMNS` (`Name`, `Variable`), `_DEFAULT_COLUMN` and `_REFUSAL_FIRST_COLUMN` in `src/factory/shared/domain/documents.py`. Criterion 2 is checkable by reading `README.md`, and `Report (not checked yet):` matches `_REPORT_HEADING` in `src/factory/entry/check_documents.py`. Criteria 3 and 4 are commands. No Interface behaviour or rule lacks a criterion, because the Interface states none beyond the file list.
   - Smoke test: both commands are `grep -c` runs with checkable expectations (a number greater than 0). No pytest command is involved.
   - Docs criterion: it names what each reader must know (the table shapes the settings check compares; what the document check checks and that it blocks only listed files) and dictates no sentences. The operator guide is explicitly left unchanged.
   - Architecture: documents only, so nothing is placed in code. The project guide and README are written by the documenter.
   - Scope: it fits feature F0053 (the documents are checked against the code). It rewrites no operator-guide content and changes no checks, so it stays out of "Out of scope". It is not listed in the feature's Stories section, which names S0001 to S0007. I did not treat that as blocking, since it was started from `backlog/` by the human.
4. factory: started docs-only as vm.
5. documenter: Files changed:
   - `docs/project-guide/style.md` (operator guide section): the settings bullet now names the four header cells (`Name`, `What it does`, `Default`, `Example`). It says the settings check reads only the tables in *Configuration* of `docs/operator-guide/install.md`. A table counts only when its first header cell is `Name` (`Variable` also counts). Defaults are compared only under a header cell spelled exactly `Default`, with `none` or an empty cell for no default. A new bullet says how to write a refusal so it is checked: a table under the heading `The refusals`, first header cell `Refusal`, the message in backticks, a `<placeholder>` for what varies, and each piece of three or more characters must occur in the settings source. I read each fact in `src/factory/shared/domain/documents.py` (`SETTINGS_SECTION`, `_SETTINGS_FIRST_COLUMNS`, `_DEFAULT_COLUMN`, `_NO_DEFAULT_CELLS`, `REFUSALS_HEADING`, `_REFUSAL_FIRST_COLUMN`, `_SHORTEST_CHECKED_PIECE`) and in *The settings check* in `docs/project-guide/shared.md`. I did not read the checking code beyond those constants.
   - `README.md`: the `factory.entry.check_documents` sentence now names the name check, the settings check and the example check. It also says a finding blocks only in a file listed in `docs/checked-documents.txt`, that other files' findings are printed under `Report (not checked yet):`, and that it ends with `documents ok (<seconds> s)`.

   Checks: I ran `make documents`; it ends `documents ok (0.6 s)`. Its output has no finding for `docs/project-guide/style.md`. I did not run `make check`, since only documents changed. I added no example. The `console` blocks in `style.md` are unchanged.

   Cross-read and found current: `docs/project-guide/shared.md` (*The settings check*) agrees with the new style text; I read no other document.

   Stale text I noticed and did not touch: `make documents` prints report lines (not blocking) for files outside `docs/checked-documents.txt`. These include `README.md:24` (`factory/stage.Containerfile`) and many `docs/project-guide/README.md` lines (`support/*_support.py` paths, `factory.adapters.landlock`). They do not belong to this story.

   No "Rejected" line was written; this story changes no `docs/decisions.md` entry.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (0.6 s)
6. factory: started docs-review as vm.
