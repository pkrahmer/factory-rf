"""The settings of one factory instance: its one project, its name and its fixed paths."""

from collections.abc import Callable, Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from factory.domain.errors import SettingsInvalid
from factory.domain.git import GitIdentity
from factory.domain.identifiers import Name

CHECKOUT_PATH = Path("/work/checkout")
STATE_DIRECTORY = Path("/state")
REPOSITORY_URL_VARIABLE = "FACTORY_REPOSITORY_URL"
INSTANCE_VARIABLE = "FACTORY_INSTANCE"
GIT_USER_NAME_VARIABLE = "GIT_USER_NAME"
GIT_USER_EMAIL_VARIABLE = "GIT_USER_EMAIL"
DEFAULT_GIT_IDENTITY = GitIdentity(name="factory", email="factory@noreply.invalid")
IMAGE_ID_FILE = Path("/opt/factory/image-id")
IMAGE_ID_FILE_VARIABLE = "FACTORY_IMAGE_ID_FILE"

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
    instance = _required(environ, INSTANCE_VARIABLE)
    try:
        return _NAME.validate_python(instance)
    except ValidationError as error:
        raise SettingsInvalid(INSTANCE_VARIABLE, "is not a name") from error


def _git_identity(environ: Mapping[str, str]) -> GitIdentity:
    return GitIdentity(
        name=_optional(environ, GIT_USER_NAME_VARIABLE) or DEFAULT_GIT_IDENTITY.name,
        email=_optional(environ, GIT_USER_EMAIL_VARIABLE) or DEFAULT_GIT_IDENTITY.email,
    )


def _optional(environ: Mapping[str, str], variable: str) -> str:
    return environ.get(variable, "").strip()


def _image(environ: Mapping[str, str], read_file: Callable[[Path], str]) -> str:
    path = Path(environ.get(IMAGE_ID_FILE_VARIABLE) or IMAGE_ID_FILE)
    try:
        image = read_file(path).strip()
    except OSError as error:
        raise SettingsInvalid(IMAGE_ID_FILE_VARIABLE, f"cannot read {path}: {error}") from error
    if not image:
        raise SettingsInvalid(IMAGE_ID_FILE_VARIABLE, f"{path} is empty")
    return image
