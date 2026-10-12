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

- `NewEntry.text` is stripped of surrounding whitespace and must not be blank afterwards; `on` is required when the speaker is `human` and refused for any other speaker.
- `render_entry(number, entry)` is `"<number>. "`, then `"<YYYY-MM-DD> "` exactly when `on` is set, then `"<speaker>: "`, then the text. The speaker is shown as its name. Every line of the text after the first is indented by `len("<number>. ")` spaces, so by 3 spaces for the numbers 1 to 9, by 4 for 10 to 99 and by 5 for 100 to 999; a blank line stays empty. There is no final newline.
- `append_entry` raises `WorkItemFormatError` with the fault `the document has no state` when `state` is `None` and with the fault `missing section: ## Journal` when the body has no `Journal` section outside a code fence. Otherwise it returns a document whose state is the old state with one more record, `JournalRecord(number=len(old journal) + 1, speaker=..., kind=...)`, and whose body has the rendered entry placed on the lines after the last non-blank line of the `Journal` section, or after one blank line under the heading when the section has no text. Entries follow one another with no blank line between them. Nothing else changes: not the other state fields, not `ignored_keys`, not another line of the body, and the result ends with a newline exactly when the body did. The input document is not changed.
- `entry_text(document, number)` finds the entry that starts with `"<number>. "` at column 0 in the `Journal` section and returns its text as it was given to `NewEntry`: the entry's lines up to the next line that starts with a number at column 0 or the end of the section, without trailing blank lines, with everything up to and including the first `": "` of the first line removed and the indent removed from the other lines. It raises `WorkItemFormatError` with the fault `missing section: ## Journal` or `no journal entry <number>`. It reads neither speaker, kind nor cost from the text and is for display only.
- `last_record(document, speaker=..., kind=...)` is the last record of `state.journal` that matches every filter given, or `None`; with no filter it is the last record. It raises `WorkItemFormatError` with the fault `the document has no state` when `state` is `None`.
- `restore_state_and_journal(current, baseline)` returns a document with the baseline's whole state; with a body that is the current body in which the first `Journal` section, from its heading line to its last non-blank line, is replaced by the baseline's first `Journal` section taken the same way; the lines between that block and the next section stay as they are in the current body; and with the current `ignored_keys`. When the current body has no `Journal` section, the baseline's block is added at the end of the body after one blank line and the body ends with a newline. It raises `WorkItemFormatError` with the fault `the document has no state` when the baseline's state is `None` and with `missing section: ## Journal` when the baseline's body has no `Journal` section.

Tests: `tests/domain/test_journal.py`, `tests/adapters/test_journal_as_data.py`.

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
18. make check stays green.
19. docs: `docs/project-guide.md` explains the journal: the visible format with its continuation indent, that only the human's entries are dated, that speaker and kind are data in the front matter and are never read from the text, and what the restore does; `docs/decisions.md` records why the journal's data sits in the front matter.

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
