"""The tick status counts the errors of each event on each remote state."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.tick_status import (
    ERROR_CAP,
    ErrorCount,
    TickStatus,
    at_cap,
    clear_errors,
    find_error,
    record_error,
)

KEY = "run:F0001-S0001"
OTHER_KEY = "comment:F0001-S0002"
STATE = "a" * 40
OTHER_STATE = "b" * 40


def test_a_first_error_gives_one_unreported_entry_and_leaves_the_input_unchanged() -> None:
    status = TickStatus()

    recorded = record_error(status, KEY, STATE, "ValueError: boom")

    assert recorded.errors == [
        ErrorCount(event_key=KEY, remote_state=STATE, count=1, last_error="ValueError: boom")
    ]
    assert recorded.errors[0].reported is False
    assert status == TickStatus()


def test_a_repeated_error_on_the_same_state_counts_up_and_keeps_the_newer_error() -> None:
    status = record_error(TickStatus(), KEY, STATE, "ValueError: first")

    status = record_error(status, KEY, STATE, "ValueError: second")

    entry = find_error(status, KEY, STATE)
    assert entry is not None
    assert entry.count == 2
    assert entry.last_error == "ValueError: second"
    assert find_error(status, KEY, OTHER_STATE) is None


def test_an_error_on_another_state_replaces_the_keys_entries_and_keeps_other_keys() -> None:
    status = record_error(TickStatus(), KEY, STATE, "ValueError: boom")
    status = record_error(status, KEY, STATE, "ValueError: boom")
    status = record_error(status, OTHER_KEY, STATE, "KeyError: 'x'")
    other = find_error(status, OTHER_KEY, STATE)

    status = record_error(status, KEY, OTHER_STATE, "ValueError: new")

    assert [entry for entry in status.errors if entry.event_key == KEY] == [
        ErrorCount(event_key=KEY, remote_state=OTHER_STATE, count=1, last_error="ValueError: new")
    ]
    assert find_error(status, OTHER_KEY, STATE) == other


def test_clearing_removes_every_entry_of_the_key_and_keeps_other_keys() -> None:
    status = TickStatus(
        errors=[
            ErrorCount(event_key=KEY, remote_state=STATE, count=2),
            ErrorCount(event_key=KEY, remote_state=OTHER_STATE, count=1),
            ErrorCount(event_key=OTHER_KEY, remote_state=STATE, count=1),
        ]
    )

    cleared = clear_errors(status, KEY)

    assert cleared.errors == [ErrorCount(event_key=OTHER_KEY, remote_state=STATE, count=1)]


@pytest.mark.parametrize(("count", "expected"), [(2, False), (3, True)])
def test_the_cap_is_three_errors(count: int, expected: bool) -> None:
    entry = ErrorCount(event_key=KEY, remote_state=STATE, count=count)

    assert ERROR_CAP == 3
    assert at_cap(entry) is expected


@pytest.mark.parametrize("count", [0, 1])
def test_an_error_count_starts_at_one(count: int) -> None:
    model: type[BaseModel] = ErrorCount

    if count == 0:
        with pytest.raises(ValidationError):
            model(event_key=KEY, remote_state=STATE, count=count)
    else:
        assert isinstance(model(event_key=KEY, remote_state=STATE, count=count), ErrorCount)


@pytest.mark.parametrize("remote_state", ["a" * 39, "A" + "a" * 39])
def test_an_error_count_refuses_a_remote_state_that_is_no_commit_id(remote_state: str) -> None:
    model: type[BaseModel] = ErrorCount

    with pytest.raises(ValidationError):
        model(event_key=KEY, remote_state=remote_state, count=1)
