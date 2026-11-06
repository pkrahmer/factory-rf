---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 589
comments_read: [6681611113]
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-06T09:25:58.540243Z'
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
5. `make check` stays green.
6. docs: `docs/project-guide/shared.md`: the checked files and the report. `docs/project-guide/style.md`, rule 8: a path of another repository, such as the project the factory runs on, starts with a placeholder (`<project>/factory/agents/`), and a path in the repository is written from its root (`tests/support/time_limits.py`, not `support/time_limits.py`), so that the name check reads it right. `docs/decisions.md`: an entry for feature decisions 1 to 4, naming F0053.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok`

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
