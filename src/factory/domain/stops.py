"""The stops of a repository, the machine and one work item, and the health status."""

from datetime import UTC, datetime
from typing import Literal, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    PositiveInt,
    field_validator,
    model_validator,
)

from factory.domain.hosting import PostKey, PostOutcome
from factory.domain.identifiers import branch_name

RepositoryStopReason = Literal[
    "fetch_failed",
    "checkout_restore_failed",
    "pipeline_definition_invalid",
    "agent_definition_invalid",
    "repository_unavailable",
    "main_branch_failing",
    "preflight_failed",
]
StopScope = Literal["repository", "machine"]

_MACHINE_REASON: RepositoryStopReason = "preflight_failed"


class RepositoryStop(BaseModel):
    """A fault that stops the repository or the machine, reported and never carried past."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scope: StopScope
    reason: RepositoryStopReason
    detail: str
    at: AwareDatetime

    @field_validator("detail")
    @classmethod
    def _detail_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("a stop's detail must name the fault")
        return value

    @field_validator("at")
    @classmethod
    def _to_utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def _scope_matches_reason(self) -> Self:
        expected: StopScope = "machine" if self.reason == _MACHINE_REASON else "repository"
        if self.scope != expected:
            raise ValueError(f"a stop for {self.reason} has the scope {expected}")
        return self


class HealthStatus(BaseModel):
    """The stops in force, at most one per reason; the file the health check reads."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stops: list[RepositoryStop] = []

    @field_validator("stops")
    @classmethod
    def _one_stop_per_reason(cls, value: list[RepositoryStop]) -> list[RepositoryStop]:
        reasons = [stop.reason for stop in value]
        duplicates = sorted({reason for reason in reasons if reasons.count(reason) > 1})
        if duplicates:
            raise ValueError(f"more than one stop for: {', '.join(duplicates)}")
        return value

    @property
    def healthy(self) -> bool:
        """True exactly when no stop is in force."""
        return not self.stops


class WorkItemStop(BaseModel):
    """A stop of one work item, posted once on its pull request under its key."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: PostKey
    branch: str
    title: str
    pull_request: PositiveInt | None
    text: str

    @field_validator("branch", "title", "text")
    @classmethod
    def _is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def _branch_is_the_work_items(self) -> Self:
        expected = branch_name(self.key.work_item)
        if self.branch != expected:
            raise ValueError(f"a stop of {self.key.work_item} belongs to the branch {expected}")
        return self


class StopPosted(BaseModel):
    """Where a work item's stop was posted, and whether its pull request is new to the state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pull_request: PositiveInt
    opened: bool
    outcome: PostOutcome
