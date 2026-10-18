"""The cost record of one agent run, attributed to a work item, a stage and a role."""

from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    StringConstraints,
    field_validator,
    model_validator,
)

from factory.domain.agent_runs import EndReason, TokenCounts
from factory.domain.identifiers import Name, WorkItemId
from factory.domain.times import UtcDatetime

RunId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{32}$")]
Duration = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Cost = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]


class CostRecord(BaseModel):
    """One agent run: started, or completed with its measures; a measure `None` is unknown.

    `image` and `instance` say where the run ran: the machine's image and the name of
    the instance; either may be `None` on a record written without settings.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    run: RunId
    work_item: WorkItemId
    stage: Name
    role: Name
    attempt: NonNegativeInt
    status: Literal["started", "completed"]
    started_at: UtcDatetime
    duration_seconds: Duration | None = None
    model_seconds: Duration | None = None
    end_reason: EndReason | None = None
    turns: NonNegativeInt | None = None
    tokens: TokenCounts | None = None
    cost_usd: Cost | None = None
    image: str | None = None
    instance: Name | None = None

    @field_validator("cost_usd", mode="before")
    @classmethod
    def _cost_is_never_a_number(cls, value: object) -> object:
        # A float would round the cost; only a Decimal or its text keeps every digit.
        if value is None or isinstance(value, Decimal | str):
            return value
        raise ValueError(f"a cost is a Decimal or a string, got {type(value).__name__}")

    @model_validator(mode="after")
    def _measures_only_when_completed(self) -> Self:
        if self.status == "started":
            measures = {
                "duration_seconds": self.duration_seconds,
                "model_seconds": self.model_seconds,
                "end_reason": self.end_reason,
                "turns": self.turns,
                "tokens": self.tokens,
                "cost_usd": self.cost_usd,
            }
            for field, value in measures.items():
                if value is not None:
                    raise ValueError(f"a started record has no {field}")
        else:
            for field, value in (
                ("duration_seconds", self.duration_seconds),
                ("end_reason", self.end_reason),
            ):
                if value is None:
                    raise ValueError(f"a completed record needs {field}")
        return self

    @property
    def ok(self) -> bool:
        """Whether the run completed and ended as completed."""
        return self.status == "completed" and self.end_reason == "completed"
