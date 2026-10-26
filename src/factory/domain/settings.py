"""The settings of one factory instance: its one project, its name and its paths."""

import re
from collections.abc import Callable, Mapping
from datetime import timedelta
from pathlib import Path
from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)

from factory.domain.errors import SettingsInvalid
from factory.domain.git import DEFAULT_GIT_IDENTITY, GitIdentity
from factory.domain.identifiers import Name
from factory.domain.provider_limits import (
    DEFAULT_CEILING,
    DEFAULT_COOLDOWN,
    DEFAULT_LIMIT_STATUS,
    HIGHEST_STATUS,
    LOWEST_STATUS,
    ProviderLimit,
)

# The default identity is still read from here; its one definition is in the git module.
__all__ = [
    "DEFAULT_GIT_IDENTITY",
    "InstanceSettings",
    "named_state_directory",
    "read_setting_file",
    "read_settings",
]

CHECKOUT_PATH = Path("/work/checkout")
STATE_DIRECTORY = Path("/state")
REPOSITORY_URL_VARIABLE = "FACTORY_REPOSITORY_URL"
INSTANCE_VARIABLE = "FACTORY_INSTANCE"
CHECKOUT_VARIABLE = "FACTORY_CHECKOUT"
STATE_VARIABLE = "FACTORY_STATE"
GIT_USER_NAME_VARIABLE = "GIT_USER_NAME"
GIT_USER_EMAIL_VARIABLE = "GIT_USER_EMAIL"
IMAGE_ID_FILE_VARIABLE = "FACTORY_IMAGE_ID_FILE"
AGENT_HOME_VARIABLE = "FACTORY_CLAUDE_HOME"
CLAUDE_EXECUTABLE_VARIABLE = "FACTORY_CLAUDE"
CLAUDE_VERSION_VARIABLE = "FACTORY_CLAUDE_VERSION"
# No word `token` in the name: ruff's S105 takes a string assigned to such a name for a secret.
CREDENTIAL_FILE_VARIABLE = "FACTORY_TOKEN_FILE"
CLAUDE_LOGIN_FILE_VARIABLE = "FACTORY_CLAUDE_LOGIN_FILE"
API_LOGIN_FILE_VARIABLE = "FACTORY_API_LOGIN_FILE"
MIN_FREE_SPACE_VARIABLE = "FACTORY_MIN_FREE_GB"
DEFAULT_MIN_FREE_GB = 5
PROVIDER_LIMIT_STATUS_VARIABLE = "FACTORY_PROVIDER_LIMIT_STATUS"
PROVIDER_LIMIT_MESSAGE_VARIABLE = "FACTORY_PROVIDER_LIMIT_MESSAGE"
PROVIDER_LIMIT_COOLDOWN_VARIABLE = "FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES"
PROVIDER_LIMIT_CEILING_VARIABLE = "FACTORY_PROVIDER_LIMIT_CEILING_MINUTES"
AGENT_RUNTIME_VARIABLE = "FACTORY_AGENT_RUNTIME"
OPENCODE_EXECUTABLE_VARIABLE = "FACTORY_OPENCODE"
OPENCODE_VERSION_VARIABLE = "FACTORY_OPENCODE_VERSION"
OPENCODE_MODELS_VARIABLE = "FACTORY_OPENCODE_MODELS"
OPENCODE_PROVIDER_FILE_VARIABLE = "FACTORY_OPENCODE_PROVIDER_FILE"
DATASET_VARIABLE = "FACTORY_DATASET"
WORKSPACE_VARIABLE = "FACTORY_WORKSPACE"
STAGE_IMAGE_VARIABLE = "FACTORY_STAGE_IMAGE"
PODMAN_EXECUTABLE_VARIABLE = "FACTORY_PODMAN"
ZFS_EXECUTABLE_VARIABLE = "FACTORY_ZFS"
CONTAINER_ENV_VARIABLE = "FACTORY_CONTAINER_ENV"
CA_BUNDLE_VARIABLE = "FACTORY_CA_BUNDLE"
IDLE_SHUTDOWN_VARIABLE = "FACTORY_IDLE_SHUTDOWN_MINUTES"
# The names the factory gives a container itself: the home, the logins, opencode's
# configuration, git's credential prompt, and every name of its own.
RESERVED_CONTAINER_NAMES = frozenset(
    {"HOME", "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "OPENCODE_CONFIG", "GIT_ASKPASS"}
)
RESERVED_CONTAINER_PREFIX = "FACTORY_"
RUNS_DIRECTORY_NAME = "runs"
_CLAUDE_EXECUTABLE_DEFAULT = "claude"
_OPENCODE_EXECUTABLE_DEFAULT = "opencode"
_PODMAN_EXECUTABLE_DEFAULT = "podman"
_ZFS_EXECUTABLE_DEFAULT = "zfs"
_NOT_ABSOLUTE = "is not an absolute path"

AgentRuntimeName = Literal["claude", "opencode"]
_AGENT_RUNTIMES: tuple[AgentRuntimeName, ...] = ("claude", "opencode")

_NAME = TypeAdapter(Name)
_VARIABLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class InstanceSettings(BaseModel):
    """What one instance is told: its repository, its name, its commit identity and image."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    repository_url: str
    instance: Name
    git_identity: GitIdentity = DEFAULT_GIT_IDENTITY
    image: str | None = None
    checkout: Path = CHECKOUT_PATH
    state_directory: Path = STATE_DIRECTORY
    agent_home: Path
    claude_executable: str = _CLAUDE_EXECUTABLE_DEFAULT
    token_file: Path | None = None
    claude_login_file: Path | None = None
    api_login_file: Path | None = None
    pinned_agent_version: str | None = None
    min_free_gb: PositiveInt = DEFAULT_MIN_FREE_GB
    temporary_directory: Path | None = None
    provider_limit: ProviderLimit = ProviderLimit()
    agent_runtime: AgentRuntimeName = "claude"
    opencode_executable: str = _OPENCODE_EXECUTABLE_DEFAULT
    pinned_opencode_version: str | None = None
    opencode_models: dict[str, str] = {}
    opencode_provider_file: Path | None = None
    dataset: str | None = None
    workspace: Path | None = None
    stage_image: str | None = None
    podman_executable: str = _PODMAN_EXECUTABLE_DEFAULT
    zfs_executable: str = _ZFS_EXECUTABLE_DEFAULT
    container_env: tuple[str, ...] = ()
    ca_bundle: Path | None = None
    idle_shutdown_minutes: NonNegativeInt = 0

    @field_validator(
        "checkout", "state_directory", "agent_home", "opencode_provider_file", "ca_bundle"
    )
    @classmethod
    def _absolute(cls, path: Path | None) -> Path | None:
        if path is not None and not path.is_absolute():
            raise ValueError(_NOT_ABSOLUTE)
        return path

    @field_validator("container_env")
    @classmethod
    def _container_names(cls, names: tuple[str, ...]) -> tuple[str, ...]:
        fault = container_env_fault(names)
        if fault is not None:
            raise ValueError(fault)
        return names

    @model_validator(mode="after")
    def _workspace_apart(self) -> Self:
        fault = workspace_overlap_fault(self.workspace, self.checkout, self.state_directory)
        if fault is not None:
            variable, text = fault
            raise ValueError(f"{variable}: {text}")
        return self


def workspace_overlap_fault(
    workspace: Path | None, checkout: Path, state_directory: Path
) -> tuple[str, str] | None:
    """The variable and the fault of a relative workspace or of a path inside it.

    `None` without a workspace and for an absolute one that holds neither the checkout nor the
    state directory.
    """
    if workspace is None:
        return None
    if not workspace.is_absolute():
        return WORKSPACE_VARIABLE, _NOT_ABSOLUTE
    # Every rollback of the dataset would reset the factory's own work tree, and the agent's
    # container would reach the health file and the runs.
    for variable, path in ((CHECKOUT_VARIABLE, checkout), (STATE_VARIABLE, state_directory)):
        if path.is_relative_to(workspace):
            return variable, f"{path} lies inside FACTORY_WORKSPACE"
    return None


def read_settings(
    environ: Mapping[str, str], read_file: Callable[[Path], str] | None = None
) -> InstanceSettings:
    """Read the settings from the environment and, given a reader, the image identity file."""
    repository_url = _repository_url(environ)
    instance = _instance(environ)
    checkout = _absolute_path(environ, CHECKOUT_VARIABLE, CHECKOUT_PATH)
    state_directory = _absolute_path(environ, STATE_VARIABLE, STATE_DIRECTORY)
    image = None if read_file is None else _image(environ, read_file)
    dataset = _optional(environ, DATASET_VARIABLE) or None
    workspace = _optional_path(environ, WORKSPACE_VARIABLE)
    stage_image = _optional(environ, STAGE_IMAGE_VARIABLE) or None
    # Checked here too, so that a fault names its variable instead of a validation error.
    fault = workspace_overlap_fault(workspace, checkout, state_directory)
    if fault is not None:
        raise SettingsInvalid(*fault)
    return InstanceSettings(
        repository_url=repository_url,
        instance=instance,
        git_identity=_git_identity(environ),
        image=image,
        checkout=checkout,
        state_directory=state_directory,
        agent_home=_agent_home(environ),
        claude_executable=_optional(environ, CLAUDE_EXECUTABLE_VARIABLE)
        or _CLAUDE_EXECUTABLE_DEFAULT,
        token_file=_optional_path(environ, CREDENTIAL_FILE_VARIABLE),
        claude_login_file=_optional_path(environ, CLAUDE_LOGIN_FILE_VARIABLE),
        api_login_file=_optional_path(environ, API_LOGIN_FILE_VARIABLE),
        pinned_agent_version=_optional(environ, CLAUDE_VERSION_VARIABLE) or None,
        min_free_gb=_min_free_gb(environ),
        provider_limit=_provider_limit(environ),
        agent_runtime=_agent_runtime(environ),
        opencode_executable=_optional(environ, OPENCODE_EXECUTABLE_VARIABLE)
        or _OPENCODE_EXECUTABLE_DEFAULT,
        pinned_opencode_version=_optional(environ, OPENCODE_VERSION_VARIABLE) or None,
        opencode_models=_opencode_models(environ),
        opencode_provider_file=_optional_absolute_path(environ, OPENCODE_PROVIDER_FILE_VARIABLE),
        dataset=dataset,
        workspace=workspace,
        stage_image=stage_image,
        podman_executable=_optional(environ, PODMAN_EXECUTABLE_VARIABLE)
        or _PODMAN_EXECUTABLE_DEFAULT,
        zfs_executable=_optional(environ, ZFS_EXECUTABLE_VARIABLE) or _ZFS_EXECUTABLE_DEFAULT,
        container_env=_container_env(environ),
        ca_bundle=_optional_absolute_path(environ, CA_BUNDLE_VARIABLE),
        idle_shutdown_minutes=_idle_shutdown_minutes(environ),
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


def _agent_runtime(environ: Mapping[str, str]) -> AgentRuntimeName:
    value = _optional(environ, AGENT_RUNTIME_VARIABLE)
    if not value:
        return "claude"
    for runtime in _AGENT_RUNTIMES:
        if value == runtime:
            return runtime
    raise SettingsInvalid(
        AGENT_RUNTIME_VARIABLE, f"holds {value}, which is neither claude nor opencode"
    )


def _opencode_models(environ: Mapping[str, str]) -> dict[str, str]:
    value = _optional(environ, OPENCODE_MODELS_VARIABLE)
    models: dict[str, str] = {}
    if not value:
        return models
    for entry in value.split(","):
        alias, model = _opencode_model(entry.strip())
        if alias in models:
            raise SettingsInvalid(OPENCODE_MODELS_VARIABLE, f"names {alias} twice")
        models[alias] = model
    return models


def _opencode_model(entry: str) -> tuple[str, str]:
    alias, equals, model = (part.strip() for part in entry.partition("="))
    # The provider is the part before the first slash; the model may hold slashes of its own.
    provider, slash, model_name = model.partition("/")
    if not (equals and alias and slash and provider and model_name):
        raise SettingsInvalid(
            OPENCODE_MODELS_VARIABLE, f"holds {entry}, which is not <alias>=<provider>/<model>"
        )
    return alias, model


def _container_env(environ: Mapping[str, str]) -> tuple[str, ...]:
    parts = _optional(environ, CONTAINER_ENV_VARIABLE).split(",")
    names = tuple(name for name in (part.strip() for part in parts) if name)
    # Checked here too, so that a fault names its variable instead of a validation error.
    fault = container_env_fault(names)
    if fault is not None:
        raise SettingsInvalid(CONTAINER_ENV_VARIABLE, fault)
    return names


def container_env_fault(names: tuple[str, ...]) -> str | None:
    """The fault of the first name, in order, that a container may not be given; else `None`."""
    seen: set[str] = set()
    for name in names:
        if not _VARIABLE_NAME.fullmatch(name):
            return f"holds {name}, which is not a variable name"
        if name in RESERVED_CONTAINER_NAMES or name.startswith(RESERVED_CONTAINER_PREFIX):
            return f"holds {name}, which the factory sets itself"
        if name in seen:
            return f"names {name} twice"
        seen.add(name)
    return None


def _min_free_gb(environ: Mapping[str, str]) -> int:
    value = _whole_number(environ, MIN_FREE_SPACE_VARIABLE, "gigabytes")
    return DEFAULT_MIN_FREE_GB if value is None else value


def _whole_number(environ: Mapping[str, str], variable: str, unit: str) -> int | None:
    value = _optional(environ, variable)
    if not value:
        return None
    # `isdigit` alone takes other scripts' digits, which `int` reads but no operator means.
    if not (value.isascii() and value.isdigit()) or int(value) < 1:
        raise SettingsInvalid(variable, f"is not a whole number of {unit} of at least 1")
    return int(value)


def _idle_shutdown_minutes(environ: Mapping[str, str]) -> int:
    value = _optional(environ, IDLE_SHUTDOWN_VARIABLE)
    if not value:
        return 0
    # `isdigit` alone takes other scripts' digits, which `int` reads but no operator means.
    if not (value.isascii() and value.isdigit()):
        raise SettingsInvalid(IDLE_SHUTDOWN_VARIABLE, "is not a whole number of minutes")
    return int(value)


def _provider_limit(environ: Mapping[str, str]) -> ProviderLimit:
    cooldown = _minutes(environ, PROVIDER_LIMIT_COOLDOWN_VARIABLE, DEFAULT_COOLDOWN)
    ceiling = _minutes(environ, PROVIDER_LIMIT_CEILING_VARIABLE, DEFAULT_CEILING)
    if ceiling < cooldown:
        raise SettingsInvalid(PROVIDER_LIMIT_CEILING_VARIABLE, "is shorter than the cool-down")
    return ProviderLimit(
        status=_provider_limit_status(environ),
        message=_provider_limit_message(environ),
        cooldown=cooldown,
        ceiling=ceiling,
    )


def _minutes(environ: Mapping[str, str], variable: str, default: timedelta) -> timedelta:
    minutes = _whole_number(environ, variable, "minutes")
    return default if minutes is None else timedelta(minutes=minutes)


def _provider_limit_status(environ: Mapping[str, str]) -> int:
    value = _optional(environ, PROVIDER_LIMIT_STATUS_VARIABLE)
    if not value:
        return DEFAULT_LIMIT_STATUS
    # `isdigit` alone takes other scripts' digits, which `int` reads but no operator means.
    if not (value.isascii() and value.isdigit()) or not (
        LOWEST_STATUS <= int(value) <= HIGHEST_STATUS
    ):
        raise SettingsInvalid(
            PROVIDER_LIMIT_STATUS_VARIABLE,
            f"is not an HTTP status from {LOWEST_STATUS} to {HIGHEST_STATUS}",
        )
    return int(value)


def _provider_limit_message(environ: Mapping[str, str]) -> str | None:
    value = _optional(environ, PROVIDER_LIMIT_MESSAGE_VARIABLE)
    if not value:
        return None
    try:
        re.compile(value)
    except re.error as error:
        raise SettingsInvalid(
            PROVIDER_LIMIT_MESSAGE_VARIABLE, f"is not a regular expression: {error}"
        ) from error
    return value


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


def _absolute_path(environ: Mapping[str, str], variable: str, default: Path) -> Path:
    path = _optional_absolute_path(environ, variable)
    return default if path is None else path


def _optional_absolute_path(environ: Mapping[str, str], variable: str) -> Path | None:
    path = _optional_path(environ, variable)
    if path is not None and not path.is_absolute():
        raise SettingsInvalid(variable, _NOT_ABSOLUTE)
    return path


def named_state_directory(environ: Mapping[str, str]) -> Path | None:
    """The state directory `environ` names, or `None` when it names none or a relative one."""
    path = _optional_path(environ, STATE_VARIABLE)
    return path if path is not None and path.is_absolute() else None


def _agent_home(environ: Mapping[str, str]) -> Path:
    return _required_absolute_path(environ, AGENT_HOME_VARIABLE)


def _image(environ: Mapping[str, str], read_file: Callable[[Path], str]) -> str:
    path = _required_absolute_path(environ, IMAGE_ID_FILE_VARIABLE)
    return read_setting_file(IMAGE_ID_FILE_VARIABLE, path, read_file)


def _required_absolute_path(environ: Mapping[str, str], variable: str) -> Path:
    path = Path(_required(environ, variable).strip())
    if not path.is_absolute():
        raise SettingsInvalid(variable, _NOT_ABSOLUTE)
    return path


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
