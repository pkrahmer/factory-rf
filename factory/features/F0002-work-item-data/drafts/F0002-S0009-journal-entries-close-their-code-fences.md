# Journal entries close their code fences

<!-- proposed by feature acceptance of 2026-10-13; refine before promoting -->

## Assignment (as of log entry 1)

Make the journal and the form check agree on where an entry ends, so that an entry whose text opens a code fence and never closes it cannot make a valid work item look damaged. Today an entry ends at the next column-0 number whatever the fences: `entry_text` and `append_entry` count three entries. The form check, though, counts only numbered lines outside fenced blocks, so it sees two and reports `the journal data lists 3 entries but the text shows 2`. The operator guide tells the human that this finding means a damaged state to restore. The same open fence also hides every `## ` section after the journal (the "Known limit" in `docs/project-guide.md`). The case is likely: an agent's result often quotes a tail of output, and a tail can start or end inside a fence.

The fix is in the one place that writes entries. `render_entry` adds a closing line when the rendered entry leaves a block open, so the body never holds an unclosed fence from the journal. The alternative, which the human may prefer while refining, is to refuse such a text in `NewEntry`; that moves the repair to every caller in F0005. A third option is to count journal entries regardless of fences in the form check; it leaves the hidden sections, so it is not proposed. It keeps SI1.1 (the two halves stay in step) and SI1.3 (fences are respected).

## Interface

`src/factory/domain/journal.py` (exists; one rule changes)

```python
def render_entry(number: int, entry: NewEntry) -> str: ...   # closes a block the rendered entry leaves open
def entry_text(document: WorkItemDocument, number: int) -> str: ...   # unchanged signature
```

The rules; each has a criterion below:

- The rendered entry's lines (the first line with its `<number>. ` prefix, the continuation lines indented) are read with `factory.domain.sections.code_blocks`. When the last block has `end=None`, one more continuation line is added: the indent, then the opening line's run of fence characters, the same character and the same count, without the info string.
- The first line of an entry starts with its number, so it opens no block, even when the text's first line is a fence run. No closing line is added for it.
- A rendered entry whose blocks are all closed, or that has none, is unchanged.
- `NewEntry.text` and the journal record are unchanged. `entry_text` returns the text as rendered, so for such an entry its last line is the closing run, without the indent.

Tests: `tests/domain/test_journal.py` (new tests beside the existing ones).

## Acceptance criteria

1. `render_entry(2, NewEntry(speaker="tester", kind="result", text="red:\n```\nE   assert 1 == 2"))` is `"2. tester: red:\n   ```\n   E   assert 1 == 2\n   ```"`.
2. The closing run is the opening run. An unclosed opening of four backticks with the info string `python` gets the closing line of four backticks and no info string; an unclosed `~~~~~` gets `~~~~~`; an unclosed run of exactly three gets exactly three.
3. Only the last, unclosed block is closed. A text with a closed `~~~~` block and then an unclosed ```` ``` ```` gets one closing ```` ``` ```` line.
4. A text whose blocks are all closed (`"a\n```\nx\n```"`), a text with no fence (`"a\nb"`), a text whose first line is ```` ``` ```` with nothing after it, and a text with a run of two backticks each render exactly as before (no closing line).
5. After `append_entry` of a human entry, the entry of criterion 1 and a third entry, `check_story_form(document, "# F\n\n## Journal\n", folder="in-progress")` is `[]`. The state has three records, and `entry_text(document, 3)` is the third text.
6. With a `## After` section after `## Journal`, appending the entry of criterion 1 leaves `After` in `[s.heading for s in sections(body)]`.
7. `entry_text` of the entry of criterion 1 is `"red:\n```\nE   assert 1 == 2\n```"`; `entry_text` of an entry without an unclosed fence is still its text as given.
8. `make check` stays green.
9. docs: `docs/project-guide.md`, "The journal's entries": the "Known limit" is replaced by the rule that an entry closes a block its text leaves open, and `entry_text` is described as returning that closing line too.

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
