"""The git values the factory reasons about."""

from datetime import timedelta
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from factory.domain.kill_points import KillPoints

CommitId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]

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
