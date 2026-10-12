"""Fixtures shared by the whole test suite."""

import pytest

from factory.domain.kill_points import KillPoints


@pytest.fixture
def kill_points() -> KillPoints:
    """Return a new, inert set of kill points for each test."""
    return KillPoints()
