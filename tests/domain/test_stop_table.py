"""The stop table: every stop v1 left in a log, with the destination v1.1 gives it."""

from collections import Counter
from typing import get_args

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.stop_table import STOP_TABLE, StopRow
from factory.domain.stops import RepositoryStopReason

REPOSITORY_TEST = "test_repository_stop_reaches_the_health_status_and_the_factory_log"
FIRST_ROW: dict[str, object] = {
    "id": "fetch-failed",
    "limits": ("L26", "L58"),
    "destination": "health_status",
    "reason": "fetch_failed",
    "test": REPOSITORY_TEST,
}
ROWS = [
    ("fetch-failed", ("L26", "L58"), "health_status", "fetch_failed", REPOSITORY_TEST),
    (
        "checkout-restore-failed",
        ("L64",),
        "health_status",
        "checkout_restore_failed",
        REPOSITORY_TEST,
    ),
    (
        "pipeline-definition-invalid",
        ("L64",),
        "health_status",
        "pipeline_definition_invalid",
        REPOSITORY_TEST,
    ),
    (
        "agent-definition-invalid",
        ("L30",),
        "health_status",
        "agent_definition_invalid",
        REPOSITORY_TEST,
    ),
    (
        "repository-unavailable",
        ("L64",),
        "health_status",
        "repository_unavailable",
        REPOSITORY_TEST,
    ),
    ("main-branch-failing", ("L65",), "health_status", "main_branch_failing", REPOSITORY_TEST),
    ("preflight-failed", ("L55",), "health_status", "preflight_failed", REPOSITORY_TEST),
    (
        "duplicate",
        ("L19",),
        "pull_request",
        None,
        "test_duplicate_is_a_counted_error_reported_once_on_the_pull_request",
    ),
    (
        "pull-request-lookup",
        ("L19",),
        "pull_request",
        None,
        "test_failed_pull_request_lookup_is_a_counted_error_reported_once",
    ),
    (
        "ask-without-pull-request",
        ("L19", "L26"),
        "pull_request",
        None,
        "test_ask_without_pull_request_is_reported_once_on_a_draft_pull_request_opened_first",
    ),
    (
        "handler-error",
        ("L26",),
        "pull_request",
        None,
        "test_handler_that_fails_every_time_is_reported_once_after_the_error_cap",
    ),
    (
        "hand-over-error",
        ("L33",),
        "pull_request",
        None,
        "test_hand_over_that_fails_every_time_is_reported_once_after_the_error_cap",
    ),
    (
        "push-rejected",
        ("L58",),
        "pull_request",
        None,
        "test_rejected_push_is_a_counted_error_reported_once",
    ),
    (
        "later-stage-in-backlog-file",
        ("L11",),
        "none",
        None,
        "test_story_file_naming_a_later_stage_starts_at_intake_with_no_stop",
    ),
]
V1_LIMITS = {"L11", "L19", "L26", "L30", "L33", "L55", "L58", "L64", "L65"}


def test_the_table_holds_the_fourteen_stops_in_order() -> None:
    rows = [(row.id, row.limits, row.destination, row.reason, row.test) for row in STOP_TABLE]

    assert rows == ROWS


def test_every_repository_stop_reason_is_the_reason_of_exactly_one_row() -> None:
    reasons = Counter(row.reason for row in STOP_TABLE if row.reason is not None)

    assert sorted(reasons) == sorted(get_args(RepositoryStopReason))
    assert set(reasons.values()) == {1}


def test_the_table_covers_every_limit_of_v1_whose_stop_reached_only_a_log() -> None:
    limits = {limit for row in STOP_TABLE for limit in row.limits}

    assert limits >= V1_LIMITS


@pytest.mark.parametrize(
    "changes",
    [
        {"reason": None},
        {"destination": "pull_request"},
        {"destination": "none"},
        {"limits": ()},
    ],
    ids=[
        "health-without-reason",
        "pull-request-with-reason",
        "none-with-reason",
        "no-limits",
    ],
)
def test_a_row_breaking_a_rule_of_the_table_is_rejected(changes: dict[str, object]) -> None:
    model: type[BaseModel] = StopRow

    with pytest.raises(ValidationError):
        model(**{**FIRST_ROW, **changes})


@pytest.mark.parametrize(
    ("limit", "accepted"),
    [
        ("L7", True),
        ("L65", True),
        ("L7\n", False),
        ("L7 ", False),
        ("L7x", False),
        ("L", False),
        ("l7", False),
        ("XL7", False),
        ("X7", False),
        ("L\u0663", False),
    ],
    ids=[
        "L7",
        "L65",
        "trailing-newline",
        "trailing-space",
        "trailing-letter",
        "no-digits",
        "lowercase",
        "prefix",
        "X7",
        "non-ascii-digit",
    ],
)
def test_a_limit_is_the_whole_text_l_and_ascii_digits(limit: str, accepted: bool) -> None:
    model: type[BaseModel] = StopRow
    fields = {**FIRST_ROW, "limits": (limit,)}

    if accepted:
        assert isinstance(model(**fields), StopRow)
    else:
        with pytest.raises(ValidationError):
            model(**fields)


def test_the_first_row_of_the_table_is_accepted() -> None:
    model: type[BaseModel] = StopRow

    row = model(**FIRST_ROW)

    assert row == STOP_TABLE[0]


def test_a_built_row_refuses_the_assignment_of_a_field() -> None:
    row = STOP_TABLE[0]
    field = "destination"

    with pytest.raises(ValidationError):
        setattr(row, field, "none")


@pytest.mark.parametrize(
    "changes",
    [{"severity": "high"}, {"destination": "log"}, {"reason": "v1_work_item_found"}],
    ids=["unknown-key", "unknown-destination", "unknown-reason"],
)
def test_a_row_with_an_unknown_key_or_value_is_rejected(changes: dict[str, object]) -> None:
    model: type[BaseModel] = StopRow

    with pytest.raises(ValidationError):
        model(**{**FIRST_ROW, **changes})
