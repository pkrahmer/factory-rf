# Reading and writing work items

## Assignment (as of log entry 1)

Build the one reader and the one writer of the work item file (R13): a Markdown file with YAML front matter that holds the state of F0002-S0002 and a body that holds the specification and the journal's text. The writer renders the state in one fixed notation with the keys in the order of `WorkItemState`; the reader splits the file with python-frontmatter, reads the front matter with ruamel.yaml, validates it into `WorkItemState` and returns a `WorkItemDocument`, or raises `WorkItemFormatError` with a fault that names the key. A second reading, `parse_specification`, takes a file whose front matter the factory does not own (a story in the backlog) and returns only its body, listing the front matter keys it dropped; this is how a draft's own front matter can never skip a stage (ST6.1). The story covers R13 for this format and R15 (state in the front matter, the body kept as text). The interfaces `WorkItemReader` and `WorkItemWriter` live in `factory.application.files` and the classes in `factory.adapters.work_item_markdown`; wiring comes later.

## Interface

`src/factory/application/files.py`

```python
class WorkItemReader(ABC):
    @abstractmethod
    def parse(self, text: str) -> WorkItemDocument: ...
    @abstractmethod
    def parse_specification(self, text: str) -> WorkItemDocument: ...
    @abstractmethod
    def read(self, path: Path) -> WorkItemDocument: ...

class WorkItemWriter(ABC):
    @abstractmethod
    def render(self, document: WorkItemDocument) -> str: ...
    @abstractmethod
    def write(self, path: Path, document: WorkItemDocument) -> None: ...
```

`src/factory/adapters/work_item_markdown.py`

```python
class RuamelYamlHandler(YAMLHandler):        # frontmatter.default_handlers.YAMLHandler
    @override
    def load(self, fm: str, **kwargs: object) -> dict[str, object]: ...
    @override
    def export(self, metadata: dict[str, object], **kwargs: object) -> str: ...

class FrontmatterWorkItemReader(WorkItemReader):
    def __init__(self) -> None: ...

class FrontmatterWorkItemWriter(WorkItemWriter):
    def __init__(self) -> None: ...
```

The file format; each rule has a criterion below.

- A work item file is a boundary line, the front matter, a boundary line and the body, split as python-frontmatter 1.3.0 splits it. The reader first turns `\r\n` into `\n` and removes the whitespace around the whole text, so blank lines and spaces before the opening line do not count. A boundary line is a line of three or more `-` followed by nothing but whitespace (`YAMLHandler.FM_BOUNDARY`, `^-{3,}\s*$`): `---`, `----` and `--- ` are boundary lines; `--- x`, `- - -` and a later line ` ---` with a leading space are not. Front matter exists only when the prepared text starts with a boundary line and a later line is a boundary line. The front matter is the text between those two lines, and the body is everything after the second.
- python-frontmatter splits the file and ruamel.yaml reads and writes its YAML (R13). `RuamelYamlHandler` subclasses `frontmatter.default_handlers.YAMLHandler`. It keeps that class's boundary and `---` delimiters and overrides only two methods. `load` reads with ruamel.yaml's safe loading: nothing gives `{}`; a mapping is returned with its keys in file order, each key converted with `str(key)` (the key `1` gives `"1"`); YAML that does not load raises `WorkItemFormatError("front matter is not valid YAML")`; any other value raises `WorkItemFormatError("front matter is not a mapping")`. `export` writes the notation below with ruamel.yaml, without a final newline. Both overrides carry `typing.override`, which also keeps ruff's `ARG002` quiet about the unused `kwargs`.

  The reader calls the handler's `detect` on the prepared text, then its `split` (a `ValueError` means the front matter is never closed), then its `load`. It calls neither `frontmatter.parse` nor `frontmatter.loads`, for four reasons. Given a handler, they skip `detect`, so they would take the text between two `---` lines further down a body (two thematic breaks) as front matter and drop what comes before it. They return the whole text when the closing line is missing. They silently drop front matter that is not a mapping. And `loads` raises `TypeError` for a key named `content` or `handler`.

  The writer calls `frontmatter.dumps(frontmatter.Post(<the body with the whitespace around it removed>, None, **<values>), handler=<the handler>)`. The `None` is `Post`'s own handler argument; without it, `mypy --strict` refuses `**` of a `dict[str, object]`. No variable is named `yaml`, because the project's semgrep rule `factory-no-unsafe-yaml-load` matches any `yaml.load(...)`.
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

- Notation: a missing value is written as `null`; an empty list as `[]`; a non-empty `comments_read` as a flow list (`[4, 9]`); `claim` as a mapping with the keys `instance`, `stage`, `started_at`, `lease_duration` in that order, and `claim: null` when there is none; `started_at` as single-quoted text of the UTC time in `isoformat()` form with the trailing UTC offset replaced by `Z`; `journal` as a block list of mappings with the keys `number`, `speaker`, `kind`, and `journal: []` when empty. Every other scalar is unquoted, except that a name (a `stage`, `handed_over`, `instance`, `speaker`) which a YAML reader (YAML 1.1 included) could read back as null or a boolean (`null`, `true`, `false`, `yes`, `no`, `on`, `off`, `y`, `n`) is single-quoted, so the round trip returns the same text (`handed_over: 'true'`).
- `render` writes python-frontmatter's layout and a final newline: `---`, the front matter, `---`, an empty line, the body with the whitespace around it removed, and `\n`. For a body that is empty or only whitespace, the text ends with the closing `---` and `\n`. (`frontmatter.dumps` writes `---\n<front matter>\n---\n\n<body>` and removes the whitespace around the whole result only, not between the closing `---` and the body; so the writer removes the whitespace around the body before it builds the `Post`, and adds the final `\n`.)
- `parse` and `parse_specification` normalise the body as python-frontmatter does: the whitespace around it is removed (blank lines before and after it, spaces at the start of its first line and at the end of its last) and one final newline is added. A body that is empty or only whitespace is `""`. So `parse(render(document))` equals `document` for every document whose body is normalised.
- `parse`: the state is required; only `stage` is required among its keys and the others take their initial values. `ignored_keys` is `[]`.
- Front matter that YAML loads as nothing (empty, blank, only comments, or `null`) is an empty mapping: `parse` then reports `missing key: stage`, and `parse_specification` returns no ignored keys. Front matter that loads as anything else but a mapping is `front matter is not a mapping`.
- `parse` raises `WorkItemFormatError` and its `fault` is exactly or starts with one of: `no front matter`; `front matter is not valid YAML`; `front matter is not a mapping`; `unknown key: <path>`; `missing key: <path>`; `invalid <path>: <reason>`; `invalid state: <reason>`. `<path>` names the value: the top-level key, then each nested key after a dot, and a list position in brackets after the list's key (`attempts`, `claim.extra`, `claim.lease_duration`, `comments_read[0]`, `journal[1].kind`). `missing key` names `stage` or a required key of a claim or a journal record (`claim.instance`). `invalid <path>` is reported for the first invalid value in the order of the fields of `WorkItemState`, and for a rule of one field, at the location the model gives (F0002-S0002: `comments_read`, `journal`); `invalid state` is reported only when every value is valid and a rule that spans keys (the claim's stage against the state's stage) is broken. When several faults exist the first in this order is reported: structure, unknown key, missing key, invalid value, rule that spans keys. Every key that `WorkItemState` does not define is an unknown key.
- `parse_specification` returns `WorkItemDocument(state=None, body=<normalised body>, ignored_keys=<the top-level front matter keys in file order>)`. A text without front matter (a text whose front matter is never closed included) has no ignored keys, and the whole text, normalised like a body, is the body. Front matter that is not valid YAML or not a mapping raises `WorkItemFormatError` with the faults above.
- `read(path)` is `parse` of the file read as UTF-8. A file that cannot be read, a file that is not UTF-8 included, raises `WorkItemFormatError` whose `fault` starts with `cannot read` and whose `path` is `str(path)`; a fault of `parse` is raised again with `path` set to `str(path)`.
- `render` raises `WorkItemFormatError` with the fault `the document has no state` when `state` is `None`. `write(path, document)` writes the text of `render` as UTF-8 with `\n` line ends and replaces an existing file.

Tests: `tests/adapters/test_work_item_markdown.py`.

## Acceptance criteria

1. `render` of a document whose state has every field set as in the example above (with a claim whose `started_at` is a UTC time) and the body `"# T\n"` returns exactly `---`, the front matter of the example with the `started_at` line equal to `  started_at: '` plus `started_at.isoformat()` with the trailing UTC offset replaced by `Z` plus `'`, `---`, an empty line and `# T`, each line ending with `\n`.
2. `render` of `initial_state("intake")` writes all ten keys in field order with `blocked: null`, `pull_request: null`, `handed_over: null`, `claim: null`, the three counters as `0`, `comments_read: []` and `journal: []`.
3. `render` writes a name that a YAML reader could read as null or a boolean in single quotes: a state with `handed_over="true"` and a claim with `instance="null"` gives the lines `handed_over: 'true'` and `  instance: 'null'`, and `parse` gives back the same state; a name such as `approval` stays unquoted.
4. `render` writes an empty line after the closing `---` and then the body with the whitespace around it removed and one final newline: the bodies `"# T\n"`, `"# T"` and `"\n\n# T\n\n\n"` each give a text that ends with `---\n\n# T\n`; for the bodies `""` and `"\n\n"` the text ends with the closing `---` and one `\n`.
5. `render` raises `WorkItemFormatError` with the fault `the document has no state` for a document whose state is `None`.
6. `parse(render(document))` equals `document` for a full document whose normalised body contains a line `---` and a fenced block containing `---`: the body is split off at the closing `---` of the front matter only.
7. `parse` removes the whitespace around the body and keeps one final newline: the text `---\nstage: t\n---\n\n\n  # T\n\nx  \n\n\n` gives the body `"# T\n\nx\n"`; a text with nothing or only blank lines after the closing `---` gives the body `""`.
8. `parse` of a file whose front matter holds only `stage: tests` returns the state `initial_state("tests")`, and `ignored_keys` is `[]`.
9. `parse` raises `WorkItemFormatError` with the fault `no front matter` in three cases. The first is a text whose first non-blank line is not a boundary line (`# T`, `--- x`, `- - -`). The second is a text that starts with `# T` and holds two `---` lines further down (two thematic breaks are not front matter). The third is front matter that is never closed (no later boundary line; a later line ` ---` with a leading space is not one). It raises `front matter is not valid YAML` for `---\nstage: [\n---\n` and `front matter is not a mapping` for a list as front matter.
10. `parse` finds the front matter as python-frontmatter does. Each of these texts gives the state `initial_state("tests")` and the body `"# T\n"`: `\n\n  ---\nstage: tests\n---\n# T\n` (blank lines and spaces before the opening line), `----\nstage: tests\n-----\n# T\n` (longer boundary lines), `---  \nstage: tests\n---\t\n# T\n` (whitespace after a boundary line) and `---\r\nstage: tests\r\n---\r\n# T\r\n` (`\r\n` line ends).
11. `parse` raises `WorkItemFormatError` with the fault `unknown key: colour` for the key `colour`, `unknown key: claim.extra` for an extra key inside a claim and `unknown key: journal[0].extra` for an extra key in a journal record; with an unknown key and a missing `stage` it reports the unknown key.
12. `parse` raises `WorkItemFormatError` with the fault `missing key: stage` when `stage` is absent, and with the fault `missing key: claim.lease_duration` for a claim without `lease_duration`.
13. `parse` of front matter without `stage` and with `attempts: -1` reports `missing key: stage`, not an invalid value.
14. `parse` raises `WorkItemFormatError` with a fault starting with `invalid attempts` for `attempts: -1`, `invalid blocked` for `blocked: asked`, `invalid claim.lease_duration` for a claim with `lease_duration: 0`, `invalid comments_read[0]` for `comments_read: [0]` and `invalid journal[0].kind` for a journal record of the kind `note`; with `blocked: asked` and `attempts: -1` together it reports `invalid blocked`, the first in the order of the state's fields.
15. `parse` raises `WorkItemFormatError` with a fault starting with `invalid comments_read` for `comments_read: [5, 3]`, with `invalid journal` for a journal numbered 1 and 3, and with `invalid state` for a claim whose stage differs from the state's stage; the same claim with `lease_duration: 0` reports `invalid claim.lease_duration`, not `invalid state`.
16. Empty front matter (`---\n---\n# T\n`): `parse` raises `WorkItemFormatError` with the fault `missing key: stage`, and `parse_specification` returns `state` `None`, `ignored_keys` `[]` and the body `# T\n`; front matter that holds only `null`, or only a comment line (`# none`), is read the same way.
17. `parse_specification` of a text with the front matter `stage: tests` and `attempts: 1` returns a document with `state` `None`, `ignored_keys` equal to `["stage", "attempts"]` and the normalised body, so a story that was started with its own `stage` cannot skip a stage; a text with the front matter `1: x` and `stage: tests` returns `ignored_keys` equal to `["1", "stage"]`.
18. `parse_specification` of a text without front matter returns `state` `None`, `ignored_keys` `[]` and the normalised text as body. This includes a text that starts with `# T` and holds two `---` lines further down, which stays whole, and a text whose front matter is never closed. `parse_specification` raises `WorkItemFormatError` for front matter that is not valid YAML and for front matter that is not a mapping.
19. `read(path)` of a file in `tmp_path` returns the same document as `parse` of its text.
20. `read(path)` of a missing file raises `WorkItemFormatError` with a fault starting with `cannot read` and `path` equal to `str(path)`; so does a file whose bytes are not UTF-8 (`b"\xff\xfe"`); of a file with an unknown key it raises the `unknown key` fault with `path` equal to `str(path)`.
21. `write(path, document)` leaves a file whose bytes are the UTF-8 encoding of `render(document)`, with `\n` line ends, replaces a file that exists, and `read(path)` gives back the document.
22. `WorkItemReader` and `WorkItemWriter` are abstract base classes whose every operation is abstract, and `FrontmatterWorkItemReader` and `FrontmatterWorkItemWriter` are subclasses of them. `RuamelYamlHandler` is a subclass of `frontmatter.default_handlers.YAMLHandler` whose `FM_BOUNDARY`, `START_DELIMITER` and `END_DELIMITER` are that class's own. `factory.adapters.work_item_markdown` imports `frontmatter` and `ruamel.yaml`, and no module of `factory.domain`, `factory.application` or `factory.entry` imports either, found by parsing every module's imports with `ast`.
23. make check stays green.
24. docs: `docs/project-guide.md` shows the file format of a work item (the front matter's notation with an example, the body normalisation, the fault messages of the reader) and says that every file format has one reader and one writer class in `factory.adapters`.

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
Expect: fifteen lines: `---`, then `stage: intake`, `blocked: null`, `round: 0`, `attempts: 1`, `crashes: 0`, `pull_request: null`, `comments_read: [4, 9]`, `handed_over: null`, `claim: null`, `journal: []`, then `---`, an empty line, `# Title`, and last `1 [4, 9] '# Title\n'`.

```bash
uv run python -c "
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.domain.errors import WorkItemFormatError
reader = FrontmatterWorkItemReader()
try:
    reader.parse('---\nstage: tests\ncolour: 2\n---\n# T\n')
except WorkItemFormatError as error:
    print(error.fault)
spec = reader.parse_specification('---\nstage: tests\nattempts: 1\n---\n\n\n# T\n')
print(spec.state, spec.ignored_keys, repr(spec.body))
"
```
Expect: two lines: `unknown key: colour`, then `None ['stage', 'attempts'] '# T\n'`.

## Log (append only)

1. 2026-10-12 human: created.
