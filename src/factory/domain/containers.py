"""The data of a container run: its mounts, the words that start it, its result and its call."""

from collections.abc import Mapping, Sequence
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from factory.domain.agent_runs import AbsolutePath
from factory.domain.settings import InstanceSettings

WORK = "/work"
WORK_CHECKOUT = "/work/checkout"
WORK_HOME = "/work/home"
# Node, OpenSSL and Python's requests each read the CA bundle from one of these.
CA_BUNDLE_NAMES = ("NODE_EXTRA_CA_CERTS", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE")
# Podman's global options in a managed sandbox such as a Cloud Run job: crun refuses its hybrid
# cgroups where runc accepts them, and `overlay` makes podman refuse an unsuitable storage root
# instead of falling back to a slower driver. The machine puts that root where the kernel's own
# overlay accepts it, a tmpfs in a job, since a userspace overlay made the tests too slow there.
JOB_PODMAN_OPTIONS: tuple[str, ...] = (
    "--runtime=runc",
    "--cgroup-manager=cgroupfs",
    "--storage-driver=overlay",
)
# The instance id is the metadata server's smallest answer; `000` means curl could not connect.
METADATA_PROBE_URL = "http://169.254.169.254/computeMetadata/v1/instance/id"
METADATA_PROBE_COMMAND: tuple[str, ...] = (
    "curl",
    "-sS",
    "-m",
    "5",
    "-o",
    "/dev/null",
    "-w",
    "%{http_code}",
    METADATA_PROBE_URL,
)


def _must_be_container_path(target: str) -> str:
    # Split by hand: `PurePosixPath` would fold `/a//b` and `/a/` into valid paths.
    segments = target.removeprefix("/").split("/")
    if not target.startswith("/") or any(segment in {"", ".."} for segment in segments):
        raise ValueError(f"not an absolute container path: {target!r}")
    return target


ContainerPath = Annotated[str, AfterValidator(_must_be_container_path)]


class Mount(BaseModel):
    """A host path mounted into a container: its source, its target, read-only or not."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source: AbsolutePath
    target: ContainerPath
    read_only: bool = False


def read_only_at_own_path(path: Path) -> Mount:
    """The mount of the host file `path`, read-only, at the same path in the container."""
    return Mount(source=path, target=str(path), read_only=True)


def bundle_mounts(ca_bundle: Path | None) -> list[Mount]:
    """The mount of the operator's CA bundle, or none without one."""
    return [] if ca_bundle is None else [read_only_at_own_path(ca_bundle)]


def extra_environment(settings: InstanceSettings, source: Mapping[str, str]) -> dict[str, str]:
    """The environment the operator adds to every container: the listed names, then the bundle.

    A listed name that `source` lacks is left out; the bundle's names win over listed ones.
    """
    extra = {name: source[name] for name in settings.container_env if name in source}
    if settings.ca_bundle is not None:
        extra.update(dict.fromkeys(CA_BUNDLE_NAMES, str(settings.ca_bundle)))
    return extra


def beneath_or_at(relative: str, above: str) -> bool:
    """Whether the `/`-separated path `relative` is `above` itself or lies under it."""
    return relative == above or relative.startswith(f"{above}/")


def check_container_call(command: Sequence[str], mounts: Sequence[Mount]) -> None:
    """Refuse with `ValueError` a run without command words or a mount on the dataset `/work`."""
    if not command:
        raise ValueError("a container run needs command words")
    for mount in mounts:
        if beneath_or_at(mount.target, WORK):
            raise ValueError(f"a mount may not target {mount.target}: the dataset is {WORK}")


class ContainerLaunch(BaseModel):
    """The words, environment and time limit that start one command in a container."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    argv: Annotated[list[str], Field(min_length=1)]
    # `None`: the process's own environment.
    env: dict[str, str] | None
    time_limit: Annotated[timedelta, Field(gt=timedelta(0))]


class ContainerResult(BaseModel):
    """What one container run left: the command's exit status, its merged output, its end."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    exit_status: int | None
    output: str
    timed_out: bool
    duration: timedelta

    @model_validator(mode="after")
    def _no_exit_status_exactly_when_timed_out(self) -> Self:
        if (self.exit_status is None) != self.timed_out:
            raise ValueError(
                f"exit status {self.exit_status} contradicts timed_out {self.timed_out}"
            )
        return self


class ContainerCall(BaseModel):
    """One command a `ContainerRuns` was asked to launch or run, as it was asked."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    command: list[str]
    mounts: list[Mount]
    environment: dict[str, str]
    time_limit: timedelta
    working_directory: str
