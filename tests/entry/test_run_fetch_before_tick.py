"""A fetch that fails before the tick stands as the stop `fetch_failed` and runs no tick."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import override

import pytest

import factory.entry.run as run_module
from factory.entry.run import run_instance
from factory.entry.wiring import git_options, health_store
from factory.hosting.adapters.fake_hosting import FakeHostingService
from factory.hosting.adapters.git_cli import GitCli
from factory.hosting.application.hosting import HostingService
from factory.hosting.domain.git import GitOptions
from factory.machine.adapters.fake_images import FakeImages
from factory.machine.application.images import Images
from factory.machine.domain.containers import SYSTEM_PATH
from factory.machine.domain.stage_layer import STAGE_FILE, project_image_tag, stage_layer
from factory.pipeline.application.boundaries import Boundaries
from factory.pipeline.application.tick import Tick, TickOutcome
from factory.pipeline.domain.stops import RepositoryStop
from factory.shared.domain.errors import GitError
from factory.shared.domain.settings import InstanceSettings
from support.human_clone import HumanClone
from support.log_support import state_log_lines
from support.remote_outage_support import RemoteOutage, fetch_failed
from support.stage_image_support import BASE_IDENTITY, FIRST, SECOND, StageSeen, built_path

STOP_LINE = "stop repository fetch_failed: "


class CountingImages(FakeImages):
    """Builds that pass; the project image's `PATH` names how many builds were asked for."""

    @override
    def path(self, image: str) -> str:
        if image.endswith("-project"):
            return built_path(len(self.builds))
        return SYSTEM_PATH


class RecordingTick(Tick):
    """Records what it runs with; idle."""

    def __init__(
        self, seen: StageSeen, record: Callable[[StageSeen], None], images: FakeImages
    ) -> None:
        self._seen = seen
        self._record = record
        self._images = images

    @override
    def run(self, *, fetched: bool = False) -> TickOutcome:
        self._record(replace(self._seen, builds=len(self._images.builds)))
        return TickOutcome()


@dataclass
class Run:
    """What a run left: the ticks, whether each iteration ticked, the builds at each pause."""

    stages: list[StageSeen]
    ticked: list[bool]
    builds_at_pause: list[int]
    lines: list[str]
    stops: list[RepositoryStop]


class Outage(RemoteOutage):
    """The instance on its remote, which can be renamed away and back, and the human's clone."""

    def __init__(
        self,
        settings: InstanceSettings,
        hosting: FakeHostingService,
        human: HumanClone,
        remote: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        super().__init__(remote)
        self.settings = settings
        self.hosting = hosting
        self.human = human
        self.monkeypatch = monkeypatch

    def push_during_outage(self, text: str) -> Callable[[], None]:
        """Push `text` as the stage file on `main` between two times the remote is unreachable."""

        def push() -> None:
            self.come_back()
            self.human.push_file("main", STAGE_FILE, text)
            self.go_away()

        return push

    def run(self, images: FakeImages, between: list[Callable[[], None]]) -> Run:
        """Run one iteration more than `between` has actions, one of them after each iteration."""
        stages: list[StageSeen] = []
        ticked: list[bool] = []
        builds_at_pause: list[int] = []

        def build(boundaries: Boundaries, given: InstanceSettings) -> Tick:
            seen = StageSeen(
                image=given.stage_image, identity=given.image, path=boundaries.image_path, builds=0
            )
            return RecordingTick(seen, stages.append, images)

        self.monkeypatch.setattr(run_module, "build_tick", build)
        sleeps: list[float] = []

        def sleep(seconds: float) -> None:
            ticked.append(len(stages) > sum(ticked))
            builds_at_pause.append(len(images.builds))
            if len(sleeps) < len(between):
                between[len(sleeps)]()
            sleeps.append(seconds)

        run_instance(
            self.settings,
            sleep=sleep,
            should_stop=lambda: len(sleeps) > len(between),
            hosting=self.hosting,
            images=images,
        )
        return Run(
            stages=stages,
            ticked=ticked,
            builds_at_pause=builds_at_pause,
            lines=state_log_lines(self.settings.state_directory),
            stops=list(health_store(self.settings.state_directory).read().stops),
        )


@pytest.fixture
def outage(
    base_identity_settings: InstanceSettings,
    hosting: FakeHostingService,
    human: HumanClone,
    remote: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Outage:
    """The test's instance on its remote, the human's clone beside it."""
    return Outage(base_identity_settings, hosting, human, remote, monkeypatch)


def _failed_iterations(run: Run) -> list[str]:
    return [line for line in run.lines if "iteration failed" in line]


def _project(text: str, base: str, builds: int) -> StageSeen:
    return StageSeen(
        image=project_image_tag(base),
        identity=stage_layer(text, BASE_IDENTITY).identity,
        path=built_path(builds),
        builds=builds,
    )


@pytest.mark.parametrize(
    "fails", [pytest.param(True, id="fails"), pytest.param(False, id="passes")]
)
def test_a_failed_fetch_before_the_tick_stands_as_fetch_failed_and_runs_no_tick(
    outage: Outage, fails: bool
) -> None:
    run = outage.run(CountingImages(), [outage.go_away if fails else lambda: None])

    assert _failed_iterations(run) == []
    if fails:
        [stop] = fetch_failed(run.stops)
        assert stop.scope == "repository"
        assert stop.detail.startswith("git fetch")
        assert " failed (exit " in stop.detail
        assert any(line.endswith(STOP_LINE + stop.detail.splitlines()[0]) for line in run.lines)
        assert run.ticked == [True, False]
    else:
        assert fetch_failed(run.stops) == []
        assert not any(STOP_LINE in line for line in run.lines)
        assert run.ticked == [True, True]


@pytest.mark.parametrize(
    "stage_file", [pytest.param(None, id="no-stage-file"), pytest.param(FIRST, id="stage-file")]
)
def test_while_the_fetch_fails_the_image_in_use_stays_and_nothing_is_built(
    outage: Outage, base_image: str, stage_file: str | None
) -> None:
    if stage_file is not None:
        outage.human.push_file("main", STAGE_FILE, stage_file)
    images = CountingImages()

    run = outage.run(images, [outage.go_away, lambda: None, outage.come_back])

    builds = 0 if stage_file is None else 1
    if stage_file is None:
        before = StageSeen(image=base_image, identity=BASE_IDENTITY, path=SYSTEM_PATH, builds=0)
    else:
        before = _project(stage_file, base_image, 1)
    assert run.ticked == [True, False, False, True]
    assert run.builds_at_pause == [builds] * 4
    assert run.stages == [before, before]


@pytest.mark.parametrize(
    "changed",
    [pytest.param(False, id="main-unchanged"), pytest.param(True, id="stage-file-changed")],
)
def test_the_first_fetch_that_passes_after_the_outage_clears_fetch_failed_and_ticks(
    outage: Outage, base_image: str, changed: bool
) -> None:
    outage.human.push_file("main", STAGE_FILE, FIRST)
    images = CountingImages()
    during = outage.push_during_outage(SECOND) if changed else lambda: None

    run = outage.run(images, [outage.go_away, during, outage.come_back])

    assert any(STOP_LINE in line for line in run.lines)
    assert any(line.endswith("stop cleared fetch_failed") for line in run.lines)
    assert fetch_failed(run.stops) == []
    assert run.ticked == [True, False, False, True]
    after = _project(SECOND, base_image, 2) if changed else _project(FIRST, base_image, 1)
    assert run.stages == [_project(FIRST, base_image, 1), after]
    assert len(images.builds) == (2 if changed else 1)


class BreakableFetch(GitCli):
    """A git whose fetch, once broken, fails with a git error that is not `FetchFailed`."""

    broken = False

    @override
    def fetch(self) -> None:
        if BreakableFetch.broken:
            raise GitError("git fetch", None, "time limit reached")
        super().fetch()


def test_a_fetch_that_fails_with_another_git_error_is_no_fetch_failed_stop(
    outage: Outage, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = run_module.build_boundaries

    def build_boundaries(
        settings: InstanceSettings,
        token: str,
        *,
        hosting: HostingService | None = None,
        images: Images | None = None,
    ) -> Boundaries:
        boundaries = original(settings, token, hosting=hosting, images=images)
        options: GitOptions = git_options(settings)
        return replace(boundaries, git=BreakableFetch(settings.checkout, options))

    def break_fetch() -> None:
        monkeypatch.setattr(BreakableFetch, "broken", True)

    monkeypatch.setattr(run_module, "build_boundaries", build_boundaries)

    run = outage.run(CountingImages(), [break_fetch])

    assert fetch_failed(run.stops) == []
    assert not any(STOP_LINE in line for line in run.lines)
    assert any("iteration failed: GitError: git fetch" in line for line in run.lines)
