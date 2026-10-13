---
stage: tests
pr: 29
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Work item state

## Assignment (as of log entry 1)

Create the data types of a work item: the state that lives in the front matter (stage, blocked, round, attempts, crashes, pull request number, ids of comments read, the hand-over marker, the claim and the journal's data), the claim, the one journal record that the state lists for each entry, the document that pairs a state with the body text, the initial state of a started story, and the error for a work item file that cannot be read. Every rule that has one right answer is a validation of these types, so the reader and the writer of the next story only translate. The journal's records are the data half of SI1.1 (speaker and kind kept as data); the functions that append and read entries are the story after next. The story covers R15 (the state's fields, their order and initial values) and keeps kept thing 4 (the work item is the memory: state beside the specification and the journal). It builds only domain types; no file is read or written.

## Interface

`src/factory/domain/errors.py` (adds to the hierarchy that F0001-S0001 created)

```python
class WorkItemFormatError(FactoryError):
    fault: str
    path: str | None
    def __init__(self, fault: str, path: str | None = None) -> None: ...
```

`src/factory/domain/journal.py` (this story creates the module with the data types; F0002-S0005 adds the functions)

```python
HUMAN = "human"
FACTORY = "factory"
Speaker = Name
JournalKind = Literal[
    "created", "started", "result", "question", "comment", "close",
    "stall", "crash", "expiry", "move_back", "send_back", "done",
]

class JournalRecord(BaseModel):               # one element of the front matter's journal list
    number: PositiveInt
    speaker: Speaker
    kind: JournalKind
```

`src/factory/domain/work_item.py`

```python
Blocked = Literal["question", "attempts_cap", "round_cap", "crash_cap", "send_back"]

class Claim(BaseModel):
    instance: Name
    stage: Name
    started_at: AwareDatetime
    lease_duration: PositiveInt               # minutes

class WorkItemState(BaseModel):               # fields in this order
    stage: Name
    blocked: Blocked | None = None
    round: NonNegativeInt = 0
    attempts: NonNegativeInt = 0
    crashes: NonNegativeInt = 0
    pull_request: PositiveInt | None = None
    comments_read: list[PositiveInt] = []
    handed_over: Name | None = None
    claim: Claim | None = None
    journal: list[JournalRecord] = []

class WorkItemDocument(BaseModel):
    state: WorkItemState | None           # None for a document read as a specification (F0002-S0003)
    body: str
    ignored_keys: list[str] = []

def initial_state(first_stage: str) -> WorkItemState: ...
```

Every model above is `ConfigDict(frozen=True, extra="forbid")`. `Name` is `factory.domain.identifiers.Name`. The rules; each has a criterion below:

- `initial_state(first_stage)` has `stage=first_stage`, no `blocked`, no `pull_request`, no `handed_over`, no `claim`, every counter 0, and empty `comments_read` and `journal`. `first_stage` must be a `Name`, else `pydantic.ValidationError`. Only `stage` has no default.
- `comments_read` is sorted ascending with no repeats.
- When `claim` is set, `claim.stage == stage`.
- The `number`s of `journal` are 1, 2, 3 up to n in order.
- Where an error is located (F0002-S0003 names a fault by it): the rules for `comments_read` and for `journal` are validations of their own field, so their errors are located at that field; the rule that `claim.stage` equals `stage` spans two keys, so it is a validation of the whole state and its error has no location.
- A `Claim`'s `started_at` is converted to UTC; a naive time is refused. `lease_duration` is at least 1.
- `WorkItemFormatError(fault, path)` carries both as attributes. Its message is `fault` when `path` is `None` and `<path>: <fault>` otherwise. It is a `FactoryError`.

Tests: `tests/domain/test_work_item.py`, `tests/domain/test_journal_records.py`, `tests/domain/test_work_item_errors.py`. A test that constructs a model without a required field, with an unknown field or with a value of the wrong type does so through a variable typed `type[BaseModel]`, and a test that assigns to a field does so with `setattr` (`CLAUDE.md`, Tests; the pydantic mypy plugin types the real constructor and frozen fields).

## Acceptance criteria

1. `initial_state("intake")` has `stage == "intake"`, `blocked`, `pull_request`, `handed_over` and `claim` all `None`, `round`, `attempts` and `crashes` all 0, and `comments_read` and `journal` both `[]`; the field names of `WorkItemState`, in order, are `stage`, `blocked`, `round`, `attempts`, `crashes`, `pull_request`, `comments_read`, `handed_over`, `claim`, `journal`.
2. `WorkItemState(stage="tests")` equals `initial_state("tests")`; `WorkItemState()` (constructed through a variable typed `type[BaseModel]`, as `CLAUDE.md` says) raises `ValidationError`; `WorkItemState(stage="Bad Stage")`, `WorkItemState(stage="")` and `initial_state("Bad Stage")` raise `ValidationError`.
3. `blocked` accepts `None` and each of `question`, `attempts_cap`, `round_cap`, `crash_cap` and `send_back`, and refuses `asked` and the empty string (constructed through a variable typed `type[BaseModel]`).
4. `round`, `attempts` and `crashes` accept 0 and refuse -1; `pull_request` accepts 1 and `None` and refuses 0 and -1; `handed_over` accepts `approval` and `None` and refuses `Approval` and the empty string.
5. `comments_read` accepts `[]`, `[3]` and `[3, 5]` and refuses `[5, 3]` (not ascending), `[3, 3]` (a repeat) and `[0]`.
6. A state with a claim whose `stage` equals the state's `stage` is accepted; a claim for another stage is refused with `ValidationError`.
7. `journal` accepts `[]` and records numbered 1, 2, 3 in order, and refuses records numbered `[2]`, `[1, 3]`, `[1, 1]` and `[2, 1]`.
8. The location of an error (`ValidationError.errors()[0]["loc"]`, a state built with `model_validate` from a dict) is `("comments_read",)` for `comments_read: [5, 3]`, `("journal",)` for a journal numbered `[1, 3]`, `()` for a claim whose stage differs from the state's stage, and `("claim", "lease_duration")` for a claim with `lease_duration: 0`.
9. `JournalKind` accepts each of the twelve kinds listed in the Interface and refuses `comment_copied` and the empty string; `JournalRecord` refuses `number=0` and `speaker="Human"`; `HUMAN` is `"human"` and `FACTORY` is `"factory"`.
10. `Claim` accepts `lease_duration=1` and refuses 0; it refuses a `started_at` without a time zone; a `started_at` with a UTC offset of two hours east (`timezone(timedelta(hours=2))`) is stored as the same instant in UTC, with a `utcoffset()` of zero; it refuses an `instance` or `stage` that is not a `Name`.
11. `WorkItemState`, `Claim`, `JournalRecord` and `WorkItemDocument` each refuse an unknown field with `ValidationError` (constructed through a variable typed `type[BaseModel]`) and refuse assignment to a field with `ValidationError` (assigned with `setattr`).
12. `WorkItemDocument(state=None, body="x")` is valid and has `ignored_keys == []`; `WorkItemDocument(body="x")` without `state` (constructed through a variable typed `type[BaseModel]`) raises `ValidationError`.
13. `WorkItemFormatError("bad key", "a/b.md")` has `fault == "bad key"`, `path == "a/b.md"` and the message `a/b.md: bad key`; without a path the message is `bad key` and `path` is `None`; it is a subclass of `FactoryError`.
14. make check stays green.
15. docs: `docs/project-guide.md` describes a work item's data: the state's fields with their order and initial values, the claim, and that the journal's speaker and kind are data in the front matter.

## Demo

```bash
uv run python -c "
from factory.domain.work_item import initial_state
print(initial_state('intake').model_dump())
"
```
Expect: one line, `{'stage': 'intake', 'blocked': None, 'round': 0, 'attempts': 0, 'crashes': 0, 'pull_request': None, 'comments_read': [], 'handed_over': None, 'claim': None, 'journal': []}`.

```bash
uv run python -c "
from pydantic import ValidationError
from factory.domain.work_item import WorkItemState
for kwargs in ({'stage': 'tests', 'comments_read': [5, 3]}, {'stage': 'tests', 'blocked': 'asked'}):
    try:
        WorkItemState(**kwargs)
    except ValidationError as error:
        print('refused', error.error_count())
"
```
Expect: two lines, `refused 1` and `refused 1`: both invalid states are refused with one error each.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules (`domain/errors.py`, `domain/journal.py`, `domain/work_item.py`) with full signatures, field order and defaults. Every rule is listed and has a criterion.
   - Criteria: each is testable by a test function without further decisions. Every rule has its failing side: unsorted, repeated and zero `comments_read` (5); claim stage mismatch (6); journal numbering (7); blocked, handed_over, counters and pull_request bounds (3, 4); naive `started_at` and `lease_duration` 0 (10); unknown fields and assignment (11); missing `state` (12); `Bad Stage` and the empty string for `stage` (2). The behaviours in the Interface comments are covered: the UTC conversion (10), the error locations (8) and the error message (13).
   - Demo: both commands are runnable. Each `Expect:` line is checkable: the dumped dict is given exactly, and the second shows two lines of `refused 1`.
   - Architecture: pure domain types with no I/O, in `factory.domain`, with Pydantic DTOs. `Name` comes from the domain identifiers. Tests are placed under `tests/domain/`.
   - Scope: within F0002's "state in the front matter (R15)". The reader and writer (S0003) and the journal functions (S0005) are left out.
