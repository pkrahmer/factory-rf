"""What the tests of the project image between ticks share: stage files, identity, what ran."""

from dataclasses import dataclass

from factory.domain.containers import SYSTEM_PATH

BASE_IDENTITY = "sha256-base"
FIRST = "ARG FACTORY_BASE\nFROM ${FACTORY_BASE}\nRUN echo first\n"
SECOND = "ARG FACTORY_BASE\nFROM ${FACTORY_BASE}\nRUN echo second\n"


@dataclass(frozen=True)
class StageSeen:
    """What one tick ran with, and how many builds had been asked for when it ran."""

    image: str | None
    identity: str | None
    path: str
    builds: int


def built_path(build: int) -> str:
    """The `PATH` of the project image after its `build`-th build."""
    return f"/opt/build-{build}/bin:{SYSTEM_PATH}"
