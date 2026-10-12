"""The hosting-service client on PyGithub: the one route to the hosting service's API."""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime

from github import GithubException
from github.IssueComment import IssueComment
from github.PullRequest import PullRequest
from github.Repository import Repository

from factory.domain.errors import HostingServiceError
from factory.domain.hosting import (
    PostKey,
    PostOutcome,
    PullRequestComment,
    PullRequestState,
    PullRequestView,
    render_post,
)
from factory.domain.kill_points import KillPoint, KillPoints
from factory.domain.paths import LABEL_PREFIX, MAIN_BRANCH


@contextmanager
def _failing_as(operation: str) -> Iterator[None]:
    # A connection error is an `OSError`; everything else is a bug and passes through.
    try:
        yield
    except (GithubException, OSError) as error:
        raise HostingServiceError(operation, str(error)) from error


def _state(pull: PullRequest) -> PullRequestState:
    if pull.merged:
        return "merged"
    return "open" if pull.state == "open" else "closed"


def _view(pull: PullRequest) -> PullRequestView:
    state = _state(pull)
    # GitHub reports a test-merge commit for open pull requests; only a merge counts.
    merge_commit = pull.merge_commit_sha if state == "merged" else None
    return PullRequestView(
        number=pull.number,
        branch=pull.head.ref,
        title=pull.title,
        state=state,
        draft=pull.draft,
        merge_commit=merge_commit,
        url=pull.html_url,
    )


def _as_utc(moment: datetime) -> datetime:
    return moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment


def _comment(comment: IssueComment) -> PullRequestComment:
    return PullRequestComment.from_body(
        id=comment.id,
        author=comment.user.login,
        body=comment.body,
        created_at=_as_utc(comment.created_at),
    )


def _comments(pull: PullRequest) -> list[PullRequestComment]:
    comments = [_comment(comment) for comment in pull.get_issue_comments()]
    return sorted(comments, key=lambda comment: comment.id)


class PyGithubHostingService:
    """The hosting service on PyGithub; every failing call raises `HostingServiceError`."""

    def __init__(self, repository: Repository, kill_points: KillPoints | None = None) -> None:
        """Keep the repository without touching it, so that construction never calls out."""
        self._repository = repository
        self._kill_points = kill_points

    def create_pull_request(
        self, branch: str, title: str, body: str, *, draft: bool
    ) -> PullRequestView:
        """Open a pull request from `branch` to the main branch, as draft or ready."""
        with _failing_as("create_pull_request"):
            pull = self._repository.create_pull(
                base=MAIN_BRANCH, head=branch, title=title, body=body, draft=draft
            )
            return _view(pull)

    def find_open_pull_request(self, branch: str) -> PullRequestView | None:
        """The open pull request of `branch`, if there is one."""
        with _failing_as("find_open_pull_request"):
            head = f"{self._repository.owner.login}:{branch}"
            for pull in self._repository.get_pulls(state="open", head=head):
                return _view(pull)
            return None

    def get_pull_request(self, number: int) -> PullRequestView:
        """The pull request `number` with its state and merge state."""
        with _failing_as("get_pull_request"):
            return _view(self._repository.get_pull(number))

    def list_comments(self, number: int) -> list[PullRequestComment]:
        """The comments of pull request `number`, oldest first."""
        with _failing_as("list_comments"):
            return _comments(self._repository.get_pull(number))

    def post_comment(self, number: int, text: str, key: PostKey) -> PostOutcome:
        """Post `text` with the marker and `key`; a post whose key exists is a no-op."""
        with _failing_as("post_comment"):
            pull = self._repository.get_pull(number)
            if any(comment.key == key for comment in _comments(pull)):
                return "already_posted"
            pull.create_issue_comment(render_post(text, key))
        if self._kill_points is not None:
            self._kill_points.reach(KillPoint.AFTER_POST)
        return "posted"

    def close(self, number: int) -> None:
        """Close pull request `number` without merging."""
        with _failing_as("close"):
            self._repository.get_pull(number).edit(state="closed")

    def reopen(self, number: int) -> None:
        """Reopen the closed pull request `number`."""
        with _failing_as("reopen"):
            self._repository.get_pull(number).edit(state="open")

    def set_draft(self, number: int, draft: bool) -> None:
        """Mark pull request `number` as draft or as ready for review."""
        with _failing_as("set_draft"):
            pull = self._repository.get_pull(number)
            if draft:
                pull.convert_to_draft()
            else:
                pull.mark_ready_for_review()

    def set_description(self, number: int, body: str) -> None:
        """Replace the description of pull request `number`."""
        with _failing_as("set_description"):
            self._repository.get_pull(number).edit(body=body)

    def set_labels(self, number: int, labels: Sequence[str]) -> None:
        """Replace the stage labels of pull request `number`, keeping every other label."""
        with _failing_as("set_labels"):
            pull = self._repository.get_pull(number)
            foreign = [
                label.name for label in pull.get_labels() if not label.name.startswith(LABEL_PREFIX)
            ]
            pull.set_labels(*foreign, *labels)
