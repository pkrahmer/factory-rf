"""The generic result of a project command, judged by its exit status alone."""

import re
from datetime import timedelta
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, NonNegativeFloat, StringConstraints, model_validator

OUTPUT_TAIL_LINES = 30

CheckStatus = Literal["passed", "failed", "time_limit"]

COMMAND_NAME_PATTERN = r"^[a-z][a-z0-9-]*$"

CommandName = Annotated[str, StringConstraints(pattern=COMMAND_NAME_PATTERN)]

_TARGET_NAME = COMMAND_NAME_PATTERN.removeprefix("^").removesuffix("$")

_TARGET_TIME_LINE = re.compile(rf"({_TARGET_NAME}): green \(([0-9]+(?:\.[0-9]+)?) s\)")


def status_of(exit_status: int | None) -> CheckStatus:
    """The status an exit status means; `None` is a command ended by its time limit."""
    if exit_status is None:
        return "time_limit"
    return "passed" if exit_status == 0 else "failed"


class TargetTime(BaseModel):
    """One target of a project command that ended green, and the seconds it took."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target: CommandName
    seconds: NonNegativeFloat


def target_times(output: str) -> list[TargetTime]:
    """The `<target>: green (<seconds> s)` lines of `output`, in their order."""
    times = []
    for line in output.splitlines():
        match = _TARGET_TIME_LINE.fullmatch(line)
        if match:
            times.append(TargetTime(target=match[1], seconds=float(match[2])))
    return times


class CheckResult(BaseModel):
    """How a project command ended, with the last line and the tail of its output."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    command: CommandName
    status: CheckStatus
    exit_status: int | None
    duration: timedelta
    last_line: str
    output_tail: str
    targets: list[TargetTime] = []

    @model_validator(mode="after")
    def _status_follows_exit_status(self) -> Self:
        if self.status != status_of(self.exit_status):
            raise ValueError(f"status {self.status} contradicts exit status {self.exit_status}")
        return self

    @property
    def passed(self) -> bool:
        """Whether the command exited with status 0."""
        return self.status == "passed"
