"""The extra machine items of a container instance, in order, run on the adapters it builds."""

from pathlib import Path

import pytest

from factory.application.boundaries import Boundaries
from factory.entry.wiring import machine_extras
from podman_support import IMAGE, Podman, PodmanPlan
from wiring_support import CONTAINER_ITEMS, PODMAN_VERSION, machine_item, profile_settings
from zfs_support import Zfs


@pytest.mark.parametrize(
    ("fields", "names"),
    [
        pytest.param({}, [*CONTAINER_ITEMS, "agent-run-probe"], id="container"),
        pytest.param(
            {"agent_runtime": "opencode"},
            [*CONTAINER_ITEMS, "opencode", "agent-run-probe"],
            id="container-opencode",
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
    run_environment: dict[str, str],
    fields: dict[str, object],
    names: list[str],
) -> None:
    settings = profile_settings(tmp_path, agent_home, versioned_podman, listing_zfs, fields)

    extras = machine_extras(boundaries, settings, run_environment)

    assert [check().name for check in extras] == names


def test_the_container_items_run_the_podman_and_zfs_the_settings_name(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    agent_home: Path,
    versioned_podman: Podman,
    listing_zfs: Zfs,
    run_environment: dict[str, str],
) -> None:
    settings = profile_settings(tmp_path, agent_home, versioned_podman, listing_zfs, {})

    podman_item = machine_item(boundaries, settings, run_environment, "podman")
    versioned_podman.plan(PodmanPlan(exit_status=1))
    image_item = machine_item(boundaries, settings, run_environment, "stage-image")
    dataset_item = machine_item(boundaries, settings, run_environment, "dataset")

    assert podman_item.passed
    assert podman_item.detail == PODMAN_VERSION
    assert not image_item.passed
    assert image_item.detail == f"the stage image {IMAGE} is not built; build it with podman build"
    assert dataset_item.passed
