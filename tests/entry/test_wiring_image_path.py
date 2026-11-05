"""The containers' `PATH` is the one the image in use configures: sync, check and agent."""

import sys
from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from agent_definition_support import COMPLETED
from container_extra_support import CHECK_LIMIT, COMMIT, env_words
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_images import FakeImages
from factory.adapters.podman_images import PodmanImages
from factory.application.boundaries import Boundaries
from factory.application.images import Images
from factory.application.stage_environment import stage_environment_of
from factory.domain.containers import SYSTEM_PATH
from factory.entry.wiring import agent_environment, build_boundaries, build_tick
from factory.hosting.adapters.fake_hosting import FakeHostingService
from factory.shared.domain.settings import InstanceSettings
from git_support import CHECKOUT, PIPELINE_YAML, install_agents
from human_clone import HumanClone
from podman_support import IMAGE
from probe_support import COMPLETED as PROBE
from recording_stand_in_support import recorded_calls, recording_stand_in
from stage_run_support import BACKLOG_PATH, STORY
from wiring_support import CREDENTIAL, every_tool, with_dataset
from zfs_support import DATASET

JDK_PATH = "/opt/jdk/bin:/usr/local/bin:/usr/bin:/bin"


@pytest.mark.usefixtures("checkout", "sudo_stand_in")
@pytest.mark.parametrize(
    ("images_of", "expected"),
    [
        pytest.param(
            lambda _podman: FakeImages(paths={IMAGE: JDK_PATH}), JDK_PATH, id="image-path"
        ),
        pytest.param(lambda _podman: FakeImages(), SYSTEM_PATH, id="no-image-path"),
        # The stand-in `podman` prints no JSON for `image inspect`, so `path` raises.
        pytest.param(lambda podman: PodmanImages(str(podman)), SYSTEM_PATH, id="path-raises"),
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


def test_the_tick_gives_the_agent_run_the_path_of_the_image_in_use(
    boundaries: Boundaries,
    *,
    remote: Path,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
) -> None:
    settings = with_dataset(
        InstanceSettings(
            repository_url=str(remote),
            instance="factory-1",
            checkout=tmp_path / "instance-checkout",
            state_directory=tmp_path / "state",
            agent_home=agent_home,
            claude_executable=str(tmp_path / "no-claude"),
        ),
        tmp_path,
    )
    built = build_boundaries(
        settings,
        CREDENTIAL,
        hosting=FakeHostingService(),
        images=FakeImages(paths={IMAGE: JDK_PATH}),
    )
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    human.push_file("main", "Makefile", "lint:\n\ttrue\nsync:\n\t@:\n")
    human.push_file("main", BACKLOG_PATH, STORY)
    human.start(BACKLOG_PATH)
    token_file = tmp_path / "hosting-token"
    token_file.write_text("example-value\n", encoding="utf-8")
    token_file.chmod(0o600)
    agent_runtime.queue(ScriptedRun(result=PROBE))
    agent_runtime.queue(ScriptedRun(result=COMPLETED))
    ready = settings.model_copy(update={"pinned_agent_version": "fake", "token_file": token_file})
    tick = build_tick(replace(boundaries, image_path=built.image_path), ready, every_tool)

    tick.run()

    request = agent_runtime.requests()[-1]
    assert request.environment["PATH"] == f"{Path(sys.executable).parent}:{JDK_PATH}"
