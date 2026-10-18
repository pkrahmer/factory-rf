---
stage: done
pr: 91
blocked: null
comments_seen: 2
round: 0
attempts: 0
---
# The pull request read before every agent run

## Assignment (as of log entry 1)

Build the gate that reads the pull request before a stage is run, and register the handlers of this feature in the production wiring. A stage can be due for a work item whose pull request the human has meanwhile closed or merged; running the agent first would spend a run on a story the human has already decided. `RunGate` is a handler for `run` events that wraps the stage protocol's handler: it reads the pull request's state first and, when it is closed or merged, hands the event to the `closed` or the `merged` handler instead, so the human's act is handled before any agent run; when the work item has no pull request, or the pull request is open, the stage runs as before. By the human's answer to questionnaire 1, Q20 (A), the wiring grows with each feature: `factory.entry.wiring.build_handlers` (F0006-S0007), the one place that registers a handler, gets an entry for every event kind this feature owns, with the `run` entry gated around F0006's `RunHandler`, and `NOT_YET_HANDLED` shrinks to `crash`, `expired` and `acceptance_due`. No second registry is built in `factory.application`. Registering the handlers breaks three tests that F0006-S0007 wrote (its criteria 4, 5 and 9); this story changes exactly those three, with the human's leave (Q20 A), and names them in the Interface. It keeps the planner's note that the pull request's state is read before every agent run (v1's `run` step 3) and applies R22 (the human's act comes first). Every other path to an agent run must go through the gate too: F0008's rerun after a crash passes its run through `RunGate`, because a story whose head branch the hosting service deleted reads as fresh and the gate is the only place that notices its closed pull request. No morning observation.

## Interface

`src/factory/application/handlers/run_gate.py`

```python
class RunGate(Handler):      # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries, run: Handler, closed: Handler, merged: Handler) -> None: ...
    def handle(self, event: Event) -> None: ...
    @property
    def run(self) -> Handler: ...
    @property
    def closed(self) -> Handler: ...
    @property
    def merged(self) -> Handler: ...
```

`src/factory/entry/wiring.py` (grown; F0006-S0007 created it)

```python
NOT_YET_HANDLED: tuple[EventKind, ...] = ("crash", "expired", "acceptance_due")

def build_handlers(boundaries: Boundaries, definition: PipelineDefinition, instance: Name,
                   environment: Mapping[str, str]) -> dict[EventKind, Handler]: ...
```

Rules:

- `RunGate.handle` takes `target_of(event)`. When `target.pull_request` is `None` it calls `run.handle(event)` unchanged and reads nothing from the hosting service.
- Otherwise it reads `HostingService.get_pull_request(number)` once, before any handler is called, and passes on the event copied with `pull_request` set to the view read. A view whose state is `closed` goes to `closed.handle` with the event's `kind` set to `closed`; a view whose state is `merged` goes to `merged.handle` with the kind set to `merged`; a view whose state is `open` goes to `run.handle`, with the kind unchanged.
- A failing read leaves `handle` by raising, and none of the three handlers is called.
- `build_handlers` returns a dict with exactly the keys `idle`, `run`, `comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `duplicate` and `pull_request_lookup`. With `closed = ClosedHandler(boundaries, definition)` and `merged = MergedHandler(boundaries)` the values are `IdleHandler()`, `RunGate(boundaries, RunHandler(boundaries, instance, definition, environment), closed, merged)`, `CommentHandler(boundaries)`, `AskHandler(boundaries, definition)`, `merged`, `closed`, `RejectHandler(boundaries)`, `HandOverHandler(boundaries, definition)`, `DuplicateHandler()` and `PullRequestLookupHandler()`: the gate holds the very instances registered for `closed` and `merged`. The mapping type-checks because every handler inherits `Handler`.
- `NOT_YET_HANDLED` and the keys of `build_handlers`' result partition `EventKind` (F0006-S0007's rule stays): the three kinds left are F0008's (`crash`, `expired`) and F0009's (`acceptance_due`).
- The changed tests of F0006-S0007, all in its `tests/entry/test_wiring_handlers.py`, and nothing else of that file: the test of its criterion 4 now asserts that the keys of `build_handlers(...)` include `idle` and `run`, that the `idle` handler is an `IdleHandler` and that the `run` handler is a `RunGate`; the test of its criterion 5 compares `unhandled_kinds(build_handlers(...))` with `list(NOT_YET_HANDLED)` only and no longer lists the eleven kinds; the test of its criterion 9 dispatches a `crash` event, not a `comment` event, and expects the last error `UnhandledEvent: no handler for event kind crash`. The Demo of F0006-S0007 prints the old constant and is out of date after this story; the human's leave covers the three tests only.

Tests: `tests/application/handlers/test_run_gate.py`; `tests/entry/test_wiring_human_handlers.py` (a new file) for `build_handlers` and `NOT_YET_HANDLED` as this story leaves them; the three changed tests in `tests/entry/test_wiring_handlers.py`. The unit tests of the gate use small recording handlers as stand-ins for the three handlers it calls, each a subclass of `Handler`; the integration tests use the real `ClosedHandler` and `MergedHandler`, real git and the fake hosting service. The wiring tests use the shared fixtures of F0006-S0007 (`remote`, `checkout`, `human`, `hosting`, `agent_runtime`, `boundaries`, `agent_home`, `clock`) and start a complete story as it does.

## Acceptance criteria

1. For a work item whose state has no pull request, `RunGate.handle` calls the run handler once with the event unchanged, and the hosting service is not read: with `get_pull_request` set to fail, no error occurs.
2. For an open pull request, the pull request is read exactly once and the run handler is called once, with `event.pull_request` equal to the view read and the kind unchanged; the closed and merged handlers are not called.
3. The pull request is read before the run handler is called: at the moment the run handler is entered, the read has already happened.
4. For a closed pull request, the closed handler is called once with the kind `closed` and the view read, and the run handler is not called.
5. For a merged pull request, the merged handler is called once with the kind `merged` and the view read, and the run handler is not called.
6. When `get_pull_request` fails, `handle` raises `HostingServiceError` and none of the three handlers is called.
7. A story at `doing` whose pull request the human closed while its stage was due, handled through a `RunGate` with the real `ClosedHandler`, ends in `backlog/` on `origin/main` with its branch deleted, and the run handler was never called.
8. A story whose pull request the human merged while its stage was due, handled through a `RunGate` with the real `MergedHandler`, is archived under `done/` on `origin/main`, and the run handler was never called.
9. `build_handlers(...)` returns a dict whose keys are exactly `idle`, `run`, `comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `duplicate` and `pull_request_lookup`.
10. The values of `build_handlers(...)` are instances of `IdleHandler`, `CommentHandler`, `AskHandler`, `MergedHandler`, `ClosedHandler`, `RejectHandler`, `HandOverHandler`, `DuplicateHandler`, `PullRequestLookupHandler` and, for `run`, `RunGate`, whose `run` property is a `RunHandler` and whose `closed` and `merged` properties are the very instances registered for `closed` and `merged`.
11. The `run` entry of `build_handlers(...)` runs the stage of a started story with no pull request: `agent_runtime.requests()` then holds exactly one request, as in F0006-S0007's first criterion.
12. `NOT_YET_HANDLED` is `("crash", "expired", "acceptance_due")`, and `unhandled_kinds(build_handlers(...))` equals `list(NOT_YET_HANDLED)`; no kind of `NOT_YET_HANDLED` is a key of the mapping and every other kind is.
13. A `crash` event dispatched through a `Dispatcher` built over `build_handlers(...)` returns `error`, and the status holds `UnhandledEvent: no handler for event kind crash` as the last error.
14. make check stays green.
15. docs: `docs/project-guide.md` states that the pull request is read before every agent run, that a close or a merge found then is handled first, that every path to an agent run (the rerun after a crash included) goes through `RunGate`, and lists the event kinds that `build_handlers` registers for this feature and the three that `NOT_YET_HANDLED` still lists; `docs/operator-guide.md` says that a story whose pull request was closed or merged while its stage waited to run is discarded or archived without that run.

## Demo

```bash
uv run python -c "
from types import SimpleNamespace
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.dispatcher import Handler
from factory.application.handlers.run_gate import RunGate
from factory.domain.events import Event
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState

class Spy(Handler):
    def __init__(self, name, calls):
        self.name = name
        self.calls = calls
    def handle(self, event):
        self.calls.append((self.name, event.kind))

hosting = FakeHostingService()
calls = []
gate = RunGate(SimpleNamespace(hosting=hosting), Spy('run', calls), Spy('closed', calls), Spy('merged', calls))

def event(number):
    document = WorkItemDocument(state=WorkItemState(stage='doing', pull_request=number), body='# T\n')
    snapshot = WorkItemSnapshot(id='F0001-S0001', path='factory/features/F0001-x/in-progress/F0001-S0001-y.md', folder='in-progress', branch='work-item/F0001-S0001', branch_commit='1' * 40, document=document)
    return Event(kind='run', work_item=snapshot, remote_state='1' * 40)

opened = hosting.create_pull_request('work-item/a', 'a', 'body', draft=True)
closed = hosting.create_pull_request('work-item/b', 'b', 'body', draft=True)
merged = hosting.create_pull_request('work-item/c', 'c', 'body', draft=True)
hosting.close_by_human(closed.number)
hosting.merge_by_human(merged.number, '2' * 40)
for number in (opened.number, closed.number, merged.number):
    gate.handle(event(number))
gate.handle(event(None))
print(calls)
"
```
Expect: one line, `[('run', 'run'), ('closed', 'closed'), ('merged', 'merged'), ('run', 'run')]`: the open pull request and the work item without a pull request reach the run handler, the closed one reaches the closed handler as a `closed` event, the merged one the merged handler as a `merged` event.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `RunGate` in `application/handlers/run_gate.py` (constructor, `handle`, and the `run`, `closed` and `merged` properties) and the grown `entry/wiring.py` (`NOT_YET_HANDLED`, `build_handlers`) are concrete. They name the modules, the handler instances and the three F0006-S0007 tests that change (its criteria 4, 5 and 9). Their new assertions are stated.
   - Criteria: each is testable by one test function. The rules and their failing sides are covered:
     - No pull request: criterion 1 (no read).
     - Open: criteria 2 and 3.
     - Closed: criteria 4 and 7.
     - Merged: criteria 5 and 8.
     - A failing read: criterion 6 (raises, no handler called).
     - Wiring: criteria 9 to 13 (exact keys, instance types, the shared `closed` and `merged` instances, the `crash` error).
   - Demo: runnable with the fake hosting service. Its `Expect:` line gives the exact output list.
   - Architecture: the gate is in the application layer and uses only `Boundaries` and the hosting-service interface. Registration stays in `factory.entry.wiring`, with no second registry, as the human decided in questionnaire 1 Q20 (A).
   - Scope: within FEATURE.md ("the pull request read before every agent run"). The rerun after a crash stays with F0008. Nothing here falls under "Out of scope".
3. tester: Wrote red tests for every acceptance criterion. `make lint` is green. `make test` stops at collection because `factory.application.handlers.run_gate` does not exist yet, which is the expected failure.

   Criterion → test:
   - criterion 1: tests/application/handlers/test_run_gate.py::test_a_work_item_without_a_pull_request_runs_unchanged_without_a_read
   - criterion 2: tests/application/handlers/test_run_gate.py::test_an_open_pull_request_is_read_once_and_the_stage_runs_with_the_view
   - criterion 3: tests/application/handlers/test_run_gate.py::test_the_pull_request_is_read_before_the_run_handler_is_entered
   - criterion 4: tests/application/handlers/test_run_gate.py::test_a_closed_pull_request_goes_to_the_closed_handler_as_a_closed_event
   - criterion 5: tests/application/handlers/test_run_gate.py::test_a_merged_pull_request_goes_to_the_merged_handler_as_a_merged_event
   - criterion 6: tests/application/handlers/test_run_gate.py::test_a_failing_read_raises_and_calls_no_handler
   - criterion 7: tests/application/handlers/test_run_gate.py::test_a_story_closed_while_its_stage_was_due_is_discarded_without_a_run
   - criterion 8: tests/application/handlers/test_run_gate.py::test_a_story_merged_while_its_stage_was_due_is_archived_without_a_run
   - criterion 9: tests/entry/test_wiring_human_handlers.py::test_build_handlers_registers_the_kinds_of_the_human_on_the_pull_request
   - criterion 10: tests/entry/test_wiring_human_handlers.py::test_each_kind_has_its_handler_and_the_gate_shares_the_closed_and_merged_handlers
   - criterion 11: tests/entry/test_wiring_human_handlers.py::test_the_run_entry_runs_the_stage_of_a_started_story_without_a_pull_request. It drives a `Tick` over `build_handlers`.
   - criterion 12: tests/entry/test_wiring_human_handlers.py::test_only_the_crash_expiry_and_acceptance_kinds_are_not_yet_handled
   - criterion 13: tests/entry/test_wiring_handlers.py::test_an_event_not_yet_handled_is_a_counted_error, changed to dispatch a `crash` event (this is F0006-S0007's criterion 9).

   Unit-test setup for the gate:
   - The three handlers are recording subclasses of `Handler`.
   - Hosting reads are counted by a `CountingHosting` subclass of `FakeHostingService`, swapped into the `boundaries` fixture with `dataclasses.replace`.
   - The run handler's stand-in records how many reads had happened when it was entered; criterion 3 uses this.
   - Criteria 7 and 8 use the real `ClosedHandler` and `MergedHandler`, real git through `human`/`checkout`, and the fake hosting service's `close_by_human`/`merge_by_human`.

   Changed tests in tests/entry/test_wiring_handlers.py, exactly the three the Interface names (the human's leave, Q20 A):
   - The criterion 4 test was renamed to test_build_handlers_registers_the_idle_handler_and_the_gated_run_handler. It now checks that the keys include `idle` and `run`, that `idle` is an `IdleHandler` and that `run` is a `RunGate`.
   - The criterion 5 test now compares `unhandled_kinds` with `list(NOT_YET_HANDLED)` only.
   - The criterion 9 test now dispatches `crash` and expects `UnhandledEvent: no handler for event kind crash`.
   - The import of `RunHandler` became `RunGate`.

   Files created:
   - tests/application/handlers/test_run_gate.py
   - tests/entry/test_wiring_human_handlers.py

   File modified:
   - tests/entry/test_wiring_handlers.py

   Modules that could not be imported: factory.application.handlers.run_gate. All three test modules fail at collection because of it.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: I built `RunGate` (src/factory/application/handlers/run_gate.py) and the expanded `build_handlers` / `NOT_YET_HANDLED` (src/factory/entry/wiring.py), committed as 38684ce. Lint, types, layers, sast, secrets and licences pass. Coverage is 99 %. Every test passes except one: tests/application/handlers/test_run_gate.py::test_a_story_merged_while_its_stage_was_due_is_archived_without_a_run (criterion 8).

   Why it fails: the test's story body is `BODY = "# First story\n\nRewritten by the factory on the branch.\n"`, which has no `## Journal` section. The gate hands the event to the real `MergedHandler`, as the criterion requires. That handler appends a `done` entry through `append_entry`, which raises `WorkItemFormatError: missing section: ## Journal`. The test is out of line with the existing `MergedHandler`, not with the gate. Every work item has a journal section, and tests/application/handlers/test_merged.py uses a body that contains one. The closed test (criterion 7) passes with the same body only because discarding the story appends no entry.

   Options:
   (A) The tester changes `BODY` in tests/application/handlers/test_run_gate.py to include a journal section that matches the state's single `created` record, e.g. `"# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"` (as test_merged.py does). Criterion 7 keeps passing with that body.
   (B) Make `MergedHandler` tolerate a body without a journal. This changes an existing handler outside this story's scope and weakens a format rule. I reject it.

   I recommend (A). With your answer I will end with `tests` naming exactly that change.
5. human (pull request comment, 2026-10-14): (A): the tester changes `BODY` in `tests/application/handlers/test_run_gate.py` to include a journal section matching the state's single `created` record, as `test_merged.py` does; `MergedHandler` stays as it is. End with `tests` and name exactly that change.
6. coder: Following the human's answer (A) in entry 5, I am sending the ticket back with exactly one test change for the tester. In tests/application/handlers/test_run_gate.py, change line 30 from `BODY = "# First story\n\nRewritten by the factory on the branch.\n"` to `BODY = "# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"`, the same value tests/application/handlers/test_merged.py uses on line 34. The journal section then matches the state's single `created` record. After that change, `MergedHandler` can append its `done` entry, and test_a_story_merged_while_its_stage_was_due_is_archived_without_a_run (criterion 8) should pass. Criterion 7 does not depend on the body, because discarding a story appends no entry. `MergedHandler` stays as it is. I changed no code in this run: `RunGate` and the larger wiring are in 38684ce, and every other test already passed against them. The Assignment is unchanged. The refactor step is still open and I will do it when the ticket returns to doing.
7. tester: I made the test change the human approved in entry 5 and the coder named in entry 6, and nothing else. In tests/application/handlers/test_run_gate.py, line 30 changed from `BODY = "# First story\n\nRewritten by the factory on the branch.\n"` to `BODY = "# First story\n\n## Journal\n\n1. 2026-10-12 human: created.\n"`. This is the same value tests/application/handlers/test_merged.py uses. The reason: the real `MergedHandler` appends a `done` entry to the journal, so the story body needs a `## Journal` section that matches the state's single `created` record. `MergedHandler` is unchanged. I ran `make test` once and it was green, with total coverage at 99.22 %. That includes test_a_story_merged_while_its_stage_was_due_is_archived_without_a_run (criterion 8). Still open: the coder's refactor step, which entry 6 notes.

   `make lint`: lint: green
   `make test`: test: green
8. coder: The tester's change from entry 7 is in. `make check` now passes with every test green and total coverage at 99.22 %. I made no code change in this run.

   What I built, all in commit 38684ce:
   - `RunGate` in src/factory/application/handlers/run_gate.py:
     - When `target_of(event).pull_request` is `None`, it calls `run` with the event unchanged and does not read the hosting service.
     - Otherwise it calls `get_pull_request` once, before any handler. The event is copied with `pull_request` set to the view that was read:
       - `closed` goes to the `closed` handler with kind `closed`.
       - `merged` goes to the `merged` handler with kind `merged`.
       - `open` goes to `run` with the kind unchanged.
     - A failed read raises out of `handle`.
   - In src/factory/entry/wiring.py:
     - `build_handlers` now registers the ten kinds the Interface lists. One `ClosedHandler` instance and one `MergedHandler` instance are created first and used twice: they are the values registered for `closed` and `merged`, and the same objects are passed to the `RunGate` that wraps `RunHandler`.
     - `NOT_YET_HANDLED` is now `("crash", "expired", "acceptance_due")`.

   Main design decision: the gate calls whichever of the three handlers applies; it does not rewrite the event and send it back through the dispatcher. It is given its three handlers, so it stays a plain `Handler` and knows nothing about the registry. That matches the Interface and keeps registration in the entry layer only. The alternative I rejected was giving the gate the `build_handlers` mapping: that would effectively be a second registry in the application layer, which Q20 (A) rules out.

   Refactor step (still open from entry 6): I reread `git diff main...HEAD` outside `factory/` and `tests/` and found nothing to rename, simplify or remove, so there is no refactor commit.

   Noticed but not touched: the Demo of F0006-S0007 prints the old `NOT_YET_HANDLED` and is now out of date, as this ticket's Interface already says. The docs criterion is the documenter's.

   `make check`: check: green
9. reviewer: no findings.

   What I checked in `git diff main...HEAD -- . ':!factory'` (run_gate.py, wiring.py, test_run_gate.py, test_wiring_human_handlers.py, the changed test_wiring_handlers.py):
   - Acceptance criteria 1 to 13 each map to the test that entry 3 names, and each test checks what its criterion says:
     - Criterion 1 primes `fail_next` and asserts zero reads. `CountingHosting` counts a read before the failure, so a stray read would show.
     - Criterion 3 records the read count at the moment the run handler is entered.
     - Criteria 7 and 8 use the real `ClosedHandler`/`MergedHandler`, real git and the fake hosting service.
     - Criterion 10 checks the gate's `closed`/`merged` with `is` against the registered instances.
     - The failing sides the Interface states are tested: no pull request means no read (criterion 1), a failing read raises and calls no handler (criterion 6), the closed and merged handlers are not called for an open pull request (criterion 2). The Interface states no numeric limits.
     - The coder's entry 8 says the factory's `make check` was green.
   - Changed F0006-S0007 tests: exactly the three the Interface names (criteria 4, 5 and 9 of that story), changed as stated. The criterion 5 test now compares `unhandled_kinds` with `NOT_YET_HANDLED` only. The disjointness check it dropped is still asserted in test_wiring_human_handlers.py (criterion 12).
   - Architecture:
     - `RunGate` is in `factory.application` and imports only application and domain modules. It reads through `Boundaries.hosting` and inherits `Handler`.
     - Registration stays in `factory.entry.wiring.build_handlers`; the application layer has no second registry.
     - One `ClosedHandler` and one `MergedHandler` are shared between their own entries and the gate.
     - `Event.model_copy` sets `kind` and `pull_request` on the frozen model. The values are valid `EventKind`/`PullRequestView` values.
   - Security: no tool calls, strings or suppression markers added.
   - Quality:
     - The gate reuses `target_of` rather than duplicating it.
     - Module, class and public method docstrings are present and accurate.
     - The one comment in wiring.py explains why.
   - Ticket hygiene:
     - Entry 8 gives the main decision: the gate calls its three handlers directly and does not re-dispatch. It also names what was rejected: handing the gate the registry.
     - The Assignment matches what was built, and the docs criterion (15) still describes what the documenter must write.

   Open: the Demo of F0006-S0007 is out of date, as the Interface already notes. That is not under this story's review.
10. documenter: Documented the run gate and the grown wiring. I ran `make check` after the edits and it is green. I wrote no new examples, so none needed running.

    Files changed:
    - docs/project-guide.md:
      - New paragraph in *The handlers of the events* on `RunGate`. It covers the pull request read before every agent run, the closed and merged hand-off, a failing read raising, and every path to a run (the rerun after a crash included) going through the gate.
      - `build_handlers` now lists its ten registered kinds, and `NOT_YET_HANDLED` is `crash`, `expired` and `acceptance_due`.
      - Removed "built but not yet registered" for the merged, closed, reject, duplicate and lookup handlers, and the stale sentence in the comment section. Also fixed the kinds paragraph that said only `idle` and `run` are registered.
    - docs/operator-guide.md:
      - Merge and close sections: a story merged or closed while its stage waited to run is archived or discarded without that run.
      - Removed the "Not yet running" notes.
      - Rewrote "An event that keeps failing" so only `crash`, `expired` and `acceptance_due` have no handler.
      - Updated the hand-over, stage-changed-by-hand and "Stops that cannot be done" passages.

    Cross-read and found current: README.md. No stale passages left alone.

    No findings. The code matches the Interface and the criteria.

    Not touched, outside this story's lane: the Demo of F0006-S0007 prints the old constant, as the Interface already notes. The operator guide's "AskHandler is registered" wording rests on `AskHandler` being in `build_handlers`, which the diff confirms.

    `make check`: check: green
11. demo: I ran the one command under `## Demo` exactly as written, from the repository root. It exited with code 0.

    Command 1 (the `uv run python -c` script that drives `RunGate` with spy handlers and the fake hosting service):
    ```
    [('run', 'run'), ('closed', 'closed'), ('merged', 'merged'), ('run', 'run')]
    ```
    It met its `Expect:` line: one line with that exact list.
    - The open pull request and the work item without a pull request reached the run handler with kind `run`.
    - The closed pull request reached the closed handler as a `closed` event.
    - The merged pull request reached the merged handler as a `merged` event.

    Against the acceptance criteria:
    - The output is consistent with criteria 1, 2, 4 and 5: each case went to exactly one handler, with the kind the Interface states.
    - The work item without a pull request ran even though the fake hosting service had no pull request for it, so no read got in the way (criterion 1).
    - The demo does not exercise criterion 3 (read order), 6 (failing read), 7 and 8 (real git), or 9 to 13 (wiring), and does not contradict them. Entries 3, 8 and 9 map those criteria to tests that pass.

    No findings. Open, as the Interface already says: the Demo of F0006-S0007 prints the old `NOT_YET_HANDLED` and is out of date. That is not part of this story's demo.
12. done (pull request merged); cost: 9 runs, 25.8 min, 72 turns, 197k tokens in (1570k more from cache), 30k out, $2.18
