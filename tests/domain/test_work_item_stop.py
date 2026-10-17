"""A stop of one work item and the result of posting it on its pull request."""

import pytest
from pydantic import ValidationError

from factory.domain.hosting import PostKey
from factory.domain.stops import StopPosted, WorkItemStop

KEY = PostKey(work_item="F0001-S0001", kind="stall", n="3")


def _fields(**changes: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "key": KEY,
        "branch": "work-item/F0001-S0001",
        "title": "F0001-S0001: stage tests stalled",
        "pull_request": None,
        "text": "Comment anything to retry; close the pull request to stop.",
    }
    fields.update(changes)
    return fields


def _posted(**changes: object) -> dict[str, object]:
    fields: dict[str, object] = {"pull_request": 1, "opened": False, "outcome": "posted"}
    fields.update(changes)
    return fields


def test_a_stop_with_branch_title_and_text_filled_is_accepted() -> None:
    stop = WorkItemStop.model_validate(_fields())

    assert stop.branch == "work-item/F0001-S0001"
    assert stop.title == "F0001-S0001: stage tests stalled"
    assert stop.text == "Comment anything to retry; close the pull request to stop."


@pytest.mark.parametrize("blank", ["", " ", "\t\n"], ids=["empty", "space", "whitespace"])
def test_a_blank_branch_is_rejected(blank: str) -> None:
    with pytest.raises(ValidationError):
        WorkItemStop.model_validate(_fields(branch=blank))


@pytest.mark.parametrize("blank", ["", " ", "\t\n"], ids=["empty", "space", "whitespace"])
def test_a_blank_title_is_rejected(blank: str) -> None:
    with pytest.raises(ValidationError):
        WorkItemStop.model_validate(_fields(title=blank))


@pytest.mark.parametrize("blank", ["", " ", "\t\n"], ids=["empty", "space", "whitespace"])
def test_a_blank_text_is_rejected(blank: str) -> None:
    with pytest.raises(ValidationError):
        WorkItemStop.model_validate(_fields(text=blank))


def test_a_branch_of_another_work_item_is_rejected() -> None:
    with pytest.raises(ValidationError):
        WorkItemStop.model_validate(_fields(branch="work-item/F0001-S0002"))


@pytest.mark.parametrize(
    ("value", "accepted"), [(-1, False), (0, False), (1, True)], ids=["-1", "0", "1"]
)
def test_the_pull_request_of_a_stop_is_a_positive_integer(value: int, accepted: bool) -> None:
    if accepted:
        assert WorkItemStop.model_validate(_fields(pull_request=value)).pull_request == value
    else:
        with pytest.raises(ValidationError):
            WorkItemStop.model_validate(_fields(pull_request=value))


def test_a_stop_accepts_no_pull_request() -> None:
    assert WorkItemStop.model_validate(_fields(pull_request=None)).pull_request is None


@pytest.mark.parametrize(
    ("value", "accepted"), [(-1, False), (0, False), (1, True)], ids=["-1", "0", "1"]
)
def test_the_pull_request_of_a_posted_stop_is_a_positive_integer(
    value: int, accepted: bool
) -> None:
    if accepted:
        assert StopPosted.model_validate(_posted(pull_request=value)).pull_request == value
    else:
        with pytest.raises(ValidationError):
            StopPosted.model_validate(_posted(pull_request=value))
