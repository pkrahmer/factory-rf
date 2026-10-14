---
stage: review
pr: 75
blocked: null
comments_seen: 2
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
24. `last_stage_change` returns `None` when the newest commit that touched the file deleted it.
25. `last_stage_change` returns `correction=False` when the newest commit changed the stage and left the journal the same length, also when the journal's last record (an older one) has kind `move_back`.
26. make check stays green.
27. docs: `docs/project-guide.md` explains the rule for stage changes made outside the pipeline (the last commit beyond `origin/main` on the branch, the opening commit and merge commits exempt, the `move_back` entry) and that the pull request's state is read first; `docs/operator-guide.md` says what the factory does when someone changes a stage by hand and that a merge by any method is not such a change.

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
2. intake: The format check passed. Two rules in the `## Interface` have no criterion for the side that returns the other result, so two coders could read them differently and both pass:

   1. `last_stage_change` returns `None` "when the file does not exist ... at `C`", where `C` is the newest commit. Criterion 11 covers a file that `C` added, which is missing at the parent. It does not cover a file that `C` deleted, which is missing at `C`. Proposed: add to criterion 11, or as a new criterion before the two closing ones, that a newest commit which deleted the work item's file gives `None`.

   2. `correction` is true only when `C`'s journal is longer than the parent's and its last record has kind `move_back`. Criterion 12 tests only an appended `move_back` record (true) and an appended record of another kind (false). Nothing tests the "longer" condition. Proposed: add a criterion that a commit which changes the stage and leaves the journal the same length gives `correction=False`, even when the last record of that journal has kind `move_back`. The journal would have to hold an older `move_back` record for this test.

   I would choose both additions as new criteria, placed before the `make check` and `docs:` criteria.

   Everything else holds up:
   - The Interface names concrete modules and signatures.
   - The Demo is runnable, and its `Expect:` line is checkable.
   - The architecture is respected: the rule is pure in `domain`, the reading is in `application`, and the watcher fills the input.
   - The scope matches `FEATURE.md`.
3. human (pull request comment, 2026-10-14): 1 and 2: add both as new criteria, as you worded them, before the `make check` and `docs:` criteria: a newest commit that deleted the work item's file gives `None`; a commit that changes the stage and leaves the journal the same length gives `correction=False`, also when the journal's last record (an older one) has kind `move_back`. The Interface stays as it is.
4. intake: accepted. Checked again with the human's answer (log entry 3); the format check passed.
   - Answer carried in (log entry 3): I added the two criteria exactly as the human approved. Criterion 24: a newest commit that deleted the file gives `None`. Criterion 25: a stage change that leaves the journal the same length gives `correction=False`, also when an older last record has kind `move_back`. Both go before the closing criteria, which are now 26 (`make check`) and 27 (`docs:`). The Interface and Assignment are unchanged, since the human said the Interface stays as it is.
   - Interface: it names concrete modules and signatures. Each rule of `is_legal_change`, `factory_moves`, `last_stage_change` and `evaluate` is stated precisely.
   - Criteria: each is testable by one test function. Every rule has a criterion for the failing side as well as the passing side: illegal and legal changes (1–5), the `None` cases (9–11, 24), `correction` true and false (12, 25), and `reject` skipped only for a merged pull request (16, 17).
   - Demo: it is runnable, and its `Expect:` line lists six checkable outputs.
   - Architecture: the pure rule is in `domain`, the git reading is in `application` through `Git.log` and `Git.is_ancestor`, and the watcher fills the input. The layers are respected.
   - Scope: the story is within the feature's "move rule" scope, and handling `reject` stays with F0007-S0006.
5. tester: Wrote the red tests for every acceptance criterion. Each one tests the Interface as specified.

   Criterion → test:
   - criterion 1: tests/domain/test_move_rule.py::test_every_move_a_next_list_names_is_legal (parametrized over every next pair of the definition, which mirrors `PIPELINE_YAML` and is built in Python so the domain test does not import an adapter)
   - criterion 2: tests/domain/test_move_rule.py::test_a_skipped_stage_is_illegal_and_the_same_stage_is_legal
   - criterion 3: tests/domain/test_move_rule.py::test_a_stage_the_definition_lacks_is_illegal
   - criterion 4: tests/domain/test_move_rule.py::test_done_is_legal_from_an_approval_stage_even_unlisted_and_from_no_other
   - criterion 5: tests/domain/test_move_rule.py::test_a_correction_is_legal_whatever_it_jumps (the `correction` default is checked in test_a_stage_change_is_no_correction_by_default)
   - criterion 6: tests/domain/test_move_rule.py::test_factory_moves_list_every_next_in_order_and_approval_to_done_once; the appended `(approval, done)` rule is in test_factory_moves_add_approval_to_done_after_the_next_lists
   - criterion 7: tests/domain/test_move_rule.py::test_every_factory_move_is_legal (the fixture definition, and one whose approval lists only `doing`)
   - criterion 8: tests/application/test_stage_changes.py::test_a_commit_that_changed_the_stage_is_the_last_stage_change, plus test_only_the_newest_commit_that_touched_the_file_counts
   - criterion 9: tests/application/test_stage_changes.py::test_a_commit_that_kept_the_stage_is_no_stage_change (journal, claim and body cases)
   - criterion 10: tests/application/test_stage_changes.py::test_a_merge_commit_is_no_stage_change. A second plain clone changes `stage` on a side branch, and the branch, which changed `pull_request`, merges it with `--no-ff`.
   - criterion 11: tests/application/test_stage_changes.py::test_a_snapshot_without_a_branch_has_no_stage_change, ::test_a_branch_whose_commits_beyond_main_left_the_file_alone_has_no_stage_change, ::test_a_file_the_newest_commit_added_has_no_stage_change, ::test_a_previous_version_that_cannot_be_parsed_has_no_stage_change
   - criterion 12: tests/application/test_stage_changes.py::test_a_stage_change_that_appends_a_move_back_is_a_correction
   - criterion 13: tests/application/test_stage_changes.py::test_the_opening_commit_of_a_started_story_is_no_stage_change and tests/application/test_watcher_move_rule.py::test_the_opening_commit_of_a_started_story_is_no_reject
   - criterion 14: tests/domain/test_evaluation_reject.py::test_the_first_illegal_change_in_snapshot_order_is_rejected_at_its_branch. `illegal_changes` is listed in reverse order, so the test proves the snapshot order decides; the detail is checked as the exact string from the Interface. Also test_no_illegal_change_is_no_reject.
   - criterion 15: tests/domain/test_evaluation_reject.py::test_reject_comes_before_every_later_event (comment, ask, hand_over, crash, expired, run, idle; each case also checks that without the change it gives that event) and ::test_a_duplicate_comes_before_reject
   - criterion 16: tests/domain/test_evaluation_reject.py::test_the_waiting_work_items_change_is_skipped_only_when_its_pull_request_is_merged and ::test_another_work_items_change_is_rejected_beside_a_merged_pull_request
   - criterion 17: tests/domain/test_evaluation_reject.py::test_a_failed_lookup_skips_no_illegal_change and ::test_no_lookup_when_no_work_item_waits. Every test in the file that looks up asserts `lookup.calls == [PULL_REQUEST]`.
   - criterion 18: tests/application/test_watcher_move_rule.py::test_a_hand_made_stage_change_the_definition_forbids_is_rejected
   - criterion 19: tests/application/test_watcher_move_rule.py::test_the_correction_commit_ends_the_reject
   - criterion 20: tests/application/test_watcher_move_rule.py::test_a_merge_by_any_method_is_merged_and_never_a_reject (merge, squash, rebase)
   - criterion 21: tests/application/test_watcher_move_rule.py::test_an_illegal_change_beside_a_merged_pull_request_is_merged. The merged case uses squash, so the illegal commit stays beyond `origin/main`.
   - criterion 22: tests/application/test_watcher_move_rule.py::test_every_factory_move_is_no_reject (parametrized over `factory_moves` of the parsed `PIPELINE_YAML`)
   - criterion 23: tests/domain/test_move_rule.py::test_move_rule_models_refuse_an_unknown_key, ::test_move_rule_models_refuse_an_assignment, ::test_a_from_stage_must_be_a_lower_case_name, ::test_an_illegal_change_needs_a_work_item_id. For `EvaluationInput`: tests/domain/test_evaluation_reject.py::test_evaluation_input_refuses_an_unknown_key_and_an_assignment, and the default is checked in ::test_evaluation_input_has_no_illegal_changes_by_default.
   - criterion 24: tests/application/test_stage_changes.py::test_a_file_the_newest_commit_deleted_has_no_stage_change
   - criterion 25: tests/application/test_stage_changes.py::test_a_stage_change_that_keeps_the_journals_length_is_no_correction
   - criteria 26 and 27: not tests; they are the factory's `make check` and the documenter's.

   Files created:
   - tests/domain/test_move_rule.py
   - tests/domain/test_evaluation_reject.py
   - tests/application/test_stage_changes.py
   - tests/application/test_watcher_move_rule.py

   `make test`: all 4 new files fail at collection because `factory.domain.move_rule` does not exist yet. `RemoteWorkItems.last_stage_change` and `EvaluationInput.illegal_changes` are missing too, but the tests do not reach them until that module exists. `make lint` is green. I did not run the type check, as this stage's skill says.

   No criterion needed interpreting.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
6. coder: Implemented the move rule and made `reject` wait for the pull request lookup. All of the tester's tests pass unchanged, and `make check` is green (coverage 99.41 %).

   What I built:
   - `src/factory/domain/move_rule.py`
     - `StageChange`, `FactoryMove` and `IllegalChange`: frozen, and they forbid unknown keys.
     - `is_legal_change`: true for a correction or an unchanged stage; otherwise `to_stage` must be in `from_stage`'s `next`, or be `done` from an approval stage. An unknown `from_stage` is false.
     - `factory_moves`: the `next` pairs in stage order, then each approval stage → `done`. Duplicates are removed with `dict.fromkeys`.
   - `src/factory/domain/evaluation.py`
     - `EvaluationInput.illegal_changes` is added, with default `[]`.
     - `evaluate` now finds the first waiting pair. It makes the lookup at most once (`_looked_up` returns the observation, the `HostingServiceError`, or `None` when there is no pull request).
     - `_reject` then runs, then `_human_signal` from the same lookup result, then tiers 3 and 4.
     - `_reject` goes through the snapshots in order. It skips the waiting snapshot only when the lookup returned a merged pull request. A failed lookup skips nothing.
   - `src/factory/application/work_items.py`: `RemoteWorkItems.last_stage_change`.
     - It reads `Git.log(origin/<branch>, since=origin/main, path=...)`, newest first. It returns `None` when there is no remote branch, no commit, a merge commit, or an opening commit (the parent is an ancestor of `origin/main`).
     - It also returns `None` when the file is missing on either side, the parent cannot be parsed, or the stage is unchanged.
     - `correction` means the journal grew and its last record has kind `move_back`.
   - `src/factory/application/watcher.py`: `_illegal_changes` fills `illegal_changes` from `last_stage_change` and `is_legal_change`, in snapshot order.

   Main decision: I split the old `_signal_of` into a lookup step and a step that interprets the result, so `reject` and the human signal share one lookup. The rejected alternative was to keep the lookup inside `_human_signal` and pass a callback that remembers its result. That hides the "at most once" rule in state; an explicit value is simpler to read.

   Refactor: commit 0dc76f0 adds the `_Pair` alias for the repeated waiting-pair tuple type. Nothing else needed changing.

   Noticed but did not touch:
   - `last_stage_change` treats `snapshot.branch_commit is None` as "no branch", because a snapshot always carries a branch name.
   - A work item's `illegal_changes` entry is matched to its snapshot by id. Duplicate ids are already returned as `duplicate` before `reject`.
   - Docs criterion 27 is the documenter's.

   `make check`: check: green
