"""Marking an error as reported needs both its event key and its remote state to match."""

import pytest

from factory.domain.tick_status import ErrorCount, TickStatus, mark_reported

STATUS = TickStatus(
    errors=[
        ErrorCount(event_key="run:F0001-S0001", remote_state="a" * 40, count=1),
        ErrorCount(event_key="run:F0001-S0001", remote_state="b" * 40, count=1),
        ErrorCount(event_key="ask:F0001-S0002", remote_state="a" * 40, count=1),
    ]
)


@pytest.mark.parametrize(
    ("event_key", "remote_state", "reported"),
    [
        pytest.param("run:F0001-S0001", "a" * 40, [True, False, False], id="both-match"),
        pytest.param("ask:F0001-S0002", "b" * 40, [False, False, False], id="one-matches"),
    ],
)
def test_only_entries_matching_key_and_state_are_marked_reported(
    event_key: str, remote_state: str, reported: list[bool]
) -> None:
    marked = mark_reported(STATUS, event_key, remote_state)

    assert [entry.reported for entry in marked.errors] == reported
    assert [entry.model_dump(exclude={"reported"}) for entry in marked.errors] == [
        entry.model_dump(exclude={"reported"}) for entry in STATUS.errors
    ]
