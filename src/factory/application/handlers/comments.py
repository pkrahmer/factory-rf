"""The human's comments on a pull request, copied into the work item's journal by comment id."""

from collections.abc import Callable, Sequence
from datetime import UTC

from pydantic import BaseModel, ConfigDict

from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.recording import (
    WorkItemRecorder,
    commit_subject,
    require_pull_request,
    target_of,
)
from factory.domain.answers import unblock
from factory.domain.events import Event
from factory.domain.git import CommitId
from factory.domain.hosting import PostKey, PullRequestComment
from factory.domain.journal import HUMAN, NewEntry, append_entry, last_record
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot, WorkItemState

Adjust = Callable[[WorkItemDocument, Sequence[PullRequestComment]], WorkItemDocument]


class CopyResult(BaseModel):
    """What a copy recorded: the ids newly read and the commit pushed, or None for no change."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    recorded: list[int]
    commit: CommitId | None


def _state_of(document: WorkItemDocument) -> WorkItemState:
    if document.state is None:
        raise ValueError("a work item without a state has no comments to read")
    return document.state


def _entry_of(comment: PullRequestComment) -> NewEntry:
    return NewEntry(
        speaker=HUMAN,
        kind="comment",
        text=comment.body.replace("\r\n", "\n"),
        on=comment.created_at.astimezone(UTC).date(),
    )


class CommentCopier:
    """Copies the human's unread comments into the journal and pushes them before anything else."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Read comments from the boundaries' hosting service and record through their git."""
        self._boundaries = boundaries

    def unread(self, state: WorkItemState, pull_request: int) -> list[PullRequestComment]:
        """Return the human's comments whose ids are not yet read, in the order listed.

        Only the marker tells the factory's comments apart; the author is never looked at.
        """
        read = set(state.comments_read)
        comments = self._boundaries.hosting.list_comments(pull_request)
        return [
            comment for comment in comments if not comment.by_factory and comment.id not in read
        ]

    def append(
        self, document: WorkItemDocument, comments: Sequence[PullRequestComment]
    ) -> WorkItemDocument:
        """Append one human entry per non-blank comment and mark every comment read."""
        appended = document
        for comment in comments:
            if comment.body.strip():
                appended = append_entry(appended, _entry_of(comment))
        state = _state_of(appended)
        read = sorted({*state.comments_read, *(comment.id for comment in comments)})
        return appended.model_copy(
            update={"state": state.model_copy(update={"comments_read": read})}
        )

    def copy(
        self, snapshot: WorkItemSnapshot, pull_request: int, adjust: Adjust | None = None
    ) -> CopyResult:
        """Record the unread comments in the work item's branch and push them.

        `adjust`, when given, changes the appended document within the same commit.
        """
        recorder = WorkItemRecorder(self._boundaries)
        recorder.check_out(snapshot.branch)
        document = recorder.read(snapshot.path)
        unread = self.unread(_state_of(document), pull_request)
        if not unread:
            return CopyResult(recorded=[], commit=None)
        appended = self.append(document, unread)
        if adjust is not None:
            appended = adjust(appended, unread)
        subject = commit_subject(snapshot.id, "comments from the pull request")
        commit = recorder.record(snapshot.branch, snapshot.path, appended, subject)
        return CopyResult(recorded=[comment.id for comment in unread], commit=commit)


def _question_post(
    work_item: str, document: WorkItemDocument, listed: Sequence[PullRequestComment]
) -> PullRequestComment | None:
    """Return the factory's post of the question the document waits on, if it is posted."""
    state = _state_of(document)
    question = last_record(document, kind="question")
    if state.blocked is None or question is None:
        return None
    key = PostKey(work_item=work_item, kind=state.blocked, n=str(question.number))
    return next((comment for comment in listed if comment.by_factory and comment.key == key), None)


def _answer_after(post: PullRequestComment, comments: Sequence[PullRequestComment]) -> bool:
    return any(comment.body.strip() and comment.id > post.id for comment in comments)


class CommentHandler(Handler):
    """Records the human's comments; one written after the posted question ends the wait."""

    def __init__(self, boundaries: Boundaries) -> None:
        """Read and record through the boundaries' hosting service and git."""
        self._boundaries = boundaries

    def handle(self, event: Event) -> None:
        """Copy the unread comments and, for a waiting work item, end the wait they answer."""
        target = target_of(event)
        pull_request = require_pull_request(target, "comment")
        copier = CommentCopier(self._boundaries)
        if target.state.blocked is None:
            copier.copy(target.snapshot, pull_request)
            return
        listed = self._boundaries.hosting.list_comments(pull_request)
        work_item = target.snapshot.id

        # A comment the human wrote before the question was posted cannot answer it.
        def adjust(
            document: WorkItemDocument, comments: Sequence[PullRequestComment]
        ) -> WorkItemDocument:
            post = _question_post(work_item, document, listed)
            if post is None or not _answer_after(post, comments):
                return document
            return document.model_copy(update={"state": unblock(_state_of(document))})

        copier.copy(target.snapshot, pull_request, adjust)
