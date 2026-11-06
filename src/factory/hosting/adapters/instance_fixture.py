"""The fixture `instance`: a valid instance's settings, state folder and bare remote."""

from pathlib import Path

from factory.hosting.adapters.git_cli import GitCli
from factory.pipeline.domain.stops import HealthStatus
from factory.shared.adapters.atomic_file import replace_text
from factory.shared.application.document_examples import Fixture
from factory.shared.domain.errors import FixtureError, GitError
from factory.shared.domain.settings import (
    AGENT_HOME_VARIABLE,
    CHECKOUT_VARIABLE,
    IMAGE_ID_FILE_VARIABLE,
    INSTANCE_VARIABLE,
    REPOSITORY_URL_VARIABLE,
    SNAPSHOT_BASE_VARIABLE,
    SNAPSHOTS_VARIABLE,
    STAGE_IMAGE_VARIABLE,
    STATE_VARIABLE,
    WORKSPACE_VARIABLE,
)
from factory.watching.adapters.health_file import HEALTH_FILE_NAME, JsonHealthStatusFile

INSTANCE_NAME = "docs"
SETTINGS_FILE = "factory.env"
_SNAPSHOTS = "copy"
_STAGE_IMAGE = "localhost/factory-stage:docs"
_IMAGE_ID = "docs"
_REMOTE_FOLDER = "remote.git"
_CHECKOUT_FOLDER = "checkout"
_STATE_FOLDER = "state"
_AGENT_HOME_FOLDER = "agent-home"
_WORKSPACE_FOLDER = "workspace"
_SNAPSHOT_BASE_FOLDER = "base"
_IMAGE_ID_FILE = "image-id"


def _environment(folder: Path) -> dict[str, str]:
    return {
        REPOSITORY_URL_VARIABLE: str(folder / _REMOTE_FOLDER),
        INSTANCE_VARIABLE: INSTANCE_NAME,
        CHECKOUT_VARIABLE: str(folder / _CHECKOUT_FOLDER),
        STATE_VARIABLE: str(folder / _STATE_FOLDER),
        AGENT_HOME_VARIABLE: str(folder / _AGENT_HOME_FOLDER),
        IMAGE_ID_FILE_VARIABLE: str(folder / _IMAGE_ID_FILE),
        WORKSPACE_VARIABLE: str(folder / _WORKSPACE_FOLDER),
        SNAPSHOTS_VARIABLE: _SNAPSHOTS,
        SNAPSHOT_BASE_VARIABLE: str(folder / _SNAPSHOT_BASE_FOLDER),
        STAGE_IMAGE_VARIABLE: _STAGE_IMAGE,
    }


def _settings_text(environment: dict[str, str]) -> str:
    return "".join(f"{name}={value}\n" for name, value in environment.items())


class InstanceFixture(Fixture):
    """Builds a healthy instance named `docs` whose remote is a bare clone of `git`'s copy."""

    def __init__(self, git: GitCli) -> None:
        """Make the instance's remote from the working copy of `git`."""
        self._git = git

    def prepare(self, folder: Path) -> dict[str, str]:
        """Build the instance in `folder` and return its settings as the environment."""
        root = folder.absolute()
        environment = _environment(root)
        try:
            self._git.clone_bare(Path(environment[REPOSITORY_URL_VARIABLE]))
        except GitError as error:
            raise FixtureError(str(error)) from error
        for variable in (AGENT_HOME_VARIABLE, WORKSPACE_VARIABLE, SNAPSHOT_BASE_VARIABLE):
            Path(environment[variable]).mkdir()
        state = Path(environment[STATE_VARIABLE])
        JsonHealthStatusFile(state / HEALTH_FILE_NAME).write(HealthStatus())
        replace_text(Path(environment[IMAGE_ID_FILE_VARIABLE]), _IMAGE_ID)
        replace_text(root / SETTINGS_FILE, _settings_text(environment))
        return environment
