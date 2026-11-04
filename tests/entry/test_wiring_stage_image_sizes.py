"""The log lines of the stage image name its sizes and the build's warnings."""

from datetime import timedelta
from pathlib import Path

from factory.adapters.fake_images import FakeImages
from factory.application.boundaries import Boundaries
from factory.application.images import ImageBuild
from factory.application.stops import StopService
from factory.domain.settings import InstanceSettings
from factory.domain.stage_layer import STAGE_FILE, project_image_tag, stage_layer
from factory.entry.wiring import StageImageReport, project_image_settings
from human_clone import HumanClone
from recording_log import RecordingLog

BASE = "factory-stage:vm"
BASE_IDENTITY = "sha256-base"
VALID = "ARG FACTORY_BASE\nFROM ${FACTORY_BASE}\nRUN true\n"
COMMIT = "c" * 12


class SizedImages(FakeImages):
    """Fake images whose sizes are given per image."""

    def __init__(self, sizes: dict[str, int], build_result: ImageBuild) -> None:
        super().__init__(build_result=build_result)
        self._sizes = sizes

    def size_bytes(self, image: str) -> int | None:
        return self._sizes.get(image)

    def store_path(self) -> Path | None:
        return None


def _settings(local_settings: InstanceSettings) -> InstanceSettings:
    return local_settings.model_copy(update={"stage_image": BASE, "image": BASE_IDENTITY})


def _lines(boundaries: Boundaries, settings: InstanceSettings, images: SizedImages) -> list[str]:
    log = RecordingLog()
    boundaries.git.fetch()
    project_image_settings(
        settings,
        boundaries.git,
        images,
        StopService(boundaries),
        report=StageImageReport(log=log, clock=boundaries.clock, commit=COMMIT),
    )
    return log.lines


def test_a_built_image_logs_its_sizes_and_its_warnings(
    boundaries: Boundaries, local_settings: InstanceSettings, human: HumanClone
) -> None:
    human.push_file("main", STAGE_FILE, VALID)
    build = ImageBuild(passed=True, duration=timedelta(seconds=3), output_tail="done", warnings=2)
    images = SizedImages(
        {BASE: 1_580_000_000, project_image_tag(BASE): 2_000_000_000}, build_result=build
    )

    lines = _lines(boundaries, _settings(local_settings), images)

    identity = stage_layer(VALID, BASE_IDENTITY).identity
    assert lines == [
        f"stage image: built {identity} at {COMMIT} in 3 s, base 1.58 GB, layer 0.42 GB, 2 warnings"
    ]


def test_a_start_without_a_stage_file_logs_the_base_size_once(
    boundaries: Boundaries, local_settings: InstanceSettings
) -> None:
    build = ImageBuild(passed=True, duration=timedelta(0), output_tail="", warnings=0)
    images = SizedImages({BASE: 1_580_000_000}, build_result=build)

    lines = _lines(boundaries, _settings(local_settings), images)

    assert lines == ["stage image: base 1.58 GB"]
