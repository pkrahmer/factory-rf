"""Answers for a recording stand-in of the project commands."""

from collections.abc import Callable
from datetime import timedelta

from factory.domain.checks import CheckResult


def raising(error: Exception) -> Callable[[str, timedelta], CheckResult]:
    """Return an answer that raises `error` on every run."""

    def answer(_command: str, _limit: timedelta) -> CheckResult:
        raise error

    return answer
