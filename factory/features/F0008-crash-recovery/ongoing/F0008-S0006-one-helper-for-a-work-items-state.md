# One helper for a work item's state

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

Ten modules under `src/factory` define the same private helper, `_state_of`. Each one returns `document.state` and raises an error when it is `None`. The F0007 acceptance counted five copies, and F0008 added more. CLAUDE.md says to search for an existing helper and reuse or extend it, and the reviewer counts a second copy as a finding. Eight more functions make the same check inline: three on `<document>.state` directly, five after reading the state into a variable. This story replaces nine of the copies and the eight inline checks with one public function in `factory.domain.work_item`, the module of `WorkItemDocument` and `WorkItemState`. The tenth copy, in `factory.domain.journal`, stays: `factory.domain.work_item` imports `JournalRecord` from the journal module, so the journal module may import `work_item` only under `TYPE_CHECKING` (`docs/project-guide.md`, "Imports"; `docs/decisions.md`).

Each call site passes the exception its copy raised, so no exception type or message changes and no existing test has to change. This is a refactoring: no behaviour of the factory changes.

## Interface

`src/factory/domain/work_item.py` (added):

```python
def require_state(document: WorkItemDocument, error: Exception) -> WorkItemState: ...
```

- It returns `document.state` when that is not `None`.
- Otherwise it raises `error`, the very instance passed.

The nine copies and eight inline checks it replaces. Each copy is removed, and each call site and inline check becomes `require_state(document, <the exception below>)`:

| Module | Exception passed, unchanged |
|---|---|
| `src/factory/application/recovery.py` | `CannotHandle("crash", f"work item {work_item} has no state")` |
| `src/factory/application/claims.py` | `ValueError("the work item has no state to claim")` |
| `src/factory/application/stage.py` | `ValueError("the work item has no state")` |
| `src/factory/application/stalls.py` | `ValueError("the work item has no state to stall")` |
| `src/factory/application/handlers/closed.py` | `ValueError("a work item without a state cannot be sent back")` |
| `src/factory/application/handlers/questions.py` | `ValueError("a work item without a state has no question to ask")` |
| `src/factory/application/handlers/comments.py` | `ValueError("a work item without a state has no comments to read")` |
| `src/factory/application/handlers/reject.py` | `CannotHandle(_KIND, "a work item without a state has no stage to move back")` |
| `src/factory/application/handlers/hand_over.py` | `CannotHandle(_KIND, "the work item on its branch has no state")` |
| `src/factory/application/claims.py`, inline in `ClaimService.release` | `ValueError("the work item has no state to release")` |
| `src/factory/application/handlers/merged.py`, inline (the archived document) | `ValueError(f"the work item at {path} has no state to archive")` |
| `src/factory/adapters/work_item_markdown.py`, inline in `FrontmatterWorkItemWriter.render` | `WorkItemFormatError("the document has no state")` |
| `src/factory/application/costs.py`, inline in `CostRecorder.begin` | `ValueError(f"the work item {started.work_item} has no state")` |
| `src/factory/application/handlers/recording.py`, inline in `target_of` | `CannotHandle(event.kind, f"work item {snapshot.id} has no state")` |
| `src/factory/application/stage.py`, inline in `StageLauncher._launchable_stage` | `ValueError(f"the work item {prepared.work_item} has no state")` |
| `src/factory/application/task.py`, inline in `TaskComposer._round` | `WorkItemFormatError("the document has no state", context.path)` |
| `src/factory/domain/evaluation.py`, inline in `_validated_state` | `ValueError(f"work item {snapshot.id} has no state")` |

A module may keep a module-level constant or a small private function that builds its exception, if that reads better. It may not keep a function that checks `document.state` itself.

`src/factory/domain/journal.py` keeps its private `_state_of` unchanged, with a one-line comment above it saying why: the module cannot import `factory.domain.work_item` at run time, because that module imports `JournalRecord` from it. It is the one function besides `require_state` that checks a document's state itself.

Tests:

- `tests/domain/test_work_item_require_state.py`, new, for the function.
- `tests/test_no_state_copies.py`, new, at the `tests/` root: an `ast` search over `src/factory`, as `tests/test_no_journal_reading.py` searches.
- No existing test changes.

## Acceptance criteria

1. `require_state` returns the document's state for a `WorkItemDocument` that has one. The returned value equals `document.state`.
2. `require_state` raises the very exception passed for a `WorkItemDocument` whose `state` is `None` (`excinfo.value is error`). The test is parametrized over a `ValueError`, a `CannotHandle` and a `WorkItemFormatError`.
3. No module under `src/factory` other than `factory.domain.journal` defines a function named `_state_of`. The search test finds such a function in a source text written into the test itself, and finds none in `src/factory`.
4. No function under `src/factory` other than `require_state` and `factory.domain.journal`'s `_state_of` has an `if` whose body is only a `raise` and whose test is `X is None`, where `X` is `<name>.state` or a name that the same function assigns from `<expression>.state`. The search test finds such a function in two source texts written into the test itself, one for each form of `X`, and finds none in `src/factory`.
5. Every test that existed before this story passes unchanged.
6. make check stays green.
7. docs: `docs/project-guide.md` names `require_state` where it describes `WorkItemDocument` and `WorkItemState`, as the one way to get a document's state when it must be there, and its "Imports" bullet under the journal says that the journal keeps its own private check for that reason. CLAUDE.md is the human's file and is not changed.

## Demo

```bash
grep -rn "def _state_of" src/factory; echo "copies: $?"
```
Expect: two lines: `src/factory/domain/journal.py:<n>:def _state_of(document: WorkItemDocument) -> WorkItemState:` and then `copies: 0` (grep found the journal's one copy and no other).

```bash
uv run python -c "
from factory.domain.work_item import WorkItemDocument, initial_state, require_state
print(require_state(WorkItemDocument(state=initial_state('doing'), body=''), ValueError('none')).stage)
try:
    require_state(WorkItemDocument(state=None, body=''), ValueError('no state here'))
except ValueError as error:
    print(error)
"
```
Expect: two lines, `doing` and then `no state here`.

## Log (append only)

1. 2026-10-14 human: created.
