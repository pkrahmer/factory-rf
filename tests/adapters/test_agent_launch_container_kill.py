"""Podman's exit status at its `--timeout` is read as the kill at the limit, in a container only."""

from datetime import timedelta

import pytest

from factory.adapters.agent_launch import (
    CONTAINER_KILL_STATUSES,
    KILL_STATUSES,
    PODMAN_TIMEOUT_STATUS,
    killed_at_limit,
)

LIMIT = timedelta(seconds=30)


def test_a_container_s_kill_statuses_add_podman_s_timeout_status() -> None:
    assert frozenset({137, -9, 255}) == CONTAINER_KILL_STATUSES
    assert PODMAN_TIMEOUT_STATUS == 255
    assert frozenset({137, -9}) == KILL_STATUSES


@pytest.mark.parametrize(
    ("in_container", "exit_status", "seconds", "killed"),
    [
        pytest.param(True, 255, 30.0, True, id="container-255-at-the-limit"),
        pytest.param(True, 255, 29.9, False, id="container-255-before-the-limit"),
        pytest.param(True, 137, 30.0, True, id="container-137-at-the-limit"),
        pytest.param(True, 1, 30.0, False, id="container-1-at-the-limit"),
        pytest.param(False, 255, 30.0, False, id="no-user-255-at-the-limit"),
    ],
)
def test_255_at_the_limit_is_a_kill_only_in_a_container(
    *, in_container: bool, exit_status: int, seconds: float, killed: bool
) -> None:
    result = killed_at_limit(
        exit_status=exit_status,
        duration=timedelta(seconds=seconds),
        time_limit=LIMIT,
        in_container=in_container,
    )

    assert result is killed
