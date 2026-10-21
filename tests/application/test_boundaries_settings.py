"""The instance's settings held by the boundaries the services work through."""

import dataclasses

from factory.application.boundaries import Boundaries
from factory.domain.settings import read_settings


def test_boundaries_hold_the_settings_they_are_given(boundaries: Boundaries) -> None:
    settings = read_settings(
        {"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "factory-1"}
    )

    replaced = dataclasses.replace(boundaries, settings=settings)

    assert isinstance(replaced, Boundaries)
    assert replaced.settings is settings
