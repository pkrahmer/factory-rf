"""The wiring gives the podman adapter the settings' instance for its label."""

from pathlib import Path

import pytest

from factory.entry.wiring import build_boundaries
from factory.hosting.adapters.fake_hosting import FakeHostingService
from factory.machine.adapters.podman_runs import PodmanRuns
from factory.shared.domain.settings import InstanceSettings
from podman_support import IMAGE, launch_words
from recording_stand_in_support import recording_stand_in
from wiring_support import CREDENTIAL
from zfs_support import DATASET


@pytest.mark.usefixtures("sudo_stand_in")
@pytest.mark.parametrize("instance", ["factory-1", "night"])
def test_the_container_adapter_labels_its_containers_with_the_setting_s_instance(
    tmp_path: Path, instance: str
) -> None:
    root = tmp_path.resolve()
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance=instance,
        checkout=root / "checkout",
        state_directory=root / "state",
        agent_home=root / "agents-home",
        dataset=DATASET,
        workspace=root / "work",
        stage_image=IMAGE,
        zfs_executable=str(recording_stand_in(tmp_path / "zfs-bin")),
        podman_executable=str(recording_stand_in(tmp_path / "podman-bin")),
    )

    containers = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService()).containers

    assert isinstance(containers, PodmanRuns)
    argv = launch_words(containers, ["true"], [])
    assert "--label" in argv
    assert argv[argv.index("--label") + 1] == f"factory.instance={instance}"
