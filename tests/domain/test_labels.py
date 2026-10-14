"""The labels of a pull request as a projection of its work item's stage."""

import pytest

from factory.domain.labels import labels_for
from factory.domain.work_item import WorkItemState


@pytest.mark.parametrize(
    "state",
    [
        WorkItemState(stage="review"),
        WorkItemState(stage="tests", blocked="question", round=2, attempts=1, crashes=1),
    ],
    ids=["moving", "blocked"],
)
def test_the_labels_are_the_stage_label_of_the_state(state: WorkItemState) -> None:
    assert labels_for(state) == [f"stage:{state.stage}"]
