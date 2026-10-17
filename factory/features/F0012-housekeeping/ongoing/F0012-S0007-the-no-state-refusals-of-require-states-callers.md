---
stage: accept
pr: 159
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
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

Before it raises, `claim` leaves the remote's work item branch at the commit it had; `ask_crash_cap` posts nothing and opens no pull request; `stall` leaves the remote's work item branch at the commit it had and posts nothing.

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
2. intake: accepted
   - Interface: no new names; five existing public calls with concrete module paths, signatures, exceptions and messages. I checked the messages against `src/factory/application` (claims.py 76 and 111, recovery.py 57, task.py 140, stalls.py 137): they match.
   - Criteria: criteria 1 to 5 each name one call, the exception, its fields or message, and the side effects (branch unchanged, no post, no pull request). Each is testable by one test function. Criterion 2 covers both sides of `release` (no state refused, claimed state cleared) in one parametrized test. Every refusal in the Interface has its criterion, and the Interface has no passing side to add.
   - Demo: both commands are runnable. The expectations are checkable: `n passed` with n at least 6, and a `def test_` count of at least 5.
   - Architecture: the story only adds a test module under `tests/application/`, which mirrors the package. It uses the services' existing constructors and the fixtures of `tests/conftest.py`, with the fake hosting service and no mocks of the code under test.
   - Scope: within F0012 scope item 1.2, which takes in the parked draft F0008-S0007 (decision 5). It is not in "Out of scope". No test of another module changes.
3. tester: wrote the refusal tests for the five calls in one new module, `tests/application/test_no_state_refusals.py`. No existing test module changed.
   - criterion 1: tests/application/test_no_state_refusals.py::test_a_claim_of_a_document_without_a_state_is_refused_and_pushes_nothing
   - criterion 2: tests/application/test_no_state_refusals.py::test_a_release_refuses_a_document_without_a_state_and_clears_a_claim (parametrized: `no-state` raises with the message; `claimed` returns a state with `claim is None`)
   - criterion 3: tests/application/test_no_state_refusals.py::test_asking_the_crash_cap_question_of_a_document_without_a_state_is_refused_and_posts_nothing (the fake holds no pull request, so it holds no post either)
   - criterion 4: tests/application/test_no_state_refusals.py::test_composing_a_task_for_a_document_without_a_state_is_refused_with_its_path
   - criterion 5: tests/application/test_no_state_refusals.py::test_a_stall_of_a_document_without_a_state_is_refused_and_pushes_and_posts_nothing
   - criteria 6 and 7: not test criteria.

   Setup:
   - The claim and stall tests share an `opened` fixture. It pushes the story to `main`, starts it, and pushes the work item's branch with a stateful document, as `test_stalls.py` does. Both tests compare the remote branch head before and after the call with `git_support.remote_commit`.
   - The recovery test builds the `WorkItemSnapshot` directly with a stateless document. It reuses `crash_support.Rerun`, the stand-in rerun handler the crash-cap tests already use.
   - The task test builds `TaskContext` and `AgentDefinition` the way `test_task.py` does.

   Run result: unlike a usual tests stage, these tests are not red. The ticket says the code already behaves this way, and `make test` is green: all 6 cases pass and coverage is 99.51 %. So there is no module the test runner could not import, and nothing for the coder to fix in `src/`. `make lint` is green. I also ran `make types` because the code exists: green.

   No criterion needed interpreting.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (27.4 s)
4. coder: nothing to build. The tester's module `tests/application/test_no_state_refusals.py` passes against the code as it is, as the Assignment expected: all five calls already refuse a document without a state with the exception type, fields and message the Interface gives, and they write, push and post nothing. I changed nothing in `src/` and made no commit.
   - Design decision: I left the code as it is. The tests are green, so changing code would only add risk and go beyond the ticket's scope. I rejected tightening the call sites so that each one builds its exception only after `require_state` finds no state. The coverage gap the Assignment describes is now closed by these tests, so that change is not needed and it is not in the Interface.
   - Refactor: there is no diff outside `factory/` and `tests/` (`git diff main...HEAD -- . ':!factory' ':!tests'` is empty), so nothing needed refactoring.
   - Noticed, not touched: nothing.
   `make check`: check: green (test: green, coverage 99.51 %)

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: No findings.
   - Scope: outside `factory/`, the only change the story made is the new module `tests/application/test_no_state_refusals.py`. Nothing changed in `src/`, as the Assignment expected. The other files in the diff (`docs/runs/2026-10-12-overnight/night-log.md`, `planning/overnight/restructure-after-f0011.md`, `planning/overnight/briefs/draft-F0012-S0028-S0029.md`) come from the human's own commits 9e7b43a and fec8d9d, which reached the branch with main. Those are the human's files and not under review.
   - Criteria 1 to 5: each has one test, and each test checks what the Interface states.
     - claim: the `ValueError` message, and the remote branch head is the same before and after (`remote_commit`).
     - release: one parametrized test, with the `no-state` row raising the message and the `claimed` row returning `claim is None`.
     - ask_crash_cap: `CannotHandle` with `kind == "crash"` and the reason built from `snapshot.id`. The fake holds no pull request, so it holds no post either.
     - compose: `WorkItemFormatError` with the `fault` and `path == context.path`.
     - stall: called with `stage_start=None`, `cost=None` and a pull request given; checks the message, the unchanged branch head and `factory_posts == []`.
   - The Interface has no other limit or refused side to test. The coder's entry says `make check` is green and that `make duplicates` reports 0 new findings.
   - Architecture and security: nothing in `src/` changed. The test uses the real git remote fixtures and the fake hosting service, mocks nothing, and writes only under `tmp_path`.
   - Quality: the module docstring is present. `_definition` follows the pattern each sibling test module uses. The `opened` fixture is shared by the claim and stall tests.
   - Ticket hygiene: the coder's entry records the decision to leave the code as it is and what was rejected (building each exception only after the state check). The Assignment matches what was done. Docs criterion 7 ("none") still holds.
6. documenter: wrote nothing. Criterion 7 says `none`, and the diff outside `factory/` is only the new test module `tests/application/test_no_state_refusals.py`; `src/` is unchanged.
   - Cross-read: `docs/project-guide.md` (line 470, `require_state` and the caller building its own exception, and line 429 on the journal's `_state_of`) matches the code and the five refusals the tests pin. I found it current.
   - README and the other docs don't mention these calls, so the diff leaves them current.
   - Stale but untouched: nothing.
   - Findings: none. I didn't run `make check`, because I changed no file outside README and docs; the factory's check after this stage is the gate.

   `make check`: check: green
   `make documents`: documents ok
7. demo: both commands met their expectations; no findings.

   Command 1: `uv run pytest --no-header -p no:cacheprovider tests/application/test_no_state_refusals.py`
   ```
   ......                                                                   [100%]
   6 passed in 0.31s
   ```
   Met: the last line is `6 passed in 0.31s`, and the expectation asks for at least 6 (the five calls plus the second row of criterion 2).

   Command 2: `grep -c "def test_" tests/application/test_no_state_refusals.py`
   ```
   5
   ```
   Met: 5, one test function per call.

   Criteria check: the demo contradicts no criterion. Criteria 1 to 5 are pinned by the 6 passing cases, as the tester's entry maps them. Criterion 6 (`make check` green) is the factory's own gate after this stage. Criterion 7 (docs: none) is consistent with the diff, which adds only the test module.
