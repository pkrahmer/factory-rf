---
stage: done
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 597
comments_read: []
handed_over: docs-approval
claim: null
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
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-06T13:13:57.308534Z'
  stage: docs-review
  run: 335fc23c5b96453592f527268859e8f1
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-06T13:14:02.851082Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-06T13:16:38.676127Z'
  stage: docs-only
  run: 8392ae0e5a574b00b8568eefd3d5546d
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-06T13:16:44.178854Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-06T13:17:34.559167Z'
  stage: docs-review
  run: 5004f4a1358b49ff90fd8a00574fcb85
- number: 12
  speaker: factory
  kind: done
  at: '2026-11-06T13:18:24.457429Z'
  stage: docs-approval
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
7. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md` against `src/factory/shared/domain/documents.py` (`guide_tables`, `settings_findings`, `_default_findings`, `refusal_findings`, `_is_held`), `src/factory/entry/check_documents.py` (`main`, `_name_findings`, `_settings_guide_findings`), `docs/project-guide/shared.md` (*The name check*, *The checked documents and the report*, *The settings check*) and the rules in `docs/project-guide/style.md`. In the style page's settings bullet, these facts match the code: the `Name`/`Variable` first cell, the exact `Default` header, the `none` or empty cell for no default, the *Configuration* section of `install.md`, and the `no settings table` finding when no table counts. In the refusal bullet, the `The refusals` heading, the `Refusal` first cell, the backticked first cell, the `<placeholder>` cut and the three-character pieces all match the code. The README's descriptions of the settings check, the example check and `Report (not checked yet):` also match.

   Findings:
   1. `README.md:22`, "and name every stop, kill point and fault-injection path (the name check)": the code contradicts this label. The name check (`_name_findings`, which calls `named_references` and `unresolved`; shared.md *The name check*) reports every module, repository path or link a document writes that does not exist. Checking that the documents exist, use their own words and name every stop, kill point and fault-injection path is done by the document findings of `check_documents`. Fix: describe those as the document checks, and add a separate clause saying the name check finds names that do not exist.
   2. `README.md:22`, "A finding blocks only in a file listed in `docs/checked-documents.txt`": false. `check_documents.main` blocks on the document findings of every file and on `checked_list_findings`. `split_findings` gates only the findings of the name, settings and example checks (see its docstring and shared.md *The checked documents and the report*, step 1). Fix: say that only a finding of the name, settings or example check blocks just in a listed file, and that the document checks block in every file.
   3. `README.md:22`: breaks style.md rule 2 (one idea per sentence, about 25 words, at most one parenthesis). The rewritten "Beside the five console commands, …" sentence is well over 100 words, holds several ideas and has five parentheses, one of which contains a nested parenthesis. Fix: split it into short sentences: the contract command, then one sentence for each check, the blocking rule, the report and the closing line. While doing so, drop the version name "v1.1" (rule 1).
   4. `docs/project-guide/style.md:80` (refusal bullet): it does not say where the refusal table must sit. `_settings_guide_findings` passes the refusal check only `guide_tables(text, SETTINGS_SECTION)`, so a `The refusals` table counts only as a subsection of *Configuration* in `docs/operator-guide/install.md`. A writer who puts it under install.md's own `## When the process refuses to start` gets no finding at all, and criterion 1 asks for exactly this. Fix: say that the heading `The refusals` must be a subsection of *Configuration* in `docs/operator-guide/install.md`.
   5. `docs/project-guide/style.md:80`, "in the settings source": the term is not explained anywhere on the page (rule 3). The code reads `Path(settings.__file__)`, the source of `src/factory/shared/domain/settings.py`. Fix: name that file and link it relatively (rule 8).
   6. `docs/project-guide/style.md:79-80`: breaks style.md rule 2. Three sentences run to about 28–30 words with two ideas each: "The settings check reads only … (`Variable` also counts).", "It compares the defaults only … has no default." and "The check looks up each piece … is a finding." Fix: split each into two sentences.
8. factory: started docs-only as vm.
9. documenter: Round 1: I fixed the reviewer's six findings.

   Files changed:
   - `README.md`: I split the long `check_documents` sentence into short ones, which fixes findings 1 to 3. The contract command now has its own sentence. The document checks (missing document, not in its own words, unnamed stop, kill point or fault-injection path) are described apart from the name check. The name check finds a module, path or link that does not exist. The settings check and the example check each have a sentence. The text now says the document checks block in every file. Only a name, settings or example finding blocks just in a file listed in `docs/checked-documents.txt`; other files' findings are printed under `Report (not checked yet):`. The text ends with `documents ok (<seconds> s)`. I dropped the version name.
   - `docs/project-guide/style.md` (operator guide section): this fixes findings 4 to 6. The settings bullet is now two bullets of shorter sentences. The refusal rule is now two bullets of shorter sentences. It says the `The refusals` table must be a subsection of *Configuration* in `docs/operator-guide/install.md`. "The settings source" is now a relative link to `src/factory/shared/domain/settings.py`.

   Checks: I ran `make documents`; it ends with `documents ok (0.6 s)`. The style page has no finding. I ran no `make check`, since only documents changed. I wrote no new examples.

   Cross-read and found current: `docs/project-guide/shared.md` (*The settings check*), as in round 0. I did not recheck the code facts the reviewer confirmed.

   Stale text I saw and did not touch: report-only lines remain for `README.md:28` (`factory/stage.Containerfile`) and for `docs/project-guide/README.md`. They are outside this story.

   I wrote no "Rejected" line, because no `docs/decisions.md` entry changed.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (0.6 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1 docs-review. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md` (`README.md`, `docs/project-guide/style.md`). I checked every sentence against `src/factory/shared/domain/documents.py` and `src/factory/entry/check_documents.py`, then checked the writing against `docs/project-guide/style.md`.

    Facts checked in `docs/project-guide/style.md`, operator guide section, lines 79-82:
    - The header cells `Name` and `Variable` match `_SETTINGS_FIRST_COLUMNS`, and the exact `Default` matches `_DEFAULT_COLUMN` and `_default_findings`.
    - `none` or an empty cell means no default, as in `_NO_DEFAULT_CELLS`.
    - A table with another first header cell is skipped, and a finding comes only when no table counts. This matches `settings_findings` and `NO_SETTINGS_TABLE`.
    - The tables are read only in *Configuration* of `docs/operator-guide/install.md`, as `_settings_guide_findings` does with `OPERATOR_INSTALL` and `SETTINGS_SECTION`.
    - A refusal table needs the heading `The refusals` (`REFUSALS_HEADING`, the nearest heading in `guide_tables`), and the heading must sit inside *Configuration*, because `guide_tables` takes only that section. Its first header cell is `Refusal` (`_REFUSAL_FIRST_COLUMN`).
    - The message is in backticks (`_quoted_refusal`), and `<placeholder>` is cut out (`_PLACEHOLDER`). Pieces of three or more characters (`_SHORTEST_CHECKED_PIECE`) must occur in the source of `settings.py`, which is read through `Path(settings.__file__)`. The relative link `../../src/factory/shared/domain/settings.py` resolves to a file that exists.

    Facts checked in `README.md`, lines 22-26:
    - The contract command is described as before.
    - The document checks match `_messages`, `_missing_sections`, `_wording`, `_stop_rows` and `_project_guide_rows`.
    - The name check matches `_name_findings`, `named_references` and `unresolved`. The settings check matches `_settings_guide_findings`.
    - The example check covers the README and both guides (`_named_documents`).
    - The document checks block in every file. The name, settings and example findings block only in a file listed in `docs/checked-documents.txt`; findings in other files go under `Report (not checked yet):`. This matches `main` and `split_findings`.
    - The closing line `documents ok (<seconds> s)` matches `main`.

    The six findings of round 0 are fixed:
    - The name check is now described apart from the document checks.
    - The blocking rule is right.
    - The long sentence is split and the version name is gone from the changed text.
    - The refusal table is placed as a subsection of *Configuration*.
    - "The settings source" is now a link to `settings.py`.
    - The long sentences in style.md are split.

    The writing meets the style rules. Every sentence is under about 25 words and has at most one parenthesis. There are no version names or story ids, and the file link is relative. The new text adds no `console` example.

    Criteria 1, 2 and 5 are met. For criteria 3 and 4 I take the documenter's reported `documents ok (0.6 s)` and the factory's `check: green`.

    no findings
12. factory: done (pull request merged); cost: 5 runs, 3.3 min, 34 turns, 142994 tokens in (666524 more from cache), 16905 out, $1.26
