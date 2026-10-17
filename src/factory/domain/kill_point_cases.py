"""The cases of the recovery proof: what dies, where, and which pass list applies."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

from factory.domain.kill_points import KillPoint

Dies = Literal["tick", "agent-run", "container"]
ResultClass = Literal["crash", "stall"]


class KillPointCase(BaseModel):
    """One way the factory can die, and the result class its recovery must meet."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    dies: Dies
    kill_point: KillPoint | None
    result_class: ResultClass
    charges_crash: bool

    @model_validator(mode="after")
    def _kill_point_marks_a_crash(self) -> Self:
        # A stall is an agent run ending on its own, so no kill point fires.
        if (self.kill_point is None) != (self.result_class == "stall"):
            raise ValueError(
                f"kill point {self.kill_point} contradicts result class {self.result_class}"
            )
        return self

    @model_validator(mode="after")
    def _stall_charges_no_crash(self) -> Self:
        if self.result_class == "stall" and self.charges_crash:
            raise ValueError("a stall never charges a crash")
        return self


KILL_POINT_CASES: tuple[KillPointCase, ...] = (
    KillPointCase(
        id="agent-run-tick",
        dies="tick",
        kill_point=KillPoint.AGENT_RUN,
        result_class="crash",
        charges_crash=True,
    ),
    KillPointCase(
        id="agent-run-dies",
        dies="agent-run",
        kill_point=None,
        result_class="stall",
        charges_crash=False,
    ),
    KillPointCase(
        id="commit-push",
        dies="tick",
        kill_point=KillPoint.BEFORE_PUSH,
        result_class="crash",
        charges_crash=True,
    ),
    # The kill falls after the stage's result is pushed, so no stage is in flight.
    KillPointCase(
        id="post-record",
        dies="tick",
        kill_point=KillPoint.AFTER_POST,
        result_class="crash",
        charges_crash=False,
    ),
    KillPointCase(
        id="tick-other",
        dies="tick",
        kill_point=KillPoint.AFTER_PUSH,
        result_class="crash",
        charges_crash=True,
    ),
    KillPointCase(
        id="container",
        dies="container",
        kill_point=KillPoint.AGENT_RUN,
        result_class="crash",
        charges_crash=True,
    ),
)
