"""The lease clock: the age of a claim, its expiry and the status it gives an instance."""

import ast
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from factory.domain import lease
from factory.domain.lease import claim_status, lease_age, lease_expired
from factory.domain.work_item import Claim
from stage_run_support import INSTANCE

START = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
OWN = INSTANCE
OTHER = "factory-2"
CLOCK_CALLS = {"now", "utcnow", "today", "time"}


def _claim(lease_duration: int = 60, instance: str = OWN) -> Claim:
    return Claim(instance=instance, stage="coder", started_at=START, lease_duration=lease_duration)


@pytest.mark.parametrize(
    "age",
    [timedelta(minutes=45), timedelta(minutes=-5)],
    ids=["45-minutes-after", "5-minutes-before"],
)
def test_lease_age_is_now_minus_the_start(age: timedelta) -> None:
    assert lease_age(_claim(), START + age) == age


@pytest.mark.parametrize(
    ("age", "expired"),
    [
        (timedelta(minutes=59, seconds=59), False),
        (timedelta(minutes=60), True),
        (timedelta(minutes=60, seconds=1), True),
    ],
    ids=["59m59s", "60m", "60m1s"],
)
def test_lease_expires_when_its_age_reaches_the_lease_duration(
    age: timedelta, expired: bool
) -> None:
    assert lease_expired(_claim(60), START + age) is expired


@pytest.mark.parametrize("lease_duration", [1, 60])
@pytest.mark.parametrize(
    "age", [timedelta(seconds=-1), timedelta(minutes=-5)], ids=["1s-before", "5m-before"]
)
def test_a_negative_age_is_not_expired(lease_duration: int, age: timedelta) -> None:
    assert lease_expired(_claim(lease_duration), START + age) is False


@pytest.mark.parametrize(("lease_duration", "expired"), [(30, True), (90, False)], ids=["30", "90"])
def test_lease_expired_uses_the_claims_own_lease_duration(
    lease_duration: int, expired: bool
) -> None:
    assert lease_expired(_claim(lease_duration), START + timedelta(minutes=45)) is expired


def test_no_claim_has_status_none() -> None:
    assert claim_status(None, instance=OWN, now=START) == "none"


@pytest.mark.parametrize(
    "age",
    [timedelta(minutes=-5), timedelta(minutes=30), timedelta(days=3)],
    ids=["before-start", "within-lease", "long-after-lease"],
)
def test_an_own_claim_is_own_whatever_its_age(age: timedelta) -> None:
    assert claim_status(_claim(60, OWN), instance=OWN, now=START + age) == "own"


@pytest.mark.parametrize(
    ("age", "status"),
    [
        (timedelta(minutes=59, seconds=59), "held"),
        (timedelta(minutes=60), "expired"),
        (timedelta(minutes=60, seconds=1), "expired"),
    ],
    ids=["59m59s", "60m", "60m1s"],
)
def test_another_instances_claim_is_held_until_its_lease_has_run_out(
    age: timedelta, status: str
) -> None:
    assert claim_status(_claim(60, OTHER), instance=OWN, now=START + age) == status


def _called_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def test_the_lease_module_reads_no_clock() -> None:
    tree = ast.parse(Path(lease.__file__).read_text(encoding="utf-8"))
    called = {_called_name(node) for node in ast.walk(tree) if isinstance(node, ast.Call)}

    assert called & CLOCK_CALLS == set()
