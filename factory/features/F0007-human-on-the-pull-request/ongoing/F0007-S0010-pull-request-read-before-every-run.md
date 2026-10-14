---
stage: ready
pr: null
blocked: null
comments_seen: 0
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
