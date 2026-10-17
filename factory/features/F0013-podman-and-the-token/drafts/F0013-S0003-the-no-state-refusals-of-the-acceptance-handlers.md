# The no-state refusals of the acceptance handlers

## Assignment (as of log entry 1)

F0012-S0007 pinned the refused side of five callers of `require_state`. A caller builds its exception before `require_state` checks the state, so line coverage cannot show that no test reaches the refusal. F0012's feature acceptance ran `make mutants` and found three more such callers in `src/factory/application/acceptance.py`: `AcceptanceHandOver.handle` (line 219), `AcceptanceMerged.handle` through `_book` (line 292) and `AcceptanceClosed.handle` through `_record_close` (line 353). The mutant `no_state = None` survives at each of them, and no test names their messages. This story pins those three refusals: the exception type, its kind and reason, and that nothing is pushed or posted before it. It is F0012's proposed draft S0031, taken in as F0013's third story (FEATURE decision 2). The code already behaves as the criteria say. The tester writes the tests in a new module, and the coder expects to change nothing in `src/`. If a test fails, the code is wrong and the coder fixes it within the Interface.

## Interface

No new or changed names. The behaviour pinned is that of three existing handlers. Each handles an event that passes its own guards (the acceptance work item, the approval, the pull request in the state the handler wants), and the report it reads holds a document without a state, `WorkItemDocument(state=None, body=<any text>)`:

| Call | Where the stateless report is read | Raises |
|---|---|---|
| `AcceptanceHandOver(...).handle(event)` | the report on its branch | `CannotHandle` with `kind == "hand_over"` and `reason == "the work item on its branch has no state"` |
| `AcceptanceMerged(...).handle(event)` | the report on the merged main branch | `CannotHandle` with `kind == "merged"` and `reason == "the report on the main branch has no state"` |
| `AcceptanceClosed(...).handle(event)` | the report on its branch | `CannotHandle` with `kind == "closed"` and `reason == "the report on its branch has no state"` |

The kinds are the values of `_HAND_OVER`, `_MERGED` and `_CLOSED` in `factory.application.acceptance`.

Before it raises, a handler pushes nothing to the remote's acceptance branch or `main`, and it posts no comment. (`AcceptanceMerged._book` moves the report with `git mv` in the checkout before it checks the state; that local move is not pushed and is not part of this story.)

Tests: one new module, `tests/application/test_acceptance_no_state_refusals.py`. It brings the acceptance of `F0002-todo` to each event with the `walk` fixture of `tests/conftest.py` (`AcceptanceWalk` in `tests/acceptance_walk.py`), so that no fixture of the three handlers' modules is copied: `walk.open(FIRST)`, then `walk.record(FIRST, number, FIRST_RECORDS, stage="approval")` gives the `hand_over` event; recorded with `handed_over="approval"` and then `walk.merge(FIRST, number)`, the `merged` event; recorded with `handed_over="approval"` and then `walk.close(number)`, the `closed` event; `walk.evaluate()` returns each event. The real reader cannot give a stateless document here: `FrontmatterWorkItemReader.read` parses like `parse`, which raises `WorkItemFormatError("no front matter")` for a text without front matter and gives a state for any other. So each handler is built with `walk.definition` and `dataclasses.replace(boundaries, work_item_reader=<stand-in>)`, where the stand-in is a class in the new module deriving from `factory.application.files.WorkItemReader` (as `CLAUDE.md` asks of every implementation): its `parse` and `parse_specification` delegate to a `FrontmatterWorkItemReader`, and its `read` returns `WorkItemDocument(state=None, body=<the file's text>)` for the report's path in the checkout and delegates for any other path. The three cases are three tests or three rows of one parametrized test. No existing test module changes, so no leave is needed (FEATURE decision 12).

## Acceptance criteria

1. `AcceptanceHandOver.handle`, for a stateless report on its branch, raises `CannotHandle` with the kind and reason of the table. The remote's acceptance branch stays at the commit it had, and the fake hosting service holds no new comment.
2. `AcceptanceMerged.handle`, for a stateless report on the merged main branch, raises `CannotHandle` with the kind and reason of the table. The remote's `main` stays at the commit it had, and no new comment is posted.
3. `AcceptanceClosed.handle`, for a stateless report on its branch, raises `CannotHandle` with the kind and reason of the table. The remote's acceptance branch stays at the commit it had, and no new comment is posted.
4. What must still hold: a report with a state still runs through each of the three handlers (the existing tests of the three handlers' modules pass).
5. `make check` stays green.
6. docs: none. The behaviour is unchanged and already described where the acceptance handlers are; this story only pins it in tests.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_acceptance_no_state_refusals.py
```
Expect: the last line reads `3 passed in <t>s`, with no `failed`, `error` or `skipped` count.

```bash
grep -c 'has no state' src/factory/application/acceptance.py
```
Expect: `3`, the three messages the tests pin.

## Log (append only)

1. 2026-10-17 human: created from F0012's proposed draft S0031 (feature acceptance of 2026-10-17).
