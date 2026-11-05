"""The log lines of the stage image name its sizes and the build's warnings."""

from datetime import timedelta

import pytest

from factory.application.boundaries import Boundaries
from factory.application.stops import StopService
from factory.entry.wiring import (
    ImageSizes,
    StageImageReport,
    chosen_image,
    image_sizes,
    project_image_settings,
)
from factory.machine.application.images import ImageBuild
from factory.machine.domain.stage_layer import STAGE_FILE, project_image_tag, stage_layer
from factory.shared.domain.settings import InstanceSettings
from human_clone import HumanClone
from recording_log import RecordingLog
from sized_images import SizedImages

BASE = "factory-stage:vm"
BASE_IDENTITY = "sha256-base"
VALID = "ARG FACTORY_BASE\nFROM ${FACTORY_BASE}\nRUN true\n"
COMMIT = "c" * 12


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
        {BASE: 1_580_000_000, project_image_tag(BASE): 2_000_000_000}.get, build_result=build
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
    images = SizedImages({BASE: 1_580_000_000}.get, build_result=build)

    lines = _lines(boundaries, _settings(local_settings), images)

    assert lines == ["stage image: base 1.58 GB"]


def test_a_return_to_the_base_gives_both_sizes_without_a_build(
    boundaries: Boundaries, local_settings: InstanceSettings, human: HumanClone
) -> None:
    human.push_file("main", STAGE_FILE, VALID)
    build = ImageBuild(passed=True, duration=timedelta(seconds=3), output_tail="done", warnings=0)
    images = SizedImages(
        {BASE: 1_580_000_000, project_image_tag(BASE): 2_000_000_000}.get, build_result=build
    )
    settings = _settings(local_settings)
    _lines(boundaries, settings, images)
    human.remove_file("main", STAGE_FILE)
    boundaries.git.fetch()

    # A return to the base is chosen without a report, as the run chooses it.
    chosen = chosen_image(settings, boundaries.git, images, StopService(boundaries))

    assert chosen is not None
    assert chosen.sizes == ImageSizes(base_bytes=1_580_000_000, layer_bytes=0)
    assert len(images.builds) == 1


@pytest.mark.parametrize(
    ("sizes", "text"),
    [
        pytest.param({}, "base unknown, layer unknown", id="base-unreadable"),
        pytest.param({BASE: 1_580_000_000}, "base 1.58 GB, layer unknown", id="project-unreadable"),
        pytest.param(
            {BASE: 1_580_000_000, project_image_tag(BASE): 1_000_000_000},
            "base 1.58 GB, layer unknown",
            id="project-smaller-than-base",
        ),
    ],
)
def test_a_size_that_cannot_be_read_is_logged_unknown(
    boundaries: Boundaries,
    local_settings: InstanceSettings,
    human: HumanClone,
    sizes: dict[str, int],
    text: str,
) -> None:
    human.push_file("main", STAGE_FILE, VALID)
    build = ImageBuild(passed=True, duration=timedelta(seconds=3), output_tail="done", warnings=0)
    images = SizedImages(sizes.get, build_result=build)

    lines = _lines(boundaries, _settings(local_settings), images)

    identity = stage_layer(VALID, BASE_IDENTITY).identity
    assert lines == [f"stage image: built {identity} at {COMMIT} in 3 s, {text}, 0 warnings"]


def test_a_base_that_cannot_be_read_is_logged_unknown_at_the_start(
    boundaries: Boundaries, local_settings: InstanceSettings
) -> None:
    unknown: dict[str, int] = {}
    images = SizedImages(unknown.get)

    lines = _lines(boundaries, _settings(local_settings), images)

    assert lines == ["stage image: base unknown"]


def test_a_project_image_smaller_than_its_base_has_no_layer_size() -> None:
    images = SizedImages({BASE: 1_580_000_000, project_image_tag(BASE): 1_000_000_000}.get)

    sizes = image_sizes(images, BASE, project_image_tag(BASE))

    assert sizes == ImageSizes(base_bytes=1_580_000_000, layer_bytes=None)
