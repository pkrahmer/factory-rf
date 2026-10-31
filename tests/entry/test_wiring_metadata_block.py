"""The metadata-block item joins the preflight with the container profile `job` alone."""

from pathlib import Path

import pytest

from factory.application.boundaries import Boundaries
from factory.domain.containers import METADATA_PROBE_COMMAND, WORK
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import machine_extras
from podman_support import IMAGE, Podman
from wiring_support import CONTAINER_ITEMS, machine_item
from zfs_support import DATASET, Zfs


@pytest.fixture
def environment(tmp_path: Path) -> dict[str, str]:
    """The agent runs' environment."""
    return {"PATH": "/usr/bin", "HOME": str(tmp_path)}


def _settings(
    tmp_path: Path, agent_home: Path, podman: Podman, zfs: Zfs, fields: dict[str, object]
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
            "podman_executable": str(podman.path),
            "zfs_executable": str(zfs.path),
            **fields,
        }
    )


@pytest.mark.parametrize(
    ("fields", "names"),
    [
        pytest.param({}, [*CONTAINER_ITEMS, "agent-run-probe"], id="default"),
        pytest.param(
            {"container_profile": "rootless"},
            [*CONTAINER_ITEMS, "agent-run-probe"],
            id="rootless",
        ),
        pytest.param(
            {"container_profile": "job"},
            [*CONTAINER_ITEMS, "metadata-block", "agent-run-probe"],
            id="job",
        ),
    ],
)
def test_the_metadata_block_item_runs_after_the_stage_image_with_the_job_profile_alone(
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


def _value_of(words: list[str], option: str) -> str:
    return words[words.index(option) + 1]


def test_the_metadata_probe_runs_its_command_alone_for_30_seconds_in_work(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    agent_home: Path,
    versioned_podman: Podman,
    listing_zfs: Zfs,
    environment: dict[str, str],
) -> None:
    settings = _settings(
        tmp_path, agent_home, versioned_podman, listing_zfs, {"container_profile": "job"}
    )

    machine_item(boundaries, settings, environment, "metadata-block")

    [words] = [call.arguments for call in versioned_podman.calls() if "run" in call.arguments]
    assert words[words.index(IMAGE) + 1 :] == list(METADATA_PROBE_COMMAND)
    # The workspace is every run's own volume; the probe adds none.
    assert words.count("--volume") == 1
    assert "--env" not in words
    assert _value_of(words, "--timeout") == "30"
    assert _value_of(words, "--workdir") == WORK
