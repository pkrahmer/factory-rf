"""The folder of the agent files stays a setting after the agent's home reset is gone."""

from pathlib import Path

from factory.domain.settings import read_settings
from settings_support import BASE


def test_the_agent_files_folder_still_comes_from_its_variable() -> None:
    environ = {**BASE, "FACTORY_CLAUDE_HOME": "/srv/factory/vm/factory/claude"}

    assert read_settings(environ).agent_home == Path("/srv/factory/vm/factory/claude")
