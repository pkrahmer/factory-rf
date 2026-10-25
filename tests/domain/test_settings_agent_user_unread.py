"""The setting `FACTORY_AGENT_USER` is read by nothing: an instance runs no second user."""

import pytest

from factory.domain.settings import read_settings
from settings_support import BASE

CONTAINER = {
    "FACTORY_STAGE_ENVIRONMENT": "container",
    "FACTORY_DATASET": "tank/factory/vm",
    "FACTORY_WORKSPACE": "/srv/factory/vm/work",
    "FACTORY_STAGE_IMAGE": "factory-stage:1",
}


@pytest.mark.parametrize(
    ("environment", "value"),
    [
        pytest.param(BASE, "agent", id="inline-agent"),
        pytest.param(BASE, "Bad Name", id="inline-refused-until-now"),
        pytest.param({**BASE, **CONTAINER}, "agent", id="container-agent"),
    ],
)
def test_the_agent_user_setting_changes_no_setting(environment: dict[str, str], value: str) -> None:
    settings = read_settings({**environment, "FACTORY_AGENT_USER": value})

    assert settings == read_settings(environment)
