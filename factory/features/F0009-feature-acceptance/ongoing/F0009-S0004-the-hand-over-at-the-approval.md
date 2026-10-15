---
stage: tests
pr: 106
blocked: null
comments_seen: 2
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
