---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Merged before its approval, and repeated acceptances

## Assignment (as of log entry 1)

Make two edge cases of the acceptance end without a loop, shown here at the level of the handler and the reader; S0011 walks the same cases over ticks. First, the human may merge an acceptance's pull request before it reached its approval (while the reviewer works, or waits with a question): the merge is the human's decision, so the acceptance is booked `accepted` like any other merge, and its journal gets an entry that says it was merged before approval (R31). In v1 this alternated forever between `merged` and `reject`; here the report moves to `done/` as a new file, so the move rule has no stage change to judge, and the proposed stories the merge brought make the feature `incomplete`, not due. Second, a feature is accepted again when another story has been archived since: the repeated acceptance is a new work item (`F0001-A0002`) with its own report and cost records, the earlier report stays as it was, and once the repeated acceptance is recorded the feature is not due again. The repeated acceptance after a refusal is shown with the close handler in S0007. Covers ST2.1, ST2.2 and R31 (and the repeated side of GH4.4); keeps kept thing 19 (due again whenever the set of archived stories changes) and kept thing 2 (the human's merge decides). Most criteria walk what the earlier stories built: they are the proof of ST2.1 and ST2.2 for the units, and a test may pass at once where an earlier story already does the work. The registration of the handlers is S0010; the proof over ticks, including that no tick yields `reject`, is S0011.

## Interface

`src/factory/domain/acceptance.py` (grown)

```python
def is_before_approval(definition: PipelineDefinition, stage: str) -> bool: ...
def book_merge(document: WorkItemDocument, bill: Bill, *, before_approval: bool = False) -> WorkItemDocument: ...
```

`src/factory/application/acceptance.py` (grown): `AcceptanceMerged.handle` passes `before_approval`.

Rules:

- `is_before_approval(definition, stage)` is true exactly when `stage` is a stage of the definition that lies before the first stage with `approval=True` in the definition's order (`PipelineDefinition.position`); the approval stage itself and every later stage, `done` included, give false. A stage not in `definition.stages` raises `KeyError`, checked before `position` is called (which raises `ValueError` for an unknown stage); a definition with no approval stage raises `ValueError`.
- `book_merge(document, bill, before_approval=True)` is the S0005 booking with the entry text `done (pull request merged before approval); cost: ` and `cost_line(bill)`; with `before_approval=False` (the default) the text is `done_entry_text(bill)`, the one without `before approval`.
- `AcceptanceMerged.handle` reads the state of the merged report on the main branch and books it with `before_approval=is_before_approval(definition, <the report's stage>)`; a `blocked` question is cleared by the booking.
- No new rule for repeated acceptances: each acceptance is a work item of its own (`next_acceptance_id`), and `acceptance_status` judges the set of archived stories against the recorded reports.

Tests: `tests/domain/test_acceptance_before_approval.py`, `tests/application/test_acceptance_merged_before_approval.py`, `tests/application/test_acceptance_repeated.py`; the fixtures of the earlier stories. The fixture's feature `F0001` has a backlog story and is never due; the tests use a feature `F0002-todo` that they push with `human.push_file("main", ...)`: its `feature.md`, stories under `done/`, and nothing under `backlog/` or `in-progress/`. Each acceptance is opened with `AcceptanceService.open`, its pull request is created with `hosting.create_pull_request`, its number is written into the report's state on the branch (and its stage set) with `human.push_file`, and the human merges with `human.merge(branch, method)` and `hosting.merge_by_human`; the handler is called directly with a hand-built `Event(kind="merged", work_item=<the acceptance's snapshot>, pull_request=<the merged view>, remote_state=<the head of origin/main>)`; S0008 and S0011 produce and run that event through the watcher and ticks.

## Acceptance criteria

1. With the fixture's pipeline definition, `is_before_approval` is true for the stage `acceptance` and false for `approval` and for `done`.
2. `is_before_approval` raises `KeyError` for a stage the definition does not have, and `ValueError` for a definition without an approval stage.
3. `book_merge(document, bill, before_approval=True)` appends one record (speaker `factory`, kind `done`) whose visible text is `done (pull request merged before approval); cost: ` followed by `cost_line(bill)`, and otherwise books as `book_merge` does.
4. R31: after the human merged the pull request of an acceptance that is at the stage `acceptance`, `AcceptanceMerged.handle` books it `accepted` in `done/` with the entry `done (pull request merged before approval); cost: <its own cost line>`.
5. An acceptance merged at the stage `acceptance` with `blocked == "question"` is booked the same way, and the booked state has `blocked` `None`.
6. An acceptance merged at the stage `approval`, before its hand-over, is booked with the entry that does not say `before approval`.
7. The merge methods `merge`, `squash` and `rebase` each give the same booked result for an acceptance merged before its approval: the report in `done/`, outcome `accepted`, the same entry text.
8. After the merge of criterion 4 brought the proposed stories into the feature's backlog and `handle` ran, the feature's status is `incomplete` and `due_features()` is empty.
9. ST2.2: with an acceptance `F0002-A0001` accepted for the stories `F0002-S0001` and `F0002-S0002`, a story `F0002-S0003` that was archived afterwards makes the feature `due` again, and `open("F0002")` opens `F0002-A0002`: the branch `work-item/F0002-A0002` and its report at `in-progress/F0002-A0002-acceptance.md` exist on the remote.
10. ST2.2: the report `F0002-A0001-acceptance.md` in `done/` is byte for byte what it was before the repeated acceptance opened, and its cost records file too.
11. ST2.2: after the repeated acceptance `F0002-A0002` was merged and `AcceptanceMerged.handle` ran, the feature's status is `accepted` and it is not due; while the merge is not yet recorded the status is `merged_unrecorded` and `due_features()` is empty.
12. GH4.4: the cost lines of `F0002-A0001` and `F0002-A0002`, each with records of its own, count only their own records, also in the entries `done (...); cost: ...` of both reports after both were merged.
13. make check stays green.
14. docs: `docs/operator-guide.md` explains what happens when an acceptance is merged before its approval (accepted, with an entry saying so) and when a feature is accepted again (a new acceptance, an earlier report unchanged); `docs/decisions.md` records why each acceptance is a work item with its own report, so that neither case loops.

## Demo

```bash
uv run python -c "
from factory.domain.acceptance import AcceptanceState, FeatureFiles, ReportFacts, acceptance_status, book_merge, is_before_approval, next_acceptance_id
from factory.domain.bills import bill
from factory.domain.journal import entry_text
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.work_item import WorkItemDocument
definition = PipelineDefinition.model_validate({'contract': '1.0', 'acceptance_stage': 'acceptance', 'roles': {'acceptance-reviewer': {'write_paths': ['{work_item}']}}, 'stages': {'acceptance': {'role': 'acceptance-reviewer', 'next': ['approval']}, 'approval': {'approval': True, 'next': ['done']}, 'done': {}}})
print([is_before_approval(definition, stage) for stage in ('acceptance', 'approval', 'done')])
document = WorkItemDocument(state=AcceptanceState(stage='acceptance', stories=['F0001-S0001']), body='# Acceptance of Todo service\n\n## Journal\n')
merged = book_merge(document, bill([]), before_approval=True)
print(merged.state.stage, merged.state.outcome, entry_text(merged, 1).startswith('done (pull request merged before approval); cost: '))
recorded = ReportFacts(id='F0001-A0001', folder='done', on_branch=False, state=merged.state)
files = FeatureFiles(feature='F0001', done=['F0001-S0001-a.md'])
print(acceptance_status(files, [recorded]))
more = files.model_copy(update={'done': ['F0001-S0001-a.md', 'F0001-S0003-c.md']})
print(acceptance_status(more, [recorded]), next_acceptance_id('F0001', [recorded.id]))
"
```
Expect: four lines: `[True, False, False]`, then `done accepted True`, then `accepted` (the recorded report covers the one archived story), then `due F0001-A0002` (a second story was archived, so the feature is due again, and the next acceptance has the next number).

## Log (append only)

1. 2026-10-12 human: created.
