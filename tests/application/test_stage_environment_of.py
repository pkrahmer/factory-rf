"""The boundaries' environment is the container one, on their snapshots and containers."""

from pathlib import Path

from container_support import FIVE_MINUTES, container_dataset, push_main, sync_makefile
from factory.application.boundaries import Boundaries
from factory.application.stage_environment import ContainerEnvironment, stage_environment_of
from git_support import install_agents
from human_clone import HumanClone

STRAY = "stray.txt"


def test_the_environment_of_the_boundaries_is_the_container_one(
    boundaries: Boundaries, human: HumanClone, agent_home: Path, tmp_path: Path
) -> None:
    dataset = container_dataset(boundaries, tmp_path)
    commit = push_main(boundaries, human, {"Makefile": sync_makefile()})
    install_agents(agent_home, ["tester"])
    (dataset.workspace / STRAY).write_text("left by an earlier stage\n", encoding="utf-8")
    environment = stage_environment_of(boundaries)

    environment.prepare(commit, "main", sync_time_limit=FIVE_MINUTES)

    assert isinstance(environment, ContainerEnvironment)
    assert not (dataset.workspace / STRAY).exists()
    assert len(dataset.containers.calls) == 1
