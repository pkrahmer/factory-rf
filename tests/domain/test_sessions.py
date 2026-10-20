"""The kernel's process table read one line at a time, and what of a session is left to kill."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.sessions import ProcessEntry, left_to_kill, parse_stat


@pytest.mark.parametrize(
    ("pid", "stat", "expected"),
    [
        pytest.param(
            4242,
            "4242 (make) S 1 4242 4242 0 -1",
            ProcessEntry(pid=4242, session=4242, ended=False),
            id="make",
        ),
        pytest.param(
            77,
            "77 (a) (b c) R 1 70 70 0",
            ProcessEntry(pid=77, session=70, ended=False),
            id="name-with-space-and-parentheses",
        ),
        pytest.param(5, "5 (x) Z 1 5 5 0", ProcessEntry(pid=5, session=5, ended=True), id="Z"),
        pytest.param(5, "5 (x) X 1 5 5 0", ProcessEntry(pid=5, session=5, ended=True), id="X"),
        pytest.param(5, "5 (x) S 1 5 5 0", ProcessEntry(pid=5, session=5, ended=False), id="S"),
        pytest.param(5, "5 (x) R 1 5 5 0", ProcessEntry(pid=5, session=5, ended=False), id="R"),
        pytest.param(5, "5 (x) D 1 5 5 0", ProcessEntry(pid=5, session=5, ended=False), id="D"),
        pytest.param(5, "5 (x) T 1 5 5 0", ProcessEntry(pid=5, session=5, ended=False), id="T"),
    ],
)
def test_status_line_gives_the_entry(pid: int, stat: str, expected: ProcessEntry) -> None:
    assert parse_stat(pid, stat) == expected


@pytest.mark.parametrize(
    "stat",
    [
        pytest.param("5 x S 1 5 5 0", id="no-closing-parenthesis"),
        pytest.param("5 (x) S 1 5", id="three-fields"),
        pytest.param("5 (x) S 1 5 x 0", id="session-not-a-number"),
        pytest.param("5 (x) S 1 5 -1 0", id="session-negative"),
    ],
)
def test_unreadable_status_line_is_refused(stat: str) -> None:
    with pytest.raises(ValueError):  # noqa: PT011  # pydantic's ValidationError is one
        parse_stat(5, stat)


@pytest.mark.parametrize(
    ("field", "value", "accepted"),
    [
        pytest.param("pid", 0, False, id="pid-0"),
        pytest.param("pid", 1, True, id="pid-1"),
        pytest.param("session", -1, False, id="session-minus-1"),
        pytest.param("session", 0, True, id="session-0"),
    ],
)
def test_entry_limits(field: str, value: int, accepted: bool) -> None:
    model: type[BaseModel] = ProcessEntry
    fields = {"pid": 1, "session": 0, "ended": False, field: value}

    if accepted:
        assert getattr(model(**fields), field) == value
    else:
        with pytest.raises(ValidationError):
            model(**fields)


def _entry(pid: int, session: int = 10, *, ended: bool = False) -> ProcessEntry:
    return ProcessEntry(pid=pid, session=session, ended=ended)


@pytest.mark.parametrize(
    ("entries", "refused", "expected"),
    [
        pytest.param([_entry(12)], [], [12], id="kept"),
        pytest.param([_entry(12, 11)], [], [], id="other-session"),
        pytest.param([_entry(12, ended=True)], [], [], id="ended"),
        pytest.param([_entry(12)], [12], [], id="refused"),
        pytest.param([_entry(30), _entry(12), _entry(20)], [], [12, 20, 30], id="ascending"),
        pytest.param([_entry(12), _entry(12)], [], [12], id="twice"),
        pytest.param([], [], [], id="none"),
    ],
)
def test_what_is_left_to_kill(
    entries: list[ProcessEntry], refused: list[int], expected: list[int]
) -> None:
    assert left_to_kill(entries, session=10, refused=refused) == expected
