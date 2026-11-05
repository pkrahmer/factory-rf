"""A provider's spend limit: the pattern that shows it, the wait a text names, how long to wait."""

import re
from datetime import timedelta
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DEFAULT_LIMIT_STATUS = 428
LOWEST_STATUS = 100
HIGHEST_STATUS = 599
DEFAULT_COOLDOWN = timedelta(minutes=10)
DEFAULT_CEILING = timedelta(minutes=120)
SHORTEST_COOLDOWN = timedelta(minutes=1)

_SECONDS_PER_UNIT: dict[str, int] = {
    "": 1,
    "s": 1,
    "sec": 1,
    "second": 1,
    "seconds": 1,
    "m": 60,
    "min": 60,
    "minute": 60,
    "minutes": 60,
    "h": 3600,
    "hour": 3600,
    "hours": 3600,
}

# The longer unit names come first, so that `min` is not read as `m` followed by `in`.
_UNIT = "seconds|second|sec|s|minutes|minute|min|m|hours|hour|h"
_WAIT = re.compile(
    rf"\b(?:in|after)\s+(?P<amount>\d{{1,6}})(?!\d)(?:\s*(?P<unit>{_UNIT})\b)?"
    r"|\bretry-after:?\s*(?P<seconds>\d{1,6})(?!\d)",
    re.IGNORECASE,
)


class ProviderLimit(BaseModel):
    """How a provider's spend limit shows, and how long the factory waits it out.

    It shows by its HTTP status and, optionally, a message pattern. The factory waits a
    `cooldown` after each limit, until the waits reach the `ceiling`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: int = Field(default=DEFAULT_LIMIT_STATUS, ge=LOWEST_STATUS, le=HIGHEST_STATUS)
    message: str | None = None
    cooldown: timedelta = Field(default=DEFAULT_COOLDOWN, ge=SHORTEST_COOLDOWN)
    ceiling: timedelta = DEFAULT_CEILING

    @field_validator("message")
    @classmethod
    def _message_compiles(cls, message: str | None) -> str | None:
        if message is not None:
            # Pydantic turns only a ValueError into a validation error, and `re.error` is none.
            try:
                re.compile(message)
            except re.error as error:
                raise ValueError(f"message is not a regular expression: {error}") from error
        return message

    @model_validator(mode="after")
    def _ceiling_holds_the_cooldown(self) -> Self:
        if self.ceiling < self.cooldown:
            raise ValueError("the ceiling is shorter than the cool-down")
        return self


def limit_in_text(text: str, limit: ProviderLimit) -> bool:
    """Whether `text` holds the limit's status as a whole number, or its message pattern."""
    if re.search(rf"(?<!\d){limit.status}(?!\d)", text):
        return True
    return limit.message is not None and re.search(limit.message, text) is not None


def named_wait(text: str) -> timedelta | None:
    """The first wait `text` names (`in 7 minutes`, `Retry-After: 120`), or `None`."""
    match = _WAIT.search(text)
    if match is None:
        return None
    if match["seconds"] is not None:
        seconds = int(match["seconds"])
    else:
        unit = (match["unit"] or "").lower()
        seconds = int(match["amount"]) * _SECONDS_PER_UNIT[unit]
    return timedelta(seconds=seconds) if seconds > 0 else None
