"""The one conversion of a model's aware time to UTC."""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime


def in_utc(value: datetime) -> datetime:
    """`value`, an aware time, as the same instant in UTC."""
    return value.astimezone(UTC)


UtcDatetime = Annotated[AwareDatetime, AfterValidator(in_utc)]
