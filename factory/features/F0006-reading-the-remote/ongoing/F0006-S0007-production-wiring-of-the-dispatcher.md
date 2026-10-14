---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The production wiring of the dispatcher

## Assignment (as of log entry 1)

Build the first part of the production wiring that picks the handlers of the events (questionnaire 1, Q20): the `run` handler around F0005's `StageRunner`, the function in `factory.entry.wiring` that maps event kinds to handlers, the environment of the agent run, and a test that fails when an event kind built so far has no handler. Without this story `factory-run` would count every `run` event as `UnhandledEvent`. The `run` handler is `RunHandler`, which runs one stage through `StageRunner(boundaries, instance, definition, environment).run(work_item.id, work_item.path)`; the handlers take the pipeline definition that the tick has just loaded, so the tick receives a handler factory (F0006-S0004) and the wiring supplies `handler_factory`. The agent run's environment is the caller's (F0005 decision 23): `agent_environment` makes a `PATH` that holds the directory of the `factory-guard` console script (F0001 decision 17) and a `HOME`; F0010 scrubs it, probes both and completes `build_boundaries` from the instance settings. Later stories that add a handler (F0007, F0008, F0009) register it in `build_handlers` and shrink `NOT_YET_HANDLED` by its kinds, each with a criterion of its own, and edit no test written here. Covers SI2.4 end to end (an event kind with a handler never reaches `UnhandledEvent`) and the wiring of F0005 decision 23; keeps kept thing 12 (a state no handler was written for is a counted error, never silence). Morning observation: a real `claude -p` run whose guard hook is found on the `PATH` of the container. Uses `StageRunner` (F0005-S0007), `Handler`, `Dispatcher` and `unhandled_kinds` (F0006-S0003), `Tick`, `IdleHandler` and `HandlerFactory` (F0006-S0004), `Event` (F0006-S0002).

## Interface

`src/factory/application/handlers/__init__.py`: the package `factory.application.handlers`, with its module docstring only, created here when no story has created it yet. Later stories add their modules to it.

`src/factory/application/handlers/run.py`

```python
class RunHandler(Handler):
    def __init__(self, boundaries: Boundaries, instance: Name, definition: PipelineDefinition,
                 environment: Mapping[str, str]) -> None: ...
    def handle(self, event: Event) -> None: ...
        # ValueError for an event whose kind is not "run"
        # otherwise StageRunner(boundaries, instance, definition, environment).run(work_item.id, work_item.path);
        # the StageReport is dropped (a stall is a result the stage has already recorded);
        # whatever StageRunner.run raises propagates, to be a counted error of the dispatcher
```

`src/factory/entry/wiring.py` (grown)

```python
NOT_YET_HANDLED: tuple[EventKind, ...] = (
    "comment", "ask", "merged", "closed", "reject", "hand_over", "crash", "expired",
    "duplicate", "pull_request_lookup", "acceptance_due",
)   # the event kinds with no handler in build_handlers, in the order of EventKind; a story that registers one removes it

def agent_environment(scripts: Path, home: Path) -> dict[str, str]: ...
    # {"PATH": f"{scripts}:/usr/local/bin:/usr/bin:/bin", "HOME": str(home)}; no other key
def production_environment() -> dict[str, str]: ...
    # agent_environment(Path(sys.executable).parent, Path.home())
def build_handlers(boundaries: Boundaries, definition: PipelineDefinition, instance: Name,
                   environment: Mapping[str, str]) -> dict[EventKind, Handler]: ...
    # {"idle": IdleHandler(), "run": RunHandler(boundaries, instance, definition, environment)}
def handler_factory(boundaries: Boundaries, instance: Name,
                    environment: Mapping[str, str]) -> HandlerFactory: ...
    # a function of the loaded definition that returns build_handlers(boundaries, definition, instance, environment)
```

Rules:

- `RunHandler` is the one place that turns a `run` event into a stage; it adds nothing to the environment and takes nothing from it.
- `build_handlers` is the one place that registers a handler (R5, "nothing else wires"); the production code never builds a `Dispatcher` from a hand-written mapping. The tick builds its dispatcher from `handler_factory(...)` after each load.
- `NOT_YET_HANDLED` and the keys of `build_handlers`' result partition `EventKind`: no kind is in both and none is in neither.
- This story creates no model, so it states no closed-model rule.

Tests: `tests/application/handlers/__init__.py` (a package, as `CLAUDE.md` requires) and `tests/application/handlers/test_run.py` for `RunHandler`; `tests/entry/test_wiring_handlers.py` for the rest (`tests/entry/test_wiring.py` is F0002-S0008's and stays as it is). The tests use the shared fixtures `remote`, `checkout`, `human`, `hosting`, `agent_runtime`, `boundaries`, `agent_home` and `clock`, fill the agent home with `install_agents(agent_home, <the roles of the fixture's pipeline definition>)` from `tests/git_support.py`, and start a complete story (every section of the fixture's story form) through `human.push_file` and `human.start`: the fixture's backlog story `# First story` has form findings, which would turn the stage into rule 1 (F0005-S0007 Tests). The agent run is scripted on `FakeAgentRuntime` as F0005-S0007's tests do. The test of `NOT_YET_HANDLED` compares `unhandled_kinds(build_handlers(...))` with `list(NOT_YET_HANDLED)` and is written once.

## Acceptance criteria

1. `RunHandler.handle` on a `run` event of a started story runs the stage: `agent_runtime.requests()` then holds exactly one request, its `environment` equals the mapping the handler was given (a `PATH` and a `HOME` in the test) and has no other entry, and after `checkout.fetch()` the branch `origin/work-item/<id>` exists.
2. `RunHandler.handle` raises `ValueError` for an event of any other kind (a `comment` event with a work item, and an `idle` event) and the agent runtime has received no request.
3. A failure of the stage is not swallowed: with `hosting.fail_next("create_pull_request")`, `RunHandler.handle` raises `HostingServiceError`.
4. `build_handlers` returns a mapping whose keys are exactly `idle` and `run`; the `idle` handler is an `IdleHandler` and the `run` handler a `RunHandler`.
5. `unhandled_kinds(build_handlers(...))` equals `list(NOT_YET_HANDLED)`, the eleven kinds `comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `crash`, `expired`, `duplicate`, `pull_request_lookup` and `acceptance_due` in the order of `EventKind`; no kind of `NOT_YET_HANDLED` is a key of the mapping.
6. `agent_environment(scripts, home)` has exactly the keys `PATH` and `HOME`; `HOME` equals `str(home)`; the first entry of `PATH` is `str(scripts)`, and with an executable file `factory-guard` in `scripts`, `shutil.which("factory-guard", path=<PATH>)` finds it, while with no such file in `scripts` it is not found.
7. `production_environment()` has `PATH` starting with the directory of `sys.executable` and `HOME` equal to `str(Path.home())` (the test sets `HOME` through `monkeypatch`).
8. A `Tick` built with `handler_factory(boundaries, "factory-1", environment)` over a remote with one started story runs one stage in one tick: the tick returns dispatch outcome `handled` for the event `run`, and `agent_runtime.requests()` holds one request with `environment` equal to the given mapping.
9. An event whose kind is in `NOT_YET_HANDLED` is a counted error, not a crash: a `Dispatcher` built over `build_handlers(...)` dispatches a `comment` event and returns `error`, and its status holds `UnhandledEvent: no handler for event kind comment` as the last error.
10. make check stays green.
11. docs: `docs/project-guide.md` says that `factory.entry.wiring.build_handlers` is the one place that registers handlers, that `NOT_YET_HANDLED` lists the kinds still without one and shrinks as stories register theirs, and how the agent run's environment is made; `docs/operator-guide.md` says that the agent runs with only a `PATH` and a `HOME`, and that the console script `factory-guard` must be on that `PATH`; `docs/decisions.md` records why the handlers are built from the loaded pipeline definition on every tick and why a constant, not a test, lists the kinds still unhandled.

## Demo

```bash
uv run python -c "
import shutil, tempfile
from pathlib import Path
from factory.entry.wiring import NOT_YET_HANDLED, agent_environment
scripts = Path(tempfile.mkdtemp())
(scripts / 'factory-guard').write_text('')
(scripts / 'factory-guard').chmod(0o755)
environment = agent_environment(scripts, Path('/home/factory'))
print(sorted(environment))
print(shutil.which('factory-guard', path=environment['PATH']) == str(scripts / 'factory-guard'))
print(environment['HOME'])
print(NOT_YET_HANDLED)
"
```
Expect: four lines: `['HOME', 'PATH']`, `True`, `/home/factory`, and `('comment', 'ask', 'merged', 'closed', 'reject', 'hand_over', 'crash', 'expired', 'duplicate', 'pull_request_lookup', 'acceptance_due')`.

## Log (append only)

1. 2026-10-12 human: created.
