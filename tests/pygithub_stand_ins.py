"""Stand-ins for the PyGithub objects the hosting client uses; they record every call."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class Call:
    """One recorded call on a stand-in."""

    name: str
    args: tuple[object, ...] = ()
    kwargs: dict[str, object] = field(default_factory=dict)


class _Recorder:
    """Records calls and raises the failure configured for a method."""

    def __init__(self) -> None:
        self.calls: list[Call] = []
        self.failures: dict[str, BaseException] = {}

    def _record(self, name: str, *args: object, **kwargs: object) -> None:
        self.calls.append(Call(name, args, kwargs))
        if name in self.failures:
            raise self.failures[name]

    def calls_to(self, name: str) -> list[Call]:
        """The recorded calls of the method `name`."""
        return [call for call in self.calls if call.name == name]


@dataclass(frozen=True)
class StandInUser:
    """A GitHub user or owner."""

    login: str


@dataclass(frozen=True)
class StandInHead:
    """The head of a pull request."""

    ref: str


@dataclass(frozen=True)
class StandInLabel:
    """A label on a pull request."""

    name: str


@dataclass(frozen=True)
class StandInComment:
    """An issue comment on a pull request."""

    id: int
    user: StandInUser
    body: str
    created_at: datetime


class StandInPullRequest(_Recorder):
    """A pull request with the members the client reads and calls."""

    def __init__(
        self,
        number: int = 5,
        branch: str = "work-item/F0001-S0001",
        *,
        title: str = "title",
        state: str = "open",
        merged: bool = False,
        draft: bool = False,
        merge_commit_sha: str | None = None,
        html_url: str = "https://example.invalid/pull/5",
        comments: list[StandInComment] | None = None,
        labels: list[str] | None = None,
    ) -> None:
        super().__init__()
        self.number = number
        self.head = StandInHead(branch)
        self.title = title
        self.state = state
        self.merged = merged
        self.draft = draft
        self.merge_commit_sha = merge_commit_sha
        self.html_url = html_url
        self.comments: list[StandInComment] = list(comments or [])
        self.labels: list[StandInLabel] = [StandInLabel(name) for name in labels or []]

    def get_issue_comments(self) -> list[StandInComment]:
        """The comments in the stand-in's order."""
        self._record("get_issue_comments")
        return list(self.comments)

    def create_issue_comment(self, body: str) -> StandInComment:
        """Add a comment by the factory's user."""
        self._record("create_issue_comment", body)
        comment = StandInComment(
            id=max((existing.id for existing in self.comments), default=0) + 1,
            user=StandInUser("factory-bot"),
            body=body,
            created_at=datetime(2026, 10, 12, 10, 0, tzinfo=UTC),
        )
        self.comments.append(comment)
        return comment

    def edit(self, **kwargs: object) -> None:
        """Record an edit of state or body."""
        self._record("edit", **kwargs)

    def convert_to_draft(self) -> None:
        """Record the conversion to draft."""
        self._record("convert_to_draft")

    def mark_ready_for_review(self) -> None:
        """Record the mark as ready."""
        self._record("mark_ready_for_review")

    def get_labels(self) -> list[StandInLabel]:
        """The labels in their order."""
        self._record("get_labels")
        return list(self.labels)

    def set_labels(self, *names: str) -> None:
        """Record the labels set."""
        self._record("set_labels", *names)


class StandInRepository(_Recorder):
    """A repository with the members the client reads and calls."""

    def __init__(
        self,
        owner_login: str = "octo",
        pulls: list[StandInPullRequest] | None = None,
        open_pulls: list[StandInPullRequest] | None = None,
    ) -> None:
        super().__init__()
        self.owner = StandInUser(owner_login)
        self.pulls: dict[int, StandInPullRequest] = {pull.number: pull for pull in pulls or []}
        self.open_pulls: list[StandInPullRequest] = list(open_pulls or [])

    def create_pull(
        self, base: str, head: str, *, title: str, body: str, draft: bool
    ) -> StandInPullRequest:
        """Create a pull request with the next number."""
        self._record("create_pull", base=base, head=head, title=title, body=body, draft=draft)
        number = max(self.pulls, default=0) + 1
        pull = StandInPullRequest(
            number,
            head,
            title=title,
            draft=draft,
            html_url=f"https://example.invalid/pull/{number}",
        )
        self.pulls[number] = pull
        return pull

    def get_pulls(self, **kwargs: object) -> list[StandInPullRequest]:
        """The configured open pull requests, whatever the filter."""
        self._record("get_pulls", **kwargs)
        return list(self.open_pulls)

    def get_pull(self, number: int) -> StandInPullRequest:
        """The pull request of that number."""
        self._record("get_pull", number)
        return self.pulls[number]


class Untouchable:
    """A repository that raises on every attribute access."""

    def __getattribute__(self, name: str) -> object:
        raise AssertionError(f"the repository was touched: {name}")
