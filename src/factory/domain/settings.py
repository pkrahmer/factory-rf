"""The settings of one factory instance: its one project, its name and its fixed paths."""

from collections.abc import Callable, Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict, PositiveInt, TypeAdapter, ValidationError

from factory.domain.errors import SettingsInvalid
from factory.domain.git import DEFAULT_GIT_IDENTITY, GitIdentity
from factory.domain.identifiers import Name

# The default identity is still read from here; its one definition is in the git module.
__all__ = ["DEFAULT_GIT_IDENTITY", "InstanceSettings", "read_setting_file", "read_settings"]

CHECKOUT_PATH = Path("/work/checkout")
STATE_DIRECTORY = Path("/state")
REPOSITORY_URL_VARIABLE = "FACTORY_REPOSITORY_URL"
INSTANCE_VARIABLE = "FACTORY_INSTANCE"
GIT_USER_NAME_VARIABLE = "GIT_USER_NAME"
GIT_USER_EMAIL_VARIABLE = "GIT_USER_EMAIL"
IMAGE_ID_FILE = Path("/opt/factory/image-id")
IMAGE_ID_FILE_VARIABLE = "FACTORY_IMAGE_ID_FILE"
AGENT_HOME_DEFAULT = Path("/home/agent/.claude")
AGENT_HOME_VARIABLE = "FACTORY_CLAUDE_HOME"
CLAUDE_EXECUTABLE_VARIABLE = "FACTORY_CLAUDE"
CLAUDE_VERSION_VARIABLE = "FACTORY_CLAUDE_VERSION"
# No word `token` in the name: ruff's S105 takes a string assigned to such a name for a secret.
CREDENTIAL_FILE_VARIABLE = "FACTORY_TOKEN_FILE"
AGENT_USER_VARIABLE = "FACTORY_AGENT_USER"
MIN_FREE_SPACE_VARIABLE = "FACTORY_MIN_FREE_GB"
DEFAULT_MIN_FREE_GB = 5
RUNS_DIRECTORY_NAME = "runs"
_HOME_VARIABLE = "HOME"
_CLAUDE_EXECUTABLE_DEFAULT = "claude"

_NAME = TypeAdapter(Name)


class InstanceSettings(BaseModel):
    """What one instance is told: its repository, its name, its commit identity and image."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_url: str
    instance: Name
    git_identity: GitIdentity = DEFAULT_GIT_IDENTITY
    image: str | None = None
    checkout: Path = CHECKOUT_PATH
    state_directory: Path = STATE_DIRECTORY
    agent_home: Path = AGENT_HOME_DEFAULT
    claude_executable: str = _CLAUDE_EXECUTABLE_DEFAULT
    token_file: Path | None = None
    pinned_agent_version: str | None = None
    agent_user: Name | None = None
    min_free_gb: PositiveInt = DEFAULT_MIN_FREE_GB
    temporary_directory: Path | None = None


def read_settings(
    environ: Mapping[str, str], read_file: Callable[[Path], str] | None = None
) -> InstanceSettings:
    """Read the settings from the environment and, given a reader, the image identity file."""
    repository_url = _repository_url(environ)
    instance = _instance(environ)
    image = None if read_file is None else _image(environ, read_file)
    return InstanceSettings(
        repository_url=repository_url,
        instance=instance,
        git_identity=_git_identity(environ),
        image=image,
        agent_home=_agent_home(environ),
        claude_executable=_optional(environ, CLAUDE_EXECUTABLE_VARIABLE)
        or _CLAUDE_EXECUTABLE_DEFAULT,
        token_file=_optional_path(environ, CREDENTIAL_FILE_VARIABLE),
        pinned_agent_version=_optional(environ, CLAUDE_VERSION_VARIABLE) or None,
        agent_user=_agent_user(environ),
        min_free_gb=_min_free_gb(environ),
    )


def _required(environ: Mapping[str, str], variable: str) -> str:
    value = environ.get(variable, "")
    if not value.strip():
        raise SettingsInvalid(variable, "missing")
    return value


def _repository_url(environ: Mapping[str, str]) -> str:
    url = _required(environ, REPOSITORY_URL_VARIABLE)
    if any(character.isspace() or character == "," for character in url):
        raise SettingsInvalid(REPOSITORY_URL_VARIABLE, "names more than one repository")
    if _holds_password(url):
        # Git would keep the password in the shared checkout's configuration, where agents read.
        raise SettingsInvalid(REPOSITORY_URL_VARIABLE, "holds a password; use the token file")
    return url


def _holds_password(url: str) -> bool:
    _, separator, rest = url.partition("://")
    if not separator:
        return False
    authority = rest.split("/", 1)[0]
    user_information, at, _ = authority.rpartition("@")
    return bool(at) and ":" in user_information


def _instance(environ: Mapping[str, str]) -> str:
    return _name(INSTANCE_VARIABLE, _required(environ, INSTANCE_VARIABLE))


def _agent_user(environ: Mapping[str, str]) -> str | None:
    agent_user = _optional(environ, AGENT_USER_VARIABLE)
    return _name(AGENT_USER_VARIABLE, agent_user) if agent_user else None


def _min_free_gb(environ: Mapping[str, str]) -> int:
    value = _optional(environ, MIN_FREE_SPACE_VARIABLE)
    if not value:
        return DEFAULT_MIN_FREE_GB
    # `isdigit` alone takes other scripts' digits, which `int` reads but no operator means.
    if not (value.isascii() and value.isdigit()) or int(value) < 1:
        raise SettingsInvalid(
            MIN_FREE_SPACE_VARIABLE, "is not a whole number of gigabytes of at least 1"
        )
    return int(value)


def _name(variable: str, value: str) -> str:
    try:
        return _NAME.validate_python(value)
    except ValidationError as error:
        raise SettingsInvalid(variable, "is not a name") from error


def _git_identity(environ: Mapping[str, str]) -> GitIdentity:
    return GitIdentity(
        name=_optional(environ, GIT_USER_NAME_VARIABLE) or DEFAULT_GIT_IDENTITY.name,
        email=_optional(environ, GIT_USER_EMAIL_VARIABLE) or DEFAULT_GIT_IDENTITY.email,
    )


def _optional(environ: Mapping[str, str], variable: str) -> str:
    return environ.get(variable, "").strip()


def _optional_path(environ: Mapping[str, str], variable: str) -> Path | None:
    value = _optional(environ, variable)
    return Path(value) if value else None


def _agent_home(environ: Mapping[str, str]) -> Path:
    agent_home = _optional_path(environ, AGENT_HOME_VARIABLE)
    if agent_home is not None:
        return agent_home
    home = _optional_path(environ, _HOME_VARIABLE)
    return AGENT_HOME_DEFAULT if home is None else home / ".claude"


def _image(environ: Mapping[str, str], read_file: Callable[[Path], str]) -> str:
    path = Path(environ.get(IMAGE_ID_FILE_VARIABLE) or IMAGE_ID_FILE)
    return read_setting_file(IMAGE_ID_FILE_VARIABLE, path, read_file)


def read_setting_file(variable: str, path: Path, read_file: Callable[[Path], str]) -> str:
    """Return the content of the file at `path`, which `variable` names, stripped of whitespace.

    Raises `SettingsInvalid` naming `variable` when the file cannot be read or is blank.
    """
    try:
        content = read_file(path).strip()
    except OSError as error:
        raise SettingsInvalid(variable, f"cannot read {path}: {error}") from error
    if not content:
        raise SettingsInvalid(variable, f"{path} is empty")
    return content
