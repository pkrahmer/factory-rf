---
stage: review
pr: 37
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Journal entries close their code fences

<!-- proposed by feature acceptance of 2026-10-13; refine before promoting -->

## Assignment (as of log entry 1)

Make the journal and the form check agree on where an entry ends, so that an entry whose text opens a code fence and never closes it cannot make a valid work item look damaged. Today an entry ends at the next column-0 number whatever the fences: `entry_text` and `append_entry` count three entries. The form check, though, counts only numbered lines outside fenced blocks, so it sees two and reports `the journal data lists 3 entries but the text shows 2`. The operator guide tells the human that this finding means a damaged state to restore. The same open fence also hides every `## ` section after the journal (the "Known limit" in `docs/project-guide.md`). The case is likely: an agent's result often quotes a tail of output, and a tail can start or end inside a fence.

The fix is in the one place that writes entries. `render_entry` adds a closing line when the rendered entry leaves a block open, so the body never holds an unclosed fence from the journal; the text in `NewEntry` and the journal records stay as given. Refusing such a text in `NewEntry` was rejected: it moves the repair to every caller in F0005, and an agent's output is not the caller's to repair. Counting journal entries regardless of fences in the form check was rejected too: it leaves the hidden sections, and the human confirmed on 2026-10-13 that journal entries are counted only outside code blocks. It keeps SI1.1 (the two halves stay in step) and SI1.3 (fences are respected).

## Interface

`src/factory/domain/sections.py` (exists; one public function added, and `code_blocks` uses it)

```python
def opening_fence(line: str) -> str | None: ...   # the run of backticks or tildes this line opens a block with, without indentation or info string; None when it opens none
```

`src/factory/domain/journal.py` (exists; one rule changes)

```python
def render_entry(number: int, entry: NewEntry) -> str: ...   # closes a block the rendered entry leaves open
def entry_text(document: WorkItemDocument, number: int) -> str: ...   # unchanged signature and code; its docstring says it returns the text as rendered, a closing line included
```

The rules; each has a criterion below:

- The rendered entry's lines (the first line with its `<number>. ` prefix, the continuation lines indented) are read with `factory.domain.sections.code_blocks`. When the last block has `end=None`, one more continuation line is added: the indent, then `opening_fence` of the opening line, the same character and the same count, without the info string.
- The first line of an entry starts with its number, so it opens no block, even when the text's first line is a fence run. No closing line is added for it; a later fence run in such a text opens a block of its own, which the first rule closes.
- A rendered entry whose blocks are all closed, or that has none, is unchanged.
- `NewEntry.text` and the journal record are unchanged. `entry_text` returns the text as rendered, so for such an entry its last line is the closing run, without the indent.

Tests: `tests/domain/test_journal.py` and `tests/domain/test_sections.py` (new tests beside the existing ones).

## Acceptance criteria

1. `render_entry(2, NewEntry(speaker="tester", kind="result", text="red:\n```\nE   assert 1 == 2"))` is `"2. tester: red:\n   ```\n   E   assert 1 == 2\n   ```"`, and `render_entry(10, …)` of the same entry ends with `"\n    ```"`: the closing line has the four-space indent of a two-digit number.
2. The closing run is the opening run. An unclosed opening of four backticks with the info string `python` gets the closing line of four backticks and no info string; an unclosed `~~~~~` gets `~~~~~`; an unclosed run of exactly three gets exactly three.
3. Only the last, unclosed block is closed. A text with a closed `~~~~` block and then an unclosed ```` ``` ```` gets one closing ```` ``` ```` line. `render_entry(2, NewEntry(speaker="tester", kind="result", text="```python\nx = 1\n```"))` is `"2. tester: ```python\n   x = 1\n   ```\n   ```"`: the first fence is on the numbered line, so the last one opens a block, which is closed.
4. These texts render with no closing line (a parametrized test of `render_entry(2, NewEntry(speaker="tester", kind="result", text=...))`): `"a\n```\nx\n```"` is `"2. tester: a\n   ```\n   x\n   ```"`; `"a\nb"` is `"2. tester: a\n   b"`; `"```"` is `"2. tester: ```"`; `"a\n``\nb"` is `"2. tester: a\n   ``\n   b"`.
5. Start from `WorkItemDocument(state=initial_state("tests"), body="# T\n\n## Journal\n")` and append `NewEntry(speaker="human", kind="created", text="created.", on=date(2026, 10, 13))`, the entry of criterion 1 and `NewEntry(speaker="coder", kind="result", text="green")`. Then `check_story_form(document, "# F\n\n## Journal\n", folder="in-progress")` is `[]`, the state has three records, and `entry_text(document, 3)` is `"green"`.
6. With a `## After` section after `## Journal`, appending the entry of criterion 1 leaves `After` in `[s.heading for s in sections(body)]`.
7. `entry_text` of the entry of criterion 1 is `"red:\n```\nE   assert 1 == 2\n```"`; `entry_text` of an entry without an unclosed fence is still its text as given.
8. `NewEntry.text` and the journal records stay as given: `NewEntry(speaker="tester", kind="result", text="red:\n```\nE   assert 1 == 2").text` is `"red:\n```\nE   assert 1 == 2"`, and after `append_entry` of a human entry and that entry the state's `journal` is `[JournalRecord(number=1, speaker="human", kind="created"), JournalRecord(number=2, speaker="tester", kind="result")]`.
9. `opening_fence("  ````python")` is `"````"` and `opening_fence("~~~")` is `"~~~"`; `opening_fence("``x")`, `opening_fence("x ```")` and `opening_fence("")` are `None`.
10. `make check` stays green.
11. docs: `docs/project-guide.md`, "The journal's entries": the "Format" bullet says that an entry whose text leaves a block open gets a closing line (the indent and the opening run, without the info string); `entry_text` is described as returning the text as rendered, that closing line included, not "as it was given"; the "Known limit" is removed; "Sections of a Markdown body" lists `opening_fence`. `docs/decisions.md` records why the entry closes the block instead of `NewEntry` refusing the text or the form check counting entries inside blocks.

## Demo

```bash
uv run python -c "
from datetime import date
from factory.domain.journal import NewEntry, append_entry, entry_text
from factory.domain.story_form import check_story_form
from factory.domain.work_item import WorkItemDocument, initial_state
F = chr(96) * 3
doc = WorkItemDocument(state=initial_state('tests'), body='# T\n\n## Journal\n\n## After\n')
doc = append_entry(doc, NewEntry(speaker='human', kind='created', text='created.', on=date(2026, 10, 13)))
doc = append_entry(doc, NewEntry(speaker='tester', kind='result', text='red:\n' + F + '\nE   assert 1 == 2'))
doc = append_entry(doc, NewEntry(speaker='coder', kind='result', text='green'))
print(doc.body, end='')
print(check_story_form(doc, '# F\n\n## Journal\n\n## After\n', folder='in-progress'))
print(repr(entry_text(doc, 2)))
"
```
Expect: the body shows `2. tester: red:`, then three-space-indented lines with a fence line, `E   assert 1 == 2` and a closing fence line, then `3. coder: green`, an empty line and `## After`. Then `[]`, because the form check finds the three entries and the `After` section. Last comes `'red:\n```\nE   assert 1 == 2\n```'`.

## Log (append only)

1. 2026-10-13 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`factory.domain.sections.opening_fence`, `factory.domain.journal.render_entry` and `entry_text`). The rules say how the closing line is built: indent, same character, same count, no info string. Each rule maps to a criterion.
   - Criteria: each is testable by one test function with literal inputs and outputs (1 to 9). The rules have their failing sides: unclosed vs closed (2, 3, 4), a first-line fence that opens no block (3, 4), two backticks that are no fence and an indented or empty line (4, 9), and the two-digit indent (1). Criteria 10 and 11 close the list as required.
   - Demo: runnable with `uv run python -c`. The Expect line is checkable: the body layout, `[]` and the repr of `entry_text`.
   - Architecture: the change is in `factory.domain` only, pure functions with no I/O. This fits the layering in CLAUDE.md, and no new dependency is involved.
   - Scope: within F0002's scope (journal, sections with code fences respected, form check). The story adds nothing from "Out of scope". Decision 15 in FEATURE.md records the human's choice.
3. tester: Tests written for criteria 1–9. The tests are red on purpose. `make lint` is green.
   - criterion 1: tests/domain/test_journal.py::test_render_entry_closes_a_block_the_entry_leaves_open (number 2 checks the full string, number 10 checks for the four-space closing line)
   - criterion 2: tests/domain/test_journal.py::test_the_closing_line_repeats_the_opening_run_without_info_string (parametrized: four backticks with `python`, `~~~~~`, exactly three backticks)
   - criterion 3: tests/domain/test_journal.py::test_only_the_last_unclosed_block_is_closed (a closed `~~~~` block, then an unclosed block of three backticks) and tests/domain/test_journal.py::test_a_fence_on_the_numbered_line_opens_no_block (the literal case from the criterion)
   - criterion 4: tests/domain/test_journal.py::test_an_entry_without_an_open_block_gets_no_closing_line (parametrized over the four texts in the criterion)
   - criterion 5: tests/domain/test_journal.py::test_an_entry_after_an_unclosed_fence_is_seen_by_the_form_check
   - criterion 6: tests/domain/test_journal.py::test_a_section_after_an_unclosed_fence_entry_stays_a_section
   - criterion 7: tests/domain/test_journal.py::test_entry_text_includes_the_closing_line (also checks that an entry without an open block, `created.`, comes back as given)
   - criterion 8: tests/domain/test_journal.py::test_the_entry_text_and_the_journal_records_stay_as_given
   - criterion 9: tests/domain/test_sections.py::test_opening_fence_is_the_run_a_line_opens_a_block_with (parametrized; I added exactly three backticks to the criterion's cases to cover the three-versus-two boundary, with `"``x"` as the refused side)

   No new files. The new tests sit beside the existing ones in tests/domain/test_journal.py and tests/domain/test_sections.py. test_journal.py gets a `TICKS` constant, `UNCLOSED`/`UNCLOSED_TEXT` and the helpers `_tester` and `_with_unclosed_entry`. It now imports `check_story_form`.

   What the test runner could not import: `opening_fence` from `factory.domain.sections`. Because of that, tests/domain/test_sections.py fails at collection and stops the run. The new journal tests import fine; they should then fail with wrong results until `render_entry` closes open blocks.

   Open: the existing test `test_entry_text_returns_the_text_as_it_was_given` keeps its name. It still passes because its text has no fence, but under the new rule the name is only half true. Renaming it is not part of this ticket.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Implemented in commit a7172fc. `make check` is green with 99.64 % coverage.
   - `src/factory/domain/sections.py`: added `opening_fence(line)`, which returns the backtick or tilde run that `_FENCE_OPENING` matches, or None when the line opens no block. `code_blocks` now uses it, so there is still one fence rule.
   - `src/factory/domain/journal.py`: `render_entry` builds the rendered lines first (the numbered first line, then the indented continuation lines). A new private `_closing_line` runs `code_blocks` over them. When the last block has `end=None`, it adds the indent plus `opening_fence` of that block's opening line. The numbered first line never matches the fence pattern, so a fence on it opens no block, as the rules require. `entry_text` has no code change; its docstring now says it returns the text as rendered, the closing fence line included.
   - Main decision: `render_entry` checks the lines as they will appear in the body, with prefix and indent, not the raw text. That way the closing line comes from the same `code_blocks` reading the form check uses, so the two cannot disagree. Rejected: checking `entry.text` on its own. Its first line has no number in front, so a fence there would wrongly count as opening a block (see criterion 3).
   - `_closing_line` keeps a `fence is None` guard. It never fires, because a block's opening line always has a fence; it is there only because `opening_fence` returns `str | None` for mypy.
   - Refactor: I read the diff and found nothing to change, so there is no refactor commit.
   - Noticed, not touched: as the tester also notes, the existing test name `test_entry_text_returns_the_text_as_it_was_given` is now only half true. Docs for criterion 11 (`docs/project-guide.md` and `docs/decisions.md`) are the documenter's work.

   `make check`: check: green
