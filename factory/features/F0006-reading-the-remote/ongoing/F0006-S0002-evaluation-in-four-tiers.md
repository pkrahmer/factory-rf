---
stage: doing
pr: 72
blocked: null
comments_seen: 2
round: 2
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
25. The `idle` events of tier 2 and tier 3 have `remote_state` equal to `main_commit`; `duplicate`, `crash`, `expired` and `ask` have the `branch_commit` of their snapshot, and `main_commit` when it has none.
26. make check stays green.
27. docs: `docs/project-guide.md` lists the event kinds, the four tiers in their order and when each event is made, the rule that a waiting work item holds back new work, and that the evaluation validates every stage against the definition before it looks anything up; `docs/operator-guide.md` explains that an `idle` tick can mean a work item waiting for the human or a claim held by another instance.

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
4. intake: accepted. Carried in from log entry 3 (the human's answer (a) to the question in entry 2): I added new criterion 25, worded as the human gave it, before the two closing ones. The closing ones are now 26 (`make check`) and 27 (`docs:`). I changed nothing else, and the Assignment's meaning is the same.
   - Interface: it names concrete modules and signatures (`events.py`, `evaluation.py`, `watcher.py`). The rules cover tier order, validation order and the `Event` shape. Every comment-stated behaviour, including `remote_state`, now has a criterion.
   - Criteria: each is testable by one test function. Each rule has its failing side: duplicate ids (2), no state or unknown stage (3), no pull request (5), lookup failure (6), the factory's own or read comments giving no `comment` (9), `handed_over` equal giving no `hand_over` (11), `question_posted` false cases (13), attempts below the cap (17), and the `Event` pairing and field refusals (23, 24). Origin/main not resolving is covered by 22.
   - Demo: it is runnable. Its `Expect:` line is checkable: `merged:F0001-S0001 [7]` and `run:F0001-S0002 []`.
   - Architecture: pure rules and DTOs are in `factory.domain`, and the `Watcher` is in `factory.application` using `Boundaries`. This fits the layer rules.
   - Scope: the story is within the feature's scope. The `reject` event, the handlers and the dispatcher stay with later stories and features.
5. tester: I wrote red tests for criteria 1 to 25. Criterion 26 is the factory's `make check` gate, and criterion 27 belongs to the documenter.

   Which test covers each criterion:
   - criterion 1: tests/domain/test_evaluation.py::test_no_work_items_is_idle_at_main_without_a_lookup
   - criterion 2: tests/domain/test_evaluation.py::test_two_work_items_with_one_id_are_a_duplicate_before_anything_else. Parametrized: the duplicates are runnable or waiting, with or without a waiting work item before them.
   - criterion 3: tests/domain/test_evaluation.py::test_a_work_item_without_state_or_in_an_unknown_stage_is_a_value_error
   - criterion 4: tests/domain/test_evaluation.py::test_only_the_first_waiting_work_item_is_looked_up_once. Parametrized: blocked first, or approval first.
   - criterion 5: tests/domain/test_evaluation.py::test_a_waiting_work_item_without_a_pull_request_asks_without_a_lookup
   - criterion 6: tests/domain/test_evaluation.py::test_a_failed_lookup_is_a_pull_request_lookup_event
   - criterion 7: tests/domain/test_evaluation.py::test_a_merged_or_closed_pull_request_is_its_own_event and ::test_events_after_a_successful_lookup_carry_the_view (covers comment, hand_over and ask)
   - criterion 8: tests/domain/test_evaluation.py::test_unread_human_comments_are_a_comment_event_with_their_count
   - criterion 9: tests/domain/test_evaluation.py::test_factory_and_read_comments_are_no_comment_event
   - criterion 10: tests/domain/test_evaluation.py::test_an_approval_not_handed_over_is_a_hand_over_before_comments
   - criterion 11: tests/domain/test_evaluation.py::test_an_approval_handed_over_is_no_hand_over
   - criterion 12: tests/domain/test_evaluation.py::test_a_blocked_work_item_whose_question_is_not_posted_asks
   - criterion 13: tests/domain/test_evaluation.py::test_a_post_keyed_to_the_latest_question_is_the_posted_question, ::test_question_posted_is_false_without_a_post_for_the_latest_question (cases: another number, another kind, not blocked, no question record) and ::test_a_post_for_an_earlier_question_still_asks
   - criterion 14: tests/domain/test_evaluation.py::test_a_waiting_work_item_with_nothing_new_is_idle_and_holds_back_new_work. Parametrized: the runnable work item has the lower id or the higher one.
   - criterion 15: tests/domain/test_evaluation.py::test_a_claim_of_this_or_an_expired_instance_comes_before_new_work and ::test_a_claim_held_by_another_instance_is_idle_and_holds_back_new_work. Both also assert that claim status is asked only for the first claimed work item.
   - criterion 16: tests/domain/test_evaluation.py::test_the_first_work_item_with_a_role_runs_and_done_is_skipped
   - criterion 17: tests/domain/test_evaluation.py::test_a_work_item_at_the_attempts_cap_asks_instead_of_running (attempts 1 and 2)
   - criterion 18: tests/domain/test_events.py::test_key_names_the_kind_and_the_work_item_or_feature
   - criterion 19: tests/application/test_watcher.py::test_a_started_story_without_a_branch_runs_at_the_first_stage
   - criterion 20: tests/application/test_watcher.py::test_no_waiting_work_item_makes_no_hosting_call and ::test_a_waiting_work_item_is_looked_up_once_and_its_comments_only_when_open
   - criterion 21: tests/application/test_watcher.py::test_the_claim_tier_is_decided_by_the_claim_service. Cases: own claim; other instance at 59, 60 and 61 minutes against a lease of 60.
   - criterion 22: tests/application/test_watcher.py::test_a_remote_without_main_is_a_git_error
   - criterion 23: tests/domain/test_events.py::test_idle_and_acceptance_due_refuse_a_work_item, ::test_every_other_kind_refuses_a_missing_work_item, ::test_a_feature_is_refused_for_every_kind_but_acceptance_due, ::test_acceptance_due_refuses_a_missing_feature, ::test_every_accepted_pairing_builds and ::test_the_kinds_are_the_thirteen_named
   - criterion 24: tests/domain/test_events.py::test_event_refuses_an_unknown_key, ::test_event_refuses_an_assignment, ::test_event_accepts_only_a_known_kind and ::test_event_accepts_only_a_full_lower_case_commit_id; tests/domain/test_evaluation.py::test_closed_models_refuse_an_unknown_key and ::test_closed_models_refuse_an_assignment
   - criterion 25: tests/domain/test_evaluation.py::test_idle_events_of_a_work_item_are_at_main and ::test_work_item_events_are_at_their_branch_else_at_main. The second covers duplicate, crash, expired and both kinds of ask, each with and without a branch commit.

   Files created: tests/domain/test_events.py, tests/domain/test_evaluation.py and tests/application/test_watcher.py.

   `make test` stops with 3 collection errors because the modules under test don't exist yet. They are factory.domain.events, factory.domain.evaluation and factory.application.watcher. `make lint` passes.

   Notes for the coder:
   - In the Watcher tests, the test calls `boundaries.git.fetch()` before `Watcher.evaluate`. The Interface does not say whether the Watcher fetches, so the tests work either way.
   - Hosting calls are counted by `_CountingHosting`, a subclass of FakeHostingService that overrides every operation except `post_comment`.
   - Branch states are written with `FrontmatterWorkItemWriter().render` and pushed with `human.push_file`.
   - I did not run the type check, as this stage says. `make check` covers it once the modules exist.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
6. coder: I implemented the four-tier evaluation and the watcher. `make check` is green, and all the tester's tests for criteria 1 to 25 pass. Commits: 2bb4467 (feat) and 7e09ef2 (refactor).

   What I built:
   - `src/factory/domain/events.py` holds `EventKind` and `Event`. Frozen with extra keys forbidden, it has one `model_validator` that ties `work_item` and `feature` to the kind, and `key`.
   - `src/factory/domain/evaluation.py` holds `PullRequestObservation`, `EvaluationInput`, `PullRequestLookup`, `ClaimStatusOf`, `waiting`, `question_posted` and `evaluate`. `evaluate` first checks for duplicates (tier 1). It then validates every snapshot's state and stage before any definition lookup. Then it chains three private tier functions with `or`: `_human_signal`, `_agent_at_work` and `_new_work`. Each returns `Event | None`, and the empty `idle` at `main_commit` is the fallback. `_event` builds every work-item event, so `remote_state` is the `branch_commit`, else `main_commit`, in one place.
   - `src/factory/application/watcher.py` holds `Watcher`. It resolves `origin/main` first: a `None` raises `GitError("resolve origin/main", None, "origin/main does not resolve")`. It then reads through `RemoteWorkItems` and passes `ClaimService(...).status` as the claim status. Its lookup calls `get_pull_request` and calls `list_comments` only for an open pull request. The watcher does not fetch; the caller fetches, as the tests do.

   Main design decision: the tiers are three functions that each return `Event | None`, chained with `or`, so the order of the chain is the tier order. I rejected a loop over a tuple of tier functions, because it forced one signature on all of them and left unused parameters.

   Small choices the Interface leaves open:
   - If `claim_status` returns `"none"` for a set claim, which cannot happen with `claim_status` from `lease`, tier 3 falls through to tier 4.
   - The detail of a tier-2 `idle` is `"<id> waits for the human"`. The detail of a held-claim `idle` is `"<id> is held by <instance>"`.

   Refactor: I renamed `_open_signal` to `_signal_of_observation`, because it also handles merged and closed pull requests. I also moved the `_Pairs` alias up beside the other aliases. Nothing else needed changing.

   Noticed but not touched: the docs for criterion 27 belong to the documenter.

   `make check`: check: green
7. reviewer: one finding, in group 1 (acceptance criteria). I read the full diff of `src/` and `tests/` against the Interface and criteria 1 to 25. Criteria 1 to 21 and 23 to 25 each have a test that checks what the criterion says, including the refused sides: 39 characters and an upper-case letter for `remote_state`, the lease at 59/60/61 minutes, attempts 1 and 2, every refused kind/subject pairing, and a no-claim item never being asked for its claim status. The coder's entry 6 reports `make check` green.

   1. `tests/application/test_watcher.py::test_a_remote_without_main_is_a_git_error`: the Interface says "a `None` from that resolve raises `GitError` whose message names `origin/main`". The test only checks `pytest.raises(GitError)`. Two problems follow:
      - The message rule has no test.
      - The test cannot tell the resolve check from some other `GitError` raised while reading an empty clone. A Watcher that read the work items before resolving, and let some other git failure surface, would also pass.

      Fix: `pytest.raises(GitError, match="origin/main")`. This is a test change, so per R9 the coder hands it to the tester (`tests`) with exactly this change. The code in `src/factory/application/watcher.py` (`_main_commit`) already raises `GitError("resolve origin/main", None, "origin/main does not resolve")`, which matches, so no source change is needed.

   Rejected as findings:
   - `question_posted` with a non-factory comment that carries a matching key: `PullRequestComment.from_body` derives both `by_factory` and `key` from the marker, so that case cannot come from the hosting service.
   - The `state.claim is not None` guard in `evaluation.py` `_agent_at_work`: it only narrows the type for mypy.
   - A `"none"` status for a set claim falling through to tier 4: the Interface leaves it open, `lease.claim_status` cannot return it, and entry 6 records it.

   I did not go on to groups 2 to 5, because the checklist stops at the first failing group.
8. coder: Round 1. The reviewer's only finding (entry 7) asks for a change to a test. Under R9 the coder cannot make that change, so I am sending the ticket to the tester.

   Test change requested: in `tests/application/test_watcher.py::test_a_remote_without_main_is_a_git_error`, change `pytest.raises(GitError)` to `pytest.raises(GitError, match="origin/main")`. Change nothing else.

   No source change is needed. `src/factory/application/watcher.py:39-41` already raises `GitError(f"resolve {_MAIN_REF}", None, f"{_MAIN_REF} does not resolve")`. I checked that its `str()` is `resolve origin/main failed (no exit status): origin/main does not resolve`, which the new `match` accepts. I made no commits this round.
9. tester: Round 1, the test change from entry 8, which comes from the reviewer's finding in entry 7. In `tests/application/test_watcher.py::test_a_remote_without_main_is_a_git_error` I changed `pytest.raises(GitError)` to `pytest.raises(GitError, match="origin/main")` and touched nothing else.

   Why: the Interface says the `GitError` raised when `origin/main` resolves to `None` must name `origin/main`. Before the change, the test only checked the exception type. It could not tell the resolve check apart from some other git failure while reading an empty clone.

   `make test`: test: green (total coverage 99.38%).

   `make lint`: lint: green
   `make test`: test: green
10. coder: Round 1. Entry 7 had one finding, and it was about a test. Entry 9 made that change: `tests/application/test_watcher.py::test_a_remote_without_main_is_a_git_error` now uses `pytest.raises(GitError, match="origin/main")`. The finding needed no source change, and I made none: `src/factory/application/watcher.py` already raises a `GitError` that names `origin/main` (checked in entry 8). No commits this round, and nothing to refactor. Nothing else is open. Criterion 27 (docs) belongs to the documenter.

    `make check`: check: green (coverage 99.38%).

    `make check`: check: green
11. reviewer: Round 1. One finding, in group 1 (acceptance criteria).

    I read the full diff of `src/` and `tests/` against the Interface and criteria 1 to 25. Entry 9 fixed the earlier finding from entry 7: `test_a_remote_without_main_is_a_git_error` now matches `origin/main`. Entry 10 reports `make check` green.

    Criteria 1 to 19 and 21 to 25 each have a test that checks what the criterion says, including the refused sides:
    - the Event pairings and the 39-character and upper-case `remote_state`
    - attempts 1 and 2, and leases of 59, 60 and 61 minutes
    - an unknown stage and a missing state, each named in the message
    - a later question that outdates an earlier post
    - the idles of tier 2 and tier 3 at `main_commit`

    1. `tests/application/test_watcher.py::test_a_waiting_work_item_is_looked_up_once_and_its_comments_only_when_open`:
       - The Interface says hosting calls are counted by overriding every operation except `post_comment`, and that "posts are counted with `factory_posts`". The test never checks `factory_posts`. A Watcher that posted a comment while looking up a waiting work item would still pass, so criterion 20's "exactly one `get_pull_request` and one `list_comments`" is not fully tested.
       - In the no-waiting test there is no pull request, so a post would already fail there.
       - Fix: add `assert hosting.factory_posts(number) == []` after the `calls` assertion. This is a test change, so the coder hands it to the tester (`tests`) with exactly this change. No source change is expected: `src/factory/application/watcher.py` makes no post.

    Rejected as findings:
    - `src/factory/domain/evaluation.py` `_duplicate` uses identity (`first is not snapshot`), so a list that holds the same snapshot object twice would not count as a duplicate. The only real input is `RemoteWorkItems.read`, which builds one snapshot per path, so this cannot happen.
    - In `_agent_at_work`, the `state.claim is not None` part of the `"held"` branch only narrows the type for mypy.
    - The Watcher does not fetch, and the caller does. The Interface leaves this open, entry 6 records it, and F0006-S0004 decides the tick.

    I did not go on to groups 2 to 5, because the checklist stops at the first failing group. Nothing in them stood out while I read.
