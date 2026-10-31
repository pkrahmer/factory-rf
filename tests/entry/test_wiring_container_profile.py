"""The wiring gives the podman adapter the instance's container profile."""

from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.podman_runs import PodmanRuns
from factory.domain.containers import JOB_PODMAN_OPTIONS
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from podman_support import IMAGE
from recording_stand_in_support import recording_stand_in
from wiring_support import CREDENTIAL
from zfs_support import DATASET


@pytest.mark.usefixtures("sudo_stand_in")
@pytest.mark.parametrize(
    ("profile", "global_options"),
    [
        pytest.param(None, [], id="unset"),
        pytest.param("job", list(JOB_PODMAN_OPTIONS), id="job"),
    ],
)
def test_the_container_adapter_gets_the_setting_s_profile(
    tmp_path: Path, profile: str | None, global_options: list[str]
) -> None:
    root = tmp_path.resolve()
    podman = recording_stand_in(tmp_path / "podman-bin")
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=root / "checkout",
        state_directory=root / "state",
        agent_home=root / "agents-home",
        dataset=DATASET,
        workspace=root / "work",
        stage_image=IMAGE,
        zfs_executable=str(recording_stand_in(tmp_path / "zfs-bin")),
        podman_executable=str(podman),
    )
    if profile is not None:
        settings = settings.model_copy(update={"container_profile": profile})

    containers = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService()).containers

    assert isinstance(containers, PodmanRuns)
    argv = containers.launch(
        ["true"],
        mounts=[],
        environment={},
        time_limit=timedelta(seconds=1),
        working_directory="/work",
    ).argv
    assert argv[1 : argv.index("run")] == global_options
    assert not set(JOB_PODMAN_OPTIONS) & set(argv[argv.index("run") :])
