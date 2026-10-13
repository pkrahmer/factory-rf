"""The factory log: time-stamped lines to standard output and an appended file."""

import sys
from datetime import UTC
from pathlib import Path
from typing import override

from factory.application.machine import Clock, FactoryLog

_STAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class TimestampedFactoryLog(FactoryLog):
    """Stamps every line with the UTC time in whole seconds."""

    def __init__(self, path: Path, clock: Clock) -> None:
        """Append to the file at `path`, stamping with the time of `clock`."""
        self._path = path
        self._clock = clock

    @override
    def line(self, text: str) -> None:
        stamp = self._clock.now().astimezone(UTC).strftime(_STAMP_FORMAT)
        lines = text.splitlines() or [""]
        stamped = "".join(f"{stamp} {line}\n" for line in lines)
        # Standard output first: the operator sees the line even when the file cannot take it.
        sys.stdout.write(stamped)
        sys.stdout.flush()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8", newline="\n") as file:
            file.write(stamped)
