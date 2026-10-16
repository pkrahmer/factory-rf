"""The health check: the stops of the health status file as lines and an exit status."""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.process import ProcessRequest, run_process
from factory.application.boundaries import Boundaries
from factory.application.stops import StopService
from factory.domain.stops import HealthStatus, RepositoryStop, RepositoryStopReason, StopScope
from factory.entry.health import main

AT = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
MAKE_MISSING = RepositoryStop(
    scope="machine",
    reason="preflight_failed",
    detail="tool:make: make is not on the PATH",
    at=AT,
)


def _write(state_directory: Path, *stops: RepositoryStop) -> None:
    JsonHealthStatusFile(state_directory / "health.json").write(HealthStatus(stops=list(stops)))


def test_a_state_directory_without_a_health_file_is_healthy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status = main(["--state-directory", str(tmp_path)])

    assert capsys.readouterr().out == "healthy\n"
    assert status == 0


def test_one_stop_prints_its_line_and_returns_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(tmp_path, MAKE_MISSING)

    status = main(["--state-directory", str(tmp_path)])

    assert capsys.readouterr().out == (
        "preflight_failed (machine): tool:make: make is not on the PATH"
        " (since 2026-10-12T12:00:00Z)\n"
    )
    assert status == 1


def test_a_given_store_is_read_and_each_stop_prints_one_line_in_order(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    later = datetime(2026, 10, 13, 8, 30, 5, tzinfo=UTC)
    unavailable = RepositoryStop(
        scope="repository",
        reason="repository_unavailable",
        detail="the repository has no main branch yet",
        at=later,
    )
    store = JsonHealthStatusFile(tmp_path / "elsewhere" / "status.json")
    store.write(HealthStatus(stops=[unavailable, MAKE_MISSING]))

    status = main([], store=store)

    assert capsys.readouterr().out.splitlines() == [
        "repository_unavailable (repository): the repository has no main branch yet"
        " (since 2026-10-13T08:30:05Z)",
        "preflight_failed (machine): tool:make: make is not on the PATH"
        " (since 2026-10-12T12:00:00Z)",
    ]
    assert status == 1


@pytest.mark.parametrize(
    "reason",
    [
        "fetch_failed",
        "checkout_restore_failed",
        "pipeline_definition_invalid",
        "agent_definition_invalid",
        "repository_unavailable",
        "main_branch_failing",
        "preflight_failed",
    ],
)
def test_every_stop_reason_makes_the_check_fail_until_it_is_cleared(
    boundaries: Boundaries, tmp_path: Path, reason: RepositoryStopReason
) -> None:
    scope: StopScope = "machine" if reason == "preflight_failed" else "repository"
    stops = StopService(boundaries)
    arguments = ["--state-directory", str(tmp_path / "state")]

    stops.raise_stop(RepositoryStop(scope=scope, reason=reason, detail="a fault", at=AT))
    raised = main(arguments)
    stops.clear_stop(reason)
    cleared = main(arguments)

    assert (raised, cleared) == (1, 0)


@pytest.mark.parametrize(("stops", "exit_status"), [((), 0), ((MAKE_MISSING,), 1)])
def test_the_module_run_as_a_process_exits_with_the_health_status(
    tmp_path: Path, stops: tuple[RepositoryStop, ...], exit_status: int
) -> None:
    state = tmp_path / "state"
    state.mkdir()
    if stops:
        _write(state, *stops)

    result = run_process(
        ProcessRequest(
            argv=[sys.executable, "-m", "factory.entry.health", "--state-directory", str(state)],
            cwd=tmp_path,
        )
    )

    assert result.exit_status == exit_status
