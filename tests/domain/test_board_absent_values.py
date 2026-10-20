"""A work item without a state shows its absent values, and a board line writes `-` or the value."""

import pytest

from factory.domain.board import BoardRow, render_board, work_item_row
from factory.domain.work_item import WorkItemDocument, WorkItemSnapshot

ABSENT_ROW = BoardRow(
    work_item="F0001-S0001",
    title="Domain model",
    folder="backlog",
    stage=None,
    blocked=None,
    claim=None,
    running_since=None,
    pull_request=None,
)


def test_a_work_item_without_a_state_shows_every_state_value_as_absent() -> None:
    snapshot = WorkItemSnapshot(
        id="F0001-S0001",
        path="factory/features/F0001-demo/backlog/F0001-S0001-story.md",
        folder="backlog",
        branch="work-item/F0001-S0001",
        branch_commit=None,
        document=WorkItemDocument(state=None, body="# Domain model\n"),
    )
    row = work_item_row(snapshot)
    assert row == ABSENT_ROW
    assert render_board([], [row]) == (
        "features\nwork items\n"
        "F0001-S0001  Domain model  backlog  stage=-  blocked=-  claim=-  running_since=-"
        "  pull_request=-\n"
    )


@pytest.mark.parametrize(
    ("row", "line"),
    [
        pytest.param(
            ABSENT_ROW,
            "F0001-S0001  Domain model  backlog  stage=-  blocked=-  claim=-  running_since=-"
            "  pull_request=-",
            id="absent",
        ),
        pytest.param(
            BoardRow(
                work_item="F0001-S0001",
                title="Domain model",
                folder="in-progress",
                stage="tests",
                blocked="question",
                claim=None,
                running_since=None,
                pull_request=7,
            ),
            "F0001-S0001  Domain model  in-progress  stage=tests  blocked=question  claim=-"
            "  running_since=-  pull_request=7",
            id="blocked",
        ),
    ],
)
def test_a_board_line_writes_an_absent_value_as_a_dash_and_a_blocked_row_with_its_reason(
    row: BoardRow, line: str
) -> None:
    assert render_board([], [row]) == f"features\nwork items\n{line}\n"
