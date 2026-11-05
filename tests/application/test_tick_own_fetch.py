"""A tick run without the fetch before it fetches itself, and stands a failed fetch as a stop."""

from dataclasses import replace
from pathlib import Path
from typing import override

import pytest

from factory.application.boundaries import Boundaries
from factory.application.tick import IdleHandler, Tick, TickOutcome
from factory.hosting.adapters.git_cli import GitCli
from factory.hosting.domain.git import GitOptions
from factory.shared.domain.kill_points import KillPoints
from git_support import CHECKOUT, TEST_IDENTITY
from remote_outage_support import move_remote_away
from stage_run_support import INSTANCE
from tick_support import handlers_of

pytestmark = pytest.mark.usefixtures("installed_agents", "checkout")


class CountingFetch(GitCli):
    """The real git, counting its fetches."""

    def __init__(self, directory: Path, options: GitOptions) -> None:
        super().__init__(directory, options)
        self.fetches = 0

    @override
    def fetch(self) -> None:
        self.fetches += 1
        super().fetch()


@pytest.fixture
def counting(tmp_path: Path, kill_points: KillPoints) -> CountingFetch:
    """A counting git on the test's checkout, with the checkout fixture's options."""
    return CountingFetch(
        tmp_path / CHECKOUT, GitOptions(kill_points=kill_points, identity=TEST_IDENTITY)
    )


def _tick(boundaries: Boundaries, git: CountingFetch) -> Tick:
    return Tick(replace(boundaries, git=git), INSTANCE, handlers_of({"idle": IdleHandler()}))


@pytest.mark.parametrize(
    "explicit", [pytest.param(False, id="default"), pytest.param(True, id="fetched-false")]
)
def test_a_tick_run_without_the_fetch_before_it_fetches_once(
    boundaries: Boundaries, counting: CountingFetch, explicit: bool
) -> None:
    tick = _tick(boundaries, counting)

    outcome = tick.run(fetched=False) if explicit else tick.run()

    assert counting.fetches == 1
    assert outcome.stopped is None
    assert outcome.dispatch is not None


def test_a_tick_run_alone_whose_fetch_fails_stops_and_the_next_passed_one_clears_it(
    boundaries: Boundaries, counting: CountingFetch, remote: Path, tmp_path: Path
) -> None:
    tick = _tick(boundaries, counting)
    moved = move_remote_away(remote, tmp_path)

    failed = tick.run(fetched=False)

    assert failed == TickOutcome(stopped="fetch_failed")
    assert [stop.reason for stop in boundaries.health.read().stops] == ["fetch_failed"]
    moved.rename(remote)

    passed = tick.run(fetched=False)

    assert passed.stopped is None
    assert passed.dispatch is not None
    assert all(stop.reason != "fetch_failed" for stop in boundaries.health.read().stops)
