"""The agent run's `HOME` is the dataset's home in a container and the agent user's inline."""

from pathlib import Path

import pytest

from factory.domain.settings import InstanceSettings
from factory.entry.wiring import agent_run_environment

BASE_ENVIRONMENT = {
    "PATH": "/opt/scripts:/usr/bin:/bin",
    "LANG": "C.UTF-8",
    "HOME": "/home/factory",
}


@pytest.mark.parametrize(
    ("fields", "home"),
    [
        pytest.param(
            {
                "stage_environment": "container",
                "dataset": "tank/factory/vm",
                "workspace": Path("/srv/factory/vm/work"),
                "stage_image": "factory-stage:1",
            },
            "/work/home",
            id="container",
        ),
        pytest.param(
            {},
            "/home/factory",
            id="inline-without-agent-user",
        ),
    ],
)
def test_the_agent_run_s_home_follows_the_stage_environment(
    fields: dict[str, object], home: str
) -> None:
    settings = InstanceSettings.model_validate(
        {"repository_url": "/srv/project.git", "instance": "factory-1", **fields}
    )
    base = dict(BASE_ENVIRONMENT)

    environment = agent_run_environment(settings, base)

    assert environment["HOME"] == home
    assert environment["PATH"] == BASE_ENVIRONMENT["PATH"]
    assert environment["LANG"] == BASE_ENVIRONMENT["LANG"]
    assert base == BASE_ENVIRONMENT
