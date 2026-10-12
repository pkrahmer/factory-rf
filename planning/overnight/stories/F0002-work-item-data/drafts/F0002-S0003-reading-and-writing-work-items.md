# Reading and writing work items

## Assignment (as of log entry 1)

Build the one reader and the one writer of the work item file (R13): a Markdown file with YAML front matter that holds the state of F0002-S0002 and a body that holds the specification and the journal's text. The writer renders the state in one fixed notation with the keys in the order of `WorkItemState`; the reader splits the file, validates the front matter into `WorkItemState` and returns a `WorkItemDocument`, or raises `WorkItemFormatError` with a fault that names the key. A second reading, `parse_specification`, takes a file whose front matter the factory does not own (a story in the backlog) and returns only its body, listing the front matter keys it dropped; this is how a draft's own front matter can never skip a stage (ST6.1) and how F0006 can tell a v1 work item (R26). The story covers R13 for this format and R15 (state in the front matter, the body kept as text). The interfaces `WorkItemReader` and `WorkItemWriter` live in `factory.application.files` and the classes in `factory.adapters.work_item_markdown`; wiring comes later.

## Interface

`src/factory/application/files.py`

```python
class WorkItemReader(Protocol):
    def parse(self, text: str) -> WorkItemDocument: ...
    def parse_specification(self, text: str) -> WorkItemDocument: ...
    def read(self, path: Path) -> WorkItemDocument: ...

class WorkItemWriter(Protocol):
    def render(self, document: WorkItemDocument) -> str: ...
    def write(self, path: Path, document: WorkItemDocument) -> None: ...
```

`src/factory/adapters/work_item_markdown.py`

```python
class FrontmatterWorkItemReader:        # satisfies WorkItemReader structurally, no inheritance
    def __init__(self) -> None: ...

class FrontmatterWorkItemWriter:        # satisfies WorkItemWriter structurally, no inheritance
    def __init__(self) -> None: ...
```

The file format; each rule has a criterion below.

- A work item file is a line `---`, the front matter, a line `---`, and the body. Front matter exists only when the first line of the text is `---` and a later line is `---`.
- The writer always writes all ten keys, in the order of the fields of `WorkItemState`. This is the front matter of a state with every field set, between the two `---` lines of the file:

```yaml
---
stage: doing
blocked: question
round: 1
attempts: 2
crashes: 0
pull_request: 12
comments_read: [4, 9]
handed_over: approval
claim:
  instance: factory-1
  stage: doing
  started_at: '<the start time in UTC, as isoformat() with the trailing UTC offset written as Z>'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
- number: 2
  speaker: factory
  kind: started
---
```

- Notation: a missing value is written as `null`; an empty list as `[]`; a non-empty `comments_read` as a flow list (`[4, 9]`); `claim` as a mapping with the keys `instance`, `stage`, `started_at`, `lease_duration` in that order, and `claim: null` when there is none; `started_at` as single-quoted text of the UTC time in `isoformat()` form with the trailing UTC offset replaced by `Z`; `journal` as a block list of mappings with the keys `number`, `speaker`, `kind`, and `journal: []` when empty. Every other scalar is unquoted.
- `render` writes `---`, the front matter, `---` and then the body unchanged, adding a final newline when the body is not empty and lacks one.
- `parse` and `parse_specification` normalise the body: leading blank lines are dropped, trailing blank lines are dropped and one final newline is kept; a text with nothing after the front matter has the body `""`.
- `parse`: the state is required; only `stage` is required among its keys and the others take their initial values. `ignored_keys` is `[]`.
- `parse` raises `WorkItemFormatError` and its `fault` is exactly or starts with one of: `no front matter`; `front matter is not valid YAML`; `front matter is not a mapping`; `unknown key: <key>` (a nested key is written with dots, `claim.extra`); `missing key: stage`; `invalid <key>: <reason>`, where `<key>` is the first key of the offending value, or `invalid state: <reason>` for a rule that spans keys. When several faults exist the first in this order is reported: structure, unknown key, missing key, invalid value. v1's key `comments_seen` is an unknown key like any other.
- `parse_specification` returns `WorkItemDocument(state=None, body=<normalised body>, ignored_keys=<the top-level front matter keys in file order>)`. A text without front matter has no ignored keys and the whole text is the body. Front matter that is not valid YAML or not a mapping raises `WorkItemFormatError` with the faults above.
- `read(path)` is `parse` of the file read as UTF-8. A file that cannot be read raises `WorkItemFormatError` whose `fault` starts with `cannot read` and whose `path` is `str(path)`; a fault of `parse` is raised again with `path` set to `str(path)`.
- `render` raises `WorkItemFormatError` with the fault `the document has no state` when `state` is `None`. `write(path, document)` writes the text of `render` as UTF-8 with `\n` line ends and replaces an existing file.

Tests: `tests/adapters/test_work_item_markdown.py`.

## Acceptance criteria

1. `render` of a document whose state has every field set as in the example above (with a claim whose `started_at` is a UTC time) returns exactly `---`, the front matter of the example with the `started_at` line equal to `  started_at: '` plus `started_at.isoformat()` with the trailing UTC offset replaced by `Z` plus `'`, `---`, and the body.
2. `render` of `initial_state("intake")` writes all ten keys in field order with `blocked: null`, `pull_request: null`, `handed_over: null`, `claim: null`, the three counters as `0`, `comments_read: []` and `journal: []`.
3. `render` writes the body unchanged, adds a final newline to a non-empty body that lacks one, and adds nothing after the closing `---` for the body `""`.
4. `render` raises `WorkItemFormatError` with the fault `the document has no state` for a document whose state is `None`.
5. `parse(render(document))` equals `document` for a full document whose normalised body contains a line `---` and a fenced block containing `---`: the body is split off at the closing `---` of the front matter only.
6. `parse` drops leading blank lines of the body, drops trailing blank lines and keeps exactly one final newline; for a text with nothing after the closing `---` the body is `""`.
7. `parse` of a file whose front matter holds only `stage: tests` returns the state `initial_state("tests")`, and `ignored_keys` is `[]`.
8. `parse` raises `WorkItemFormatError` with the faults `no front matter` (for a text whose first line is not `---`, and for one whose front matter is never closed), `front matter is not valid YAML` and `front matter is not a mapping` (a list as front matter).
9. `parse` raises `WorkItemFormatError` with the fault `unknown key: comments_seen` for v1's key, and `unknown key: claim.extra` for an extra key inside a claim; with several faults it reports the unknown key before a missing `stage`.
10. `parse` raises `WorkItemFormatError` with the fault `missing key: stage` when `stage` is absent, and with a fault starting with `invalid attempts` for `attempts: -1`, `invalid blocked` for `blocked: asked`, and a fault starting with `invalid` for each rule that spans values: `comments_read: [5, 3]`, a journal numbered 1 and 3, and a claim whose stage differs from the state's stage.
11. `parse_specification` of a text with the front matter `stage: tests` and `attempts: 1` returns a document with `state` `None`, `ignored_keys` equal to `["stage", "attempts"]` and the normalised body, so a story that was started with its own `stage` cannot skip a stage.
12. `parse_specification` of a text without front matter returns `state` `None`, `ignored_keys` `[]` and the normalised text as body; it raises `WorkItemFormatError` for front matter that is not valid YAML and for one that is not a mapping.
13. `read(path)` of a file in `tmp_path` returns the same document as `parse` of its text.
14. `read(path)` of a missing file raises `WorkItemFormatError` with a fault starting with `cannot read` and `path` equal to `str(path)`; of a file with an unknown key it raises the `unknown key` fault with `path` equal to `str(path)`.
15. `write(path, document)` leaves a file whose bytes are the UTF-8 encoding of `render(document)`, with `\n` line ends, replaces a file that exists, and `read(path)` gives back the document.
16. `FrontmatterWorkItemReader` and `FrontmatterWorkItemWriter` are not subclasses of their protocols, and the tests annotate the instances as `WorkItemReader` and `WorkItemWriter`, so `make check` (mypy) proves they satisfy them; no module of `factory.domain`, `factory.application` or `factory.entry` imports `frontmatter`, found by parsing every module's imports with `ast`.
17. make check stays green.
18. docs: `docs/project-guide.md` shows the file format of a work item (the front matter's notation with an example, the body normalisation, the fault messages of the reader) and says that every file format has one reader and one writer class in `factory.adapters`.

## Demo

```bash
uv run python -c "
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.domain.work_item import WorkItemDocument, initial_state
state = initial_state('intake').model_copy(update={'attempts': 1, 'comments_read': [4, 9]})
text = FrontmatterWorkItemWriter().render(WorkItemDocument(state=state, body='# Title\n'))
print(text, end='')
back = FrontmatterWorkItemReader().parse(text)
print(back.state.attempts, back.state.comments_read, repr(back.body))
"
```
Expect: fourteen lines: `---`, then `stage: intake`, `blocked: null`, `round: 0`, `attempts: 1`, `crashes: 0`, `pull_request: null`, `comments_read: [4, 9]`, `handed_over: null`, `claim: null`, `journal: []`, then `---`, `# Title`, and last `1 [4, 9] '# Title\n'`.

```bash
uv run python -c "
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.domain.errors import WorkItemFormatError
reader = FrontmatterWorkItemReader()
try:
    reader.parse('---\nstage: tests\ncomments_seen: 2\n---\n# T\n')
except WorkItemFormatError as error:
    print(error.fault)
spec = reader.parse_specification('---\nstage: tests\nattempts: 1\n---\n\n\n# T\n')
print(spec.state, spec.ignored_keys, repr(spec.body))
"
```
Expect: two lines: `unknown key: comments_seen`, then `None ['stage', 'attempts'] '# T\n'`.

## Log (append only)

1. 2026-10-12 human: created.
