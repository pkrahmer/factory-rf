"""The bearer token of a model API and the wait before the next one is requested."""

from datetime import timedelta
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PositiveInt, StringConstraints

REFRESH_INTERVAL = timedelta(minutes=10)
MIN_REFRESH_INTERVAL = timedelta(seconds=30)
RETRY_INTERVAL = timedelta(minutes=1)

_MASK = "***"


class Token(BaseModel):
    """A bearer token and how many seconds it lives from its issue."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: Annotated[str, StringConstraints(pattern=r"^\S+$")]
    expires_in: PositiveInt


def refresh_wait(token: Token) -> timedelta:
    """The wait before the next refresh: the interval, half a shorter life, at least the floor."""
    # A token that lives under two intervals would otherwise expire between two refreshes.
    half_life = timedelta(seconds=token.expires_in) / 2
    return max(MIN_REFRESH_INTERVAL, min(REFRESH_INTERVAL, half_life))


def masked(message: str, hidden: list[str]) -> str:
    """`message` with every non-empty value of `hidden` replaced by `***`."""
    for value in hidden:
        if value:
            message = message.replace(value, _MASK)
    return message
