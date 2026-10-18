"""The human's waits: one per blocking question, until the human's next record, and their line."""

from collections.abc import Sequence
from datetime import timedelta
from decimal import Decimal
from typing import get_args

from pydantic import BaseModel, ConfigDict, PositiveInt

from factory.domain.bills import one_decimal
from factory.domain.journal import HUMAN, Blocked, JournalRecord
from factory.domain.times import UtcDatetime

_SECONDS_PER_HOUR = Decimal(3600)


class HumanWait(BaseModel):
    """One wait for the human: the blocking question, its cause, when it was asked and answered."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    question: PositiveInt
    blocked: Blocked
    asked_at: UtcDatetime
    answered_at: UtcDatetime | None = None


def _answered_at(journal: Sequence[JournalRecord], question: int) -> UtcDatetime | None:
    # A comment's record carries the time it was copied from the pull request, so a wait
    # ends up to one tick after the human wrote.
    for record in journal:
        if record.number > question and record.speaker == HUMAN and record.at is not None:
            return record.at
    return None


def human_waits(journal: Sequence[JournalRecord]) -> list[HumanWait]:
    """One wait per question record with a `blocked` and an `at`, in journal order."""
    return [
        HumanWait(
            question=record.number,
            blocked=record.blocked,
            asked_at=record.at,
            answered_at=_answered_at(journal, record.number),
        )
        for record in journal
        if record.kind == "question" and record.blocked is not None and record.at is not None
    ]


def _hours(duration: timedelta) -> str:
    seconds = Decimal(str(duration.total_seconds()))
    return one_decimal(seconds / _SECONDS_PER_HOUR)


def _causes(answered: Sequence[HumanWait]) -> str:
    causes = [wait.blocked for wait in answered]
    return ", ".join(
        f"{cause} {causes.count(cause)}" for cause in get_args(Blocked) if cause in causes
    )


def human_line(waits: Sequence[HumanWait]) -> str:
    """`<n> questions answered (<cause> <count>, ...), <hours> h waited`."""
    answered: list[HumanWait] = []
    waited = timedelta(0)
    for wait in waits:
        if wait.answered_at is not None:
            answered.append(wait)
            waited += wait.answered_at - wait.asked_at
    causes = f" ({_causes(answered)})" if answered else ""
    return f"{len(answered)} questions answered{causes}, {_hours(waited)} h waited"
