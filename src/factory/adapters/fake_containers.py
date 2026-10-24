"""The fake container runs the tests use: a child process on the host, with the paths mapped."""

from collections.abc import Mapping, Sequence
from datetime import timedelta
from pathlib import Path

from factory.adapters.process import ProcessRequest, run_process
from factory.application.containers import ContainerRuns
from factory.domain.containers import WORK, ContainerCall, ContainerLaunch, ContainerResult, Mount
from factory.domain.errors import ContainerError

# The shell goes to the working directory and then becomes the command, as a container would.
_ENTER = ["/bin/sh", "-c", 'cd "$1" && shift && exec "$@"', "fake-container"]


class FakeContainerRuns(ContainerRuns):
    """Container runs played on the host: a child process, the mounts' paths mapped to folders."""

    def __init__(self, workspace: Path) -> None:
        """Play `/work` as `workspace`, and record every accepted call."""
        self._workspace = workspace
        self._calls: list[ContainerCall] = []

    @property
    def calls(self) -> list[ContainerCall]:
        """Every call of `launch` and `run` that was not refused with `ValueError`, in order."""
        return list(self._calls)

    def launch(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerLaunch:
        """The shell words that enter the mapped working directory and run the mapped command."""
        call = self._accept(command, mounts, environment, time_limit, working_directory)
        return self._launch(call)

    def run(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerResult:
        """Run the launch's words as a child process on the host, its output merged."""
        call = self._accept(command, mounts, environment, time_limit, working_directory)
        launch = self._launch(call)
        request = ProcessRequest(
            argv=launch.argv,
            cwd=Path(self._map(call.working_directory, call.mounts)),
            env=launch.env,
            time_limit=launch.time_limit,
            merge_stderr=True,
        )
        try:
            result = run_process(request)
        except OSError as error:
            raise ContainerError(call.command[0], str(error)) from error
        return ContainerResult(
            exit_status=result.exit_status,
            output=result.stdout,
            timed_out=result.timed_out,
            duration=result.duration,
        )

    def _accept(
        self,
        command: Sequence[str],
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerCall:
        if not command:
            raise ValueError("a container run needs command words")
        for mount in mounts:
            if _lies_under(mount.target, WORK):
                raise ValueError(f"a mount may not target {mount.target}: the dataset is {WORK}")
        call = ContainerCall(
            command=list(command),
            mounts=list(mounts),
            environment=dict(environment),
            time_limit=time_limit,
            working_directory=working_directory,
        )
        self._calls.append(call)
        return call

    def _launch(self, call: ContainerCall) -> ContainerLaunch:
        return ContainerLaunch(
            argv=[
                *_ENTER,
                self._map(call.working_directory, call.mounts),
                *(self._map(word, call.mounts) for word in call.command),
            ],
            env={name: self._map(value, call.mounts) for name, value in call.environment.items()},
            time_limit=call.time_limit,
        )

    def _map(self, value: str, mounts: Sequence[Mount]) -> str:
        every_mount = [*mounts, Mount(source=self._workspace, target=WORK)]
        # The longest target first, so that a deeper mount wins over the one it lies in.
        for mount in sorted(every_mount, key=lambda mount: len(mount.target), reverse=True):
            if _lies_under(value, mount.target):
                return str(mount.source) + value.removeprefix(mount.target)
        return value


def _lies_under(path: str, target: str) -> bool:
    return path == target or path.startswith(f"{target}/")
