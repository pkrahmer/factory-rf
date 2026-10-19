"""A provider's spend limit: the pattern that recognizes it in a text and the wait a text names."""

import re
from datetime import timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator

DEFAULT_LIMIT_STATUS = 428
LOWEST_STATUS = 100
HIGHEST_STATUS = 599

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
    """How a provider's spend limit shows: its HTTP status and, optionally, a message pattern."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: int = Field(default=DEFAULT_LIMIT_STATUS, ge=LOWEST_STATUS, le=HIGHEST_STATUS)
    message: str | None = None

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
