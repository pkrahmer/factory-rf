"""The container's health check: the stops in force as lines, and an exit status."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from factory.application.machine import HealthStatusStore
from factory.domain.settings import STATE_DIRECTORY
from factory.domain.stops import RepositoryStop
from factory.entry.wiring import health_file, health_store

_PROGRAM = "factory-health"
_HEALTHY = 0
_STOPPED = 1


def _line(stop: RepositoryStop) -> str:
    since = stop.at.strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"{stop.reason} ({stop.scope}): {stop.detail} (since {since})"


def main(argv: Sequence[str] | None = None, *, store: HealthStatusStore | None = None) -> int:
    """Print `healthy` and return 0, or print one line per stop in force and return 1.

    The status is read from `store`, or from the health file of the state directory; a
    missing health file prints its path and returns 1.
    """
    parser = argparse.ArgumentParser(prog=_PROGRAM)
    parser.add_argument("--state-directory", type=Path, default=STATE_DIRECTORY)
    arguments = parser.parse_args(argv)
    state_directory: Path = arguments.state_directory
    if store is None:
        path = health_file(state_directory)
        if not path.exists():
            print(f"no health status: {path} is missing")
            return _STOPPED
        store = health_store(state_directory)
    status = store.read()
    if status.healthy:
        print("healthy")
        return _HEALTHY
    for stop in status.stops:
        print(_line(stop))
    return _STOPPED


if __name__ == "__main__":
    raise SystemExit(main())
