"""The stop of a repository or the machine and the health status that holds the stops."""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.stops import HealthStatus, RepositoryStop

AT = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
REPOSITORY_REASONS = [
    "fetch_failed",
    "checkout_restore_failed",
    "pipeline_definition_invalid",
    "agent_definition_invalid",
    "repository_unavailable",
    "main_branch_failing",
]
SCOPES = [(reason, "repository") for reason in REPOSITORY_REASONS] + [
    ("preflight_failed", "machine"),
    ("disk_low", "machine"),
]
OTHER_SCOPE = {"repository": "machine", "machine": "repository"}


def _fields(**changes: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "scope": "repository",
        "reason": "fetch_failed",
        "detail": "origin unreachable",
        "at": AT,
    }
    fields.update(changes)
    return fields


def _stop(reason: str = "fetch_failed") -> RepositoryStop:
    scope = "machine" if reason == "preflight_failed" else "repository"
    return RepositoryStop.model_validate(_fields(scope=scope, reason=reason))


@pytest.mark.parametrize(("detail", "accepted"), [("", False), (" \t\n", False), ("x", True)])
def test_a_blank_detail_is_rejected(detail: str, accepted: bool) -> None:
    if accepted:
        assert RepositoryStop.model_validate(_fields(detail=detail)).detail == detail
    else:
        with pytest.raises(ValidationError):
            RepositoryStop.model_validate(_fields(detail=detail))


@pytest.mark.parametrize(("reason", "scope"), SCOPES)
def test_each_reason_is_accepted_with_its_scope(reason: str, scope: str) -> None:
    stop = RepositoryStop.model_validate(_fields(scope=scope, reason=reason))

    assert (stop.reason, stop.scope) == (reason, scope)


@pytest.mark.parametrize(("reason", "scope"), SCOPES)
def test_each_reason_is_rejected_with_the_other_scope(reason: str, scope: str) -> None:
    with pytest.raises(ValidationError):
        RepositoryStop.model_validate(_fields(scope=OTHER_SCOPE[scope], reason=reason))


@pytest.mark.parametrize("reason", ["other", ""])
def test_an_unknown_reason_is_rejected(reason: str) -> None:
    with pytest.raises(ValidationError):
        RepositoryStop.model_validate(_fields(reason=reason))


def test_a_naive_time_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RepositoryStop.model_validate(_fields(at=datetime(2026, 10, 12, 12, 0)))  # noqa: DTZ001


def test_an_aware_time_is_stored_as_the_same_instant_in_utc() -> None:
    east = datetime(2026, 10, 12, 14, 0, tzinfo=timezone(timedelta(hours=2)))

    stop = RepositoryStop.model_validate(_fields(at=east))

    assert stop.at == east
    assert stop.at.utcoffset() == timedelta(0)


def test_both_models_reject_an_unknown_field() -> None:
    stop_model: type[BaseModel] = RepositoryStop
    status_model: type[BaseModel] = HealthStatus

    with pytest.raises(ValidationError):
        stop_model(**_fields(extra=1))
    with pytest.raises(ValidationError):
        status_model(stops=[], extra=1)


@pytest.mark.parametrize(
    ("instance", "field", "value"),
    [
        (_stop(), "detail", "changed"),
        (HealthStatus(), "stops", []),
    ],
    ids=["repository-stop", "health-status"],
)
def test_a_field_cannot_be_assigned(instance: BaseModel, field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        setattr(instance, field, value)


def test_a_status_is_healthy_exactly_when_it_holds_no_stop() -> None:
    assert HealthStatus().healthy
    assert not HealthStatus(stops=[_stop()]).healthy


def test_a_status_holds_at_most_one_stop_per_reason() -> None:
    with pytest.raises(ValidationError):
        HealthStatus(stops=[_stop("fetch_failed"), _stop("fetch_failed")])

    status = HealthStatus(stops=[_stop("fetch_failed"), _stop("preflight_failed")])

    assert [stop.reason for stop in status.stops] == ["fetch_failed", "preflight_failed"]
