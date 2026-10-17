"""The record of one run of a project command, telemetry beside the factory log."""

from pydantic import BaseModel, ConfigDict

from factory.domain.checks import CheckStatus, CommandName, TargetTime
from factory.domain.cost_records import Duration
from factory.domain.git import CommitId
from factory.domain.times import UtcDatetime


class CommandRecord(BaseModel):
    """One run of a project command: what, on which commit, when, how long and how it ended."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    command: CommandName
    commit: CommitId | None
    started_at: UtcDatetime
    duration_seconds: Duration
    status: CheckStatus
    exit_status: int | None
    targets: list[TargetTime] = []
