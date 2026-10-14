---
stage: review
pr: 87
blocked: null
comments_seen: 2
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
18. When `set_labels` fails after the push, `handle` raises and the remote branch still holds the correction commit with the restored stage and the `move_back` entry.
19. A branch whose newest commit that touched the work item's file has a parent whose work item file cannot be read (for example invalid frontmatter) raises `CannotHandle` with kind `reject`, and nothing is written or posted.
20. make check stays green.
21. docs: `docs/operator-guide.md` describes the correction note and what the factory did when it moved a stage back; `docs/project-guide.md` states that the factory puts an illegal stage change back with a commit whose subject contains `moved back` and whose journal gains a `move_back` entry, that the `move_back` entry is what exempts the correction from the move rule, that the change is taken from the same source as the watcher's (the newest commit that touched the work item's file), and that only the work item's branch is written.

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
3. human (pull request comment, 2026-10-14): 1 A and 2 A: add both criteria before the two closing ones, as you worded them (the failing `set_labels` after the push raises and leaves the correction on the remote branch; a parent whose work item file cannot be read raises `CannotHandle` with kind `reject` and writes and posts nothing). The Interface stays as it is.
4. intake: accepted. Both additions come from log entry 3 (the human's answer: 1 A and 2 A); they are the human's edit carried in, not mine. I added criterion 18 (a failing `set_labels` after the push raises and the remote branch keeps the correction commit with the restored stage and the `move_back` entry) and criterion 19 (a parent whose work item file cannot be read raises `CannotHandle` with kind `reject` and writes and posts nothing). Both went before the two closing criteria, which are now 20 (`make check`) and 21 (`docs:`). The Interface is unchanged and the Assignment's meaning is unchanged.
   - Interface: names concrete modules and signatures (`post_texts.py` additions, `RejectHandler`). Its comments state exact texts, the post key, the recorded change and the subject marker.
   - Criteria: each is testable by one test function. Every Interface rule with a failing side now has a criterion for it: merge commit (12), no stage change (13), parent without the file (14), unreadable parent (19), a change that is itself a correction (16), a failing `set_labels` (18).
   - Demo: runnable with `uv run python -c`. The Expect line gives the three exact lines to compare against.
   - Architecture: the domain texts live in `factory.domain.post_texts`. The handler is in `factory.application.handlers` and uses Boundaries, WorkItemRecorder and HostingService, so no layer is crossed.
   - Scope: it matches the `reject` item of FEATURE.md and is not in its Out of scope.
5. tester: Wrote the red tests for every acceptance criterion except 20 (`make check`) and 21 (`docs:`).
   - criterion 1: tests/domain/test_correction_texts.py::test_the_move_back_entry_names_the_illegal_change (the Interface constant is checked by ::test_the_moved_back_marker_is_the_words_moved_back)
   - criterion 2: tests/domain/test_correction_texts.py::test_the_correction_note_says_the_stage_is_back_where_it_was
   - criterion 3: tests/application/handlers/test_reject.py::test_an_illegal_stage_change_is_put_back_by_a_new_commit_on_the_branch
   - criterion 4: tests/application/handlers/test_reject.py::test_the_correction_commit_subject_says_moved_back
   - criterion 5: tests/application/handlers/test_reject.py::test_the_correction_appends_one_move_back_entry_by_the_factory
   - criterion 6: tests/application/handlers/test_reject.py::test_with_a_pull_request_one_correction_note_is_posted_keyed_by_the_new_entry
   - criterion 7: tests/application/handlers/test_reject.py::test_without_a_pull_request_nothing_is_posted_and_the_stage_is_still_moved_back
   - criterion 8: tests/application/handlers/test_reject.py::test_a_claim_held_at_the_illegal_stage_is_cleared
   - criterion 9: tests/application/handlers/test_reject.py::test_a_kill_before_the_push_leaves_the_branch_and_a_second_run_corrects_once
   - criterion 10: tests/application/handlers/test_reject.py::test_a_kill_after_the_post_leaves_the_branch_and_a_second_run_posts_no_second_note
   - criterion 11: tests/application/handlers/test_reject.py::test_the_main_branch_keeps_its_head
   - criterion 12: tests/application/handlers/test_reject.py::test_a_merge_commit_is_refused_and_nothing_is_written_or_posted
   - criterion 13: tests/application/handlers/test_reject.py::test_a_commit_that_kept_the_stage_is_refused_and_nothing_is_written_or_posted
   - criterion 14: tests/application/handlers/test_reject.py::test_a_parent_without_the_work_item_file_is_refused_and_nothing_is_written_or_posted
   - criterion 15: tests/application/handlers/test_reject.py::test_an_illegal_change_followed_by_a_commit_to_another_file_is_moved_back
   - criterion 16: tests/application/handlers/test_reject.py::test_a_stage_change_that_is_itself_a_correction_is_refused
   - criterion 17: tests/application/handlers/test_reject.py::test_the_stage_label_is_set_again_only_with_a_pull_request (parametrized with and without a pull request)
   - criterion 18: tests/application/handlers/test_reject.py::test_a_failing_label_call_raises_and_the_correction_stays_on_the_branch
   - criterion 19: tests/application/handlers/test_reject.py::test_an_unreadable_parent_is_refused_and_nothing_is_written_or_posted

   Files created: tests/domain/test_correction_texts.py and tests/application/handlers/test_reject.py.

   Setup in the handler tests: the branch gets an opening commit at `tests`, then a legal commit at `doing`, then the illegal commit at `approval`, all through `human.push_file`, each state with the one `created` record. That makes the new entry number 2 and the post key `PostKey(work_item="F0001-S0001", kind="correction", n="2")`.
   - "Nothing is written or posted" (12, 13, 14, 16, 19) is checked as: remote branch head unchanged, `origin/main` unchanged, no factory posts and no labels on the pull request.
   - "No label call" (the no-pull-request case of 17) is checked by arming `hosting.fail_next("set_labels")`: any call would make `handle` raise.
   - "No uncommitted change" (9) is checked as `checkout.status().changes == []`.

   Run results:
   - `make test`: red on purpose, with two collection errors. `factory.domain.post_texts` has no `MOVED_BACK_MARKER` (nor the two text functions), and the module `factory.application.handlers.reject` does not exist.
   - `make lint`: green.
   - The type check was skipped, as the stage says.

   No criterion needed interpretation; nothing is open.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
6. coder: Built the reject handler. All 21 tests in tests/application/handlers/test_reject.py and tests/domain/test_correction_texts.py pass, and `make check` is green (coverage 99.23 %, reject.py fully covered).
   - `src/factory/domain/post_texts.py`: adds `MOVED_BACK_MARKER`, `move_back_entry_text` and `correction_note`. The entry text builds on the marker, so the two words appear only once in the code.
   - `src/factory/application/handlers/reject.py`: `RejectHandler(boundaries)`. `handle` takes the target and checks out the branch through `WorkItemRecorder`. It takes the change from `RemoteWorkItems(git, work_item_reader).last_stage_change(snapshot)` and raises `CannotHandle("reject", …)` when that is `None` or a correction, before anything is posted or written. It reads the checked-out document. With a pull request it posts `correction_note` keyed `PostKey(kind="correction", n=len(journal)+1)`. It then records the stage set back to `from_stage` with `claim=None` and one FACTORY `move_back` entry, under the subject `stage <new> -> <old>, moved back`. Finally, with a pull request, it calls `set_labels(labels_for(recorded state))`. Main is never checked out.
   - Commits: 4afc60e (feat) and 685c699 (refactor: the note posting moved into `_post_note` so that `handle` reads note → record → label).

   Main design decision: the claim is cleared directly in the state, as the Interface says and as `ClosedHandler._record_decision` already does. I did not go through `ClaimService.release`. I also did not give `RejectHandler` a pipeline definition: the legality judgement belongs to the watcher, and the handler only re-derives the change from the same source.

   Noticed but not touched: `_state_of` is defined privately in closed.py, questions.py and now reject.py. Sharing it in recording.py would be a separate clean-up. Nothing is open.

   `make check`: check: green
