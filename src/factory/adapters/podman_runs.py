"""Throwaway containers of one image on the dataset, started rootless by the `podman` executable."""

import math
from collections.abc import Mapping, Sequence
from datetime import timedelta
from pathlib import Path

from factory.adapters.agent_launch import KILL_STATUSES
from factory.adapters.printed_output import failure_detail, first_printed_line, no_end_detail
from factory.adapters.process import ProcessRequest, ProcessResult, run_process
from factory.application.containers import ContainerRuns
from factory.domain.containers import (
    WORK,
    ContainerLaunch,
    ContainerResult,
    Mount,
    check_container_call,
)
from factory.domain.errors import ContainerError

# Podman's `--timeout` ends the container at its limit; the factory's own kill waits this
# much longer, so that it fires only when podman's did not.
CONTAINER_GRACE = timedelta(seconds=30)
PODMAN_TIME_LIMIT = timedelta(minutes=2)

# Podman reads no file from its working directory; the container's is `--workdir`.
_ROOT = Path("/")


def _volume(mount: Mount) -> str:
    # A rootless container cannot write a `:ro` bind mount: the protection of the host's files.
    suffix = ":ro" if mount.read_only else ""
    return f"{mount.source}:{mount.target}{suffix}"


def _killed_at_limit(result: ProcessResult, time_limit: timedelta) -> bool:
    return result.exit_status in KILL_STATUSES and result.duration >= time_limit


class PodmanRuns(ContainerRuns):
    """Throwaway containers of one image, started rootless by the `podman` executable."""

    def __init__(
        self,
        executable: str,
        image: str,
        workspace: Path,
        *,
        time_limit: timedelta = PODMAN_TIME_LIMIT,
    ) -> None:
        """Start containers of `image` through `executable`, `workspace` mounted at `/work`.

        `time_limit` bounds the queries `version` and `image_exists`.
        """
        self._executable = executable
        self._image = image
        self._workspace = workspace
        self._time_limit = time_limit

    def launch(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerLaunch:
        """The `podman run` words, under the factory's environment and the limit plus the grace."""
        check_container_call(command, mounts)
        environment_words = [
            word for name, value in environment.items() for word in ("--env", f"{name}={value}")
        ]
        volumes = [Mount(source=self._workspace, target=WORK), *mounts]
        volume_words = [word for mount in volumes for word in ("--volume", _volume(mount))]
        argv = [
            self._executable,
            "run",
            "--rm",
            "--userns=keep-id",
            "--timeout",
            str(math.ceil(time_limit.total_seconds())),
            *environment_words,
            *volume_words,
            "--workdir",
            working_directory,
            self._image,
            *command,
        ]
        return ContainerLaunch(argv=argv, env=None, time_limit=time_limit + CONTAINER_GRACE)

    def run(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerResult:
        """Run the launch's words; podman's exit status is the command's, 125 its own fault."""
        launch = self.launch(
            command,
            mounts=mounts,
            environment=environment,
            time_limit=time_limit,
            working_directory=working_directory,
        )
        request = ProcessRequest(
            argv=launch.argv,
            cwd=_ROOT,
            env=launch.env,
            time_limit=launch.time_limit,
            merge_stderr=True,
        )
        try:
            result = run_process(request)
        except OSError as error:
            raise ContainerError(command[0], str(error)) from error
        timed_out = result.timed_out or _killed_at_limit(result, time_limit)
        return ContainerResult(
            exit_status=None if timed_out else result.exit_status,
            output=result.stdout,
            timed_out=timed_out,
            duration=result.duration,
        )

    def version(self) -> str:
        """The first non-blank line `<podman> --version` prints; `ContainerError` when it fails."""
        arguments = ["--version"]
        result = self._query(arguments)
        if result.exit_status != 0:
            raise ContainerError(
                self._command(arguments), failure_detail(result.stdout, result.exit_status)
            )
        version = first_printed_line(result.stdout)
        if version is None:
            raise ContainerError(self._command(arguments), "printed nothing")
        return version

    def image_exists(self) -> bool:
        """Whether `<podman> image exists <image>` finds the image; `ContainerError` for a fault."""
        arguments = ["image", "exists", self._image]
        result = self._query(arguments)
        if result.exit_status not in (0, 1):
            raise ContainerError(
                self._command(arguments), failure_detail(result.stdout, result.exit_status)
            )
        return result.exit_status == 0

    def _command(self, arguments: list[str]) -> str:
        return " ".join([self._executable, *arguments])

    def _query(self, arguments: list[str]) -> ProcessResult:
        request = ProcessRequest(
            argv=[self._executable, *arguments],
            cwd=self._workspace,
            env=None,
            time_limit=self._time_limit,
            merge_stderr=True,
        )
        try:
            result = run_process(request)
        except OSError as error:
            raise ContainerError(self._command(arguments), str(error)) from error
        if result.timed_out:
            raise ContainerError(self._command(arguments), no_end_detail(self._time_limit))
        return result
