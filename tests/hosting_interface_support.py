"""The operations of the hosting-service interface, shared by the interface tests."""

from typing import Literal

from factory.domain.hosting import PullRequestComment, PullRequestView

OPERATIONS = {
    "create_pull_request": PullRequestView,
    "find_open_pull_request": PullRequestView | None,
    "get_pull_request": PullRequestView,
    "list_comments": list[PullRequestComment],
    "post_comment": Literal["posted", "already_posted"],
    "close": type(None),
    "reopen": type(None),
    "set_draft": type(None),
    "set_description": type(None),
    "set_labels": type(None),
}
