# SPDX-License-Identifier: Apache-2.0
"""The fake images the tests use: no build runs, and each image's `PATH` and size are given."""

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from factory.machine.application.images import ImageBuild, Images
from factory.machine.domain.containers import SYSTEM_PATH
from factory.machine.domain.stage_layer import StageLayer

PASSED_BUILD = ImageBuild(passed=True, duration=timedelta(0), output_tail="")


@dataclass(frozen=True)
class BuildCall:
    """One call of `build`, with its arguments."""

    layer: StageLayer
    base: str
    tag: str
    time_limit: timedelta


class FakeImages(Images):
    """Images whose builds end as given and whose `PATH`s and sizes are given per image."""

    def __init__(
        self,
        paths: dict[str, str] | None = None,
        build_result: ImageBuild = PASSED_BUILD,
        sizes: dict[str, int] | None = None,
    ) -> None:
        """Give each image of `paths` its `PATH`, every other the base's; end builds as given.

        Each image of `sizes` has its size, every other none known.
        """
        self._paths = dict(paths or {})
        self._image_sizes = dict(sizes or {})
        self._build_result = build_result
        self.builds: list[BuildCall] = []

    def build(self, layer: StageLayer, base: str, tag: str, time_limit: timedelta) -> ImageBuild:
        """Record the call and end as given."""
        self.builds.append(BuildCall(layer, base, tag, time_limit))
        return self._build_result

    def path(self, image: str) -> str:
        """The `PATH` given for `image`, or the base's."""
        return self._paths.get(image, SYSTEM_PATH)

    def size_bytes(self, image: str) -> int | None:
        """The size given for `image`, or `None`."""
        return self._image_sizes.get(image)

    def store_path(self) -> Path | None:
        """Unknown: `None`."""
        return None
