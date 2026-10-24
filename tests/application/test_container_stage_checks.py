"""A whole container stage: the agent on the dataset, the take, the checks in a check container."""

from dataclasses import dataclass
from pathlib import Path

import pytest

from container_support import (
    FIVE_MINUTES,
    INSIDE,
    NOTES,
    Dataset,
    assert_taken_and_pushed,
    whole_stage,
)
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.make_commands import ContainerMakeCommands
from factory.application.boundaries import Boundaries
from factory.application.stage import StageReport
from factory.application.stage_environment import ContainerEnvironment
from factory.domain.git import CommitId
from git_support import write_files
from human_clone import HumanClone
from stage_run_support import BRANCH, branch_head
from take_support import AGENT_TEXT

STRAY = "stray.txt"
LEFTOVER = "leftover"


@dataclass(frozen=True)
class Staged:
    """The dataset after one whole stage, the stage's report and the commit it started on."""

    dataset: Dataset
    report: StageReport
    stage_start: CommitId


@pytest.fixture
def staged(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    tmp_path: Path,
) -> Staged:
    """Run the story's `tests` stage on the dataset, its checks in check containers."""
    dataset, report = whole_stage(
        boundaries,
        human=human,
        agent_home=agent_home,
        agent_runtime=agent_runtime,
        tmp_path=tmp_path,
        project_commands=lambda given: ContainerMakeCommands(
            given.snapshots, given.containers, boundaries.git, checkout=boundaries.checkout
        ),
    )

    # The claim is the stage's first commit on the branch; the result commit follows it.
    stage_start = boundaries.git.resolve(f"{report.commit}^")
    assert stage_start is not None
    return Staged(dataset=dataset, report=report, stage_start=stage_start)


def test_a_whole_container_stage_pushes_the_taken_work_and_leaves_the_host_clean(
    boundaries: Boundaries, remote: Path, staged: Staged
) -> None:
    assert_taken_and_pushed(boundaries, remote, staged.report)


def test_the_sync_and_each_check_run_in_their_containers_on_the_taken_result(
    staged: Staged,
) -> None:
    calls = staged.dataset.containers.calls

    assert [call.command[-1] for call in calls] == [staged.stage_start, "lint", "test"]
    checkout = staged.dataset.workspace / "checkout"
    assert (checkout / INSIDE).read_text(encoding="utf-8") == AGENT_TEXT
    assert not (checkout / NOTES).exists()


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        pytest.param(f"checkout/{STRAY}", None, id="stray-file-gone"),
        pytest.param(f"home/{LEFTOVER}", None, id="home-leftover-gone"),
        pytest.param(f"checkout/{INSIDE}", AGENT_TEXT, id="taken-file-kept"),
    ],
)
def test_the_next_prepare_starts_from_the_pushed_result_and_nothing_else(
    remote: Path, staged: Staged, *, path: str, expected: str | None
) -> None:
    dataset = staged.dataset
    write_files(dataset.workspace / "checkout", {STRAY: "left\n"})
    write_files(dataset.workspace / "home", {LEFTOVER: "left\n"})
    environment = ContainerEnvironment(dataset.boundaries, dataset.snapshots, dataset.containers)

    environment.prepare(branch_head(remote), BRANCH, sync_time_limit=FIVE_MINUTES)

    target = dataset.workspace / path
    if expected is None:
        assert not target.exists()
    else:
        assert target.read_text(encoding="utf-8") == expected
