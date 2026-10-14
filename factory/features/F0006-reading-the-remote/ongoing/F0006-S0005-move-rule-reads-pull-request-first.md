---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The move rule reads the pull request first

## Assignment (as of log entry 1)

Build the rule that notices a stage change nobody was allowed to make, and make it judge only after the pull request's state is read. The watcher takes, for each work item with a remote branch, the last commit beyond `origin/main` that touched the work item's file on that branch, compares the stage before and after, and calls the change illegal when the pipeline definition's `next` does not allow it. A merge commit, a first commit, the opening commit (whose parent is the text on `origin/main`), an unreadable previous version and the factory's own correction (marked in the journal by the kind `move_back`, not by a commit message) are never a change. The evaluation then makes the one pull request lookup before it decides on `reject`, and a work item whose pull request is merged is not rejected, so a merge by any method (merge commit, squash, rebase) is never misread as an illegal stage change. Every stage change the factory makes itself is derived from the pipeline definition and is legal under the rule, which a test walks. That walk proves the factory's own moves legal only because the stage protocol takes its moves from the same `next` lists (F0005-S0006 does through `next`) and `factory_moves` is derived from them; a handler of F0007 that moves a work item must take its target from the definition too. Covers ST2.3 and ST2.4; keeps kept thing 5 (the pipeline definition decides which moves are legal). Builds on `evaluate` (F0006-S0002), `RemoteWorkItems` (F0006-S0001) and `Git.log` (F0001-S0011). Handling a `reject` event (moving the stage back) is F0007-S0006.

## Interface

`src/factory/domain/move_rule.py`

```python
class StageChange(BaseModel):
    from_stage: Name
    to_stage: Name
    correction: bool = False              # the same commit appended a journal entry of kind "move_back"

class FactoryMove(BaseModel):             # not StageMove: that name is F0005-S0006's decision
    from_stage: Name
    to_stage: Name

class IllegalChange(BaseModel):
    work_item: WorkItemId
    change: StageChange

def is_legal_change(definition: PipelineDefinition, change: StageChange) -> bool: ...
def factory_moves(definition: PipelineDefinition) -> list[FactoryMove]: ...
```

Every model here is frozen and forbids unknown keys.

`src/factory/domain/evaluation.py` (changed)

```python
class EvaluationInput(BaseModel):
    definition: PipelineDefinition
    snapshots: list[WorkItemSnapshot]
    main_commit: CommitId
    illegal_changes: list[IllegalChange] = []     # added; the watcher fills it

def evaluate(facts: EvaluationInput, lookup: PullRequestLookup, claim_status: ClaimStatusOf) -> Event: ...
    # unchanged signature; the order of its steps changes as described below
```

`src/factory/application/work_items.py` (added to `RemoteWorkItems`)

```python
    def last_stage_change(self, snapshot: WorkItemSnapshot) -> StageChange | None: ...
```

`src/factory/application/watcher.py` (changed): `Watcher.evaluate` fills `illegal_changes`.

Rules for `is_legal_change(definition, change)`: it is true when any of these holds, else false:

- `change.correction` is true;
- `from_stage == to_stage`;
- `from_stage` is a stage of the definition and `to_stage` is in that stage's `next`;
- `to_stage == DONE_STAGE` and `from_stage` is a stage of the definition with `approval` true (the human's merge accepts, so the factory's archive is legal even when that stage's `next` does not list `done`).

Rules for `factory_moves(definition)`: first, in the definition's stage order, a `FactoryMove` for every name in every stage's `next`, in that order; then, for every stage with `approval` true, `FactoryMove(stage, DONE_STAGE)` unless it is already listed. No pair is listed twice.

Rules for `last_stage_change(snapshot)`:

- It reads `Git.log("origin/" + snapshot.branch, since="origin/main", path=snapshot.path)`, so that only commits not reachable from `origin/main` are considered, and takes the newest commit `C`. It returns `None` when the snapshot has no branch, when that log is empty, when `C` is a merge commit (more than one parent), when `C`'s parent is reachable from `origin/main` (`Git.is_ancestor(parent, "origin/main")`: `C` is the opening commit, whose parent is the text the human started), when the file does not exist at `C`'s parent or at `C`, or when the parent's text cannot be read by `WorkItemReader.parse`.
- Otherwise it parses the file at the parent and at `C`. Equal stages give `None`. Different stages give `StageChange(from_stage=<parent's stage>, to_stage=<C's stage>, correction=<C's journal is longer than the parent's and its last record has kind "move_back">)`.

Rules for `evaluate`, changed; the other rules of F0006-S0002 stay:

- The order is: duplicates, validation, then the lookup of the first waiting work item `W` (made at most once, exactly when F0006-S0002 made it), then `reject`, then the rest of tier 2, tier 3, tier 4, idle.
- `reject`: the first `IllegalChange` in the order of `snapshots` (the snapshot with its work item's id) is returned as `Event(kind="reject", work_item=<snapshot>, detail=f"stage changed from {from} to {to}, which the pipeline definition does not allow")` with `remote_state` the snapshot's `branch_commit`, unless that snapshot is `W` and the lookup returned a merged pull request; such a change is skipped and the next illegal change, if any, is considered. A lookup that failed does not skip anything.
- `Watcher.evaluate` sets `illegal_changes` to `IllegalChange(work_item=<id>, change=<c>)` for each snapshot in order whose `last_stage_change` is a `StageChange` `c` with `is_legal_change(definition, c)` false.

Tests: `tests/domain/test_move_rule.py`, `tests/domain/test_evaluation_reject.py`, `tests/application/test_stage_changes.py` (`last_stage_change` against a real remote through `human.push_file`, with texts made by `FrontmatterWorkItemWriter`), `tests/application/test_watcher_move_rule.py` (the watcher with the fake hosting service; merges by `human.merge(branch, method)` followed by `hosting.merge_by_human`). The closed-model tests build the models through a variable typed `type[BaseModel]` and assign with `setattr`, the field's name in a variable.

## Acceptance criteria

1. `is_legal_change` is true for every pair `(stage, name in stage.next)` of the fixture's pipeline definition.
2. `is_legal_change` is false for `tests` to `review` and for `review` to `smoke-test` (a stage skipped), and true for `tests` to `tests`.
3. `is_legal_change` is false when `from_stage` or `to_stage` is not a stage of the definition.
4. `is_legal_change(approval, done)` is true for a definition whose approval stage does not list `done` in `next`; `is_legal_change(review, done)` is false when `review.next` does not list `done`.
5. `is_legal_change` is true for a jump the definition forbids when `correction` is true.
6. `factory_moves` of the fixture's definition lists every `(stage, name)` of every `next` in the definition's order, lists `(approval, done)` once, and lists no pair twice.
7. ST2.4: every move of `factory_moves` is legal under `is_legal_change`, for the fixture's definition and for one whose approval stage lists only `doing` in `next`.
8. `last_stage_change` returns `StageChange(from_stage=<before>, to_stage=<after>, correction=False)` when the newest commit beyond `origin/main` that touched the work item's file on its branch changed the stage.
9. `last_stage_change` returns `None` when the newest commit that touched the file changed only the journal, the claim or the body, and the stage is the same.
10. `last_stage_change` returns `None` when the newest commit that touched the file is a merge commit whose stage differs from its first parent's (two clones edit different keys of the front matter, one of them `stage`, and the branch merges the other).
11. `last_stage_change` returns `None` for a snapshot without a branch, for a branch with no commit beyond `origin/main` that touched the file, for a file whose newest commit added it, and for a file whose previous version cannot be parsed.
12. `last_stage_change` returns `correction=True` when the newest commit changed the stage and appended a journal record of kind `move_back`, and `correction=False` when it appended a record of another kind.
13. ST6.1: a started story whose file on `origin/main` says `stage: review` and whose branch holds only the opening commit, at the first stage, gives `last_stage_change` `None`, and `Watcher.evaluate` gives no `reject` for it.
14. `evaluate` returns kind `reject` for the first illegal change in the order of the snapshots, with the work item, the `remote_state` of its branch head and a `detail` that names both stages.
15. `evaluate` returns `reject` instead of `comment`, `ask`, `hand_over`, `crash`, `expired`, `run` and `idle`, and returns `duplicate` instead of `reject`.
16. `evaluate` skips the illegal change of the waiting work item exactly when the lookup returned a merged pull request: with a merged pull request it returns `merged`; with an open one it returns `reject`; an illegal change of another work item still gives `reject`.
17. When the lookup raises `HostingServiceError`, `evaluate` still returns `reject` for an illegal change; the lookup is called at most once in every case, and not at all when no work item waits.
18. `Watcher.evaluate` returns `reject` for a work item whose branch holds a hand-made stage change that its pipeline definition does not allow, with the pull request open.
19. After the correction commit (stage moved back and a `move_back` entry appended), `Watcher.evaluate` no longer returns `reject` for that work item.
20. ST2.3: a work item at the approval stage whose pull request the human merged with the merge method `merge`, with `squash` and with `rebase` gives kind `merged` and never `reject`.
21. A work item whose branch holds an illegal stage change and whose pull request is merged gives kind `merged`, not `reject`; the same change with an open pull request gives `reject`.
22. ST2.4 end to end: for each move of `factory_moves` of the fixture's definition, a branch whose newest commit makes exactly that move (written with `FrontmatterWorkItemWriter`) gives no `reject` from `Watcher.evaluate`.
23. `StageChange`, `FactoryMove`, `IllegalChange` and `EvaluationInput` refuse an unknown key and an assignment to a field; a `from_stage` of `Tests` (an upper-case letter) raises `ValidationError` and `tests` is accepted; an `IllegalChange` with `work_item` `F001-S0001` raises `ValidationError` and `F0001-S0001` is accepted.
24. make check stays green.
25. docs: `docs/project-guide.md` explains the rule for stage changes made outside the pipeline (the last commit beyond `origin/main` on the branch, the opening commit and merge commits exempt, the `move_back` entry) and that the pull request's state is read first; `docs/operator-guide.md` says what the factory does when someone changes a stage by hand and that a merge by any method is not such a change.

## Demo

```bash
uv run python -c "
from factory.domain.move_rule import StageChange, factory_moves, is_legal_change
from factory.domain.pipeline_definition import PipelineDefinition, RoleDefinition, StageDefinition
definition = PipelineDefinition(contract='1.0', stages={'work': StageDefinition(role='worker', next=['approval']), 'approval': StageDefinition(approval=True, next=['work']), 'done': StageDefinition()}, roles={'worker': RoleDefinition(write_paths=['{work_item}'])})
for a, b in (('work', 'approval'), ('work', 'done'), ('approval', 'done'), ('approval', 'approval')):
    print(a, b, is_legal_change(definition, StageChange(from_stage=a, to_stage=b)))
print(is_legal_change(definition, StageChange(from_stage='work', to_stage='done', correction=True)))
print([(m.from_stage, m.to_stage) for m in factory_moves(definition)])
"
```
Expect: six lines: `work approval True`, `work done False`, `approval done True` (the merge archives from an approval although `next` lists only `work`), `approval approval True`, `True` (a correction is legal), and `[('work', 'approval'), ('approval', 'work'), ('approval', 'done')]`.

## Log (append only)

1. 2026-10-12 human: created.
