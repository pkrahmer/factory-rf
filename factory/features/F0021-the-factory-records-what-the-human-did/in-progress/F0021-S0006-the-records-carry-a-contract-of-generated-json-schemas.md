---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 240
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T00:01:10.028656Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T00:01:10.034029Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T00:01:24.892340Z'
  stage: intake
  run: 7442cdcf4b0b410cb4a79ed7022ab9e4
---

# The records carry a contract of generated JSON Schemas

## Description

Readers outside the factory, first the Factory Timeline (`pkrahmer/factory-timeline`, a page that reads a factory's records from GitHub), read what the factory writes: a work item's front matter, the lines of its `.costs.jsonl` sidecar, the lines of `factory/stops.jsonl` (S0003), and the pipeline definition. Today the only description of those records is the Pydantic models inside the factory, so such a reader learns of a change only when it breaks. This story gives the records a contract. Five JSON Schema files, generated from the models that already validate each record with Pydantic's `model_json_schema` and never written by hand, are committed under `src/factory/contract/`. Each schema carries the records contract's version, `1.0`. A command regenerates them, and a test regenerates them into a temporary folder and compares them with the committed files, so a model change without a schema change fails `make check`. The major version rises for a change that can break a reader (a field removed or renamed, a type narrowed, a meaning changed), the minor for an added optional field or value. It is separate from the pipeline definition's own `contract`. The operator guide says what a reader may rely on: the front matter and the JSON lines as these schemas describe them, never the Markdown text of a work item, which is for people. The contract describes the records the engine writes. It names no stage, no role and no reader. This story builds on the fields of S0001 (the causes), S0003 (the stop record) and S0004 (the refused tool calls) and comes after them.

## Interface

`factory.domain.contract` (`domain`, new):

```python
RECORDS_CONTRACT = "1.0"
CONTRACT_KEY = "x-records-contract"
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

SchemaMode = Literal["validation", "serialization"]


@dataclass(frozen=True)
class ContractEntry:
    """One record of the contract: its file's name, the model that validates it and the mode."""

    name: str
    model: type[BaseModel]
    mode: SchemaMode


CONTRACT: tuple[ContractEntry, ...] = (
    ContractEntry("work-item-state", WorkItemState, "serialization"),
    ContractEntry("acceptance-state", AcceptanceState, "serialization"),
    ContractEntry("cost-record", CostRecord, "serialization"),
    ContractEntry("stop-record", StopRecord, "serialization"),
    ContractEntry("pipeline-definition", PipelineDefinition, "validation"),
)


def schema_file_name(entry: ContractEntry) -> str:
    """`<name>.schema.json`."""


def contract_schema(entry: ContractEntry) -> str:
    """The schema's text: `$schema`, the contract key and version, then the model's schema."""
```

- `contract_schema` is `json.dumps({"$schema": JSON_SCHEMA_DIALECT, CONTRACT_KEY: RECORDS_CONTRACT, **entry.model.model_json_schema(mode=entry.mode)}, indent=2)` followed by one newline. Nothing in the model's schema is added, removed or reordered.
- The records the factory writes use `serialization`, the shape they have on disk (a cost as a string, a time in UTC). The pipeline definition, which the human writes and the factory reads, uses `validation`.
- A dataclass, not a Pydantic model, since it holds a class. `tests/test_model_configuration.py` therefore does not see it.

`factory.entry.contract` (`entry`, new), run as `uv run python -m factory.entry.contract [<folder>]`:

```python
CONTRACT_FOLDER: Path  # src/factory/contract, the folder beside the package's modules


def write_contract(folder: Path) -> list[Path]:
    """Write every schema of `CONTRACT` into `folder`, creating it; return the paths in order."""


def main(argv: Sequence[str] | None = None) -> int:
    """Write the schemas into the folder given, or `CONTRACT_FOLDER`; print one line; 0."""
```

- `main` prints `contract: <n> schemas written` (`<n>` is 5) and returns 0. More than one argument prints `usage: python -m factory.entry.contract [<folder>]` to standard error and returns 2.
- `write_contract` replaces a file of the same name and leaves every other file in the folder alone.

`src/factory/contract/` (written by the coder through the command, never by hand): `work-item-state.schema.json`, `acceptance-state.schema.json`, `cost-record.schema.json`, `stop-record.schema.json`, `pipeline-definition.schema.json`, and nothing else. They are package data: hatchling ships them in the wheel with `src/factory`, and a reader in another repository can fetch them from `main`.

Test modules (new): `tests/domain/test_contract.py`, `tests/entry/test_contract.py`; criterion 5 is the parametrized test `test_the_committed_schemas_are_the_generated_ones` in `tests/entry/test_contract.py`, the name the feature's human change 1 deselects in mutmut runs. No earlier test changes.

## Acceptance criteria

1. `CONTRACT` holds the five entries of the Interface in that order, and their names are unique. `schema_file_name` of the first is `work-item-state.schema.json`.
2. `contract_schema` of each entry (rows of one parametrized test, one per entry) parses as JSON whose first two keys are `$schema` with `https://json-schema.org/draft/2020-12/schema` and `x-records-contract` with `1.0`. The rest equals `model_json_schema(mode=<the entry's mode>)` of its model, and the text ends in exactly one newline.
3. The schema of `work-item-state` has `JournalRecord` under `$defs`, with `blocked` and `reason` among its properties and neither required. The schema of `cost-record` has `denials` and `denied_paths` among its properties and neither required. The schema of `stop-record` requires `event`, `scope`, `reason` and `at` (rows of one parametrized test).
4. `write_contract(tmp_path / "out")`, rows of one parametrized test over what the folder held before: nothing (the folder does not exist); a file `other.txt`; a `stop-record.schema.json` with the text `{}`. In each row it returns the paths of the five files in `CONTRACT`'s order, each file holds the text `contract_schema` gives (the stale `stop-record.schema.json` replaced), and `other.txt` stays unchanged.
5. The committed files: `write_contract` into `tmp_path` gives exactly the files `src/factory/contract/` holds, same names and same bytes. Rows of one parametrized test, one per file, plus a row that the folder holds no file beyond the five.
6. `main`, rows of one parametrized test: `main([str(tmp_path)])` writes the five files into `tmp_path`, prints `contract: 5 schemas written` and returns 0; `main([])`, with `CONTRACT_FOLDER` of `factory.entry.contract` set to `tmp_path / "default"` (`monkeypatch.setattr`), writes the five files there, prints the same line and returns 0; `main([str(tmp_path), "x"])` prints `usage: python -m factory.entry.contract [<folder>]` to standard error, writes nothing and returns 2. In every row `CONTRACT_FOLDER` before the patch is `Path(factory.__file__).parent / "contract"`.
7. For each entry (rows of one parametrized test), the `required` list of its committed schema, as a set, equals the names of the model's fields that `model_fields` marks as required, and every field of the model is among the schema's `properties`. No validator library is added (decision 16).
8. `make check` stays green.
9. docs:
   - `docs/operator-guide.md`: a new section `## The records contract`. It gives:
     - the records a reader outside the factory may rely on: the front matter of a work item (`work-item-state`, and `acceptance-state` for an acceptance report), one line of a `.costs.jsonl` sidecar (`cost-record`), one line of `factory/stops.jsonl` (`stop-record`), and `factory/pipeline.yml` (`pipeline-definition`);
     - where the schemas live and how they are regenerated (`uv run python -m factory.entry.contract`);
     - that the Markdown body of a work item, the journal entries' text included, is for people and never for parsing;
     - where a work item's records are: on its branch `work-item/<id>` while it is in progress (the factory writes the front matter and the sidecar there at every stage), and on `main` from the merge on, moved to `done/` by the archive commit; a work item in `in-progress/` on `main` without a merge shows only the state it had at its start;
     - that a work item enters the approval with its last `result` record: no record marks the entry, so a reader takes the approval's start from that record's `at` and its end from the `done` record's `at`;
     - the version rule of the feature's decision 15;
     - that a reader ignores a property it does not know, although the schemas say `additionalProperties: false` for what this version of the factory writes;
     - that the records contract's version is not the pipeline definition's `contract`.
   - `docs/project-guide.md`, a subsection *The records contract* under *The data of a work item*: `factory.domain.contract`, the command, the test that compares the committed files, and that a model change regenerates the schemas in the same story.
   - `docs/decisions.md`: a new entry, "The records carry generated JSON Schemas under `src/factory/contract/`", with the reasons (the readers outside the factory, a schema that cannot drift from its model) and the rejected alternatives: schemas written by hand, a folder at the repository's root (it needs a write path of its own), and the pipeline definition's `contract` as the records' version.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python -m factory.entry.contract "$d"
ls "$d"
diff -r "$d" src/factory/contract && echo same
```

Expect: seven lines: `contract: 5 schemas written`; then `acceptance-state.schema.json`, `cost-record.schema.json`, `pipeline-definition.schema.json`, `stop-record.schema.json` and `work-item-state.schema.json`, one per line; then `same`.

```bash
uv run -q python -c '
import json

with open("src/factory/contract/stop-record.schema.json", encoding="utf-8") as file:
    schema = json.load(file)
print(schema["x-records-contract"], sorted(schema["required"]))
'
```

Expect: `1.0 ['at', 'event', 'reason', 'scope']`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: `factory.domain.contract` (constants, `ContractEntry`, `CONTRACT`, `schema_file_name`, `contract_schema`) and `factory.entry.contract` (`CONTRACT_FOLDER`, `write_contract`, `main`) are concrete, with signatures and exact output formulas (the `json.dumps` call, the usage and result lines, exit codes 0 and 2). Every comment behaviour has a criterion: the schema text format (2), modes per entry (2), folder creation, replacement and leaving other files alone (4), the default folder and the argument count (6).
   Criteria: each one is testable by one parametrized test function. Rules have both sides: one argument and none succeed and two arguments fail (6); a missing folder, an unrelated file and a stale schema (4); the committed files match and no extra file exists (5); required and not-required fields (3, 7).
   Smoke test: both commands are runnable with `uv run`. Each `Expect:` line is checkable: seven exact lines, and `1.0 ['at', 'event', 'reason', 'scope']`.
   Architecture: the pure `ContractEntry` and the schema text sit in `domain`; the file writing and the command sit in `entry`; the dependency direction is respected. The dataclass is explained, and no new dependency is added (decision 16).
   Scope: it matches the feature's S0006 bullets and decision 15. It names no stage, role or reader, and it changes no earlier test. The docs criterion covers the operator guide, the project guide and the decisions entry.
