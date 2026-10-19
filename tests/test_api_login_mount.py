"""The agent's API login: a host file mounted read-only in its home, its path set in the image."""

from pathlib import PurePosixPath

from ruamel.yaml import YAML

from dockerfile_support import dockerfile_instructions
from factory.domain.settings import AGENT_HOME_VARIABLE, API_LOGIN_FILE_VARIABLE
from test_claude_token_mount import COMPOSE, LOGIN_ENV, SECRETS_FOLDER, _env_settings

API_LOGIN_FILE = "/home/agent/.anthropic-api-key"
API_LOGIN_ENV = f"ENV {API_LOGIN_FILE_VARIABLE}={API_LOGIN_FILE}"


def test_the_api_login_file_is_set_once_and_bind_mounted_read_only_in_the_agent_home() -> None:
    instructions = dockerfile_instructions()
    loaded = YAML(typ="safe").load(COMPOSE.read_text(encoding="utf-8"))
    volumes = loaded["services"]["factory"]["volumes"]
    mount = volumes[4]
    target = PurePosixPath(mount["target"])
    named_targets = [
        PurePosixPath(entry.partition(":")[2]) for entry in volumes if isinstance(entry, str)
    ]

    assert sum(f"{API_LOGIN_FILE_VARIABLE}=" in line for line in instructions) == 1
    assert instructions.count(API_LOGIN_ENV) == 1
    assert (
        instructions.index(LOGIN_ENV)
        < instructions.index(API_LOGIN_ENV)
        < instructions.index("USER factory")
    )
    assert mount == {
        "type": "bind",
        "source": "${FACTORY_API_KEY_FILE:-./secrets/anthropic-api-key}",
        "target": API_LOGIN_FILE,
        "read_only": True,
        "bind": {"create_host_path": False},
    }
    assert list(mount) == ["type", "source", "target", "read_only", "bind"]
    assert mount["target"] == _env_settings()[API_LOGIN_FILE_VARIABLE]
    assert target.parent == PurePosixPath(_env_settings()[AGENT_HOME_VARIABLE]).parent
    assert target.parent == PurePosixPath("/home/agent")
    assert not target.is_relative_to(SECRETS_FOLDER)
    assert not any(target.is_relative_to(named) for named in named_targets)
