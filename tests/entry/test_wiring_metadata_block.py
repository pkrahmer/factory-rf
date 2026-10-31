"""The metadata-block item joins the preflight with the container profile `job` alone."""

from pathlib import Path

import pytest

from command_words_support import value_after
from factory.application.boundaries import Boundaries
from factory.domain.containers import METADATA_PROBE_COMMAND, WORK
from factory.entry.wiring import machine_extras
from podman_support import Podman
from wiring_support import CONTAINER_ITEMS, after_image, machine_item, profile_settings
from zfs_support import Zfs


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
    run_environment: dict[str, str],
    fields: dict[str, object],
    names: list[str],
) -> None:
    settings = profile_settings(tmp_path, agent_home, versioned_podman, listing_zfs, fields)

    extras = machine_extras(boundaries, settings, run_environment)

    assert [check().name for check in extras] == names


def test_the_metadata_probe_runs_its_command_alone_for_30_seconds_in_work(
    boundaries: Boundaries,
    tmp_path: Path,
    *,
    agent_home: Path,
    versioned_podman: Podman,
    listing_zfs: Zfs,
    run_environment: dict[str, str],
) -> None:
    settings = profile_settings(
        tmp_path, agent_home, versioned_podman, listing_zfs, {"container_profile": "job"}
    )

    machine_item(boundaries, settings, run_environment, "metadata-block")

    # The job profile's global options come before `run`, so the call is the one that holds it.
    [words] = [call.arguments for call in versioned_podman.calls() if "run" in call.arguments]
    assert after_image(words) == list(METADATA_PROBE_COMMAND)
    # The workspace is every run's own volume; the probe adds none.
    assert words.count("--volume") == 1
    assert "--env" not in words
    assert value_after(words, "--timeout") == "30"
    assert value_after(words, "--workdir") == WORK
