"""The tick's repository stops carry the error's text, and the error cap reaches the log."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.boundaries import Boundaries
from factory.application.tick import IdleHandler, Tick, TickOutcome
from factory.domain.errors import FetchFailed, GitError
from factory.domain.git import GitOptions
from factory.domain.kill_points import KillPoints
from git_support import CHECKOUT, TEST_IDENTITY
from log_support import log_lines
from stage_run_support import INSTANCE
from tick_support import Failing, handlers_of

pytestmark = pytest.mark.usefixtures("installed_agents")


class FailingFetch(GitCli):
    """A git whose fetch fails as a hung-up remote does."""

    def fetch(self) -> None:
        raise FetchFailed("git fetch", 128, "fatal: the remote end hung up")


class FailingReset(GitCli):
    """A git whose hard reset fails as an unwritable index does."""

    def reset_to(self, ref: str) -> None:
        del ref  # The reset fails whatever it was asked to reset to.
        raise GitError("git reset", 128, "fatal: unable to write the index")


@pytest.mark.parametrize(
    ("git_class", "outcome", "stops"),
    [
        pytest.param(
            FailingFetch,
            TickOutcome(stopped="fetch_failed"),
            [("fetch_failed", "git fetch failed (exit 128): fatal: the remote end hung up")],
            id="fetch",
        ),
        pytest.param(
            FailingReset,
            TickOutcome(stopped="checkout_restore_failed"),
            [
                (
                    "checkout_restore_failed",
                    "git reset failed (exit 128): fatal: unable to write the index",
                )
            ],
            id="restore",
        ),
    ],
)
def test_a_repository_stop_carries_the_errors_text_as_its_detail(
    boundaries: Boundaries,
    *,
    tmp_path: Path,
    kill_points: KillPoints,
    git_class: Callable[[Path, GitOptions], GitCli],
    outcome: TickOutcome,
    stops: list[tuple[str, str]],
) -> None:
    git = git_class(
        tmp_path / CHECKOUT, GitOptions(kill_points=kill_points, identity=TEST_IDENTITY)
    )

    result = Tick(
        replace(boundaries, git=git), INSTANCE, handlers_of({"idle": IdleHandler()})
    ).run()

    assert result == outcome
    assert [(stop.reason, stop.detail) for stop in boundaries.health.read().stops] == stops


def test_the_error_cap_of_an_event_without_a_work_item_is_written_to_the_factory_log(
    boundaries: Boundaries, tmp_path: Path
) -> None:
    tick = Tick(
        boundaries, INSTANCE, handlers_of({"idle": Failing(RuntimeError("handler failed"))})
    )

    outcomes = [tick.run().dispatch for _ in range(3)]

    assert outcomes == ["error", "error", "reported"]
    assert [line for line in log_lines(tmp_path) if "error cap" in line] == [
        "2026-10-12T12:00:00Z error cap reached on idle:-: RuntimeError: handler failed"
    ]
