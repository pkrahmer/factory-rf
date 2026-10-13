"""The git values the factory reasons about."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, field_validator

from factory.domain.kill_points import KillPoints

CommitId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]

PushOutcome = Literal["pushed", "rejected", "unreachable"]

# A rename is a deletion plus an addition, so that no tool's rename detection shapes the answer.
ChangeKind = Literal["added", "modified", "deleted"]

GIT_TIME_LIMIT = timedelta(minutes=5)


class RemoteBranch(BaseModel):
    """A branch as the remote holds it: its name without the remote's prefix, and its commit."""

    name: str
    commit: CommitId


class GitIdentity(BaseModel):
    """The author and committer of the factory's commits."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: Annotated[str, Field(min_length=1)]
    email: Annotated[str, Field(min_length=1)]


class GitOptions(BaseModel):
    """The settings of a git wrapper: identity, environment, kill points, executable, limit."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    identity: GitIdentity = GitIdentity(name="factory", email="factory@noreply.invalid")
    environment: dict[str, str] = {}
    kill_points: KillPoints | None = None
    executable: str = "git"
    time_limit: timedelta = GIT_TIME_LIMIT


class ChangedPath(BaseModel):
    """A path that differs from the state it is compared with, and how."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    change: ChangeKind


class CommitInfo(BaseModel):
    """One commit of a log: its id, parents, subject, author and committer date in UTC."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    commit: CommitId
    parents: list[CommitId]
    subject: str
    author: str
    committed_at: AwareDatetime

    @field_validator("committed_at")
    @classmethod
    def _in_utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)


class WorkTreeStatus(BaseModel):
    """The checked-out branch, the commit HEAD points to and what differs from it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    branch: str | None
    head: CommitId | None
    changes: list[ChangedPath]
