---
stage: tests
pr: 79
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# A report that fails with a git error

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

The feature acceptance of F0006 hand-mutated the dispatcher. One mutant survived: a report that fails with an exception other than `HostingServiceError` could be marked as reported, and no test would notice. The rule is F0006-S0003's: "a report that raises any `Exception` leaves the entry unreported and returns `"error"`; the next dispatch of the same event on the same state makes the report again; a failed report does not count". Its criterion 19 tests the rule only with `HostingServiceError`.

`StopService.post` raises `GitError` too. For a work item without a pull request it resolves the branch through `Git.resolve` before it opens a draft pull request, and a broken checkout fails there. Such a report would be lost without a word, because the hosting-service exception would not apply (it turns a report into a log line only for `HostingServiceError` on a work item without a branch on the remote).

This story adds the missing criteria for the non-hosting failure. It is expected to need no code change: `src/factory/application/dispatcher.py` already behaves this way. The coder confirms that and builds nothing if the tests pass. Keeps kept thing 12 (errors capped and reported, never lost). Uses `Dispatcher` and `StopService` (F0006-S0003, F0003-S0002).

## Interface

No new names. The rule under test, in `src/factory/application/dispatcher.py` (`Dispatcher.dispatch`, unchanged):

```python
def dispatch(self, event: Event) -> DispatchOutcome: ...
    # a report that raises an Exception other than HostingServiceError returns "error",
    # leaves the entry unreported with its count and last_error unchanged, and writes no log line,
    # whatever the snapshot's branch_commit; the next dispatch of the event on the same remote
    # state makes the report again without calling the handler
```

Tests: new test functions in `tests/application/test_dispatcher.py`, with its fixtures and helpers (`boundaries`, `hosting`, `human`, `checkout`, `remote`, `Failing`, `RecordingLog`, `_snapshot`, `_event`, `_entry`, `_report_key`); no existing test, helper or import of that module changes. The `GitError` comes from the real `GitCli`, not from a test double. The checkout's `.git` directory (`boundaries.checkout / ".git"`) is renamed to a sibling of the checkout (`boundaries.checkout.with_name("git-away")`) just before the dispatch that makes the report, and renamed back afterwards. `GitCli.resolve` then fails with `GitError` ("not a git repository"). The work item has no pull request, so `StopService.post` reaches `Git.resolve`.

## Acceptance criteria

1. For a work item without a pull request whose branch is on the remote with a commit beyond `main`, and whose handler raises `ValueError("boom")`: when the checkout's `.git` is gone for the third dispatch, `dispatch` returns `"error"`. The entry is not `reported`, its `count` is 3 and its `last_error` is `ValueError: boom`. The hosting service holds no pull request, and the given log holds no line.
2. After `.git` is back, the next dispatch of the same event does not call the handler. It opens the draft pull request on the work item's branch, posts the one keyed report there and returns `"reported"`. The dispatch after that returns `"capped"` and posts nothing.
3. The log-line exception stays limited to `HostingServiceError`. For a work item whose `branch_commit` is `None` (no pull request), a `GitError` from the report (the checkout's `.git` gone for the third dispatch) gives `"error"`, not `"reported"`. The entry is not `reported`, its `count` is 3 and its `last_error` is `ValueError: boom`, and the given log holds no line. After `.git` is back, the next dispatch does not call the handler; its report fails with `HostingServiceError` (the branch is not on the remote), so it writes the one line `error cap reached on <event key>: ValueError: boom` to the given log and returns `"reported"`, and the hosting service holds no pull request.
4. make check stays green.
5. docs: in `docs/operator-guide.md`, "An event that keeps failing", the sentence on a report that cannot be posted names a git failure in the factory's checkout next to the hosting service being down, as a reason the report is tried again on the next tick.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider --cov=factory.application.dispatcher --cov-branch --cov-report=term-missing tests/application/test_dispatcher.py
```
Expect: the coverage line of `src/factory/application/dispatcher.py` shows `100%` with an empty `Missing` column, and the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-14 human: created.
2. intake: accepted
   - Interface: no new names; it names the unchanged `Dispatcher.dispatch` in `src/factory/application/dispatcher.py`. It names the test module, the fixtures and helpers to reuse, and how the `GitError` is produced: the real `GitCli`, with `.git` renamed to `git-away` and back.
   - Criteria: each is testable by one test function. Criteria 1 and 2 cover the failing report and the retry. Criterion 3 covers the log-line exception, with both its failing side (a `GitError` gives `"error"` and no log line) and its passing side (a `HostingServiceError` gives the log line and `"reported"`). Every behaviour in the Interface comment has a criterion: `"error"`, the unchanged count and `last_error`, no log line, the retry that skips the handler, and `"capped"` afterwards.
   - Demo: the pytest command is runnable. The `Expect:` line checks against the output: 100% coverage of the dispatcher with an empty `Missing` column, and `<n> passed` with no failed, error or skipped count.
   - Architecture: tests only, no new layer or dependency. The real git wrapper is used and not faked, as CLAUDE.md requires.
   - Scope: this is within F0006's dispatcher scope, and the feature's story list names it as proposed by the feature acceptance. It touches nothing under Out of scope.
