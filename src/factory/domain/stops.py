"""The stops of a repository, the machine and one work item, and the health status."""

from collections.abc import Sequence
from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    PositiveInt,
    ValidationError,
    field_validator,
    model_validator,
)

from factory.domain.hosting import PostKey, PostOutcome
from factory.domain.identifiers import Name, branch_name
from factory.domain.times import UtcDatetime

RepositoryStopReason = Literal[
    "fetch_failed",
    "checkout_restore_failed",
    "pipeline_definition_invalid",
    "agent_definition_invalid",
    "repository_unavailable",
    "main_branch_failing",
    "preflight_failed",
    "disk_low",
]
StopScope = Literal["repository", "machine"]
StopEvent = Literal["raised", "cleared"]

_MACHINE_REASONS: frozenset[RepositoryStopReason] = frozenset({"preflight_failed", "disk_low"})


def _require_scope_of_reason(scope: StopScope, reason: RepositoryStopReason) -> None:
    expected: StopScope = "machine" if reason in _MACHINE_REASONS else "repository"
    if scope != expected:
        raise ValueError(f"a stop for {reason} has the scope {expected}")


class RepositoryStop(BaseModel):
    """A fault that stops the repository or the machine, reported and never carried past."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scope: StopScope
    reason: RepositoryStopReason
    detail: str
    at: UtcDatetime

    @field_validator("detail")
    @classmethod
    def _detail_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("a stop's detail must name the fault")
        return value

    @model_validator(mode="after")
    def _scope_matches_reason(self) -> Self:
        _require_scope_of_reason(self.scope, self.reason)
        return self


class StopRecord(BaseModel):
    """One event of a stop of the repository or the machine, as the remote keeps it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event: StopEvent
    scope: StopScope
    reason: RepositoryStopReason
    at: UtcDatetime
    instance: Name | None = None

    @model_validator(mode="after")
    def _scope_matches_reason(self) -> Self:
        _require_scope_of_reason(self.scope, self.reason)
        return self


def stop_records_text(records: Sequence[StopRecord]) -> str:
    """One `model_dump_json()` line per record, each ending in a newline; `""` for none."""
    return "".join(record.model_dump_json() + "\n" for record in records)


def parse_stop_records(text: str) -> list[StopRecord]:
    """The records of the lines of `text` that validate, in order; other lines are skipped."""
    records: list[StopRecord] = []
    for line in text.splitlines():
        try:
            records.append(StopRecord.model_validate_json(line))
        except ValidationError:
            continue
    return records


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

    def with_stop(self, stop: RepositoryStop) -> "HealthStatus":
        """This status with `stop` added, in place of a stop of the same reason."""
        if any(known.reason == stop.reason for known in self.stops):
            return HealthStatus(
                stops=[stop if known.reason == stop.reason else known for known in self.stops]
            )
        return HealthStatus(stops=[*self.stops, stop])


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
