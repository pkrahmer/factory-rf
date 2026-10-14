---
stage: accept
pr: 82
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The human's comments copied by id

## Assignment (as of log entry 1)

Build the first handler service of F0007 and the plumbing that all its handlers share. The human's comments on a work item's pull request are copied into its journal by comment id, never by count: a comment is the human's when its body carries no factory marker (its author is kept but never used to decide), every new one becomes a dated `human` entry of kind `comment`, its id goes into `comments_read`, and the change is committed and pushed into the work item's branch before the factory posts, reopens or checks out anything else. The story also creates what every later handler of the feature uses: the error `CannotHandle` (a handler that cannot do its work raises it, so the dispatcher counts it), two helpers that take the work item and its pull request number out of an event, and a recorder that resets a branch to the remote's head, whatever a killed handler left uncommitted in the checkout, and commits and pushes a change (a rejected push is `PushFailed`). It covers GH3.1, GH3.2, R22 and R34 and builds R28's error type; it keeps kept thing 3 (the human's acts are recorded before the factory acts). No event handler is registered here: the comment handler is S0007, and the send-back (S0005) uses the copier too. No morning observation.

## Interface

`src/factory/domain/errors.py` (adds one type to the hierarchy)

```python
class CannotHandle(FactoryError):
    kind: str
    reason: str
    def __init__(self, kind: str, reason: str) -> None: ...
```

`src/factory/application/handlers/__init__.py`: the package `factory.application.handlers` exists (F0006-S0007 created it, with `run.py`, and `tests/application/handlers/__init__.py`); this story adds `recording.py` and `comments.py` to it and widens its module docstring to say that it holds the handlers of the events of a pull request, among them those of the human's acts on it.

`src/factory/application/handlers/recording.py`

```python
class Target(BaseModel):
    snapshot: WorkItemSnapshot
    state: WorkItemState
    pull_request: int | None

def target_of(event: Event) -> Target: ...
def require_pull_request(target: Target, kind: str) -> int: ...
def commit_subject(work_item: str, text: str) -> str: ...

class WorkItemRecorder:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def check_out(self, branch: str) -> None: ...
    def read(self, path: str) -> WorkItemDocument: ...
    def write(self, path: str, document: WorkItemDocument) -> None: ...
    def publish(self, branch: str, subject: str) -> CommitId: ...
    def record(self, branch: str, path: str, document: WorkItemDocument, subject: str) -> CommitId: ...
```

`src/factory/application/handlers/comments.py`

```python
class CopyResult(BaseModel):
    recorded: list[int]
    commit: CommitId | None

class CommentCopier:
    def __init__(self, boundaries: Boundaries) -> None: ...
    def unread(self, state: WorkItemState, pull_request: int) -> list[PullRequestComment]: ...
    def append(self, document: WorkItemDocument,
               comments: Sequence[PullRequestComment]) -> WorkItemDocument: ...
    def copy(self, snapshot: WorkItemSnapshot, pull_request: int,
             adjust: Callable[[WorkItemDocument, Sequence[PullRequestComment]], WorkItemDocument] | None = None
             ) -> CopyResult: ...
```

`Target` and `CopyResult` are frozen and forbid unknown keys.

Rules:

- `CannotHandle.__str__` is `cannot handle <kind>: <reason>`; `kind` is an event kind.
- `target_of` returns the event's work item as `snapshot`, that snapshot's `document.state` as `state` and the state's `pull_request`. With no work item (`Event` allows that only for the kinds `idle` and `acceptance_due`) it raises `CannotHandle(event.kind, "the event names no work item")`; with a snapshot whose document has no state it raises `CannotHandle(event.kind, "work item <id> has no state")`.
- `require_pull_request(target, kind)` returns `target.pull_request`, or raises `CannotHandle(kind, "work item <id> has no pull request")`.
- `commit_subject(work_item, text)` is `work item <work_item>: <text>`. Commit subjects are free text and nothing parses them.
- `WorkItemRecorder.check_out(branch)` calls `Git.reset_to("HEAD")` first, then `Git.checkout(branch, start_point="origin/<branch>")` (F0001's `GitCli.checkout` runs `git switch --force-create`, which git refuses while an uncommitted change touches a file that differs between `HEAD` and the start point), and then `Git.reset_to("origin/<branch>")`, so the local branch is the remote's and every local leftover, uncommitted or committed, is gone. `read` and `write` use the work item reader and writer on `boundaries.checkout / path`.
- `publish(branch, subject)` calls `Git.commit(subject)` and `Git.push(branch)` and returns the commit; any push outcome other than `pushed` raises `PushFailed(branch, outcome)`. `record(branch, path, document, subject)` is `write` followed by `publish`.
- `CommentCopier.unread` lists the pull request's comments and keeps those that are not `by_factory` and whose id is not in `state.comments_read`, in the order listed. The author is never looked at, and no text prefix such as `factory:` counts.
- `append` handles the comments in the order given. A comment with a non-blank body becomes `append_entry(document, NewEntry(speaker=HUMAN, kind="comment", text=<the body with every "\r\n" replaced by "\n">, on=<created_at date in UTC>))`; `NewEntry` removes the leading and trailing whitespace (F0002), so a two-line body keeps both lines and loses only its edges. A comment whose body is empty or only whitespace gets no entry. Every given id is added to `comments_read`, which stays sorted with no repeats.
- `copy` calls `check_out(snapshot.branch)`, reads the work item at `snapshot.path`, takes `unread` against the checked-out state and appends them. When none is unread it returns `CopyResult(recorded=[], commit=None)` and writes nothing. Otherwise it applies `adjust` (when given) to the appended document, together with the comments it appended, in the order given, and records with the subject `commit_subject(id, "comments from the pull request")`, and returns the ids newly added and the commit. Nothing else is done before the push.

Tests: `tests/application/handlers/test_recording.py` and `tests/application/handlers/test_comments.py`, with builders for a snapshot and an event in `tests/application/handlers/conftest.py`; `tests/domain/test_cannot_handle.py` (a new file: `tests/domain/test_errors.py` is F0001's) for criterion 1. The closed-model tests build the models through a variable typed `type[BaseModel]` and assign with `setattr`, the field's name in a variable. They use the shared fixtures `remote`, `checkout`, `human`, `hosting`, `kill_points`, `clock` and `boundaries`; git is real, in `tmp_path`, and the hosting service is the fake.

## Acceptance criteria

1. `CannotHandle("comment", "x")` is a `FactoryError` that carries `kind == "comment"` and `reason == "x"`, and its message is `cannot handle comment: x`.
2. `target_of(event)` returns a `Target` whose `snapshot` is the event's work item, whose `state` is that snapshot's `document.state` and whose `pull_request` is that state's `pull_request`.
3. `target_of` raises `CannotHandle` whose `kind` is the event's kind for an `idle` event (`kind == "idle"`, reason `the event names no work item`) and for a `comment` event whose snapshot's document has no state (reason `work item <id> has no state`): two cases, one test.
4. `require_pull_request(target, "ask")` returns the state's pull request number, and raises `CannotHandle` with kind `ask` and reason `work item <id> has no pull request` when the state has none.
5. `WorkItemRecorder.check_out(branch)` leaves the checkout's local branch at the head of `origin/<branch>`: a commit made locally and never pushed, an uncommitted change to a tracked file that differs between the local branch and `origin/<branch>` (which `git switch` alone would refuse), and an untracked file, are gone afterwards.
6. `WorkItemRecorder.record(branch, path, document, subject)` writes the document at the path, commits with the subject, pushes and returns the commit: the remote branch's head is that commit and the file at it parses to the document written.
7. `commit_subject("F0001-S0001", "x")` returns `work item F0001-S0001: x`.
8. `publish` raises `PushFailed` carrying the branch name and `outcome == "rejected"` when the remote branch has moved since `check_out` (the human pushed to it), and the human's commit stays the remote branch's head; with the remote's directory renamed away it raises `PushFailed` with `outcome == "unreachable"` (two cases, one test).
9. `CommentCopier.unread` leaves out a comment whose body carries the factory marker whatever its author, a marked comment by the login `human` included.
10. `unread` returns an unmarked comment by any author without looking at the author (a comment by `someone-else` is returned), and also an unmarked comment whose body starts with `factory:`.
11. `unread` leaves out every comment whose id is in `state.comments_read` and returns the others in the order the hosting service lists them.
12. `append` adds one journal entry per comment with a non-blank body, in the order given: speaker `human`, kind `comment`, text equal to the body with `\r\n` replaced by `\n` and leading and trailing whitespace removed (a two-line body keeps both lines; a body `a\r\nb\r\n` gives the text `a` and `b` on two lines, with no `\r` and no trailing newline), dated with the date of `created_at` in UTC, numbered after the entries already there, with a matching record in `state.journal`.
13. `append` adds the id of a comment with a blank body (empty, or only whitespace) to `comments_read` and adds no entry for it.
14. `append` leaves `comments_read` as the sorted union of the ids it held and the ids of the comments given, with no repeats.
15. `copy` records before it does anything else: afterwards the work item's remote branch holds the entries and the ids in `comments_read`, `CopyResult.recorded` lists the new ids and `CopyResult.commit` is the remote branch's head.
16. `copy` with nothing unread returns `CopyResult(recorded=[], commit=None)` and does not move the remote branch.
17. A human comment written after a first `copy`, with the factory posting its own comment in between, is recorded by the second `copy`: nothing that was counted earlier hides it (GH3.1).
18. After three comments were copied, deleting the second and adding a new comment makes the next `copy` record exactly the new comment: none is skipped and none is copied twice (GH3.2).
19. `adjust` is called once, with the document after the entries were appended and with the comments `copy` appended (the unread ones, in the order listed, blank ones included), and its result is written in the same commit (the remote branch gains exactly one commit); it is not called when nothing was recorded.
20. A kill at `before-push` during `copy` leaves the remote branch as it was, and a second `copy` after the kill records each comment exactly once.
21. `Target` and `CopyResult` are frozen and forbid unknown keys: each refuses an unknown key and an assignment to a field with `ValidationError`; `CopyResult` accepts a `commit` of 40 lower-case hex characters and refuses one of 39 characters and one of 40 with an upper-case letter.
22. make check stays green.
23. docs: `docs/project-guide.md` explains that a handler records the human's act in the work item's branch and pushes it before it acts, that comments are copied by id into the journal, and that the marker alone tells the factory's comments from the human's.

## Demo

```bash
uv run python -c "
from types import SimpleNamespace
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.handlers.comments import CommentCopier
from factory.domain.hosting import FACTORY_MARKER
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, WorkItemState
hosting = FakeHostingService()
pr = hosting.create_pull_request('work-item/F0001-S0001', 'F0001-S0001: demo', 'body', draft=True)
first = hosting.add_human_comment(pr.number, 'first answer')
second = hosting.add_human_comment(pr.number, 'factory: still the human', author='someone-else')
hosting.add_human_comment(pr.number, 'posted by the factory ' + FACTORY_MARKER)
records = [JournalRecord(number=1, speaker='human', kind='created')]
state = WorkItemState(stage='doing', pull_request=pr.number, journal=records)
copier = CommentCopier(SimpleNamespace(hosting=hosting))
unread = copier.unread(state, pr.number)
print([comment.id for comment in unread] == [first, second])
body = '# T\n\n## Journal\n\n1. 2026-10-12 human: created.\n'
document = copier.append(WorkItemDocument(state=state, body=body), unread)
print([(r.number, r.speaker, r.kind) for r in document.state.journal])
print(document.state.comments_read == sorted([first, second]))
"
```
Expect: three lines: `True`; then `[(1, 'human', 'created'), (2, 'human', 'comment'), (3, 'human', 'comment')]`; then `True`. The marked comment is left out, the `factory:` comment by another author is kept, and both kept comments are in `comments_read`.

```bash
uv run python -c "
from factory.domain.errors import CannotHandle, FactoryError
error = CannotHandle('comment', 'work item F0001-S0001 has no pull request')
print(isinstance(error, FactoryError), str(error))
"
```
Expect: one line, `True cannot handle comment: work item F0001-S0001 has no pull request`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: concrete modules and signatures (`domain/errors.py`, `application/handlers/recording.py` and `comments.py`); every rule (message format, target_of failures, subject, check_out sequence, publish outcomes, unread filter, append, copy) is stated precisely. The names the Demo and Interface use exist: `add_human_comment(number, body, *, author=)`, `FACTORY_MARKER`, `Git.reset_to`, `Git.checkout(start_point=)`, `PushFailed`.
   - Criteria: each is testable by one test function. Every rule has its failing side: no state or no work item (3), no pull request (4), a rejected or unreachable push (8), marked or already-read comments left out (9, 11), blank body (13), nothing unread (16), a kill before push (20), and the closed models refuse unknown keys, assignment and bad commit ids (21). Every behaviour in the Interface comments has a criterion: CRLF and strip (12), UTC date (12), sorted union (14), adjust (19).
   - Demo: both commands are runnable and each Expect line can be checked against the output.
   - Architecture: the handlers sit in `factory.application` and reach git, hosting and the work item reader and writer only through `Boundaries`. Nothing in the domain does I/O.
   - Scope: the story is within F0007's scope (shared plumbing and comments copied by id). It registers no handler, which matches the feature, and S0007 and S0005 are named as later users.
3. tester: Wrote red tests for every acceptance criterion except the closing two. `make lint` passes. The one `make test` run stopped at collection with 3 errors, one per new test module, because `factory.domain.errors.CannotHandle`, `factory.application.handlers.recording` and `factory.application.handlers.comments` do not exist yet.

   Criterion → test:
   - criterion 1: tests/domain/test_cannot_handle.py::test_cannot_handle_is_a_factory_error_that_names_kind_and_reason
   - criterion 2: tests/application/handlers/test_recording.py::test_the_target_of_an_event_is_its_work_item_state_and_pull_request
   - criterion 3: tests/application/handlers/test_recording.py::test_an_event_without_a_work_item_or_without_a_state_cannot_be_handled (parametrized: `idle`, `comment`)
   - criterion 4: tests/application/handlers/test_recording.py::test_a_pull_request_is_required_of_the_target
   - criterion 5: tests/application/handlers/test_recording.py::test_check_out_drops_every_local_leftover_and_stands_at_the_remote_head
   - criterion 6: tests/application/handlers/test_recording.py::test_record_writes_commits_and_pushes_the_document
   - criterion 7: tests/application/handlers/test_recording.py::test_a_commit_subject_names_the_work_item
   - criterion 8: tests/application/handlers/test_recording.py::test_publish_raises_push_failed_when_the_push_does_not_reach_the_remote (parametrized: `rejected` is the human's push after `check_out`; `unreachable` is the remote directory renamed away)
   - criterion 9: tests/application/handlers/test_comments.py::test_unread_leaves_out_every_comment_with_the_marker_whatever_its_author
   - criterion 10: tests/application/handlers/test_comments.py::test_unread_returns_unmarked_comments_of_any_author_and_any_prefix
   - criterion 11: tests/application/handlers/test_comments.py::test_unread_leaves_out_the_comments_read_and_keeps_the_listed_order
   - criterion 12: tests/application/handlers/test_comments.py::test_append_adds_one_dated_human_comment_entry_per_comment_in_order (a `+02:00` `created_at` whose UTC date is the day before; the body `a\r\nb\r\n`)
   - criterion 13: tests/application/handlers/test_comments.py::test_append_marks_a_blank_comment_read_without_an_entry (an empty body and a whitespace-only body)
   - criterion 14: tests/application/handlers/test_comments.py::test_append_keeps_comments_read_sorted_without_repeats
   - criterion 15: tests/application/handlers/test_comments.py::test_copy_records_and_pushes_the_comments_before_anything_else (also asserts that no factory post was made)
   - criterion 16: tests/application/handlers/test_comments.py::test_copy_with_nothing_unread_records_nothing
   - criterion 17: tests/application/handlers/test_comments.py::test_a_comment_after_a_factory_post_is_copied_by_the_next_copy
   - criterion 18: tests/application/handlers/test_comments.py::test_a_deleted_comment_neither_skips_nor_repeats_any_other
   - criterion 19: tests/application/handlers/test_comments.py::test_adjust_sees_the_appended_document_and_lands_in_the_same_commit (first not called on an empty copy, then called once with the answer and a blank comment; checks for exactly one new commit)
   - criterion 20: tests/application/handlers/test_comments.py::test_a_kill_before_the_push_leaves_the_remote_and_the_next_copy_records_once
   - criterion 21: tests/application/handlers/test_recording.py::test_a_target_is_frozen_and_forbids_unknown_keys, tests/application/handlers/test_comments.py::test_a_copy_result_is_frozen_and_forbids_unknown_keys, tests/application/handlers/test_comments.py::test_a_copy_result_commit_is_a_commit_id (40 lower-case accepted; 39, and 40 with one upper-case letter, refused)
   - criteria 22 and 23: no test (`make check`, docs).

   Files created:
   - tests/domain/test_cannot_handle.py
   - tests/application/handlers/conftest.py: fixtures `snapshot_of`, `state_with`, `event_of`, `pull_request` (a draft pull request on the fake), and `work_item` (the human pushes a rendered work item to `work-item/F0001-S0001` and the checkout fetches it)
   - tests/application/handlers/test_recording.py
   - tests/application/handlers/test_comments.py

   Unresolved imports: `factory.domain.errors.CannotHandle`, `factory.application.handlers.recording`, `factory.application.handlers.comments`.

   I asked no questions: no criterion needed interpreting. The tests expect `copy` not to fetch: the remote-tracking ref after its own push is enough, and the tests fetch after the human pushes.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Built the comment copier and the plumbing the handlers share. All tests pass without any change to them, and `make check` is green.
      - `src/factory/domain/errors.py`: adds `CannotHandle(kind, reason)`. Its message is `cannot handle <kind>: <reason>`.
      - `src/factory/application/handlers/__init__.py`: the module docstring now says the package holds the handlers of a pull request's events, among them those of the human's acts on it.
      - `src/factory/application/handlers/recording.py`: adds `Target` (frozen, forbids unknown keys), `target_of`, `require_pull_request`, `commit_subject` and `WorkItemRecorder`.
        - `check_out` does `reset_to("HEAD")`, then `checkout(branch, start_point="origin/<branch>")`, then `reset_to("origin/<branch>")`.
        - `publish` commits and pushes, and raises `PushFailed` for any outcome other than `pushed`. `record` is `write` followed by `publish`.
      - `src/factory/application/handlers/comments.py`: adds `CopyResult` (frozen, forbids unknown keys, `commit: CommitId | None`) and `CommentCopier`.
        - `unread` filters on `by_factory` and the ids in `comments_read`, and nothing else.
        - `append` adds one `human`/`comment` entry per non-blank body, with `\r\n` normalised and the date of `created_at` in UTC. It then sets `comments_read` to the sorted union of the ids.
        - `copy` checks out, reads, takes the unread comments, appends them, applies `adjust` and records with one commit. With nothing unread it returns early and writes nothing.
      - Commits: bdcd2b6 (feat) and aaf6309 (refactor). The refactor only renames the one-letter variable in the `unread` filter to `comment`. Apart from that I found nothing to clean up in the diff.

      Main decision: `append` sets the new `comments_read` with `model_copy(update=...)` on the appended document. The other way was to build a new `WorkItemState` through validation; I rejected it because the list is already sorted and has no repeats by construction. A private helper `_state_of` raises `ValueError` when a document has no state. It guards a case that `copy` cannot reach after `check_out`, so no test covers it.

      Noticed, not touched: `copy` does not fetch. It relies on the remote-tracking ref, as the tester noted. Whoever calls it later (S0005, S0007) must have fetched first. The docs criterion (23) is left to the documenter.

   `make check`: check: green
5. reviewer: No findings.

   - Criteria 1–21: each has a test, and each test checks the criterion it is named after. Some details I checked:
     - The check_out test leaves a local commit that was never pushed, an uncommitted change to a file that differs from `origin/<branch>`, and an untracked file. It checks that all three are gone.
     - The append test uses a `+02:00` `created_at` that falls on the previous day in UTC, and the body `a\r\nb\r\n`.
     - The adjust test checks that `adjust` is not called when nothing is unread, that it receives the blank comment as well, and that the branch gains exactly one commit.
     - The kill test checks that the remote has not moved and that the second copy records each comment once.
     - The closed-model tests use a variable typed `type[BaseModel]` and `setattr`. The commit-id test covers 40 lower-case characters (accepted), 39 characters, and 40 with an upper-case letter (both refused).
   - Every rule in the Interface has its failing side tested: no work item, no state, no pull request, a rejected push, an unreachable push, marked comments, comments already read, blank bodies, nothing unread.
   - The coder's entry reports `make check` green.
   - Architecture: `recording.py` and `comments.py` import only `factory.application.boundaries` and `factory.domain`. They reach git, hosting and the work-item reader and writer only through `Boundaries`. `CannotHandle` is pure domain code.
   - Security: no secrets and no command strings. No suppression markers were added.
   - Quality: the code matches the Interface step by step: the `check_out` sequence, `publish` raising `PushFailed` for any outcome other than `pushed`, `unread` filtering only on `by_factory` and the ids already read, the sorted union in `comments_read`, and the early return in `copy`. Public names have docstrings and the comments explain why.
   - Hygiene: the log explains the main decision (updating `comments_read` with `model_copy`, rejected: building a new state through validation). Assignment matches what was built, and criterion 23 still describes what the documenter has to write.
   - Open, not a finding: the coder says `_state_of` in `comments.py` cannot be reached. It can be: `copy` reaches it when the checked-out work item has no state, and `append` reaches it when called directly with a stateless document. It then raises `ValueError`, not `CannotHandle`. The Interface does not cover this case. S0005 and S0007 call `target_of` first, which already needs a state. Also open: `copy` does not fetch, so the stories that call it must fetch first.
6. documenter: wrote criterion 23 in one file.
   - `docs/project-guide.md`:
     - *Errors* now has `CannotHandle`.
     - A new section "Recording the human's act" covers `target_of`, `require_pull_request`, `commit_subject` and `WorkItemRecorder`. It says a handler records the act in the work item's branch and pushes it before it acts. It also says `check_out` does not fetch, so the caller must have.
     - A new section "Comments are copied by id" covers `CommentCopier`: only the marker separates the factory's comments from the human's, comments are tracked by id and not by count, and it lists the rules for `append` and `copy`. It also says no handler is registered yet.
   - Cross-read and still true: README, `docs/operator-guide.md` and the "handlers of the events" section (`NOT_YET_HANDLED` is unchanged, since this story registers nothing). The diff against the Interface found no contradiction.
   - Not run: I did not run the two demo commands, and the new text has no runnable examples. `make check` is green.
   - Seen, not touched: `CommentCopier._state_of` raises `ValueError` for a stateless document. The reviewer noted this and the Interface doesn't cover it. I documented it as it is.

   `make check`: check: green
7. demo: both commands were run from the repository root, exactly as written. Both met their `Expect:` line and there are no findings.

   1. Comment copier (`unread` and `append` on the fake hosting service). Exit 0.
      ```
      True
      [(1, 'human', 'created'), (2, 'human', 'comment'), (3, 'human', 'comment')]
      True
      ```
      This met Expect. `unread` returned exactly the unmarked comment and the `factory:` comment by `someone-else`, in the order listed, and left out the marked one (criteria 9 and 10). `append` numbered the two `human`/`comment` entries after the existing entry (criterion 12). `comments_read` is the sorted list of both ids (criterion 14).

   2. `CannotHandle`. Exit 0.
      ```
      True cannot handle comment: work item F0001-S0001 has no pull request
      ```
      This met Expect. It is a `FactoryError` and its message has the form `cannot handle <kind>: <reason>` (criterion 1).

   Checked against the acceptance criteria: nothing in either output contradicts any criterion. The demo does not exercise the git-backed parts (`check_out`, `record`, `publish`, `copy`, criteria 5, 6, 8 and 15 to 20). The tests cover those, and neither command contradicts them.

   Still open, carried from the reviewer's and documenter's entries and not a demo finding: `CommentCopier._state_of` raises `ValueError` rather than `CannotHandle` for a document without a state. Also, `copy` does not fetch, so its later callers (S0005, S0007) must fetch first.
