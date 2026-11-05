"""The image sizes the stages see: measured at a build or a return to the base, not at every run."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

import pytest

import factory.entry.run as run_module
from factory.application.boundaries import Boundaries
from factory.application.tick import Tick, TickOutcome
from factory.domain.stage_layer import STAGE_FILE
from factory.entry.run import run_instance
from factory.hosting.adapters.fake_hosting import FakeHostingService
from factory.shared.domain.settings import InstanceSettings
from human_clone import HumanClone
from log_support import state_log_lines
from sized_images import BASE_BYTES, PROJECT_BYTES, SizedImages, sized_by_tag
from stage_image_support import FIRST


@dataclass(frozen=True)
class SizesSeen:
    """The image sizes one tick's boundaries held, and how many sizes had been read by then."""

    base_image_bytes: int | None
    project_layer_bytes: int | None
    readings: int


class SeeingTick(Tick):
    """Records what it was given; idle."""

    def __init__(self, seen: SizesSeen, record: Callable[[SizesSeen], None]) -> None:
        self._seen = seen
        self._record = record

    @override
    def run(self, *, fetched: bool = False) -> TickOutcome:
        self._record(self._seen)
        return TickOutcome()


def _run(
    settings: InstanceSettings,
    hosting: FakeHostingService,
    monkeypatch: pytest.MonkeyPatch,
    between: list[Callable[[], None]],
) -> list[SizesSeen]:
    images = SizedImages(sized_by_tag)
    seen: list[SizesSeen] = []

    def build(boundaries: Boundaries, _given: InstanceSettings) -> Tick:
        sizes = SizesSeen(
            boundaries.base_image_bytes, boundaries.project_layer_bytes, len(images.sized)
        )
        return SeeingTick(sizes, seen.append)

    monkeypatch.setattr(run_module, "build_tick", build)
    sleeps: list[float] = []

    def sleep(seconds: float) -> None:
        if len(sleeps) < len(between):
            between[len(sleeps)]()
        sleeps.append(seconds)

    run_instance(
        settings,
        sleep=sleep,
        should_stop=lambda: len(sleeps) > len(between),
        hosting=hosting,
        images=images,
    )
    return seen


def test_a_project_without_a_stage_file_has_a_layer_of_zero(
    base_identity_settings: InstanceSettings,
    hosting: FakeHostingService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _run(base_identity_settings, hosting, monkeypatch, [])

    assert [(s.base_image_bytes, s.project_layer_bytes) for s in seen] == [(BASE_BYTES, 0)]


def test_the_sizes_change_only_after_a_build_or_a_return_to_the_base(
    base_identity_settings: InstanceSettings,
    hosting: FakeHostingService,
    human: HumanClone,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    human.push_file("main", STAGE_FILE, FIRST)

    seen = _run(
        base_identity_settings,
        hosting,
        monkeypatch,
        [
            lambda: human.push_file("main", "notes.txt", "another commit\n"),
            lambda: human.remove_file("main", STAGE_FILE),
        ],
    )

    layer = PROJECT_BYTES - BASE_BYTES
    sizes = [(s.base_image_bytes, s.project_layer_bytes) for s in seen]
    assert sizes == [(BASE_BYTES, layer), (BASE_BYTES, layer), (BASE_BYTES, 0)]
    assert seen[1].readings == seen[0].readings
    assert seen[2].readings > seen[1].readings


def test_a_run_without_a_stage_file_logs_the_base_size_only_at_its_start(
    base_identity_settings: InstanceSettings,
    hosting: FakeHostingService,
    human: HumanClone,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run(
        base_identity_settings,
        hosting,
        monkeypatch,
        [lambda: human.push_file("main", "notes.txt", "another commit\n")],
    )

    lines = state_log_lines(base_identity_settings.state_directory)
    mark = "stage image:"
    assert [line[line.index(mark) :] for line in lines if mark in line] == [
        "stage image: base 1.58 GB"
    ]
