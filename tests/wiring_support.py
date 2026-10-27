"""Constants and helpers the wiring and preflight tests share."""

from collections.abc import Callable
from pathlib import Path

import github
import pytest

from factory.application.boundaries import Boundaries
from factory.domain.preflight import PreflightItem
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import machine_extras
from podman_support import IMAGE, Podman, PodmanPlan, write_podman
from zfs_support import DATASET, Answer, write_zfs

CREDENTIAL = "example-value"
ENVIRONMENT = {"PATH": "/opt/scripts:/usr/bin:/bin", "HOME": "/home/factory"}
HOSTED_URL = "https://github.com/example/project.git"
PODMAN_VERSION = "podman version 4.9.3"
CONTAINER_ITEMS = ["token-file", "podman", "zfs", "dataset", "stage-image"]


def _record_get_repo(monkeypatch: pytest.MonkeyPatch) -> list[tuple[object, ...]]:
    """Record the arguments of every `Github.get_repo` call; the calls still go through."""
    repositories: list[tuple[object, ...]] = []
    original: Callable[..., object] = github.Github.get_repo

    def recording(self: github.Github, *args: object, **kwargs: object) -> object:
        repositories.append((*args, *kwargs.values()))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(github.Github, "get_repo", recording)
    return repositories


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


def dataset_podman(root: Path, plan: PodmanPlan) -> Podman:
    """The stand-in `podman` that `with_dataset(settings, root)` wrote, planned as `plan`."""
    folder = root / "podman-bin"
    podman = Podman(path=folder / "podman", folder=folder)
    podman.plan(plan)
    return podman


def run_words(podman: Podman) -> list[str]:
    """The words of the one `podman run` call the stand-in saw."""
    [call] = [call for call in podman.calls() if call.arguments[:1] == ["run"]]
    return call.arguments


def after_image(words: list[str]) -> list[str]:
    """The words of a `podman run` call that follow the image: the container's command."""
    return words[words.index(IMAGE) + 1 :]
