# The no-state refusals of the acceptance handlers

<!-- proposed by feature acceptance of 2026-10-17; refine before promoting -->

## Assignment (as of log entry 1)

F0012-S0007 pinned the refused side of five callers of `require_state`. A caller builds its exception before `require_state` checks the state, so line coverage cannot show that no test reaches the refusal. F0012's feature acceptance ran `make mutants` and found three more such callers in `src/factory/application/acceptance.py`: `AcceptanceHandOver.handle` (line 219), `AcceptanceMerged.handle` through `_book` (line 292) and `AcceptanceClosed.handle` through `_record_close` (line 353). The mutant `no_state = None` survives at each of them, and no test names their messages. This story pins those three refusals: the exception type, its kind and reason, and that nothing is pushed or posted before it. The code already behaves as the criteria say. The tester writes the tests, and the coder expects to change nothing in `src/`. If a test fails, the code is wrong and the coder fixes it within the Interface.

## Interface

No new or changed names. The behaviour pinned is that of three existing handlers. Each handles an event that passes its own guards (the acceptance work item, the approval, the pull request in the state the handler wants), and the report it reads holds a document without a state, `WorkItemDocument(state=None, body=<any text>)`:

| Call | Where the stateless report is read | Raises |
|---|---|---|
| `AcceptanceHandOver(...).handle(event)` | the report on its branch | `CannotHandle` with `kind == "hand_over"` and `reason == "the work item on its branch has no state"` |
| `AcceptanceMerged(...).handle(event)` | the report on the merged main branch | `CannotHandle` with `kind == "merged"` and `reason == "the report on the main branch has no state"` |
| `AcceptanceClosed(...).handle(event)` | the report on its branch | `CannotHandle` with `kind == "closed"` and `reason == "the report on its branch has no state"` |

The kinds are the values of `_HAND_OVER`, `_MERGED` and `_CLOSED` in `factory.application.acceptance`.

Before it raises, a handler pushes nothing to the remote's acceptance branch or `main`, and it posts no comment.

Tests: one new module, `tests/application/test_acceptance_no_state_refusals.py`. It builds each handler as its own test module does: `tests/application/test_acceptance_hand_over.py`, `tests/application/test_acceptance_merged.py` and `tests/application/test_acceptance_closed.py`, with the fixtures of `tests/conftest.py`. The stateless report reaches the branch the same way those modules put a report there. No existing test module changes.

## Acceptance criteria

1. `AcceptanceHandOver.handle`, for a stateless report on its branch, raises `CannotHandle` with the kind and reason of the table. The remote's acceptance branch stays at the commit it had, and the fake hosting service holds no new comment.
2. `AcceptanceMerged.handle`, for a stateless report on the merged main branch, raises `CannotHandle` with the kind and reason of the table. The remote's `main` stays at the commit it had, and no new comment is posted.
3. `AcceptanceClosed.handle`, for a stateless report on its branch, raises `CannotHandle` with the kind and reason of the table. The remote's acceptance branch stays at the commit it had, and no new comment is posted.
4. For each of the three handlers, a report with a state still runs through as its own module's tests show; the new module needs no such test of its own.
5. `make check` stays green.
6. docs: none. The behaviour is unchanged and already described where the acceptance handlers are; this story only pins it in tests.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_acceptance_no_state_refusals.py -q
```
Expect: three tests, or three rows of one parametrized test, passed; no failure.

```bash
grep -c 'has no state' src/factory/application/acceptance.py
```
Expect: `3`, the three messages the tests pin.

## Log (append only)

1. 2026-10-17 feature acceptance of F0012: proposed.
