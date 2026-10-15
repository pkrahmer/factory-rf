---
stage: accept
pr: 108
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
2. intake: accepted
   - Interface: names concrete modules and signatures (`factory.domain.acceptance.is_before_approval`, `book_merge(..., before_approval=False)`, `AcceptanceMerged.handle` in `factory.application.acceptance`). The rules state the entry texts, the error types and the order of the checks, so they are concrete.
   - Criteria: each is testable by one test function. Each Interface rule has its failing side. Criterion 2 covers `KeyError` and `ValueError`. Criterion 1 covers true for `acceptance` and false for `approval` and `done`. Criterion 3 covers the entry text with `before_approval=True`, and criterion 6 covers the default text. Criterion 7 covers all three merge methods. Criterion 5 covers the cleared `blocked`. Criteria 8 to 12 cover the repeated acceptance (status, untouched earlier report, own cost lines).
   - Demo: a single runnable `uv run python -c` command. The `Expect:` line gives four checkable output lines.
   - Architecture: the pure rules are in `factory.domain`, and the handler change is in `factory.application`, which uses the domain and no adapter. This fits the layering in `CLAUDE.md`.
   - Scope: within F0009's "A merge before the approval and repeated acceptances (ST2.1, ST2.2, R31)". Nothing falls under Out of scope. The close handler (S0007), the registration (S0010) and the ticks (S0011) are left to the stories that own them.
3. tester: wrote red tests for criteria 1 to 12; criteria 13 and 14 belong to the checks and the documenter.
   - criterion 1: tests/domain/test_acceptance_before_approval.py::test_only_a_stage_before_the_first_approval_is_before_approval (parametrized: acceptance → True, approval → False, done → False, run against the fixture's stage order)
   - criterion 2: tests/domain/test_acceptance_before_approval.py::test_an_unknown_stage_or_a_definition_without_approval_is_refused (unknown stage → KeyError; a definition with no approval stage → ValueError)
   - criterion 3: tests/domain/test_acceptance_before_approval.py::test_a_merge_before_approval_books_like_a_merge_with_an_entry_that_says_so (the state equals what plain `book_merge` produces, one factory `done` record is appended, and its text is the before-approval prefix plus `cost_line(bill)`)
   - criterion 4: tests/application/test_acceptance_merged_before_approval.py::test_an_acceptance_merged_at_its_review_stage_is_booked_accepted_before_approval
   - criterion 5: tests/application/test_acceptance_merged_before_approval.py::test_an_acceptance_merged_while_it_waits_with_a_question_is_booked_and_unblocked
   - criterion 6: tests/application/test_acceptance_merged_before_approval.py::test_an_acceptance_merged_at_its_approval_before_the_hand_over_is_booked_as_usual
   - criterion 7: tests/application/test_acceptance_merged_before_approval.py::test_every_merge_method_books_an_acceptance_merged_before_approval_alike (merge, squash, rebase)
   - criterion 8: tests/application/test_acceptance_merged_before_approval.py::test_the_proposed_stories_of_a_merge_before_approval_leave_the_feature_incomplete
   - criterion 9: tests/application/test_acceptance_repeated.py::test_a_story_archived_after_the_acceptance_makes_the_feature_due_and_opens_the_next
   - criterion 10: tests/application/test_acceptance_repeated.py::test_opening_the_repeated_acceptance_leaves_the_earlier_report_and_its_costs_unchanged
   - criterion 11: tests/application/test_acceptance_repeated.py::test_a_recorded_repeated_acceptance_leaves_the_feature_accepted_and_not_due
   - criterion 12: tests/application/test_acceptance_repeated.py::test_each_acceptance_bills_only_its_own_cost_records

   Files created: tests/domain/test_acceptance_before_approval.py, tests/application/test_acceptance_merged_before_approval.py, tests/application/test_acceptance_repeated.py.

   Run results: `make test` stopped at collection because `is_before_approval` cannot be imported from `factory.domain.acceptance`. No other module is missing. The two application files import only names that already exist. Once collection gets past the domain file, criteria 4, 5 and 7 should fail on the entry text, because the handler does not pass `before_approval` yet. The other application tests walk what earlier stories built and may pass at once, which the Assignment allows. `make lint` is green.

   Choices:
   - The domain test builds the fixture's pipeline definition in-file with `PipelineDefinition.model_validate`, with the same stages and order as `PIPELINE_YAML`. A domain test should not import the YAML adapter, and importing the definition from tests/domain/test_move_rule.py would couple two test modules.
   - The "no approval stage" case is a valid definition with stages `acceptance` → `done`. No load-time rule requires an approval stage.
   - Each application file has its own local fixtures, as tests/application/test_acceptance_merged.py does. I did not move them into a shared module, because that would mean editing a test I did not write.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: made criteria 1 to 12 pass; `make check` is green.
      - `src/factory/domain/acceptance.py`: added `is_before_approval(definition, stage)`. It raises `KeyError` for a stage the definition does not have, and checks this before it calls `position`. It raises `ValueError` when the definition has no approval stage. Otherwise it compares `position(stage)` with the position of the first stage that has `approval=True`. `book_merge` now takes a keyword-only `before_approval=False`. When it is true, the entry text is `done (pull request merged before approval); cost: ` followed by `cost_line(bill)`, and the prefix is a module constant next to `_CLOSED_ENTRY_PREFIX`. When it is false, the entry still uses `done_entry_text(bill)`. Both paths book through the existing `_booked`, so the outcome, the `done` stage and the cleared `claim` and `blocked` are the same.
      - `src/factory/application/acceptance.py`: `AcceptanceMerged._book` takes the stage from the report it reads on main through `require_state`. A report without a state now raises `CannotHandle` ("the report on the main branch has no state"). Before this change, `book_merge` raised `ValueError` in that case. I used `require_state` rather than an inline `is None` check because `tests/test_no_state_copies.py` allows only that helper to make this check. The handler passes `is_before_approval(definition, stage)` to `book_merge`.
      - Design: I added a flag on `book_merge`, as the Interface specifies. I rejected a second booking function (`book_early_merge`) because it would repeat the merge booking. I also rejected moving the stage judgement into `book_merge`, because the domain booking would then need the definition.
      - Repeated acceptances needed no code. As the Assignment allows, the tests for criteria 8 to 12 passed on what earlier stories built.
      - Refactor: I read the diff and found nothing to change, so there is no refactor commit.
      - Noticed, not touched: the new no-state branch in `_book` (`application/acceptance.py:272`) is not covered by a test. Coverage is still at 99 %.

   `make check`: check: green
5. reviewer: no findings.
      - Acceptance criteria: each of criteria 1 to 12 has a test named in entry 3 that checks what the criterion says. The coder's entry reports `make check` green.
      - Interface rules and their failing sides: the unknown stage gives `KeyError`. The test checks this before `position`, whose `ValueError` would otherwise fail the test. A definition without an approval stage gives `ValueError`. The boundary is tested on both sides: `acceptance` gives true, and `approval` and `done` give false.
      - `is_before_approval` (`src/factory/domain/acceptance.py:277`) takes the first approval stage in `definition.stages` order. That is the same order `PipelineDefinition.position` uses (`list(self.stages).index`), so it matches the rule.
      - The domain test's copy of the fixture definition has the same stage order as `PIPELINE_YAML`. The tester gave the reason for the copy in entry 3.
      - Architecture: the domain function takes the definition as data and does no I/O. The handler (`src/factory/application/acceptance.py:271`) uses only domain functions and the existing `require_state` helper. No new imports cross layers.
      - Security: no suppression markers, no strings built for a shell, no secrets.
      - Quality: the before-approval prefix is a module constant next to `_CLOSED_ENTRY_PREFIX`, and both paths book through the existing `_booked`, so nothing is duplicated.
      - Considered and not counted: the new no-state `CannotHandle` in `AcceptanceMerged._book` has no test, which the coder disclosed. It replaces the `ValueError` that `book_merge` raised at the same point before this change, so it is not a regression, and `require_state` is the helper the codebase requires for that check.
      - Ticket hygiene: the Assignment matches what was built. The coder's entry gives the main decision (a flag on `book_merge`) and what was rejected. Criterion 14 still describes what the documenter must write.
6. documenter: criterion 14 written; `make check` is green.
   - `docs/operator-guide.md`: in the section on the human's act on an acceptance, after the sentence on each acceptance's own cost, two paragraphs. "Merged before its approval": booked `accepted`, the entry `done (pull request merged before approval); cost: ...`, a waiting question cleared, a merge at the approval stage gets the ordinary entry, the feature is `incomplete` and not due, and nothing loops. "Accepted again": a story archived afterwards makes the feature due, the next acceptance is `A0002` with its own report and cost records, the earlier report stays unchanged, the status is `merged_unrecorded` until the repeat is recorded and then `accepted`.
   - `docs/decisions.md`: a new entry on why a merge before approval is booked like any merge and a repeated acceptance is a new work item. It gives the reason (v1's loop came from one report file whose stage had to change) and the alternatives rejected.
   - Cross-read against the diff and found current: README, `docs/project-guide.md`, and the rest of the operator guide, including "When a feature acceptance is due" (the `merged_unrecorded` and covering-report rules match) and the merge paragraph above my addition.
   - Findings: none. The code matches the Interface. Stale but unrelated: none seen. The coder disclosed that the new no-state `CannotHandle` in `AcceptanceMerged._book` has no test, and the reviewer did not count it.

   `make check`: check: green
7. demo: I ran the one command under `## Demo` from the repository root. Its output matches the `Expect:` line, and I found no findings.

   Command 1 (`uv run python -c "…"`, which calls is_before_approval, book_merge with before_approval=True, acceptance_status and next_acceptance_id):
   ```
   [True, False, False]
   done accepted True
   accepted
   due F0001-A0002
   ```
   It met its `Expect:` line. That line asks for four output lines and all four are right:
   - `[True, False, False]`: only the stage `acceptance` counts as before the approval.
   - `done accepted True`: the report is booked `accepted` at `done`, and its journal entry starts with `done (pull request merged before approval); cost: `.
   - `accepted`: the recorded report covers the one archived story.
   - `due F0001-A0002`: a second story was archived, so the feature is due again and the next acceptance gets the next number.

   Checked against the acceptance criteria: the output agrees with criteria 1, 3, 4, 9 and 11. It contradicts none of criteria 1 to 14. The demo does not exercise the handler, the merge methods or the files on the remote (criteria 4 to 12). Entries 3 to 5 name the tests for those, and the reviewer checked them. The factory runs `make check` itself after this stage. I did not run it.
