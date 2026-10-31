"""What a command-line tool printed, read into the details of the adapters' faults."""

import math
from datetime import timedelta

from factory.domain.printed_lines import printed_lines


def first_printed_line(output: str) -> str | None:
    """The first non-blank line of `output`, stripped, or `None`."""
    printed = printed_lines(output)
    return printed[0] if printed else None


def failure_detail(output: str, exit_status: int | None) -> str:
    """The last non-blank line of `output`, or `exit status <n>` when it has none."""
    printed = printed_lines(output)
    return printed[-1] if printed else f"exit status {exit_status}"


def no_end_detail(time_limit: timedelta) -> str:
    """The detail of a command that reached `time_limit`, in whole seconds rounded up."""
    return f"no end within {math.ceil(time_limit.total_seconds())} s"
