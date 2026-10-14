---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The dispatcher and the tick status

## Assignment (as of log entry 1)

Build the dispatcher that hands one event to its handler and counts what goes wrong. Every event kind has a handler or raises: a kind without a handler raises `UnhandledEvent` inside the dispatch, and that raise is a counted error like any other. A handler that raises is counted per event and the work item's remote state; at three errors one report is posted on the work item's pull request (keyed, so a repeat after a kill posts nothing), and the same event on the same remote state is not tried again. A push to the work item's remote branch is a new remote state, so the retry that is keyed to it starts again. A success clears the event's counts. The tick status is a local cache that may reset when the process restarts; the keyed report makes that harmless. A report that cannot be posted because the work item has no branch on the remote is not retried for ever: it becomes a log line. Covers SI2.4, GH5.4 and R28; keeps kept things 12 (an unknown event raises; errors capped and reported) and 14 (errors counted per event and state). Uses `StopService` (F0003-S0002) and `WorkItemStop` (F0003-S0003), the fake hosting service (F0001-S0014) and `PostKey` (F0001-S0002), `KillPoints` (F0001-S0001) and `Event` (F0006-S0002).

## Interface

`src/factory/domain/errors.py` (added)

```python
class UnhandledEvent(FactoryError):
    kind: str
    def __init__(self, kind: str) -> None: ...   # message: f"no handler for event kind {kind}"
```

`src/factory/domain/tick_status.py`

```python
ERROR_CAP = 3

class ErrorCount(BaseModel):
    event_key: str                            # Event.key
    remote_state: CommitId                    # Event.remote_state
    count: PositiveInt
    reported: bool = False
    last_error: str = ""                      # f"{type(error).__name__}: {error}" of the latest error

class TickStatus(BaseModel):
    errors: list[ErrorCount] = []

def find_error(status: TickStatus, event_key: str, remote_state: CommitId) -> ErrorCount | None: ...
def record_error(status: TickStatus, event_key: str, remote_state: CommitId, last_error: str) -> TickStatus: ...
    # same key and state: count + 1 and the new last_error; the same key with another state: the key's
    # entries are replaced by one with count 1; other keys are untouched
def mark_reported(status: TickStatus, event_key: str, remote_state: CommitId) -> TickStatus: ...
def clear_errors(status: TickStatus, event_key: str) -> TickStatus: ...    # every entry of that key
def at_cap(entry: ErrorCount) -> bool: ...                                  # count >= ERROR_CAP
```

Every model here is frozen and forbids unknown keys.

`src/factory/domain/post_texts.py` (added)

```python
def error_report_text(event_key: str, error: str, remote_state: CommitId, cap: int) -> str: ...
    # f"The factory failed {cap} times on `{event_key}` and has stopped retrying it. Last error: {error}. "
    # f"A new commit on the work item's branch (now at {remote_state[:12]}) makes the factory try again."
```

`src/factory/application/dispatcher.py`

```python
class Handler(ABC):
    @abstractmethod
    def handle(self, event: Event) -> None: ...    # any Exception it raises is a counted error (R28)

DispatchOutcome = Literal["handled", "error", "reported", "capped"]

class Dispatcher:
    def __init__(self, handlers: Mapping[EventKind, Handler], status: TickStatus, stops: StopService,
                 log: FactoryLog | None = None) -> None: ...
    @property
    def status(self) -> TickStatus: ...            # the current counts
    def handler_for(self, kind: EventKind) -> Handler: ...      # UnhandledEvent when none is registered
    def dispatch(self, event: Event) -> DispatchOutcome: ...

def unhandled_kinds(handlers: Mapping[EventKind, Handler]) -> list[EventKind]: ...
    # the kinds of EventKind with no handler, in the order of EventKind
```

Rules for `dispatch`, in this order:

- If an entry for `(event.key, event.remote_state)` is at the cap and `reported`, return `"capped"`: the handler is not called and nothing is posted. If it is at the cap and not `reported`, make the report (below) without calling the handler.
- Otherwise call `handler_for(event.kind).handle(event)`. On success `clear_errors` for the event's key and return `"handled"`.
- An `Exception` from `handler_for` or from `handle` is recorded with `record_error` (`last_error` is `f"{type(error).__name__}: {error}"`). Below the cap return `"error"`. At the cap make the report.
- `InjectedKill` and every other `BaseException` that is not an `Exception` pass through; the status is not changed by them.
- The report of an event with a work item is `StopService.post(WorkItemStop(...))` with `key=PostKey(work_item=<its id>, kind="error", n=event.remote_state[:12])`, `branch` the snapshot's branch, `title` `f"{id}: {story title}"` (just the id when the body has no title line), `pull_request` the state's pull request number, and `text=error_report_text(event.key, entry.last_error, event.remote_state, ERROR_CAP)`. A work item without a pull request therefore gets its draft pull request opened first by the stop service. A successful report (`"posted"` or `"already_posted"`) marks the entry `reported` and returns `"reported"`. A report that raises any `Exception` leaves the entry unreported and returns `"error"`; the next dispatch of the same event on the same state makes the report again. A failed report does not count: the entry's `count` and `last_error` are not changed by it.
- Exception to that last rule: when the report raises `HostingServiceError` and the work item has no branch on the remote (`branch_commit is None`), the stop service cannot open a pull request (it refuses a branch that is not on the remote with a commit beyond `main`), and no later tick could change that. The report is then the log line of an event without a work item (next rule), and the entry is marked `reported`.
- The report of an event without a work item is one line, `f"error cap reached on {event.key}: {entry.last_error}"`, to `log` when a log was given; the entry is marked `reported` and the outcome is `"reported"` either way.

Tests: `tests/domain/test_tick_status.py`, `tests/domain/test_unhandled_event.py`, `tests/domain/test_error_report_text.py`, `tests/application/test_dispatcher.py`, with the fixtures `hosting` (`FakeHostingService`, whose `factory_posts` counts the posts), `kill_points`, `boundaries` and `clock`. The handlers are small test classes that implement `Handler`. The closed-model tests build the models through a variable typed `type[BaseModel]` and assign with `setattr`, the field's name in a variable.

## Acceptance criteria

1. `record_error` on an empty status gives one entry with `count == 1`, `reported is False` and the given `last_error`; the input status is unchanged.
2. `record_error` for the same event key and the same remote state again gives `count == 2` and the newer `last_error`; `find_error` returns that entry for that key and state and `None` for another state.
3. `record_error` for the same event key and another remote state replaces that key's entries by one entry with `count == 1`, and leaves the entries of other keys untouched.
4. `clear_errors` removes every entry of the event key and keeps the entries of other keys.
5. `ERROR_CAP` is 3: `at_cap` is false for an entry with `count == 2` and true for `count == 3`.
6. `UnhandledEvent("merged")` is a `FactoryError`, carries `kind == "merged"`, and its message is `no handler for event kind merged`.
7. `handler_for` returns the registered handler, and raises `UnhandledEvent` for a kind that has none.
8. `unhandled_kinds({})` returns all thirteen kinds of `EventKind` in their order, and it returns `[]` when every kind has a handler.
9. A handler that succeeds is called once with the event and `dispatch` returns `"handled"`; entries recorded by earlier failures of that event key are gone afterwards.
10. A handler that raises `ValueError("boom")` makes `dispatch` return `"error"`, records one entry for the event key and remote state with `count == 1` and `last_error == "ValueError: boom"`, and posts nothing.
11. The same failure a second time gives `"error"` with `count == 2` and still no post on the pull request.
12. The third failure on the same event and remote state returns `"reported"` and posts exactly one comment on the work item's pull request: its key is `PostKey(work_item=<id>, kind="error", n=<first 12 characters of the remote state>)` and its text is `error_report_text(<event key>, "ValueError: boom", <remote state>, 3)`.
13. After the report, `dispatch` of the same event on the same remote state returns `"capped"`, does not call the handler, and posts nothing more; the entry is `reported`.
14. GH5.4: the same event on another remote state (a push to the work item's branch) is counted from 1 and its handler is called; after three errors on that state a second report with a different key is posted, and the two reports are the only posts.
15. An event whose kind has no handler is counted like any other error with `last_error == "UnhandledEvent: no handler for event kind merged"`, and at the third dispatch it is reported on the pull request (SI2.4).
16. Two different events of one work item on one remote state (a `comment` and a `merged` event) that fail every time each return `"reported"` at their third error; the two reports have the same key, so the pull request holds exactly one factory post, the report of the event that reached the cap first, and further dispatches of either return `"capped"` and post nothing.
17. The report of a work item without a pull request, whose branch is on the remote with one commit beyond `main`, opens a draft pull request on its branch with the title `<id>: <story title>` and posts the report there; for a story whose body has no title line the pull request's title is `<id>` alone.
18. When the report of a work item whose branch is not on the remote (`branch_commit` `None`, no pull request) raises `HostingServiceError`, the third failure returns `"reported"`, writes one line `error cap reached on <event key>: <last error>` to the given log, and the next dispatch returns `"capped"` and writes no second line.
19. When the report cannot be posted (`hosting.fail_next("post_comment")`) for a work item whose branch is on the remote, `dispatch` returns `"error"`, the entry is not `reported`, and its `count` is still 3 and its `last_error` still `ValueError: boom`; the next dispatch of the event does not call the handler, posts the report and returns `"reported"`.
20. With the kill point `after-post` armed, the dispatch that makes the report raises `InjectedKill` after the comment exists; a new `Dispatcher` with an empty `TickStatus` (the restart) whose handler fails three times again ends with exactly one comment on the pull request.
21. A handler that raises `InjectedKill` makes `dispatch` raise it too and leaves `status` as it was.
22. An event without a work item that fails three times returns `"reported"` and writes exactly one line `error cap reached on <event key>: <last error>` to the given log; the next dispatch returns `"capped"` and writes no second line; without a log nothing is written and no error is raised.
23. `error_report_text("run:F0001-S0001", "ValueError: boom", "c" * 40, 3)` equals ``The factory failed 3 times on `run:F0001-S0001` and has stopped retrying it. Last error: ValueError: boom. A new commit on the work item's branch (now at cccccccccccc) makes the factory try again.``
24. `ErrorCount` refuses an unknown key, an assignment to `count`, `count` 0 (1 is accepted) and a `remote_state` of 39 hex characters or with an upper-case letter; `TickStatus` refuses an unknown key and an assignment to `errors`; all with `ValidationError`.
25. make check stays green.
26. docs: `docs/operator-guide.md` says that after three errors on one event and one remote state the factory posts one report on the pull request and stops retrying until the work item's branch changes, and what to do about it; `docs/decisions.md` records why errors are counted per event and remote state, why the report is keyed, and why the report of a work item without a branch on the remote is a log line.

## Demo

```bash
uv run python -c "
import tempfile
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.clock import SystemClock
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.git_cli import GitCli
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Dispatcher, Handler
from factory.application.stops import StopService
from factory.domain.events import Event
from factory.domain.tick_status import TickStatus
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, initial_state
base = Path(tempfile.mkdtemp())
clock = SystemClock()
hosting = FakeHostingService()
boundaries = Boundaries(git=GitCli(base), hosting=hosting, agent_runtime=FakeAgentRuntime(), project_commands=MakeProjectCommands(base), work_item_reader=FrontmatterWorkItemReader(), work_item_writer=FrontmatterWorkItemWriter(), cost_reader=JsonLinesCostRecordReader(), cost_writer=JsonLinesCostRecordWriter(), clock=clock, log=TimestampedFactoryLog(base / 'factory.log', clock), health=JsonHealthStatusFile(base / 'health.json'), pipeline_reader=RuamelPipelineDefinitionReader(), agent_definitions=FrontmatterAgentDefinitionReader(base), checkout=base)
view = hosting.create_pull_request('work-item/F0001-S0001', 't', 'b', draft=True)
state = initial_state('intake').model_copy(update={'pull_request': view.number})
snapshot = WorkItemSnapshot(id='F0001-S0001', path='factory/features/F0001-demo/in-progress/F0001-S0001-x.md', folder='in-progress', branch='work-item/F0001-S0001', branch_commit='c' * 40, document=WorkItemDocument(state=state, body='# Demo story\n'))
class Boom(Handler):
    def handle(self, event):
        raise ValueError('boom')
dispatcher = Dispatcher({'run': Boom()}, TickStatus(), StopService(boundaries))
event = Event(kind='run', work_item=snapshot, remote_state='c' * 40)
print([dispatcher.dispatch(event) for _ in range(5)])
posts = hosting.factory_posts(view.number)
print(len(posts), posts[0].body.splitlines()[0])
"
```
Expect: two lines. The first is `['error', 'error', 'reported', 'capped', 'capped']`: the third failure is reported and the next two are not tried. The second starts with `1 The factory failed 3 times on` and reads in full ``1 The factory failed 3 times on `run:F0001-S0001` and has stopped retrying it. Last error: ValueError: boom. A new commit on the work item's branch (now at cccccccccccc) makes the factory try again.`` : one post only.

## Log (append only)

1. 2026-10-12 human: created.
