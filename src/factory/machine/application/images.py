"""The interface through which the factory builds a project's stage image and reads an image."""

from abc import ABC, abstractmethod
from datetime import timedelta
from pathlib import Path

from pydantic import BaseModel, ConfigDict, NonNegativeInt

from factory.machine.domain.stage_layer import StageLayer

IMAGE_BUILD_TIME_LIMIT = timedelta(minutes=30)


class ImageBuild(BaseModel):
    """How a build of a stage file ended: passed or not, its duration, last lines and warnings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    passed: bool
    duration: timedelta
    # The build's last lines, joined by newlines.
    output_tail: str
    # The lines of the whole output that warn.
    warnings: NonNegativeInt = 0


class Images(ABC):
    """The images the containers run in: a project's layer built on the base, and their `PATH`."""

    @abstractmethod
    def build(self, layer: StageLayer, base: str, tag: str, time_limit: timedelta) -> ImageBuild:
        """Build `layer` on `base`, given as `FACTORY_BASE`, with an empty context; tag it `tag`.

        Images left without a tag after it are removed. A build that reaches `time_limit` has
        not passed.
        """

    @abstractmethod
    def path(self, image: str) -> str:
        """The `PATH` `image` configures, or `/usr/local/bin:/usr/bin:/bin` when it sets none.

        `ContainerError` when the image cannot be read.
        """

    @abstractmethod
    def size_bytes(self, image: str) -> int | None:
        """The size of `image` in bytes; `None` when it cannot be read."""

    @abstractmethod
    def store_path(self) -> Path | None:
        """The folder of the image store; `None` when it cannot be read."""
