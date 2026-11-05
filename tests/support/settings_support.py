"""The required and the container settings, the agent home and the container names' fault texts."""

from collections.abc import Callable
from pathlib import Path

AGENT_HOME = Path("/srv/factory/factory-1/factory/claude")
BASE = {
    "FACTORY_REPOSITORY_URL": "/srv/project.git",
    "FACTORY_INSTANCE": "factory-1",
    "FACTORY_CLAUDE_HOME": str(AGENT_HOME),
}
CONTAINER = {
    "FACTORY_DATASET": "tank/factory/vm",
    "FACTORY_WORKSPACE": "/srv/factory/vm/work",
    "FACTORY_STAGE_IMAGE": "factory-stage:1",
}
NOT_A_NAME = "which is not a variable name"
SET_BY_FACTORY = "which the factory sets itself"


def raising(error: OSError) -> Callable[[Path], str]:
    """Return a file reader that raises `error` for every path."""

    def read_file(_path: Path) -> str:
        raise error

    return read_file
