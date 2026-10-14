---
stage: ready
pr: 72
blocked: null
comments_seen: 2
round: 0
attempts: 0
---
# The watcher's evaluation in four tiers

## Assignment (as of log entry 1)

Build the function that turns what the remote shows into one event, and the watcher that feeds it. The evaluation keeps no memory: it takes the work items read by F0006-S0001, the pipeline definition and two callables (the one pull request lookup and the claim status), and returns the first match of four tiers: integrity (two work items with one id), the human's signals (a merged or closed pull request, a hand-over due, new comments, a question not yet posted), the agent at work (an own, expired or held claim), and new work in id order (the attempts-cap question or `run`). A work item that waits for the human holds back all new work, and at most one pull request lookup is made per evaluation. Because the evaluation keeps no memory, a `run` event that the dispatcher has capped is still the first runnable work item on the next evaluation (F0006-S0004 decides what that means for the tick). The `reject` event (an illegal stage change) is added to tier 1 by F0006-S0005. The handlers of these events belong to later features, except `idle` and `run` (F0006-S0007). Covers R18 (the claim tier through F0004's service); keeps kept things 15 (waiting outranks new work; one agent run at a time; id order), 16 (an idle tick costs at most one lookup) and 12 (a state no handler was written for becomes an event, never silence). Uses `RemoteWorkItems` (F0006-S0001), `ClaimService` and `claim_status` (F0004), `HostingService` (F0001-S0002), `Boundaries` (F0003-S0002).

## Interface

`src/factory/domain/events.py`

```python
EventKind = Literal[
    "run", "comment", "ask", "merged", "closed", "reject", "hand_over", "crash",
    "expired", "duplicate", "pull_request_lookup", "acceptance_due", "idle",
]

class Event(BaseModel):
    kind: EventKind
    work_item: WorkItemSnapshot | None        # None for "idle" and "acceptance_due"
    pull_request: PullRequestView | None = None   # the evaluation's one lookup, when it was made and succeeded
    feature: FeatureId | None = None          # set for "acceptance_due" (F0009), and only for it
    remote_state: CommitId                    # head of the work item's remote branch, else of origin/main
    detail: str = ""                          # display only; no code reads it back

    @property
    def key(self) -> str: ...                 # f"{kind}:{work item id, else feature id, else '-'}"
```

`src/factory/domain/evaluation.py`

```python
class PullRequestObservation(BaseModel):      # what the one lookup returns
    view: PullRequestView
    comments: list[PullRequestComment]        # empty unless view.state == "open"

class EvaluationInput(BaseModel):
    definition: PipelineDefinition
    snapshots: list[WorkItemSnapshot]         # plain id order, as RemoteWorkItems.read returns them
    main_commit: CommitId                     # head of origin/main

PullRequestLookup = Callable[[int], PullRequestObservation]   # raises HostingServiceError when it fails
ClaimStatusOf = Callable[[WorkItemState], ClaimStatus]

def waiting(state: WorkItemState, definition: PipelineDefinition) -> bool: ...
def question_posted(snapshot: WorkItemSnapshot, comments: Sequence[PullRequestComment]) -> bool: ...
def evaluate(facts: EvaluationInput, lookup: PullRequestLookup, claim_status: ClaimStatusOf) -> Event: ...
    # ValueError for a snapshot with no state, or in a stage the definition lacks
```

Every model here is frozen and forbids unknown keys.

`src/factory/application/watcher.py`

```python
class Watcher:
    def __init__(self, boundaries: Boundaries, instance: Name) -> None: ...
    def evaluate(self, definition: PipelineDefinition) -> Event: ...
        # GitError (also when origin/main does not resolve); WorkItemFormatError (from RemoteWorkItems.read)
```

Rules for `Event`: it refuses, with `ValidationError`, a `work_item` set for kind `idle` or `acceptance_due`, a missing `work_item` for every other kind, a `feature` set for any kind but `acceptance_due`, and a missing `feature` for `acceptance_due`.

Rules for `evaluate`, in this order; the first that matches decides:

- Tier 1. Two snapshots with the same id (the first such id in id order): `Event(kind="duplicate", work_item=<the first of the two snapshots>, detail=f"{id} at {path} and {path}")` with both paths in snapshot order.
- Validation, after tier 1, before any call of `role_of`, `position` or `waiting`: a snapshot whose `document.state` is `None` raises `ValueError(f"work item {id} has no state")`; one whose stage is not in `definition.stages` raises `ValueError(f"work item {id}: stage {stage} is not in the pipeline definition")`. The evaluation therefore settles the question F0003 left open for its first caller: an unknown stage never reaches the definition's accessors.
- `waiting(state, definition)` is true when `state.blocked` is not `None` or `definition.stages[state.stage].approval` is true.
- Tier 2, for the first waiting work item `W` in snapshot order, and no other:
  - `W` has no `pull_request`: `Event(kind="ask", work_item=W, detail="no pull request")`; no lookup is made.
  - Otherwise `lookup(W.document.state.pull_request)` is called once. If it raises `HostingServiceError`: `Event(kind="pull_request_lookup", work_item=W, detail=<the error's text>)`.
  - `view.state == "merged"`: `Event(kind="merged", work_item=W, pull_request=view)`; `"closed"`: kind `"closed"`.
  - Open, stage is an approval and `state.handed_over != state.stage`: kind `"hand_over"`.
  - Open and `comments` holds a comment with `by_factory` false whose id is not in `state.comments_read`: kind `"comment"`, detail `f"{n} new comments"` with the count.
  - Open, `state.blocked` is not `None` and `question_posted(W, comments)` is false: kind `"ask"`.
  - Otherwise `Event(kind="idle", work_item=None, pull_request=view)` with a `detail` that names `W`'s id: nothing below tier 2 is reached.
  - Every event of this list except `idle` carries `W`'s snapshot and `pull_request=view` (when the lookup succeeded).
- `question_posted` is true when some comment has `by_factory` true and a `key` with `key.work_item == snapshot.id`, `key.kind == state.blocked` and `key.n == str(<number of the latest record of kind "question" in state.journal>)`; false when `blocked` is `None` or the journal holds no `question` record. A record written after the question (a `comment`, for example) does not change which post answers it.
- Tier 3, the first snapshot in order whose `state.claim` is set decides, by `claim_status(state)`: `"own"` is `Event(kind="crash", work_item=...)`, `"expired"` is kind `"expired"`, `"held"` is `Event(kind="idle", work_item=None)` with a `detail` that names the work item and the claiming instance.
- Tier 4, the first snapshot in order whose stage has a role (`definition.stages[stage].role is not None`) and which is not waiting: `state.attempts >= definition.attempts_cap` gives `Event(kind="ask", work_item=..., detail="attempts cap")`, else `Event(kind="run", work_item=...)`. A snapshot in a stage with no role that is not an approval is skipped; the only such stage a valid definition has is `done`.
- Nothing matched: `Event(kind="idle", work_item=None, remote_state=main_commit)`.
- `remote_state` of an event with a work item is that snapshot's `branch_commit`, else `main_commit`; of an event with none, `main_commit`.

Rules for `Watcher.evaluate`: it reads with `RemoteWorkItems(boundaries.git, boundaries.work_item_reader).read(definition)` and `boundaries.git.resolve("origin/main")`, and a `None` from that resolve raises `GitError` whose message names `origin/main`; its `lookup` calls `boundaries.hosting.get_pull_request(number)` and, only when that pull request is open, `boundaries.hosting.list_comments(number)`; its `claim_status` is `ClaimService(boundaries, instance, definition).status`.

Tests: `tests/domain/test_events.py`, `tests/domain/test_evaluation.py` (hand-built snapshots, the lookup and the claim status as plain functions), `tests/application/test_watcher.py` (a real bare remote through `human.push_file`, the fake hosting service wrapped in a test subclass that counts its calls by overriding every operation except `post_comment` (`tests/test_hosting_fake_search.py` refuses a test class that defines `post_comment`; posts are counted with `factory_posts`), `clock` for claims). The closed-model tests build the models through a variable typed `type[BaseModel]` and assign with `setattr`, the field's name in a variable.

## Acceptance criteria

1. With no snapshot `evaluate` returns `Event(kind="idle", work_item=None, remote_state=main_commit)` and never calls the lookup.
2. Two snapshots with one id give kind `"duplicate"` with `work_item` the first of them and a `detail` that names both paths, even when a work item is runnable or waiting, and the lookup is not called.
3. `evaluate` raises `ValueError` for a snapshot whose `document.state` is `None` and for one whose stage is not in the definition, each message naming the work item.
4. With two work items that wait (one `blocked`, one at an approval stage), the lookup is called once, with the lower id's pull request number, and never for the other.
5. A waiting work item without a pull request gives kind `"ask"` with detail `no pull request`, and the lookup is not called.
6. A lookup that raises `HostingServiceError` gives kind `"pull_request_lookup"` for the waiting work item, with `pull_request is None` and the error's text in `detail`.
7. A lookup that returns a merged pull request gives kind `"merged"`, and one that returns a closed pull request gives kind `"closed"`; both carry the waiting work item, `pull_request` set to the view, and `remote_state` equal to its `branch_commit`; the events `comment`, `hand_over` and `ask` made after a successful lookup carry the view in `pull_request` as well.
8. An open pull request with a comment by a human whose id is not in `comments_read` gives kind `"comment"` with the work item and the count in `detail`.
9. An open pull request whose only comments are the factory's, or whose human comments are all in `comments_read`, gives no `"comment"` event.
10. A work item at an approval stage whose `handed_over` differs from its stage, with an open pull request, gives kind `"hand_over"`, also when an unread human comment exists.
11. A work item at an approval stage whose `handed_over` equals its stage gives no `"hand_over"` event.
12. An open pull request, a work item with `blocked` set and no factory comment keyed to it gives kind `"ask"` with the work item.
13. A factory comment keyed with the work item, the kind equal to `blocked` and `n` equal to the number of the latest `question` record makes `question_posted` true and gives no `"ask"`, also when a `comment` record follows the question; a comment of the same kind whose `n` is another number does not; `question_posted` is false for a work item whose `blocked` is `None` and for one whose journal holds no `question` record, whatever the comments.
14. A waiting work item with an open pull request and nothing new gives `Event(kind="idle", work_item=None)` with the view in `pull_request` and the work item's id in `detail`, and holds back a runnable work item of any id.
15. With a claim on the first work item that has one, `claim_status` `"own"` gives kind `"crash"`, `"expired"` gives kind `"expired"`, and `"held"` gives `"idle"` whose `detail` names the work item and the claiming instance, with no `"run"` for another runnable work item; a work item with no claim is not asked about its claim status.
16. Without any signal, the first work item in id order whose stage has a role gives kind `"run"` with its snapshot and `remote_state` equal to its `branch_commit`; a work item at stage `done` (still in `in-progress/`) is skipped.
17. With `attempts_cap` 2, a runnable work item with `attempts == 1` gives `"run"` and one with `attempts == 2` gives kind `"ask"` with detail `attempts cap`.
18. `Event.key` is `run:F0001-S0001` for a work item event, `acceptance_due:F0001` for a feature event, and `idle:-` for neither.
19. `Watcher.evaluate` on a real remote with one started story without a branch returns kind `"run"` for it, with a state equal to `initial_state(<first stage>)` and `remote_state` equal to the head of `origin/main`.
20. `Watcher.evaluate` makes no hosting-service call when no work item waits, and for a waiting work item with an open pull request exactly one `get_pull_request` and one `list_comments`; for a merged one, one `get_pull_request` and no `list_comments`.
21. `Watcher.evaluate` decides the claim tier through `ClaimService`: a work item on its branch whose claim names the watcher's own instance gives `"crash"`; a claim of another instance older than its `lease_duration` gives `"expired"`; one younger gives `"idle"`.
22. `Watcher.evaluate` on a clone of an empty bare repository, where `origin/main` does not resolve, raises `GitError`.
23. `Event` refuses a `work_item` for the kinds `idle` and `acceptance_due`, a missing `work_item` for each of the other eleven kinds, a `feature` for any kind but `acceptance_due` and a missing `feature` for `acceptance_due`, each with `ValidationError`; every accepted pairing builds.
24. `Event`, `PullRequestObservation` and `EvaluationInput` refuse an unknown key and an assignment to a field; `Event` accepts `kind="idle"` and refuses `kind="other"`, accepts a `remote_state` of 40 lower-case hex characters and refuses 39 characters and 40 with an upper-case letter, all with `ValidationError`.
25. make check stays green.
26. docs: `docs/project-guide.md` lists the event kinds, the four tiers in their order and when each event is made, the rule that a waiting work item holds back new work, and that the evaluation validates every stage against the definition before it looks anything up; `docs/operator-guide.md` explains that an `idle` tick can mean a work item waiting for the human or a claim held by another instance.

## Demo

```bash
uv run python -c "
from factory.domain.evaluation import EvaluationInput, PullRequestObservation, evaluate
from factory.domain.hosting import PullRequestView
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState, initial_state
definition = PipelineDefinition(contract='1.0', stages={'intake': StageDefinition(role='intake', next=['approval']), 'approval': StageDefinition(approval=True, next=['done']), 'done': StageDefinition()}, roles={'intake': RoleDefinition(write_paths=['{work_item}'])})
def snapshot(number, state):
    work_item = 'F0001-S000' + str(number)
    return WorkItemSnapshot(id=work_item, path='factory/features/F0001-demo/in-progress/' + work_item + '-x.md', folder='in-progress', branch='work-item/' + work_item, branch_commit=None, document=WorkItemDocument(state=state, body='# T\n'))
calls = []
def lookup(number):
    calls.append(number)
    view = PullRequestView(number=number, branch='work-item/F0001-S0001', title='t', state='merged', draft=False, merge_commit='b' * 40, url='https://example.test/7')
    return PullRequestObservation(view=view, comments=[])
def facts(*snapshots):
    return EvaluationInput(definition=definition, snapshots=list(snapshots), main_commit='a' * 40)
waiting = snapshot(1, WorkItemState(stage='approval', pull_request=7, handed_over='approval'))
runnable = snapshot(2, initial_state('intake'))
print(evaluate(facts(waiting, runnable), lookup, lambda state: 'none').key, calls)
calls.clear()
print(evaluate(facts(runnable), lookup, lambda state: 'none').key, calls)
"
```
Expect: two lines. The first is `merged:F0001-S0001 [7]`: the waiting work item is looked up once (pull request 7) and its merge comes before the runnable one. The second is `run:F0001-S0002 []`: no work item waits, so the lookup is never called.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: 1. The Interface rule "`remote_state` of an event with a work item is that snapshot's `branch_commit`, else `main_commit`; of an event with none, `main_commit`" is tested only for `merged`, `closed` (criterion 7), `run` (16, 19) and the empty `idle` (1). No criterion checks it for the `idle` events of tier 2 (waiting work item, nothing new) and tier 3 (held claim), which carry no work item although a work item caused them, nor for `duplicate`, `crash`, `expired` or `ask`. The dispatcher counts errors per event and `remote_state` (F0006-S0003), so a wrong value there is silent. Two coders could pick `main_commit` or the waiting work item's `branch_commit` for those idles, and both would pass. Options: (a) add a criterion before the two closing ones: "the `idle` events of tier 2 and tier 3 have `remote_state` equal to `main_commit`; `duplicate`, `crash`, `expired` and `ask` have the `branch_commit` of their snapshot, and `main_commit` when it has none". This is what I would choose. (b) Drop the sentence from the Interface for those kinds.

   All other checks pass: the Interface names concrete modules and signatures, the tiers and validation order are covered by criteria 1 to 17 including each failing side, the Demo is runnable with a checkable `Expect:`, and the architecture and scope match `FEATURE.md`.
3. human (pull request comment, 2026-10-14): (a): add the criterion before the two closing ones, as you worded it: "the `idle` events of tier 2 and tier 3 have `remote_state` equal to `main_commit`; `duplicate`, `crash`, `expired` and `ask` have the `branch_commit` of their snapshot, and `main_commit` when it has none". The Interface sentence stays as it is.
