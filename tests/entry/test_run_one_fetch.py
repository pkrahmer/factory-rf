"""One iteration of `factory-run` fetches once, and its tick works on what that fetch brought."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import get_args

import pytest

import factory.entry.run as run_module
from factory.adapters.fake_images import FakeImages
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.tick import Tick
from factory.domain.events import Event, EventKind
from factory.domain.stops import RepositoryStop
from factory.entry.run import run_instance
from factory.entry.wiring import health_store
from factory.hosting.adapters.fake_hosting import FakeHostingService
from factory.hosting.adapters.git_cli import GitCli
from factory.shared.domain.errors import FetchFailed
from factory.shared.domain.identifiers import branch_name
from factory.shared.domain.settings import InstanceSettings
from git_support import remote_commit
from human_clone import HumanClone
from remote_outage_support import RemoteOutage, fetch_failed
from tick_support import handlers_of

# A work-item branch of no story: the tick has nothing to run on it and stays idle.
BRANCH = branch_name("F0001-S0009")
# More handled events than the iterations of a test hold: the loop never paused.
HANDLED_CAP = 20

pytestmark = pytest.mark.usefixtures("installed_agents")


@dataclass
class Seen:
    """What one handled event saw: the remote-tracking commits of `main` and of the branch."""

    kind: EventKind
    main: str | None
    branch: str | None


class SeeingHandler(Handler):
    """Records, for every event, the remote-tracking commits its tick's checkout holds."""

    def __init__(self, git: GitCli, seen: list[Seen]) -> None:
        self._git = git
        self._seen = seen

    def handle(self, event: Event) -> None:
        main = self._git.resolve("origin/main")
        branch = self._git.resolve(f"origin/{BRANCH}")
        self._seen.append(Seen(kind=event.kind, main=main, branch=branch))


@dataclass
class Iterations:
    """What each iteration left, read at the pause after it."""

    fetches: list[int] = field(default_factory=list)
    ticked: list[bool] = field(default_factory=list)
    stops: list[list[RepositoryStop]] = field(default_factory=list)
    fetch_errors: list[str] = field(default_factory=list)
    seen: list[Seen] = field(default_factory=list)


class Instance(RemoteOutage):
    """The test's instance on its remote: every fetch counted, a tick that records what it saw."""

    def __init__(
        self,
        settings: InstanceSettings,
        hosting: FakeHostingService,
        remote: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        super().__init__(remote)
        self.settings = settings
        self.hosting = hosting
        self.monkeypatch = monkeypatch

    def run(self, between: list[Callable[[], None]]) -> Iterations:
        """Run one iteration more than `between` has actions, one of them after each iteration."""
        result = Iterations()
        fetches: list[None] = []
        original_fetch = GitCli.fetch

        def counting_fetch(git: GitCli) -> None:
            fetches.append(None)
            try:
                original_fetch(git)
            except FetchFailed as error:
                result.fetch_errors.append(str(error))
                raise

        def build(boundaries: Boundaries, given: InstanceSettings) -> Tick:
            assert isinstance(boundaries.git, GitCli)
            handler = SeeingHandler(boundaries.git, result.seen)
            handlers: dict[EventKind, Handler] = dict.fromkeys(get_args(EventKind), handler)
            return Tick(boundaries, given.instance, handlers_of(handlers))

        self.monkeypatch.setattr(GitCli, "fetch", counting_fetch)
        self.monkeypatch.setattr(run_module, "build_tick", build)
        handled_before = [0]
        fetches_before = [0]
        pauses: list[float] = []

        def sleep(seconds: float) -> None:
            result.fetches.append(len(fetches) - fetches_before[0])
            result.ticked.append(len(result.seen) > handled_before[0])
            result.stops.append(list(health_store(self.settings.state_directory).read().stops))
            handled_before[0] = len(result.seen)
            if len(pauses) < len(between):
                between[len(pauses)]()
            fetches_before[0] = len(fetches)
            pauses.append(seconds)

        run_instance(
            self.settings,
            sleep=sleep,
            should_stop=lambda: len(pauses) > len(between) or len(result.seen) > HANDLED_CAP,
            hosting=self.hosting,
            images=FakeImages(),
        )
        return result


@pytest.fixture
def instance(
    base_identity_settings: InstanceSettings,
    hosting: FakeHostingService,
    human: HumanClone,
    remote: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Instance:
    """The test's instance on its remote, which holds a work-item branch."""
    human.push_file(BRANCH, "notes-first.txt", "a first commit\n")
    return Instance(base_identity_settings, hosting, remote, monkeypatch)


@pytest.mark.parametrize(
    "branch",
    [
        pytest.param("main", id="new-commit-on-main"),
        pytest.param(BRANCH, id="new-commit-on-branch"),
    ],
)
def test_an_iteration_fetches_once_and_its_tick_sees_what_that_fetch_brought(
    instance: Instance, human: HumanClone, remote: Path, branch: str
) -> None:
    pushed: list[str | None] = []

    def push() -> None:
        human.push_file(branch, "notes-human.txt", "a human commit\n")
        pushed.append(remote_commit(remote, branch))

    iterations = instance.run([push])

    assert iterations.ticked == [True, True]
    assert iterations.fetches[1] == 1
    [new] = pushed
    assert new is not None
    last = iterations.seen[-1]
    assert (last.main if branch == "main" else last.branch) == new


def test_a_failed_fetch_in_an_iteration_stands_as_fetch_failed_and_the_next_passed_one_clears_it(
    instance: Instance,
) -> None:
    iterations = instance.run([instance.go_away, instance.come_back])

    assert iterations.ticked == [True, False, True]
    assert iterations.fetches[1] == 1
    [error] = iterations.fetch_errors
    [stop] = fetch_failed(iterations.stops[1])
    assert error.splitlines()[0] in stop.detail
    assert fetch_failed(iterations.stops[2]) == []
