"""The shared launch module starts a call in a container and reads its kill at the limit."""

from collections.abc import Mapping, Sequence
from datetime import timedelta
from pathlib import Path

import pytest

from adapters.container_runtime_support import read_only
from factory.adapters.agent_launch import (
    CallEnd,
    Launch,
    LoginFiles,
    Starters,
    container_launch,
    killed_at_limit,
    read_call_end,
    version_launch,
)
from factory.adapters.fake_containers import FakeContainerRuns
from factory.domain.containers import WORK_CHECKOUT, ContainerCall, ContainerLaunch, Mount

INSTRUCTIONS = Path("/state/runs/instructions-1.md")
TOKEN = Path("/home/factory/.claude-token")
MINUTE = timedelta(seconds=60)


class _OwnEnvironmentRuns(FakeContainerRuns):
    """The fake's launch, with the process's own environment as `PodmanRuns` gives it."""

    def launch(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerLaunch:
        launched = super().launch(
            command,
            mounts=mounts,
            environment=environment,
            time_limit=time_limit,
            working_directory=working_directory,
        )
        return launched.model_copy(update={"env": None})


@pytest.mark.parametrize(
    ("runs_class", "argv", "environment", "files", "time_limit", "refused"),
    [
        pytest.param(
            FakeContainerRuns,
            ["/bin/sh", "-c", "x"],
            {"HOME": "/work/home"},
            [INSTRUCTIONS, TOKEN],
            timedelta(minutes=2),
            False,
            id="mounted",
        ),
        pytest.param(
            _OwnEnvironmentRuns,
            ["/bin/true"],
            {},
            [],
            timedelta(seconds=1),
            False,
            id="own-environment",
        ),
        pytest.param(
            FakeContainerRuns,
            ["/bin/true"],
            {},
            [Path("/state/a"), Path("/state/b"), Path("/state/a")],
            timedelta(seconds=1),
            False,
            id="each-file-once",
        ),
        pytest.param(
            FakeContainerRuns,
            ["x"],
            {},
            [Path("/work/x")],
            timedelta(seconds=1),
            True,
            id="mount-under-work",
        ),
    ],
)
def test_a_container_launch_mounts_the_files_read_only_at_their_own_paths(  # noqa: PLR0913 - one parameter per column of the table
    tmp_path: Path,
    *,
    runs_class: type[FakeContainerRuns],
    argv: list[str],
    environment: dict[str, str],
    files: list[Path],
    time_limit: timedelta,
    refused: bool,
) -> None:
    runs = runs_class(tmp_path / "workspace")
    mounts = [read_only(file) for file in dict.fromkeys(files)]

    if refused:
        with pytest.raises(ValueError, match="/work"):
            container_launch(runs, argv, environment, files=files, time_limit=time_limit)
        assert runs.calls == []
        return
    started = container_launch(runs, argv, environment, files=files, time_limit=time_limit)

    expected = runs_class(tmp_path / "workspace").launch(
        argv,
        mounts=mounts,
        environment=environment,
        time_limit=time_limit,
        working_directory=WORK_CHECKOUT,
    )
    assert started == Launch(argv=expected.argv, env=expected.env, time_limit=expected.time_limit)
    assert runs.calls == [
        ContainerCall(
            command=argv,
            mounts=mounts,
            environment=environment,
            time_limit=time_limit,
            working_directory=WORK_CHECKOUT,
        )
    ]


@pytest.mark.parametrize(
    ("in_container", "exit_status", "seconds", "expected"),
    [
        pytest.param(True, 137, 61, True, id="137-after-the-limit"),
        pytest.param(True, -9, 60, True, id="sigkill-at-the-limit"),
        pytest.param(True, 137, 59, False, id="137-before-the-limit"),
        pytest.param(True, 1, 61, False, id="status-1-after-the-limit"),
        pytest.param(False, 137, 61, False, id="not-in-a-container"),
    ],
)
def test_in_a_container_a_kill_status_at_the_limit_is_the_limit(
    *, in_container: bool, exit_status: int, seconds: int, expected: bool
) -> None:
    assert (
        killed_at_limit(
            os_user=None,
            exit_status=exit_status,
            duration=timedelta(seconds=seconds),
            time_limit=MINUTE,
            in_container=in_container,
        )
        is expected
    )


@pytest.mark.parametrize(
    "stderr",
    [
        pytest.param("", id="quiet"),
        pytest.param("sudo: unable to resolve host x\n", id="sudo-line"),
    ],
)
def test_a_container_call_killed_at_the_limit_is_read_as_the_limit_and_no_refusal(
    stderr: str,
) -> None:
    end = CallEnd(
        stderr=stderr,
        printed=False,
        exit_status=137,
        duration=timedelta(seconds=61),
        timed_out=False,
    )
    starters = Starters(
        sudo_executable="/usr/bin/sudo", confine_executable=None, login_files=LoginFiles()
    )

    assert (
        read_call_end(end, time_limit=MINUTE, os_user=None, starters=starters, in_container=True)
        is True
    )


def test_the_version_call_on_the_host_has_the_process_s_own_environment() -> None:
    assert version_launch("claude", containers=None, time_limit=timedelta(seconds=30)) == Launch(
        argv=["claude", "--version"], env=None, time_limit=timedelta(seconds=30)
    )
