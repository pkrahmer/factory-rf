# The four documents

## Assignment (as of log entry 1)

Make the four documents (`README.md`, `docs/operator-guide.md`, `docs/project-guide.md`, `docs/decisions.md`) a checked part of the project: they exist, they say what v1.1 does in the glossary's names, and none describes a behaviour that v1.1's items replaced. The coder builds the check, a pure function over the documents' texts and a command that runs it on the repository (`python -m factory.entry.check_documents`, which prints `documents ok` or one finding per line); the documenter then writes or completes the four documents so that the check passes, from the docs criteria of all earlier stories, and the smoke test runs the command on the real files. The check requires the operator guide's sections *Install*, *Configuration* and *The stops* with one table row for every row of `STOP_TABLE` (F0011-S0004), and the project guide's sections *Kill points* and *Fault-injection paths* with one table row for every case of `KILL_POINT_CASES` (F0011-S0001) and every path of `FAULT_PATHS` (F0011-S0002 and F0011-S0003). The check flags any occurrence of a replaced phrase or a v1 word, not only a description of a replaced behaviour, so one named section, `## Replaced from v1`, is exempt from both lists in every document: the statements that other stories' docs criteria require (no `--follow` mode, the leftover files of v1, this repository's own v1 tree) belong there. It covers WE6.1, WE6.2, WE6.4, WE6.5 and R17 and keeps kept thing 21 (the decision log). WE6.3 (every story's docs criterion names its documents) is not built here: it is checked across the stories by the cross-feature check and traced there as an observation, not by a test. No console script is added, because `pyproject.toml` is outside the coder's write paths; the command runs with `python -m`. The check is not wired into `make check` for the same reason, which `docs/decisions.md` records.

## Interface

`src/factory/domain/documents.py`

```python
from collections.abc import Mapping
from typing import Final

from pydantic import BaseModel, ConfigDict

README: Final = "README.md"
OPERATOR_GUIDE: Final = "docs/operator-guide.md"
PROJECT_GUIDE: Final = "docs/project-guide.md"
DECISION_LOG: Final = "docs/decisions.md"
DOCUMENT_PATHS: Final = (README, OPERATOR_GUIDE, PROJECT_GUIDE, DECISION_LOG)
OPERATOR_GUIDE_SECTIONS: Final = ("Install", "Configuration", "The stops")
PROJECT_GUIDE_SECTIONS: Final = ("Kill points", "Fault-injection paths")
REPLACED_SECTION: Final = "Replaced from v1"
REPLACED_PHRASES: Final = (
    "--follow", "factory-last-line", "tasks/.gitkeep", "factory-tick.lock",
    "factory-run.json", "recover_dirty_tree", "lease plus ten minutes",
    "local branch first", "run record",
)
GLOSSARY_FORBIDDEN: Final = (
    "ticket", "tickets", "lane", "lanes", "stage table", "stages.yml", "promote", "promoted",
    "acceptor", "demonstration", "control surface", "hardening", "memo", "lease_minutes",
    "max_attempts", "max_rounds", "drafts/", "ongoing/",
)


class DocumentFinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    document: str
    message: str


def check_documents(texts: Mapping[str, str | None]) -> list[DocumentFinding]: ...
```

`src/factory/entry/check_documents.py`

```python
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int: ...
```

`check_documents` judges the four documents of `DOCUMENT_PATHS`; a key that is absent from `texts` counts like a value of `None`. It returns the findings of the documents in the order of `DOCUMENT_PATHS`, and within a document in the order of these rules (sections, then table rows, then phrases, then words). A document that is missing or blank gets one finding and no other rule is applied to it. A "code fence" is a fenced block as `factory.domain.sections.code_blocks` finds it; a "heading line" `## <text>` and a "table row" are lines outside code fences.

- Missing (the value is `None` or the key is absent): the message is `missing`.
- Blank (only whitespace): the message is `empty`.
- Operator guide: for each name in `OPERATOR_GUIDE_SECTIONS`, a heading line `## <name>` outside code fences is required (found with `factory.domain.sections.sections`, which skips code fences); the message is `section '<name>' is missing`.
- Operator guide: for each row of `STOP_TABLE`, a table row (a line outside code fences whose first character is `|`) that contains the row's id in backticks and the destination in words, in any letter case (`health status` for `health_status`, `pull request` for `pull_request`, `no stop` for `none`) is required; the message is `stop '<id>' has no table row with its destination`.
- Project guide: for each name in `PROJECT_GUIDE_SECTIONS` the same section rule, with the same message.
- Project guide: for each case of `KILL_POINT_CASES`, a table row that contains the case's id in backticks is required; the message is `kill point case '<id>' has no table row`.
- Project guide: for each path of `FAULT_PATHS`, a table row that contains the path's `test` in backticks is required; the message is `fault-injection path <number> has no table row naming '<test>'`.
- Decision log: at least one heading line `## <text>` is required; the message is `no decision recorded`.
- Every document except the decision log (which records what was replaced and renamed): the text that the next two rules read leaves out the exempt section, that is, the heading line `## Replaced from v1` (outside code fences) and every line after it up to the next heading line `## <text>` or the end of the text. Each phrase of `REPLACED_PHRASES` that occurs in that text, in any letter case, is a finding with the message `describes a replaced behaviour: '<phrase>'`. Each entry of `GLOSSARY_FORBIDDEN` that occurs in that text, in any letter case, is a finding with the message `uses the v1 word '<entry>'`; it counts as an occurrence only where the character directly before it is not a letter, digit, hyphen or underscore and, when the entry ends in a letter, the character directly after it is not one either (so `drafts/` is found in `drafts/F0001-x.md`, because it ends in a slash). Findings follow the order of the two tuples, phrases first.

The model `DocumentFinding` is closed: `frozen=True` refuses the assignment of a field and `extra="forbid"` refuses an unknown key, each with a `pydantic.ValidationError`.

`main` takes `--root <directory>` (default: the current directory), reads each path of `DOCUMENT_PATHS` under it as UTF-8 (a file that does not exist is `None`), prints each finding of `check_documents` as `<document>: <message>`, one per line, and returns 1; with no findings it prints `documents ok` and returns 0. The module ends with `if __name__ == "__main__": raise SystemExit(main())`.

Tests: `tests/domain/test_documents.py` (criteria 1 to 18); `tests/entry/test_check_documents.py` (criteria 19 to 23).

## Acceptance criteria

1. `check_documents` returns `[]` for four texts that are clean: the operator guide holds the three required sections and one table row for each row of `STOP_TABLE`, the project guide the two required sections and one table row for each case and each path, the decision log one `## ` section, and none holds a phrase of `REPLACED_PHRASES` or an entry of `GLOSSARY_FORBIDDEN` outside the section `## Replaced from v1`.
2. For each of the four documents, a value of `None` (and, separately, an absent key) gives exactly one finding for that document, with the message `missing`.
3. For each of the four documents, a text of only whitespace (and, separately, the empty string) gives exactly one finding for that document, with the message `empty`.
4. An operator guide without the heading `## Install`, `## Configuration` or `## The stops`, and a project guide without `## Kill points` or `## Fault-injection paths`, each give the finding `section '<name>' is missing` for the absent name only.
5. A required heading that occurs only inside a code fence does not count: the finding `section '<name>' is missing` is still given.
6. An operator guide without a table row for the stop `fetch-failed` gives the finding `stop 'fetch-failed' has no table row with its destination`, and only that one; so does an operator guide whose only row for `fetch-failed` stands inside a code fence, one whose only row for it names the id without backticks (`| fetch-failed | health status and factory log |`), and one whose only line naming `` `fetch-failed` `` and `health status` does not start with `|` (the prose line `` `fetch-failed` goes to the health status and the factory log. ``), and one whose only row for it is indented (``  | `fetch-failed` | health status and factory log |``).
7. A row with the stop's id in backticks but without its destination's words gives `stop '<id>' has no table row with its destination` for that id, for each destination: an operator guide whose only row for `fetch-failed` says `pull request` instead of `health status`, one whose only row for `duplicate` lacks `pull request`, and one whose only row for `later-stage-in-backlog-file` lacks `no stop` (three cases, one test); the same rows holding `Health Status`, `Pull Request` and `No Stop` give none.
8. A project guide without a table row holding `` `commit-push` ``, one whose only row for that case names `commit-push` without backticks, and one whose only line holding `` `commit-push` `` does not start with `|`, each give the finding `kill point case 'commit-push' has no table row`.
9. A project guide without a table row holding the test name of path 7 in backticks, one whose only row for path 7 names the test without backticks, and one whose only line holding that name in backticks does not start with `|`, each give the finding `fault-injection path 7 has no table row naming 'test_round_cap_question_killed_between_post_and_record_posts_once_and_waits'`.
10. Each phrase of `REPLACED_PHRASES`, placed in the README, the operator guide or the project guide, gives the finding `describes a replaced behaviour: '<phrase>'` for that document only; the phrase `factory-run.json` written as `Factory-Run.json` gives it too.
11. The entry `ticket` placed as a word in the operator guide gives the finding `uses the v1 word 'ticket'`, also written `TICKET` and also followed by a full stop; the entry `drafts/` in `drafts/F0001-x.md` gives the finding `uses the v1 word 'drafts/'`.
12. `ticketing`, `my-ticket`, `_ticket`, `ticket_1`, `ticket1`, `1ticket`, `xticket` and `ticket-x` each give no finding for `ticket` (the word must stand alone).
13. A phrase of `REPLACED_PHRASES` and an entry of `GLOSSARY_FORBIDDEN` that stand between the heading line `## Replaced from v1` and the next heading line `## <text>` (or the end of the text) of the README, the operator guide or the project guide give no finding, also when they stand after a `### <text>` line or after a `## <text>` line inside a code fence within that section.
14. The same phrase and the same entry give their findings when they stand before the heading `## Replaced from v1`, after the next heading line `## <text>`, or under a `## Replaced from v1` that occurs only inside a code fence.
15. The decision log holding a phrase of `REPLACED_PHRASES` and an entry of `GLOSSARY_FORBIDDEN` gives no finding for them.
16. A decision log without a line `## <text>`, and one whose only such line stands inside a code fence, each give the finding `no decision recorded`; one with such a line outside code fences gives none.
17. An otherwise clean operator guide that lacks `## Install` and the table row of `fetch-failed`, and holds outside the exempt section `lane` twice, then `ticket`, `factory-run.json` and `--follow`, in that order in its text, gives exactly these six findings, in this order: `section 'Install' is missing`, `stop 'fetch-failed' has no table row with its destination`, `describes a replaced behaviour: '--follow'`, `describes a replaced behaviour: 'factory-run.json'`, `uses the v1 word 'ticket'`, `uses the v1 word 'lane'`; and an otherwise clean project guide that lacks `## Kill points`, the table row of `commit-push` and the table row of path 7 gives exactly `section 'Kill points' is missing`, `kill point case 'commit-push' has no table row` and `fault-injection path 7 has no table row naming 'test_round_cap_question_killed_between_post_and_record_posts_once_and_waits'`, in this order.
18. A `DocumentFinding` is a closed model: assigning a field of a built one (`setattr` with the field name in a variable) and an unknown key are each rejected with `pydantic.ValidationError`, the second constructed through a variable typed `type[BaseModel]`.
19. `main(["--root", root])` on a directory holding four clean documents prints exactly `documents ok` and returns 0.
20. `main(["--root", root])` on a directory whose README is missing, whose operator guide lacks `## Install`, whose project guide lacks `## Kill points` and whose decision log is blank (all else clean) prints exactly `README.md: missing`, `docs/operator-guide.md: section 'Install' is missing`, `docs/project-guide.md: section 'Kill points' is missing` and `docs/decisions.md: empty`, in that order and nothing more, and returns 1; it does not print `documents ok`.
21. `main([])` reads the current directory: after `monkeypatch.chdir` into a directory with four clean documents it prints `documents ok` and returns 0.
22. `python -m factory.entry.check_documents --root <directory>` run as a subprocess exits with the status `main` returns (0 for clean documents, 1 for an empty directory) and writes the same lines to standard output (run through `run_process`, as `tests/entry/test_health.py` runs `factory.entry.health`).
23. `main(["--root", root])` on a directory whose four clean documents are written as UTF-8 bytes and whose README holds `café` and an em dash prints exactly `documents ok` and returns 0.
24. make check stays green.
25. docs: all four documents describe what v1.1 does, in the glossary's names, and `uv run python -m factory.entry.check_documents` prints `documents ok` (the documenter runs it and fixes the documents until it does): `README.md` says what the factory is, how to run it and where to look next, and links the other three; its list of commands names `uv run python -m factory.entry.check_documents` beside the six console commands (it is no console script); `docs/operator-guide.md` has *Install*, which says that v1.1 is installed only on a repository v1 has not worked in, or whose v1 work items are archived or discarded (decision 008), and that nothing detects a v1 work item, *Configuration* and *The stops* (the table of F0011-S0004, one row per stop); `docs/project-guide.md` has the layers and conventions of `CLAUDE.md` as an agent needs them, *Kill points* and *Fault-injection paths*; where a document must say what v1.1 does not do or no longer reads (no `--follow` mode, v1's leftover files, this repository's own v1 tree of `drafts/`, `ongoing/` and `TICKET.md`), the statement stands in a section `## Replaced from v1`; `docs/decisions.md` records the decisions of F0001 to F0011, and that this check is a command and not part of `make check`, that the decision log is exempt from its two word lists and every other document's section `## Replaced from v1` with it, and that WE6.3 is observed across the stories.

## Demo

```bash
uv run python -c "
from factory.domain.documents import check_documents
texts = {'README.md': 'x', 'docs/operator-guide.md': None, 'docs/project-guide.md': '  ', 'docs/decisions.md': 'x'}
for f in check_documents(texts):
    print(f.document, '-', f.message)
"
```
Expect: three lines, `docs/operator-guide.md - missing`, `docs/project-guide.md - empty`, `docs/decisions.md - no decision recorded`.

```bash
uv run python -m factory.entry.check_documents; echo "exit=$?"
```
Expect: the line `documents ok`, then the line `exit=0`.

```bash
uv run python -m factory.entry.check_documents --root /nonexistent; echo "exit=$?"
```
Expect: five lines, `README.md: missing`, `docs/operator-guide.md: missing`, `docs/project-guide.md: missing`, `docs/decisions.md: missing`, then `exit=1`.

## Log (append only)

1. 2026-10-12 human: created.
