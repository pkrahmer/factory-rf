"""Kill points: inert until armed, firing once with an injected kill."""

import ast
import importlib.util
from enum import StrEnum
from pathlib import Path

import pytest

from factory.domain.errors import FactoryError
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints

ALL_POINTS = list(KillPoint)


def _others(point: KillPoint) -> list[KillPoint]:
    return [other for other in KillPoint if other is not point]


def test_kill_point_has_exactly_the_four_named_members() -> None:
    assert issubclass(KillPoint, StrEnum)
    assert {member.name: member.value for member in KillPoint} == {
        "AGENT_RUN": "agent-run",
        "BEFORE_PUSH": "before-push",
        "AFTER_POST": "after-post",
        "AFTER_PUSH": "after-push",
    }


@pytest.mark.parametrize("point", ALL_POINTS)
def test_new_kill_points_never_raise(kill_points: KillPoints, point: KillPoint) -> None:
    for _ in range(5):
        kill_points.reach(point)


def test_reached_counts_every_reach_per_point(kill_points: KillPoints) -> None:
    for point in KillPoint:
        assert kill_points.reached(point) == 0
    for _ in range(3):
        kill_points.reach(KillPoint.AGENT_RUN)
    kill_points.reach(KillPoint.AFTER_POST)
    assert kill_points.reached(KillPoint.AGENT_RUN) == 3
    assert kill_points.reached(KillPoint.AFTER_POST) == 1
    assert kill_points.reached(KillPoint.BEFORE_PUSH) == 0
    assert kill_points.reached(KillPoint.AFTER_PUSH) == 0


@pytest.mark.parametrize("point", ALL_POINTS)
def test_armed_point_raises_injected_kill_on_next_reach(
    kill_points: KillPoints, point: KillPoint
) -> None:
    kill_points.arm(point)
    with pytest.raises(InjectedKill) as caught:
        kill_points.reach(point)
    assert caught.value.point is point


@pytest.mark.parametrize("point", ALL_POINTS)
def test_after_lets_that_many_reaches_pass_first(kill_points: KillPoints, point: KillPoint) -> None:
    kill_points.arm(point, after=2)
    kill_points.reach(point)
    kill_points.reach(point)
    with pytest.raises(InjectedKill):
        kill_points.reach(point)


@pytest.mark.parametrize("point", ALL_POINTS)
def test_point_is_disarmed_after_it_fires_and_the_raising_reach_counts(
    kill_points: KillPoints, point: KillPoint
) -> None:
    kill_points.arm(point)
    with pytest.raises(InjectedKill):
        kill_points.reach(point)
    assert kill_points.reached(point) == 1
    kill_points.reach(point)
    assert kill_points.reached(point) == 2


@pytest.mark.parametrize("point", ALL_POINTS)
def test_arming_one_point_leaves_the_others_inert(
    kill_points: KillPoints, point: KillPoint
) -> None:
    kill_points.arm(point)
    for other in _others(point):
        for _ in range(3):
            kill_points.reach(other)


def test_arming_one_point_leaves_an_armed_other_point_as_it_was(
    kill_points: KillPoints,
) -> None:
    kill_points.arm(KillPoint.BEFORE_PUSH, after=1)
    kill_points.arm(KillPoint.AFTER_PUSH)
    kill_points.reach(KillPoint.BEFORE_PUSH)
    with pytest.raises(InjectedKill) as caught:
        kill_points.reach(KillPoint.BEFORE_PUSH)
    assert caught.value.point is KillPoint.BEFORE_PUSH


@pytest.mark.parametrize("point", ALL_POINTS)
def test_after_counts_from_the_arming(kill_points: KillPoints, point: KillPoint) -> None:
    kill_points.reach(point)
    kill_points.reach(point)
    kill_points.arm(point)
    with pytest.raises(InjectedKill):
        kill_points.reach(point)


@pytest.mark.parametrize("point", ALL_POINTS)
def test_arming_an_armed_point_replaces_the_earlier_arming(
    kill_points: KillPoints, point: KillPoint
) -> None:
    kill_points.arm(point, after=3)
    kill_points.arm(point)
    with pytest.raises(InjectedKill):
        kill_points.reach(point)


@pytest.mark.parametrize(("after", "accepted"), [(-1, False), (0, True)])
def test_after_must_not_be_negative(kill_points: KillPoints, after: int, accepted: bool) -> None:
    point = KillPoint.BEFORE_PUSH
    if accepted:
        kill_points.arm(point, after=after)
        with pytest.raises(InjectedKill):
            kill_points.reach(point)
    else:
        with pytest.raises(ValueError):
            kill_points.arm(point, after=after)
        kill_points.reach(point)


def test_negative_after_leaves_an_earlier_arming_as_it_was(
    kill_points: KillPoints,
) -> None:
    point = KillPoint.AFTER_PUSH
    kill_points.arm(point, after=1)
    with pytest.raises(ValueError):
        kill_points.arm(point, after=-1)
    kill_points.reach(point)
    with pytest.raises(InjectedKill):
        kill_points.reach(point)


def test_injected_kill_passes_through_except_exception(
    kill_points: KillPoints,
) -> None:
    assert issubclass(InjectedKill, BaseException)
    assert not issubclass(InjectedKill, Exception)
    kill_points.arm(KillPoint.AGENT_RUN)
    swallowed: list[Exception] = []

    def handler_that_catches_everything() -> None:
        try:
            kill_points.reach(KillPoint.AGENT_RUN)
        except Exception as error:  # noqa: BLE001  (the point of the test)
            swallowed.append(error)

    with pytest.raises(InjectedKill):
        handler_that_catches_everything()
    assert swallowed == []


def test_injected_kill_message_names_the_point_and_is_no_factory_error() -> None:
    assert str(InjectedKill(KillPoint.AFTER_PUSH)) == "injected kill at after-push"
    assert not issubclass(InjectedKill, FactoryError)


@pytest.mark.parametrize("point", ALL_POINTS)
def test_two_kill_points_instances_are_independent(point: KillPoint) -> None:
    armed = KillPoints()
    untouched = KillPoints()
    armed.arm(point)
    untouched.reach(point)
    assert untouched.reached(point) == 1
    assert armed.reached(point) == 0


@pytest.mark.parametrize("module", ["factory.domain.kill_points", "factory.domain.errors"])
def test_domain_modules_import_nothing_that_touches_the_outside(module: str) -> None:
    spec = importlib.util.find_spec(module)
    assert spec is not None
    assert spec.origin is not None
    tree = ast.parse(Path(spec.origin).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint({"os", "subprocess", "time", "socket", "pathlib"})
