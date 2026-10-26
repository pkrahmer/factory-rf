"""The instance's settings held by the boundaries the services work through."""

import dataclasses

from factory.application.boundaries import Boundaries
from factory.domain.settings import read_settings
from settings_support import BASE


def test_boundaries_hold_the_settings_they_are_given(boundaries: Boundaries) -> None:
    settings = read_settings(BASE)

    replaced = dataclasses.replace(boundaries, settings=settings)

    assert isinstance(replaced, Boundaries)
    assert replaced.settings is settings
