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
