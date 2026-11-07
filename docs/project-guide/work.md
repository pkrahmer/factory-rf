# Work items

This file covers the identity, data, files, sections and form of a [work item](glossary.md). Read the index, [README.md](README.md), first.

## Identity, order and places of work items

A work item has an id, a place in the order and a place in the repository. Two pure modules give them: [identifiers.py](../../src/factory/shared/domain/identifiers.py) (`factory.shared.domain.identifiers`) for the ids and [paths.py](../../src/factory/shared/domain/paths.py) (`factory.shared.domain.paths`) for the names of the project's `factory/` tree. Neither reads a file, the clock or a process. A test parses their imports.

    WorkItemId, FeatureId, Name
    is_name(text) -> bool
    parse_work_item_file_name(text) -> WorkItemFileName | None
    parse_feature_directory_name(text) -> FeatureDirectoryName | None
    work_item_order(id) -> tuple[str, int, str]
    branch_name(id) -> str
    work_item_of_branch(branch) -> WorkItemId | None
    work_item_path(feature_directory, folder, file_name) -> str
    cost_records_path(path) -> str
    folder_of(path) -> LifecycleFolder | None

- `WorkItemId` is `F0001-S0001` for a story or `F0001-A0001` for an [acceptance](glossary.md). `FeatureId` is `F0001`. `Name` is lower-case letters, digits and hyphens, starting with a letter.
- `is_name(text)` is `True` exactly when `Name` accepts `text`. The agent readers use it to check an agent's name.
- A work item file is `<id>.md` or `<id>-<slug>.md`. A [feature](glossary.md) directory is `<id>` or `<id>-<slug>`.
- A slug is lower-case segments of letters and digits joined by single hyphens. `2fa` and `a-b` are slugs. `Bad`, `a-`, `-a` and `a--b` are not.
- `parse_work_item_file_name` and `parse_feature_directory_name` return `None` for any other string. They never raise.
- `is_acceptance`, `feature_of`, `work_item_order` and `branch_name` raise `ValueError` for a string that is not a `WorkItemId`.
- The branch of a work item is `work-item/<id>`, never the file name, so a slug cannot change it. `work_item_of_branch` gives the id back for exactly that form and `None` for anything else.
- `work_item_order(id)` is the sort key `(feature id, 0 for a story or 1 for an acceptance, id)`. Sorted by it, the features come in plain string order and every story of a feature comes before its acceptances. The slug is not part of the id, so it never changes the order.
- Use this key wherever work items are listed or picked. Plain string order alone would put `F0002-A0001` before `F0002-S0001`. The reason it is a key is in [decisions.md](../decisions.md).
- `work_item_path(feature_directory, folder, file_name)` is `factory/features/<feature_directory>/<folder>/<file_name>`.
- `cost_records_path(path)` replaces the final `.md` with `.costs.jsonl`, so the sidecar sits beside the work item. A path that does not end in `.md` is a `ValueError`.
- `folder_of(path)` returns the lifecycle folder of a work item path and `None` for anything else. A work item path is exactly `factory/features/<feature directory>/<folder>/<file>`. The directory parses as a feature directory name, the folder is a lifecycle folder and the file parses as a work item file name (an acceptance file too).
- So a sidecar, a `.gitkeep`, a `README.md`, a folder such as `drafts` or `ongoing` and a path one level too deep or too shallow all give `None`.

The commands in this file run in the project's environment. From a plain shell, write `uv run python` for `python`.

```console
$ python -c "from factory.shared.domain.identifiers import parse_work_item_file_name, work_item_order; ids = [parse_work_item_file_name(n).id for n in ['F0002-A0001.md', 'F0002-S0002-2fa.md', 'F0002-S0001.md', 'F0001-S0010-x.md']]; print(sorted(ids, key=work_item_order))"
['F0001-S0010', 'F0002-S0001', 'F0002-S0002', 'F0002-A0001']
```

See also: *The tree* in the Reference below for every constant of `paths`.

## The data of a work item

A work item file is a front matter and a body. Three pure domain modules hold the front matter's data as frozen Pydantic models that refuse unknown fields. None reads or writes a file. Every rule with one right answer is a validation of these types, so the reader and the writer only translate.

[work_item.py](../../src/factory/work/domain/work_item.py) holds `factory.work.domain.work_item.WorkItemState` (the front matter), its `Claim`, `WorkItemDocument` and the snapshots. [journal.py](../../src/factory/work/domain/journal.py) holds the journal's records and entries. [acceptance.py](../../src/factory/work/domain/acceptance.py) holds the acceptance's data.

### The state

    initial_state(first_stage) -> WorkItemState
    require_state(document, error) -> WorkItemState
    WorkItemDocument(state, body, ignored_keys=[])

- `WorkItemState` has ten fields, in the order they are written: `stage`, `blocked`, `round`, `attempts`, `crashes`, `pull_request`, `comments_read`, `handed_over`, `claim` and `journal`. The Reference lists their types and initial values.
- `initial_state(first_stage)` is `WorkItemState(stage=first_stage)`. A `first_stage` that is not a `Name` raises `pydantic.ValidationError`.
- `comments_read` ascends with no repeats.
- A [claim](glossary.md) is for the state's own `stage`.
- The `journal`'s numbers are 1, 2, 3 up to n in order.
- The first two rules are validations of their own field, so their error is located at that field (`("comments_read",)`, `("journal",)`). The claim rule spans two fields, so its error has an empty location (`()`). The work item reader names a fault by that location.
- `WorkItemDocument` pairs a state with the body text. `state` is required but may be `None`, for a file read as a specification. `ignored_keys` lists front matter keys the reader did not use.
- `require_state(document, error)` is the one way to get a document's state when it must be there. It returns `document.state`, or raises `error`, the very instance passed, when the state is `None`.
- The caller builds the exception it wants (a `ValueError`, a `CannotHandle`, a `WorkItemFormatError`), so a module keeps its own message.
- Write no private `_state_of` and no `if state is None: raise` of your own. [test_no_state_copies.py](../../tests/guards/test_no_state_copies.py) searches `src/factory` for both. The one exception is the journal module, which keeps a private `_state_of` (see *The journal's entries*).
- `factory.shared.domain.errors.WorkItemFormatError(fault, path=None)` is the `FactoryError` for a work item file that cannot be read. Both are attributes. The message is `fault`, or `<path>: <fault>` with a path. The error type is in [errors.py](../../src/factory/shared/domain/errors.py).

```console
$ python -c "from factory.work.domain.work_item import initial_state; print(initial_state('intake').model_dump())"
{'stage': 'intake', 'blocked': None, 'round': 0, 'attempts': 0, 'crashes': 0, 'pull_request': None, 'comments_read': [], 'handed_over': None, 'claim': None, 'journal': []}
```

### The claim

A `Claim` is an [instance](glossary.md)'s hold on a work item.

- `Claim` has `instance` and `stage` (both `Name`), `started_at` and `lease_duration` in minutes (at least 1).
- `started_at` must carry a time zone and is stored in UTC.
- `UtcDatetime` in [times.py](../../src/factory/shared/domain/times.py) (`factory.shared.domain.times`) converts an aware time to the same instant in UTC. It is the one way a model converts a time. Give every new time field that type and write no validator of your own.

### The journal's data

Every [journal](glossary.md) entry has a record in the front matter, beside its text in the body. So the speaker and the kind of an entry are data, not text.

    JournalRecord(number, speaker, kind, at=None, stage=None, run=None, blocked=None, reason=None)

- `number` is 1 or more. `speaker` is a `Name`; `HUMAN` is `"human"` and `FACTORY` is `"factory"`.
- `JournalKind` is one of `created`, `started`, `result`, `question`, `comment`, `close`, `stall`, `crash`, `expiry`, `move_back`, `send_back`, `done`.
- `at`, `stage`, `run`, `blocked` and `reason` are optional with the default `None`. A reader accepts each alone. Nothing ties `at`, `stage` and `run` to one another.
- `at` is an aware time stored in UTC; a naive time is refused.
- A record carries `blocked` only if its kind is `question`, and `reason` only if its kind is `stall`. Either on another kind, or a value outside its type, is refused with a `ValueError`.
- `Blocked` and `StallReason` are defined in `factory.work.domain.journal`. `factory.work.domain.work_item.Blocked` and `factory.work.domain.decisions.StallReason` ([decisions.py](../../src/factory/work/domain/decisions.py)) are the same types by assignment.
- The work item writer leaves an unset field out of the front matter.
- Every entry the factory appends carries `at` and `stage`, and `run` when it came from a run. The time comes from the factory's `Clock` (`boundaries.clock`; the claim's `started_at` for `started`), because the domain has no clock of its own. The [stage](glossary.md) comes from the state the entry is appended to.
- These places write `blocked`: the agent's own question and the factory's question of a move (`question`, or `round_cap` past the [round cap](glossary.md)), the ask handler at the [attempts cap](glossary.md) (`attempts_cap`), the recovery at the crash cap after a [`crash`](glossary.md) or an `expiry` (`crash_cap`), and a close at the [approval](glossary.md) that sends the story back with a question (`send_back`).
- `StallService` writes `reason` on every [`stall`](glossary.md) record. The `crash` and `expiry` records carry no reason: they are not stalls, and what follows from them is the crash cap's question, which carries `blocked`.
- The status map reads these fields from the front matter and never parses the entry text.
- A run is carried by the [role](glossary.md)'s entry at a stage's end, the factory's `question` of that move, and a `stall` that has a cost record (a red check, a new form finding). All other entries have `run` `None`.
- Two entries carry a stage that is not the one the work item ends in. A `move_back` entry carries the stage the human set, because it is appended before the move back. A story's `done` entry carries the stage it was merged in, because `_archived` appends before it sets `done`. The acceptance's `done` entry carries `done`, since its booking sets the stage first.

### The journal's entries

The journal is two halves that always match. The visible half is Markdown in the body under `## Journal`. The data half is the front matter's `journal` list.

    append_entry(document, NewEntry(...), at=..., run=..., **causes) -> WorkItemDocument
    last_record(document, speaker=..., kind=...) -> JournalRecord | None
    entry_text(document, number) -> str
    restore_state_and_journal(current, baseline) -> WorkItemDocument

- `append_entry` writes both halves in one call, so the number of records equals the number of entries. The input document is not changed. The result ends with a newline exactly when the body did.
- `at` and `run` are keyword-only and optional. `blocked` and `reason` are the optional causes, passed as `**causes: Unpack[JournalCauses]`, a `TypedDict`, because ruff's `PLR0913` refuses two more parameters. They go into the new record as given, with or without `at`.
- Given `at`, the new record carries it, the `stage` of the document's state and `run`. Without `at` it carries none of the three.
- A `run` without `at` raises `ValueError("an entry with a run needs the time it was written")` before anything else, also for a document with no state.
- The rendered entry shows no time, stage or run.
- An entry is `<number>. <speaker>: <text>`. Only the human's entries are dated: `<number>. <YYYY-MM-DD> human: <text>`. `NewEntry` requires `on` for the speaker `human` and refuses it for any other. The text is stripped and must not be blank.
- Lines after the first are indented by the width of `"<number>. "`: 3 spaces for 1 to 9, 4 for 10 to 99, 5 for 100 to 999. A blank line stays empty.
- An entry whose text leaves a code block open gets one more line that closes it: the indent and the opening run, the same character and count, without the info string. A text ending in an unclosed four-backtick `python` block gets a closing line of four backticks. The numbered first line opens no block, so a fence there does not count.
- Without that line an open fence would hide the later entries and the sections after the journal, and the form check would report a valid work item as damaged.
- `NewEntry.text` and the journal records stay as given.
- Entries follow one another with no blank line between them, directly after the last non-blank line of the section, or one blank line under the heading when the section is empty. So a section after the journal keeps its blank line.
- Code that needs to know who spoke or what kind an entry is reads the state with `last_record`, which returns the last record that matches every filter given, or `None`. Nothing reads them from the text, so changing how a speaker is displayed (`intake:` to `Intake Agent:`) changes no record.
- `entry_text(document, number)` returns an entry's text as rendered, a closing fence line included (without its indent), for display only. It finds the line that starts with `"<number>. "` at column 0 and ends the entry at the next line that starts with a number at column 0. So an indented `2. ...` inside a text is not an entry.
- `restore_state_and_journal(current, baseline)` undoes an agent's tampering with state and journal. It returns the current document with the baseline's whole state and the baseline's `Journal` section (from its heading to its last non-blank line) put in place of the current one.
- Edits elsewhere in the body, the blank lines before the next section and the current `ignored_keys` stay. If the current body has no `Journal` section, the baseline's is added at the end after one blank line.
- Faults are `WorkItemFormatError`: `the document has no state` (for `append_entry`, `last_record` and a baseline without state), `missing section: ## Journal` and, for `entry_text`, `no journal entry <number>`.
- `factory.work.domain.work_item` imports `JournalRecord` from `factory.work.domain.journal`. So the journal module imports `work_item` only under `TYPE_CHECKING` and builds documents with `model_copy`. For the same reason it cannot use `require_state`, so it keeps its own private `_state_of`, the one other function that checks a document's state. Either module can be imported first.

```console
$ python -c "from datetime import date; from factory.work.domain.journal import NewEntry, append_entry, entry_text, last_record; from factory.work.domain.work_item import WorkItemDocument, initial_state; doc = WorkItemDocument(state=initial_state('intake'), body='# T\n\n## Journal\n'); doc = append_entry(doc, NewEntry(speaker='human', kind='created', text='created.', on=date(2026, 10, 12))); doc = append_entry(doc, NewEntry(speaker='intake', kind='result', text='accepted\nEvery criterion is testable.')); print(doc.body, end=''); print(last_record(doc, speaker='intake')); print(entry_text(doc, 2))"
# T

## Journal

1. 2026-10-12 human: created.
2. intake: accepted
   Every criterion is testable.
number=2 speaker='intake' kind='result' at=None stage=None run=None blocked=None reason=None
accepted
Every criterion is testable.
```

### The feature acceptance

A feature acceptance is a work item beside the stories, with its own report file and its own [cost records](glossary.md). A later acceptance never overwrites an earlier report. The data is in `factory.work.domain.acceptance`, which does no I/O. The reading and the opening are in [acceptance_reading.py](../../src/factory/work/application/acceptance_reading.py) and [acceptance.py](../../src/factory/work/application/acceptance.py), the modules `factory.work.application.acceptance_reading` and `factory.work.application.acceptance`.

    acceptance_id(feature, number) -> WorkItemId
    next_acceptance_id(feature, existing) -> WorkItemId
    acceptance_file_name(id) -> str
    acceptance_status(files, reports) -> AcceptanceStatus
    AcceptanceReader(boundaries, definition).read() / .snapshots() / .due_features() / .fill_board(rows)
    AcceptanceService(boundaries, definition).open(feature) / .facts(feature)
    AcceptanceHandOver(boundaries, definition).handle(event)
    SplitByWorkItemKind(story, acceptance).handle(event)

- The id is `F0001-A0001`: the feature id, `-A` and a four-digit number, numbered per feature. `acceptance_id` takes 1 to 9999 and raises `ValueError` for any other number.
- `next_acceptance_id(feature, existing)` looks only at the feature's own acceptances in `existing`. It adds one to the highest number, does not fill a gap, and raises `ValueError` at 9999.
- `acceptance_file_name("F0001-A0004")` is `F0001-A0004-acceptance.md`. The slug is `ACCEPTANCE_SLUG`, `acceptance`. A story id raises `ValueError`. `parse_work_item_file_name` reads the name back to the id and that slug.
- An acceptance sorts after every story of its feature, also when the feature directory's slug starts with a digit (`F0002-2fa`) or is missing (`F0002`).
- `AcceptanceState` subclasses `WorkItemState` and adds `stories` (the archived story ids the report covers, strictly ascending, default `[]`) and `outcome` (`accepted`, `refused` or `None`). `outcome` is set exactly when the stage is `done`.
- The reader returns an `AcceptanceState` when the front matter has a `stories` or an `outcome` key, and a plain `WorkItemState` otherwise. A story that carries either key is therefore read as an acceptance. Any other unknown key is still a `WorkItemFormatError`.
- `stories` and `outcome` belong to the factory, like the rest of the state. `append_entry` keeps the state's type, and `restore_state_and_journal` puts the baseline's `stories` and `outcome` back after every agent run.
- `acceptance_status(files, reports)` is pure. It takes `FeatureFiles` and `ReportFacts` and returns the first applicable of `in_flight`, `merged_unrecorded`, `incomplete`, `accepted` or `refused`, and `due`. The rules are in *When a feature acceptance is due* in [operator-guide/work-items.md](../operator-guide/work-items.md).
- `AcceptanceService.open(feature)` opens a feature whose status is `due`. Any other status raises `CannotHandle` and changes nothing. It writes one file, the report head, on the branch `work-item/<acceptance id>`, and pushes.
- The opening opens no pull request, writes no claim and runs no agent. The stage protocol meets the branch as an ordinary work item at the acceptance stage and starts its journal with `started`.
- `AcceptanceHandOver` follows the story hand-over step for step. It sets the description with `acceptance_description`, marks the pull request ready, posts the cost table and records `handed_over`.
- `SplitByWorkItemKind(story, acceptance)` passes an event to `acceptance` when its work item's id is an acceptance's and to `story` otherwise. It raises `CannotHandle(kind, "no work item")` for an event without a work item.
- `AcceptanceService.facts(feature)` reads `origin/main` only and returns the facts the reviewer is told. The facts are computed by code, not by the agent. `TaskComposer.compose` appends them to the reviewer's task.
- The reviewer writes only what the role of `acceptance_stage` may write: its own report and new stories in the feature's `backlog/`. It cannot write `done/`, `feature.md`, another feature or code.
- Each report has its own sidecar, `cost_records_path` of the report. So `BillService(...).for_work_item(<acceptance id>).line` counts only that acceptance's records.

See also: *The remote's work items* below; the Reference for the full rules of the reader, the opening, the hand-over and the facts.

### The remote's work items

`WorkItemSnapshot` and `StoryFile` in `factory.work.domain.work_item` are what the remote shows. Both are frozen and refuse unknown keys. `RemoteWorkItems` in [work_items.py](../../src/factory/work/application/work_items.py) (`factory.work.application.work_items`) reads them.

    StoryFile(id, path, feature_directory, file_name, folder)
    WorkItemSnapshot(id, path, folder, branch, branch_commit, document)
    RemoteWorkItems(git, reader).list_stories(folder)
    RemoteWorkItems(git, reader).read(definition)

- A `StoryFile` is one story file on `origin/main`. A `WorkItemSnapshot` is one work item: `branch` is `branch_name(id)`, `branch_commit` the head of `origin/<branch>` or `None` when the branch does not exist, and `document` the state and body.
- `RemoteWorkItems` reads only remote-tracking refs through `Git.list_files`, `resolve` and `show_file`. It never reads a local branch or the work tree. It does not fetch: the caller does, first.
- `list_stories(folder)` lists the story files of one lifecycle folder on `origin/main`, in `work_item_order`, then path.
- A story file is a path for which `folder_of` is not `None`, whose file name's feature id equals its directory's, and whose id is not an acceptance. Anything else is ignored: `.gitkeep`, `feature.md`, deeper files and any path that `folder_of` refuses.
- `read(definition)` returns one snapshot per story file in `in-progress/`, in the same order. Two files with one id give two snapshots. `backlog/` and `done/` are never read.
- With a branch, the document is `reader.parse` of the story file at `origin/work-item/<id>`, even when that branch is an ancestor of `origin/main` (see [decisions.md](../decisions.md)). A stale local branch of the same name has no influence.
- Without a branch, the story has just been started by the human's move into `in-progress/`. Its document is `initial_state(definition.first_stage())` with the body and `ignored_keys` of `parse_specification` on `origin/main`. State fields in that file are not applied; they are listed in `ignored_keys`.
- A story file missing at its branch tip, or a text the reader refuses on the branch or on `origin/main`, raises `WorkItemFormatError` with `path` set to the story's path. `GitError` from `Git` passes through.

### The records contract

The records contract names the records that readers outside the factory may rely on. It lives in [contract.py](../../src/factory/shared/domain/contract.py) (`factory.shared.domain.contract`). The committed schemas are generated from it by [contract.py](../../src/factory/entry/contract.py) (`factory.entry.contract`).

    CONTRACT: tuple[ContractEntry, ...]
    schema_file_name(entry) -> str
    contract_schema(entry) -> str
    write_contract(folder) -> list[Path]

- `CONTRACT` is a tuple of five `ContractEntry(name, model, mode)`: `work-item-state` (`WorkItemState`), `acceptance-state` (`AcceptanceState`), `cost-record` (`CostRecord`) and `stop-record` (`StopRecord`) in `serialization` mode, and `pipeline-definition` (`PipelineDefinition`) in `validation` mode, since the human writes it.
- `ContractEntry` is a frozen dataclass, not a model, because it holds a class. [test_model_configuration.py](../../tests/guards/test_model_configuration.py) does not see it.
- The files are committed in `src/factory/contract/`, one `<name>.schema.json` for each entry.
- A change to one of the five models, its docstrings and field descriptions included, regenerates the schemas in the same story, through the command and never by hand.
- [test_contract.py](../../tests/entry/test_contract.py) (`test_the_committed_schemas_are_the_generated_ones`) writes the schemas into a temporary folder and compares them with the committed files byte for byte. It also checks that the folder holds nothing else.
- The reviewer checks the version rule: a change that can break a reader raises the major version, an added optional field or value the minor (see [decisions.md](../decisions.md)).
- The version is `RECORDS_CONTRACT`, separate from the [pipeline definition](glossary.md)'s `contract` (`CONTRACT_MAJOR`).

The command writes the schemas into a folder, the committed one when none is given:

```console
$ python -m factory.entry.contract schemas
contract: 5 schemas written
```

See also: *Cost records* in [watching.md](watching.md); the Reference for the schema text and the command's exit status.

## Reading and writing a work item file

Every file format the factory owns has one reader class and one writer class in the `adapters` layer of its area, behind an interface in the `application` layer. They validate into Pydantic DTOs, and no other module parses or renders that format.

For the work item file the interfaces are `WorkItemReader` and `WorkItemWriter` in [files.py](../../src/factory/shared/application/files.py) (`factory.shared.application.files`). The classes are `FrontmatterWorkItemReader` and `FrontmatterWorkItemWriter` in [work_item_markdown.py](../../src/factory/work/adapters/work_item_markdown.py) (`factory.work.adapters.work_item_markdown`).

    reader.parse(text) -> WorkItemDocument
    reader.parse_specification(text) -> WorkItemDocument
    reader.read(path) -> WorkItemDocument
    writer.render(document) -> str
    writer.write(path, document) -> None

- `work_item_markdown.py` is the only module that imports `frontmatter` (python-frontmatter) or `ruamel.yaml`.
- Wiring builds both. [wiring.py](../../src/factory/entry/wiring.py) (`factory.entry.wiring`) `build_work_item_reader` returns `FrontmatterWorkItemReader` for the check command, and `build_boundaries` builds `FrontmatterWorkItemWriter` as `work_item_writer`.
- `parse` returns the state and the normalised body. The state is required.
- `parse_specification` returns `state=None`, the body and `ignored_keys`. Use it for a file whose front matter the factory does not own, such as a story in the [backlog](glossary.md), so its own `stage` can never skip a stage.
- `read` is `parse` of the file read as UTF-8. `write` writes `render` as UTF-8 with `\n` line ends, replacing an existing file.
- A file is a boundary line, the front matter, a boundary line and the body. The reader first turns `\r\n` into `\n` and strips the whitespace around the whole text.
- A boundary line is three or more `-` and nothing else but whitespace: `---`, `----` and `--- ` are boundaries. `--- x`, `- - -` and an indented ` ---` are not.
- Front matter exists only when the text starts with a boundary line and a later line is one. Two `---` lines further down a body are thematic breaks, not front matter.
- The writer always writes all ten keys of `WorkItemState`, in field order. An `AcceptanceState` adds `stories` and `outcome` after `journal`, and a plain state gets neither.
- `render` writes `---`, the front matter, `---`, an empty line, the body stripped of the whitespace around it, and a final `\n`. An empty body ends the text at the closing `---` and `\n`.
- `parse` and `parse_specification` strip the body the same way and add one final newline. An empty or blank body is `""`. So `parse(render(document))` equals `document` when the body is normalised.
- `parse` raises `WorkItemFormatError` with a `fault` that is, or starts with, one of those in the table below. The first applicable in this order is reported: structure, unknown key, missing key, invalid value, rule across keys.
- A `<path>` is the top-level key, then nested keys after dots, and a list position in brackets: `attempts`, `claim.extra`, `comments_read[0]`, `journal[1].kind`.
- `parse_specification` raises only `front matter is not valid YAML` and `front matter is not a mapping`. A text with no front matter is a body with no ignored keys.
- `read` raises `WorkItemFormatError` with `path` set to `str(path)`: `cannot read: <reason>` for a file that is missing or not UTF-8, otherwise the fault of `parse`.
- `render` raises `the document has no state` for a document whose `state` is `None`.

| Fault | When |
|---|---|
| `no front matter` | no opening boundary line, or front matter never closed |
| `front matter is not valid YAML` | the YAML does not load |
| `front matter is not a mapping` | it loads as a list or a scalar (empty, blank, comment-only or `null` front matter is an empty mapping) |
| `unknown key: <path>` | a key `WorkItemState`, `Claim` or `JournalRecord` does not define |
| `missing key: <path>` | `stage`, or a required key of a claim or journal record |
| `invalid <path>: <reason>` | a value the model refuses; the first in the order of the state's fields |
| `invalid state: <reason>` | every value is valid but a rule across keys is broken (the claim's stage differs from the state's) |

A bad `stories` or `outcome` is a `WorkItemFormatError` whose fault names that key. The agent files have their own reader and faults: see *The agent definition reader* in [agents.md](agents.md).

```console
$ python -c "from factory.work.adapters.work_item_markdown import FrontmatterWorkItemReader; FrontmatterWorkItemReader().parse('---\nstage: tests\ncolour: 2\n---\n# T\n')" 2>&1 | tail -n 1
factory.shared.domain.errors.WorkItemFormatError: unknown key: colour
$ python -c "from factory.work.adapters.work_item_markdown import FrontmatterWorkItemReader; spec = FrontmatterWorkItemReader().parse_specification('---\nstage: tests\nattempts: 1\n---\n\n\n# T\n'); print(spec.state, spec.ignored_keys, repr(spec.body))"
None ['stage', 'attempts'] '# T\n'
```

See also: *The layout of the file* in the Reference for the written keys, their notation and the YAML handler.

## Sections of a Markdown body

One module finds the title, the `## ` sections and the fenced code blocks of a Markdown body: [sections.py](../../src/factory/shared/domain/sections.py) (`factory.shared.domain.sections`). It is pure. It works on text, and nothing reads a file. Every module that needs a heading or a fenced block uses it and does not look for `## ` itself.

    split_lines(body) -> list[str]
    code_blocks(lines) -> list[CodeBlock]
    opening_fence(line) -> str | None
    lines_outside_blocks(lines) -> list[int]
    title(body) -> str | None
    sections(body) -> list[Section]
    section_text(body, heading) -> str | None
    insert_paragraph(body, heading, paragraph) -> str
    required_sections(form) -> list[str]

- Every index is an index into `split_lines(body)`, which splits at `"\n"` and drops an empty last element. `""` gives `[]`.
- A code block opens at a line that starts, after optional spaces or tabs, with three or more backticks or three or more tildes.
- It closes at the first later line that is the same character repeated at least as often, then nothing but whitespace. A shorter run, the other character or trailing text does not close it.
- A block never closed runs to the end and has `end=None`. A line starting with one or two backticks (inline code) opens nothing.
- A heading is a line outside every block that starts with `## ` at column 0. `### x`, an indented `## x`, `##x`, `##` and `# x` are not.
- A `Section` (`heading`, `start`, `end`) runs from its heading line to the next heading or the end. Lines before the first heading belong to no section.
- The title is the stripped text of the first line outside every block that starts with `# ` at column 0, or `None`.
- A heading is matched by its exact text, case-sensitive. The first section wins when it occurs twice.
- The code knows three heading names as constants: `ACCEPTANCE_CRITERIA` (`"Acceptance criteria"`), `SMOKE_TEST` (`"Smoke test"`) and `JOURNAL` (`"Journal"`). Every other section a story has comes from the project's own form.
- `required_sections(form)` is the headings of the form in order, so a section added to the form becomes required.
- `section_text` returns the text under the heading without its heading line and without leading and trailing blank lines (`""` when empty), or `None` when no section has the heading.
- `insert_paragraph` returns the body with the paragraph first under the heading, a blank line on each side. It ends with a newline exactly when `body` did. It raises `WorkItemFormatError` with the fault `missing section: ## <heading>` when no section has the heading (a heading only inside a fence counts as missing), and `ValueError` for a blank paragraph.
- `Section` and `CodeBlock` are frozen, refuse unknown fields, and take indices of 0 or more.
- `opening_fence(line)` returns the run of backticks or tildes the line opens a block with, without indentation or info string, or `None`.
- `lines_outside_blocks(lines)` returns the indices of the lines outside every block. A block's fence lines count as inside.

```console
$ python -c "from factory.shared.domain.sections import insert_paragraph, section_text, sections, title; fence = '~' * 3; body = '# Story\n\n## Demo\n\n' + fence + 'bash\n## start the server\necho ok\n' + fence + '\nExpect: ok\n\n## Journal\n\n1. 2026-10-12 human: created.\n'; print(title(body)); print([s.heading for s in sections(body)]); print(repr(section_text(body, 'Demo'))); print(insert_paragraph(body, 'Journal', 'Note.').split('\n')[10:])"
Story
['Demo', 'Journal']
'~~~bash\n## start the server\necho ok\n~~~\nExpect: ok'
['## Journal', '', 'Note.', '', '1. 2026-10-12 human: created.', '']
```

The `## start the server` line is inside the fence, so it is no heading.

## The form check of a story

The form check says what is wrong with the shape of a [story](glossary.md) file. It is [story_form.py](../../src/factory/work/domain/story_form.py) (`factory.work.domain.story_form`), pure, and run by the command `factory-check-story` ([check_story.py](../../src/factory/entry/check_story.py), `factory.entry.check_story`).

    check_story_form(document, form, *, folder) -> list[FormFinding]
    check_story_place(path, *, feature_file_exists) -> list[FormFinding]
    lifecycle_folder_of_location(path) -> LifecycleFolder | None
    main(argv=None, *, root=None) -> int

- `check_story_form` returns one `FormFinding` (`line`, `message`) for each rule the story breaks, all of them, in the order of the table below.
- `line` is a line of the body counted from 1, or `None` when the finding has no line. `FormFinding` is frozen, refuses unknown fields and takes a `line` of 1 or more.
- `document` is a `WorkItemDocument`, `form` is the text of the project's story form (`factory/story-form.md`) and `folder` is the `LifecycleFolder` the story is in.
- The sections come from the project's form, not from the code. `required_sections(form)` is what a story must have, so a `## Notes` added to the form makes `Notes` required.
- The code knows only the names `Acceptance criteria`, `Smoke test` and `Journal`. A rule about one of them does nothing when the body has no such section; rule 2 reports it when the form requires it.
- Code blocks are respected. A `## heading`, a `# comment` or a numbered line inside a fenced block is never a heading, a title or an item.
- An item is a line at column 0 that starts with digits and `". "`. It runs to the line before the next item or to the end of the section.
- Fewer than two criteria get no closing finding. No criteria or no entries is no finding of rules 3 and 6.
- Every code block of the smoke test is judged by itself. A block that is never closed runs to the end of the body, so it hides a later `## Journal`. That is the safer reading of a half-written story.
- Rules 7 and 10 check the human's file in the backlog. Rules 8 and 9 are for the factory's own calls on a document that belongs to a work item's branch.
- A backlog story's `Journal` section has no entries, because the opening writes entry 1 into it. An entry already there would make a second entry 1.
- A caller that holds only the specification of a started story names the folder `backlog`, so that rules 8 and 9 are not asked of a document that cannot have a state. The text on `main` has no front matter.

| # | Rule | Message | Line |
|---|---|---|---|
| 1 | no line outside the code blocks starts with `# ` | `the story has no title line` | none |
| 2 | a heading of the form is not a section (one finding each, in the form's order) | `missing section: ## <heading>` | none |
| 3 | the criteria are not numbered 1, 2, 3 and so on (the first one that differs) | `criterion numbered <found> where <expected> is expected` | that item |
| 4 | with two criteria or more: the second-to-last lacks `make check` or `green`; the last does not start with `docs:` after its number | `the second-to-last criterion must contain "make check" and "green"`; `the last criterion must start with "docs:"` | that item |
| 5 | `Smoke test` has no code block; a block is not followed, after blank lines, by an `Expect:` line (or is never closed, or ends the section) | `the Smoke test has no code block`; `the code block opened at line <n> is not followed by an "Expect:" line` | the heading; the opening of the block |
| 6 | the journal entries are not numbered 1, 2, 3 and so on (the first one that differs) | `journal entry numbered <found> where <expected> is expected` | that entry |
| 7 | `backlog` and the document has front matter keys | `a backlog story carries no front matter: <keys joined by ", ">` | none |
| 8 | another folder and the document has no state | `the story has no state` | none |
| 9 | another folder and the state's `journal` has a different number of records than the text has entries | `the journal data lists <n> entries but the text shows <m>` | none |
| 10 | `backlog` and the `Journal` section has entries | `a backlog story carries no journal entries` | the first entry |

```console
$ python -c "from factory.work.domain.story_form import check_story_form; from factory.work.domain.work_item import WorkItemDocument; form = '# Form\n\n## Description\n\n## Acceptance criteria\n\n## Smoke test\n\n## Journal\n'; body = '# S\n\n## Description\n\nText.\n\n## Acceptance criteria\n\n1. It works.\n3. make check stays green.\n4. done.\n\n## Smoke test\n\nNo block here.\n'; print(*[f'{f.line} {f.message}' for f in check_story_form(WorkItemDocument(state=None, body=body), form, folder='backlog')], sep='\n')"
None missing section: ## Journal
10 criterion numbered 3 where 2 is expected
11 the last criterion must start with "docs:"
13 the Smoke test has no code block
```

### Where a story sits

`check_story_place(path, *, feature_file_exists)` returns the findings against where a story file sits. It is pure. `path` is a repository-relative path with `/`, and `feature_file_exists` is whether `factory/features/<directory>/feature.md` exists, which the caller looks up. The findings have no line.

| # | Rule | Message |
|---|---|---|
| 1 | the path is not exactly `factory/features/<feature directory>/<folder>/<file>`, with the folder one of `LIFECYCLE_FOLDERS` (`ongoing` is not one); this is the only finding then | `not a work item location: expected factory/features/<feature>/<backlog\|in-progress\|done>/<file>.md` |
| 2 | the file name is not a story file name (`F0000-S0000.md`, with or without a slug; an acceptance's name is not one) | `the file name "<name>" is not F0000-S0000[-slug].md` |
| 3 | the feature directory is not `F0000` or `F0000-<slug>` | `the feature directory "<directory>" is not F0000[-slug]` |
| 4 | both parse and their feature ids differ | `the story <story id> is in the directory of feature <feature id>` |
| 5 | `feature_file_exists` is false | `the feature file feature.md is missing in factory/features/<directory>` |

- After rule 1 passes, rules 2 to 5 are independent and reported in that order.
- `lifecycle_folder_of_location(path)` returns the folder of a path that passes rule 1 and `None` otherwise. The command uses it to decide whether to read the file and with which reader.

### The check command

`main(argv=None, *, root=None)` returns the exit status (0, 1 or 2). The module runs as `python -m factory.entry.check_story`.

- It reaches the work item reader only through `factory.entry.wiring.build_work_item_reader()`, the one entry module that imports from an `adapters` layer. A test parses the imports to hold that.
- A backlog file is read with `parse_specification`.
- A file in `in-progress` or `done` is read with `parse`. When the reader's fault is `no front matter`, it is read again with `parse_specification` and checked as `backlog`: on `main` a started story is the human's moved file, and its state lives on the work item's branch.
- Any other reader fault becomes the only form finding of that file.

See also: the output of the command in [pipeline.md](../operator-guide/pipeline.md), *Checking a story before it starts*; the index [README.md](README.md).

## Reference

Exact detail that the sections above summarise.

### The tree

All spellings are constants in `factory.shared.domain.paths`:

| Constant | Value |
| --- | --- |
| `FACTORY_DIRECTORY` | `factory` |
| `PIPELINE_DEFINITION_FILE` | `factory/pipeline.yml` |
| `STORY_FORM_FILE`, `FEATURE_FORM_FILE` | `factory/story-form.md`, `factory/feature-form.md` |
| `FEATURES_DIRECTORY` | `factory/features` |
| `FEATURE_FILE_NAME` | `feature.md` |
| `LIFECYCLE_FOLDERS` | `backlog`, `in-progress`, `done` (in that order) |
| `COST_RECORDS_SUFFIX` | `.costs.jsonl` |
| `BRANCH_PREFIX` | `work-item/` |
| `LABEL_PREFIX` | `stage:` |
| `REMOTE`, `MAIN_BRANCH` | `origin`, `main` |

- `FEATURE_ID`, `STORY_ID` and `ACCEPTANCE_ID` in `identifiers` are the unanchored regular expressions of the ids.
- `PROJECT_AGENTS_DIRECTORY` in `paths` is where a project keeps its own agents: the folder `<project>/factory/agents/`. The constant and `project_agent_file(name)` hold paths relative to the project's root, and the function gives the file `<name>.md` in that folder. `AGENT_SUFFIX` is the `.md`.
- `parse_work_item_file_name` returns a `WorkItemFileName` and `parse_feature_directory_name` a `FeatureDirectoryName`. Both are frozen, with `id` and `slug`, the slug `None` when absent.
- `BRANCH_PREFIX` is defined in `identifiers`, to avoid an import cycle, and re-exported by `paths`.
- `is_acceptance`, `feature_of`, `work_item_order` and `branch_name` all live in `identifiers`.

### The data of a work item

The fields of `WorkItemState`, in the order they are written:

| Field | Type | Initial |
|---|---|---|
| `stage` | `Name` | the first stage (no default) |
| `blocked` | `question`, `attempts_cap`, `round_cap`, `crash_cap`, `send_back` or `None` | `None` |
| `round` | integer ≥ 0 | 0 |
| `attempts` | integer ≥ 0 | 0 |
| `crashes` | integer ≥ 0 | 0 |
| `pull_request` | integer ≥ 1 or `None` | `None` |
| `comments_read` | ids of the comments already read | `[]` |
| `handed_over` | `Name` or `None` (the hand-over marker) | `None` |
| `claim` | `Claim` or `None` | `None` |
| `journal` | list of `JournalRecord` | `[]` |

The fields of `JournalRecord` after `number`, `speaker` and `kind`:

| Field | Type | Meaning |
|---|---|---|
| `at` | `UtcDatetime \| None` (`factory.shared.domain.times`) | when the entry was written; an aware time, stored in UTC; a naive time is refused |
| `stage` | `Name \| None` | the stage of the work item's state when the entry was written |
| `run` | `RunId \| None` ([cost_records.py](../../src/factory/watching/domain/cost_records.py), `factory.watching.domain.cost_records`) | the id of the agent run the entry came from: 32 lowercase hexadecimal characters, the `run` of that run's cost record |
| `blocked` | `Blocked \| None` | on a `question` record only: the block the question opened, one of `question`, `attempts_cap`, `round_cap`, `crash_cap`, `send_back` |
| `reason` | `StallReason \| None` | on a `stall` record only: the stall reason the factory decided (the values of `StallReason`) |

- The entries that carry no run are `created`, `started`, `crash`, `expiry`, `close`, `send_back`, `comment`, the other questions and `done`.

### The feature acceptance

- **Order.** `work_item_order` puts an acceptance after every story of its feature.
- **Status.** `acceptance_status` takes `FeatureFiles` (the names directly in `backlog`, `in-progress` and `done`) and `ReportFacts` (id, folder, state, `on_branch`). `accepted` and `refused` come from the highest covering id. `story_file_ids(names)` keeps only story file names, ascending and without repeats. `ReportFacts.on_branch` is true exactly for reports read from a branch ref.
- **Front matter.** The writer writes both keys, `stories` then `outcome` (`outcome: null` while unset), after `journal`.
- **Reader.** `AcceptanceReader(boundaries, definition)` reads only `origin/` refs through `Git.list_files`, `show_file` and `remote_branches`.
  - `read()` returns a `FeatureAcceptance` per feature directory on `origin/main`: status, archived stories and `next_acceptance`.
  - `snapshots()` returns one `WorkItemSnapshot` per acceptance whose report is in `in-progress/` of its feature on `origin/main` or on `origin/work-item/<id>`. It never gives two for one id, and gives `[]` without an `acceptance_stage`.
  - `path` is the one on `origin/main` when the report is there, else the branch's. `branch_commit` is the branch's commit, `None` once the hosting service deleted the branch.
  - The document is read from the branch when it holds the file, else from `origin/main`. So a merged and not yet recorded report is included, and the `merged` event can be raised for it.
  - A report in `done/` gives no snapshot unless a branch still holds it in `in-progress/`, the leftover of a kill.
  - Story branches, branches without a report file and reports under another feature's directory are ignored. A state that is not an acceptance's raises `WorkItemFormatError` with the path, and so does an unreadable report.
  - The result is in `work_item_order`.
  - `due_features()` returns the due feature ids, `[]` without an `acceptance_stage`. `fill_board(rows)` sets `FeatureRow.acceptance`.
  - `parse_at` in `factory.work.application.work_items` is the shared helper that reads and parses a file at a ref.
- **Opening.** `AcceptanceService(boundaries, definition).open(feature)` reads the last fetch only.
  - A status other than `due` raises `CannotHandle` with the text `feature F0001 is incomplete, not due`, for the status `incomplete`.
  - It checks out `work-item/<acceptance id>` from `origin/main`, writes `factory/features/<directory>/in-progress/<id>-acceptance.md`, commits and pushes.
  - The head is `acceptance_head(feature_title, acceptance_stage, archived stories)`: the initial state, `stories`, `outcome: null`, and the body `# Acceptance of <feature title>`, an empty line and `## Journal`.
  - The title is the first `# ` line of `feature.md` on `origin/main`. A missing file or a file without a title raises `WorkItemFormatError` with that path, before anything is written.
  - A push that is not `pushed` raises `PushFailed`, so a branch the checkout has not fetched is `rejected` and left as it is.
  - `AcceptanceDueHandler` runs `open` for the feature of an `acceptance_due` event. It raises `CannotHandle` for another kind, no feature, or no `acceptance_stage`. It is registered for `acceptance_due` in `build_handlers`.
- **The hand-over.** `AcceptanceHandOver(boundaries, definition)` uses the same helpers as `HandOverHandler` (`target_of`, `require_pull_request`, `WorkItemRecorder`, `commit_subject`, `cost_table_post`) and the same post key, `cost_table_key(work_item, document)` in [hand_over.py](../../src/factory/hosting/domain/hand_over.py) (`factory.hosting.domain.hand_over`).
  - Its refusals, in order, are `CannotHandle` with `not a hand_over event`, `not an acceptance`, `no acceptance stage`, `stage <stage> is not an approval` and, from `require_pull_request`, `work item <id> has no pull request`.
  - The reviewer's role is the role of `definition.acceptance_stage`, looked up in `handle`.
  - It checks out the branch and returns at once when `handed_over` equals the stage. Otherwise it sets the description to `acceptance_description(document, role)` (`factory.work.domain.acceptance`), marks the pull request ready, posts the cost table and records `handed_over`. A push that is not `pushed` raises `PushFailed`.
  - `acceptance_description` joins `## Recommendation` (`section_text` of `RECOMMENDATION`), `## Findings in short` (`entry_text` of the latest `result` record found by `last_record(speaker=role, kind="result")`), `## Proposed stories` and `ACCEPTANCE_CLOSING` with empty lines. A missing or empty part reads `NONE_TEXT`. The closing names no merge method.
  - The tests are [test_acceptance_hand_over.py](../../tests/pipeline/application/test_acceptance_hand_over.py) and [test_acceptance_description.py](../../tests/work/domain/test_acceptance_description.py).
- **The split.** `SplitByWorkItemKind(story, acceptance)` has the properties `story` and `acceptance`, which return the two handlers for wiring tests. It is registered for `hand_over`, `merged` and `closed` in `build_handlers`, and the `RunGate` holds the same `closed` and `merged` instances.
- **The reviewer's facts.** `AcceptanceService.facts(feature)` returns `AcceptanceFacts`.
  - `archived` is the story ids in `done/`.
  - `next_story` is the highest story number in `backlog`, `in-progress` and `done`, plus one, in four digits. It is `S0001` for none and a `ValueError` at 9999. Reports and non-story files do not count.
  - `cost_line` is the line of `bill` over the cost records of the archived stories only. A story without a sidecar adds none.
  - `human_line`, `disk_now` and `disk_before` are strings, default `None`. `human_line` is the line of the human's waits over the archived stories.
  - `facts` first reads `DiskRecorder(boundaries).last()`, the latest disk record of any occasion. Then it appends one record of occasion `acceptance` with `record("acceptance")`. `disk_now` is `disk_line` of the new record. `disk_before` is `disk_line` of the earlier one, or `None` when there is none.
  - `lines()` gives `Archived stories: ...`, `Next free story number: ...` and `Cost of the stories: ...`. When `human_line` is set it adds `Human interventions of the stories: ...`. When `disk_now` is set it adds `Disk now: ...` and `Disk at the previous record: ...`, with `none` when `disk_before` is `None`.
  - `acceptance_prompt(base, facts)` is `base`, an empty line and those lines. `acceptance_facts(files, cost_line, *, human_line=None, disk_now=None, disk_before=None)` builds the facts.
  - The shipped acceptance reviewer is told to compare the two disk lines and name growth the feature's changes do not explain.
- **What the reviewer may write.** Its [write paths](glossary.md) are those of the role of `acceptance_stage`, expanded by `WritePathService` as for any work item.
- **Its cost.** `read_cost_records` in [costs.py](../../src/factory/watching/application/costs.py) (`factory.watching.application.costs`) is the one read of a sidecar at a ref. `feature_file_path` and `read_feature_file` read a feature's file and are shared with the board.

### The records contract

- `contract_schema(entry)` is the schema's text: `$schema` (the 2020-12 dialect), `x-records-contract` (`RECORDS_CONTRACT`, `4.4`), then the model's `model_json_schema(mode=...)` unchanged, indented by 2 and ending in one newline.
- `schema_file_name(entry)` is `<name>.schema.json`.
- `write_contract(folder)` replaces the five files and leaves others alone. `main` prints `contract: 5 schemas written`, and returns 2 with a usage line for more than one argument.

### The layout of the file

The writer writes all ten keys, in field order:

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
  started_at: '2026-10-13T09:00:00Z'
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

- A missing value is `null`, an empty list `[]`, a non-empty `comments_read` a flow list, `claim` is `claim: null` when absent, and `journal` is a block list of mappings.
- Every unset field of a journal record (`at`, `stage`, `run`, `blocked`, `reason`) is left out of the file. Every key of the state itself stays (`claim: null`). A record with all three of `at`, `stage` and `run`:

  ```yaml
  - number: 2
    speaker: tester
    kind: result
    at: '2026-10-17T20:31:00Z'
    stage: tests
    run: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
  ```

  `at` is written like `started_at`. A `run` a YAML reader would take for a number (32 times `1`) is single-quoted.
- `started_at` is single-quoted UTC text in `isoformat()` form with the offset written as `Z`.
- A name a YAML reader could take for null or a boolean (`null`, `true`, `false`, `yes`, `no`, `on`, `off`, `y`, `n`) is single-quoted (`handed_over: 'true'`), so it reads back as the same text. Every other scalar is unquoted.
- `RuamelYamlHandler` subclasses python-frontmatter's `YAMLHandler` and overrides only `load` (ruamel.yaml's safe loader, keys converted with `str`) and `export`.
- The reader calls the handler's `detect`, `split` and `load` itself, not `frontmatter.loads`. The split is the module function `split_front_matter(handler, text)`, which the agent definition reader calls too.
- `frontmatter.loads` would take two later `---` lines for front matter, return an unclosed text whole, drop front matter that is not a mapping and refuse a key named `content`.
