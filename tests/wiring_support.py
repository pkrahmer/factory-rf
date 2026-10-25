"""Constants and helpers the wiring and preflight tests share."""

from pathlib import Path

from factory.application.boundaries import Boundaries
from factory.domain.preflight import PreflightItem
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import machine_extras
from podman_support import IMAGE, PodmanPlan, write_podman
from zfs_support import DATASET, Answer, write_zfs

CREDENTIAL = "example-value"
ENVIRONMENT = {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}
HOSTED_URL = "https://github.com/example/project.git"
PODMAN_VERSION = "podman version 4.9.3"
CONTAINER_ITEMS = ["token-file", "podman", "zfs", "dataset", "stage-image"]


def every_tool(name: str) -> str | None:
    """Find every tool, each under `/usr/bin`."""
    return f"/usr/bin/{name}"


def machine_item(
    boundaries: Boundaries, settings: InstanceSettings, environment: dict[str, str], name: str
) -> PreflightItem:
    """Return the item `name` of `machine_extras`, running only the items before it."""
    # The items run in order up to the one asked for, so the agent run probe never starts.
    for check in machine_extras(boundaries, settings, environment):
        item = check()
        if item.name == name:
            return item
    raise AssertionError(name)


def with_dataset(settings: InstanceSettings, root: Path) -> InstanceSettings:
    """The settings with a dataset, a workspace `<root>/work`, an image and stand-in tools.

    The stand-in `zfs` and `podman` are written into `<root>/zfs-bin` and `<root>/podman-bin`:
    `podman` prints its version, `zfs` its version and the dataset, so the preflight passes.
    """
    workspace = root / "work"
    workspace.mkdir(exist_ok=True)
    zfs = write_zfs(
        root / "zfs-bin",
        {"--version": Answer(stdout="zfs-2.2.2\n"), "list": Answer(stdout=f"{DATASET}\n")},
    )
    podman = write_podman(root / "podman-bin", PodmanPlan(stdout=f"{PODMAN_VERSION}\n"))
    return settings.model_copy(
        update={
            "dataset": DATASET,
            "workspace": workspace,
            "stage_image": IMAGE,
            "zfs_executable": str(zfs.path),
            "podman_executable": str(podman.path),
        }
    )
