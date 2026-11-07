# SPDX-License-Identifier: Apache-2.0
"""The images of the stage, built and read by the `podman` executable."""

import json
import tempfile
import time
from datetime import timedelta
from pathlib import Path

from factory.machine.adapters.podman_runs import PODMAN_TIME_LIMIT, run_podman
from factory.machine.application.images import ImageBuild, Images
from factory.machine.domain.containers import JOB_PODMAN_OPTIONS, SYSTEM_PATH
from factory.machine.domain.stage_layer import StageLayer
from factory.shared.adapters.printed_output import failure_detail
from factory.shared.domain.errors import ContainerError
from factory.shared.domain.settings import ContainerProfileName
from factory.watching.domain.machine import count_warnings

BUILD_OUTPUT_TAIL_LINES = 20

_CONTAINERFILE_NAME = "Containerfile"
_CONTEXT_NAME = "context"
_PATH_PREFIX = "PATH="


class PodmanImages(Images):
    """Builds a project's layer and reads an image's configuration through `podman`."""

    def __init__(self, executable: str, *, profile: ContainerProfileName = "rootless") -> None:
        """Build and inspect images through `executable`, with the job's global options in a job."""
        self._podman = [executable, *(JOB_PODMAN_OPTIONS if profile == "job" else ())]

    def build(self, layer: StageLayer, base: str, tag: str, time_limit: timedelta) -> ImageBuild:
        """Run `podman build` on the layer's text in an empty context, then prune untagged ones."""
        with tempfile.TemporaryDirectory(prefix="factory-stage-file-") as folder:
            containerfile = Path(folder, _CONTAINERFILE_NAME)
            containerfile.write_text(layer.text, encoding="utf-8")
            context = Path(folder, _CONTEXT_NAME)
            context.mkdir()
            argv = [
                *self._podman,
                "build",
                "--build-arg",
                f"FACTORY_BASE={base}",
                "--network=host",
                "-t",
                tag,
                "-f",
                str(containerfile),
                str(context),
            ]
            started = time.monotonic()
            try:
                result = run_podman(argv, time_limit)
            except ContainerError as error:
                # Podman may still be ending a build its limit cut off; the next build's prune
                # removes what that one left.
                elapsed = timedelta(seconds=time.monotonic() - started)
                return ImageBuild(passed=False, duration=elapsed, output_tail=str(error))
        run_podman([*self._podman, "image", "prune", "-f"], PODMAN_TIME_LIMIT)
        return ImageBuild(
            passed=result.exit_status == 0,
            duration=result.duration,
            output_tail="\n".join(result.stdout.splitlines()[-BUILD_OUTPUT_TAIL_LINES:]),
            warnings=count_warnings(result.stdout),
        )

    def path(self, image: str) -> str:
        """The `PATH` of the image's configured environment, or the base's when it sets none."""
        argv = [*self._podman, "image", "inspect", "--format", "{{json .Config.Env}}", image]
        command = " ".join(argv)
        result = run_podman(argv, PODMAN_TIME_LIMIT)
        if result.exit_status != 0:
            raise ContainerError(command, failure_detail(result.stdout, result.exit_status))
        try:
            environment = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise ContainerError(command, f"printed no environment: {error}") from error
        return _configured_path(environment) or SYSTEM_PATH

    def size_bytes(self, image: str) -> int | None:
        """The size `podman image inspect` gives `image`, or `None` when it gives none."""
        printed = self._printed(["image", "inspect", "--format", "{{.Size}}", image])
        if printed is None or not printed.isdigit():
            return None
        return int(printed)

    def store_path(self) -> Path | None:
        """The graph root `podman info` names, or `None` when it names none."""
        printed = self._printed(["info", "--format", "{{.Store.GraphRoot}}"])
        return None if not printed else Path(printed)

    def _printed(self, words: list[str]) -> str | None:
        # A measure the machine cannot give is unknown, never a fault of the run.
        try:
            result = run_podman([*self._podman, *words], PODMAN_TIME_LIMIT)
        except ContainerError:
            return None
        if result.exit_status != 0:
            return None
        return result.stdout.strip()


def _configured_path(environment: object) -> str | None:
    # Podman prints `null` for an image that configures no environment.
    if not isinstance(environment, list):
        return None
    for entry in environment:
        if isinstance(entry, str) and entry.startswith(_PATH_PREFIX):
            return entry.removeprefix(_PATH_PREFIX)
    return None
