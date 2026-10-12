# The tick: fetch first, then the remote's state

## Assignment (as of log entry 1)

Build the tick: one pass of fetch, load, restore, evaluate and dispatch, in that order, where the remote is the only truth and the local checkout is disposable. The tick fetches first, and a failed fetch (an expired token fails the same way) is a repository stop and ends the tick. It loads and validates the pipeline definition from `origin/main`; an invalid one is a repository stop and the tick does nothing else. It restores the checkout to `origin/main`, discarding uncommitted changes and writing one line that names them. It evaluates the remote's state and hands the one event to the dispatcher. Because nothing local is ever read, a rejected push leaves no trace: the next tick judges the remote's state, and at most one report is posted over all later ticks on that state. A push to a work item's remote branch retries the capped event. A fresh clone continues every work item. A work item of v1's format stops the repository with a line that names it. The local run record and any lock change nothing the tick does; v1.1 keeps no lock. Covers GH5.2, GH5.3, GH5.5, GH1.5 and the tick's side of GH5.4 and R26; keeps kept thing 3 (the remote is the truth) and 16 (an idle tick costs a fetch and at most one lookup). Uses `Git` (F0001), `PipelineLoader` and `StopService` (F0003), `Watcher` (F0006-S0002), `Dispatcher` (F0006-S0003), `RemoteWorkItems` (F0006-S0001).

## Interface

`src/factory/application/tick.py`

```python
class TickOutcome(BaseModel):
    stopped: RepositoryStopReason | None = None   # set when the tick ended at a repository stop
    event: Event | None = None                    # the evaluated event; None when stopped
    dispatch: DispatchOutcome | None = None       # None when stopped

class IdleHandler:
    def handle(self, event: Event) -> None: ...   # does nothing

class V1WorkItemHandler:
    def __init__(self, stops: StopService, clock: Clock) -> None: ...
    def handle(self, event: Event) -> None: ...
        # stops.raise_stop(RepositoryStop(scope="repository", reason="v1_work_item_found",
        #                                 detail=event.detail, at=clock.now()))

def default_handlers(stops: StopService, clock: Clock) -> dict[EventKind, Handler]: ...
    # {"idle": IdleHandler(), "v1_work_item": V1WorkItemHandler(stops, clock)}; later features add theirs

class Tick:
    def __init__(self, boundaries: Boundaries, instance: Name, dispatcher: Dispatcher) -> None: ...
    def run(self) -> TickOutcome: ...
```

Rules for `Tick.run`, in this order; a repository stop ends the tick with `TickOutcome(stopped=<reason>)`, and nothing after it runs:

- Fetch: `boundaries.git.fetch()`. `FetchFailed` raises the stop `fetch_failed` with `detail=str(error)`. When it succeeds the stop `fetch_failed` is cleared.
- Load: `PipelineLoader(boundaries).load()`. `PipelineDefinitionInvalid` raises the stop `pipeline_definition_invalid` with `detail=error.fault`. When it succeeds that stop is cleared.
- Restore: the checkout is put on branch `main` at `origin/main` with no uncommitted change and no untracked file (ignored paths stay). When `Git.status()` lists changes before that, one line `discarded uncommitted changes: <path>, <path>` (the paths in the order of `status`) is written to `boundaries.log`; with no changes no line is written. A `GitError` in this step raises the stop `checkout_restore_failed` with `detail=str(error)`. When it succeeds that stop is cleared.
- Evaluate: `Watcher(boundaries, instance).evaluate(definition)`. When the event is not `v1_work_item` the stop `v1_work_item_found` is cleared.
- Dispatch: `dispatcher.dispatch(event)`; the outcome is `TickOutcome(event=event, dispatch=<outcome>)`.
- Every stop raised here is `RepositoryStop(scope="repository", reason=..., detail=..., at=boundaries.clock.now())` raised through `StopService.raise_stop`.
- The tick reads neither a run record nor a lock, and creates none.

Tests: `tests/application/test_tick.py`, with the shared fixtures `remote`, `checkout`, `human`, `hosting`, `clock`, `kill_points` and `boundaries`. The test module builds its own `Boundaries` from the shared one with `dataclasses.replace`, for a `JsonHealthStatusFile` and a `TimestampedFactoryLog` under `tmp_path` and a `FrontmatterAgentDefinitionReader` over a `tmp_path` agent home that holds one agent file per role of the fixture's pipeline definition. Handlers are small test classes that implement `Handler`. A fetch is made to fail by moving the bare remote away; a restore is made to fail by an untracked directory that has been made unwritable.

## Acceptance criteria

1. `run` fetches before it reads: a commit that the human pushed to a runnable work item's remote branch since the last tick is the `remote_state` of the event this tick dispatches, and the test never fetches.
2. GH5.3: when the fetch fails, `run` returns `TickOutcome(stopped="fetch_failed")` with no event and no dispatch, the handler is not called, and the health status holds exactly one stop with scope `repository`, reason `fetch_failed`, a non-empty `detail` and `at` equal to `clock.now()`.
3. For that stop the factory log holds a line that begins with the clock's UTC time stamp.
4. On the first tick after the remote is back, the stop `fetch_failed` is gone from the health status and the tick dispatches an event.
5. An invalid pipeline definition on `origin/main` (a missing key without a default) makes `run` return `TickOutcome(stopped="pipeline_definition_invalid")` whose stop names the missing key in `detail`; nothing is dispatched and a file left untracked in the checkout is still there.
6. After the definition is repaired on `origin/main`, the next tick clears that stop.
7. The restore removes a modified tracked file and an untracked file from the checkout, leaves the checkout on `main` at the head of `origin/main`, and writes one line `discarded uncommitted changes:` naming both paths; an ignored file in the checkout is still there, and on a clean checkout no such line is written.
8. When the restore cannot remove an untracked file, `run` returns `TickOutcome(stopped="checkout_restore_failed")` with the stop in the health status and nothing dispatched; the next tick, after the file can be removed, clears the stop.
9. GH5.2: a handler of `run` that commits on a copy of the work item's branch made from an older commit and pushes it gets the outcome `rejected` because the human pushed to the branch meanwhile, and raises `PushFailed`; the next tick's event has `remote_state` equal to the head of the remote branch, and the checkout is back on `main` at `origin/main`.
10. GH5.2: with that handler failing on every tick, six ticks give the dispatch outcomes `error`, `error`, `reported`, `capped`, `capped`, `capped`, and the hosting service holds exactly one factory post on the work item's pull request.
11. GH5.4: after that report, a new commit pushed by the human to the work item's remote branch makes the next tick call the handler again.
12. GH5.5: a tick in a fresh clone made with `GitCli.clone` into an empty directory (no local branch of any work item) dispatches the same event for the same work item, with the same `remote_state` and the state the branch holds, as a tick in the original checkout; two work items in different stages are both read from their branches.
13. A story in a feature's `ongoing/` folder makes the tick dispatch the event `v1_work_item`, outcome `handled`, and the health status holds one stop with reason `v1_work_item_found` whose `detail` names its path; no other work item's `run` is dispatched in that tick.
14. After that file is removed from `origin/main`, the next tick clears the stop `v1_work_item_found`.
15. GH1.5: the events and outcomes of a tick are the same when the run record store holds a record for another work item, holds a record for the dispatched work item, holds unreadable text, or is empty.
16. GH1.5: none of the modules `factory.application.tick`, `factory.application.watcher`, `factory.application.work_items` and `factory.domain.evaluation` mentions `run_record` or `RunRecord` or the word `lock`.
17. A tick on a repository with no work item in progress makes no hosting-service call; with one waiting work item whose pull request is open it makes exactly one `get_pull_request` and one `list_comments`.
18. `default_handlers` holds exactly the kinds `idle` and `v1_work_item`; the `idle` handler changes nothing.
19. With only `default_handlers` registered, a tick whose event is `run` returns dispatch outcome `error`, and the status holds `UnhandledEvent: no handler for event kind run` as the last error (SI2.4 end to end).
20. `make check` stays green.
21. docs: `docs/operator-guide.md` lists the stops `fetch_failed`, `pipeline_definition_invalid`, `checkout_restore_failed` and `v1_work_item_found`, what each means and what to do; `docs/project-guide.md` states the order of a tick; `docs/decisions.md` records that the checkout is disposable and restored to `origin/main` at the start of every tick.

## Demo

```bash
uv run python -c "
import re, subprocess, tempfile
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
from factory.adapters.run_record_file import JsonRunRecordFile
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Dispatcher
from factory.application.stops import StopService
from factory.application.tick import Tick
from factory.domain.tick_status import TickStatus
base = Path(tempfile.mkdtemp())
checkout = base / 'checkout'
subprocess.run(['git', 'init', '-b', 'main', str(checkout)], check=True, capture_output=True)
subprocess.run(['git', 'remote', 'add', 'origin', str(base / 'missing.git')], cwd=checkout, check=True, capture_output=True)
clock = SystemClock()
boundaries = Boundaries(git=GitCli(checkout), hosting=FakeHostingService(), agent_runtime=FakeAgentRuntime(), project_commands=MakeProjectCommands(checkout), work_item_reader=FrontmatterWorkItemReader(), work_item_writer=FrontmatterWorkItemWriter(), cost_reader=JsonLinesCostRecordReader(), cost_writer=JsonLinesCostRecordWriter(), clock=clock, log=TimestampedFactoryLog(base / 'factory.log', clock), health=JsonHealthStatusFile(base / 'health.json'), pipeline_reader=RuamelPipelineDefinitionReader(), agent_definitions=FrontmatterAgentDefinitionReader(base), run_record=JsonRunRecordFile(base / 'run-record.json'), checkout=checkout)
tick = Tick(boundaries, 'factory-1', Dispatcher({}, TickStatus(), StopService(boundaries)))
outcome = tick.run()
print(outcome.stopped, outcome.event, outcome.dispatch)
print([stop.scope + ':' + stop.reason for stop in boundaries.health.read().stops])
lines = (base / 'factory.log').read_text().splitlines()
print(bool(lines) and all(re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z ', line) for line in lines))
"
```
Expect: three lines. `fetch_failed None None` (the fetch from the missing remote stopped the tick before anything was read or dispatched), then `['repository:fetch_failed']`, then `True` (every line the stop wrote to the factory log begins with a UTC time stamp).

## Log (append only)

1. 2026-10-12 human: created.
