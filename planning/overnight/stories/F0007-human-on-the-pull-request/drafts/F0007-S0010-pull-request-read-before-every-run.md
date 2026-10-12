# The pull request read before every agent run

## Assignment (as of log entry 1)

Build the gate that reads the pull request before a stage is run, and the one place that collects the feature's handlers. A stage can be due for a work item whose pull request the human has meanwhile closed or merged; running the agent first would spend a run on a story the human has already decided. `RunGate` is a handler for `run` events that wraps the stage protocol's handler: it reads the pull request's state first and, when it is closed or merged, hands the event to the `closed` or the `merged` handler instead, so the human's act is handled before any agent run; when the work item has no pull request, or the pull request is open, the stage runs as before. `human_handlers` builds the mapping from event kind to handler for every kind this feature owns, with the stage protocol's handler passed in and gated, so that the tick (F0006) can register all of them and no event of these kinds is left without a handler. It keeps the planner's note that the pull request's state is read before every agent run (v1's `run` step 3) and applies R22 (the human's act comes first). The wiring that passes the mapping to the dispatcher is F0006's. No morning observation.

## Interface

`src/factory/application/handlers/run_gate.py`

```python
class RunGate:
    def __init__(self, boundaries: Boundaries, run: Handler, closed: Handler, merged: Handler) -> None: ...
    def handle(self, event: Event) -> None: ...
```

`src/factory/application/handlers/registry.py`

```python
def human_handlers(boundaries: Boundaries, definition: PipelineDefinition,
                   run: Handler) -> dict[EventKind, Handler]: ...
```

Rules:

- `RunGate.handle` takes `target_of(event)`. When `target.pull_request` is `None` it calls `run.handle(event)` unchanged and reads nothing from the hosting service.
- Otherwise it reads `HostingService.get_pull_request(number)` once, before any handler is called, and passes on the event copied with `pull_request` set to the view read. A view whose state is `closed` goes to `closed.handle` with the event's `kind` set to `closed`; a view whose state is `merged` goes to `merged.handle` with the kind set to `merged`; a view whose state is `open` goes to `run.handle`, with the kind unchanged.
- A failing read leaves `handle` by raising, and none of the three handlers is called.
- `human_handlers` returns a dict with exactly the keys `run`, `comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `duplicate` and `pull_request_lookup`. The values are `CommentHandler(boundaries)`, `AskHandler(boundaries, definition)`, `MergedHandler(boundaries)`, `ClosedHandler(boundaries, definition)`, `RejectHandler(boundaries)`, `HandOverHandler(boundaries, definition)`, `DuplicateHandler()`, `PullRequestLookupHandler()` and, for `run`, `RunGate(boundaries, run, <the closed handler>, <the merged handler>)`, built with the same two instances.

Tests: `tests/application/handlers/test_run_gate.py` and `tests/application/handlers/test_registry.py`. The unit tests of the gate use small recording handlers as stand-ins for the three handlers it calls; the integration tests use the real `ClosedHandler` and `MergedHandler`, real git and the fake hosting service.

## Acceptance criteria

1. For a work item whose state has no pull request, `RunGate.handle` calls the run handler once with the event unchanged, and the hosting service is not read: with `get_pull_request` set to fail, no error occurs.
2. For an open pull request, the pull request is read exactly once and the run handler is called once, with `event.pull_request` equal to the view read and the kind unchanged; the closed and merged handlers are not called.
3. The pull request is read before the run handler is called: at the moment the run handler is entered, the read has already happened.
4. For a closed pull request, the closed handler is called once with the kind `closed` and the view read, and the run handler is not called.
5. For a merged pull request, the merged handler is called once with the kind `merged` and the view read, and the run handler is not called.
6. When `get_pull_request` fails, `handle` raises `HostingServiceError` and none of the three handlers is called.
7. A story at `doing` whose pull request the human closed while its stage was due, handled through a `RunGate` with the real `ClosedHandler`, ends in `backlog/` on `origin/main` with its branch deleted, and the run handler was never called.
8. A story whose pull request the human merged while its stage was due, handled through a `RunGate` with the real `MergedHandler`, is archived under `done/` on `origin/main`, and the run handler was never called.
9. `human_handlers` returns a dict whose keys are exactly `run`, `comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `duplicate` and `pull_request_lookup`.
10. The values of `human_handlers` are instances of `CommentHandler`, `AskHandler`, `MergedHandler`, `ClosedHandler`, `RejectHandler`, `HandOverHandler`, `DuplicateHandler`, `PullRequestLookupHandler` and, for `run`, `RunGate`, whose closed and merged handlers are the very instances registered for `closed` and `merged`.
11. The `run` entry of `human_handlers` calls the handler passed in when the work item's pull request is open.
12. make check stays green.
13. docs: `docs/project-guide.md` states that the pull request is read before every agent run, that a close or a merge found then is handled first, and lists the event kinds that `human_handlers` covers; `docs/operator-guide.md` says that a story whose pull request was closed or merged while its stage waited to run is discarded or archived without that run.

## Demo

```bash
uv run python -c "
from types import SimpleNamespace
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.handlers.run_gate import RunGate
from factory.domain.events import Event
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState

class Spy:
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
