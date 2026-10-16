---
stage: doing
pr: 128
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The preflight in the tick and the wiring

## Assignment (as of log entry 1)

Put the preflight into the tick, in the right place. The built tick runs fetch, load the pipeline definition, restore the checkout, clean up stale branches (F0008-S0004), evaluate and dispatch (F0006 decision 10: the definition is loaded before the restore, so an invalid definition leaves the checkout alone). The preflight of the previous story runs after the restore and before the cleanup and the evaluation, so after the tick has fetched and reset its checkout to the remote. A preflight that stops (a machine that fails, a main branch that fails the lint) ends the tick there with `TickOutcome(stopped=<the reason>)`, and the tick does nothing else. This covers ST4.2 and keeps kept thing 18 (the machine and its preflight). The story also wires the preflight into `build_tick` with the checks it has so far; the probe story (F0010-S0016) adds the later machine items (the token, the agent user, `sudo`, the agent run's environment and its probe) to the wiring in one place.

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

Tests: `tests/application/test_tick_preflight.py` (the tick on the `remote`, `checkout`, `human`, `hosting` and `agent_runtime` fixtures with a real `MakeProjectCommands`; the remote's `main` gets a `Makefile` whose target `lint` is `test ! -f BROKEN`, and a file named `BROKEN` makes it red; the pipeline's agents are installed with `install_agents`), `tests/entry/test_wiring_preflight.py`. F0010-S0004's test of its criterion 6 (one `run()` of `build_tick(boundaries, settings)` runs one stage; in `tests/entry/test_wiring_run.py`) meets the preflight from this story on: the tester of this story changes that one test and nothing else in it, to call `build_tick(boundaries, settings, which)` with a `which` that answers a path for every tool, settings with `pinned_agent_version="fake"` (the version of `FakeAgentRuntime`) and `state_directory` in `tmp_path` (the preflight writes its stamp there), and a `Makefile` on `main` whose target `lint` is `true`, pushed with `human.push_file`; the human's word is in `FEATURE.md` decision 28.

## Acceptance criteria

1. The tick fetches before the preflight: with an `origin/main` that failed the lint when the checkout was cloned, and a fix the human pushed afterwards, one tick given the preflight passes it (ST4.2).
2. The same order in the other direction: with a clean `origin/main` at clone time and a breaking commit the human pushed afterwards, one tick given the preflight returns `TickOutcome(stopped="main_branch_failing")` and the stop is in the health status.
3. A tick whose preflight stops does nothing else: no agent run is requested, no pull request exists in the fake hosting service, and no event is dispatched (`event is None`), although a started story is waiting on the remote.
4. A tick whose preflight stops ends before the cleanup of stale branches (F0008-S0004): with a stale remote branch of a story that is back in the backlog and a red `origin/main`, `Tick.run` returns `TickOutcome(stopped="main_branch_failing")` and the branch is still on the remote.
5. `build_preflight(boundaries, settings, which)`, with a `which` that answers a path for every tool, the pipeline's agents installed, `pinned_agent_version="fake"` and `settings.state_directory` in `tmp_path`, returns a `Preflight` whose `run()` leaves the file `preflight-stamp.json` in `settings.state_directory`, holding `settings.image`.
6. A `Tick` from `build_tick(boundaries, settings, which)` with a `which` that answers `None` for `git` returns `TickOutcome(stopped="preflight_failed")` and leaves the machine stop in the health status.
7. The tick loads and restores before the preflight: with an invalid pipeline definition on `origin/main` and a `which` that answers `None` for `git`, one tick given the preflight returns `TickOutcome(stopped="pipeline_definition_invalid")` and leaves no `preflight_failed` stop; with a valid definition, a red `origin/main` and an untracked file `notes.txt` in the checkout, it returns `TickOutcome(stopped="main_branch_failing")` and the factory log holds the line `discarded uncommitted changes: notes.txt`.
8. make check stays green.
9. docs: `docs/operator-guide.md` explains the preflight as the tick runs it (after the fetch, the load and the restore, before the cleanup and before anything is evaluated) and that a tick the preflight stops does nothing else; `docs/project-guide.md` states the order of a tick as fetch, load, restore, preflight, clean up, evaluate, dispatch; `docs/decisions.md` records why the preflight runs after the restore and not before the load (F0006 decision 10: the built tick loads the definition before it restores the checkout).

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
2. intake: accepted
   - Interface: `Tick(boundaries, instance, handlers, status=None, preflight=None)`, the order fetch, load, restore, preflight, cleanup, evaluate, dispatch, and the signatures of `build_preflight` and `build_tick` are concrete. The wiring line names every constructor argument. The change to S0004's criterion 6 test is covered by FEATURE.md decision 28.
   - Criteria: each is testable by one test function. Criteria 1 and 2 give both orders of the fetch against the preflight. Criterion 3 covers a stopped tick doing nothing else, and criterion 4 the cleanup being skipped. Criterion 5 covers the stamp. Criterion 6 covers `preflight_failed`. Criterion 7 gives the invalid-definition side and the restore side. Each stop rule has its failing side, and the passing side is criterion 1. A tick built without a preflight (`preflight=None`) keeps today's behaviour, which the existing tick tests cover.
   - Demo: runnable. The `Expect:` line gives two exact parameter lists to compare with the output.
   - Architecture: the tick change is in `application`, the wiring in `entry`, and the concrete `JsonPreflightStampFile` and `StopService` are named only in the wiring. The layering is respected.
   - Scope: this is S0010 of F0010, covering ST4.2 and the wiring. The later machine items are left to S0016, which the Assignment says.
3. tester: Wrote the red tests for the preflight in the tick and its wiring, and changed the S0004 wiring test as decision 28 says.

   Mapping:
   - criterion 1: tests/application/test_tick_preflight.py::test_a_fix_pushed_after_the_clone_is_fetched_before_the_preflight
   - criterion 2: tests/application/test_tick_preflight.py::test_a_break_pushed_after_the_clone_is_fetched_and_stops_the_tick
   - criterion 3: tests/application/test_tick_preflight.py::test_a_tick_the_preflight_stops_runs_no_agent_and_dispatches_nothing
   - criterion 4: tests/application/test_tick_preflight.py::test_a_tick_the_preflight_stops_leaves_a_stale_branch_on_the_remote
   - criterion 5: tests/entry/test_wiring_preflight.py::test_the_built_preflight_writes_its_stamp_in_the_state_directory
   - criterion 6: tests/entry/test_wiring_preflight.py::test_the_built_tick_stops_at_a_failed_machine_item
   - criterion 7 (the invalid-definition side): tests/application/test_tick_preflight.py::test_an_invalid_definition_stops_the_tick_before_the_preflight
   - criterion 7 (the restore side): tests/application/test_tick_preflight.py::test_the_checkout_is_restored_before_the_preflight_stops_the_tick
   - criteria 8 and 9: no test (`make check` and docs).

   Files created: tests/application/test_tick_preflight.py and tests/entry/test_wiring_preflight.py.
   File changed: tests/entry/test_wiring_run.py. Only `test_build_tick_runs_one_stage_in_the_production_environment_under_its_instance` changed. It now:
   - pushes a `Makefile` whose `lint` is `true` to `main` with `human.push_file`;
   - uses `settings.model_copy(update={"pinned_agent_version": "fake"})`, whose `state_directory` is already `tmp_path / "state"`;
   - calls `build_tick(boundaries, ready, _every_tool)`.
   A module-level helper `_every_tool` was added for it. The `settings` fixture is unchanged.

   How the tests are built:
   - The tick tests build `Preflight(boundaries, MachineChecks(...), JsonPreflightStampFile(tmp_path/state/preflight-stamp.json), StopService(boundaries), "build-7")`, with the pipeline's agents installed and `pinned_agent_version="fake"`.
   - Their handler factory holds a real `RunHandler` for `run` and an `IdleHandler`, so criterion 3 shows that no agent request and no pull request happen.
   - `main` gets the `Makefile` with `lint: test ! -f BROKEN`. A `BROKEN` file pushed by the human makes it red.
   - Criterion 1: "red when cloned" is simulated by pushing `BROKEN` and running `checkout.fetch()` before the human removes it again.
   - Criterion 4: the stale branch is `work-item/F0001-S0001` with a marker file, while the story is in the backlog.
   - Criterion 7: the invalid definition is `contract: [`.

   Run of `make test`: collection stops with ImportError: cannot import name `build_preflight` from `factory.entry.wiring`. The tick tests will fail on the missing `preflight` keyword of `Tick`. `make lint` is green.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
