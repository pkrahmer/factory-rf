"""The preflight's report, the version rule and the machine stop a failed report becomes."""

from datetime import UTC, datetime

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.preflight import PreflightItem, PreflightReport, machine_stop, version_matches

AT = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)


def _passed(name: str) -> PreflightItem:
    return PreflightItem(name=name, passed=True)


def test_both_models_reject_an_unknown_field() -> None:
    item_model: type[BaseModel] = PreflightItem
    report_model: type[BaseModel] = PreflightReport

    with pytest.raises(ValidationError):
        item_model(name="tool:git", passed=True, extra=1)
    with pytest.raises(ValidationError):
        report_model(items=[], extra=1)


@pytest.mark.parametrize(
    ("instance", "field", "value"),
    [
        (_passed("tool:git"), "passed", False),
        (PreflightReport(items=[]), "items", []),
    ],
    ids=["item", "report"],
)
def test_a_field_cannot_be_assigned(instance: BaseModel, field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        setattr(instance, field, value)


@pytest.mark.parametrize(
    ("reported", "pinned", "expected"),
    [
        ("2.1.289", "2.1.289", True),
        ("2.1.289 (Claude Code)", "2.1.289", True),
        ("2.1.289", "", False),
        ("2.1.289", "   ", False),
        ("2.1.289-beta", "2.1.289", False),
        ("", "2.1.289", False),
    ],
    ids=["equal", "first-word", "empty-pin", "blank-pin", "suffixed", "empty-reported"],
)
def test_a_version_matches_exactly_when_its_first_word_is_the_pinned_one(
    reported: str, pinned: str, expected: bool
) -> None:
    assert version_matches(reported, pinned) is expected


@pytest.mark.parametrize(
    "report",
    [
        PreflightReport(items=[]),
        PreflightReport(items=[_passed("tool:git"), _passed("agents")]),
    ],
    ids=["empty", "all-passed"],
)
def test_a_passed_report_passes_and_makes_no_stop(report: PreflightReport) -> None:
    assert report.passed
    assert report.failed() == []
    assert machine_stop(report, at=AT) is None


def test_a_failed_report_becomes_one_machine_stop_naming_every_failed_item() -> None:
    uv = PreflightItem(name="tool:uv", passed=False, detail="uv is not on the PATH")
    version = PreflightItem(name="agent-runtime-version", passed=False, detail="2.1.290, 2.1.289")
    report = PreflightReport(items=[uv, _passed("agents"), version])

    stop = machine_stop(report, at=AT)

    assert not report.passed
    assert report.failed() == [uv, version]
    assert stop is not None
    assert stop.scope == "machine"
    assert stop.reason == "preflight_failed"
    assert stop.at == AT
    assert stop.detail == (
        "tool:uv: uv is not on the PATH; agent-runtime-version: 2.1.290, 2.1.289"
    )
