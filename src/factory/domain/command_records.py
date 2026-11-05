"""The record of one run of a project command, telemetry beside the factory log."""

from pydantic import BaseModel, ConfigDict

from factory.domain.checks import CheckStatus, CommandName, TargetTime
from factory.hosting.domain.git import CommitId
from factory.shared.domain.times import UtcDatetime
from factory.watching.domain.cost_records import Duration


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
