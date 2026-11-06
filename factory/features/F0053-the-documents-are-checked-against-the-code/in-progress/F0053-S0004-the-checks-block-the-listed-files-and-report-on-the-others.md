---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-06T09:23:35.963315Z'
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
