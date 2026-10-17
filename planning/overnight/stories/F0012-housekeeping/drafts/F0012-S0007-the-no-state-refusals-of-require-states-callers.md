# The no-state refusals of require_state's callers

<!-- takes in the parked draft F0008-S0007 (proposed by F0008's feature acceptance of 2026-10-15) -->

## Assignment (as of log entry 1)

F0008-S0006 moved 17 checks of a work item's state onto `require_state(document, error)` and promised that "no exception type or message changes". Its only pin was that the existing tests pass. The second feature acceptance of F0008 ran a hand mutation pass. It found that five public calls can be given a document without a state, and that each one could raise another exception type, kind or message without any test failing:

- `ClaimService.claim`;
- `ClaimService.release`;
- `RecoveryHandler.ask_crash_cap`;
- `TaskComposer.compose`;
- `StallService.stall`.

Line coverage does not show the gap. Each call site builds its exception before `require_state` checks the state, so the line that builds it runs on every happy path.

The human folded it into this feature (FEATURE decision 5). This story pins the refused side of those five calls: the exception type, its fields, and that nothing is written or pushed. The code already behaves as the criteria say. The tester writes the tests, and the coder expects to change nothing in `src/`. If a test fails, the code is wrong and the coder fixes it within the Interface below.

## Interface

No new or changed names. The behaviour pinned is that of five existing public calls, each given a `WorkItemDocument(state=None, body=<any text>)`:

| Call | Raises |
|---|---|
| `ClaimService(boundaries, instance, definition).claim(branch, path, document, stage)` (`src/factory/application/claims.py`) | `ValueError` with the message `the work item has no state to claim` |
| `ClaimService(...).release(document)` (`src/factory/application/claims.py`) | `ValueError` with the message `the work item has no state to release` |
| `RecoveryHandler(boundaries, definition, claims, run).ask_crash_cap(snapshot)` (`src/factory/application/recovery.py`), the snapshot's `document` without a state | `CannotHandle` with `kind == "crash"` and `reason == "work item <snapshot.id> has no state"` |
| `TaskComposer(boundaries, definition, environment).compose(context, agent)` (`src/factory/application/task.py`), `context.document` without a state | `WorkItemFormatError` with `fault == "the document has no state"` and `path == context.path` |
| `StallService(boundaries, instance, definition).stall(context, reason)` (`src/factory/application/stalls.py`), with `context.document` without a state, `stage_start=None`, `cost=None` and `pull_request` given | `ValueError` with the message `the work item has no state to stall` |

None of the five commits, pushes, posts or starts an agent run before it raises.

Tests: one new module, `tests/application/test_no_state_refusals.py`. It builds each service as its own test module does: `tests/application/test_claims.py` for `ClaimService`, `tests/application/test_recovery_cap.py` for `RecoveryHandler`, `tests/application/test_task.py` for `TaskComposer`, and `tests/application/test_stalls.py` for `StallService`, using the fixtures of `tests/conftest.py`. No existing test module changes.

## Acceptance criteria

1. `ClaimService.claim` with a document without a state raises `ValueError` whose `str` is `the work item has no state to claim`. The remote's work item branch is at the commit it had before the call.
2. `ClaimService.release` with a document without a state raises `ValueError` whose `str` is `the work item has no state to release`. With a document that has a claimed state, the same call returns a document whose state has `claim is None` (both sides in one parametrized test).
3. `RecoveryHandler.ask_crash_cap` with a snapshot whose document has no state raises `CannotHandle` with `kind == "crash"` and `reason == f"work item {snapshot.id} has no state"`. The fake hosting service holds no post and no pull request afterwards.
4. `TaskComposer.compose` with a context whose document has no state raises `WorkItemFormatError` with `fault == "the document has no state"` and `path == context.path`.
5. `StallService.stall` with a context whose document has no state (`stage_start=None`, `cost=None`, a `pull_request` given) raises `ValueError` whose `str` is `the work item has no state to stall`. The remote's work item branch is at the commit it had before the call, and the fake hosting service holds no post.
6. make check stays green.
7. docs: none. The project guide already names `require_state` as the one way to get a document's state and says the caller builds its own exception. These tests pin what it says.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_no_state_refusals.py
```
Expect: the last line is `<n> passed in <time>`, with n at least 6 (criterion 2 has two rows).

```bash
grep -c "def test_" tests/application/test_no_state_refusals.py
```
Expect: a number of at least 5, one test function per call.

## Log (append only)

1. 2026-10-17 human: created.
