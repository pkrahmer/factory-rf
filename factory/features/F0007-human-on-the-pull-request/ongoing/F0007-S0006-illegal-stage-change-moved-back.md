---
stage: ready
pr: 87
blocked: asked
comments_seen: 1
round: 0
attempts: 0
---
# An illegal stage change moved back

## Assignment (as of log entry 1)

Build the handler of `reject` events. When the newest commit on a work item's branch that touched its file changed the stage in a way the pipeline definition does not allow (the watcher raises `reject` for it; a later commit that touches only another file does not hide the change), the handler puts the stage back with a new commit on that branch: the stage returns to the one before the change, a `move_back` entry says what happened (that journal record is what exempts the correction from the next evaluation's rule, F0006-S0005, so it cannot itself be rejected), the commit's subject contains `moved back` for the human who reads the history, and, when the work item has a pull request, one correction note is posted there and its label is set again. The note is posted first and carries a key made from the number the new entry will get, so a kill at any point leaves no duplicate note and no half-written branch, and the correction is made again by the next tick from the same event. Only the work item's branch is ever written; the main branch stays as it was, so a killed correction cannot leave it dirty. It covers GH3.5 and R22. No morning observation.

## Interface

`src/factory/domain/post_texts.py` (adds)

```python
MOVED_BACK_MARKER = "moved back"
def move_back_entry_text(old: str, new: str) -> str: ...
def correction_note(old: str, new: str) -> str: ...
```

`src/factory/application/handlers/reject.py`

```python
class RejectHandler(Handler):      # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries) -> None: ...
    def handle(self, event: Event) -> None: ...
```

Rules:

- `move_back_entry_text(old, new)` is `illegal stage change <old> -> <new>, moved back.` `correction_note(old, new)` is `The stage was changed from <old> to <new>, which factory/pipeline.yml does not allow; it is back at <old>.`
- `handle` takes `target_of(event)` and calls `WorkItemRecorder.check_out(snapshot.branch)`. The illegal change is the one the watcher judged, taken from the same source: `RemoteWorkItems(boundaries.git, boundaries.work_item_reader).last_stage_change(snapshot)` (F0006-S0005), the stage change of the newest commit beyond `origin/main` that touched the work item's file, whatever commits that touched other files came after it. `old` is its `from_stage` and `new` its `to_stage`. A `None` (no change: a merge commit, the opening commit, a parent without the work item file, equal stages, an unreadable parent) or a change whose `correction` is true raises `CannotHandle("reject", ...)`, and nothing is written or posted.
- When the checked-out state has a pull request, `handle` posts `correction_note(old, new)` before it records, with `PostKey(work_item=<id>, kind="correction", n=str(len(state.journal) + 1))`: the number the new entry will get. Without a pull request nothing is posted.
- The recorded change: `stage` is `old`; `claim` is set to `None` (a claim is always for the work item's current stage, which is `new` at the head of the branch, so it never outlives the move back; set directly in the state, not through `ClaimService.release`, which is built for an instance name and a pipeline definition that `RejectHandler(boundaries)` does not hold; `tests/test_claim_ownership.py` forbids only building a claim and judging a lease outside the service); one entry is appended, `NewEntry(speaker=FACTORY, kind="move_back", text=move_back_entry_text(old, new))`. It is recorded with `WorkItemRecorder.record` and the subject `commit_subject(id, "stage <new> -> <old>, " + MOVED_BACK_MARKER)`. The subject's marker is for the reader of the history; the exemption from the move rule is the `move_back` record (F0006-S0005 reads no commit subject).
- When the state has a pull request, after the push `HostingService.set_labels(number, labels_for(<the recorded state>))` (`factory.domain.labels`, F0005-S0007), so that the label does not keep the illegal stage until the next stage finishes. A failing `set_labels` raises; the correction stays recorded.
- The main branch is never checked out, written or pushed by this handler.

Tests: `tests/domain/test_correction_texts.py` (a new file: `tests/domain/test_post_texts.py` is F0003-S0003's) and `tests/application/handlers/test_reject.py`. The tests first push a legal commit that touches the work item's file to the branch (so that the illegal one is not the opening commit, whose parent is on `origin/main`), then make the illegal commit with `human.push_file` on the work item's branch, with a work item file whose state names the new stage.

## Acceptance criteria

1. `move_back_entry_text("doing", "approval")` is `illegal stage change doing -> approval, moved back.`
2. `correction_note("doing", "approval")` is `The stage was changed from doing to approval, which factory/pipeline.yml does not allow; it is back at doing.`
3. After `RejectHandler.handle` for a branch whose newest commit that touched the work item's file changed the stage from `doing` to `approval` and is the branch's head, the head of the remote branch is a new commit on top of the illegal one, and the work item file at it has `stage == "doing"`.
4. The new commit's subject contains `MOVED_BACK_MARKER`.
5. The journal gains one entry numbered after the last: speaker `factory`, kind `move_back`, text `move_back_entry_text("doing", "approval")`, with a matching record in `state.journal`.
6. With a pull request, one factory post exists afterwards: text `correction_note("doing", "approval")`, key `PostKey(kind="correction", n=<the number of the new entry>)`.
7. Without a pull request, nothing is posted and the stage is still moved back.
8. A claim held at the illegal stage (its `stage` is the new stage, as `WorkItemState` requires) is cleared: the work item file at the new commit has `claim` unset and `stage` equal to the restored stage.
9. A kill at `before-push` leaves the remote branch at the illegal commit, `origin/main` unchanged and no uncommitted change in the checkout; the correction note is already posted; handling the event again adds exactly one entry and leaves exactly one note (GH3.5).
10. A kill at `after-post` leaves one note and an unchanged remote branch; handling the event again leaves one note and one new entry.
11. `origin/main` has the same head after `handle` as before it.
12. A branch whose newest commit that touched the work item's file is a merge commit (two parents) raises `CannotHandle` with kind `reject`, and nothing is written or posted.
13. A branch whose newest commit that touched the work item's file did not change the stage raises `CannotHandle` with kind `reject`, and nothing is written or posted.
14. A branch whose newest commit that touched the work item's file has a parent without the work item file raises `CannotHandle` with kind `reject`, and nothing is written or posted.
15. An illegal stage change followed by a commit that touches only another file (the head is that later commit) is moved back all the same: the remote branch's head is a new commit on top of the later one, the work item file at it has the stage before the illegal change, and one `move_back` entry is added.
16. A stage change that is itself a correction (its commit appended a `move_back` record) raises `CannotHandle` with kind `reject`, and nothing is written or posted.
17. With a pull request, afterwards `hosting.labels(<pull request>)` is `["stage:doing"]` for a change from `doing` to `approval`; without one no label call is made (two cases, one test).
18. make check stays green.
19. docs: `docs/operator-guide.md` describes the correction note and what the factory did when it moved a stage back; `docs/project-guide.md` states that the factory puts an illegal stage change back with a commit whose subject contains `moved back` and whose journal gains a `move_back` entry, that the `move_back` entry is what exempts the correction from the move rule, that the change is taken from the same source as the watcher's (the newest commit that touched the work item's file), and that only the work item's branch is written.

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
2. intake: 1. The Interface says "A failing `set_labels` raises; the correction stays recorded." No criterion tests it. Two coders could read it two ways and both pass. Option A (my choice): add a criterion before the two closing ones: "When `set_labels` fails after the push, `handle` raises and the remote branch still holds the correction commit with the restored stage and the `move_back` entry." Option B: drop the sentence from the Interface.
   2. The Interface lists an unreadable parent among the cases that raise `CannotHandle("reject", ...)`. Criterion 14 covers only a parent without the work item file. Option A (my choice): add a criterion for a parent whose work item file cannot be read (for example invalid frontmatter) that raises `CannotHandle` with kind `reject` and writes and posts nothing. Option B: drop "an unreadable parent" from the Interface list, since F0006-S0005 owns that case.
   The other checks passed: Interface, Demo, architecture and scope.
