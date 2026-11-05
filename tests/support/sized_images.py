"""Fake images that answer each image's size, for the tests of the stage image's log lines."""

from collections.abc import Callable
from pathlib import Path

from factory.machine.adapters.fake_images import PASSED_BUILD, FakeImages
from factory.machine.application.images import ImageBuild

BASE_BYTES = 1_580_000_000
PROJECT_BYTES = 2_000_000_000


def sized_by_tag(image: str) -> int:
    """`PROJECT_BYTES` for a project image's tag, `BASE_BYTES` for every other image."""
    return PROJECT_BYTES if image.endswith("-project") else BASE_BYTES


class SizedImages(FakeImages):
    """Fake images whose sizes `sizes` answers per image; the image store is at `store`."""

    def __init__(
        self,
        sizes: Callable[[str], int | None],
        build_result: ImageBuild = PASSED_BUILD,
        store: Path | None = None,
    ) -> None:
        super().__init__(build_result=build_result)
        self._sizes = sizes
        self._store = store
        self.sized: list[str] = []

    def size_bytes(self, image: str) -> int | None:
        self.sized.append(image)
        return self._sizes(image)

    def store_path(self) -> Path | None:
        return self._store
