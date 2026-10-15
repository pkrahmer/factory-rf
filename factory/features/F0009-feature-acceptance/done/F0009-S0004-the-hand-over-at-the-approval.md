---
stage: done
pr: 106
blocked: null
comments_seen: 4
round: 0
attempts: 0
---
# The hand-over at the acceptance's approval

## Assignment (as of log entry 1)

When an acceptance reaches its approval, code hands it to the human: it replaces the draft pull request's description with the acceptance reviewer's recommendation, its findings in short, its proposed stories and a closing text that says what a merge and a close do; it marks the pull request ready for review, posts the cost table once, and records in the work item that the hand-over is done (`handed_over`), so that a failure at any step is retried from state and nothing repeats. No agent writes the description. The closing text names no merge method, because every method the hosting service offers is handled (ST2.3). A story's hand-over is F0007's (`HandOverHandler`, F0007-S0009); the acceptance's handler follows it step for step, with F0007's helpers (`target_of`, `require_pull_request`, `WorkItemRecorder`, `commit_subject`, `cost_table_post`, the same post key), and differs in the description it assembles. A small handler (`SplitByWorkItemKind`) sends each `hand_over`, `merged` and `closed` event to the story's handler or to the acceptance's by the work item's id. Covers no condition of its own; it carries the approval half of kept thing 19 (the result is the human's act) and keeps kept thing 11 (draft and ready say whose turn it is; one post per stop), kept thing 20 (the bill is shown at the approval) and R22 (state before effect, keyed post). The merge and the close that follow are S0005 and S0007. The splits are registered in `factory.entry.wiring.build_handlers` by S0010.

## Interface

`src/factory/domain/acceptance.py` (grown)

```python
RECOMMENDATION = "Recommendation"
FINDINGS_IN_SHORT = "Findings in short"
PROPOSED_STORIES = "Proposed stories"
NONE_TEXT = "none"
ACCEPTANCE_CLOSING = (
    "Merge to accept the report and take the proposed stories into the feature's backlog, "
    "where you refine them before starting any. "
    "Close, with a comment saying why, to refuse: the report stays on the main branch as refused "
    "with your comment, the proposed stories are discarded, and the feature counts as not "
    "accepted until another story is archived and a new acceptance runs. "
    "Nobody answers comments while the acceptance waits here; they go into the report's journal."
)

def acceptance_description(document: WorkItemDocument, role: str) -> str: ...
```

`src/factory/application/acceptance.py` (grown)

```python
class AcceptanceHandOver(Handler):         # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...

class SplitByWorkItemKind(Handler):
    def __init__(self, story: Handler, acceptance: Handler) -> None: ...
    def handle(self, event: Event) -> None: ...
    @property
    def story(self) -> Handler: ...
    @property
    def acceptance(self) -> Handler: ...
```

`Handler` is in `factory.application.dispatcher`; `PostKey` in `factory.domain.hosting`; `cost_table`, `bills_by_stage` in `factory.domain.bills`; `cost_table_post` in `factory.domain.post_texts`; `cost_table_key` in `factory.domain.hand_over` (moved here by this story); `target_of`, `require_pull_request`, `commit_subject` and `WorkItemRecorder` in `factory.application.handlers.recording` (F0007-S0001); `HostingServiceError`, `CannotHandle`, `PushFailed` in `factory.domain.errors`.

Rules:

- `RECOMMENDATION` and `PROPOSED_STORIES` are written in the form that `factory.domain.sections` uses for `JOURNAL` (no `## `), so that `section_text(body, RECOMMENDATION)` finds the report's `## Recommendation` section.
- `acceptance_description(document, role)` is four parts joined by one empty line: the line `## Recommendation`, an empty line and the recommendation; the line `## Findings in short`, an empty line and the findings; the line `## Proposed stories`, an empty line and the proposed stories; and `ACCEPTANCE_CLOSING`.
- The recommendation is `section_text(body, RECOMMENDATION)` and the proposed stories are `section_text(body, PROPOSED_STORIES)`, each stripped of surrounding whitespace. The findings are the visible text (`entry_text`, F0002-S0003: the text after `<speaker>: `, the human's date dropped) of the last journal record with `speaker == role` and `kind == "result"` (`last_record`), stripped. A missing section, an empty text or no such record gives `NONE_TEXT` for that part. This story adds `"factory.domain.acceptance"` to the set `ALLOWED["entry_text"]` of F0005-S0009's `tests/test_no_journal_reading.py`, with the human's leave (the feature's decision 22), and changes nothing else of that file.
- `ACCEPTANCE_CLOSING` contains none of the words `squash`, `rebase` and `merge commit`.
- `AcceptanceHandOver.__init__` stores its arguments and never raises. The role is the role of `definition.acceptance_stage`, looked up in `handle`.
- `AcceptanceHandOver.handle(event)` checks, in this order, and raises `CannotHandle(kind=<the event's kind>, reason=...)` with: `"not a hand_over event"` when `event.kind != "hand_over"`; `"not an acceptance"` when the event has no work item or its id is not an acceptance's; `"no acceptance stage"` when `definition.acceptance_stage` is `None`; `"stage <stage> is not an approval"` when the work item's stage (from `target_of(event)`) is not a stage of the definition with `approval=True`; then `require_pull_request(target, "hand_over")`, which raises `CannotHandle("hand_over", "work item <id> has no pull request")` when the state has no `pull_request`.
- It then calls `WorkItemRecorder.check_out(branch)` and reads the report from the checkout, so the document it works on is the branch's, not the event's snapshot. When `state.handed_over == state.stage` it returns with no effect: no description, no post, no commit. Otherwise it does these, in this order: read the cost records from `cost_records_path(snapshot.path)` in the checkout; `HostingService.set_description` with `acceptance_description(...)`; `set_draft(number, False)`; `post_comment` of `cost_table_post(cost_table(bills_by_stage(records)))` with `PostKey(work_item=<id>, kind="cost_table", n=str(<number of the latest record of kind result, 0 when there is none>))`, the key rule of F0007-S0009; and last it sets `handed_over` to the stage and records the report with `commit_subject(id, "handed over at <stage>")` (`WorkItemRecorder.record`; a push whose outcome is not `pushed` raises `PushFailed`). A failing hosting call raises its `HostingServiceError` and nothing after it is done.
- The post key is F0007-S0009's: this story moves `_cost_table_key` of `factory.application.handlers.hand_over` to `factory.domain.hand_over` as the public `cost_table_key(work_item: WorkItemId, document: WorkItemDocument) -> PostKey`, which `HandOverHandler` and `AcceptanceHandOver` both call; nothing else of F0007's modules changes.
- `SplitByWorkItemKind.handle(event)` passes the event to `acceptance` when `event.work_item` is set and its id is an acceptance's, to `story` when it is set and is a story's, and otherwise raises `CannotHandle(kind=<the event's kind>, reason="no work item")`. The two properties return the handlers it was built with, so a wiring test can tell them.

Tests: `tests/domain/test_acceptance_description.py`, `tests/application/test_acceptance_hand_over.py`, `tests/application/test_split_by_work_item_kind.py`; the `remote`, `checkout`, `human`, `hosting`, `kill_points` and `boundaries` fixtures, with `hosting.create_pull_request` for the acceptance's draft pull request. The acceptance is opened with `AcceptanceService.open` (S0003) for a feature `F0002-todo` that the test pushes (the fixture's `F0001` has a backlog story and is never due), its pull request number is written into the report's state on the branch with `human.push_file`, and its stage is set to `approval` the same way. The recording stand-ins of the split's tests subclass `Handler`, as F0007's tests do. The event without a work item of criterion 18 is an `idle` event.

## Acceptance criteria

1. For a report whose `## Recommendation` section reads `accepted with stories`, whose `## Proposed stories` section reads `- one story`, and whose reviewer's last `result` entry reads `accepted with stories; 1 story proposed`, `acceptance_description(document, "acceptance-reviewer")` is exactly `"## Recommendation\n\naccepted with stories\n\n## Findings in short\n\naccepted with stories; 1 story proposed\n\n## Proposed stories\n\n- one story\n\n" + ACCEPTANCE_CLOSING`.
2. With two `result` records of the reviewer, the findings are the text of the later one.
3. A `result` record of another speaker and a later `comment` record of the human are not used as the findings.
4. A missing `## Recommendation` section, a missing `## Proposed stories` section, a section with no text and a journal without a `result` record of the reviewer each give the text `none` for that part and leave the other parts as they are.
5. `ACCEPTANCE_CLOSING` is the text of the Interface and contains none of `squash`, `rebase` and `merge commit`; the description ends with it, after an empty line.
6. `AcceptanceHandOver.handle` on a `hand_over` event of an acceptance at the stage `approval` sets the pull request's description to `acceptance_description(...)` and marks the pull request ready for review (`draft` is `False`).
7. It posts the cost table once: `hosting.factory_posts(number)` holds one comment whose key is `PostKey(work_item=<id>, kind="cost_table", n=<number of the latest result record, 0 without one>)` and whose body contains `cost_table(bills_by_stage(<the acceptance's records>))`.
8. It writes `handed_over == "approval"` into the report on the work item's branch and pushes it: the report at `origin/<branch>` has that state, and the commit changes the report's path only.
9. When `set_description` fails (`hosting.fail_next("set_description")`) `handle` raises `HostingServiceError`, posts nothing and leaves `origin/<branch>` as it was.
10. After `hosting.fail_next("set_draft")` made the first `handle` fail, a second `handle` completes with one cost table post in all and `handed_over` set.
11. After `kill_points.arm(KillPoint.BEFORE_PUSH)` made the first `handle` raise `InjectedKill`, a second `handle` ends with one cost table post in all and `handed_over` set on `origin/<branch>`.
12. A `hand_over` event for a report whose `handed_over` already equals its stage on `origin/<branch>` does nothing, also when the event's snapshot still shows `handed_over` unset: the description is not set again, nothing is posted and `origin/<branch>` has no new commit.
13. `handle` raises `CannotHandle` with the reason `work item <id> has no pull request` for a work item whose state has no `pull_request`, and writes and posts nothing.
14. `handle` raises `CannotHandle` with the reason `stage acceptance is not an approval` for a work item at the stage `acceptance`, and writes and posts nothing.
15. `handle` raises `CannotHandle` with the reasons `not a hand_over event` for an event of another kind and `not an acceptance` for a story's `hand_over` event, and writes and posts nothing.
16. `AcceptanceHandOver(boundaries, definition)` with `definition.acceptance_stage` `None` is built without an error, and its `handle` of a `hand_over` event of an acceptance raises `CannotHandle` with the reason `no acceptance stage` and writes and posts nothing, and a story's `hand_over` event with that definition raises with the reason `not an acceptance`.
17. `SplitByWorkItemKind` passes an event whose work item is an acceptance to the acceptance handler only, and one whose work item is a story to the story handler only; its `story` and `acceptance` properties return the two handlers it was built with.
18. `SplitByWorkItemKind` raises `CannotHandle` with the reason `no work item` for an event without a work item, and calls neither handler.
19. F0005-S0009's search test passes on the real tree with `factory.domain.acceptance` in its allow-list of `entry_text`: no module of F0009 other than `factory.domain.acceptance` references `entry_text`.
20. When the push is not `pushed` (a subclass of `FakeHostingService` whose `set_description` first pushes a commit with changed text to `origin/<branch>` through `human.push_file`, then calls the fake's own method), `handle` raises `PushFailed` and `handed_over` is not set on `origin/<branch>`.
21. make check stays green.
22. docs: `docs/operator-guide.md` describes what the human sees when an acceptance is handed over (the ready pull request, the description's four parts, the cost table) and what a merge and a close each do; `docs/project-guide.md` mentions `SplitByWorkItemKind` as the place where a story's and an acceptance's handlers are told apart, and that `factory.domain.acceptance` is on the allow-list of `entry_text` in the journal search test.

## Demo

```bash
uv run python -c "
from factory.domain.acceptance import AcceptanceState, acceptance_description
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument
journal = [JournalRecord(number=1, speaker='factory', kind='started'), JournalRecord(number=2, speaker='acceptance-reviewer', kind='result')]
body = '# Acceptance of Todo service\n\n## Recommendation\n\naccepted with stories\n\n## Journal\n\n1. factory: started.\n2. acceptance-reviewer: accepted with stories; 1 story proposed\n'
document = WorkItemDocument(state=AcceptanceState(stage='approval', stories=['F0001-S0001'], journal=journal), body=body)
parts = acceptance_description(document, 'acceptance-reviewer').split('\n\n')
print(parts[:6])
print(len(parts), parts[-1].startswith('Merge to accept'))
"
```
Expect: two lines: `['## Recommendation', 'accepted with stories', '## Findings in short', 'accepted with stories; 1 story proposed', '## Proposed stories', 'none']`, then `7 True` (the report has no proposed stories section, so that part reads `none`).

```bash
uv run python -c "
from factory.application.acceptance import SplitByWorkItemKind
from factory.application.dispatcher import Handler
from factory.domain.events import Event
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
class Recorder(Handler):
    def __init__(self, name):
        self.name = name
    def handle(self, event):
        print(self.name, event.work_item.id)
split = SplitByWorkItemKind(Recorder('story'), Recorder('acceptance'))
for work_item in ('F0001-S0001', 'F0001-A0001'):
    document = WorkItemDocument(state=WorkItemState(stage='approval'), body='# T\n')
    snapshot = WorkItemSnapshot(id=work_item, path='factory/features/F0001-x/in-progress/' + work_item + '-y.md', folder='in-progress', branch='work-item/' + work_item, branch_commit=None, document=document)
    split.handle(Event(kind='hand_over', work_item=snapshot, remote_state='0' * 40))
"
```
Expect: two lines: `story F0001-S0001`, then `acceptance F0001-A0001`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: 1. The Interface says "a push whose outcome is not `pushed` raises `PushFailed`" (`AcceptanceHandOver.handle`, last step), but no criterion tests the failing side. Criteria 9 to 11 cover a failing hosting call and a kill before the push. Nothing covers a push that is rejected, for example because `origin/<branch>` moved after `check_out`, or whatever else makes `WorkItemRecorder.record` return an outcome other than `pushed`. Two coders could implement this differently and both pass. Options: (a) add a criterion before the two closing ones, e.g. "when the push is not `pushed` (the human pushed a commit to the branch after the checkout), `handle` raises `PushFailed` and `handed_over` is not set on `origin/<branch>`"; (b) drop the sentence and leave `PushFailed` to the recorder, which F0007's tests already cover. I would choose (a), if the fixtures can produce a rejected push deterministically. Say how if they can't, or choose (b).

   Everything else checked out:
   - The Interface is concrete.
   - Every other rule has a criterion on both sides.
   - The Demo is runnable and its Expect lines are checkable.
   - The architecture and the feature's scope hold.

   The format check passed.
3. human (pull request comment, 2026-10-15): (a): add the criterion before the two closing ones, as you worded it. The fixtures can produce the rejected push deterministically: the hosting calls come between `check_out` and the record, so the test uses a subclass of `FakeHostingService` whose `set_description` first pushes a commit with changed text to `origin/<branch>` through `human.push_file` (as F0006-S0004's criterion 9 test races a human push), then calls the fake's own method. `handle` then raises `PushFailed`, and `handed_over` is not set on `origin/<branch>`. The Interface stays as it is.
4. intake: accepted. Carried in from log entry 3 (the human's answer (a)): added a new criterion 20 before the two closing ones: when the push is not `pushed` (a `FakeHostingService` subclass whose `set_description` first pushes a changed commit to `origin/<branch>` via `human.push_file`, then calls the fake's own method), `handle` raises `PushFailed` and `handed_over` is not set on `origin/<branch>`. `make check` is now 21 and `docs:` 22. The Interface and Assignment are unchanged, since the meaning of the task did not change.
   - Interface: names concrete modules, signatures, constants and rules, including the `PushFailed` rule that the new criterion now covers.
   - Criteria: each is testable by one test function. Every rule has its failing side: wrong event kind, not an acceptance, no acceptance stage, not an approval, no pull request, failing hosting calls, kill before push, rejected push, already handed over, and no work item in the split.
   - Demo: both blocks are runnable, and each Expect line is checkable against the output.
   - Architecture: the domain description function and the application handlers sit in the right layers. `cost_table_key` moves down to the domain, which respects the layering.
   - Scope: within F0009's scope ("At the approval") and not in its Out of scope. The allow-list change in `tests/test_no_journal_reading.py` is covered by decision 22.
5. tester: Wrote red tests for criteria 1–20. Criteria 21 (`make check`) and 22 (docs) belong to the coder and the documenter.

   Criterion → test:
   - criterion 1: tests/domain/test_acceptance_description.py::test_the_description_holds_the_recommendation_findings_proposed_stories_and_closing
   - criterion 2: tests/domain/test_acceptance_description.py::test_the_findings_are_the_later_of_two_results_of_the_reviewer
   - criterion 3: tests/domain/test_acceptance_description.py::test_a_result_of_another_speaker_and_a_later_human_comment_are_not_the_findings
   - criterion 4: tests/domain/test_acceptance_description.py::test_a_missing_part_reads_none_and_leaves_the_others (rows: no-recommendation, no-proposed-stories, empty-section, no-reviewer-result)
   - criterion 5: tests/domain/test_acceptance_description.py::test_the_closing_names_no_merge_method_and_ends_the_description (one row per forbidden word)
   - criterion 6: tests/application/test_acceptance_hand_over.py::test_the_hand_over_sets_the_acceptance_description_and_marks_the_pull_request_ready
   - criterion 7: tests/application/test_acceptance_hand_over.py::test_the_hand_over_posts_the_cost_table_once_keyed_by_the_latest_result (rows: latest-result n=2, no-result n=0)
   - criterion 8: tests/application/test_acceptance_hand_over.py::test_the_hand_over_records_handed_over_in_one_commit_of_the_report_only
   - criterion 9: tests/application/test_acceptance_hand_over.py::test_a_failing_description_raises_and_posts_and_records_nothing
   - criterion 10: tests/application/test_acceptance_hand_over.py::test_after_a_failing_ready_flag_the_next_handling_completes_with_one_cost_table_post
   - criterion 11: tests/application/test_acceptance_hand_over.py::test_after_a_kill_before_the_push_the_next_handling_records_with_one_cost_table_post
   - criterion 12: tests/application/test_acceptance_hand_over.py::test_a_report_handed_over_on_its_branch_is_handled_without_effect_despite_a_stale_snapshot
   - criterion 13: tests/application/test_acceptance_hand_over.py::test_a_report_without_a_pull_request_cannot_be_handed_over
   - criterion 14: tests/application/test_acceptance_hand_over.py::test_a_report_at_a_stage_that_is_not_an_approval_cannot_be_handed_over
   - criterion 15: tests/application/test_acceptance_hand_over.py::test_an_event_that_is_not_an_acceptance_hand_over_cannot_be_handled (rows: another-kind `merged`, a-story)
   - criterion 16: tests/application/test_acceptance_hand_over.py::test_without_an_acceptance_stage_the_handler_is_built_and_refuses_every_hand_over (rows: an-acceptance, a-story)
   - criterion 17: tests/application/test_split_by_work_item_kind.py::test_an_event_goes_to_the_handler_of_its_work_items_kind_only (rows: story and acceptance × hand_over, merged, closed; also checks the `story` and `acceptance` properties)
   - criterion 18: tests/application/test_split_by_work_item_kind.py::test_an_event_without_a_work_item_goes_to_neither_handler (an `idle` event)
   - criterion 19: tests/test_no_journal_reading.py::test_no_module_reads_data_from_the_journal_text. The only change to that file: `"factory.domain.acceptance"` added to `ALLOWED["entry_text"]`, as the Interface says.
   - criterion 20: tests/application/test_acceptance_hand_over.py::test_a_push_that_is_not_pushed_raises_and_leaves_handed_over_unset. `RacingHosting` subclasses `FakeHostingService`; its `set_description` has the human push a commit to the branch and then calls the fake's own method. The handler is given `dataclasses.replace(boundaries, hosting=racing)`.

   Setup in the hand-over tests: `AcceptanceService.open("F0002")` opens the acceptance after the human pushes `F0002-todo` (a feature file and two done stories). `hosting.create_pull_request` creates the draft pull request. The `publish` fixture pushes the report (an `AcceptanceState` at `approval` with the pull request number) and its cost-record sidecar through `human.push_file`, then returns the snapshot.

   Files created: tests/domain/test_acceptance_description.py, tests/application/test_acceptance_hand_over.py, tests/application/test_split_by_work_item_kind.py. Changed: tests/test_no_journal_reading.py (the allow-list only).

   Modules that could not be imported (collection errors, as intended): `factory.domain.acceptance` has no `ACCEPTANCE_CLOSING`, `FINDINGS_IN_SHORT`, `NONE_TEXT`, `PROPOSED_STORIES`, `RECOMMENDATION` or `acceptance_description`; `factory.application.acceptance` has no `AcceptanceHandOver` or `SplitByWorkItemKind`.

   `make lint` is green. The type check was skipped, as the stage says. I also ran pytest once more, on just the three new files, to see why collection failed.

   Left out: no direct test of `cost_table_key` in `factory.domain.hand_over`. No criterion names it; criterion 7 covers the key through the handler, and F0007's tests cover `HandOverHandler`.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
6. coder: The implementation is done and committed in cdf6d23. `make check` is red only at `make types`, and the cause is in a test I may not edit. It needs your answer.

   Built:
   - `src/factory/domain/acceptance.py`: `RECOMMENDATION`, `FINDINGS_IN_SHORT`, `PROPOSED_STORIES`, `NONE_TEXT` and `ACCEPTANCE_CLOSING`, plus `acceptance_description`. The findings come from `last_record(speaker=role, kind="result")` and then `entry_text`.
   - `src/factory/domain/hand_over.py`: the public `cost_table_key(work_item, document)`, moved here from `_cost_table_key`. `HandOverHandler` in `src/factory/application/handlers/hand_over.py` now calls it; nothing else in that module changed.
   - `src/factory/application/acceptance.py`: `AcceptanceHandOver` and `SplitByWorkItemKind`.
     - `AcceptanceHandOver` checks in the order the Interface gives. It reuses `target_of`, `require_pull_request`, `WorkItemRecorder` and `commit_subject`, and follows `HandOverHandler` step for step.
     - Main decision: the reviewer's role comes from `definition.stages[acceptance_stage].role`. A missing stage or role raises the same `no acceptance stage` error, so I don't add a reason the Interface doesn't name.

   Checks:
   - `make lint`, `layers`, `sast`, `secrets`, `licenses` and `test` are green (coverage 99.51 %), and every test of this ticket passes.
   - The first Demo prints the expected lines.

   The problem: `make types` fails with four `list-item` errors in `tests/domain/test_acceptance_description.py` (lines 61, 78, 88 and 140). Mypy infers `REVIEWER_RESULT = (ROLE, "result", ...)` as `tuple[str, str, str]`, but `_document` expects `list[tuple[str, JournalKind, str]]`. The production code can't fix this.

   I checked the fix on a copy outside the repo: annotating that one constant as `REVIEWER_RESULT: tuple[str, JournalKind, str] = ...` makes mypy pass on the file with the project's config.

   Options:
   - (a) The tester adds that annotation and changes nothing else. I'd choose this.
   - (b) The tester types the entries some other way, for example a small helper that returns `tuple[str, JournalKind, str]`.

   With (a), I end the next round with `tests` and name exactly that change.

   Refactor: I read the diff and found nothing to change.

   Not touched: `SplitByWorkItemKind` sends every id that is not an acceptance's to the story handler. `is_acceptance` is the only test of kind, and the event's id is already a valid work item id.
7. human (pull request comment, 2026-10-15): (a): the tester annotates `REVIEWER_RESULT: tuple[str, JournalKind, str] = ...` in `tests/domain/test_acceptance_description.py` and changes nothing else. End with `tests` and name exactly that change.
8. coder: This needs a one-line test change, as the human decided in log entry 7, option (a). In `tests/domain/test_acceptance_description.py`, line 33, the tester annotates the constant as `REVIEWER_RESULT: tuple[str, JournalKind, str] = (ROLE, "result", f"{ROLE}: {FINDINGS_TEXT}")`, adds the `JournalKind` import from `factory.domain.journal` if the file doesn't have it yet, and changes nothing else.

   The annotation fixes the four mypy `list-item` errors at lines 61, 78, 88 and 140, which are the only thing keeping `make check` red.

   The implementation is unchanged since commit cdf6d23. Every other check is green, including `make test` at 99.51 % coverage. Once the test change is in, I'll run `make check` again and hand the ticket to review.
9. tester: tester (test change the human approved): I made the change from log entry 7 (option (a)), as entry 8 names it, and changed nothing else.

   In `tests/domain/test_acceptance_description.py`, the constant is now annotated: `REVIEWER_RESULT: tuple[str, JournalKind, str] = (ROLE, "result", f"{ROLE}: {FINDINGS_TEXT}")`. The file already imported `JournalKind` from `factory.domain.journal`, so no import was added. With the annotation, the constant matches `_document`'s `list[tuple[str, JournalKind, str]]` parameter. That should clear the four mypy `list-item` errors at lines 61, 78, 88 and 140. I did not run `make types` myself; that check is the coder's `make check`.

   `make test`: test: green (coverage 99.51 %). `make lint`: lint: green.

   `make lint`: lint: green
   `make test`: test: green
10. coder: `make check` is fully green now (lint, types, layers, sast, secrets, licenses, and test at 99.51 % coverage). The tester's annotation from entry 9 cleared the four mypy `list-item` errors. Nothing changed in `src/` this round, so there is no new commit; the implementation is still cdf6d23.

    Built (cdf6d23):
    - `src/factory/domain/acceptance.py`: `RECOMMENDATION`, `FINDINGS_IN_SHORT`, `PROPOSED_STORIES`, `NONE_TEXT`, `ACCEPTANCE_CLOSING` and `acceptance_description`. The findings come from `last_record(speaker=role, kind="result")` and then `entry_text`.
    - `src/factory/domain/hand_over.py`: the public `cost_table_key`, moved from `_cost_table_key` of `factory.application.handlers.hand_over`. `HandOverHandler` now calls it; nothing else in that module changed.
    - `src/factory/application/acceptance.py`: `AcceptanceHandOver` and `SplitByWorkItemKind`.
      - `AcceptanceHandOver` follows `HandOverHandler` step for step with F0007's helpers (`target_of`, `require_pull_request`, `WorkItemRecorder`, `commit_subject`, `cost_table_post`).

    Main decision: the reviewer's role is `definition.stages[acceptance_stage].role`, looked up in `handle`. If the stage or its role is missing, `handle` raises the same `no acceptance stage` error. I rejected adding a reason the Interface doesn't name.

    Refactor: I read the diff in round 0 (entry 6) and found nothing to change, so there is no refactor commit.

    Noticed, not touched: `SplitByWorkItemKind` sends every id that is not an acceptance's to the story handler. `is_acceptance` is the only kind test, and the event's id is already a validated work item id.

    `make check`: check: green
11. reviewer: no findings.

    What I read: the ticket, and `git diff main...HEAD -- . ':!factory'` (8 files: `src/factory/application/acceptance.py`, `src/factory/application/handlers/hand_over.py`, `src/factory/domain/acceptance.py`, `src/factory/domain/hand_over.py`, the three new test files and `tests/test_no_journal_reading.py`).

    1. Acceptance criteria:
       - Each of criteria 1 to 20 has a test named in entry 5, and each test checks the criterion it is named after.
         - Criterion 4 has rows for every missing or empty part.
         - Criterion 5 checks the exact closing text and has one row per forbidden word.
         - Criterion 7 has a row with a `result` record (n = 2) and one without (n = 0).
         - Criterion 12 runs from a stale snapshot against a branch that is already handed over.
         - Criterion 20 races a human push through a `FakeHostingService` subclass, as the human's answer in entry 3 asked.
       - Every refusal the Interface names is tested on its failing side: wrong kind, not an acceptance, no acceptance stage (for an acceptance and for a story), not an approval, no pull request, and an event without a work item in the split.
       - Entry 10 records `make check` green after the coder.
       - The only change to `tests/test_no_journal_reading.py` is the one allow-list line the Interface names.
    2. Architecture:
       - `acceptance_description` and `cost_table_key` are pure domain code.
       - `AcceptanceHandOver` and `SplitByWorkItemKind` are in the application layer and reuse F0007's helpers (`target_of`, `require_pull_request`, `WorkItemRecorder`, `commit_subject`, `cost_table_post`) rather than copying them.
       - `_cost_table_key` was moved out of `factory.application.handlers.hand_over` into the domain, not duplicated. `HandOverHandler` now calls the public `cost_table_key`, and nothing else in that handler changed.
    3. Security: no secrets, no strings built into shell commands, and no suppression markers.
    4. Quality:
       - The names are clear, and the comments say why: the speaker is taken from the record and not from the visible line, and the closing text names no merge method.
       - Docstrings are present on the public names.
       - `AcceptanceHandOver.handle` follows `HandOverHandler` step for step, with its checks in the order the Interface gives.
    5. Ticket hygiene:
       - The log explains the main decision and what was rejected: the reviewer's role comes from the acceptance stage's role, and a missing role reuses `no acceptance stage` instead of adding a new reason.
       - The Assignment matches what was built.
       - The docs criterion (22) still describes what the operator and the project guide need after this story.

    Open: nothing for review. The documenter writes criterion 22.
12. documenter: criterion 22 is written, and `make check` is green after the last edit. I found no findings for the coder. I ran no new examples, because I added none; the ticket's demo blocks are the runnable ones.

    Files changed:
    - `docs/operator-guide.md`: new subsection "The hand-over of an acceptance" under "The hand-over at the approval". It covers what the human sees: the ready pull request, the four-part description (Recommendation, Findings in short, Proposed stories, closing text), `none` for a missing part, and the cost table posted once. It also says what a merge, a close and a comment each do. It says plainly that `AcceptanceHandOver` is not yet in `build_handlers` (S0010 does that) and that the merge and close handlers are later stories. I also added a clause to "When the hand-over fails or is killed" saying it applies to stories and acceptances alike.
    - `docs/project-guide.md`:
      - A bullet "The hand-over" in the feature acceptance section: `AcceptanceHandOver`, its refusals in order, `acceptance_description`, and `cost_table_key` moved to `factory.domain.hand_over`.
      - A bullet for `SplitByWorkItemKind` as the place where a story's and an acceptance's handlers are told apart.
      - `factory.domain.acceptance` added to the `entry_text` allow-list in "No code reads data from the journal's text".

    Cross-read and found current against the diff:
    - The story's hand-over section in `docs/project-guide.md` still holds. `HandOverHandler` only swapped its private key function for the public one, with the same behaviour.
    - The story's hand-over section in `docs/operator-guide.md` holds for the same reason.
    - The README and `docs/decisions.md` were not affected.

    Stale but unrelated, not touched: the "The hand-over at the approval" intro in `docs/operator-guide.md` says `HandOverHandler` "is registered"; that is true for stories only, and my new subsection states the acceptance case.

    `make check`: check: green
13. demo: Ran both `## Demo` commands from the repository root, exactly as written and in order. Both exited 0.

    Command 1 (`acceptance_description` on a report that has no `## Proposed stories` section):
    ```
    ['## Recommendation', 'accepted with stories', '## Findings in short', 'accepted with stories; 1 story proposed', '## Proposed stories', 'none']
    7 True
    ```
    This meets its Expect line: the first six parts are as expected, the proposed-stories part reads `none`, there are 7 parts in all, and the last part, the closing text, starts with `Merge to accept`.

    Command 2 (`SplitByWorkItemKind` with one handler for stories and one for acceptances):
    ```
    story F0001-S0001
    acceptance F0001-A0001
    ```
    This meets its Expect line: the story's event went only to the story handler and the acceptance's event only to the acceptance handler.

    Against the acceptance criteria: the demo contradicts none of them. It agrees with criterion 4 (a missing section gives `none` and leaves the other parts as they are), criterion 5 (the description ends with the closing text after an empty line) and criterion 17 (each event goes to its kind's handler only). The demo does not exercise the rest of the handler's behaviour (criteria 6–16 and 20) or the docs criterion (22); those are left to the tests and the earlier stages.

    No findings.
14. done (pull request merged); cost: 10 runs, 19.4 min, 83 turns, 252k tokens in (2232k more from cache), 41k out, $2.92
