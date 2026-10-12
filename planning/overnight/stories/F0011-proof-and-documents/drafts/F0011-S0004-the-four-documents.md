# The four documents

## Assignment (as of log entry 1)

Make the four documents (`README.md`, `docs/operator-guide.md`, `docs/project-guide.md`, `docs/decisions.md`) a checked part of the project: they exist, they say what v1.1 does in the glossary's names, and none describes a behaviour that v1.1's items replaced. The coder builds the check, a pure function over the documents' texts and a command that runs it on the repository (`python -m factory.entry.check_documents`, which prints `documents ok` or one finding per line); the documenter then writes or completes the four documents so that the check passes, from the docs criteria of all earlier stories, and the smoke test runs the command on the real files. The check requires the operator guide's sections *Install*, *Configuration* and *The stops* with one table row for every row of `STOP_TABLE` (F0011-S0003), and the project guide's sections *Kill points* and *Fault-injection paths* with one table row for every case of `KILL_POINT_CASES` (F0011-S0001) and every path of `FAULT_PATHS` (F0011-S0002). It covers WE6.1, WE6.2, WE6.4, WE6.5 and R17 and keeps kept thing 21 (the decision log). WE6.3 (every story's docs criterion names its documents) is not built here: it is checked across the stories by the cross-feature check and traced there as an observation, not by a test. No console script is added, because `pyproject.toml` is outside the coder's write paths; the command runs with `python -m`. The check is not wired into `make check` for the same reason, which `docs/decisions.md` records.

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
REPLACED_PHRASES: Final = (
    "--follow", "factory-last-line", "tasks/.gitkeep", "factory-tick.lock",
    "factory-run.json", "recover_dirty_tree", "lease plus ten minutes",
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

`check_documents` judges the four documents of `DOCUMENT_PATHS`; a key that is absent from `texts` counts like a value of `None`. It returns the findings of the documents in the order of `DOCUMENT_PATHS`, and within a document in the order of these rules. A document that is missing or blank gets one finding and no other rule is applied to it.

- Missing (the value is `None` or the key is absent): the message is `missing`.
- Blank (only whitespace): the message is `empty`.
- Operator guide: for each name in `OPERATOR_GUIDE_SECTIONS`, a heading line `## <name>` outside code fences is required (found with `factory.domain.sections.sections`, which skips code fences); the message is `section '<name>' is missing`.
- Operator guide: for each row of `STOP_TABLE`, a line that starts with `|` and contains the row's id in backticks and the destination in words, in any letter case (`health status` for `health_status`, `pull request` for `pull_request`, `no stop` for `none`) is required; the message is `stop '<id>' has no table row with its destination`.
- Project guide: for each name in `PROJECT_GUIDE_SECTIONS` the same section rule, with the same message.
- Project guide: for each case of `KILL_POINT_CASES`, a line that starts with `|` and contains the case's id in backticks is required; the message is `kill point case '<id>' has no table row`.
- Project guide: for each path of `FAULT_PATHS`, a line that starts with `|` and contains the path's `test` in backticks is required; the message is `fault-injection path <number> has no table row naming '<test>'`.
- Decision log: at least one line `## <text>` outside code fences is required; the message is `no decision recorded`.
- Every document except the decision log (which records what was replaced and renamed): each phrase of `REPLACED_PHRASES` that occurs in the text, in any letter case, is a finding with the message `describes a replaced behaviour: '<phrase>'`; each entry of `GLOSSARY_FORBIDDEN` that occurs as a whole word or phrase (not directly preceded or followed by a letter, digit, hyphen or underscore), in any letter case, is a finding with the message `uses the v1 word '<entry>'`. Findings follow the order of the two tuples, phrases first.

`main` takes `--root <directory>` (default: the current directory), reads each path of `DOCUMENT_PATHS` under it as UTF-8 (a file that does not exist is `None`), prints each finding of `check_documents` as `<document>: <message>`, one per line, and returns 1; with no findings it prints `documents ok` and returns 0. The module ends with `if __name__ == "__main__": raise SystemExit(main())`.

Tests: `tests/domain/test_documents.py` (criteria 1 to 13); `tests/entry/test_check_documents.py` (criteria 14 to 17).

## Acceptance criteria

1. `check_documents` returns `[]` for four texts that are clean: the operator guide holds the three required sections and one table row for each row of `STOP_TABLE`, the project guide the two required sections and one table row for each case and each path, the decision log one `## ` section, and none holds a phrase of `REPLACED_PHRASES` or an entry of `GLOSSARY_FORBIDDEN`.
2. For each of the four documents, a value of `None` (and, separately, an absent key) gives exactly one finding for that document, with the message `missing`.
3. A text of only whitespace gives exactly one finding for that document, with the message `empty`.
4. An operator guide without the heading `## Install`, `## Configuration` or `## The stops`, and a project guide without `## Kill points` or `## Fault-injection paths`, each give the finding `section '<name>' is missing` for the absent name only.
5. A required heading that occurs only inside a code fence does not count: the finding `section '<name>' is missing` is still given.
6. An operator guide without a table row for the stop `fetch-failed` gives the finding `stop 'fetch-failed' has no table row with its destination`, and only that one.
7. An operator guide whose only row for `duplicate` lacks the words `pull request` gives the finding `stop 'duplicate' has no table row with its destination`; the same row with `Pull Request` in it gives none.
8. A project guide without a table row holding `` `commit-push` `` gives the finding `kill point case 'commit-push' has no table row`.
9. A project guide without a table row holding the test name of path 7 in backticks gives the finding `fault-injection path 7 has no table row naming 'test_round_cap_question_killed_between_post_and_record_posts_once_and_waits'`.
10. Each phrase of `REPLACED_PHRASES`, placed in the README, the operator guide or the project guide, gives the finding `describes a replaced behaviour: '<phrase>'` for that document only.
11. The entry `ticket` placed as a word in the operator guide gives the finding `uses the v1 word 'ticket'`; `ticketing` and `my-ticket` give none (the word must stand alone).
12. The decision log holding a phrase of `REPLACED_PHRASES` and an entry of `GLOSSARY_FORBIDDEN` gives no finding for them.
13. A decision log without a line `## <text>` outside code fences gives the finding `no decision recorded`; one with such a line gives none.
14. `main(["--root", root])` on a directory holding four clean documents prints exactly `documents ok` and returns 0.
15. `main(["--root", root])` on a directory whose README is missing and whose decision log is blank prints `README.md: missing` and `docs/decisions.md: empty` and nothing more (the other two documents are clean), in that order, and returns 1; it does not print `documents ok`.
16. `main([])` reads the current directory: after `monkeypatch.chdir` into a directory with four clean documents it prints `documents ok` and returns 0.
17. `python -m factory.entry.check_documents --root <directory>` run as a subprocess exits with the status `main` returns (0 for clean documents, 1 for an empty directory) and writes the same lines to standard output.
18. make check stays green.
19. docs: all four documents describe what v1.1 does, in the glossary's names, and `uv run python -m factory.entry.check_documents` prints `documents ok` (the documenter runs it and fixes the documents until it does): `README.md` says what the factory is, how to run it and where to look next, and links the other three; `docs/operator-guide.md` has *Install*, *Configuration* and *The stops* (the table of F0011-S0003, one row per stop); `docs/project-guide.md` has the layers and conventions of `CLAUDE.md` as an agent needs them, *Kill points* and *Fault-injection paths*; `docs/decisions.md` records the decisions of F0001 to F0011, and that this check is a command and not part of `make check`, that the decision log is exempt from its two word lists, and that WE6.3 is observed across the stories.

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
