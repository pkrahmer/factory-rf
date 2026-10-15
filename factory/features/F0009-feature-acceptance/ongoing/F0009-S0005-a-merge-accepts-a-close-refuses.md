---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# A merge accepts, a close refuses

## Assignment (as of log entry 1)

The human's merge or close of an acceptance's pull request decides its result, whatever the reviewer recommended. This story books both results as data and handles the merge; S0007 handles the close. A merge books the acceptance as `accepted`: the report moves with its cost records to the feature's `done` folder, its state says `done` and `accepted`, its journal gets one `done` entry with the acceptance's own cost, and the proposed stories that the merge brought into the feature's backlog stay there, untouched; the acceptance's branch is deleted. A close books it as `refused`: the report is written at `done` with the human's reason as the first paragraph under the recommendation, `refused` as the outcome and the cost in a `done` entry, and the proposed stories, which were only on the branch, are dropped with it. The two booking functions are built here (`book_refusal` and `refusal_reason` are used by S0007's handler). Code never interprets the human's text: it is copied unchanged. The merge handler can be run again after a kill and books nothing twice. It follows F0007's `MergedHandler` (F0007-S0003) step for step and reuses its helpers (`target_of`, `WorkItemRecorder`, `destination_path`, `done_entry_text`, `commit_subject`, and `move_with_cost_records`, which it makes public); it differs in the outcome and in the `AcceptanceState` it books. Merging an acceptance before it reached its approval, and the second acceptance of a feature, are the next story. Covers no handover condition alone (ST2.1, ST2.2 and R31 are built on this in S0006 and S0011); keeps kept thing 2 (the human accepts by merging, and a refusal returns the human's text), kept thing 19 (the result is the human's act, not the recommendation) and kept thing 20 (each acceptance costed). The report and its sidecar move or are written; nothing else on the main branch changes. `AcceptanceMerged` is registered, inside a `SplitByWorkItemKind`, in `factory.entry.wiring.build_handlers` by S0010.

## Interface

`src/factory/domain/acceptance.py` (grown)

```python
NO_REASON = "no reason given"

def book_merge(document: WorkItemDocument, bill: Bill) -> WorkItemDocument: ...
def book_refusal(document: WorkItemDocument, *, role: str, on: date, bill: Bill) -> WorkItemDocument: ...
def refusal_reason(document: WorkItemDocument, role: str) -> str: ...
```

`src/factory/application/acceptance.py` (grown)

```python
class AcceptanceMerged(Handler):         # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

`Bill`, `bill` and `cost_line` are in `factory.domain.bills`, `done_entry_text` in `factory.domain.post_texts` (F0007-S0003), `destination_path` in `factory.domain.archive` (F0007-S0003), `target_of`, `commit_subject` and `WorkItemRecorder` in `factory.application.handlers.recording` (F0007-S0001), which also holds the `move_with_cost_records` that this story makes public; `NewEntry` and `append_entry` are in `factory.domain.journal`; `insert_paragraph`, `sections` and `JOURNAL` in `factory.domain.sections`; `cost_records_path` in `factory.domain.paths`.

Rules:

- `book_merge(document, bill)` needs a document whose state is an `AcceptanceState`, else `ValueError`. It sets `stage` to `DONE_STAGE`, `outcome` to `"accepted"`, `claim` and `blocked` to `None`, and keeps every other field; it appends one entry (speaker `factory`, kind `done`) with the text `done_entry_text(bill)`, that is `done (pull request merged); cost: ` and `cost_line(bill)`.
- `refusal_reason(document, role)` is the visible text (`entry_text`), stripped, of every journal record with speaker `human` and kind `comment` that comes after the last record with `speaker == role` and kind `result` (after none, when there is no such record), in order, joined with one space; it is `NO_REASON` when there is none. The text is never interpreted.
- `book_refusal(document, role=..., on=..., bill=...)` needs an `AcceptanceState` too, else `ValueError`. It sets `stage` to `DONE_STAGE`, `outcome` to `"refused"`, `claim` and `blocked` to `None`, and keeps every other field. It makes `Refused by the human on <on as YYYY-MM-DD>: <refusal_reason(document, role)>` the first paragraph under the report's `## Recommendation` heading (`insert_paragraph`); a body without that section gets the section, holding only that paragraph, just before its journal section (`JOURNAL`, never the literal), and at the end of the body when it has no journal section either. It appends one entry (speaker `factory`, kind `done`) with the text `done (pull request closed by the human); cost: ` and `cost_line(bill)`.
- `AcceptanceMerged.__init__` stores its arguments and never raises.
- `AcceptanceMerged.handle(event)` raises `CannotHandle(kind=<the event's kind>, reason=...)` with these reasons, checked in this order: `"not a merged event"` for another kind; `"not an acceptance"` when the event has no work item or its id is a story's; `"no acceptance stage"` when `definition.acceptance_stage` is `None`; `"pull request is not merged"` when `event.pull_request` is `None` or its state is not `merged`. It changes nothing then.
- Otherwise it calls `WorkItemRecorder.check_out(MAIN_BRANCH)` and takes `target_of(event)`. When the report is in `in-progress/` at the snapshot's path in the checkout, it reads it, takes `bill(records)` of the records that the cost record reader returns for `cost_records_path(snapshot.path)` (a missing file gives no records; read at `HEAD`, which is `origin/main`, as F0007-S0003 does), and then, in this order: move the report and its cost records file with F0007-S0003's move, which this story makes the public `move_with_cost_records(git: Git, path: str, folder: LifecycleFolder) -> str` of `factory.application.handlers.recording` (it returns the destination; `MergedHandler` calls it in place of its `_move`, and nothing else of `merged.py` changes); write `book_merge(document, bill)` at the new path; commit with `commit_subject(id, "merged, archived")` and push `main` with `WorkItemRecorder.publish` (`PushFailed` when the outcome is not `pushed`). When the report is already in `done/` and not in `in-progress/`, it books nothing; when it is in neither, it raises `CannotHandle(kind=<the event's kind>, reason="no report on the main branch")`. Last, it deletes the branch `work-item/<id>` with `WorkItemRecorder.delete_branch` (F0007-S0001: `PushFailed` when the remote refuses, the booking stays pushed; then the local branch); a branch that is already gone is not an error. The move comes before the write: `git mv` onto an existing file fails.
- The own cost of the acceptance is read from the checkout at `HEAD` (the commit the handler works on) and not through `BillService`, whose remote-tracking refs give the same commit; the line therefore counts only the acceptance's own records (GH4.4, shown in S0003 criterion 18).

Tests: `tests/domain/test_acceptance_booking.py`, `tests/application/test_acceptance_merged.py`; the `remote`, `checkout`, `human`, `hosting`, `clock`, `kill_points` and `boundaries` fixtures; the feature is a `F0002-todo` that the test pushes (the fixture's `F0001` has a backlog story and is never due), the acceptance is opened with `AcceptanceService.open`, its pull request is created with `hosting.create_pull_request` and its number written into the report's state on the branch with `human.push_file`, and the human acts with `human.merge`, `hosting.merge_by_human` and `hosting.add_human_comment`.

## Acceptance criteria

1. `book_merge` sets the stage to `done`, the outcome to `accepted`, `claim` and `blocked` to `None`, and leaves `stories`, `round`, `attempts`, `crashes`, `pull_request`, `comments_read` and `handed_over` as they were.
2. `book_merge` appends one record (speaker `factory`, kind `done`) whose number follows the journal's last, and whose visible text equals `done_entry_text(bill)`.
3. `book_merge` and `book_refusal` raise `ValueError` for a document whose state is a plain `WorkItemState`.
4. `refusal_reason` joins the texts of the human's `comment` records after the reviewer's last `result` record with one space, unchanged: the texts `Too wide.` and `Cut the second story.` give `Too wide. Cut the second story.`
5. `refusal_reason` ignores a `comment` record before the reviewer's last `result` record, a human `close` record and the factory's records.
6. `refusal_reason` is `no reason given` when no human comment follows the reviewer's last result, and uses every human comment when the journal has no result of the reviewer.
7. `book_refusal` sets the stage to `done`, the outcome to `refused`, `claim` and `blocked` to `None`, and leaves the other state fields as they were.
8. `book_refusal` makes `Refused by the human on 2026-10-12: <the reason>` the first paragraph of the `## Recommendation` section, above the reviewer's recommendation text, and leaves the rest of the body as it was.
9. `book_refusal` on a body without a `## Recommendation` section adds that section, holding only the refusal paragraph, just before the `## Journal` section.
10. `book_refusal` on a body with neither a `## Recommendation` nor a `## Journal` section adds the section with the refusal paragraph at the end of the body.
11. `book_refusal` appends one record (speaker `factory`, kind `done`) whose visible text is `done (pull request closed by the human); cost: ` followed by `cost_line(bill)`.
12. After the human merged the acceptance's pull request, `AcceptanceMerged.handle` leaves on `origin/main` the report in the feature's `done/` folder, equal to `book_merge(<the merged report>, <bill of its records>)` as the writer renders it, and its cost records file beside it with the same records, neither file left in `in-progress/`; a report merged without a cost records file is booked alone in `done/`, its entry's cost `cost_line(bill([]))` (two cases, one test).
13. After `handle` the branch `work-item/<id>` is gone on the remote and locally, and a second `handle` of the same event makes no new commit and raises no error.
14. The commit `handle` makes on the main branch changes only the report's and the cost records file's paths: the proposed stories that the merge brought into the feature's backlog are still there, byte for byte.
15. A merge of an acceptance whose recommendation is `not accepted` is booked `accepted`: the recommendation text does not change the outcome.
16. `AcceptanceMerged.handle` raises `CannotHandle` with the five reasons the Interface gives (another kind of event, a story's event, no acceptance stage, a pull request that is not merged, no report on the main branch), each in its place in the order, and changes nothing.
17. After `kill_points.arm(KillPoint.AFTER_PUSH)` made the first `handle` raise `InjectedKill` right after the push of the main branch, a second `handle` leaves exactly one `done` record in the report, one new commit on `origin/main`, and the branch gone.
18. `AcceptanceMerged(boundaries, definition)` with `definition.acceptance_stage` `None` is built without an error.
19. When the remote's main branch moved since the last fetch (the human pushed to it), `AcceptanceMerged.handle` raises `PushFailed` with the outcome `rejected`, and the branch `work-item/<id>` is still on the remote.
20. When the remote refuses the deletion of the branch (`receive.denyDeletes` set in the bare remote), `handle` raises `PushFailed` with the outcome `rejected` after the booking is pushed: `origin/main` holds the report in `done/` and the branch is still on the remote.
21. make check stays green.
22. docs: `docs/operator-guide.md` explains what the human's merge and close of an acceptance do (accepted or refused whatever the recommendation; where the report lands; that the reason is the human's comments unchanged; that a refusal drops the proposed stories and a merge keeps them in the backlog); `docs/decisions.md` records why each acceptance has its own report and cost records.

## Demo

```bash
uv run python -c "
from datetime import date
from factory.domain.acceptance import AcceptanceState, book_merge, book_refusal, refusal_reason
from factory.domain.bills import bill, cost_line
from factory.domain.journal import JournalRecord, entry_text
from factory.domain.post_texts import done_entry_text
from factory.domain.work_item import WorkItemDocument
records = [('factory', 'started'), ('acceptance-reviewer', 'result'), ('human', 'comment'), ('human', 'comment')]
journal = [JournalRecord(number=n, speaker=s, kind=k) for n, (s, k) in enumerate(records, 1)]
body = '# Acceptance of Todo service\n\n## Recommendation\n\nnot accepted\n\n## Journal\n\n1. factory: started.\n2. acceptance-reviewer: not accepted\n3. 2026-10-12 human: Too wide.\n4. 2026-10-12 human: Cut the second story.\n'
document = WorkItemDocument(state=AcceptanceState(stage='approval', stories=['F0001-S0001'], journal=journal), body=body)
print(refusal_reason(document, 'acceptance-reviewer'))
refused = book_refusal(document, role='acceptance-reviewer', on=date(2026, 10, 12), bill=bill([]))
print(refused.state.stage, refused.state.outcome)
line = 'Refused by the human on 2026-10-12: Too wide. Cut the second story.'
print(line in refused.body, refused.body.index(line) < refused.body.index('not accepted'))
print(entry_text(refused, 5) == 'done (pull request closed by the human); cost: ' + cost_line(bill([])))
accepted = book_merge(document, bill([]))
print(accepted.state.stage, accepted.state.outcome, entry_text(accepted, 5) == done_entry_text(bill([])))
"
```
Expect: five lines: `Too wide. Cut the second story.`, `done refused`, `True True`, `True`, then `done accepted True`.

## Log (append only)

1. 2026-10-12 human: created.
