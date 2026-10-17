"""The one conversion of an aware time to UTC, and the model fields that use it."""

import ast
from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from factory.domain.cost_records import CostRecord
from factory.domain.git import CommitInfo
from factory.domain.hosting import PullRequestComment
from factory.domain.stops import RepositoryStop
from factory.domain.times import in_utc
from factory.domain.work_item import Claim
from source_search import modules

AWARE = datetime(2026, 10, 12, 14, 0, tzinfo=timezone(timedelta(hours=2)))
NAIVE = datetime(2026, 10, 12, 12, 0)
IN_UTC = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)

MODELS_WITH_TIMES = (
    "factory.domain.cost_records",
    "factory.domain.git",
    "factory.domain.hosting",
    "factory.domain.stops",
    "factory.domain.work_item",
)


def _cost_record(at: datetime) -> datetime:
    record = CostRecord(
        run="a" * 32,
        work_item="F0002-S0007",
        stage="tests",
        role="tester",
        attempt=0,
        status="started",
        started_at=at,
    )
    return record.started_at


def _commit_info(at: datetime) -> datetime:
    info = CommitInfo(commit="a" * 40, parents=[], subject="s", author="a", committed_at=at)
    return info.committed_at


def _comment(at: datetime) -> datetime:
    comment = PullRequestComment(
        id=1, author="human", body="A remark.", created_at=at, by_factory=False, key=None
    )
    return comment.created_at


def _stop(at: datetime) -> datetime:
    stop = RepositoryStop(scope="repository", reason="fetch_failed", detail="x", at=at)
    return stop.at


def _claim(at: datetime) -> datetime:
    claim = Claim(instance="factory-1", stage="tests", started_at=at, lease_duration=30)
    return claim.started_at


BUILDERS: list[Callable[[datetime], datetime]] = [
    _cost_record,
    _commit_info,
    _comment,
    _stop,
    _claim,
]
BUILDER_IDS = ["cost-record", "commit-info", "comment", "stop", "claim"]


def test_in_utc_keeps_the_instant_in_utc() -> None:
    converted = in_utc(AWARE)
    assert converted == IN_UTC
    assert converted.tzinfo is UTC


@pytest.mark.parametrize(
    ("build", "aware"),
    [(build, aware) for build in BUILDERS for aware in (True, False)],
    ids=[f"{name}-{side}" for name in BUILDER_IDS for side in ("aware", "naive")],
)
def test_time_fields_hold_utc_and_refuse_a_naive_time(
    build: Callable[[datetime], datetime], aware: bool
) -> None:
    if aware:
        held = build(AWARE)
        assert held == IN_UTC
        assert held.tzinfo is UTC
    else:
        with pytest.raises(ValidationError):
            build(NAIVE)


def _calls_astimezone(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.Attribute) and node.attr == "astimezone" for node in ast.walk(tree)
    )


def test_only_the_times_module_converts_to_utc() -> None:
    found = modules()
    assert [name for name in MODELS_WITH_TIMES if _calls_astimezone(found[name])] == []
    assert _calls_astimezone(found["factory.domain.times"])
