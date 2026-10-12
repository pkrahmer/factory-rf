# The hand-over at the acceptance's approval

## Assignment (as of log entry 1)

When an acceptance reaches its approval, code hands it to the human: it replaces the draft pull request's description with the acceptance reviewer's recommendation, its findings in short, its proposed stories and a closing text that says what a merge and a close do; it marks the pull request ready for review, posts the cost table once, and records in the work item that the hand-over is done (`handed_over`), so that a failure at any step is retried from state and nothing repeats. No agent writes the description. The closing text names no merge method, because every method the hosting service offers is handled (ST2.3). A story's hand-over is F0007's; the acceptance's differs in what it assembles, so a small handler (`SplitByWorkItemKind`) sends each `hand_over`, `merged` and `closed` event to the story's handler or to the acceptance's by the work item's id. Covers no condition of its own; it carries the approval half of kept thing 19 (the result is the human's act) and keeps kept thing 11 (draft and ready say whose turn it is; one post per stop), kept thing 20 (the bill is shown at the approval) and R22 (state before effect, keyed post). The merge and the close that follow are the next story. Registering `SplitByWorkItemKind` and the other acceptance handlers with the dispatcher is wiring in `factory.entry.wiring`; it is built and tested through ticks in the last story of this feature.

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
class AcceptanceHandOver:
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...

class SplitByWorkItemKind:
    def __init__(self, story: Handler, acceptance: Handler) -> None: ...
    def handle(self, event: Event) -> None: ...
```

`Handler` is in `factory.application.dispatcher`; `PostKey` in `factory.domain.hosting`; `cost_table`, `bills_by_stage` in `factory.domain.bills`; `HostingServiceError`, `CannotHandle`, `PushFailed` in `factory.domain.errors`.

Rules:

- `RECOMMENDATION` and `PROPOSED_STORIES` are written in the form that `factory.domain.sections` uses for `JOURNAL`, so that `section_text(body, RECOMMENDATION)` finds the report's `## Recommendation` section.
- `acceptance_description(document, role)` is four parts joined by one empty line: the line `## Recommendation`, an empty line and the recommendation; the line `## Findings in short`, an empty line and the findings; the line `## Proposed stories`, an empty line and the proposed stories; and `ACCEPTANCE_CLOSING`.
- The recommendation is `section_text(body, RECOMMENDATION)` and the proposed stories are `section_text(body, PROPOSED_STORIES)`, each stripped of surrounding whitespace. The findings are the visible text (`entry_text`) of the last journal record with `speaker == role` and `kind == "result"`, stripped. A missing section, an empty text or no such record gives `NONE_TEXT` for that part.
- `ACCEPTANCE_CLOSING` contains none of the words `squash`, `rebase` and `merge commit`.
- `AcceptanceHandOver.__init__` raises `ValueError` when `definition.acceptance_stage` is `None`; the role is the role of that stage.
- `AcceptanceHandOver.handle(event)` checks, in this order, and raises `CannotHandle(kind=<the event's kind>, reason=...)` with: `"not a hand_over event"` when `event.kind != "hand_over"`; `"not an acceptance"` when the event has no work item or its id is not an acceptance's; `"stage <stage> is not an approval"` when the work item's stage is not a stage of the definition with `approval=True`; `"no pull request"` when its state has no `pull_request`. It then does these, in this order: `HostingService.set_description` with `acceptance_description(...)`; `set_draft(number, False)`; `post_comment` of `cost_table(bills_by_stage(records))` with `PostKey(work_item=<id>, kind="cost_table", n=str(<number of the last journal record>))`, the records being the work item's cost records at `origin/<branch>`; then on the work item's branch (`Git.checkout(branch, start_point="origin/<branch>")`) it sets `handed_over` to the stage, writes the report, commits and pushes; a push whose outcome is not `pushed` raises `PushFailed`. A failing hosting call raises its `HostingServiceError` and nothing after it is done.
- `SplitByWorkItemKind.handle(event)` passes the event to `acceptance` when `event.work_item` is set and its id is an acceptance's, to `story` when it is set and is a story's, and otherwise raises `CannotHandle(kind=<the event's kind>, reason="no work item")`.

Tests: `tests/domain/test_acceptance_description.py`, `tests/application/test_acceptance_hand_over.py`; the `remote`, `checkout`, `human`, `hosting`, `kill_points` and `boundaries` fixtures, with `hosting.create_pull_request` for the acceptance's draft pull request.

## Acceptance criteria

1. For a report whose `## Recommendation` section reads `accepted with stories`, whose `## Proposed stories` section reads `- one story`, and whose reviewer's last `result` entry reads `accepted with stories; 1 story proposed`, `acceptance_description(document, "acceptance-reviewer")` is exactly `"## Recommendation\n\naccepted with stories\n\n## Findings in short\n\naccepted with stories; 1 story proposed\n\n## Proposed stories\n\n- one story\n\n" + ACCEPTANCE_CLOSING`.
2. With two `result` records of the reviewer, the findings are the text of the later one.
3. A `result` record of another speaker and a later `comment` record of the human are not used as the findings.
4. A missing `## Recommendation` section, a missing `## Proposed stories` section, a section with no text and a journal without a `result` record of the reviewer each give the text `none` for that part and leave the other parts as they are.
5. `ACCEPTANCE_CLOSING` is the text of the Interface and contains none of `squash`, `rebase` and `merge commit`; the description ends with it, after an empty line.
6. `AcceptanceHandOver.handle` on a `hand_over` event of an acceptance at the stage `approval` sets the pull request's description to `acceptance_description(...)` and marks the pull request ready for review (`draft` is `False`).
7. It posts the cost table once: `hosting.factory_posts(number)` holds one comment whose key is `PostKey(work_item=<id>, kind="cost_table", n=<number of the last journal record>)` and whose body contains `cost_table(bills_by_stage(<the acceptance's records>))`.
8. It writes `handed_over == "approval"` into the report on the work item's branch and pushes it: the report at `origin/<branch>` has that state, and the commit changes the report's path only.
9. When `set_description` fails (`hosting.fail_next("set_description")`) `handle` raises `HostingServiceError`, posts nothing and leaves `origin/<branch>` as it was.
10. After `hosting.fail_next("set_draft")` made the first `handle` fail, a second `handle` completes with one cost table post in all and `handed_over` set.
11. After `kill_points.arm(KillPoint.BEFORE_PUSH)` made the first `handle` raise `InjectedKill`, a second `handle` ends with one cost table post in all and `handed_over` set on `origin/<branch>`.
12. `handle` raises `CannotHandle` with the reason `no pull request` for a work item whose state has no `pull_request`, and writes and posts nothing.
13. `handle` raises `CannotHandle` with the reason `stage acceptance is not an approval` for a work item at the stage `acceptance`, and writes and posts nothing.
14. `handle` raises `CannotHandle` with the reasons `not a hand_over event` for an event of another kind and `not an acceptance` for a story's `hand_over` event, and writes and posts nothing.
15. `AcceptanceHandOver(boundaries, definition)` raises `ValueError` when `definition.acceptance_stage` is `None`.
16. `SplitByWorkItemKind` passes an event whose work item is an acceptance to the acceptance handler only, and one whose work item is a story to the story handler only.
17. `SplitByWorkItemKind` raises `CannotHandle` with the reason `no work item` for an event without a work item, and calls neither handler.
18. `make check` stays green.
19. docs: `docs/operator-guide.md` describes what the human sees when an acceptance is handed over (the ready pull request, the description's four parts, the cost table) and what a merge and a close each do; `docs/project-guide.md` mentions `SplitByWorkItemKind` as the place where a story's and an acceptance's handlers are told apart.

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
from factory.domain.events import Event
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState
class Recorder:
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
