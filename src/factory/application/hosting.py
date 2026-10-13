"""The interface through which the factory reaches the hosting service."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from factory.domain.hosting import PostKey, PostOutcome, PullRequestComment, PullRequestView


class HostingService(ABC):
    """Pull requests on the hosting service; every failing call raises `HostingServiceError`.

    Labels are written as a projection of the stage and never read back.
    """

    @abstractmethod
    def create_pull_request(
        self, branch: str, title: str, body: str, *, draft: bool
    ) -> PullRequestView:
        """Open a pull request from `branch` to the main branch, as draft or ready."""

    @abstractmethod
    def find_open_pull_request(self, branch: str) -> PullRequestView | None:
        """The open pull request of `branch`, if there is one."""

    @abstractmethod
    def get_pull_request(self, number: int) -> PullRequestView:
        """The pull request `number` with its state and merge state."""

    @abstractmethod
    def list_comments(self, number: int) -> list[PullRequestComment]:
        """The comments of pull request `number`, oldest first."""

    @abstractmethod
    def post_comment(self, number: int, text: str, key: PostKey) -> PostOutcome:
        """Post `text` with the marker and `key`; a post whose key exists is a no-op."""

    @abstractmethod
    def close(self, number: int) -> None:
        """Close pull request `number` without merging."""

    @abstractmethod
    def reopen(self, number: int) -> None:
        """Reopen the closed pull request `number`."""

    @abstractmethod
    def set_draft(self, number: int, draft: bool) -> None:
        """Mark pull request `number` as draft or as ready for review."""

    @abstractmethod
    def set_description(self, number: int, body: str) -> None:
        """Replace the description of pull request `number`."""

    @abstractmethod
    def set_labels(self, number: int, labels: Sequence[str]) -> None:
        """Replace the labels of pull request `number` with `labels`."""
