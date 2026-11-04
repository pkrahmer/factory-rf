"""The start reads the project's stage file, builds its image and names the image in use."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.images import IMAGE_BUILD_TIME_LIMIT, ImageBuild, Images
from factory.application.stops import StopService
from factory.domain.settings import InstanceSettings
from factory.domain.stage_layer import STAGE_FILE, StageLayer, stage_layer
from factory.domain.stops import RepositoryStop
from factory.entry.run import run_instance
from factory.entry.wiring import health_store, project_image_settings
from git_support import run_git
from human_clone import HumanClone
from wiring_support import with_dataset

BASE_IDENTITY = "sha256-base"
VALID = "ARG FACTORY_BASE\nFROM ${FACTORY_BASE}\nRUN true\n"
PASSED = ImageBuild(passed=True, duration=timedelta(seconds=3), output_tail="done")
FAILED = ImageBuild(
    passed=False, duration=timedelta(seconds=42), output_tail="step 1\nerror: no package"
)
TIMED_OUT = ImageBuild(passed=False, duration=timedelta(minutes=30), output_tail="step 7\nfetching")
AT = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)


@dataclass(frozen=True)
class _Build:
    layer: StageLayer
    base: str
    tag: str
    time_limit: timedelta


@dataclass
class _RecordingImages(Images):
    result: ImageBuild = PASSED
    builds: list[_Build] = field(default_factory=list)
    paths: dict[str, str] = field(default_factory=dict)

    def build(self, layer: StageLayer, base: str, tag: str, time_limit: timedelta) -> ImageBuild:
        self.builds.append(_Build(layer, base, tag, time_limit))
        return self.result

    def path(self, image: str) -> str:
        return self.paths.get(image, "/usr/local/bin:/usr/bin:/bin")


@pytest.fixture
def settings(local_settings: InstanceSettings) -> InstanceSettings:
    """The local settings with the base image `factory-stage:vm` and its identity."""
    return local_settings.model_copy(
        update={"stage_image": "factory-stage:vm", "image": BASE_IDENTITY}
    )


def _start(
    boundaries: Boundaries, settings: InstanceSettings, images: Images
) -> InstanceSettings | None:
    boundaries.git.fetch()
    return project_image_settings(settings, boundaries.git, images, StopService(boundaries))


def _stops(boundaries: Boundaries) -> list[tuple[str, str]]:
    return [(stop.reason, stop.detail) for stop in boundaries.health.read().stops]


def _push_bytes(tmp_path: Path, remote: Path, path: str, data: bytes) -> None:
    clone = tmp_path / "byte-clone"
    run_git(tmp_path, "clone", "-q", str(remote), str(clone))
    target = clone / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    run_git(clone, "add", path)
    identity = ["-c", "user.name=Human", "-c", "user.email=human@example.org"]
    run_git(clone, *identity, "commit", "-q", "-m", f"write {path}")
    run_git(clone, "push", "-q", "origin", "main")


def test_a_start_without_a_stage_file_builds_nothing_and_keeps_the_base(
    boundaries: Boundaries, settings: InstanceSettings
) -> None:
    images = _RecordingImages()

    started = _start(boundaries, settings, images)

    assert started == settings
    assert images.builds == []


def test_a_start_with_a_valid_stage_file_builds_it_once_and_takes_the_project_image(
    boundaries: Boundaries, settings: InstanceSettings, human: HumanClone
) -> None:
    human.push_file("main", STAGE_FILE, VALID)
    images = _RecordingImages()

    started = _start(boundaries, settings, images)

    layer = stage_layer(VALID, BASE_IDENTITY)
    assert images.builds == [
        _Build(layer, "factory-stage:vm", "factory-stage:vm-project", IMAGE_BUILD_TIME_LIMIT)
    ]
    assert started == settings.model_copy(
        update={"stage_image": "factory-stage:vm-project", "image": layer.identity}
    )


def test_the_build_time_limit_is_thirty_minutes() -> None:
    assert timedelta(minutes=30) == IMAGE_BUILD_TIME_LIMIT


@pytest.mark.parametrize(
    ("result", "seconds"),
    [pytest.param(FAILED, 42, id="failed"), pytest.param(TIMED_OUT, 1800, id="time-limit")],
)
def test_a_stage_file_that_does_not_build_stands_as_a_stop(
    boundaries: Boundaries,
    settings: InstanceSettings,
    human: HumanClone,
    result: ImageBuild,
    seconds: int,
) -> None:
    human.push_file("main", STAGE_FILE, VALID)

    started = _start(boundaries, settings, _RecordingImages(result=result))

    [(reason, detail)] = _stops(boundaries)
    assert started is None
    assert reason == "stage_image_failed"
    assert detail.startswith(f"the stage file did not build in {seconds} s:")
    assert detail.endswith(result.output_tail)


def _push_broken_rule(human: HumanClone, _tmp_path: Path, _remote: Path) -> None:
    human.push_file("main", STAGE_FILE, "FROM debian:bookworm\n")


def _push_not_utf_8(_human: HumanClone, tmp_path: Path, remote: Path) -> None:
    _push_bytes(tmp_path, remote, STAGE_FILE, b"\xff\n")


_Push = Callable[[HumanClone, Path, Path], None]


@pytest.mark.parametrize(
    "push",
    [pytest.param(_push_broken_rule, id="rule"), pytest.param(_push_not_utf_8, id="not-utf-8")],
)
def test_a_stage_file_that_breaks_the_rule_stands_as_a_stop_and_builds_nothing(
    boundaries: Boundaries,
    settings: InstanceSettings,
    *,
    human: HumanClone,
    tmp_path: Path,
    remote: Path,
    push: _Push,
) -> None:
    push(human, tmp_path, remote)
    images = _RecordingImages()

    started = _start(boundaries, settings, images)

    [(reason, detail)] = _stops(boundaries)
    assert started is None
    assert reason == "stage_image_failed"
    assert detail
    assert images.builds == []


@pytest.mark.parametrize(
    "stage_file", [pytest.param(VALID, id="valid"), pytest.param(None, id="none")]
)
def test_the_next_start_ends_a_stage_image_stop(
    boundaries: Boundaries, settings: InstanceSettings, human: HumanClone, stage_file: str | None
) -> None:
    StopService(boundaries).raise_stop(
        RepositoryStop(scope="machine", reason="stage_image_failed", detail="a fault", at=AT)
    )
    if stage_file is not None:
        human.push_file("main", STAGE_FILE, stage_file)

    started = _start(boundaries, settings, _RecordingImages())

    assert started is not None
    assert "stage_image_failed" not in [reason for reason, _ in _stops(boundaries)]


def test_no_stage_starts_while_the_stage_image_stop_stands(
    tmp_path: Path, agent_home: Path, hosting: FakeHostingService, remote: Path, human: HumanClone
) -> None:
    human.push_file("main", STAGE_FILE, VALID)
    token_file = tmp_path / "hosting-token"
    token_file.write_text("example-value\n", encoding="utf-8")
    state = tmp_path / "instance-state"
    state.mkdir()
    settings = with_dataset(
        InstanceSettings(
            repository_url=str(remote),
            instance="factory-1",
            checkout=tmp_path / "instance-checkout",
            state_directory=state,
            agent_home=agent_home,
            claude_executable=str(tmp_path / "no-claude"),
            token_file=token_file,
        ),
        tmp_path,
    )
    sleeps: list[float] = []
    images = _RecordingImages(result=FAILED)

    run_instance(
        settings,
        sleep=sleeps.append,
        should_stop=lambda: bool(sleeps),
        hosting=hosting,
        images=images,
    )

    stops = health_store(state).read().stops
    assert [stop.reason for stop in stops] == ["stage_image_failed"]
    assert len(images.builds) == 1
