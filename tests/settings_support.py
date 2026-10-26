"""The environment with the three required settings and the agent home the model requires."""

from collections.abc import Callable
from pathlib import Path

AGENT_HOME = Path("/srv/factory/factory-1/factory/claude")
BASE = {
    "FACTORY_REPOSITORY_URL": "/srv/project.git",
    "FACTORY_INSTANCE": "factory-1",
    "FACTORY_CLAUDE_HOME": str(AGENT_HOME),
}


def raising(error: OSError) -> Callable[[Path], str]:
    """Return a file reader that raises `error` for every path."""

    def read_file(_path: Path) -> str:
        raise error

    return read_file
