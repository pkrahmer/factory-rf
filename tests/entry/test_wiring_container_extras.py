"""The extra machine items of a container instance, in order, run on the adapters it builds."""

from pathlib import Path

import pytest

from factory.application.boundaries import Boundaries
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import machine_extras
from podman_support import IMAGE, Podman, PodmanPlan
from wiring_support import CONTAINER_ITEMS, PODMAN_VERSION, machine_item
from zfs_support import DATASET, Zfs

INLINE_ITEMS = ["token-file", "agent-environment"]


@pytest.fixture
def environment(tmp_path: Path) -> dict[str, str]:
    """The agent runs' environment."""
    return {"PATH": "/usr/bin", "HOME": str(tmp_path)}


def _settings(
    tmp_path: Path,
    agent_home: Path,
    versioned_podman: Podman,
    listing_zfs: Zfs,
    fields: dict[str, object],
) -> InstanceSettings:
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    return InstanceSettings.model_validate(
        {
            "repository_url": "/srv/project.git",
            "instance": "factory-1",
            "state_directory": tmp_path / "state",
            "agent_home": agent_home,
            "workspace": workspace,
            "dataset": DATASET,
            "stage_image": IMAGE,
            "podman_executable": str(versioned_podman.path),
            "zfs_executable": str(listing_zfs.path),
            **fields,
        }
    )


@pytest.mark.parametrize(
    ("fields", "names"),
    [
        pytest.param(
            {"stage_environment": "container"},
            [*CONTAINER_ITEMS, "agent-run-probe"],
            id="container",
        ),
        pytest.param(
            {"stage_environment": "container", "agent_runtime": "opencode"},
            [*CONTAINER_ITEMS, "opencode", "agent-run-probe"],
            id="container-opencode",
        ),
        pytest.param({}, [*INLINE_ITEMS, "agent-run-probe"], id="inline-no-agent-user"),
        pytest.param(
            {"agent_runtime": "opencode"},
            [*INLINE_ITEMS, "opencode", "agent-run-probe"],
            id="inline-opencode",
        ),
    ],
)
def test_the_extras_are_chosen_by_the_stage_environment_in_the_operator_guides_order(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    agent_home: Path,
    versioned_podman: Podman,
    listing_zfs: Zfs,
    environment: dict[str, str],
    fields: dict[str, object],
    names: list[str],
) -> None:
    settings = _settings(tmp_path, agent_home, versioned_podman, listing_zfs, fields)

    extras = machine_extras(boundaries, settings, environment)

    assert [check().name for check in extras] == names


def test_the_container_items_run_the_podman_and_zfs_the_settings_name(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    agent_home: Path,
    versioned_podman: Podman,
    listing_zfs: Zfs,
    environment: dict[str, str],
) -> None:
    settings = _settings(
        tmp_path, agent_home, versioned_podman, listing_zfs, {"stage_environment": "container"}
    )

    podman_item = machine_item(boundaries, settings, environment, "podman")
    versioned_podman.plan(PodmanPlan(exit_status=1))
    image_item = machine_item(boundaries, settings, environment, "stage-image")
    dataset_item = machine_item(boundaries, settings, environment, "dataset")

    assert podman_item.passed
    assert podman_item.detail == PODMAN_VERSION
    assert not image_item.passed
    assert image_item.detail == f"the stage image {IMAGE} is not built; build it with podman build"
    assert dataset_item.passed
