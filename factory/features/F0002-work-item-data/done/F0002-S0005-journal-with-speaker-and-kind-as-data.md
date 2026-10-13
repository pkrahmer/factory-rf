---
stage: done
pr: 32
blocked: null
comments_seen: 0
round: 2
attempts: 0
---
# Journal with speaker and kind as data

## Assignment (as of log entry 1)

Build the journal of a work item: numbered, append-only entries whose visible text is Markdown in the body under `## Journal` and whose speaker and kind are kept as data in the front matter's `journal` list (SI1.1). One call, `append_entry`, writes both halves, so the number of data records always equals the number of visible entries; code that needs to know who spoke or what kind of entry it was reads the data (`last_record`) and never the text, so changing how a speaker is displayed changes nothing a reader returns. The story also builds the display helpers (`render_entry`, `entry_text`) and the restore that puts one version's whole state and journal into another, which is how the factory will undo an agent's tampering with state and journal after an agent run (F0004). It covers SI1.1 and keeps kept thing 4 (the journal is append-only, numbered and attributed; only the factory writes it). Only the human's entries carry a date, as in v1. It uses the section finder of F0002-S0004 and the reader and writer of F0002-S0003; nothing here reads a file.

## Interface

`src/factory/domain/journal.py` (F0002-S0002 created the module with `HUMAN`, `FACTORY`, `Speaker`, `JournalKind` and `JournalRecord`; this story adds the rest)

```python
class NewEntry(BaseModel):
    speaker: Speaker
    kind: JournalKind
    text: str
    on: date | None = None

def render_entry(number: int, entry: NewEntry) -> str: ...
def append_entry(document: WorkItemDocument, entry: NewEntry) -> WorkItemDocument: ...
def entry_text(document: WorkItemDocument, number: int) -> str: ...
def last_record(
    document: WorkItemDocument, *, speaker: str | None = None, kind: JournalKind | None = None
) -> JournalRecord | None: ...
def restore_state_and_journal(current: WorkItemDocument, baseline: WorkItemDocument) -> WorkItemDocument: ...
```

`NewEntry` is frozen and forbids unknown fields. The rules; each has a criterion below:

- `factory.domain.work_item` imports `JournalRecord` from this module, and the functions here take and return `WorkItemDocument`, so the two modules would import each other. This module therefore imports `factory.domain.work_item` only under `typing.TYPE_CHECKING` (with `from __future__ import annotations`), and uses `model_copy` and the document's attributes where it needs a document; importing either module first works.
- `NewEntry.text` is stripped of surrounding whitespace and must not be blank afterwards; `on` is required when the speaker is `human` and refused for any other speaker.
- `render_entry(number, entry)` is `"<number>. "`, then `"<YYYY-MM-DD> "` exactly when `on` is set, then `"<speaker>: "`, then the text. The speaker is shown as its name. Every line of the text after the first is indented by `len("<number>. ")` spaces, so by 3 spaces for the numbers 1 to 9, by 4 for 10 to 99 and by 5 for 100 to 999; a blank line stays empty. There is no final newline.
- `append_entry` raises `WorkItemFormatError` with the fault `the document has no state` when `state` is `None` and with the fault `missing section: ## Journal` when the body has no `Journal` section outside a code fence. Otherwise it returns a document whose state is the old state with one more record, `JournalRecord(number=len(old journal) + 1, speaker=..., kind=...)`, and whose body has the rendered entry placed on the lines after the last non-blank line of the `Journal` section, or after one blank line under the heading when the section has no text. Entries follow one another with no blank line between them. Nothing else changes: not the other state fields, not `ignored_keys`, not another line of the body, and the result ends with a newline exactly when the body did. The input document is not changed.
- `entry_text(document, number)` finds the entry that starts with `"<number>. "` at column 0 in the `Journal` section and returns its text as it was given to `NewEntry`: the entry's lines up to the next line that starts with a number at column 0 or the end of the section, without trailing blank lines, with everything up to and including the first `": "` of the first line removed and the indent removed from the other lines. It raises `WorkItemFormatError` with the fault `missing section: ## Journal` or `no journal entry <number>`. It reads neither speaker, kind nor cost from the text and is for display only.
- `last_record(document, speaker=..., kind=...)` is the last record of `state.journal` that matches every filter given, or `None`; with no filter it is the last record. It raises `WorkItemFormatError` with the fault `the document has no state` when `state` is `None`.
- `restore_state_and_journal(current, baseline)` returns a document with the baseline's whole state; with a body that is the current body in which the first `Journal` section, from its heading line to its last non-blank line, is replaced by the baseline's first `Journal` section taken the same way; the lines between that block and the next section stay as they are in the current body; and with the current `ignored_keys`. When the current body has no `Journal` section, the baseline's block is added at the end of the body after one blank line and the body ends with a newline. It raises `WorkItemFormatError` with the fault `the document has no state` when the baseline's state is `None` and with `missing section: ## Journal` when the baseline's body has no `Journal` section.

Tests: `tests/domain/test_journal.py`, `tests/adapters/test_journal_as_data.py`. A test that constructs a model with an unknown field or a value of the wrong type (the kind `note`) does so through a variable typed `type[BaseModel]`, and one that assigns to a frozen field does so with `setattr` (`CLAUDE.md`, Tests).

## Acceptance criteria

1. `NewEntry(speaker="factory", kind="started", text=" started intake as factory-1.\n")` is valid with the text stripped and `on` `None`; `NewEntry(speaker="human", kind="created", text="created.", on=date(2026, 10, 12))` is valid.
2. `NewEntry` raises `ValidationError` for a `human` entry without `on`, for a `factory` entry and an `intake` entry with `on` set, for the texts `""` and `"  \n"`, for the speaker `Intake`, for the kind `note` and for an unknown field; the model is frozen.
3. `render_entry(2, NewEntry(speaker="factory", kind="started", text="started intake as factory-1."))` is `"2. factory: started intake as factory-1."`, and `render_entry(1, NewEntry(speaker="human", kind="created", text="created.", on=date(2026, 10, 12)))` is `"1. 2026-10-12 human: created."`.
4. `render_entry(3, ...)` with the text `"accepted\nfirst\n\nsecond"` for the speaker `intake` is `"3. intake: accepted\n   first\n\n   second"`; the continuation lines are indented by 4 spaces for the number 10 and by 5 for the number 100, and the blank line stays empty without spaces.
5. `append_entry` of a human `created` entry on a document with `initial_state("intake")` and the body `"# T\n\n## Journal\n"` gives the body `"# T\n\n## Journal\n\n1. 2026-10-12 human: created.\n"` and a state whose journal is `[JournalRecord(number=1, speaker="human", kind="created")]`.
6. A second `append_entry` puts the entry directly under the first with no blank line between and adds the record `JournalRecord(number=2, speaker="intake", kind="result")`; with nine records already in the state the new entry starts with `10. ` and its record has the number 10.
7. `append_entry` leaves everything else as it was: for a body with a section before the `Journal` section and a section `After` behind it, the entry goes after the last entry and before the blank line that precedes `After`; all other lines, the other state fields and `ignored_keys` are equal; the input document is unchanged; the result ends with a newline when the body did and has none when the body had none.
8. An entry whose text contains a line `## Not a heading` and a fenced block does not change the headings that `sections` finds in the body: they are the same before and after `append_entry`.
9. `append_entry` raises `WorkItemFormatError` with the fault `the document has no state` for a document without state, and with the fault `missing section: ## Journal` for a body without a `Journal` section and for a body whose `## Journal` line is only inside a fenced block.
10. `entry_text` returns the text as it was given: `"accepted\nfirst\n\nsecond"` for the entry rendered in criterion 4, and `"created."` for a human entry whose line starts with a date.
11. `entry_text(document, 1)` of a journal with ten entries returns the text of entry 1 only, not of entry 10 or of the entry that follows entry 1, and `entry_text` raises `WorkItemFormatError` with the fault `no journal entry 7` for a journal without entry 7 and with the fault `missing section: ## Journal` for a body without the section.
12. `last_record` returns the last record when no filter is given, the last record of a speaker with `speaker=`, the last of a kind with `kind=`, the last that matches both with both, and `None` when none matches.
13. `last_record` and `restore_state_and_journal` raise `WorkItemFormatError` with the fault `the document has no state` for a document (the baseline, for the restore) without state.
14. SI1.1: for a document built with `append_entry` and rendered with `FrontmatterWorkItemWriter`, replacing the visible `intake:` of an entry by `Intake Agent:` in the text and parsing the result with `FrontmatterWorkItemReader` returns the same `state.journal`, and `last_record(parsed, speaker="intake")` returns the same record as before the change.
15. `restore_state_and_journal` returns the baseline's whole state: a current state with another stage, `attempts`, `blocked`, `claim`, `pull_request` and a longer journal is replaced field by field by the baseline's, while `ignored_keys` stays the current document's.
16. `restore_state_and_journal` replaces the `Journal` section of the current body by the baseline's: an entry that was appended or changed in the current body is gone and the baseline's entries are back, while edits made elsewhere in the current body and the blank lines before the next section stay.
17. `restore_state_and_journal` adds the baseline's `Journal` section at the end after one blank line, with a final newline, when the current body has none, and raises `WorkItemFormatError` with the fault `missing section: ## Journal` when the baseline's body has none.
18. `factory.domain.journal` and `factory.domain.work_item` can each be imported first in a fresh interpreter (a subprocess running `python -c "import factory.domain.journal"` and the same for `work_item`, both exit 0), and `factory.domain.journal` imports `factory.domain.work_item` only inside an `if TYPE_CHECKING:` block, found by parsing the module with `ast`.
19. make check stays green.
20. docs: `docs/project-guide.md` explains the journal: the visible format with its continuation indent, that only the human's entries are dated, that speaker and kind are data in the front matter and are never read from the text, and what the restore does; `docs/decisions.md` records why the journal's data sits in the front matter.

## Demo

```bash
uv run python -c "
from datetime import date
from factory.domain.journal import NewEntry, append_entry, entry_text, last_record
from factory.domain.work_item import WorkItemDocument, initial_state
doc = WorkItemDocument(state=initial_state('intake'), body='# T\n\n## Journal\n')
doc = append_entry(doc, NewEntry(speaker='human', kind='created', text='created.', on=date(2026, 10, 12)))
doc = append_entry(doc, NewEntry(speaker='intake', kind='result', text='accepted\nEvery criterion is testable.'))
print(doc.body, end='')
record = last_record(doc, speaker='intake')
print(record.number, record.speaker, record.kind)
print(entry_text(doc, 2))
"
```
Expect: ten lines: `# T`, an empty line, `## Journal`, an empty line, `1. 2026-10-12 human: created.`, `2. intake: accepted`, `   Every criterion is testable.` (indented by three spaces), then `2 intake result`, then `accepted` and `Every criterion is testable.`.

```bash
uv run python -c "
from datetime import date
from factory.domain.journal import NewEntry, append_entry, restore_state_and_journal
from factory.domain.work_item import WorkItemDocument, initial_state
base = append_entry(WorkItemDocument(state=initial_state('intake'), body='# T\n\nSpec.\n\n## Journal\n'), NewEntry(speaker='human', kind='created', text='created.', on=date(2026, 10, 12)))
current = base.model_copy(update={'state': initial_state('doing'), 'body': base.body.replace('Spec.', 'Spec changed.') + '2. intake: forged\n'})
restored = restore_state_and_journal(current, base)
print(restored.state.stage, restored.state == base.state)
print(restored.body, end='')
"
```
Expect: `intake True`, then the body with the edit kept and the forged entry gone: `# T`, an empty line, `Spec changed.`, an empty line, `## Journal`, an empty line, `1. 2026-10-12 human: created.`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: concrete module `src/factory/domain/journal.py` with full signatures for `NewEntry`, `render_entry`, `append_entry`, `entry_text`, `last_record` and `restore_state_and_journal`. The exact fault strings and the TYPE_CHECKING import rule are stated. Every behaviour in the Interface (strip, date rule, indent width, placement, newline handling, text recovery, restore body layout) has a criterion.
   - Criteria: each is testable by one test function without further decisions. Both sides of every rule are covered. For `NewEntry`, criteria 1 and 2 cover valid and invalid input. `append_entry` fails on no state and on a missing or fenced `Journal` section (9). `entry_text` fails with `no journal entry 7` and with a missing section (11). `last_record` and the restore fail on a missing state (13). The restore fails on a baseline without the section (17). Filters have a no-match case (12).
   - Demo: both commands are runnable. I counted the first one's expected output as ten lines, and the second one's expected output matches the restore rule.
   - Architecture: the domain module is pure, reads no file and depends only on S0002 to S0004 pieces. The circular import is handled by an explicit TYPE_CHECKING rule that criterion 18 tests.
   - Scope: the story is within FEATURE.md scope (SI1.1, the journal, the restore) and touches nothing listed under Out of scope.
3. tester: Wrote red tests for every acceptance criterion against the Interface of `factory.domain.journal`.
   - criterion 1: tests/domain/test_journal.py::test_a_new_entry_strips_its_text_and_needs_a_date_only_from_the_human
   - criterion 2: tests/domain/test_journal.py::test_a_new_entry_refuses_invalid_values (parametrized: human without `on`, factory with `on`, intake with `on`, `""`, `"  \n"`, speaker `Intake`, kind `note`, unknown field, all through `type[BaseModel]`), ::test_a_new_entry_is_frozen (`setattr`)
   - criterion 3: tests/domain/test_journal.py::test_render_entry_writes_number_date_speaker_and_text
   - criterion 4: tests/domain/test_journal.py::test_render_entry_indents_continuation_lines_and_keeps_blank_lines_empty, ::test_the_continuation_indent_is_the_width_of_the_number (boundaries 1, 9, 10, 99, 100 and 999 → 3, 3, 4, 4, 5, 5)
   - criterion 5: tests/domain/test_journal.py::test_append_entry_writes_the_first_entry_under_the_heading_and_its_record
   - criterion 6: tests/domain/test_journal.py::test_append_entry_puts_the_next_entry_directly_under_the_last, ::test_append_entry_numbers_the_tenth_entry_ten
   - criterion 7: tests/domain/test_journal.py::test_append_entry_changes_nothing_else (parametrized with and without a final newline; checks the other state fields, `ignored_keys` and that the input is unchanged)
   - criterion 8: tests/domain/test_journal.py::test_an_entry_with_a_heading_and_a_fence_adds_no_section
   - criterion 9: tests/domain/test_journal.py::test_append_entry_refuses_a_document_without_state, ::test_append_entry_refuses_a_body_without_a_journal_section (no section; `## Journal` only inside a fence)
   - criterion 10: tests/domain/test_journal.py::test_entry_text_returns_the_text_as_it_was_given
   - criterion 11: tests/domain/test_journal.py::test_entry_text_returns_only_the_entry_asked_for (ten entries; entry 1 has two lines), ::test_entry_text_refuses_a_missing_entry, ::test_entry_text_refuses_a_body_without_a_journal_section
   - criterion 12: tests/domain/test_journal.py::test_last_record_without_a_filter_is_the_last_record, ::test_last_record_is_the_last_that_matches_every_filter, ::test_last_record_is_none_when_nothing_matches
   - criterion 13: tests/domain/test_journal.py::test_last_record_refuses_a_document_without_state, ::test_restore_refuses_a_baseline_without_state
   - criterion 14: tests/adapters/test_journal_as_data.py::test_a_changed_speaker_in_the_text_changes_no_record
   - criterion 15: tests/domain/test_journal.py::test_restore_returns_the_baseline_state_and_the_current_ignored_keys
   - criterion 16: tests/domain/test_journal.py::test_restore_puts_the_baseline_journal_back_and_keeps_other_edits (two blank lines before `## After` in the current body stay)
   - criterion 17: tests/domain/test_journal.py::test_restore_adds_the_journal_when_the_current_body_has_none (current body with and without a final newline), ::test_restore_refuses_a_baseline_without_a_journal_section
   - criterion 18: tests/domain/test_journal.py::test_either_module_can_be_imported_first (one subprocess per module), ::test_the_journal_imports_the_work_item_only_for_type_checking (uses `ast` through `tests/source_search.py`)
   - criteria 19 and 20 are for the coder and the documenter.

   Files created: tests/domain/test_journal.py, tests/adapters/test_journal_as_data.py.

   `make test`: both new modules fail at collection with an import error because `NewEntry`, `render_entry`, `append_entry`, `entry_text`, `last_record` and `restore_state_and_journal` don't exist yet in `factory.domain.journal`. That is the expected failure. `make lint` is green. I skipped the type check, as this stage's skill says.

   To keep the new-entry tests valid, I kept the 20-character speaker `Intake Agent` out of `NewEntry` and only edited it into the rendered text.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Built the journal in `src/factory/domain/journal.py` (commits d82bc08 feat, 321e24a refactor). It adds `NewEntry`, `render_entry`, `append_entry`, `entry_text`, `last_record` and `restore_state_and_journal`. All tests in tests/domain/test_journal.py and tests/adapters/test_journal_as_data.py pass, `make check` is green, and both demos print exactly the expected output.
      - Import cycle: the module uses `from __future__ import annotations` and imports `WorkItemDocument` and `WorkItemState` only under `TYPE_CHECKING`. It builds documents with `model_copy`, so it never needs those classes at runtime. `date`, `Speaker` and `JournalKind` stay runtime imports because Pydantic resolves `NewEntry`'s fields from them.
      - Main design decision: every function finds the `Journal` section with `sections`/`split_lines` from `factory.domain.sections`, through two small helpers. `_journal_section` raises `missing section: ## Journal` and `_last_text_line` finds the section's last non-blank line, or its heading when the section has no text. `append_entry` inserts after that line (with a leading blank line when the section is empty). The restore replaces heading-to-last-text-line, so the blank lines before the next section stay where they were. Rejected alternative: making `sections._first_section` public or adding a journal-specific helper to `sections.py`. That would have widened another story's module for one caller.
      - `entry_text` ends an entry at the next line whose first character is a digit, which is "starts with a number at column 0" from the Interface. It removes the continuation indent with `removeprefix`, so blank lines stay empty.
      - Restore without a `Journal` section in the current body: trailing blank lines of the current body are dropped before the one blank line and the block. That keeps exactly one blank line, as the Interface says.
      - Refactor: replaced a one-character regex for "next entry starts" with `str.isdigit` on the first character. Nothing else needed changing.
      - Noticed, not touched: two defensive lines are not covered by the tests: the trailing-blank trim in `_entry_lines` and the trailing-blank strip in the restore. A text whose continuation line holds an unclosed fence would still swallow later headings, because the indent does not neutralise a fence. No criterion asks for this.

   `make check`: check: green
5. reviewer: Checklist group 1 (acceptance criteria and limits) fails. The code in `src/factory/domain/journal.py` behaves as the Interface says on every path I traced, and each of criteria 1–18 has a test that checks what the criterion says. But three rules the Interface states have no test for their other side. CLAUDE.md (Tests) counts each untested side as a finding. None of the three has a criterion, so these are gaps in the story as well as in the tests. The coder may not edit tests (R9), so the fix goes through the tester or a question to the human.

   1. tests/domain/test_journal.py (criterion 11 tests) vs. `_entry_lines` in src/factory/domain/journal.py:276-287. The Interface says `entry_text` finds the entry whose `"<number>. "` is "at column 0" and ends it at the next line "that starts with a number at column 0". No test has an indented case for either rule. Fix: add a test with an entry whose text has a continuation line such as `2. not an entry`, rendered as `   2. not an entry`. `entry_text(document, 2)` must then raise `no journal entry 2` (or return the real entry 2), and `entry_text(document, 1)` must return the whole text, including that line.
   2. tests/domain/test_journal.py vs. src/factory/domain/journal.py:285-286. The Interface says `entry_text` returns the entry "without trailing blank lines", but every test has the `Journal` section at the end of the body, so the trimming loop is never run. The coder's entry says these lines are uncovered. Fix: add an `entry_text` case where the last entry is followed by blank lines and another section (`...\n2. intake: accepted\n\n## After\n`) and assert the result has no trailing blank line.
   3. tests/domain/test_journal.py::test_restore_adds_the_journal_when_the_current_body_has_none vs. src/factory/domain/journal.py:327-328. The Interface says the baseline's block goes at the end "after one blank line". Both parametrized bodies (`"# T\n\nSpec.\n"`, `"# T\n\nSpec."`) end in a non-blank line, so the "one" is never tested against a body that already ends in blank lines, and the coder reports this branch as uncovered. Fix: add a current body like `"# T\n\nSpec.\n\n\n"` to the parametrization, expecting exactly one blank line before `## Journal`.

   Checked and not a finding: the `# noqa: S603` in `test_either_module_can_be_imported_first` follows the existing marker in tests/test_layers.py:22 on main, and the guard in `docs/decisions.md` covers `src/factory` only. I did not review groups 2–5 because group 1 failed.
6. coder: Round 1. All three review findings are missing tests, not wrong code. I may not edit tests (R9), so I'm sending the ticket to the tester with the exact additions. I made no code change and no commit.
      I ran each finding's case against the current `src/factory/domain/journal.py` from the command line. All three already behave as the Interface says, so the new tests should pass without a code change:
      - `entry_text` and indented numbers: `entry_text(document, 1)` returns `'accepted\n2. not an entry'` for an entry whose continuation line is `   2. not an entry`. `entry_text(document, 2)` raises `WorkItemFormatError` `no journal entry 2`.
      - `entry_text` and trailing blank lines: for the body `...1. intake: accepted\n   2. not an entry\n2. intake: x\n\n\n## After\n`, `entry_text(document, 2)` returns `'x'`.
      - Restore onto a body ending in blank lines: the current body `'# T\n\nSpec.\n\n\n'` with no Journal section gives `'# T\n\nSpec.\n\n## Journal\n\n1. intake: accepted\n   2. not an entry\n'`, with exactly one blank line before the heading.
      Test changes for the tester, all in tests/domain/test_journal.py:
      (1) Add a test where entry 1's text has the continuation line `2. not an entry`. It asserts that `entry_text(document, 1)` returns the whole text including that line, and that `entry_text(document, 2)` raises `no journal entry 2`.
      (2) Add a test where the last entry is followed by blank lines and a `## After` section. It asserts that `entry_text` returns that entry's text with no trailing blank line.
      (3) Add the current body `"# T\n\nSpec.\n\n\n"` to the parametrization of `test_restore_adds_the_journal_when_the_current_body_has_none`. It expects exactly one blank line before `## Journal` and a final newline.
      Nothing else is open.
7. tester: Test change from the coder's entry 6, which closes the reviewer's three findings in entry 5. I changed only tests/domain/test_journal.py:
      (1) New test `test_entry_text_ignores_an_indented_number`. Entry 1's text is `created.\n2. not an entry`. The test checks that the rendered body holds `   2. not an entry`, that `entry_text(document, 1)` returns the whole text including that line, and that `entry_text(document, 2)` raises `no journal entry 2`. This covers the indented side of both "at column 0" rules.
      (2) New test `test_entry_text_drops_the_blank_lines_before_the_next_section`. It appends two entries to a `Journal` section that is followed by blank lines and `## After`. It checks that the blank lines stay between the last entry and `## After`, and that `entry_text(document, 2)` returns `accepted` with no trailing blank line.
      (3) Added the current body `"# T\n\nSpec.\n\n\n"` to the parametrization of `test_restore_adds_the_journal_when_the_current_body_has_none`. The existing assertion already expects exactly one blank line before `## Journal` and a final newline.
      The code was not changed, and all three tests pass against the current `src/factory/domain/journal.py`, as the coder predicted.
      `make test`: green, total coverage 99.66 %. `make lint`: green.

   `make lint`: lint: green
   `make test`: test: green
8. coder: Round 1, after the tester's entry 7. I made no code change and no commit. The reviewer's three findings in entry 5 were missing tests, not faulty code. The tester added those tests in tests/domain/test_journal.py: `test_entry_text_ignores_an_indented_number`, `test_entry_text_drops_the_blank_lines_before_the_next_section`, and the body `"# T\n\nSpec.\n\n\n"` in the parametrization of `test_restore_adds_the_journal_when_the_current_body_has_none`. They pass against the unchanged `src/factory/domain/journal.py` (commits d82bc08 feat, 321e24a refactor).
      - Checked: `make check` is green (total coverage 99.66 %). `src/factory/domain/journal.py` is now fully covered, including the two defensive branches entry 4 reported as untested: the trailing-blank trim in `_entry_lines` and the trailing-blank strip in the restore.
      - Refactor: no new diff this round, so there was nothing to refactor.
      - Still open from entry 4, not touched: a continuation line in an entry's text that opens an unclosed fence still hides the headings after it, because the indent does not neutralise a fence. No criterion asks for this.

      `make check`: check: green

   `make check`: check: green
9. reviewer: Round 1, second review. Groups 1 to 3 pass. Group 4 (quality) fails.

   - Group 1: each of criteria 1–18 has a test that checks what the criterion says. The three gaps from entry 5 are now closed in tests/domain/test_journal.py by `test_entry_text_ignores_an_indented_number`, `test_entry_text_drops_the_blank_lines_before_the_next_section` and the third parametrized body of `test_restore_adds_the_journal_when_the_current_body_has_none`. Each limit the Interface states is tested on both sides: the date rule for human and for non-human speakers, a blank text, an indent width at each digit boundary, the final newline present and absent, and column 0 against an indented line. Entry 8 says `make check` is green.
   - Group 2: `factory.domain.journal` stays pure, and it imports only from the domain layer. It imports `work_item` only under `TYPE_CHECKING`.
   - Group 3: the `# noqa: S603` in `test_either_module_can_be_imported_first` follows the same marker in tests/test_layers.py:22 on main and has its reason beside it. The rule in `docs/decisions.md` covers only `src/factory`. No secrets, no shell built from strings.

   Findings:
   1. src/factory/domain/journal.py:107: the private helper `_last_text_line` has a docstring, but CLAUDE.md (Docs) says there are "none on private names", and no other private function under src/factory has one. Fix: remove the docstring. If the fallback to the heading needs explaining, say why in a comment.
   2. src/factory/domain/journal.py:173: the private helper `_journal_block` has a docstring, against the same rule. Fix: remove it.

   Checked, not a finding: an entry text whose continuation line opens a fence and never closes it still hides the headings that follow. The coder recorded this as open in entries 4 and 8. No rule in the Interface covers it, and it matters only when a section follows `Journal`. If the human wants it handled, it belongs in a later story.
10. coder: Round 2. I fixed the two findings from entry 9 in src/factory/domain/journal.py (commit f72edc8) and changed nothing else.
       1. Removed the docstring from the private helper `_last_text_line`. In its place, a comment on the fallback says why it returns the heading: an empty section ends at its heading, so whatever follows goes right under it.
       2. Removed the docstring from the private helper `_journal_block`.
       - Behaviour and tests are unchanged. `make check` is green (total coverage 99.66 %).
       - Refactor: this round's diff only removes docstrings, so there was nothing to refactor.
       - Still open from entries 4 and 8, not touched: if a continuation line in an entry opens a fence and never closes it, the headings after it stay hidden. No rule in the Interface covers this.

    `make check`: check: green
11. reviewer: Round 2 review: no findings.

    - The round-2 change (commit f72edc8) fixes both findings from entry 9. The private helpers `_last_text_line` (src/factory/domain/journal.py:106) and `_journal_block` (:172) no longer have docstrings. The comment at :110 says why an empty section ends at its heading. No private name under the diff has a docstring now, and every public class and function has one.
    - Group 1: each of criteria 1–18 has a test in tests/domain/test_journal.py or tests/adapters/test_journal_as_data.py that checks what the criterion says. Every rule in the Interface is tested on both sides:
      - the date rule for human and for non-human speakers;
      - blank text;
      - indent width at 1/9, 10/99 and 100/999;
      - final newline present and absent;
      - an entry number at column 0 and an indented one;
      - trailing blank lines before a next section;
      - the restore onto a body that already ends in blank lines;
      - every fault string.
      Entry 10 says `make check` is green.
    - Group 2: `factory.domain.journal` stays pure. It imports only from the domain layer, and imports `work_item` only under `TYPE_CHECKING`.
    - Group 3: the diff has no secrets and builds no shell or SQL from strings. The only marker is `# noqa: S603` in the test's subprocess call, with its reason beside it, following tests/test_layers.py on main.
    - Group 4: names say what things are and each helper does one thing. The diff has no dead code, uses `sections`/`split_lines` from `factory.domain.sections` instead of re-parsing, and its comments say why.
    - Group 5: the log records the main decision (find the section with `sections`; restore replaces from the heading to the last text line) and the rejected alternative (widening `sections.py`). `Assignment` matches what was built. Criterion 20 still says what the documenter must write.

    Still open, not a finding: if a continuation line of an entry opens a code fence and never closes it, the headings after it stay hidden (entries 4, 8, 10). No rule in the Interface covers this. If the human wants it handled, it belongs in a later story.
12. documenter: round 2. The code matches the Interface and the criteria, so there are no findings. Docs written, `make check` green.
    - `docs/project-guide.md`: replaced "functions not built yet" in "The journal's data" with a new section, "The journal's entries". It covers the visible format and continuation indent, that only the human's entries are dated, speaker and kind as data read with `last_record` and never from the text, `entry_text` for display only, what the restore does, the fault strings, the TYPE_CHECKING import rule and the known limit (an unclosed fence in a continuation line hides later headings). It includes the first demo command, which I ran; the output matches.
    - `docs/decisions.md`: added a decision on why the journal's speaker and kind are data in the front matter. It gives the alternatives rejected.
    - `README.md`: the one-line status now lists the journal.
    - Cross-read and found current: `docs/operator-guide.md`, and the rest of `docs/project-guide.md` (the work item data, the reader and writer, and the sections).
    - Stale but unrelated, not touched: none seen.

    `make check`: check: green
13. demo: Demo round 2: I ran both `## Demo` commands from the repository root exactly as written. Both exited 0. I piped the output through `cat -A` to check line ends and indentation.

    Command 1 (append_entry, last_record, entry_text):
    ```
    # T

    ## Journal

    1. 2026-10-12 human: created.
    2. intake: accepted
       Every criterion is testable.
    2 intake result
    accepted
    Every criterion is testable.
    ```
    Met its Expect line: ten lines in the expected order. The continuation line is indented by exactly three spaces and carries no trailing spaces. The human entry has a date and the intake entry has none.

    Command 2 (restore_state_and_journal):
    ```
    intake True
    # T

    Spec changed.

    ## Journal

    1. 2026-10-12 human: created.
    ```
    Met its Expect line: the stage is back to `intake` and the whole state equals the baseline's. The body edit `Spec changed.` stays, the forged entry `2. intake: forged` is gone, and the body ends with a newline.

    Criteria check: the demo contradicts none of the acceptance criteria. It matches criteria 3–7 (render format, continuation indent, entries placed directly under each other, final newline), 10 (entry_text returns the original text), 12 (last_record with `speaker=`), 15 (the baseline's whole state comes back) and 16 (the Journal section is replaced and edits elsewhere stay).

    No findings. Nothing is open from the demo.
14. done (pull request merged); cost: 12 runs, 11.8 min, 78 turns, 267k tokens in (1191k more from cache), 46k out, $3.07
