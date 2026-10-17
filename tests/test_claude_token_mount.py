"""The agent's login: a host file mounted read-only in its home, its path set in the image."""

from pathlib import Path, PurePosixPath

from ruamel.yaml import YAML

from dockerfile_support import dockerfile_instructions
from factory.domain.settings import AGENT_HOME_VARIABLE, CLAUDE_LOGIN_FILE_VARIABLE

COMPOSE = Path(__file__).parent.parent / "image" / "compose.yml"
LOGIN_FILE = "/home/agent/.claude-token"
LOGIN_ENV = f"ENV FACTORY_CLAUDE_LOGIN_FILE={LOGIN_FILE}"
SECRETS_FOLDER = PurePosixPath("/home/factory/.secrets")


def _env_settings() -> dict[str, str]:
    """Every name the Dockerfile's `ENV` instructions set, with its value."""
    settings: dict[str, str] = {}
    for instruction in dockerfile_instructions():
        if instruction.startswith("ENV "):
            for pair in instruction.removeprefix("ENV ").split():
                name, _, value = pair.partition("=")
                settings[name] = value
    return settings


def _volumes() -> list[object]:
    """The compose service's volumes."""
    loaded = YAML(typ="safe").load(COMPOSE.read_text(encoding="utf-8"))
    volumes = loaded["services"]["factory"]["volumes"]
    assert isinstance(volumes, list)
    return volumes


def _login_mount() -> dict[str, object]:
    """The fourth entry of the compose service's volumes."""
    mount = _volumes()[3]
    assert isinstance(mount, dict)
    return mount


def test_the_image_sets_the_login_file_once_before_the_user_changes() -> None:
    instructions = dockerfile_instructions()

    assert instructions.count(LOGIN_ENV) == 1
    assert (
        instructions.index("ENV FACTORY_AGENT_USER=agent")
        < instructions.index(LOGIN_ENV)
        < instructions.index("USER factory")
    )


def test_the_image_sets_the_variable_the_settings_read() -> None:
    assert LOGIN_ENV.removeprefix("ENV ").partition("=")[0] == CLAUDE_LOGIN_FILE_VARIABLE
    assert _env_settings()[CLAUDE_LOGIN_FILE_VARIABLE] == LOGIN_FILE


def test_the_login_is_bind_mounted_read_only_at_the_image_setting() -> None:
    mount = _login_mount()

    assert list(mount) == ["type", "source", "target", "read_only", "bind"]
    assert mount["type"] == "bind"
    assert mount["source"] == "./secrets/claude-token"
    assert mount["read_only"] is True
    assert mount["bind"] == {"create_host_path": False}
    assert mount["target"] == _env_settings()[CLAUDE_LOGIN_FILE_VARIABLE]


def test_the_login_lies_in_the_agent_home_outside_secrets_and_named_volumes() -> None:
    target = PurePosixPath(str(_login_mount()["target"]))
    agent_home = PurePosixPath(_env_settings()[AGENT_HOME_VARIABLE])
    named_targets = [
        PurePosixPath(entry.partition(":")[2]) for entry in _volumes() if isinstance(entry, str)
    ]

    assert target.parent == PurePosixPath("/home/agent")
    assert target.parent == agent_home.parent
    assert not target.is_relative_to(SECRETS_FOLDER)
    assert named_targets == [
        PurePosixPath("/work"),
        PurePosixPath("/state"),
        PurePosixPath("/home/agent/.claude"),
    ]
    assert not any(target.is_relative_to(named) for named in named_targets)
