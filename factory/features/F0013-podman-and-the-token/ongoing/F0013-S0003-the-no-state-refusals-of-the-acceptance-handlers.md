---
stage: doing
pr: 184
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
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
2. intake: accepted. Nothing in the story was changed.
   - Interface: it names no new code, only three existing handlers. I checked `acceptance.py`: lines 219, 292 and 353 build `CannotHandle` with the exact kinds and reasons in the table, and `_HAND_OVER`, `_MERGED` and `_CLOSED` hold `hand_over`, `merged` and `closed`. The stand-in reader and the `walk` fixture sequence are specified concretely.
   - Criteria: criteria 1 to 3 are each one test. Each gives the exception type, kind and reason, and the unchanged remote ref and no new comment. Each criterion covers the refusing side of the no-state rule. Criterion 4 (a report with a state still passes) is covered by the existing tests of the three handlers' modules. Criteria 5 and 6 are the closing two.
   - Demo: both commands can be run. The expectations can be checked against the output: `3 passed`, and a grep count of `3`. The grep count matches the three lines found.
   - Architecture: the tests sit in `tests/application/`. The stand-in derives from the `WorkItemReader` interface, as `CLAUDE.md` asks. It adds no new dependency, and git and the hosting service are not faked beyond the existing fake.
   - Scope: the story is inside F0013's scope (taken in from F0012's draft S0031, FEATURE decision 2). It touches nothing listed under Out of scope and changes no existing test (decision 12).
3. tester: wrote the three no-state refusals as rows of one parametrized test.
   - criterion 1: tests/application/test_acceptance_no_state_refusals.py::test_a_stateless_report_is_refused_before_anything_is_pushed_or_posted[hand_over]
   - criterion 2: tests/application/test_acceptance_no_state_refusals.py::test_a_stateless_report_is_refused_before_anything_is_pushed_or_posted[merged]
   - criterion 3: tests/application/test_acceptance_no_state_refusals.py::test_a_stateless_report_is_refused_before_anything_is_pushed_or_posted[closed]
   - criterion 4: covered by the existing tests of the three handlers' modules, which I did not change.
   - criteria 5 and 6: the closing criteria, so no test.
   How each row works: the `walk` fixture brings the acceptance to the event, as the Interface describes. The row asserts that `walk.evaluate()` returns the expected kind. It then builds the handler with `walk.definition` and `dataclasses.replace(boundaries, work_item_reader=StatelessReportReader(...))`. `StatelessReportReader` is defined in the module and derives from `factory.application.files.WorkItemReader`. Its `read` returns `WorkItemDocument(state=None, body=<the file's text>)` for `boundaries.checkout / report_of(FIRST)`, and it hands every other path and both parse methods to `FrontmatterWorkItemReader`. Each row asserts the `CannotHandle` kind and reason from the table. It also asserts that the remote's watched branch (the acceptance branch, or `main` for merged) holds the same commit as before, and that `hosting.list_comments(number)` is unchanged.
   Files created: tests/application/test_acceptance_no_state_refusals.py.
   Imports: every module the test runner loads already exists. No test is red, as expected: the story says the code already behaves this way, so the coder should change nothing in `src/`. `make test` and `make lint` are green. I did not run the type check, as the stage says.
   Rejected: one test function per handler. The CLAUDE.md test rules want the sides of one rule as rows of one parametrized test.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (27.8 s)
