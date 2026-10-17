---
stage: done
pr: 149
blocked: null
comments_seen: 2
round: 0
attempts: 0
---
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
2. intake: accepted.
   - Interface: names `src/factory/domain/documents.py` and `src/factory/entry/check_documents.py` with typed signatures, the constants, the closed `DocumentFinding` model, and every rule's message and finding order. The helpers it names (`factory.domain.sections.sections` and `code_blocks`) exist. The ids it uses (`fetch-failed`, `duplicate`, `later-stage-in-backlog-file`, `commit-push`, and path 7's test name) match `STOP_TABLE`, `KILL_POINT_CASES` and `FAULT_PATHS` in the source.
   - Criteria: criteria 1 to 23 are each testable by one test function. Each rule has its failing side: missing, empty, absent section, code-fenced heading, absent row, unbackticked id, non-`|` line, indented row, the destination words, the exemption boundaries, the word-boundary cases, and the decision log. Every behaviour stated in the Interface comments has a criterion (the order of findings, UTF-8, the default root). Criterion 25 is the documenter's docs criterion and has no test.
   - Demo: the three commands are runnable. Each `Expect:` line is checkable. The first demo's README text `x` correctly gives no finding.
   - Architecture: the pure function is in `domain` and the command is in `entry`. It imports only downward and calls no tool.
   - Scope: it is within F0011's scope (the four documents, WE6.1, WE6.2, WE6.4, WE6.5, R17). It does not wire into `make check` or add a console script, as FEATURE.md's out of scope requires. WE6.3 is left out as the feature states.
3. tester: wrote red tests for criteria 1 to 23. Criteria 24 and 25 are the check and the docs, so they get no test.
   - criterion 1: tests/domain/test_documents.py::test_four_clean_documents_give_no_finding
   - criterion 2: tests/domain/test_documents.py::test_a_missing_document_gives_one_missing_finding (each document, with `None` and with the key absent)
   - criterion 3: tests/domain/test_documents.py::test_a_blank_document_gives_one_empty_finding (each document, whitespace only and the empty string)
   - criterion 4: tests/domain/test_documents.py::test_an_absent_required_section_is_a_finding_for_that_name_only (all five names)
   - criterion 5: tests/domain/test_documents.py::test_a_required_heading_only_inside_a_code_fence_does_not_count
   - criterion 6: tests/domain/test_documents.py::test_a_stop_without_its_table_row_is_a_finding (row absent, fenced, without backticks, prose line, indented)
   - criterion 7: tests/domain/test_documents.py::test_a_stop_row_needs_its_destination_in_words_in_any_case (three wrong rows, plus three rows with capitalised words that give no finding)
   - criterion 8: tests/domain/test_documents.py::test_a_kill_point_case_without_its_table_row_is_a_finding
   - criterion 9: tests/domain/test_documents.py::test_a_fault_path_without_a_row_naming_its_test_is_a_finding
   - criterion 10: tests/domain/test_documents.py::test_a_replaced_phrase_is_a_finding_for_its_document (every phrase plus `Factory-Run.json`, in each of README, operator guide and project guide)
   - criterion 11: tests/domain/test_documents.py::test_a_v1_word_standing_alone_is_a_finding
   - criterion 12: tests/domain/test_documents.py::test_a_v1_word_inside_a_longer_word_is_no_finding
   - criterion 13: tests/domain/test_documents.py::test_the_replaced_section_is_exempt_from_both_lists (section running to the end of the text, section ending at the next heading, a `###` line inside it, a fenced `## ` line inside it)
   - criterion 14: tests/domain/test_documents.py::test_text_outside_the_replaced_section_is_checked (text before the section, text after the next heading, a fenced `## Replaced from v1`)
   - criterion 15: tests/domain/test_documents.py::test_the_decision_log_is_exempt_from_both_lists
   - criterion 16: tests/domain/test_documents.py::test_a_decision_log_needs_a_heading_outside_code_fences
   - criterion 17: tests/domain/test_documents.py::test_findings_follow_the_rule_order_and_the_list_order (the operator-guide and project-guide cases together, in one call)
   - criterion 18: tests/domain/test_documents.py::test_a_finding_is_a_closed_model
   - criterion 19: tests/entry/test_check_documents.py::test_clean_documents_print_documents_ok_and_return_zero
   - criterion 20: tests/entry/test_check_documents.py::test_each_finding_prints_one_line_in_order_and_returns_one
   - criterion 21: tests/entry/test_check_documents.py::test_without_a_root_the_current_directory_is_read
   - criterion 22: tests/entry/test_check_documents.py::test_the_module_run_as_a_process_exits_with_the_status_of_main (clean documents give 0 and `documents ok`; an empty directory gives 1 and four `missing` lines; run through `run_process`)
   - criterion 23: tests/entry/test_check_documents.py::test_documents_are_read_as_utf_8

   Files created: tests/document_texts.py, tests/domain/test_documents.py, tests/entry/test_check_documents.py. tests/document_texts.py is a shared builder at the tests root, imported the way `human_clone` is. It builds clean texts from `STOP_TABLE`, `KILL_POINT_CASES` and `FAULT_PATHS`, so the tests follow the tables when they change. Destinations appear in words: health status, pull request, no stop. It also writes the documents as UTF-8 bytes.

   `make test` stops with 2 collection errors, in tests/domain/test_documents.py and tests/entry/test_check_documents.py. The modules `factory.domain.documents` and `factory.entry.check_documents` do not exist yet, and tests/document_texts.py also imports `factory.domain.documents`. `make lint` is green. Nothing open; no criterion needed interpreting.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: question. A test that already exists contradicts the Interface.

   Built and committed in 8813045: `src/factory/domain/documents.py` (`check_documents`, `DocumentFinding`, the constants) and `src/factory/entry/check_documents.py` (`main`, `--root`). All tests in `tests/domain/test_documents.py` and `tests/entry/test_check_documents.py` pass, and coverage is 99.5 %. `make check` is still red, for one reason only:

   - `tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode[--follow]` and `[factory-last-line]` fail. That test reads the bytes of every file under `src/`, `__pycache__` included, and forbids `--follow` and `factory-last-line`.
   - The Interface requires `REPLACED_PHRASES` in `src/factory/domain/documents.py` to hold exactly those two strings. The check cannot reject a phrase without naming it.

   Options:
   (a) The tester narrows `test_no_source_file_knows_the_follow_mode` so it skips `src/factory/domain/documents.py` and its compiled `.pyc`. Another way to do the same: the test checks only the watch and run entry modules and the adapters, so it still proves that no code implements a follow mode. I would then end with `tests` and name this change.
   (b) Build the two strings at runtime so their bytes appear neither in the source nor in the `.pyc`, e.g. `"".join(("-", "-follow"))`. Plain `"-" + "-follow"` is not enough, because the compiler folds it into one constant. This leaves the test untouched, but it only gets past the test rather than meeting its intent, and a reviewer would rightly flag it.
   (c) Move the replaced phrases out of `src/` into a data file. That changes the Interface, which names them as constants in `documents.py`.

   My recommendation is (a): the test is meant to stop code from knowing a follow mode, and a list of forbidden phrases is not such code.

   No refactor pass yet; it follows once the check is green. Nothing else is open.
5. human (pull request comment, 2026-10-17): (a), the first form: the tester exempts exactly `src/factory/domain/documents.py` and its compiled `.pyc` from `tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode`, by name, with a comment saying why (the list of replaced phrases must name them); every other file under `src/` stays searched. This is the human's leave for that change to an earlier story's test (recorded as F0011 decision 21). `src/` keeps the constants as the Interface states.
6. coder: tests. The human's answer (entry 5, option (a) in its first form) needs a test change. I may not make it.

   - **The change.** In `tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode`, exempt exactly `src/factory/domain/documents.py` and its compiled `.pyc` by name, with a comment saying why: the list of replaced phrases has to name them. Every other file under `src/` is still searched.
   - **Current state.** The test still searches every file under `src/` (lines 282-285), so `make check` is red on its `[--follow]` and `[factory-last-line]` cases.
   - **Committed so far.** The implementation is in 8813045: `src/factory/domain/documents.py` and `src/factory/entry/check_documents.py`. The constants stay in `src/`, as the Interface states.
   - **Next.** Once the tester has made this change, the ticket comes back to me. I will check that `make check` is green, then do the refactor pass and hand on to review.
   - **Assignment.** Not rewritten: the answer does not change what the task means.
7. tester: made the test change the human approved in entry 5 (option (a), first form), as the coder's entry 6 names it.
      - `tests/entry/test_watch.py::test_no_source_file_knows_the_follow_mode` now skips exactly two kinds of file, named in a new private helper `_names_the_replaced_phrases`: `src/factory/domain/documents.py`, and its compiled `.pyc` files (any file in `src/factory/domain/__pycache__/` whose name starts with `documents.`). A comment gives the reason: the document check's list of replaced phrases has to name the phrases in order to reject them. The test still searches every other file under `src/` for `--follow` and `factory-last-line`.
      - No other test was changed.
      - `make test` is green: every test passes, coverage is 99.53 %. `make lint` is green.

   `make lint`: lint: green
   `make test`: test: green
8. coder: review. The tester's change from entry 7 made `make check` green with no change to the code from 8813045. Coverage is 99.53 %; the one uncovered line is the `__main__` guard of `check_documents.py`, which the subprocess test runs outside coverage.
      - **Built (8813045).** `src/factory/domain/documents.py` holds the constants, the closed `DocumentFinding` and `check_documents`. It has one private helper per rule (`_missing_sections`, `_operator_guide_rows`, `_project_guide_rows`, `_wording`), and `_messages` calls them in the rule order the Interface gives. `src/factory/entry/check_documents.py` holds `main` with `--root`, defaulting to the current directory. It reads each document as UTF-8 and treats a file that does not exist as `None`.
      - **Main decision.** I reused the existing helpers in `factory.domain.sections` instead of writing a second fence-aware scanner:
        - `sections` finds the headings and the exempt section's line span.
        - `lines_outside_blocks` and `split_lines` find the table rows.
        - The v1-word boundary is one regex with a lookbehind and an optional lookahead over `[\w-]`. The lookahead is added only when the entry ends in a letter, so `drafts/` matches in `drafts/F0001-x.md`.
      - **Rejected.** A Markdown parser library: it would be a new dependency, and `sections` already skips code fences the way the Interface defines them. Building the two follow-mode phrases at runtime to get past the earlier source search: the human chose the test exemption instead (entry 5, F0011 decision 21).
      - **Refactor pass.** I read `git diff main...HEAD` over the code and changed nothing. The two guide branches in `_messages` look alike, but each lists its own rules in order; merging them would hide that order. No duplicate helpers and no dead code.
      - **Noticed, not touched.** The branch diff against `main` also shows `docs/runs/2026-10-12-overnight/night-log.md`, from the human's commit 6bed325. It is not mine.
      - **Open.** The four documents themselves are the documenter's work (criterion 25). The real files are not yet expected to print `documents ok`.

   `make check`: check: green
9. reviewer: no findings.
      - Acceptance criteria: I read every one of criteria 1 to 23 against its test in `tests/domain/test_documents.py` and `tests/entry/test_check_documents.py`. Each test checks the exact findings list or output, not just part of it.
        - Every failing side the Interface states has a test case: missing (`None` and an absent key), blank (whitespace and the empty string), an absent section, a heading only inside a code fence, a row only inside a code fence, a row without backticks, a prose line, an indented row, the destination words in any letter case, the word-boundary cases on both sides, the edges of the exempt section, and the decision log's heading inside and outside a code fence.
        - The coder's entry 8 records `make check` green.
      - Architecture: `src/factory/domain/documents.py` is pure. It imports only `factory.domain` (sections, stop_table, kill_point_cases, fault_paths) and does no I/O. `src/factory/entry/check_documents.py` imports only downward and reads plain UTF-8 text without calling any tool. It reuses `sections`, `lines_outside_blocks` and `split_lines` rather than writing a second fence-aware scanner; I found no other table-row helper under `src/factory`.
      - Security: no secrets, no suppression markers, no shell or string-built commands. The `tests/entry/test_watch.py` exemption is exactly the one the human approved in entry 5: it skips `documents.py` and its `.pyc` by name, with the reason in a comment, and still searches every other file under `src/`.
      - Quality: names and docstrings fit and there is no dead code. One redundancy, too small to send the ticket back: `sys.argv[1:] if argv is None else argv` in `main` repeats what argparse already does.
      - Hygiene: Assignment matches the build, and criterion 25 still tells the documenter what to write. The `docs/runs/.../night-log.md` line in the diff comes from the human's commit 6bed325 and is not under review.
10. documenter: the four documents now pass the check. `uv run python -m factory.entry.check_documents` prints `documents ok`, and `make check` is green.

    Files changed:
    - `README.md`: removed the "no `--follow`" clause from the commands paragraph. Added a paragraph that names `uv run python -m factory.entry.check_documents` beside the six console commands and says it is no console script and that `make check` does not run it. Added a closing `## Replaced from v1` section with the no-`--follow` statement.
    - `docs/operator-guide.md`:
      - Added `## Install`. It holds the decision 008 sentence, moved from "When the process refuses to start", plus `uv sync` and `make check`.
      - Renamed `## The instance's settings` to `## Configuration`. Done tickets and the F0010 feature file still use the old name as history, and I did not touch them.
      - Added a closing `## Replaced from v1` section. It holds the `--follow` / `factory-last-line` statement, v1's leftover files in `.git/`, and this repository's own v1 `factory/` tree with the `factory-check-story` consequence. These three statements moved there from the watch, tick and story-check sections.
    - `docs/project-guide.md`:
      - Reworded the v1 words and phrases in the `list_stories` description, the `factory-watch` command-line description, the tick and the stage start.
      - Moved the v1 to v1.1 rename table of the shipped agents into a closing `## Replaced from v1` section. "The seven agents" now points to it.
    - `docs/decisions.md`: added one entry. It records that the check is a command and not part of `make check`, that the log and every `## Replaced from v1` section are exempt, that WE6.3 is observed across the stories, and the human's test exemption (F0011 decision 21) with the alternatives rejected.

    Cross-read and found current: the operator guide's *The stops* table and the project guide's *Kill points* and *Fault-injection paths* tables. The check confirms every row of `STOP_TABLE`, `KILL_POINT_CASES` and `FAULT_PATHS` is present. The rest of the three guides had no replaced phrase or v1 word.

    Not touched: nothing stale found outside what the check flags. The `docs/runs/` line in the branch diff is the human's.

    No findings for the coder.

    `make check`: check: green
11. demo: I ran the three demo commands from the repository root, exactly as written and in order. All three matched their `Expect:` lines.

    1. `check_documents` on a set of hand-built texts:
    ```
    docs/operator-guide.md - missing
    docs/project-guide.md - empty
    docs/decisions.md - no decision recorded
    ```
    Met: the three expected lines, in the expected order. The README text `x` gave no finding, as criterion 1 implies.

    2. `uv run python -m factory.entry.check_documents; echo "exit=$?"`:
    ```
    documents ok
    exit=0
    ```
    Met: the four real documents pass the check (criterion 25).

    3. `uv run python -m factory.entry.check_documents --root /nonexistent; echo "exit=$?"`:
    ```
    README.md: missing
    docs/operator-guide.md: missing
    docs/project-guide.md: missing
    docs/decisions.md: missing
    exit=1
    ```
    Met: one `missing` line per document, in the order criterion 20 gives, and exit status 1 (criterion 22).

    I read the acceptance criteria again against the demo and the documents, and nothing contradicts them:
    - `README.md` lists `uv run python -m factory.entry.check_documents` next to the six console commands, says it is not a console script and that `make check` does not run it, and links the other three documents.
    - `docs/operator-guide.md` has `## Install`, which mentions decision 008 and says that nothing detects a v1 work item. It also has `## Configuration`, `## The stops` and `## Replaced from v1`.
    - `docs/project-guide.md` has `## Kill points`, `## Fault-injection paths` and `## Replaced from v1`.
    - The README's `## Replaced from v1` holds the statement that there is no `--follow` mode.
    - `docs/decisions.md` has a section saying that this check is a command outside `make check`, that the decision log is exempt from both word lists, that the `## Replaced from v1` sections are exempt too, and that WE6.3 is observed across the stories.

    I did not run `make check` myself: the factory runs it after this stage. No findings.
12. done (pull request merged); cost: 9 runs, 23.2 min, 71 turns, 216k tokens in (1414k more from cache), 38k out, $2.41
