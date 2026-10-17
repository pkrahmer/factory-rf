"""The token's folder: made in the image for the factory's user alone, the token mounted into it."""

from pathlib import Path, PurePosixPath

from ruamel.yaml import YAML

from dockerfile_support import DOCKERFILE, dockerfile_instructions
from test_image import _commands, _path_settings
from test_image_users import _uid_of

COMPOSE = Path(__file__).parent.parent / "image" / "compose.yml"
FOLDER = "/home/factory/.secrets"
FILE_ENV = "ENV FACTORY_TOKEN_FILE="


def _token_file() -> str:
    """The value the Dockerfile's `ENV FACTORY_TOKEN_FILE` sets."""
    values = [
        instruction.removeprefix(FILE_ENV)
        for instruction in dockerfile_instructions()
        if instruction.startswith(FILE_ENV)
    ]
    assert len(values) == 1
    return values[0]


def _token_mount() -> dict[str, object]:
    """The last entry of the compose service's volumes."""
    loaded = YAML(typ="safe").load(COMPOSE.read_text(encoding="utf-8"))
    mount = loaded["services"]["factory"]["volumes"][-1]
    assert isinstance(mount, dict)
    return mount


def test_the_image_makes_the_token_folder_for_the_factory_user_alone() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    created = [
        path
        for command in _commands(dockerfile)
        if command[:2] == ["mkdir", "-p"]
        for path in command
    ]

    assert FOLDER in created
    assert _path_settings(dockerfile, "chown")[FOLDER] == "factory:factory"
    assert _path_settings(dockerfile, "chmod")[FOLDER] == "0700"


def test_the_token_setting_points_into_the_folder_before_the_user_changes() -> None:
    instructions = dockerfile_instructions()
    setting = f"{FILE_ENV}{FOLDER}/hosting-token"

    assert instructions.index(setting) < instructions.index("USER factory")


def test_the_token_is_bind_mounted_read_only_at_the_setting_in_the_folder() -> None:
    mount = _token_mount()

    assert list(mount) == ["type", "source", "target", "read_only", "bind"]
    assert mount["type"] == "bind"
    assert mount["source"] == "./secrets/hosting-token"
    assert mount["read_only"] is True
    assert mount["bind"] == {"create_host_path": False}
    assert mount["target"] == _token_file()
    assert str(PurePosixPath(str(mount["target"])).parent) == FOLDER


def test_the_folder_belongs_to_the_factory_user_whom_the_agent_is_not() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    owner = _path_settings(dockerfile, "chown")[FOLDER].partition(":")[0]
    agent_useradds = [
        command
        for command in _commands(dockerfile)
        if command[:1] == ["useradd"] and command[-1] == "agent"
    ]
    group_values = [
        command[index + 1]
        for command in agent_useradds
        for index, word in enumerate(command[:-1])
        if word in {"--gid", "-g", "--groups", "-G"}
    ]

    assert owner == "factory"
    assert _uid_of("factory") == 1000
    assert _uid_of("agent") == 1001
    assert _uid_of("factory") != _uid_of("agent")
    assert _uid_of("agent") != 0
    assert len(agent_useradds) == 1
    assert all("factory" not in value.split(",") for value in group_values)
