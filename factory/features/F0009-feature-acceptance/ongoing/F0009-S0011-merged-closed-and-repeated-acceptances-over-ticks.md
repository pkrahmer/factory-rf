---
stage: doing
pr: 113
blocked: null
comments_seen: 4
round: 1
attempts: 0
---
# Merged, closed and repeated acceptances over ticks

## Assignment (as of log entry 1)

Prove the acceptance's edge cases end without a loop when the whole factory runs them: real ticks over a real local remote, with the handlers registered by S0010. The earlier stories show each unit; this story walks the cases the handover names. ST2.1: an acceptance merged before its approval does not alternate between `merged` and `reject`; it is booked `accepted`, its journal says it was merged before approval, and further ticks on that state do nothing (R31). ST2.2: a repeated acceptance (another story archived since) is a new work item that does not trip `reject` and does not stay `due`; the earlier report and its cost records stay as they were. A close of an acceptance, also before its approval, books `refused` in one tick, and a feature refused is due again only after another story is archived. A hand-over of an acceptance at its approval runs through the wired `SplitByWorkItemKind`. Covers ST2.1, ST2.2 and R31 (and the repeated side of GH4.4), keeps kept thing 19 (due again whenever the set of archived stories changes) and kept thing 2 (the human's merge decides). Every criterion walks what the earlier stories built: a test may pass at once where an earlier story already does the work, and the story fails the day a wiring change breaks one of the walks.

## Interface

No new module and no new signature: the story's deliverable is the walks below. The only code it may change is what a walk shows to be wrong in the handlers of S0003 to S0007, in the reading of S0008 or in the registration of S0010; a walk that is green at once is a pass. The walks use `Tick` and `TickOutcome` (F0006-S0004), `handler_factory` and `build_handlers` (F0006-S0007 and S0010 of this feature), `Watcher` (S0008), `AcceptanceReader` (S0002, S0008) and the handlers of S0003 to S0007.

Rules:

- A tick is `Tick(boundaries, "factory-1", handler_factory(boundaries, "factory-1", <a PATH and HOME mapping>)).run()` after `install_agents(agent_home, <the roles of the fixture's pipeline definition>)`; its event and dispatch outcome are `TickOutcome.event` and `TickOutcome.dispatch`.
- The setup of a walk: the test pushes a feature `F0002-todo` of its own with `human.push_file("main", ...)` (the fixture's `F0001` has a backlog story and is never due): `feature.md` with a title, story files `F0002-S0001-a.md` and `F0002-S0002-b.md` under `done/`, nothing under `backlog/` or `in-progress/`. The first tick opens the acceptance (the event `acceptance_due`); the test then creates its pull request with `hosting.create_pull_request`, writes the pull request's number (and, where a criterion says so, the stage, `blocked` and `handed_over`) into the report's state on the branch with `human.push_file`, and the human merges or closes with `human.merge(branch, method)`, `hosting.merge_by_human` and `hosting.close_by_human`. Before the merge of criterion 1, the test pushes the backlog story `factory/features/F0002-todo/backlog/F0002-S0003-c.md` (a valid story file, title `# C`) to the acceptance's branch with `human.push_file`. A comment on a close is posted with `hosting.add_human_comment(<pull request>, <text>)` before `hosting.close_by_human(<pull request>)`, as `tests/application/test_acceptance_closed.py` does. No agent run is needed: a `run` event of an acceptance whose pull request is merged or closed is turned into `merged` or `closed` by the `RunGate` before any agent request is made.
- "No tick yields `reject`" is checked on `TickOutcome.event.kind` of every tick of the walk and on the evaluation (`Watcher.evaluate`) made before each of them.

Tests: `tests/application/test_acceptance_ticks_merged.py`, `tests/application/test_acceptance_ticks_repeated.py`, `tests/application/test_acceptance_ticks_closed.py`; the fixtures `remote`, `checkout`, `human`, `hosting` (a test subclass counting its calls is not needed: posts are read with `factory_posts`), `agent_runtime`, `boundaries`, `agent_home`, `clock` and `kill_points`.

## Acceptance criteria

1. R31: an acceptance at the stage `acceptance` whose recorded pull request the human merged is, before the next tick, the `run` event of the acceptance (not `reject`); one tick hands it through the `RunGate` to `AcceptanceMerged`, dispatches `handled`, and leaves on `origin/main` the report in `done/` with the outcome `accepted` and the entry `done (pull request merged before approval); cost: <its own cost line>`; its branch is gone and no agent request was made.
2. An acceptance at the stage `approval` whose recorded pull request the human merged is the `merged` event of the acceptance; one tick books it `accepted` with the entry `done (pull request merged); cost: <its own cost line>`.
3. An acceptance at the stage `acceptance` with `blocked == "question"` whose pull request the human merged is the `merged` event; one tick books it `accepted` like criterion 1, and the booked state has `blocked` `None`.
4. ST2.1: a second and a third tick after the booking yield the event `idle`, make no commit on `origin/main` and post nothing (`hosting.factory_posts` is unchanged).
5. No tick of the walk in criteria 1 to 4, and no evaluation made before one, yields a `reject` event.
6. After the merge of criterion 1 brought proposed stories into the feature's backlog, the feature's status is `incomplete`, `due_features()` is empty, and the next tick yields `idle` and opens no new acceptance (no branch `work-item/F0002-A0002`).
7. ST2.2: with `F0002-A0001` accepted for `F0002-S0001` and `F0002-S0002`, a story `F0002-S0003` archived afterwards makes the feature due again, and one tick yields `acceptance_due` and opens `F0002-A0002`: the branch `work-item/F0002-A0002` and its report at `in-progress/F0002-A0002-acceptance.md` exist on the remote.
8. ST2.2: the report `F0002-A0001-acceptance.md` in `done/` and its cost records file are byte for byte what they were before the repeated acceptance opened.
9. ST2.2: after the repeated acceptance `F0002-A0002` was merged, the evaluation before the next tick is its `merged` event when the walk recorded A0002 at the stage `approval` and its `run` event when it recorded it at `acceptance` (two parametrized rows), and the feature's status is `merged_unrecorded` with `due_features()` empty; after that tick its status is `accepted`, it is not due, and a further tick yields `idle`.
10. No tick of the walk in criteria 7 to 9, and no evaluation made before one, yields a `reject` event.
11. After the human closed an acceptance's pull request at the stage `approval` with a comment, one tick (the event `closed`) books it `refused` in `done/` with the comment as the reason; the feature is `refused`, not due, and further ticks yield `idle`; once another story is archived the feature is due again and the next tick opens `F0002-A0002`.
12. Close before the approval: an acceptance at the stage `acceptance` whose pull request the human closed is booked `refused` in `done/` by one tick, which hands it through the `RunGate` to `AcceptanceClosed`; no agent request is made and no tick or evaluation of the walk yields `reject`.
13. An acceptance at the stage `approval` with an open draft pull request and `handed_over` unset is handed over by one tick (the event `hand_over`): the pull request is ready for review with the four-part description, one cost table post exists, and a second tick yields `idle` with that one post in all.
14. make check stays green.
15. docs: `docs/operator-guide.md` explains what happens when an acceptance is merged or closed at any stage (accepted or refused, no loop, further ticks do nothing) and when a feature is accepted again (a new acceptance, the earlier report unchanged); `docs/decisions.md` records why each acceptance is a work item with its own report and why the gate hands an acceptance's merge and close to the acceptance's handlers.

## Demo

```bash
uv run python -c "
from factory.domain.acceptance import AcceptanceState
from factory.domain.evaluation import EvaluationInput, PullRequestObservation, evaluate
from factory.domain.hosting import PullRequestView
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot
definition = PipelineDefinition(contract='1.0', acceptance_stage='acceptance', stages={'acceptance': StageDefinition(role='reviewer', next=['approval']), 'approval': StageDefinition(approval=True, next=['done']), 'done': StageDefinition()}, roles={'reviewer': RoleDefinition(write_paths=['{work_item}'])})
def acceptance(stage):
    state = AcceptanceState(stage=stage, pull_request=7, handed_over=stage if stage == 'approval' else None, stories=['F0001-S0001'])
    return WorkItemSnapshot(id='F0001-A0001', path='factory/features/F0001-x/in-progress/F0001-A0001-acceptance.md', folder='in-progress', branch='work-item/F0001-A0001', branch_commit='1' * 40, document=WorkItemDocument(state=state, body='# Acceptance of T\n'))
def lookup(number):
    view = PullRequestView(number=number, branch='work-item/F0001-A0001', title='t', state='merged', draft=False, merge_commit='b' * 40, url='https://example.test/7')
    return PullRequestObservation(view=view, comments=[])
for stage in ('approval', 'acceptance'):
    facts = EvaluationInput(definition=definition, snapshots=[acceptance(stage)], main_commit='a' * 40)
    print(evaluate(facts, lookup, lambda state: 'none').key)
"
```
Expect: two lines: `merged:F0001-A0001` (an acceptance at its approval is waiting, so its merged pull request is looked up and the merge is the event, never `reject`), then `run:F0001-A0001` (an acceptance at its agent stage is runnable; the `RunGate` reads its pull request before any agent request and hands a merged one to the acceptance's merge handler).

## Log (append only)

1. 2026-10-12 human: created.
2. intake: 1. Criterion 6 starts from "the merge of criterion 1 brought proposed stories into the feature's backlog". The Interface's setup does not say how the walk puts proposed stories on the acceptance's branch. Options: (a) the test pushes a backlog story file such as `backlog/F0002-S0003-c.md` to the branch with `human.push_file` before the merge; (b) the criterion drops the proposed stories and only checks idle/no new acceptance. I would choose (a). Please add the file name and location to the setup, so the tester and the coder do not each decide.
   2. Criterion 9 says the evaluation before the next tick is "its `merged` or `run` event". One test function cannot check an either/or without a further decision. The event depends on the stage the test records for A0002 (`approval` gives `merged`, `acceptance` gives `run`). Please name the stage the walk records, or split it into two parametrized rows with the event each expects. I would choose two rows: `approval` gives `merged`, `acceptance` gives `run`.
   3. Criterion 11 says the human closed the pull request "with a comment", but the Interface does not say how the comment is posted. I assume a comment on the fake hosting service, such as a human-authored comment added before `hosting.close_by_human`. Please name the call.
3. human (pull request comment, 2026-10-15): 1 (a): before the merge, the test pushes the backlog story `factory/features/F0002-<the fixture's slug>/backlog/F0002-S0003-c.md` (a valid story file, title `# C`) to the acceptance's branch with `human.push_file`; add that file name and location to the setup.
   2: two parametrized rows, as you propose: the walk records A0002 at `approval` and expects `merged`; at `acceptance` and expects `run`.
   3: the comment is posted with `hosting.add_human_comment(<pull request>, <text>)` on the fake hosting service before `hosting.close_by_human(<pull request>)`, as `tests/application/test_acceptance_closed.py` does; name both calls in the setup.
   The Interface stays as it is otherwise.
4. intake: accepted. Carried in from log entry 3 (the human's answers to my three questions), written into the story and nothing else: (1) the Interface's setup now names the backlog story `factory/features/F0002-todo/backlog/F0002-S0003-c.md` (title `# C`), pushed to the acceptance's branch with `human.push_file` before the merge; (2) criterion 9 now has two parametrized rows: A0002 recorded at `approval` gives `merged`, at `acceptance` gives `run`; (3) the setup names `hosting.add_human_comment(<pull request>, <text>)` before `hosting.close_by_human(<pull request>)`. The Assignment's meaning is unchanged, so it is not rewritten.
   - Interface: no new signature, by design. It names the concrete pieces the walks use (`Tick`, `TickOutcome`, `handler_factory`, `build_handlers`, `Watcher`, `AcceptanceReader`, the fixtures and the three test files), and its setup is now complete.
   - Criteria: each is testable by one test function. Every rule has its failing side: merged and closed, accepted and refused, due and not due, `reject` never raised, repeated ticks idle. Criterion 11 covers the repeated-due side after another archive. Criterion 9's either/or is resolved.
   - Demo: the command is runnable, and its Expect line gives two checkable lines (`merged:F0001-A0001`, then `run:F0001-A0001`).
   - Architecture: nothing new is added. The walks go through the entry-layer wiring and the application handlers, and git and the hosting service are used only through the fixtures.
   - Scope: within F0009's goal (ST2.1, ST2.2, R31) and not in its Out of scope.
5. tester: wrote the walks. Each one runs the real Tick through `handler_factory` against a real local remote. Before every tick it records a `Watcher.evaluate`, so the "no reject" criteria can be checked across a whole walk.
   - criterion 1: tests/application/test_acceptance_ticks_merged.py::test_a_merge_at_the_review_stage_runs_through_the_gate_and_is_booked_before_approval
   - criterion 2: tests/application/test_acceptance_ticks_merged.py::test_a_merge_at_the_approval_is_the_merged_event_and_is_booked_accepted
   - criterion 3: tests/application/test_acceptance_ticks_merged.py::test_a_merge_while_the_reviewer_asks_is_booked_accepted_and_unblocked
   - criterion 4: tests/application/test_acceptance_ticks_merged.py::test_the_ticks_after_the_booking_are_idle_commit_nothing_and_post_nothing (one row for each of the walks in criteria 1 to 3)
   - criterion 5: tests/application/test_acceptance_ticks_merged.py::test_no_tick_or_evaluation_of_a_merged_acceptance_is_a_reject (same three rows)
   - criterion 6: tests/application/test_acceptance_ticks_merged.py::test_proposed_stories_leave_the_feature_incomplete_and_open_no_new_acceptance
   - criterion 7: tests/application/test_acceptance_ticks_repeated.py::test_a_story_archived_after_the_acceptance_opens_the_next_acceptance_in_one_tick
   - criterion 8: tests/application/test_acceptance_ticks_repeated.py::test_opening_the_repeated_acceptance_leaves_the_earlier_report_and_costs_byte_for_byte
   - criterion 9: tests/application/test_acceptance_ticks_repeated.py::test_the_merged_repeated_acceptance_is_booked_in_one_tick_and_the_feature_rests (rows: approval→merged, acceptance→run)
   - criterion 10: tests/application/test_acceptance_ticks_repeated.py::test_no_tick_or_evaluation_of_a_repeated_acceptance_is_a_reject (same two rows)
   - criterion 11: tests/application/test_acceptance_ticks_closed.py::test_a_close_at_the_approval_is_booked_refused_with_the_comment_until_another_archive
   - criterion 12: tests/application/test_acceptance_ticks_closed.py::test_a_close_before_the_approval_runs_through_the_gate_and_is_booked_refused
   - criterion 13: tests/application/test_acceptance_ticks_closed.py::test_an_acceptance_at_its_approval_is_handed_over_once_through_the_wiring
   - criteria 14 and 15: not tests (check gate; documenter).

   Files created: tests/acceptance_walk.py, a shared helper at the tests root like human_clone.py and bill_support.py, with the `AcceptanceWalk` class. It installs the agents and pushes `F0002-todo` with two archived stories. Its methods are open (the tick plus `create_pull_request`), record (rewrites the state of the opened report on its branch and adds a started entry and a cost-records sidecar), propose (pushes `backlog/F0002-S0003-c.md`, title `# C`), merge, close (optionally after `add_human_comment`), booked, status and due. Also created: the three test files the Interface names.

   Choices made within the spec:
   - At `approval`, the merge walks and the close walk record `handed_over="approval"`, as the Demo does. The hand-over walk leaves it unset.
   - The backlog story is pushed only in the criterion 1 walk, as the Interface says.
   - The refusal reason is checked as the first paragraph of the Recommendation, `Refused by the human on <clock date>: <comment>`, as tests/application/test_acceptance_closed.py does.
   - The "four-part description" is checked as equal to `acceptance_description(<the recorded report>, "acceptance-reviewer")`.

   Result of `make test`: green (coverage 99.53 %). Every walk passes at once: the earlier stories already do the work, which the Interface allows ("a walk that is green at once is a pass"). The test runner could import every module. `make lint` is green. The coder has nothing red to fix and only needs `make check` green.

   `make lint`: lint: green
   `make test`: test: green
6. coder: I made no code changes. The tester reported every walk as green at once, and `make test` agrees: the handlers, the reading and the registration from the earlier stories already do the work. `make check` is red at `make types`, though, and the cause is in the tester's helper, not in `src`:

   `tests/acceptance_walk.py:128: error: Incompatible return value type (got "list[Literal['run', ..., 'idle']]", expected "list[str]")  [return-value]`

   `AcceptanceWalk.kinds` is annotated `-> list[str]`. It returns a list built from `Event.kind`, whose type is the `EventKind` Literal, and `list` is invariant. The tester ran only `make lint` and `make test`, so mypy never saw the file.

   I may not edit tests (R9), and changing `EventKind` in `src` to fit a test helper would be wrong. Options:
   (a) The tester changes the return annotation of `AcceptanceWalk.kinds` in `tests/acceptance_walk.py` to `list[EventKind]`, imported from `factory.domain.events`. The callers only check membership, so nothing else changes.
   (b) The tester keeps `list[str]` and annotates the two comprehensions as `list[str]`.
   (c) The tester changes the annotation to `Sequence[str]`.

   I would choose (a): it is the precise type and needs one import. If you approve, the coder ends with `tests` and names this change. Once mypy is green, nothing else in the story needs code; `make lint` and `make test` already pass.
7. human (pull request comment, 2026-10-16): (a): the tester changes the return annotation of `AcceptanceWalk.kinds` in `tests/acceptance_walk.py` to `list[EventKind]`, imported from `factory.domain.events`, and changes nothing else. End with `tests` and name exactly that change.
8. coder: the human answered in log entry 7 with option (a). The test change: in `tests/acceptance_walk.py`, change the return annotation of `AcceptanceWalk.kinds` from `list[str]` to `list[EventKind]`, import `EventKind` from `factory.domain.events`, and change nothing else. I left `src` alone: every walk already passes against the existing handlers, reading and registration. Once this change is in, `make types` should pass and nothing else in the story needs code. After the tester sends the ticket back, the coder runs `make check` and hands it to review.
9. tester: tester (test change the human approved, log entry 7, named by the coder in entry 8): in `tests/acceptance_walk.py` I changed the return annotation of `AcceptanceWalk.kinds` from `list[str]` to `list[EventKind]`, and changed its import to `from factory.domain.events import Event, EventKind`. Nothing else changed: two lines in one file. The reason is that `kinds` returns `Event.kind` values, whose type is the invariant `EventKind` Literal, so mypy --strict rejected `list[str]` (`tests/acceptance_walk.py:128 [return-value]`). `make test`: green, coverage 99.53 %. Per this mode I did not run `make types`; the coder's `make check` should now pass it.

   `make lint`: lint: green
   `make test`: test: green
10. coder: I made no code changes. The tester changed the annotation of `AcceptanceWalk.kinds` as the human decided in entry 7 (entry 9). `make check` now passes from start to finish, including `make types`, which failed before; coverage is 99.53 %. All thirteen walks in `tests/application/test_acceptance_ticks_{merged,repeated,closed}.py` passed without any change to `src`. The work is done by the handlers of S0003 to S0007, the reading of S0008 and the registration of S0010, which the Interface allows ("a walk that is green at once is a pass").
       - Design decision: leave `src` untouched. I rejected adjusting `EventKind` or any handler to fit the test helper, because no walk shows wrong behaviour.
       - Refactor: there is no diff outside `factory/` and `tests/`, so there is nothing to refactor.
       - Open: criterion 15 (the docs in `docs/operator-guide.md` and `docs/decisions.md`) is the documenter's.

    `make check`: check: green
11. reviewer: groups 1 to 3 pass. Each of the 13 criteria has a walk that checks what the criterion says. Criteria 5 and 10 check both the evaluation before each tick and every tick's event. Criterion 9 has its two rows. The Interface states no limits that need a boundary test. The coder's entry 10 reports `make check` green. The diff touches only `tests/`, so the architecture and security groups have nothing to object to. Group 4 (quality) fails. `CLAUDE.md` says to reuse an existing helper and counts a second copy as a finding, and it says shared fixtures go in `tests/conftest.py`. The test-file changes below belong to the tester (R9), so the coder routes them with `tests`.
    1. `tests/acceptance_walk.py:62` `branch_of`: copies `factory.domain.identifiers.branch_name` (`BRANCH_PREFIX + id`) and hard-codes `"work-item/"`. Fix: delete `branch_of` and use `branch_name` in the helper and in the three test files that import it.
    2. `tests/acceptance_walk.py:67` `report_of`: builds the path by hand when `factory.domain.paths.work_item_path(feature_directory, folder, file_name)` already does this. Fix: build it as `work_item_path("F0002-todo", folder, f"{work_item}-acceptance.md")`, and `TODO`/`PROPOSED` the same way (or through `feature_file_path` for `feature.md`).
    3. `tests/application/test_acceptance_ticks_closed.py:28` and `tests/application/test_acceptance_ticks_merged.py:31`: the same `walk` fixture is written out twice. `CLAUDE.md` (Tests) says shared fixtures go in `tests/conftest.py`. Fix: move the plain `walk` fixture to `tests/conftest.py`. In `tests/application/test_acceptance_ticks_repeated.py`, build on it as a fixture that does the A0001 setup.
12. coder: coder (round 1): all three findings in the review (entry 11) are about test code (`tests/acceptance_walk.py` and the three walk files). I may not edit tests (R9), so I am sending them to the tester. I made no change to `src`, because no finding is about production code. I checked that the helpers the reviewer named exist: `factory.domain.identifiers.branch_name(work_item)` returns `BRANCH_PREFIX + id` and checks the id. `factory.domain.paths.work_item_path(feature_directory, folder: LifecycleFolder, file_name)` and `feature_file_path(feature_directory)` build the same strings the helper builds by hand. The changes for the tester, exactly as entry 11 names them:
    1. In `tests/acceptance_walk.py`, delete `branch_of`. Use `factory.domain.identifiers.branch_name` instead, both in the helper and in the three test files that import `branch_of`.
    2. In `tests/acceptance_walk.py`, build `report_of` as `work_item_path("F0002-todo", folder, f"{work_item}-acceptance.md")`. Its `folder` parameter must be typed `LifecycleFolder` so `mypy --strict` accepts it. Build `TODO`/`PROPOSED` the same way (`feature.md` through `feature_file_path`).
    3. Move the `walk` fixture, which is written out twice (`tests/application/test_acceptance_ticks_closed.py:28` and `tests/application/test_acceptance_ticks_merged.py:31`), into `tests/conftest.py`. In `tests/application/test_acceptance_ticks_repeated.py`, the fixture becomes one that builds on the shared `walk` and does the A0001 setup.
    After the tester's change, the coder runs `make check` and hands the ticket to review. Nothing else is open, except criterion 15 (docs), which belongs to the documenter.
13. tester: tester (test change the human approved, review entry 11, named by the coder in entry 12): I made the three named changes and nothing else.
       1. `tests/acceptance_walk.py`: deleted `branch_of`. The helper and the three walk files now use `factory.domain.identifiers.branch_name`.
       2. `tests/acceptance_walk.py`: `report_of` now returns `work_item_path(TODO, folder, f"{work_item}-acceptance.md")`, with `folder: LifecycleFolder`. `TODO` is now the feature directory `"F0002-todo"`. `PROPOSED` and the archived stories use `work_item_path`, and `feature.md` uses `feature_file_path`.
       3. `tests/conftest.py`: has the plain `walk` fixture, removed from `test_acceptance_ticks_closed.py` and `test_acceptance_ticks_merged.py`. In `test_acceptance_ticks_repeated.py`, `walk` now overrides the shared fixture by requesting it (`def walk(walk: AcceptanceWalk)`) and does only the A0001 setup, so the test functions keep their names.
       `ruff --fix` removed the imports that became unused. No test body changed apart from the `branch_of` → `branch_name` rename. As this mode says, I did not run `make types`; the coder's `make check` covers it.

       `make lint`: lint: green
       `make test`: test: green (coverage 99.53 %)

    `make lint`: lint: green
    `make test`: test: green
