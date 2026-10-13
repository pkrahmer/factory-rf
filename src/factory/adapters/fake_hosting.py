"""The one fake of the hosting service: pull requests, comments and posts in memory."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from factory.domain.errors import HostingServiceError
from factory.domain.git import CommitId
from factory.domain.hosting import (
    PostKey,
    PostOutcome,
    PullRequestComment,
    PullRequestState,
    PullRequestView,
    render_post,
)
from factory.domain.kill_points import KillPoint, KillPoints
from factory.domain.paths import LABEL_PREFIX

_OPERATIONS = frozenset(
    {
        "create_pull_request",
        "find_open_pull_request",
        "get_pull_request",
        "list_comments",
        "post_comment",
        "close",
        "reopen",
        "set_draft",
        "set_description",
        "set_labels",
    }
)
_FIRST_COMMENT_AT = datetime(2026, 10, 12, tzinfo=UTC)
_FACTORY_AUTHOR = "factory"


@dataclass
class _PullRequest:
    number: int
    branch: str
    title: str
    description: str
    draft: bool
    state: PullRequestState = "open"
    merge_commit: CommitId | None = None
    labels: list[str] = field(default_factory=list)
    comments: list[PullRequestComment] = field(default_factory=list)

    def view(self) -> PullRequestView:
        return PullRequestView(
            number=self.number,
            branch=self.branch,
            title=self.title,
            state=self.state,
            draft=self.draft,
            merge_commit=self.merge_commit,
            url=f"https://fake.invalid/pull/{self.number}",
        )


class FakeHostingService:
    """The hosting service in memory, with the operations a test uses to act as the human."""

    def __init__(self, kill_points: KillPoints | None = None) -> None:
        """Start without pull requests, comments or injected failures."""
        self._kill_points = kill_points
        self._pulls: dict[int, _PullRequest] = {}
        self._last_comment_id = 0
        self._failures_left: dict[str, int] = {}

    def create_pull_request(
        self, branch: str, title: str, body: str, *, draft: bool
    ) -> PullRequestView:
        """Open a pull request from `branch`, numbered after the last one."""
        self._fail_if_injected("create_pull_request")
        number = len(self._pulls) + 1
        pull = _PullRequest(
            number=number, branch=branch, title=title, description=body, draft=draft
        )
        self._pulls[number] = pull
        return pull.view()

    def find_open_pull_request(self, branch: str) -> PullRequestView | None:
        """The open pull request of `branch`, if there is one."""
        self._fail_if_injected("find_open_pull_request")
        for pull in self._pulls.values():
            if pull.branch == branch and pull.state == "open":
                return pull.view()
        return None

    def get_pull_request(self, number: int) -> PullRequestView:
        """The pull request `number` with its state and merge state."""
        self._fail_if_injected("get_pull_request")
        return self._pull("get_pull_request", number).view()

    def list_comments(self, number: int) -> list[PullRequestComment]:
        """The comments of pull request `number`, oldest first."""
        self._fail_if_injected("list_comments")
        return list(self._pull("list_comments", number).comments)

    def post_comment(self, number: int, text: str, key: PostKey) -> PostOutcome:
        """Post `text` with the marker and `key`; a post whose key exists is a no-op."""
        self._fail_if_injected("post_comment")
        pull = self._pull("post_comment", number)
        if any(comment.key == key for comment in pull.comments):
            return "already_posted"
        self._add_comment(pull, _FACTORY_AUTHOR, render_post(text, key))
        if self._kill_points is not None:
            self._kill_points.reach(KillPoint.AFTER_POST)
        return "posted"

    def close(self, number: int) -> None:
        """Close pull request `number` without merging."""
        self._fail_if_injected("close")
        self._pull("close", number).state = "closed"

    def reopen(self, number: int) -> None:
        """Reopen the closed pull request `number`."""
        self._fail_if_injected("reopen")
        self._pull("reopen", number).state = "open"

    def set_draft(self, number: int, draft: bool) -> None:
        """Mark pull request `number` as draft or as ready for review."""
        self._fail_if_injected("set_draft")
        self._pull("set_draft", number).draft = draft

    def set_description(self, number: int, body: str) -> None:
        """Replace the description of pull request `number`."""
        self._fail_if_injected("set_description")
        self._pull("set_description", number).description = body

    def set_labels(self, number: int, labels: Sequence[str]) -> None:
        """Replace the stage labels of pull request `number`, keeping every other label."""
        self._fail_if_injected("set_labels")
        pull = self._pull("set_labels", number)
        foreign = [label for label in pull.labels if not label.startswith(LABEL_PREFIX)]
        pull.labels = [*foreign, *labels]

    def add_human_comment(self, number: int, body: str, *, author: str = "human") -> int:
        """Comment on pull request `number` as `author` and return the comment's id."""
        return self._add_comment(self._pull("add_human_comment", number), author, body)

    def delete_comment(self, number: int, comment_id: int) -> None:
        """Remove the comment `comment_id` from pull request `number`."""
        pull = self._pull("delete_comment", number)
        kept = [comment for comment in pull.comments if comment.id != comment_id]
        if len(kept) == len(pull.comments):
            raise HostingServiceError("delete_comment", f"no comment {comment_id} on #{number}")
        pull.comments = kept

    def close_by_human(self, number: int) -> None:
        """Close pull request `number` as the human would, without merging."""
        self._pull("close_by_human", number).state = "closed"

    def merge_by_human(self, number: int, merge_commit: CommitId) -> None:
        """Merge pull request `number` as the human would, into `merge_commit`."""
        pull = self._pull("merge_by_human", number)
        pull.state = "merged"
        pull.merge_commit = merge_commit

    def fail_next(self, operation: str, *, times: int = 1) -> None:
        """Make the next `times` calls of the protocol operation `operation` fail."""
        if operation not in _OPERATIONS:
            raise ValueError(f"not a hosting-service operation: {operation}")
        if times < 1:
            raise ValueError(f"times must be at least 1, got {times}")
        self._failures_left[operation] = times

    def factory_posts(self, number: int) -> list[PullRequestComment]:
        """The comments of pull request `number` that carry the factory's marker, in order."""
        return [
            comment
            for comment in self._pull("factory_posts", number).comments
            if comment.by_factory
        ]

    def labels(self, number: int) -> list[str]:
        """The labels of pull request `number`."""
        return list(self._pull("labels", number).labels)

    def description(self, number: int) -> str:
        """The description of pull request `number`."""
        return self._pull("description", number).description

    def pull_requests(self) -> list[PullRequestView]:
        """Every pull request, whatever its state, ordered by number."""
        return [self._pulls[number].view() for number in sorted(self._pulls)]

    def _fail_if_injected(self, operation: str) -> None:
        left = self._failures_left.get(operation, 0)
        if left == 0:
            return
        self._failures_left[operation] = left - 1
        raise HostingServiceError(operation, "injected failure")

    def _pull(self, operation: str, number: int) -> _PullRequest:
        pull = self._pulls.get(number)
        if pull is None:
            raise HostingServiceError(operation, f"no pull request #{number}")
        return pull

    def _add_comment(self, pull: _PullRequest, author: str, body: str) -> int:
        self._last_comment_id += 1
        comment_id = self._last_comment_id
        pull.comments.append(
            PullRequestComment.from_body(
                id=comment_id,
                author=author,
                body=body,
                created_at=_FIRST_COMMENT_AT + timedelta(seconds=comment_id),
            )
        )
        return comment_id
