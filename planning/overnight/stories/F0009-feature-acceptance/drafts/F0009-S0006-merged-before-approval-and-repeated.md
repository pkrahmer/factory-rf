# Merged before its approval, and repeated acceptances

## Assignment (as of log entry 1)

Make two edge cases of the acceptance end without a loop. First, the human may merge an acceptance's pull request before it reached its approval (while the reviewer works, or waits with a question): the merge is the human's decision, so the acceptance is booked `accepted` like any other merge, and its journal gets an entry that says it was merged before approval (R31). In v1 this alternated forever between `merged` and `reject`; here the report moves to `done/` as a new file, so the move rule has no stage change to judge, the next ticks find nothing for it, and the proposed stories the merge brought make the feature `incomplete`, not due. Second, a feature is accepted again when another story has been archived since: the repeated acceptance is a new work item (`F0001-A0002`) with its own report and cost records, the earlier report stays as it was, the repeated acceptance does not trip `reject`, and once it is recorded the feature is not due again. This story also builds the dispatcher wiring for the acceptance (the due, hand-over, merged and closed handlers) and proves the stories before it together with ticks over a real local remote. Covers ST2.1, ST2.2 and R31 (and the repeated side of GH4.4); keeps kept thing 19 (due again whenever the set of archived stories changes) and kept thing 2 (the human's merge decides). Most criteria walk what the earlier stories built: they are the proof of ST2.1 and ST2.2, and a test may pass at once where an earlier story already does the work.

## Interface

`src/factory/domain/acceptance.py` (grown)

```python
def is_before_approval(definition: PipelineDefinition, stage: str) -> bool: ...
def book_merge(document: WorkItemDocument, cost_line: str, *, before_approval: bool = False) -> WorkItemDocument: ...
```

`src/factory/application/acceptance.py` (grown): `AcceptanceMerged.handle` passes `before_approval`.

`src/factory/entry/wiring.py` (grown): the dispatcher's handlers.

Rules:

- `is_before_approval(definition, stage)` is true exactly when `stage` is a stage of the definition that lies before the first stage with `approval=True` in the definition's order (`PipelineDefinition.position`); the approval stage itself and every later stage, `done` included, give false. An unknown stage raises `KeyError`; a definition with no approval stage raises `ValueError`.
- `book_merge(document, cost_line, before_approval=True)` is the S0005 booking with the entry text `done (pull request merged before approval); cost: <cost_line>`; with `before_approval=False` (the default) the text is the one without `before approval`.
- `AcceptanceMerged.handle` reads the state of the merged report on the main branch and books it with `before_approval=is_before_approval(definition, <the report's stage>)`; a `blocked` question is cleared by the booking.
- The dispatcher that `factory.entry.wiring` builds has `AcceptanceDueHandler` for `acceptance_due`, and for `hand_over`, `merged` and `closed` a `SplitByWorkItemKind` of the story's handler and `AcceptanceHandOver`, `AcceptanceMerged` and `AcceptanceClosed` respectively.
- No new rule for repeated acceptances: each acceptance is a work item of its own (`next_acceptance_id`), and `acceptance_status` judges the set of archived stories against the recorded reports.

Tests: `tests/domain/test_acceptance_before_approval.py`, `tests/application/test_acceptance_merged_before_approval.py`, `tests/application/test_acceptance_repeated.py`; the fixtures of the earlier stories; ticks are run through `factory.application.tick` (F0006-S0004) with the dispatcher that `factory.entry.wiring` builds, as F0006's tests do; the human merges with `human.merge(branch, method)` and `hosting.merge_by_human`.

## Acceptance criteria

1. With the fixture's pipeline definition, `is_before_approval` is true for the stage `acceptance` and false for `approval` and for `done`.
2. `is_before_approval` raises `KeyError` for a stage the definition does not have, and `ValueError` for a definition without an approval stage.
3. `book_merge(document, "2 runs", before_approval=True)` appends one record (speaker `factory`, kind `done`) whose visible text is `done (pull request merged before approval); cost: 2 runs`, and otherwise books as `book_merge` does.
4. R31: after the human merged the pull request of an acceptance that is at the stage `acceptance`, `AcceptanceMerged.handle` books it `accepted` in `done/` with the entry `done (pull request merged before approval); cost: <its own cost line>`.
5. An acceptance merged at the stage `acceptance` with `blocked == "question"` is booked the same way, and the booked state has `blocked` `None`.
6. An acceptance merged at the stage `approval`, before its hand-over, is booked with the entry that does not say `before approval`.
7. The merge methods `merge`, `squash` and `rebase` each give the same booked result for an acceptance merged before its approval: the report in `done/`, outcome `accepted`, the same entry text.
8. ST2.1: one tick after the merge (`hosting.merge_by_human` and `human.merge`) handles the `merged` event of the acceptance and leaves it booked in `done/`; the evaluation before that tick yields the `merged` event for the acceptance and not a `reject` event.
9. ST2.1: a second and a third tick after that yield `idle`, make no commit on `origin/main` and post nothing (`hosting.factory_posts` is unchanged).
10. No tick of the walk in criteria 8 and 9 yields a `reject` event.
11. After the merge of criterion 8 brought the proposed stories into the feature's backlog, the feature's status is `incomplete`, `due_events()` is empty, and no tick opens a new acceptance.
12. ST2.2: with an acceptance `F0001-A0001` accepted for the stories `F0001-S0001` and `F0001-S0002`, a story `F0001-S0003` that was archived afterwards makes the feature `due` again, and one tick opens `F0001-A0002`: the branch `work-item/F0001-A0002` and its report at `in-progress/F0001-A0002-acceptance.md` exist on the remote.
13. ST2.2: the report `F0001-A0001-acceptance.md` in `done/` is byte for byte what it was before the repeated acceptance opened, and its cost records file too.
14. ST2.2: after the repeated acceptance `F0001-A0002` was merged and its tick handled, the feature's status is `accepted`, it is not due, and a further tick yields `idle`; while the merge is not yet recorded the status is `merged_unrecorded` and `due_events()` is empty.
15. After an acceptance was refused (closed with a comment), the feature is `refused` and not due; once another story is archived it is `due` again and the next tick opens `F0001-A0002`.
16. GH4.4: the cost lines of `F0001-A0001` and `F0001-A0002`, each with records of its own, count only their own records, also in the entries `done (...); cost: ...` of both reports.
17. The dispatcher that `factory.entry.wiring` builds holds a handler for `acceptance_due`, `hand_over`, `merged` and `closed`, and a `hand_over`, `merged` or `closed` event of a story still reaches the story's handler.
18. `make check` stays green.
19. docs: `docs/operator-guide.md` explains what happens when an acceptance is merged before its approval (accepted, with an entry saying so) and when a feature is accepted again (a new acceptance, an earlier report unchanged); `docs/decisions.md` records why each acceptance is a work item with its own report, so that neither case loops.

## Demo

```bash
uv run python -c "
from factory.domain.acceptance import AcceptanceState, FeatureFiles, ReportFacts, acceptance_status, book_merge, is_before_approval, next_acceptance_id
from factory.domain.journal import entry_text
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument
definition = PipelineDefinition.model_validate({'contract': '1.0', 'acceptance_stage': 'acceptance', 'roles': {'acceptance-reviewer': {'write_paths': ['{work_item}']}}, 'stages': {'acceptance': {'role': 'acceptance-reviewer', 'next': ['approval']}, 'approval': {'approval': True, 'next': ['done']}, 'done': {}}})
print([is_before_approval(definition, stage) for stage in ('acceptance', 'approval', 'done')])
document = WorkItemDocument(state=AcceptanceState(stage='acceptance', stories=['F0001-S0001']), body='# Acceptance of Todo service\n\n## Journal\n')
merged = book_merge(document, '2 runs', before_approval=True)
print(merged.state.stage, merged.state.outcome, entry_text(merged, 1))
recorded = ReportFacts(id='F0001-A0001', folder='done', on_branch=False, state=merged.state)
files = FeatureFiles(feature='F0001', done=['F0001-S0001-a.md'])
print(acceptance_status(files, [recorded]))
more = files.model_copy(update={'done': ['F0001-S0001-a.md', 'F0001-S0003-c.md']})
print(acceptance_status(more, [recorded]), next_acceptance_id('F0001', [recorded.id]))
"
```
Expect: four lines: `[True, False, False]`, then `done accepted done (pull request merged before approval); cost: 2 runs`, then `accepted` (the recorded report covers the one archived story), then `due F0001-A0002` (a second story was archived, so the feature is due again, and the next acceptance has the next number).

## Log (append only)

1. 2026-10-12 human: created.
