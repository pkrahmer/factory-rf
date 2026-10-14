# The acceptance's handlers in the production wiring

## Assignment (as of log entry 1)

Register the acceptance's handlers in the production wiring and take the last kind out of `NOT_YET_HANDLED` (questionnaire 1, Q20 A: the wiring grows with each feature, `factory.entry.wiring.build_handlers` is the one place that registers a handler). `acceptance_due` gets `AcceptanceDueHandler` (S0003); `hand_over`, `merged` and `closed` get a `SplitByWorkItemKind` (S0004) of the story's handler (F0007) and the acceptance's (`AcceptanceHandOver`, `AcceptanceMerged`, `AcceptanceClosed`). F0007-S0010 built the `RunGate` with the very `ClosedHandler` and `MergedHandler` registered for `closed` and `merged`; if only the mapping's values changed, an acceptance whose pull request was merged or closed while its stage was due would reach the gate as a `run` event and go to the story's handler, which archives it with stage `done` and no `outcome` (a state the acceptance reader refuses on every tick after) or moves it back to `backlog/`. So the gate is built with the two splits, and the same split instances are the values of `closed` and `merged`. A project whose pipeline definition has no `acceptance_stage` must still tick: every handler of an acceptance constructs without an error and refuses an event it is given with `CannotHandle(kind, "no acceptance stage")` (decision 5 of the feature). Three tests of earlier stories break and are changed here, with the human's leave of Q20 (as F0007 decision 23 cites it) and nothing else of those files: F0006-S0007 criterion 9 in `tests/entry/test_wiring_handlers.py`, F0007-S0010 criterion 10 and criterion 13 in `tests/entry/test_wiring_human_handlers.py`, each as F0008-S0001 left it. F0008-S0001's remark that its forms "hold for F0009 as well" is true for the other wiring tests (F0006-S0007 criteria 4 and 5, F0007-S0010 criteria 9 and 12, F0008's criteria on `crash` and `expired`), which compare against `NOT_YET_HANDLED` and the key set without naming the value, and wrong for these three. Covers SI2.4 end to end for the last kind (an event kind with a handler never reaches `UnhandledEvent`); keeps kept thing 12 (a state no handler was written for is a counted error, never silence). Uses `build_handlers`, `NOT_YET_HANDLED` and `handler_factory` (F0006-S0007), `RunGate` (F0007-S0010), `RecoveryHandler` (F0008) and the handlers of S0003 to S0007.

## Interface

`src/factory/entry/wiring.py` (grown; F0006-S0007 created it, F0007-S0010 and F0008 grew it)

```python
NOT_YET_HANDLED: tuple[EventKind, ...] = ()

def build_handlers(boundaries: Boundaries, definition: PipelineDefinition, instance: Name,
                   environment: Mapping[str, str]) -> dict[EventKind, Handler]: ...
```

Rules:

- `build_handlers` returns F0008-S0003's keys plus `acceptance_due`: every kind of `EventKind` is a key, and `NOT_YET_HANDLED` is empty. The values of the keys F0007 and F0008 registered are as they were, except these. It builds `closed = SplitByWorkItemKind(ClosedHandler(boundaries, definition), AcceptanceClosed(boundaries, definition))` and `merged = SplitByWorkItemKind(MergedHandler(boundaries), AcceptanceMerged(boundaries, definition))` once. Those two instances are the values of `closed` and `merged` and the `closed` and `merged` arguments of the one `RunGate` (the value of `run`, and the `run` that `RecoveryHandler` reruns through). `hand_over` is `SplitByWorkItemKind(HandOverHandler(boundaries, definition), AcceptanceHandOver(boundaries, definition))`, and `acceptance_due` is `AcceptanceDueHandler(boundaries, definition)`.
- With `definition.acceptance_stage` `None`, `build_handlers` builds the same mapping and no constructor raises; the acceptance handlers refuse the events they are handed (S0003 criterion 21, S0004 criterion 16, S0005 criterion 18, S0007 criterion 10), and nothing is ever due.
- `NOT_YET_HANDLED` and the keys of `build_handlers`' result partition `EventKind` (F0006-S0007's rule stays): the constant is empty and every kind is a key.
- The tests this story changes, with the human's leave of Q20 and nothing else of those files:
  - In `tests/entry/test_wiring_handlers.py`, the test of F0006-S0007 criterion 9, as F0008-S0001 left it (it dispatches an `acceptance_due` event and expects `UnhandledEvent`), now builds a `Dispatcher` over `build_handlers(...)` with the key `comment` removed and expects the dispatch of a `comment` event to return `error` with the last error `UnhandledEvent: no handler for event kind comment`.
  - In `tests/entry/test_wiring_human_handlers.py`, the test of F0007-S0010 criterion 10, as F0008-S0001 left it (the values of the ten kinds it names, each by its key), now checks `merged`, `closed` and `hand_over` as `SplitByWorkItemKind` instances whose `story` handlers are `MergedHandler`, `ClosedHandler` and `HandOverHandler`, and the gate's `closed` and `merged` properties as the very instances registered for `closed` and `merged`; its checks of the other keys are unchanged.
  - In the same file, the test of F0007-S0010 criterion 13, as F0008-S0001 left it (it dispatches an `acceptance_due` event), now builds the `Dispatcher` over `build_handlers(...)` with the key `crash` removed and expects the dispatch of a `crash` event to return `error` with the last error `UnhandledEvent: no handler for event kind crash`.
  Criteria 2, 3, 5 and 6 below are those changed tests.

Tests: `tests/entry/test_wiring_acceptance.py` (a new file) for the registration; the three changed tests named above in their files. The wiring tests use the shared fixtures of F0006-S0007 (`remote`, `checkout`, `human`, `hosting`, `agent_runtime`, `boundaries`, `agent_home`, `clock`) and start a complete story as it does. The test of criterion 8 pushes the fixture's pipeline definition without its `acceptance_stage` line to `factory/pipeline.yml` with `human.push_file("main", ...)` (the stage `acceptance` may stay in the stages table) and ticks with `Tick(boundaries, "factory-1", handler_factory(boundaries, "factory-1", <a PATH and HOME mapping>))` after `install_agents(agent_home, <the roles of the fixture's pipeline definition>)`, as F0006-S0007's tests do.

## Acceptance criteria

1. `NOT_YET_HANDLED` is `()`, every kind of `EventKind` is a key of `build_handlers(...)`, `unhandled_kinds(build_handlers(...))` is `[]`, and `build_handlers(...)["acceptance_due"]` is an `AcceptanceDueHandler`.
2. The values of `merged`, `closed` and `hand_over` are `SplitByWorkItemKind` instances whose `story` handlers are a `MergedHandler`, a `ClosedHandler` and a `HandOverHandler` and whose `acceptance` handlers are an `AcceptanceMerged`, an `AcceptanceClosed` and an `AcceptanceHandOver` (F0007-S0010 criterion 10 as changed here).
3. The `RunGate` that is the value of `run` holds the very `SplitByWorkItemKind` instances registered for `closed` and `merged` (its `closed` and `merged` properties), and its `run` property is a `RunHandler` (F0007-S0010 criterion 10 as changed here).
4. A `merged` event of a story dispatched through `build_handlers(...)["merged"]` archives the story under `done/` on `origin/main`: it reaches the story's handler.
5. A `Dispatcher` built over `build_handlers(...)` with the key `comment` removed returns `error` for a `comment` event, and its status holds `UnhandledEvent: no handler for event kind comment` as the last error (F0006-S0007 criterion 9 as changed here).
6. A `Dispatcher` built over `build_handlers(...)` with the key `crash` removed returns `error` for a `crash` event, and its status holds `UnhandledEvent: no handler for event kind crash` as the last error (F0007-S0010 criterion 13 as changed here).
7. A `run` event of an acceptance at the stage `acceptance`, whose pull request the human closed while its stage was due, handled by `build_handlers(...)["run"]` (the `RunGate`), books the acceptance `refused` in `done/` on `origin/main` and never reaches the `RunHandler`; the story's `ClosedHandler` is not called and no agent request is made.
8. With a pipeline definition without `acceptance_stage`, `build_handlers(...)` builds without an error, `build_handlers(...)["acceptance_due"].handle(<an acceptance_due event>)` raises `CannotHandle` with the reason `no acceptance stage`, and one `Tick` over a remote with a started story runs that story's stage: the tick returns the dispatch outcome `handled` for the event `run`.
9. make check stays green.
10. docs: `docs/project-guide.md` lists `acceptance_due` and the three splits (`hand_over`, `merged`, `closed`) among the kinds `build_handlers` registers, says that the `RunGate` is built with the `closed` and `merged` splits and that `NOT_YET_HANDLED` is now empty; `docs/decisions.md` records why the gate holds the splits and not the story's handlers.

## Demo

```bash
uv run python -c "
from types import SimpleNamespace
from factory.application.acceptance import AcceptanceDueHandler
from factory.domain.errors import CannotHandle
from factory.domain.events import Event
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
from factory.entry.wiring import NOT_YET_HANDLED
definition = PipelineDefinition(contract='1.0', stages={'intake': StageDefinition(role='intake', next=['approval']), 'approval': StageDefinition(approval=True, next=['done']), 'done': StageDefinition()}, roles={'intake': RoleDefinition(write_paths=['{work_item}'])})
print(NOT_YET_HANDLED)
handler = AcceptanceDueHandler(SimpleNamespace(), definition)
try:
    handler.handle(Event(kind='acceptance_due', work_item=None, feature='F0001', remote_state='1' * 40))
except CannotHandle as error:
    print(error)
"
```
Expect: two lines: `()` (every kind has a handler), then `cannot handle acceptance_due: no acceptance stage` (the definition has no `acceptance_stage`, so the handler is built and refuses the event).

## Log (append only)

1. 2026-10-12 human: created.
