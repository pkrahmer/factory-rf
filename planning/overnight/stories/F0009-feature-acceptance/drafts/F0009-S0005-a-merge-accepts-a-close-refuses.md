# A merge accepts, a close refuses

## Assignment (as of log entry 1)

The human's merge or close of an acceptance's pull request decides its result, whatever the reviewer recommended. A merge books the acceptance as `accepted`: the report moves with its cost records to the feature's `done` folder, its state says `done` and `accepted`, its journal gets one `done` entry with the acceptance's own cost, and the proposed stories that the merge brought into the feature's backlog stay there, untouched; the acceptance's branch is deleted. A close books it as `refused`: the human's comments and the close are first recorded in the report on its branch and pushed (R22), then the report is written to the main branch at `done` with the human's reason as the first paragraph under the recommendation, `refused` as the outcome and the cost records beside it, and the proposed stories, which were only on the branch, are dropped with it; the branch is deleted. Code never interprets the human's text: it is copied unchanged. Both handlers can be run again after a kill and book nothing twice. Merging an acceptance before it reached its approval, and the second acceptance of a feature, are the next story. Covers no handover condition alone (ST2.1, ST2.2 and R31 are built on this in the next story); keeps kept thing 2 (the human accepts by merging, and a refusal returns the human's text), kept thing 19 (the result is the human's act, not the recommendation) and kept thing 20 (each acceptance costed). The report and its sidecar move or are written; nothing else on the main branch changes.

## Interface

`src/factory/domain/acceptance.py` (grown)

```python
NO_REASON = "no reason given"

def book_merge(document: WorkItemDocument, cost_line: str) -> WorkItemDocument: ...
def book_refusal(document: WorkItemDocument, *, role: str, on: date, cost_line: str) -> WorkItemDocument: ...
def refusal_reason(document: WorkItemDocument, role: str) -> str: ...
```

`src/factory/application/acceptance.py` (grown)

```python
class AcceptanceMerged:
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...

class AcceptanceClosed:
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

`NewEntry` and `append_entry` are in `factory.domain.journal`; `insert_paragraph` and `sections` in `factory.domain.sections`; `work_item_path` and `cost_records_path` in `factory.domain.paths`.

Rules:

- `book_merge(document, cost_line)` needs a document whose state is an `AcceptanceState`, else `ValueError`. It sets `stage` to `DONE_STAGE`, `outcome` to `"accepted"`, `claim` and `blocked` to `None`, and keeps every other field; it appends one entry (speaker `factory`, kind `done`) with the text `done (pull request merged); cost: <cost_line>`.
- `refusal_reason(document, role)` is the visible text (`entry_text`), stripped, of every journal record with speaker `human` and kind `comment` that comes after the last record with `speaker == role` and kind `result` (after none, when there is no such record), in order, joined with one space; it is `NO_REASON` when there is none. The text is never interpreted.
- `book_refusal(document, role=..., on=..., cost_line=...)` needs an `AcceptanceState` too, else `ValueError`. It sets `stage` to `DONE_STAGE`, `outcome` to `"refused"`, `claim` and `blocked` to `None`, and keeps every other field. It makes `Refused by the human on <on as YYYY-MM-DD>: <refusal_reason(document, role)>` the first paragraph under the report's `## Recommendation` heading (`insert_paragraph`); a body without that section gets the section, holding only that paragraph, just before the `## Journal` section (at the end of the body when there is no such section). It appends one entry (speaker `factory`, kind `done`) with the text `done (pull request closed by the human); cost: <cost_line>`.
- Both handlers raise `ValueError` at construction when `definition.acceptance_stage` is `None`.
- `AcceptanceMerged.handle(event)` raises `CannotHandle(kind=<the event's kind>, reason=...)` with `"not a merged event"` for another kind, `"not an acceptance"` when the event has no work item or its id is a story's, and `"pull request is not merged"` when `event.pull_request` is `None` or its state is not `merged`; it changes nothing then. Otherwise it runs `Git.checkout("main", start_point="origin/main")`; reads the report at the snapshot's path (in `in-progress/`); when that file is there it writes `book_merge(document, <own cost line of the acceptance at ref "HEAD", read before the move>)` at the same file name in the feature's `done/` folder, moves the report and its cost records file (`cost_records_path`) with `Git.move` when the latter exists, commits and pushes `main` (`PushFailed` when the outcome is not `pushed`); when the report is already in `done/` and not in `in-progress/` it books nothing; when it is in neither it raises `CannotHandle(kind=<the event's kind>, reason="no report on the main branch")`. Last, it deletes the branch `work-item/<id>` on the remote when it is there and locally when it exists; a branch that is already gone is not an error.
- `AcceptanceClosed.handle(event)` raises `CannotHandle` with `"not a closed event"`, `"not an acceptance"` and `"pull request is not closed"` (no `event.pull_request`, or its state is not `closed`), checked in this order, and changes nothing then. Otherwise, in this order: (1) `Git.checkout(branch, start_point="origin/<branch>")` and read the report at the snapshot's path. (2) Record: every comment of `HostingService.list_comments(event.pull_request.number)` that is not by the factory and whose id is not in `comments_read` becomes, in id order, a journal entry (speaker `human`, kind `comment`, the comment's text, `on` the date of its `created_at` in UTC) and its id is added to `comments_read`; then one entry (speaker `human`, kind `close`, text `closed the pull request.`, `on` the date of `Clock.now()`) unless the journal already holds a record with speaker `human` and kind `close`. When anything was added, write the report, commit and push the branch (`PushFailed` when not pushed). (3) `Git.checkout("main", start_point="origin/main")`; unless the report's file name is already in `done/` on the main branch, write `book_refusal(document, role=<the role of acceptance_stage>, on=<the date of Clock.now()>, cost_line=<own cost line, ref "HEAD" of step 1>)` at the same file name in the feature's `done/` folder, copy the cost records file of the branch (when it has one) to `cost_records_path` of that path, commit and push `main`. (4) Delete the branch on the remote and locally, as the merged handler does. The proposed stories exist on the branch only; nothing of them is written to the main branch.

Tests: `tests/domain/test_acceptance_booking.py`, `tests/application/test_acceptance_merged.py`, `tests/application/test_acceptance_closed.py`; the `remote`, `checkout`, `human`, `hosting`, `clock`, `kill_points` and `boundaries` fixtures; the acceptance is opened with `AcceptanceService.open`, its pull request is created with `hosting.create_pull_request`, and the human acts with `human.merge`, `hosting.merge_by_human`, `hosting.close_by_human` and `hosting.add_human_comment`.

## Acceptance criteria

1. `book_merge` sets the stage to `done`, the outcome to `accepted`, `claim` and `blocked` to `None`, and leaves `stories`, `round`, `attempts`, `crashes`, `pull_request`, `comments_read` and `handed_over` as they were.
2. `book_merge` appends one record (speaker `factory`, kind `done`) whose number follows the journal's last, and whose visible text is `done (pull request merged); cost: <cost_line>`.
3. `book_merge` and `book_refusal` raise `ValueError` for a document whose state is a plain `WorkItemState`.
4. `refusal_reason` joins the texts of the human's `comment` records after the reviewer's last `result` record with one space, unchanged: the texts `Too wide.` and `Cut the second story.` give `Too wide. Cut the second story.`
5. `refusal_reason` ignores a `comment` record before the reviewer's last `result` record, a human `close` record and the factory's records.
6. `refusal_reason` is `no reason given` when no human comment follows the reviewer's last result, and uses every human comment when the journal has no result of the reviewer.
7. `book_refusal` sets the stage to `done`, the outcome to `refused`, `claim` and `blocked` to `None`, and leaves the other state fields as they were.
8. `book_refusal` makes `Refused by the human on 2026-10-12: <the reason>` the first paragraph of the `## Recommendation` section, above the reviewer's recommendation text, and leaves the rest of the body as it was.
9. `book_refusal` on a body without a `## Recommendation` section adds that section, holding only the refusal paragraph, just before the `## Journal` section.
10. `book_refusal` appends one record (speaker `factory`, kind `done`) whose visible text is `done (pull request closed by the human); cost: <cost_line>`.
11. After the human merged the acceptance's pull request, `AcceptanceMerged.handle` leaves on `origin/main` the report in the feature's `done/` folder, equal to `book_merge(<the merged report>, <its own cost line>)` as the writer renders it, and its cost records file beside it with the same records; neither file is left in `in-progress/`.
12. After `handle` the branch `work-item/<id>` is gone on the remote and locally, and a second `handle` of the same event makes no new commit and raises no error.
13. The commit `handle` makes on the main branch changes only the report's and the cost records file's paths: the proposed stories that the merge brought into the feature's backlog are still there, byte for byte.
14. A merge of an acceptance whose recommendation is `not accepted` is booked `accepted`: the recommendation text does not change the outcome.
15. `AcceptanceMerged.handle` raises `CannotHandle` with the four reasons the Interface gives (another kind of event, a story's event, a pull request that is not merged, no report on the main branch) and changes nothing.
16. After `kill_points.arm(KillPoint.AFTER_PUSH)` made the first `handle` raise `InjectedKill` right after the push of the main branch, a second `handle` leaves exactly one `done` record in the report, one new commit on `origin/main`, and the branch gone.
17. After the human commented twice and closed the pull request (`hosting.close_by_human`), `AcceptanceClosed.handle` records on `origin/<branch>` two `comment` records (speaker `human`, in comment order, dated with the date of each comment's `created_at`, the texts unchanged), adds their ids to `comments_read` in ascending order, and records one `close` record (speaker `human`, dated with the fixture clock's date).
18. A comment the factory posted (it carries the marker) is not recorded, and its id is not added to `comments_read`.
19. `handle` leaves on `origin/main` the report in the feature's `done/` folder equal to `book_refusal(<the recorded report>, role="acceptance-reviewer", on=<the fixture clock's date>, cost_line=<its own cost line>)` as the writer renders it, the branch's cost records file beside it (none when the branch has none), and nothing else: the proposed stories of the branch are not on `origin/main`.
20. After `handle` the branch `work-item/<id>` is gone on the remote and locally, and a second `handle` of the same event raises no error and makes no new commit.
21. After `kill_points.arm(KillPoint.BEFORE_PUSH, after=1)` made the first `handle` raise `InjectedKill` at the push of the main branch, `origin/<branch>` already holds the `comment` and `close` records; a second `handle` leaves exactly one `close` record, one report in `done/`, one new commit on `origin/main`, and the branch gone.
22. `AcceptanceClosed.handle` raises `CannotHandle` with the three reasons the Interface gives, in that order, and changes nothing.
23. `AcceptanceMerged` and `AcceptanceClosed` raise `ValueError` at construction when `definition.acceptance_stage` is `None`.
24. `make check` stays green.
25. docs: `docs/operator-guide.md` explains what the human's merge and close of an acceptance do (accepted or refused whatever the recommendation; where the report lands; that the reason is the human's comments unchanged; that a refusal drops the proposed stories and a merge keeps them in the backlog); `docs/decisions.md` records why each acceptance has its own report and cost records.

## Demo

```bash
uv run python -c "
from datetime import date
from factory.domain.acceptance import AcceptanceState, book_merge, book_refusal, refusal_reason
from factory.domain.journal import JournalRecord, entry_text
from factory.domain.work_item import WorkItemDocument
records = [('factory', 'started'), ('acceptance-reviewer', 'result'), ('human', 'comment'), ('human', 'comment')]
journal = [JournalRecord(number=n, speaker=s, kind=k) for n, (s, k) in enumerate(records, 1)]
body = '# Acceptance of Todo service\n\n## Recommendation\n\nnot accepted\n\n## Journal\n\n1. factory: started.\n2. acceptance-reviewer: not accepted\n3. 2026-10-12 human: Too wide.\n4. 2026-10-12 human: Cut the second story.\n'
document = WorkItemDocument(state=AcceptanceState(stage='approval', stories=['F0001-S0001'], journal=journal), body=body)
print(refusal_reason(document, 'acceptance-reviewer'))
refused = book_refusal(document, role='acceptance-reviewer', on=date(2026, 10, 12), cost_line='4 runs')
print(refused.state.stage, refused.state.outcome)
line = 'Refused by the human on 2026-10-12: Too wide. Cut the second story.'
print(line in refused.body, refused.body.index(line) < refused.body.index('not accepted'))
print(entry_text(refused, 5))
accepted = book_merge(document, '4 runs')
print(accepted.state.stage, accepted.state.outcome, entry_text(accepted, 5))
"
```
Expect: five lines: `Too wide. Cut the second story.`, `done refused`, `True True`, `done (pull request closed by the human); cost: 4 runs`, then `done accepted done (pull request merged); cost: 4 runs`.

## Log (append only)

1. 2026-10-12 human: created.
