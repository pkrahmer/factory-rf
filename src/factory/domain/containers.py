"""The data of a container run: its mounts, the words that start it, its result and its call."""

from datetime import timedelta
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from factory.domain.agent_home import inside_home
from factory.domain.agent_runs import AbsolutePath

WORK = "/work"
WORK_CHECKOUT = "/work/checkout"
WORK_HOME = "/work/home"


def _must_be_container_path(target: str) -> str:
    if not target.startswith("/") or not inside_home(target.removeprefix("/")):
        raise ValueError(f"not an absolute container path: {target!r}")
    return target


ContainerPath = Annotated[str, AfterValidator(_must_be_container_path)]


class Mount(BaseModel):
    """A host path mounted into a container: its source, its target, read-only or not."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source: AbsolutePath
    target: ContainerPath
    read_only: bool = False


class ContainerLaunch(BaseModel):
    """The words, environment and time limit that start one command in a container."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    argv: Annotated[list[str], Field(min_length=1)]
    # `None`: the process's own environment.
    env: dict[str, str] | None
    time_limit: Annotated[timedelta, Field(gt=timedelta(0))]


class ContainerResult(BaseModel):
    """What one container run left: the command's exit status, its merged output, its end."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    exit_status: int | None
    output: str
    timed_out: bool
    duration: timedelta

    @model_validator(mode="after")
    def _no_exit_status_exactly_when_timed_out(self) -> Self:
        if (self.exit_status is None) != self.timed_out:
            raise ValueError(
                f"exit status {self.exit_status} contradicts timed_out {self.timed_out}"
            )
        return self


class ContainerCall(BaseModel):
    """One command a `ContainerRuns` was asked to launch or run, as it was asked."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    command: list[str]
    mounts: list[Mount]
    environment: dict[str, str]
    time_limit: timedelta
    working_directory: str
