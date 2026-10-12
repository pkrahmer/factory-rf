# An illegal stage change moved back

## Assignment (as of log entry 1)

Build the handler of `reject` events. When the last commit on a work item's branch changed its stage in a way the pipeline definition does not allow (the watcher raises `reject` for it), the handler puts the stage back with a new commit on that branch: the stage returns to the one in the parent commit, a `move_back` entry says what happened, the commit's subject contains `moved back` (which exempts it from the next evaluation's rule, so the correction cannot itself be rejected), and, when the work item has a pull request, one correction note is posted there. The note is posted first and carries a key made from the number the new entry will get, so a kill at any point leaves no duplicate note and no half-written branch, and the correction is made again by the next tick from the same event. Only the work item's branch is ever written; the main branch stays as it was, so a killed correction cannot leave it dirty. It covers GH3.5 and R22. No morning observation.

## Interface

`src/factory/domain/post_texts.py` (adds)

```python
MOVED_BACK_MARKER = "moved back"
def move_back_entry_text(old: str, new: str) -> str: ...
def correction_note(old: str, new: str) -> str: ...
```

`src/factory/application/handlers/reject.py`

```python
class RejectHandler:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def handle(self, event: Event) -> None: ...
```

Rules:

- `move_back_entry_text(old, new)` is `illegal stage change <old> -> <new>, moved back.` `correction_note(old, new)` is `The stage was changed from <old> to <new>, which factory/pipeline.yml does not allow; it is back at <old>.`
- `handle` takes `target_of(event)` and calls `WorkItemRecorder.check_out(snapshot.branch)`. The illegal change is the head commit of `origin/<branch>` (`Git.log`, first entry). That commit must have exactly one parent; `old` is the stage of the work item file at the parent (`Git.show_file(parent, path)` parsed with the reader) and `new` is the stage in the checked-out file. A head with another number of parents, a parent without the work item file, or equal stages raises `CannotHandle("reject", ...)`, and nothing is written or posted.
- When the checked-out state has a pull request, `handle` posts `correction_note(old, new)` before it records, with `PostKey(work_item=<id>, kind="correction", n=str(len(state.journal) + 1))`: the number the new entry will get. Without a pull request nothing is posted.
- The recorded change: `stage` is `old`; `claim` is set to `None` when its `stage` is not `old` and kept otherwise; one entry is appended, `NewEntry(speaker=FACTORY, kind="move_back", text=move_back_entry_text(old, new))`. It is recorded with `WorkItemRecorder.record` and the subject `commit_subject(id, "stage <new> -> <old>, " + MOVED_BACK_MARKER)`.
- The main branch is never checked out, written or pushed by this handler.

Tests: `tests/domain/test_post_texts.py` and `tests/application/handlers/test_reject.py`. The tests make the illegal commit with `human.push_file` on the work item's branch, with a work item file whose state names the new stage.

## Acceptance criteria

1. `move_back_entry_text("doing", "approval")` is `illegal stage change doing -> approval, moved back.`
2. `correction_note("doing", "approval")` is `The stage was changed from doing to approval, which factory/pipeline.yml does not allow; it is back at doing.`
3. After `RejectHandler.handle` for a branch whose head commit changed the stage from `doing` to `approval`, the head of the remote branch is a new commit on top of the illegal one, and the work item file at it has `stage == "doing"`.
4. The new commit's subject contains `MOVED_BACK_MARKER`.
5. The journal gains one entry numbered after the last: speaker `factory`, kind `move_back`, text `move_back_entry_text("doing", "approval")`, with a matching record in `state.journal`.
6. With a pull request, one factory post exists afterwards: text `correction_note("doing", "approval")`, key `PostKey(kind="correction", n=<the number of the new entry>)`.
7. Without a pull request, nothing is posted and the stage is still moved back.
8. A claim whose stage is not the restored stage is cleared, and a claim whose stage is the restored stage is kept (two cases, one test).
9. A kill at `before-push` leaves the remote branch at the illegal commit, `origin/main` unchanged and no uncommitted change in the checkout; the correction note is already posted; handling the event again adds exactly one entry and leaves exactly one note (GH3.5).
10. A kill at `after-post` leaves one note and an unchanged remote branch; handling the event again leaves one note and one new entry.
11. `origin/main` has the same head after `handle` as before it.
12. A head commit with two parents (a merge) raises `CannotHandle` with kind `reject`, and nothing is written or posted.
13. A head commit that did not change the stage raises `CannotHandle` with kind `reject`, and nothing is written or posted.
14. A head commit whose parent has no work item file raises `CannotHandle` with kind `reject`, and nothing is written or posted.
15. make check stays green.
16. docs: `docs/operator-guide.md` describes the correction note and what the factory did when it moved a stage back; `docs/project-guide.md` states that the factory puts an illegal stage change back with a commit whose subject contains `moved back`, that the commit is exempt from the move rule, and that only the work item's branch is written.

## Demo

```bash
uv run python -c "
from factory.domain.post_texts import MOVED_BACK_MARKER, correction_note, move_back_entry_text
print(MOVED_BACK_MARKER)
print(move_back_entry_text('doing', 'approval'))
print(correction_note('doing', 'approval'))
"
```
Expect: three lines: `moved back`; `illegal stage change doing -> approval, moved back.`; `The stage was changed from doing to approval, which factory/pipeline.yml does not allow; it is back at doing.`

## Log (append only)

1. 2026-10-12 human: created.
