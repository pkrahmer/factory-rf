# The preflight in the tick and the wiring

## Assignment (as of log entry 1)

Put the preflight into the tick, in the right place. The built tick runs fetch, load the pipeline definition, restore the checkout, clean up stale branches (F0008-S0004), evaluate and dispatch (F0006 decision 10: the definition is loaded before the restore, so an invalid definition leaves the checkout alone). The preflight of the previous story runs after the restore and before the cleanup and the evaluation, so after the tick has fetched and reset its checkout to the remote. A preflight that stops (a machine that fails, a main branch that fails the lint) ends the tick there with `TickOutcome(stopped=<the reason>)`, and the tick does nothing else. This covers ST4.2 and keeps kept thing 18 (the machine and its preflight). The story also wires the preflight into `build_tick` with the checks it has so far; the stories that add machine items (the token, the agent user, the probe of an agent run) add them to the wiring themselves.

## Interface

`src/factory/application/tick.py`: the tick (built by F0006-S0004) becomes `Tick(boundaries, instance, handlers, status=None, preflight=None)`, the new parameter being `preflight: Preflight | None`. `Tick.run` runs fetch, load, restore, the preflight (when one is given), the cleanup of stale branches (F0008-S0004), then the evaluation and the dispatch; a tick that the preflight stops ends before the cleanup. When `preflight.run()` returns a reason, the tick ends there with `TickOutcome(stopped=<that reason>)`.

`src/factory/entry/wiring.py` (extends the module)

```python
def build_preflight(
    boundaries: Boundaries,
    settings: InstanceSettings,
    which: Callable[[str], str | None],
    extra: Sequence[Callable[[], PreflightItem]] = (),
) -> Preflight: ...
def build_tick(
    boundaries: Boundaries,
    settings: InstanceSettings,
    which: Callable[[str], str | None] = shutil.which,
) -> Tick: ...
```

Wiring: `build_preflight` is `Preflight(boundaries, MachineChecks(boundaries, settings, which, extra), JsonPreflightStampFile(<state directory>/preflight-stamp.json), StopService(boundaries), settings.image)`. `build_tick` is the run story's `Tick`, now with `preflight=build_preflight(boundaries, settings, which)`.

Tests: `tests/application/test_tick_preflight.py` (the tick on the `remote`, `checkout`, `human`, `hosting` and `agent_runtime` fixtures with a real `MakeProjectCommands`; the remote's `main` gets a `Makefile` whose target `lint` is `test ! -f BROKEN`, and a file named `BROKEN` makes it red; the pipeline's agents are installed with `install_agents`), `tests/entry/test_wiring_preflight.py`. F0010-S0004's test of its criterion 6 (one `run()` of `build_tick(boundaries, settings)` runs one stage; in `tests/entry/test_wiring_run.py`) meets the preflight from this story on: the tester of this story changes that one test and nothing else in it, to call `build_tick(boundaries, settings, which)` with a `which` that answers a path for every tool, settings with `pinned_agent_version="fake"` (the version of `FakeAgentRuntime`), and a `Makefile` on `main` whose target `lint` is `true`, pushed with `human.push_file`; the human's word is in `FEATURE.md` decision 28.

## Acceptance criteria

1. The tick fetches before the preflight: with an `origin/main` that failed the lint when the checkout was cloned, and a fix the human pushed afterwards, one tick given the preflight passes it (ST4.2).
2. The same order in the other direction: with a clean `origin/main` at clone time and a breaking commit the human pushed afterwards, one tick given the preflight returns `TickOutcome(stopped="main_branch_failing")` and the stop is in the health status.
3. A tick whose preflight stops does nothing else: no agent run is requested, no pull request exists in the fake hosting service, and no event is dispatched (`event is None`), although a started story is waiting on the remote.
4. A tick whose preflight stops ends before the cleanup of stale branches (F0008-S0004): with a stale remote branch of a story that is back in the backlog and a red `origin/main`, `Tick.run` returns `TickOutcome(stopped="main_branch_failing")` and the branch is still on the remote.
5. `build_preflight(...)` returns a `Preflight` whose `run()` leaves the file `preflight-stamp.json` in `settings.state_directory`, holding `settings.image`.
6. A `Tick` from `build_tick(boundaries, settings, which)` with a `which` that answers `None` for `git` returns `TickOutcome(stopped="preflight_failed")` and leaves the machine stop in the health status.
7. make check stays green.
8. docs: `docs/operator-guide.md` explains the preflight as the tick runs it (after the fetch, the load and the restore, before the cleanup and before anything is evaluated) and that a tick the preflight stops does nothing else; `docs/project-guide.md` states the order of a tick as fetch, load, restore, preflight, clean up, evaluate, dispatch; `docs/decisions.md` records why the preflight runs after the restore and not before the load (F0006 decision 10: the built tick loads the definition before it restores the checkout).

## Demo

```bash
uv run python -c "
import inspect
from factory.application.tick import Tick
from factory.entry.wiring import build_tick
print(list(inspect.signature(Tick).parameters))
print(list(inspect.signature(build_tick).parameters))
"
```
Expect: two lines, `['boundaries', 'instance', 'handlers', 'status', 'preflight']` and `['boundaries', 'settings', 'which']`.

## Log (append only)

1. 2026-10-12 human: created.
