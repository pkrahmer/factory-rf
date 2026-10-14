---
stage: demo
pr: 77
blocked: null
comments_seen: 2
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
6. `agent_environment(scripts, home)` has exactly the keys `PATH` and `HOME`; `HOME` equals `str(home)`; `PATH` equals `f"{scripts}:/usr/local/bin:/usr/bin:/bin"` exactly, so its first entry is `str(scripts)`, and with an executable file `factory-guard` in `scripts`, `shutil.which("factory-guard", path=<PATH>)` finds it, while with no such file in `scripts` it is not found.
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
2. intake: Intake asks one question (the format check passed, so nothing from it).

   1. The Interface comment for `agent_environment` states the exact value `{"PATH": f"{scripts}:/usr/local/bin:/usr/bin:/bin", "HOME": str(home)}`. Criterion 6 tests only that the first `PATH` entry is `str(scripts)`, that `factory-guard` is found when present and not found when absent, that `HOME` equals `str(home)`, and that the keys are exactly `PATH` and `HOME`. The fixed tail `:/usr/local/bin:/usr/bin:/bin` has no criterion, so two coders could write different tails and both would pass the tests.
      - Option A, which I would choose: extend criterion 6 so that `PATH` equals `f"{scripts}:/usr/local/bin:/usr/bin:/bin"` exactly.
      - Option B: drop the tail from the Interface comment and state only that `scripts` comes first.

   Everything else checked out.
   - Interface: concrete modules and signatures.
   - Criteria: each is testable by one function. The failing sides are covered by 2 (wrong kind), 3 (stage failure propagates), 6 (guard absent) and 9 (unhandled kind is a counted error).
   - Demo: runnable, and its `Expect:` line is checkable.
   - Architecture: `RunHandler` sits in `application`, and the wiring sits in `entry`.
   - Scope: inside the feature's "Production wiring" scope, and it touches nothing under "Out of scope".
3. human (pull request comment, 2026-10-14): A: extend criterion 6 so that `PATH` equals `f"{scripts}:/usr/local/bin:/usr/bin:/bin"` exactly. The Interface stays as it is.
4. intake: accepted. Carried in the human's answer (log entry 3, option A): criterion 6 now says `PATH` equals `f"{scripts}:/usr/local/bin:/usr/bin:/bin"` exactly. The Interface is unchanged and the Assignment keeps its meaning, so I did not rewrite it.
   - Interface: concrete modules and signatures (`RunHandler`, `NOT_YET_HANDLED`, `agent_environment`, `production_environment`, `build_handlers`, `handler_factory`). The fixed `PATH` tail now has a criterion, which was the one gap.
   - Criteria: each is testable by one test function. Failing sides are covered by 2 (wrong kind), 3 (stage failure propagates), 6 (guard absent, exact `PATH`) and 9 (unhandled kind is a counted error). The partition rule is covered by 4 and 5.
   - Demo: runnable, and its `Expect:` line is checkable. It prints the sorted keys, the `which` result, `HOME` and `NOT_YET_HANDLED`.
   - Architecture: `RunHandler` is in `application.handlers`, and the wiring is in `entry.wiring`. The layering holds.
   - Scope: inside the feature's "Production wiring" scope, and it touches nothing under "Out of scope".
5. tester: I wrote red tests for criteria 1–9. Criteria 10 and 11 are for `make check` and the documenter.

   - criterion 1: tests/application/handlers/test_run.py::test_a_run_event_runs_the_stage_with_exactly_the_given_environment
   - criterion 2: tests/application/handlers/test_run.py::test_an_event_of_another_kind_is_refused_without_an_agent_run (parametrized over `comment` with a work item, and `idle`)
   - criterion 3: tests/application/handlers/test_run.py::test_a_failure_of_the_stage_propagates
   - criterion 4: tests/entry/test_wiring_handlers.py::test_build_handlers_registers_exactly_the_idle_and_the_run_handler
   - criterion 5: tests/entry/test_wiring_handlers.py::test_the_kinds_without_a_handler_are_exactly_those_not_yet_handled
   - criterion 6: tests/entry/test_wiring_handlers.py::test_the_agent_environment_is_a_path_led_by_the_scripts_and_a_home (parametrized guard-present / guard-absent; checks the exact `PATH`, and that `shutil.which` returns the script or `None`)
   - criterion 7: tests/entry/test_wiring_handlers.py::test_the_production_environment_uses_the_interpreter_directory_and_the_home (sets `HOME` through `monkeypatch`)
   - criterion 8: tests/entry/test_wiring_handlers.py::test_a_tick_over_the_handler_factory_runs_one_stage
   - criterion 9: tests/entry/test_wiring_handlers.py::test_an_event_not_yet_handled_is_a_counted_error

   Files created:
   - tests/application/handlers/__init__.py (empty, like tests/application/__init__.py)
   - tests/application/handlers/test_run.py
   - tests/entry/test_wiring_handlers.py

   Test setup:
   - The run tests start a complete story (every section of the story form) through `human.push_file` and `human.start`, and fill the agent home with `install_agents` for every role of `PIPELINE_YAML`.
   - They take the `run` event from `Watcher(boundaries, "factory-1").evaluate(definition)`.
   - They queue one completed `ScriptedRun` with decision `tests`, because the first stage is intake and its next stage is `tests`.
   - The `comment` event for criterion 2 reuses the watcher's snapshot.
   - Criterion 9 builds its snapshot by hand with remote state `"a" * 40`.
   - Criterion 2 checks only that `ValueError` is raised, not its message, because the criteria do not state the message.

   `make test`: both new modules fail at collection, as expected, because `factory.application.handlers.run` and the new names in `factory.entry.wiring` (`NOT_YET_HANDLED`, `agent_environment`, `production_environment`, `build_handlers`, `handler_factory`) do not exist yet. `make lint` is green.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
6. coder: I built the run handler and the production wiring of the dispatcher. `make check` is green and the demo prints its four expected lines. Commit d4b29cd.

   - `src/factory/application/handlers/__init__.py`: the new package, with its module docstring only.
   - `src/factory/application/handlers/run.py`: `RunHandler(Handler)`.
     - It raises `ValueError` for any event that is not `run`. It also raises for a `run` event with no work item, which the `Event` model already rules out.
     - Otherwise it builds `StageRunner(boundaries, instance, definition, environment)` on every call and runs `run(work_item.id, work_item.path)`.
     - It drops the `StageReport` and lets every exception propagate to the dispatcher.
   - `src/factory/entry/wiring.py`: adds `NOT_YET_HANDLED` (the eleven kinds, in the order of `EventKind`), `agent_environment`, `production_environment`, `build_handlers` and `handler_factory`, and extends `__all__`.
     - `agent_environment` returns `{"PATH": f"{scripts}:/usr/local/bin:/usr/bin:/bin", "HOME": str(home)}`; the fixed tail is a private constant `_SYSTEM_PATH`.
     - `handler_factory` returns a closure over `boundaries`, `instance` and `environment` that calls `build_handlers` with each loaded definition.

   Main decision: `RunHandler` keeps its constructor arguments and builds a new `StageRunner` on each `handle` call, as the Interface says. I rejected building one `StageRunner` in the constructor. That would be cheaper, but it would make the handler hold state left over from earlier runs, and the tick already rebuilds the handlers after each load anyway.

   Refactor: I read the diff and found nothing to change, so there is no refactor commit.

   Noticed but not touched: no command-line entry point builds a `Tick` yet. `handler_factory` is used only by the tests until `factory-run` is wired in a later story. The docs criterion (11) is for the documenter.

   `make check`: check: green
7. reviewer: No findings.

   I reviewed `git diff main...HEAD -- . ':!factory'` against the ticket. The changes under `planning/` and `docs/runs/` came from the human's own commit 7cd543e. They are the human's files and not this ticket's work, so I did not review them.

   1. Acceptance criteria:
      - Criteria 1–9 each have a test named after them that checks what the criterion says:
        - Criterion 1: the handler gets a mapping and the request's `environment` equals it, so it adds no entry. The branch `origin/work-item/F0001-S0001` exists after the fetch.
        - Criterion 2: a `comment` event and an `idle` event each raise `ValueError` and leave no request.
        - Criterion 3: `fail_next("create_pull_request")` makes the handler raise `HostingServiceError`.
        - Criterion 4: the mapping's keys are `{idle, run}` with the right types.
        - Criterion 5: `unhandled_kinds` equals `list(NOT_YET_HANDLED)`, the eleven kinds are listed in order, and no kind is both handled and listed.
        - Criterion 6: `PATH` is checked exactly, with the guard present and absent.
        - Criterion 7: `HOME` is set through `monkeypatch`.
        - Criterion 8: a `Tick` over `handler_factory` returns `handled` for the `run` event, with the environment equal.
        - Criterion 9: dispatching `comment` returns `error`, and the last error is `UnhandledEvent: no handler for event kind comment`.
      - Every Interface rule has a test for its failing side: the wrong kind (criterion 2), the stage failure that propagates (3), the missing guard (6) and the unhandled kind (9). The partition is covered by criteria 4 and 5.
      - The coder's entry reports `make check` green.
   2. Architecture: the layering holds.
      - `RunHandler` is in `factory.application.handlers.run` and imports only application and domain modules.
      - The wiring is in `factory.entry.wiring`.
      - The only `Dispatcher` built in `src` is the one inside `Tick`, which builds it from the handler factory, so no production code hand-writes a mapping.
   3. Security:
      - No secrets, no suppression markers and no shell commands built from strings.
      - The environment is a fixed two-key dict.
   4. Quality:
      - The names are clear.
      - The one comment in `run.py` explains why the `StageReport` is dropped.
      - The docstrings are present and accurate.
      - `_SYSTEM_PATH` avoids repeating the `PATH` tail as a magic string.
      - The `event.work_item is None` guard is needed to narrow the type for mypy, so it is not dead code.
      - The `STORY` text is copied into both new test modules, the same pattern the existing tests under `tests/application/` already follow.
   5. Ticket hygiene:
      - The coder's entry names the main decision (a new `StageRunner` for each `handle`) and what was rejected.
      - The Assignment matches what was built.
      - The docs criterion (11) still says what the reader must know.

   Open, carried from the coder's entry: no command-line entry point builds a `Tick` yet. `handler_factory` is used only by the tests until `factory-run` is wired in a later story.
8. documenter: Documented the run handler and the production wiring, with no findings. `make check` is green. I did not run the ticket's demo command in this stage.

   Files changed:
   - `docs/project-guide.md`:
     - New section "The handlers of the events". It covers `build_handlers` as the one place that registers handlers, `handler_factory`, `NOT_YET_HANDLED` and how it shrinks, `RunHandler`, and how `agent_environment` and `production_environment` make the agent's environment.
     - The sentence in "The tick" that said the production handler factory was still to come now points to that section.
   - `docs/operator-guide.md`: under "`factory-guard` on the agent run's `PATH`", I added that the agent gets only a `PATH` and a `HOME`. `PATH` is the directory of the factory's Python followed by `/usr/local/bin:/usr/bin:/bin`. So `factory-guard` must be installed in the factory's own environment.
   - `docs/decisions.md`: new entry explaining why the handlers are built from the loaded definition on every tick, and why a constant lists the unhandled kinds, not a test.

   Cross-read and found current against the diff: the guard and agent runtime sections of the project guide, the tick section, the "Reading and writing a work item file" section, and the operator guide's agent runtime section. Nothing else in `README.md` or `docs/` mentions the changed names.

   Stale but untouched: the project guide says `build_boundaries` and the concrete adapters are not wired yet. That stays true until F0010. The `factory-run` command that builds a `Tick` does not exist yet, and the new text says so.

   `make check`: check: green
