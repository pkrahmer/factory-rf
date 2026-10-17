"""The kill-point cases of the recovery proof: the six rows and the rules of a case."""

import pydantic
import pytest
from pydantic import BaseModel

from factory.domain.kill_point_cases import KILL_POINT_CASES, KillPointCase
from factory.domain.kill_points import KillPoint


def test_the_cases_are_the_six_rows_in_order() -> None:
    rows = [
        (case.id, case.dies, case.kill_point, case.result_class, case.charges_crash)
        for case in KILL_POINT_CASES
    ]

    assert rows == [
        ("agent-run-tick", "tick", KillPoint.AGENT_RUN, "crash", True),
        ("agent-run-dies", "agent-run", None, "stall", False),
        ("commit-push", "tick", KillPoint.BEFORE_PUSH, "crash", True),
        ("post-record", "tick", KillPoint.AFTER_POST, "crash", False),
        ("tick-other", "tick", KillPoint.AFTER_PUSH, "crash", True),
        ("container", "container", KillPoint.AGENT_RUN, "crash", True),
    ]


@pytest.mark.parametrize(
    ("kill_point", "result_class", "accepted"),
    [
        (KillPoint.AGENT_RUN, "stall", False),
        (None, "crash", False),
        (None, "stall", True),
        (KillPoint.AGENT_RUN, "crash", True),
    ],
    ids=["stall-with-point", "crash-without-point", "stall-without-point", "crash-with-point"],
)
def test_a_kill_point_is_given_exactly_for_a_crash(
    kill_point: KillPoint | None, result_class: str, *, accepted: bool
) -> None:
    model: type[BaseModel] = KillPointCase
    fields = {
        "id": "x",
        "dies": "tick",
        "kill_point": kill_point,
        "result_class": result_class,
        "charges_crash": False,
    }

    if accepted:
        model(**fields)
    else:
        with pytest.raises(pydantic.ValidationError):
            model(**fields)


@pytest.mark.parametrize(
    ("charges_crash", "accepted"), [(True, False), (False, True)], ids=["charges", "free"]
)
def test_a_stall_never_charges_a_crash(*, charges_crash: bool, accepted: bool) -> None:
    fields: dict[str, object] = {
        "id": "x",
        "dies": "agent-run",
        "kill_point": None,
        "result_class": "stall",
        "charges_crash": charges_crash,
    }
    model: type[BaseModel] = KillPointCase

    if accepted:
        model(**fields)
    else:
        with pytest.raises(pydantic.ValidationError):
            model(**fields)


@pytest.mark.parametrize(
    "change",
    [{"colour": "red"}, {"dies": "process"}, {"result_class": "error"}, {"kill_point": "never"}],
    ids=["unknown-key", "dies-outside", "class-outside", "kill-point-outside"],
)
def test_a_case_outside_the_closed_model_is_refused(change: dict[str, object]) -> None:
    fields: dict[str, object] = {
        "id": "x",
        "dies": "tick",
        "kill_point": "agent-run",
        "result_class": "crash",
        "charges_crash": True,
    }
    model: type[BaseModel] = KillPointCase

    with pytest.raises(pydantic.ValidationError):
        model(**{**fields, **change})
