---
stage: done
pr: 112
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The acceptance's handlers in the production wiring

## Assignment (as of log entry 1)

Register the acceptance's handlers in the production wiring and take the last kind out of `NOT_YET_HANDLED` (questionnaire 1, Q20 A: the wiring grows with each feature, `factory.entry.wiring.build_handlers` is the one place that registers a handler). `acceptance_due` gets `AcceptanceDueHandler` (S0003); `hand_over`, `merged` and `closed` get a `SplitByWorkItemKind` (S0004) of the story's handler (F0007) and the acceptance's (`AcceptanceHandOver`, `AcceptanceMerged`, `AcceptanceClosed`). F0007-S0010 built the `RunGate` with the very `ClosedHandler` and `MergedHandler` registered for `closed` and `merged`; if only the mapping's values changed, an acceptance whose pull request was merged or closed while its stage was due would reach the gate as a `run` event and go to the story's handler, which archives it with stage `done` and no `outcome` (a state the acceptance reader refuses on every tick after) or moves it back to `backlog/`. So the gate is built with the two splits, and the same split instances are the values of `closed` and `merged`. A project whose pipeline definition has no `acceptance_stage` must still tick: every handler of an acceptance constructs without an error and refuses an event it is given with `CannotHandle(kind, "no acceptance stage")` (decision 5 of the feature). Two tests of earlier stories break and are changed here, with the human's leave of Q20 (as F0007 decision 23 cites it) and nothing else of those files: in `tests/entry/test_wiring_handlers.py`, `test_an_event_not_yet_handled_is_a_counted_error`, which is the test of F0006-S0007 criterion 9 and of F0007-S0010 criterion 13 as F0008-S0001 left it, and in `tests/entry/test_wiring_human_handlers.py` the test of F0007-S0010 criterion 10, as F0008-S0001 left it. F0008-S0001's remark that its forms "hold for F0009 as well" is true for the other wiring tests (F0006-S0007 criteria 4 and 5, F0007-S0010 criteria 9 and 12, F0008's criteria on `crash` and `expired`), which compare against `NOT_YET_HANDLED` and the key set without naming the value, and wrong for these two. Covers SI2.4 end to end for the last kind (an event kind with a handler never reaches `UnhandledEvent`); keeps kept thing 12 (a state no handler was written for is a counted error, never silence). Uses `build_handlers`, `NOT_YET_HANDLED` and `handler_factory` (F0006-S0007), `RunGate` (F0007-S0010), `RecoveryHandler` (F0008) and the handlers of S0003 to S0007.

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
  - In `tests/entry/test_wiring_handlers.py`, `test_an_event_not_yet_handled_is_a_counted_error` (the one test of F0006-S0007 criterion 9 and F0007-S0010 criterion 13, as F0008-S0001 left it: it dispatches an `acceptance_due` event and expects `UnhandledEvent`) becomes one test parametrized over the keys `comment` and `crash`: it builds a `Dispatcher` over `build_handlers(...)` with that key removed, dispatches an event of that kind about a work item, and expects `error` with the last error `UnhandledEvent: no handler for event kind <kind>`.
  - In `tests/entry/test_wiring_human_handlers.py`, the test of F0007-S0010 criterion 10, as F0008-S0001 left it (the values of the ten kinds it names, each by its key), now checks `merged`, `closed` and `hand_over` as `SplitByWorkItemKind` instances whose `story` handlers are `MergedHandler`, `ClosedHandler` and `HandOverHandler`, and the gate's `closed` and `merged` properties as the very instances registered for `closed` and `merged`; its checks of the other keys are unchanged.
  Criteria 2, 3, 5 and 6 below are those changed tests.

Tests: `tests/entry/test_wiring_acceptance.py` (a new file) for the registration; the two changed tests named above in their files. The wiring tests use the shared fixtures of F0006-S0007 (`remote`, `checkout`, `human`, `hosting`, `agent_runtime`, `boundaries`, `agent_home`, `clock`) and start a complete story as it does. The test of criterion 8 pushes the fixture's pipeline definition without its `acceptance_stage` line to `factory/pipeline.yml` with `human.push_file("main", ...)` (the stage `acceptance` may stay in the stages table) and ticks with `Tick(boundaries, "factory-1", handler_factory(boundaries, "factory-1", <a PATH and HOME mapping>))` after `install_agents(agent_home, <the roles of the fixture's pipeline definition>)`, as F0006-S0007's tests do.

## Acceptance criteria

1. `NOT_YET_HANDLED` is `()`, every kind of `EventKind` is a key of `build_handlers(...)`, `unhandled_kinds(build_handlers(...))` is `[]`, and `build_handlers(...)["acceptance_due"]` is an `AcceptanceDueHandler`.
2. The values of `merged`, `closed` and `hand_over` are `SplitByWorkItemKind` instances whose `story` handlers are a `MergedHandler`, a `ClosedHandler` and a `HandOverHandler` and whose `acceptance` handlers are an `AcceptanceMerged`, an `AcceptanceClosed` and an `AcceptanceHandOver` (F0007-S0010 criterion 10 as changed here).
3. The `RunGate` that is the value of `run` holds the very `SplitByWorkItemKind` instances registered for `closed` and `merged` (its `closed` and `merged` properties), and its `run` property is a `RunHandler` (F0007-S0010 criterion 10 as changed here).
4. A `merged` event of a story dispatched through `build_handlers(...)["merged"]` archives the story under `done/` on `origin/main`: it reaches the story's handler.
5. A `Dispatcher` built over `build_handlers(...)` with the key `comment` removed returns `error` for a `comment` event, and its status holds `UnhandledEvent: no handler for event kind comment` as the last error (F0006-S0007 criterion 9 as changed here: the `comment` row of the one parametrized test).
6. A `Dispatcher` built over `build_handlers(...)` with the key `crash` removed returns `error` for a `crash` event, and its status holds `UnhandledEvent: no handler for event kind crash` as the last error (F0007-S0010 criterion 13 as changed here: the `crash` row of the same test).
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
2. intake: accepted
   - Interface: names `factory/src/factory/entry/wiring.py` with `NOT_YET_HANDLED` and the `build_handlers` signature, and states each registered value (the two split instances shared by the keys and the one `RunGate`, `hand_over`, `acceptance_due`). The two changed tests are named by file and function, with the exact new form of each.
   - Criteria: each is testable by one test function. Criteria 1 to 4 cover the registration and the gate. Criteria 5 and 6 are the two rows of the one parametrized test. Criterion 7 covers the gate's refusal path for a closed acceptance. Criterion 8 covers the failing side of the no-`acceptance_stage` rule (`CannotHandle` with the reason `no acceptance stage`, and the tick still handles `run`). Every behaviour the Interface states has a criterion, and the changed tests are criteria 2, 3, 5 and 6.
   - Demo: one runnable command. Its `Expect:` line gives two checkable output lines (`()` and the `CannotHandle` text).
   - Architecture: the change is confined to `factory.entry` (wiring), as `CLAUDE.md` requires. It reuses application handlers and adds no new dependency.
   - Scope: within F0009 scope item 16 and decisions 5, 21 and 22. The test changes to other stories' files are limited to the two named ones and carry the leave of Q20.
3. tester: Wrote the tests for every behaviour criterion. As the Interface allows, two earlier tests are changed and nothing else in their files.

   Criterion → test:
   - criterion 1: tests/entry/test_wiring_acceptance.py::test_every_kind_has_a_handler_and_acceptance_due_opens_the_acceptance
   - criterion 2: tests/entry/test_wiring_human_handlers.py::test_each_kind_has_its_handler_and_the_gate_shares_the_closed_and_merged_handlers (changed: `merged`, `closed` and `hand_over` are now checked as `SplitByWorkItemKind`, with `story` a MergedHandler/ClosedHandler/HandOverHandler and `acceptance` an AcceptanceMerged/AcceptanceClosed/AcceptanceHandOver; the other keys are unchanged)
   - criterion 3: the same test (its existing checks: `gate.run` is a RunHandler, and `gate.closed` / `gate.merged` are the very instances registered for `closed` / `merged`)
   - criterion 4: tests/entry/test_wiring_acceptance.py::test_a_merged_story_reaches_the_story_handler_and_is_archived
   - criterion 5: tests/entry/test_wiring_handlers.py::test_an_event_without_a_handler_is_a_counted_error[comment] (replaces test_an_event_not_yet_handled_is_a_counted_error; it is parametrized over `comment` and `crash`, removes that key from build_handlers' result and dispatches an event about a story)
   - criterion 6: tests/entry/test_wiring_handlers.py::test_an_event_without_a_handler_is_a_counted_error[crash]
   - criterion 7: tests/entry/test_wiring_acceptance.py::test_a_run_of_an_acceptance_closed_while_due_is_booked_refused_by_the_gate
   - criterion 8: tests/entry/test_wiring_acceptance.py::test_without_an_acceptance_stage_the_handlers_build_refuse_and_a_story_still_ticks

   How criterion 7 is tested: the acceptance is opened through AcceptanceService, its report is pushed at stage `acceptance` with a draft pull request, and the human then closes the pull request. The test asserts that the report is booked in done/ with stage `done` and outcome `refused`, and that no agent request was made. That the story's ClosedHandler is not called is shown by that booked outcome; no spy is used.

   Files: created tests/entry/test_wiring_acceptance.py; changed tests/entry/test_wiring_handlers.py (the one test, plus a `_snapshot` helper and imports) and tests/entry/test_wiring_human_handlers.py (the one test, plus imports).

   `make test`, run once: the 4 expected tests fail; all modules import, so there are no collection errors. I piped the run through `tail -15`, so I saw only which tests failed, not their messages. The reasons below are inferred from the current wiring, not read from the output:
   - criterion 1: `NOT_YET_HANDLED` is still ("acceptance_due",).
   - criteria 2–3: `merged` is still a plain MergedHandler.
   - criterion 7: the gate still sends the event to the story's ClosedHandler.
   - criterion 8: there is no `acceptance_due` key yet.

   The tests for criteria 4–6 already pass, as they should: they cover behaviour the current wiring has and that must survive the change. `make lint` is green. I skipped `make types`, as this stage allows.

   `make lint`: lint: green
   `make test`: FAILED tests/entry/test_wiring_human_handlers.py::test_each_kind_has_its_handler_and_the_gate_shares_the_closed_and_merged_handlers
4. coder: Registered the acceptance's handlers in `src/factory/entry/wiring.py` (commit 861b72b). The tests were not changed.
   - `NOT_YET_HANDLED` is now `()`.
   - `build_handlers` builds `closed = SplitByWorkItemKind(ClosedHandler, AcceptanceClosed)` and `merged = SplitByWorkItemKind(MergedHandler, AcceptanceMerged)` once. Those two instances are the values of `closed` and `merged` and also the `closed` and `merged` arguments of the one `RunGate`, which `RecoveryHandler` reruns through.
   - `hand_over` is `SplitByWorkItemKind(HandOverHandler, AcceptanceHandOver)`, and `acceptance_due` is `AcceptanceDueHandler`.
   - With no `acceptance_stage`, every constructor still builds. The handlers refuse their events themselves (S0003 to S0007), so the wiring has no branch on the definition.

   Main decision: give the gate the same split instances instead of keeping the story's handlers inside the gate and splitting only the mapping's values. The alternative would send an acceptance closed or merged while due to the story's handlers through the `run` event, and they would archive it in a state the acceptance reader refuses. A one-line comment at the gate gives this reason. The `docs/decisions.md` entry belongs to the documenter (criterion 10).

   Refactor: I read the diff and found nothing to change, so there is no refactor commit.

   `make check`: green, coverage 99.53 %.

   Not touched: the comment above `NOT_YET_HANDLED` ("registering one removes it here") still describes the constant correctly now that it is empty.

   `make check`: check: green
5. reviewer: no findings.
   - Acceptance criteria: every criterion from 1 to 8 has a test that checks what the criterion names.
     - Criterion 1: `NOT_YET_HANDLED == ()`, the key set equals `EventKind`, `unhandled_kinds` is `[]`, and `acceptance_due` is an `AcceptanceDueHandler`.
     - Criteria 2 and 3: the changed test in `tests/entry/test_wiring_human_handlers.py` checks the three splits' `story`/`acceptance` classes, `gate.run` as a `RunHandler`, and `gate.closed`/`gate.merged` by identity. Its other checks are unchanged.
     - Criterion 4: a story merged through `build_handlers(...)["merged"]` is archived under `done/` on `origin/main`.
     - Criteria 5 and 6: one test parametrized over `comment` and `crash` removes that key and expects `error` and the `UnhandledEvent` text.
     - Criterion 7: the `run` event of an acceptance whose pull request was closed while due is booked `done`/`refused` in `done/`, and no agent request is made. The story's `ClosedHandler` would have moved it to `backlog/`, so the booked outcome shows it was not called.
     - Criterion 8: with `acceptance_stage` removed, `CannotHandle` is raised with the reason `no acceptance stage`, and one `Tick` over `handler_factory` returns `handled` for `run`.
     - The failing side of the no-`acceptance_stage` rule is covered here for `acceptance_due` and, for the other acceptance handlers, by the earlier stories' criteria the Interface cites.
     - The coder's entry reports the factory's `make check` as green.
   - Architecture: the change stays in `factory.entry.wiring`, which imports only application handlers. `src/factory/entry/wiring.py` builds the two splits once and passes the same instances to `RunGate` and to the mapping's `closed` and `merged`.
   - Security: the diff adds no suppression markers, secrets or string-built commands.
   - Quality: the comment at the gate explains why it holds the splits, and the code has no dead or duplicated logic. The `_snapshot` helper and the imports added to `tests/entry/test_wiring_handlers.py` exist only for the changed test, which the Interface allows.
   - Ticket hygiene: the coder's log gives the main decision (the gate holds the splits) and the alternative it rejected. `Assignment` matches the code, and criterion 10 still says what the documenter must write.
6. documenter: wrote the documentation criterion 10 asks for; no findings. The code matches the Interface (`NOT_YET_HANDLED == ()`, the splits and the gate share the same instances).

   Files changed:
   - `docs/project-guide.md` ("The handlers of the events"): `build_handlers` now returns all thirteen kinds. `merged`, `closed` and `hand_over` are named as `SplitByWorkItemKind`s and `acceptance_due` as `AcceptanceDueHandler`. The `RunGate` holds the `closed` and `merged` splits, the very instances registered for those keys. With no `acceptance_stage` everything still constructs and the acceptance handlers refuse with `CannotHandle(kind, "no acceptance stage")`. `NOT_YET_HANDLED` is empty, and the paragraph on it was reworded accordingly.
   - `docs/operator-guide.md` (the dispatcher's stops): it said `acceptance_due` had no handler. Now every kind has one and the unhandled-kind stop is described as applying only to a future kind.
   - `docs/decisions.md`: new entry "The run gate holds the acceptance splits, not the story's handlers". It gives the reason (an acceptance closed or merged while due would otherwise reach the story's handlers) and the rejected alternative (a work-item-kind branch inside the gate).

   Cross-read and found current: `README.md`, and the project-guide sections on acceptance (opening, hand-over, `SplitByWorkItemKind`) and on events. I left alone the earlier `NOT_YET_HANDLED` decision in `docs/decisions.md`: it records why the constant exists, which still holds.

   Nothing stale left that is unrelated to this story.

   `make check`: green, coverage 99.53 %. I did not run the demo command.

   `make check`: check: green
7. demo: no findings.

   I ran the one command under `## Demo` from the repository root, exactly as written. It exited with code 0.

   ```
   ()
   cannot handle acceptance_due: no acceptance stage
   ```

   It met its `Expect:` line: there are two lines. The first, `()`, shows that `NOT_YET_HANDLED` is empty. The second shows that `AcceptanceDueHandler` builds from a definition without `acceptance_stage` and refuses the event with `CannotHandle` and the reason `no acceptance stage`.

   Against the acceptance criteria:
   - The output agrees with criterion 1 (`NOT_YET_HANDLED` is `()`).
   - It also agrees with the refusal half of criterion 8 (the handler builds without an error, and handling the event raises `CannotHandle` with the reason `no acceptance stage`).
   - No criterion is contradicted.
   - The demo does not exercise criteria 2 to 7: the registered values, the shared split instances in the `RunGate`, the merged and closed paths, and the `UnhandledEvent` rows. Their tests are named in the tester's entry.
8. done (pull request merged); cost: 6 runs, 23.0 min, 56 turns, 149k tokens in (1401k more from cache), 22k out, $1.69
