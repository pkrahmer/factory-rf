"""Which processes of its user the leftovers program still has to end, and when it refuses."""

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.leftovers import Identity, leftover_pids, leftovers_refusal
from factory.domain.sessions import ProcessEntry
from leftovers_support import AGENT, ROOT, process_entry


@pytest.mark.parametrize(
    ("entries", "expected"),
    [
        pytest.param([process_entry(7, 1001)], [7], id="kept"),
        pytest.param([process_entry(11, 1001)], [], id="own"),
        pytest.param([process_entry(9, 1000)], [], id="other-user"),
        pytest.param([process_entry(8, 1001, ended=True)], [], id="ended"),
        pytest.param(
            [
                process_entry(10, 1001),
                process_entry(3, 1001),
                process_entry(11, 1001),
                process_entry(9, 1000),
                process_entry(7, 1001),
                process_entry(8, 1001, ended=True),
            ],
            [3, 7, 10],
            id="unsorted-table",
        ),
        pytest.param([process_entry(7, 1001), process_entry(7, 1001)], [7], id="twice"),
        pytest.param([], [], id="empty"),
    ],
)
def test_leftover_pids_are_the_user_s_other_living_processes(
    entries: list[ProcessEntry], expected: list[int]
) -> None:
    assert leftover_pids(entries, AGENT) == expected


@pytest.mark.parametrize(
    ("identity", "user", "expected"),
    [
        pytest.param(ROOT, "root", "refuses to run as root", id="root-root"),
        pytest.param(ROOT, "agent", "refuses to run as root", id="root-agent"),
        pytest.param(AGENT, "factory", "runs as agent, not factory", id="other-user"),
        pytest.param(AGENT, "Agent", "runs as agent, not Agent", id="case-differs"),
        pytest.param(AGENT, "agent", None, id="same-user"),
    ],
)
def test_root_and_another_user_are_refused(
    identity: Identity, user: str, expected: str | None
) -> None:
    assert leftovers_refusal(identity, user) == expected


@pytest.mark.parametrize(
    ("model", "fields", "field", "value", "accepted"),
    [
        pytest.param(
            ProcessEntry,
            {"pid": 1, "session": 0, "ended": False},
            "uid",
            -1,
            False,
            id="entry-uid--1",
        ),
        pytest.param(
            ProcessEntry, {"pid": 1, "session": 0, "ended": False}, "uid", 0, True, id="entry-uid-0"
        ),
        pytest.param(Identity, {"uid": 0, "pid": 1}, "user", "", False, id="identity-user-empty"),
        pytest.param(Identity, {"uid": 0, "pid": 1}, "user", "a", True, id="identity-user-a"),
        pytest.param(Identity, {"uid": 0, "user": "a"}, "pid", 0, False, id="identity-pid-0"),
        pytest.param(Identity, {"uid": 0, "user": "a"}, "pid", 1, True, id="identity-pid-1"),
        pytest.param(Identity, {"pid": 1, "user": "a"}, "uid", -1, False, id="identity-uid--1"),
        pytest.param(Identity, {"pid": 1, "user": "a"}, "uid", 0, True, id="identity-uid-0"),
    ],
)
def test_model_limits(
    model: type[BaseModel],
    fields: dict[str, object],
    field: str,
    value: object,
    accepted: bool,
) -> None:
    arguments = {**fields, field: value}

    if accepted:
        assert getattr(model(**arguments), field) == value
    else:
        with pytest.raises(ValidationError):
            model(**arguments)
