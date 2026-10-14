---
stage: accept
pr: 89
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Stops that cannot be done are counted errors

## Assignment (as of log entry 1)

Build the handlers of the `duplicate` and `pull_request_lookup` events and prove, for every stop that has no work to do, that the factory counts it as an error and reports it, instead of reporting success. In v1 three handlers (`duplicate`, `error pr-lookup`, and `ask` without a pull request) returned success and said nothing to the human. In v1.1 each raises `CannotHandle`, which the dispatcher counts per event and remote state, tries up to `ERROR_CAP` (3) times and then reports once on the work item's pull request (opened as a draft first when there is none), keyed so that a restart does not report it twice. The story builds the two handlers, tests the `ask` handler of S0002 for its stop, and adds a search test that no handler of the feature swallows an exception. It covers ST3.1 (a test per handler) and R28 and keeps kept thing 12 (a state no handler was written for is loud, never lucky). No morning observation.

## Interface

`src/factory/application/handlers/lookups.py`

```python
class DuplicateHandler(Handler):      # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self) -> None: ...
    def handle(self, event: Event) -> None: ...

class PullRequestLookupHandler(Handler):
    def __init__(self) -> None: ...
    def handle(self, event: Event) -> None: ...
```

Rules:

- `DuplicateHandler.handle` takes `target_of(event)` and always raises `CannotHandle("duplicate", reason)` where `reason` is `two work items share the id <id>` followed, when `event.detail` is not empty, by `: <event.detail>`.
- `PullRequestLookupHandler.handle` takes `target_of(event)` and always raises `CannotHandle("pull_request_lookup", reason)` where `reason` is `the pull request lookup for <branch> failed` followed, when `event.detail` is not empty, by `: <event.detail>`; `<branch>` is the snapshot's branch.
- Neither handler writes, posts or calls the hosting service, git or any other boundary.
- No module under `factory.application.handlers` catches `Exception` or `BaseException`, and none has a bare `except`: a handler that cannot do its work lets the error leave (R28).
- The report itself is the dispatcher's (F0006) and the stop service's (F0003): a `WorkItemStop` posted with `PostKey(kind="error", n=<first 12 digits of the remote state>)`.

Tests: `tests/application/handlers/test_lookups.py` and `tests/application/handlers/test_handlers_raise.py`. The dispatcher tests build `Dispatcher({kind: handler}, TickStatus(), StopService(boundaries))` with the real handler and count its calls with a small wrapper, a subclass of `Handler`, that delegates to it. `StopService.post` opens a draft pull request only for a branch that is on the remote with a commit beyond `main` (F0003-S0003); otherwise the dispatcher turns the report into a factory log line and posts nothing (F0006-S0003). The tests of criteria 4 to 7 therefore push the work item's branch with `human.push_file` (one commit beyond `main`) and give the snapshot that branch's head as `branch_commit`; for criteria 4, 5 and 7 the state holds the number of a pull request created in the fake on that branch, for criterion 6 it holds none. The test of criterion 6 calls `checkout.fetch()` after the push, so that `origin/work-item/<id>` resolves in the factory's checkout (`StopService` checks the branch through that remote-tracking ref), and takes `branch_commit` from it.

## Acceptance criteria

1. `DuplicateHandler.handle` raises `CannotHandle` with kind `duplicate` whose reason names the work item id and, for an event with `detail == "a.md, b.md"`, ends with `: a.md, b.md`; with an empty detail the reason is `two work items share the id <id>`.
2. `PullRequestLookupHandler.handle` raises `CannotHandle` with kind `pull_request_lookup` whose reason names the branch and, for an event with `detail == "rate limited"`, ends with `: rate limited`; with an empty detail the reason is `the pull request lookup for <branch> failed`.
3. Neither handler changes anything: after `handle` the hosting service has no new comment and the remote has no new commit.
4. A `duplicate` event dispatched four times on the same remote state gives the outcomes `error`, `error`, `reported`, `capped`; the handler is called three times; the work item's pull request has no factory post after the second dispatch, exactly one after the third, with key kind `error`, and still exactly one after the fourth.
5. A `pull_request_lookup` event gives the same sequence: outcomes `error`, `error`, `reported`, `capped`, three calls, one post of kind `error` after the third dispatch and still one after the fourth.
6. An `ask` event for a work item that has no pull request but whose branch is pushed (one commit beyond `main`), dispatched four times, gives the same outcomes and three calls of the `AskHandler`; after the third dispatch a draft pull request exists on the work item's branch and holds exactly one factory post of kind `error`, and after the fourth still exactly one.
7. After the report on a `duplicate` event, a new `TickStatus` (a restart) lets the same event be tried three times again, and the pull request still has exactly one factory post of kind `error`.
8. A search test over every module of `factory.application.handlers` (found by walking the package, and at least `recording`, `comments`, `questions`, `merged`, `closed`, `reject` and `lookups`) finds no `except` clause that is bare or that names `Exception` or `BaseException`.
9. make check stays green.
10. docs: `docs/operator-guide.md` lists three stops (a work item that exists twice, a failed pull request lookup, a question with no pull request to post it on), says that each is retried three times on the same state and then reported once on the pull request, and what to do for each; `docs/project-guide.md` states that a handler that cannot do its work raises `CannotHandle` and never reports success.

## Demo

```bash
uv run python -c "
from factory.application.handlers.lookups import DuplicateHandler, PullRequestLookupHandler
from factory.domain.events import Event
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
document = WorkItemDocument(state=WorkItemState(stage='doing'), body='# T\n')
snapshot = WorkItemSnapshot(id='F0001-S0001', path='factory/features/F0001-x/in-progress/F0001-S0001-y.md', folder='in-progress', branch='work-item/F0001-S0001', branch_commit=None, document=document)
for kind, handler, detail in (('duplicate', DuplicateHandler(), 'a.md, b.md'), ('pull_request_lookup', PullRequestLookupHandler(), 'rate limited')):
    try:
        handler.handle(Event(kind=kind, work_item=snapshot, remote_state='1' * 40, detail=detail))
    except Exception as error:
        print(type(error).__name__, error)
"
```
Expect: two lines: `CannotHandle cannot handle duplicate: two work items share the id F0001-S0001: a.md, b.md` and `CannotHandle cannot handle pull_request_lookup: the pull request lookup for work-item/F0001-S0001 failed: rate limited`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `lookups.py` names two concrete classes (`DuplicateHandler`, `PullRequestLookupHandler`) with signatures. Reason texts are exact, with and without `event.detail`. The no-I/O rule and the no-broad-except rule are stated. The report key (`PostKey(kind="error", n=<first 12 digits>)`) is named and belongs to F0006/F0003.
   - Criteria: every Interface behaviour has a criterion. The reason format with and without detail is covered by 1 and 2, no side effects by 3, and the dispatcher sequence `error, error, reported, capped` with call counts and post counts by 4 to 6. Restart is covered by 7 and the no-bare-except search by 8. Each is testable in one test function. The rules here are "always raises" and "never catches", so the passing and failing sides coincide. The empty-detail side is in 1 and 2, and the fourth dispatch after the cap in 4 to 6.
   - Demo: runnable with a single `uv run python -c`. The Expect line gives the two exact output lines, which can be compared directly.
   - Architecture: the handlers sit in `factory.application.handlers`, use only domain types and the dispatcher's `Handler`, and call no boundary. This is consistent with the layering in CLAUDE.md.
   - Scope: matches the FEATURE.md scope line "Stops that cannot be done" (ST3.1, R28). Nothing in Out of scope is touched. The setup the tests need is spelled out: pushed branch, `checkout.fetch()` and `branch_commit`.
3. tester: Wrote the red tests for the duplicate and pull request lookup handlers and for the rule that no handler swallows errors.
   - criterion 1: tests/application/handlers/test_lookups.py::test_the_duplicate_handler_raises_naming_the_work_item_and_the_detail (parametrized: detail `a.md, b.md` and empty detail)
   - criterion 2: tests/application/handlers/test_lookups.py::test_the_pull_request_lookup_handler_raises_naming_the_branch_and_the_detail (parametrized: `rate limited` and empty detail)
   - criterion 3: tests/application/handlers/test_lookups.py::test_a_lookup_handler_changes_nothing_on_the_hosting_service_or_the_remote (parametrized over both handlers. It checks that the comments on the pull request are unchanged and that the remote's `main` and work item branch heads have not moved.)
   - criterion 4: tests/application/handlers/test_lookups.py::test_a_duplicate_event_is_tried_three_times_and_reported_once
   - criterion 5: tests/application/handlers/test_lookups.py::test_a_pull_request_lookup_event_is_tried_three_times_and_reported_once
   - criterion 6: tests/application/handlers/test_lookups.py::test_an_ask_event_without_a_pull_request_is_reported_once_on_a_new_draft (the work item file is pushed with `human.push_file`, then `checkout.fetch()` runs, and `branch_commit` comes from `origin/work-item/<id>`)
   - criterion 7: tests/application/handlers/test_lookups.py::test_a_restart_tries_a_reported_duplicate_event_three_times_again_without_a_second_post
   - criterion 8: tests/application/handlers/test_handlers_raise.py::test_the_walk_finds_every_handler_module_of_the_feature (checks that the at-least set is present) and ::test_no_handler_module_catches_every_exception_or_has_a_bare_except (parametrized over every module that `pkgutil.walk_packages` finds; the modules are parsed with `tests/source_search.modules()`)

   Files created: tests/application/handlers/test_lookups.py, tests/application/handlers/test_handlers_raise.py. To wrap each real handler for the call counts, the dispatcher tests use a small `Counting(Handler)` wrapper that delegates to it. Criteria 4, 5 and 7 use the existing handler conftest fixtures `work_item` and `pull_request`: the branch is pushed with one commit beyond `main`, and the state holds a pull request in the fake.

   The test runner could not import `factory.application.handlers.lookups` (ModuleNotFoundError when collecting test_lookups.py). Until the module exists, the walk test in test_handlers_raise.py will also fail because `lookups` is missing. `make lint` is green. The type check was skipped as the stage says.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Built `src/factory/application/handlers/lookups.py` with `DuplicateHandler` and `PullRequestLookupHandler` (commit 122f04a). Each one takes `target_of(event).snapshot` and always raises `CannotHandle`. The reasons are `two work items share the id <id>` and `the pull request lookup for <branch> failed`. When `event.detail` is not empty, `: <detail>` is added, and a small shared helper `_with_detail` builds that suffix.
      - Main design decision: neither handler takes any boundary. Their constructors take no arguments, as the Interface says, so a stop with no work to do cannot write anything. Counting, the cap and the keyed report stay with the dispatcher and `StopService`.
      - Rejected alternative: passing `Boundaries` in for symmetry with the other handlers. It would go against the "no boundary" rule and would leave the handlers able to write.
      - Tests: all the tests the tester wrote pass. These include the `ask` stop with no pull request (criterion 6) and the search for broad `except` clauses (criterion 8). The existing handler modules needed no change for either.
      - Refactor: I read the diff and found nothing to change. The module is 38 lines and has no duplication.
      - `make check`: green, coverage 99.24 %.
      - Open: criterion 10 (the operator guide and project guide) belongs to the documenter.

   `make check`: check: green
5. reviewer: No findings.
      - Acceptance criteria: criteria 1 to 8 each have a test in `tests/application/handlers/test_lookups.py` or `tests/application/handlers/test_handlers_raise.py`. Each test checks the criterion it is named after:
        - Criteria 1 and 2 are parametrized over a detail and an empty detail, and they compare the exact reason and kind.
        - Criterion 3 checks that the comments and the remote's `main` and branch heads are unchanged.
        - Criteria 4 and 5 check the post count after the second, third and fourth dispatch, and the outcomes and the call count.
        - Criterion 6 checks that the draft pull request is opened only on the third dispatch, has exactly one `error` post, and that no second pull request or post appears on the fourth dispatch.
        - Criterion 7 is the restart test with a fresh `TickStatus`.
        - Criterion 8 walks the package with `pkgutil.walk_packages` and checks the at-least set.
        - The coder's entry records `make check` green, with 99.24 % coverage.
        - The "always raises" and "never catches" rules have no passing side. The empty-detail boundary is tested for both handlers.
      - Architecture: `src/factory/application/handlers/lookups.py` imports only `factory.application.dispatcher`, `factory.application.handlers.recording` and `factory.domain`. It holds no boundary and makes no I/O. Both classes derive from `Handler`.
      - Security: there are no suppression markers, no strings run as shell or SQL, and no `except` clauses anywhere in the handlers package.
      - Quality: the module, the public classes and the public methods have docstrings. The private `_with_detail` helper removes the duplicated suffix logic. There is no dead code.
      - Ticket hygiene: the coder's entry gives the main decision (handlers take no boundary) and the alternative it rejected (passing `Boundaries` for symmetry). `Assignment` matches what was built. Criterion 10 still states what the documenter must write.
      - Note, not a finding: the package's `__init__.py` is not walked by the criterion 8 test. It holds only a docstring today, so nothing is missed.
6. documenter: wrote the criterion 10 text and found no findings for the coder.
   - docs/operator-guide.md: new section "Stops that cannot be done" before "Claims, leases and the clock". It has a table of the three stops (a work item that exists twice, a failed pull request lookup, a question with no pull request), each with the last error in the report and what to do. It says each stop is tried three times on the same state and then reported once, on a draft pull request if there is none. It also says the handlers are not registered yet, so today the report reads `no handler for event kind <kind>`.
   - docs/project-guide.md: new subsection "A stop with no work to do is an error" before "Comments are copied by id". It states that a handler that cannot do its work raises `CannotHandle` and never reports success. It covers the two new handlers (no boundary, exact reasons, detail suffix), the key of the report, the rule against broad `except` clauses, and the tests.
   - Cross-read against the diff and found current: the `CannotHandle` line under Errors, "An event that keeps failing" and the `NOT_YET_HANDLED` lists in both guides (the two kinds are still unregistered).
   - `make check` is green (coverage 99.24 %).
   - Not touched, unrelated to this story: the operator guide's intro paragraph lists what is built and does not mention these handlers. It is a summary and still true.
   - Not run: the demo in the ticket. The code diff matches its Interface.

   `make check`: check: green
7. demo: ran the single command under `## Demo` from the repository root. No findings.

   - Command 1 (`uv run python -c "…"`, which builds both lookup handlers and calls `handle` with a detail): exit 0.

     ```
     CannotHandle cannot handle duplicate: two work items share the id F0001-S0001: a.md, b.md
     CannotHandle cannot handle pull_request_lookup: the pull request lookup for work-item/F0001-S0001 failed: rate limited
     ```

     Met its `Expect:` line. Both lines match the expected text exactly.

   - Criteria check: the output agrees with criteria 1 and 2 (the kind is `duplicate` or `pull_request_lookup`, the reason names the id or the branch and ends with `: <detail>`). Both handlers were built with no arguments and nothing was written, which fits criterion 3. The demo does not exercise criteria 4 to 8 (the dispatcher sequence, the restart, the except search) or criterion 10 (docs), and nothing in its output contradicts them. Earlier entries record their tests and a green `make check`.
