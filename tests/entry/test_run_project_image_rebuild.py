"""A stage file that changes on `main` is built again between ticks and changes the image in use."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import override

import pytest

import factory.entry.run as run_module
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.fake_images import BuildCall, FakeImages
from factory.application.boundaries import Boundaries
from factory.application.images import IMAGE_BUILD_TIME_LIMIT, ImageBuild
from factory.application.tick import Tick, TickOutcome
from factory.domain.containers import SYSTEM_PATH
from factory.domain.settings import InstanceSettings
from factory.domain.stage_layer import STAGE_FILE, StageLayer, project_image_tag, stage_layer
from factory.entry.run import run_instance
from factory.entry.wiring import health_store
from git_support import remote_commit
from human_clone import HumanClone
from log_support import state_log_lines

BASE_IDENTITY = "sha256-base"
FIRST = "ARG FACTORY_BASE\nFROM ${FACTORY_BASE}\nRUN echo first\n"
SECOND = "ARG FACTORY_BASE\nFROM ${FACTORY_BASE}\nRUN echo second\n"
THIRD = "ARG FACTORY_BASE\nFROM ${FACTORY_BASE}\nRUN echo third\n"
PASSED = ImageBuild(passed=True, duration=timedelta(seconds=3), output_tail="done")
FAILED = ImageBuild(passed=False, duration=timedelta(seconds=4), output_tail="error: no package")
MARK = "stage image:"


@dataclass(frozen=True)
class StageSeen:
    """What one tick ran with, and how many builds had been asked for when it ended."""

    image: str | None
    identity: str | None
    path: str
    builds: int


class ScriptedImages(FakeImages):
    """Builds that end as scripted, one result per call; each passed build gets its own `PATH`."""

    def __init__(self, results: list[ImageBuild]) -> None:
        super().__init__()
        self._results = list(results)
        self._passed = 0
        self._tags: set[str] = set()

    @override
    def build(self, layer: StageLayer, base: str, tag: str, time_limit: timedelta) -> ImageBuild:
        self.builds.append(BuildCall(layer, base, tag, time_limit))
        result = self._results.pop(0)
        if result.passed:
            self._passed += 1
            self._tags.add(tag)
        return result

    @override
    def path(self, image: str) -> str:
        if image in self._tags:
            return built_path(self._passed)
        return SYSTEM_PATH


def built_path(build: int) -> str:
    """The `PATH` the `build`-th passed build configures."""
    return f"/opt/build-{build}/bin:{SYSTEM_PATH}"


class RecordingTick(Tick):
    """Records what it runs with after the action of its stage, if one is left; idle."""

    def __init__(
        self,
        seen: StageSeen,
        record: Callable[[StageSeen], None],
        during: list[Callable[[], None]],
        builds: Callable[[], int],
    ) -> None:
        self._seen = seen
        self._record = record
        self._during = during
        self._builds = builds

    @override
    def run(self) -> TickOutcome:
        if self._during:
            self._during.pop(0)()
        seen = self._seen
        self._record(
            StageSeen(
                image=seen.image, identity=seen.identity, path=seen.path, builds=self._builds()
            )
        )
        return TickOutcome()


@dataclass
class Run:
    """The ticks a run saw, the commits it pushed between them, the log's lines after the first."""

    stages: list[StageSeen]
    commits: list[str]
    lines: list[str]


@pytest.fixture
def settings(instance_settings: InstanceSettings) -> InstanceSettings:
    """The instance settings with the base image's identity."""
    return instance_settings.model_copy(update={"image": BASE_IDENTITY})


@pytest.fixture
def base(settings: InstanceSettings) -> str:
    """The base image the settings name."""
    assert settings.stage_image is not None
    return settings.stage_image


def _commit(remote: Path) -> str:
    commit = remote_commit(remote, "main")
    assert commit is not None
    return commit[:12]


class World:
    """The human's clone, the remote and a run of the instance over recording ticks."""

    def __init__(
        self,
        settings: InstanceSettings,
        hosting: FakeHostingService,
        human: HumanClone,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        self.settings = settings
        self.hosting = hosting
        self.human = human
        self.remote = tmp_path / "origin" / "remote.git"
        self.monkeypatch = monkeypatch

    def write(self, text: str) -> Callable[[], None]:
        """The push of `text` as the stage file on `main`."""
        return lambda: self.human.push_file("main", STAGE_FILE, text)

    def touch_other(self) -> Callable[[], None]:
        """The push of a commit on `main` that leaves the stage file as it is."""
        return lambda: self.human.push_file("main", "notes.txt", "another commit\n")

    def remove(self) -> Callable[[], None]:
        """The push of a commit on `main` that removes the stage file."""
        return lambda: self.human.remove_file("main", STAGE_FILE)

    def run(
        self,
        images: FakeImages,
        between: list[Callable[[], None]],
        during: list[Callable[[], None]] | None = None,
    ) -> Run:
        """Run one iteration more than `between` has pushes, one of them after each iteration.

        The n-th tick that runs plays the n-th action of `during` before it records.
        """
        stages: list[StageSeen] = []
        commits: list[str] = []
        lines_at_start: list[int] = []
        pending = list(during or [])

        def build(boundaries: Boundaries, given: InstanceSettings) -> Tick:
            seen = StageSeen(
                image=given.stage_image,
                identity=given.image,
                path=boundaries.image_path,
                builds=0,
            )
            return RecordingTick(seen, stages.append, pending, lambda: len(images.builds))

        self.monkeypatch.setattr(run_module, "build_tick", build)
        sleeps: list[float] = []

        def sleep(seconds: float) -> None:
            if not sleeps:
                lines_at_start.append(len(self._lines()))
            if len(sleeps) < len(between):
                between[len(sleeps)]()
                commits.append(_commit(self.remote))
            sleeps.append(seconds)

        run_instance(
            self.settings,
            sleep=sleep,
            should_stop=lambda: len(sleeps) > len(between),
            hosting=self.hosting,
            images=images,
        )
        return Run(stages=stages, commits=commits, lines=self._lines()[lines_at_start[0] :])

    def _lines(self) -> list[str]:
        lines = state_log_lines(self.settings.state_directory)
        return [line[line.index(MARK) :] for line in lines if MARK in line]


@pytest.fixture
def world(
    settings: InstanceSettings,
    hosting: FakeHostingService,
    human: HumanClone,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> World:
    """The test's instance on its remote, the human's clone beside it."""
    return World(settings, hosting, human, tmp_path, monkeypatch)


def _identity(text: str) -> str:
    return stage_layer(text, BASE_IDENTITY).identity


def _in_use(stage: StageSeen) -> tuple[str | None, str | None, str]:
    return (stage.image, stage.identity, stage.path)


def _stops(settings: InstanceSettings) -> list[tuple[str, str]]:
    stops = health_store(settings.state_directory).read().stops
    return [(stop.reason, stop.detail) for stop in stops]


@pytest.mark.parametrize(
    "stage_file", [pytest.param(FIRST, id="same-digest"), pytest.param(None, id="no-file")]
)
def test_a_new_main_that_leaves_the_stage_file_as_it_is_builds_nothing_and_logs_nothing(
    world: World, base: str, stage_file: str | None
) -> None:
    if stage_file is not None:
        world.human.push_file("main", STAGE_FILE, stage_file)
    images = ScriptedImages([PASSED])

    run = world.run(images, [world.touch_other()])

    builds = 0 if stage_file is None else 1
    if stage_file is None:
        expected = StageSeen(image=base, identity=BASE_IDENTITY, path=SYSTEM_PATH, builds=0)
    else:
        expected = StageSeen(
            image=project_image_tag(base),
            identity=_identity(stage_file),
            path=built_path(1),
            builds=1,
        )
    assert len(images.builds) == builds
    assert run.stages == [expected, expected]
    assert run.lines == []


def test_a_changed_stage_file_is_built_once_before_the_next_stage_and_taken_by_every_later_one(
    world: World, base: str
) -> None:
    world.human.push_file("main", STAGE_FILE, FIRST)
    images = ScriptedImages([PASSED, PASSED])

    run = world.run(images, [world.write(SECOND), world.touch_other()])

    tag = project_image_tag(base)
    old = StageSeen(image=tag, identity=_identity(FIRST), path=built_path(1), builds=1)
    new = StageSeen(image=tag, identity=_identity(SECOND), path=built_path(2), builds=2)
    assert run.stages == [old, new, new]
    assert run.lines == [f"stage image: built {_identity(SECOND)} at {run.commits[0]} in 3 s"]


def test_a_stage_file_added_to_a_project_without_one_is_built_and_taken(
    world: World, base: str
) -> None:
    images = ScriptedImages([PASSED])

    run = world.run(images, [world.write(FIRST)])

    assert run.stages == [
        StageSeen(image=base, identity=BASE_IDENTITY, path=SYSTEM_PATH, builds=0),
        StageSeen(
            image=project_image_tag(base), identity=_identity(FIRST), path=built_path(1), builds=1
        ),
    ]


def test_a_removed_stage_file_returns_to_the_base_and_builds_nothing(
    world: World, base: str
) -> None:
    world.human.push_file("main", STAGE_FILE, FIRST)
    images = ScriptedImages([PASSED])

    run = world.run(images, [world.remove(), world.touch_other()])

    project = StageSeen(
        image=project_image_tag(base), identity=_identity(FIRST), path=built_path(1), builds=1
    )
    back = StageSeen(image=base, identity=BASE_IDENTITY, path=SYSTEM_PATH, builds=1)
    assert run.stages == [project, back, back]
    assert run.lines == [f"stage image: back to the base at {run.commits[0]}"]


def test_a_main_that_moves_during_a_stage_changes_its_image_only_from_the_next_stage(
    world: World, base: str
) -> None:
    world.human.push_file("main", STAGE_FILE, FIRST)
    images = ScriptedImages([PASSED, PASSED])

    run = world.run(images, [lambda: None], during=[world.write(SECOND)])

    tag = project_image_tag(base)
    assert run.stages == [
        StageSeen(image=tag, identity=_identity(FIRST), path=built_path(1), builds=1),
        StageSeen(image=tag, identity=_identity(SECOND), path=built_path(2), builds=2),
    ]


@dataclass(frozen=True)
class AfterFailure:
    """What the push after a failed rebuild leaves: the stop, the image, the builds, the log."""

    push: Callable[[World], Callable[[], None]]
    results: list[ImageBuild]
    stop_stands: bool
    # The last tick's image, identity and path when one ran after the second push; None: none.
    last: Callable[[str], StageSeen] | None
    builds: int
    # The log line of the second push, or None for none; the first is always the failure's.
    second_line: Callable[[str], str] | None


def _project(text: str, build: int, builds: int) -> Callable[[str], StageSeen]:
    def seen(base: str) -> StageSeen:
        return StageSeen(
            image=project_image_tag(base),
            identity=_identity(text),
            path=built_path(build),
            builds=builds,
        )

    return seen


def _base_seen(builds: int) -> Callable[[str], StageSeen]:
    return lambda base: StageSeen(
        image=base, identity=BASE_IDENTITY, path=SYSTEM_PATH, builds=builds
    )


@pytest.mark.parametrize(
    "after",
    [
        pytest.param(
            AfterFailure(
                push=lambda world: world.touch_other(),
                results=[PASSED, FAILED],
                stop_stands=True,
                last=None,
                builds=2,
                second_line=None,
            ),
            id="same-digest",
        ),
        pytest.param(
            AfterFailure(
                push=lambda world: world.write(THIRD),
                results=[PASSED, FAILED, PASSED],
                stop_stands=False,
                last=_project(THIRD, 2, 3),
                builds=3,
                second_line=lambda commit: (
                    f"stage image: built {_identity(THIRD)} at {commit} in 3 s"
                ),
            ),
            id="another-digest",
        ),
        pytest.param(
            AfterFailure(
                push=lambda world: world.remove(),
                results=[PASSED, FAILED],
                stop_stands=False,
                last=_base_seen(2),
                builds=2,
                second_line=lambda commit: f"stage image: back to the base at {commit}",
            ),
            id="file-removed",
        ),
    ],
)
def test_a_failed_rebuild_stands_as_a_stop_until_main_brings_another_stage_file(
    world: World, base: str, after: AfterFailure
) -> None:
    world.human.push_file("main", STAGE_FILE, FIRST)
    images = ScriptedImages(after.results)

    run = world.run(images, [world.write(SECOND), after.push(world)])

    failed_at, second_at = run.commits
    old = _project(FIRST, 1, 1)(base)
    last = None if after.last is None else after.last(base)
    failed_stops = [
        detail for reason, detail in _stops(world.settings) if reason == "stage_image_failed"
    ]
    expected_lines = [f"stage image: failed at {failed_at}"]
    if after.second_line is not None:
        expected_lines.append(after.second_line(second_at))
    assert run.stages[0] == old
    # Until the second push ends the stop, a tick that runs keeps the image before.
    assert all(_in_use(stage) == _in_use(old) or stage == last for stage in run.stages[1:])
    assert len(images.builds) == after.builds
    assert run.lines == expected_lines
    if after.stop_stands:
        [detail] = failed_stops
        assert failed_at in detail
    else:
        assert failed_stops == []
    if last is not None:
        assert run.stages[-1] == last


def test_a_passed_rebuild_builds_under_the_same_tag_so_the_previous_image_is_removed(
    world: World, base: str
) -> None:
    world.human.push_file("main", STAGE_FILE, FIRST)
    images = ScriptedImages([PASSED, PASSED])

    world.run(images, [world.write(SECOND)])

    tag = project_image_tag(base)
    assert images.builds == [
        BuildCall(stage_layer(FIRST, BASE_IDENTITY), base, tag, IMAGE_BUILD_TIME_LIMIT),
        BuildCall(stage_layer(SECOND, BASE_IDENTITY), base, tag, IMAGE_BUILD_TIME_LIMIT),
    ]
