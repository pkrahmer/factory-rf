"""The containers' `PATH` is the one the image in use configures: sync, check and agent."""

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from container_extra_support import CHECK_LIMIT, COMMIT, env_words
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.fake_images import FakeImages
from factory.adapters.podman_images import PodmanImages
from factory.application.images import Images
from factory.application.stage_environment import stage_environment_of
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import agent_environment, build_boundaries
from git_support import CHECKOUT
from podman_support import IMAGE
from recording_stand_in_support import recorded_calls, recording_stand_in
from wiring_support import CREDENTIAL
from zfs_support import DATASET

JDK_PATH = "/opt/jdk/bin:/usr/local/bin:/usr/bin:/bin"
BASE_PATH = "/usr/local/bin:/usr/bin:/bin"


@pytest.mark.usefixtures("checkout", "sudo_stand_in")
@pytest.mark.parametrize(
    ("images_of", "expected"),
    [
        pytest.param(
            lambda _podman: FakeImages(paths={IMAGE: JDK_PATH}), JDK_PATH, id="image-path"
        ),
        pytest.param(lambda _podman: FakeImages(), BASE_PATH, id="no-image-path"),
        # The stand-in `podman` prints no JSON for `image inspect`, so `path` raises.
        pytest.param(lambda podman: PodmanImages(str(podman)), BASE_PATH, id="path-raises"),
    ],
)
def test_the_sync_the_check_and_the_agent_take_the_path_of_the_image_in_use(
    tmp_path: Path, agent_home: Path, images_of: Callable[[Path], Images], expected: str
) -> None:
    zfs = recording_stand_in(tmp_path / "zfs-bin")
    podman = recording_stand_in(tmp_path / "podman-bin")
    workspace = tmp_path / "work"
    workspace.mkdir()
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=tmp_path / CHECKOUT,
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        dataset=DATASET,
        workspace=workspace,
        stage_image=IMAGE,
        zfs_executable=str(zfs),
        podman_executable=str(podman),
    )
    boundaries = build_boundaries(
        settings, CREDENTIAL, hosting=FakeHostingService(), images=images_of(podman)
    )
    scripts = tmp_path / "scripts"

    stage_environment_of(boundaries).prepare(COMMIT, "main", sync_time_limit=timedelta(minutes=5))
    boundaries.project_commands.run("check", time_limit=CHECK_LIMIT)
    agent = agent_environment(scripts, tmp_path / "home", boundaries.image_path)

    [sync, check] = [words for words in recorded_calls(podman) if words[:1] == ["run"]]
    assert boundaries.image_path == expected
    assert env_words(sync)["PATH"] == expected
    assert "factory-check" in check
    assert env_words(check)["PATH"] == expected
    assert agent["PATH"] == f"{scripts}:{expected}"
