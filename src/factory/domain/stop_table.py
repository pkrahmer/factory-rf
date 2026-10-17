"""Every stop v1 left only in a log, with the destination v1.1 gives it."""

import re
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

from factory.domain.stops import RepositoryStopReason

Destination = Literal["health_status", "pull_request", "none"]

_LIMIT = re.compile(r"^L\d+$")
_REPOSITORY_TEST = "test_repository_stop_reaches_the_health_status_and_the_factory_log"


class StopRow(BaseModel):
    """One stop: the v1 limits it answers, where v1.1 reports it and the test that proves it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    limits: tuple[str, ...]
    destination: Destination
    reason: RepositoryStopReason | None = None
    test: str

    @model_validator(mode="after")
    def _reason_matches_destination(self) -> Self:
        if (self.reason is not None) != (self.destination == "health_status"):
            raise ValueError("a stop has a reason exactly when it reaches the health status")
        return self

    @model_validator(mode="after")
    def _limits_name_v1_limits(self) -> Self:
        if not self.limits:
            raise ValueError("a stop answers at least one of v1's limits")
        for limit in self.limits:
            if not _LIMIT.match(limit):
                raise ValueError(f"{limit!r} is not one of v1's limits")
        return self


def _health(id: str, limits: tuple[str, ...], reason: RepositoryStopReason) -> StopRow:
    return StopRow(
        id=id, limits=limits, destination="health_status", reason=reason, test=_REPOSITORY_TEST
    )


def _pull_request(id: str, limits: tuple[str, ...], test: str) -> StopRow:
    return StopRow(id=id, limits=limits, destination="pull_request", test=test)


STOP_TABLE: tuple[StopRow, ...] = (
    _health("fetch-failed", ("L26", "L58"), "fetch_failed"),
    _health("checkout-restore-failed", ("L64",), "checkout_restore_failed"),
    _health("pipeline-definition-invalid", ("L64",), "pipeline_definition_invalid"),
    _health("agent-definition-invalid", ("L30",), "agent_definition_invalid"),
    _health("repository-unavailable", ("L64",), "repository_unavailable"),
    _health("main-branch-failing", ("L65",), "main_branch_failing"),
    _health("preflight-failed", ("L55",), "preflight_failed"),
    _pull_request(
        "duplicate",
        ("L19",),
        "test_duplicate_is_a_counted_error_reported_once_on_the_pull_request",
    ),
    _pull_request(
        "pull-request-lookup",
        ("L19",),
        "test_failed_pull_request_lookup_is_a_counted_error_reported_once",
    ),
    _pull_request(
        "ask-without-pull-request",
        ("L19", "L26"),
        "test_ask_without_pull_request_is_reported_once_on_a_draft_pull_request_opened_first",
    ),
    _pull_request(
        "handler-error",
        ("L26",),
        "test_handler_that_fails_every_time_is_reported_once_after_the_error_cap",
    ),
    _pull_request(
        "hand-over-error",
        ("L33",),
        "test_hand_over_that_fails_every_time_is_reported_once_after_the_error_cap",
    ),
    _pull_request(
        "push-rejected",
        ("L58",),
        "test_rejected_push_is_a_counted_error_reported_once",
    ),
    StopRow(
        id="later-stage-in-backlog-file",
        limits=("L11",),
        destination="none",
        test="test_story_file_naming_a_later_stage_starts_at_intake_with_no_stop",
    ),
)
