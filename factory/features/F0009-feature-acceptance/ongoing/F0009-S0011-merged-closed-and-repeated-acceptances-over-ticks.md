---
stage: tests
pr: 113
blocked: null
comments_seen: 2
round: 0
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
