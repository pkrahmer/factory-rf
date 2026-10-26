"""The environment with the three required settings, shared by the tests that read settings."""

from collections.abc import Callable
from pathlib import Path

BASE = {
    "FACTORY_REPOSITORY_URL": "/srv/project.git",
    "FACTORY_INSTANCE": "factory-1",
    "FACTORY_CLAUDE_HOME": "/srv/factory/factory-1/factory/claude",
}


def raising(error: OSError) -> Callable[[Path], str]:
    """Return a file reader that raises `error` for every path."""

    def read_file(_path: Path) -> str:
        raise error

    return read_file
