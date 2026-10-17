"""Reading the `<target>: green (<seconds> s)` lines out of a project command's output."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.checks import TargetTime, target_times


def test_green_target_lines_are_read_in_order_and_others_skipped() -> None:
    output = "lint: green (0.1 s)\ntypes: green (12 s)\ncheck: green\n"

    assert target_times(output) == [
        TargetTime(target="lint", seconds=0.1),
        TargetTime(target="types", seconds=12.0),
    ]


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("check: green", []),
        ("  lint: green (0.1 s)", []),
        ("lint: green (0.1 s) ", []),
        ("lint: green (0.1s)", []),
        ("lint: green (-1 s)", []),
        ("lint: green (1. s)", []),
        ("Lint: green (1 s)", []),
        ("lint: red (1 s)", []),
        ("lint: green (١ s)", []),
        ("lint: green (0 s)", [TargetTime(target="lint", seconds=0.0)]),
        ("lint: green (0.1 s)\r", [TargetTime(target="lint", seconds=0.1)]),
    ],
)
def test_only_a_line_matching_the_whole_pattern_counts(
    line: str, expected: list[TargetTime]
) -> None:
    assert target_times(line) == expected


def test_target_printed_twice_gives_two_entries_in_order() -> None:
    output = "lint: green (1 s)\ntest: green (2 s)\nlint: green (3 s)\n"

    assert target_times(output) == [
        TargetTime(target="lint", seconds=1.0),
        TargetTime(target="test", seconds=2.0),
        TargetTime(target="lint", seconds=3.0),
    ]


def test_empty_output_gives_no_entries() -> None:
    assert target_times("") == []


@pytest.mark.parametrize(
    ("target", "seconds", "accepted"),
    [
        ("lint", 0.0, True),
        ("lint", -0.1, False),
        ("Lint", 1.0, False),
    ],
)
def test_target_time_requires_a_command_name_and_non_negative_seconds(
    target: str, seconds: float, accepted: bool
) -> None:
    model: type[BaseModel] = TargetTime
    if accepted:
        model(target=target, seconds=seconds)
    else:
        with pytest.raises(ValidationError):
            model(target=target, seconds=seconds)


def test_target_time_refuses_an_unknown_field() -> None:
    model: type[BaseModel] = TargetTime

    with pytest.raises(ValidationError):
        model(target="lint", seconds=1.0, extra="x")
