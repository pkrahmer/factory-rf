"""opencode's configuration folder: made by the image, read-only to the agent."""

import re

import pytest

from dockerfile_support import dockerfile_instructions
from test_image import DOCKERFILE, _commands, _path_settings

CONFIGURATION = "/home/agent/.config/opencode"
MKDIR = f"mkdir -p {CONFIGURATION}"
AGENT_USERADD = re.compile(r"useradd [^&]*\bagent(\s|$)")


@pytest.mark.parametrize(
    ("path", "owner", "mode"),
    [
        pytest.param(CONFIGURATION, "factory:factory-work", "0755", id="configuration"),
        pytest.param("/home/agent/.config", "agent:factory-work", "0755", id="parent"),
    ],
)
def test_the_image_makes_the_configuration_folder_read_only_and_leaves_its_parent_the_agents(
    path: str, owner: str, mode: str
) -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    made = [command[2:] for command in _commands(dockerfile) if command[:2] == ["mkdir", "-p"]]

    assert any(CONFIGURATION in paths for paths in made)
    assert _path_settings(dockerfile, "chown")[path] == owner
    assert _path_settings(dockerfile, "chmod")[path] == mode
    assert int(mode, 8) & 0o022 == 0


def test_the_configuration_folder_is_made_right_after_the_agent_is_added() -> None:
    instructions = dockerfile_instructions()
    making = [
        index
        for index, line in enumerate(instructions)
        if line.startswith("RUN ") and MKDIR in line
    ]
    adding = [
        index
        for index, line in enumerate(instructions)
        if line.startswith("RUN ") and AGENT_USERADD.search(line)
    ]

    assert len(making) == 1
    assert len(adding) == 1
    assert making[0] == adding[0] + 1
    assert making[0] < instructions.index("WORKDIR /opt/factory")
    assert making[0] < instructions.index("USER factory")
