"""The fake images the tests use: no build runs, and each image's `PATH` is given."""

from dataclasses import dataclass
from datetime import timedelta

from factory.application.images import ImageBuild, Images
from factory.domain.containers import SYSTEM_PATH
from factory.domain.stage_layer import StageLayer

PASSED_BUILD = ImageBuild(passed=True, duration=timedelta(0), output_tail="")


@dataclass(frozen=True)
class BuildCall:
    """One call of `build`, with its arguments."""

    layer: StageLayer
    base: str
    tag: str
    time_limit: timedelta


class FakeImages(Images):
    """Images whose builds end as given and whose `PATH`s are given per image."""

    def __init__(
        self, paths: dict[str, str] | None = None, build_result: ImageBuild = PASSED_BUILD
    ) -> None:
        """Give each image of `paths` its `PATH`, every other the base's; end builds as given."""
        self._paths = dict(paths or {})
        self._build_result = build_result
        self.builds: list[BuildCall] = []

    def build(self, layer: StageLayer, base: str, tag: str, time_limit: timedelta) -> ImageBuild:
        """Record the call and end as given."""
        self.builds.append(BuildCall(layer, base, tag, time_limit))
        return self._build_result

    def path(self, image: str) -> str:
        """The `PATH` given for `image`, or the base's."""
        return self._paths.get(image, SYSTEM_PATH)
