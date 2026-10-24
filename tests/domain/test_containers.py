"""The container DTOs: a mount, a launch, a result and a recorded call."""

from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from factory.domain.containers import ContainerLaunch, ContainerResult, Mount


@pytest.mark.parametrize(
    ("target", "accepted"),
    [
        pytest.param("/work", True, id="work"),
        pytest.param("/work/checkout", True, id="work-checkout"),
        pytest.param("/etc/factory/claude", True, id="deep"),
        pytest.param("/", False, id="root-alone"),
        pytest.param("work/x", False, id="relative"),
        pytest.param("/a/../b", False, id="dot-dot"),
        pytest.param("/a//b", False, id="empty-segment"),
        pytest.param("", False, id="empty"),
        pytest.param("/a/", False, id="trailing-slash"),
    ],
)
def test_a_mount_target_is_an_absolute_container_path(target: str, accepted: bool) -> None:
    if accepted:
        assert Mount(source=Path("/srv/x"), target=target).target == target
    else:
        with pytest.raises(ValidationError):
            Mount(source=Path("/srv/x"), target=target)


@pytest.mark.parametrize(
    ("source", "accepted"),
    [
        pytest.param("/srv/x", True, id="absolute"),
        pytest.param("srv/x", False, id="relative"),
    ],
)
def test_a_mount_source_must_be_absolute(source: str, accepted: bool) -> None:
    if accepted:
        assert Mount(source=Path(source), target="/x").source == Path(source)
    else:
        with pytest.raises(ValidationError):
            Mount(source=Path(source), target="/x")


def test_a_mount_is_writable_by_default() -> None:
    assert Mount(source=Path("/srv/x"), target="/x").read_only is False


@pytest.mark.parametrize(
    ("argv", "env", "time_limit", "accepted"),
    [
        pytest.param([], {}, timedelta(seconds=1), False, id="no-words"),
        pytest.param(["true"], {}, timedelta(0), False, id="zero-limit"),
        pytest.param(["true"], {}, timedelta(seconds=-1), False, id="negative-limit"),
        pytest.param(["true"], {}, timedelta(seconds=1), True, id="one-word-one-second"),
        pytest.param(["true"], None, timedelta(seconds=1), True, id="env-none"),
        pytest.param(["true"], {"A": "b"}, timedelta(seconds=1), True, id="env-given"),
    ],
)
def test_a_container_launch_needs_words_and_a_positive_limit_and_keeps_env(
    argv: list[str], env: dict[str, str] | None, time_limit: timedelta, accepted: bool
) -> None:
    if accepted:
        launch = ContainerLaunch(argv=argv, env=env, time_limit=time_limit)
        assert launch.argv == argv
        assert launch.env == env
        assert launch.time_limit == time_limit
    else:
        with pytest.raises(ValidationError):
            ContainerLaunch(argv=argv, env=env, time_limit=time_limit)


@pytest.mark.parametrize(
    ("exit_status", "timed_out", "accepted"),
    [
        pytest.param(None, True, True, id="timed-out-without-status"),
        pytest.param(0, False, True, id="success"),
        pytest.param(137, False, True, id="failure"),
        pytest.param(None, False, False, id="no-status-not-timed-out"),
        pytest.param(137, True, False, id="status-and-timed-out"),
    ],
)
def test_a_container_result_has_no_exit_status_exactly_when_it_timed_out(
    exit_status: int | None, timed_out: bool, accepted: bool
) -> None:
    def build() -> ContainerResult:
        return ContainerResult(
            exit_status=exit_status,
            output="",
            timed_out=timed_out,
            duration=timedelta(seconds=1),
        )

    if accepted:
        result = build()
        assert (result.exit_status, result.timed_out) == (exit_status, timed_out)
    else:
        with pytest.raises(ValidationError):
            build()
