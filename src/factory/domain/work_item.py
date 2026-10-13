"""The state of a work item, its claim and the document that pairs a state with its body."""

from datetime import UTC, datetime
from typing import Literal, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    field_validator,
    model_validator,
)

from factory.domain.identifiers import Name
from factory.domain.journal import JournalRecord

Blocked = Literal["question", "attempts_cap", "round_cap", "crash_cap", "send_back"]


class Claim(BaseModel):
    """An instance's hold on a work item for one stage; the lease lasts `lease_duration` minutes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    instance: Name
    stage: Name
    started_at: AwareDatetime
    lease_duration: PositiveInt

    @field_validator("started_at")
    @classmethod
    def _to_utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)


class WorkItemState(BaseModel):
    """The state a work item keeps in its front matter, its fields in the order they are written."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stage: Name
    blocked: Blocked | None = None
    round: NonNegativeInt = 0
    attempts: NonNegativeInt = 0
    crashes: NonNegativeInt = 0
    pull_request: PositiveInt | None = None
    comments_read: list[PositiveInt] = []
    handed_over: Name | None = None
    claim: Claim | None = None
    journal: list[JournalRecord] = []

    @field_validator("comments_read")
    @classmethod
    def _comments_read_ascend_without_repeats(cls, comments: list[int]) -> list[int]:
        if comments != sorted(set(comments)):
            raise ValueError(f"comments read must ascend without repeats, got {comments}")
        return comments

    @field_validator("journal")
    @classmethod
    def _journal_numbered_from_one(cls, journal: list[JournalRecord]) -> list[JournalRecord]:
        numbers = [record.number for record in journal]
        if numbers != list(range(1, len(journal) + 1)):
            raise ValueError(f"journal records must be numbered 1 to n in order, got {numbers}")
        return journal

    @model_validator(mode="after")
    def _claim_is_for_the_current_stage(self) -> Self:
        if self.claim is not None and self.claim.stage != self.stage:
            raise ValueError(
                f"claim is for stage {self.claim.stage!r}, but the work item is at {self.stage!r}"
            )
        return self


class WorkItemDocument(BaseModel):
    """A work item file read: its state, or None for a specification, its body and ignored keys."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    state: WorkItemState | None
    body: str
    ignored_keys: list[str] = []


def initial_state(first_stage: str) -> WorkItemState:
    """Return the state of a story just started at the pipeline's first stage."""
    return WorkItemState(stage=first_stage)
