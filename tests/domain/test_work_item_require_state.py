"""The one way to get a work item's state when it must be there."""

import pytest

from factory.domain.errors import CannotHandle, WorkItemFormatError
from factory.domain.work_item import WorkItemDocument, initial_state, require_state


def test_require_state_returns_the_documents_state() -> None:
    document = WorkItemDocument(state=initial_state("doing"), body="")

    assert require_state(document, ValueError("no state")) == document.state


@pytest.mark.parametrize(
    "error",
    [
        ValueError("the work item has no state"),
        CannotHandle("crash", "the work item has no state"),
        WorkItemFormatError("the document has no state"),
    ],
    ids=["value-error", "cannot-handle", "work-item-format-error"],
)
def test_require_state_raises_the_very_error_passed_without_a_state(error: Exception) -> None:
    document = WorkItemDocument(state=None, body="")

    with pytest.raises(type(error)) as excinfo:
        require_state(document, error)

    assert excinfo.value is error
