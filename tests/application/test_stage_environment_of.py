"""The boundaries' environment is the container one, on their snapshots and containers."""

from factory.application.boundaries import Boundaries
from factory.application.stage_environment import ContainerEnvironment, stage_environment_of


def test_the_environment_of_the_boundaries_is_the_container_one(boundaries: Boundaries) -> None:
    environment = stage_environment_of(boundaries)

    assert isinstance(environment, ContainerEnvironment)
    assert environment._snapshots is boundaries.snapshots  # noqa: SLF001
    assert environment._containers is boundaries.containers  # noqa: SLF001
