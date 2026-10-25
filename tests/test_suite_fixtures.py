"""The suite's shared fixtures describe a container instance on the fakes."""

import subprocess  # noqa: S404
from pathlib import Path

from container_support import timing_lines
from factory.adapters.fake_containers import FakeContainerRuns
from factory.adapters.fake_snapshots import FakeSnapshots
from factory.application.boundaries import Boundaries
from factory.application.stage_environment import ContainerEnvironment, stage_environment_of
from factory.domain.identifiers import branch_name
from git_support import PIPELINE_YAML, clone
from proof_support import (
    PASSING_MAKEFILE,
    PASSING_TEST,
    SOURCE,
    World,
    completed,
    head_state,
    start_story,
)

FORBIDDEN = "forbidden.txt"
WRITES = {
    "intake": {},
    "tests": {"tests/test_example.py": PASSING_TEST},
    "doing": {"src/example.py": SOURCE},
}
LIMIT = 20


def test_the_boundaries_fixture_runs_its_stages_in_containers_on_the_fakes(
    boundaries: Boundaries, tmp_path: Path
) -> None:
    snapshots = boundaries.snapshots
    assert isinstance(snapshots, FakeSnapshots)
    assert snapshots.mount_point == tmp_path / "workspace"
    assert isinstance(boundaries.containers, FakeContainerRuns)
    assert isinstance(stage_environment_of(boundaries), ContainerEnvironment)

    snapshots.reset()


def test_the_remotes_makefile_has_a_silent_sync_that_succeeds(remote: Path, tmp_path: Path) -> None:
    work_tree = clone(remote, tmp_path / "clone")
    assert (work_tree / "Makefile").is_file()

    result = subprocess.run(  # noqa: S603, S607  (fixed command, no input)
        ["make", "-s", "sync"], cwd=work_tree, capture_output=True, text=True, check=False
    )

    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_a_story_walks_to_approval_in_the_world_on_the_container_fakes(world: World) -> None:
    world.human.push_file("main", "Makefile", PASSING_MAKEFILE)
    work_item = start_story(world)
    definition = world.boundaries.pipeline_reader.parse(PIPELINE_YAML)
    git = world.boundaries.git
    walked: list[str] = []
    for _ in range(LIMIT):
        git.fetch()
        if git.resolve(f"origin/{branch_name(work_item)}") is not None:
            state = head_state(world, work_item)
            if state.handed_over == "approval":
                break
            stage = state.stage
        else:
            stage = "intake"
        if stage not in walked:
            walked.append(stage)
        writes = {**WRITES.get(stage, {}), FORBIDDEN: "no role may write this\n"}
        world.agent_runtime.queue(completed(definition.stages[stage].next[0], writes=writes))
        world.tick.run()
    else:
        raise AssertionError(f"{work_item} did not reach approval in {LIMIT} ticks")

    assert walked == ["intake", "tests", "doing", "review", "docs", "smoke-test"]
    resets = [line for line in timing_lines(world.boundaries) if "stage environment: reset" in line]
    assert len(resets) >= len(walked)
    head = f"origin/{branch_name(work_item)}"
    assert git.show_file(head, "src/example.py") == SOURCE
    assert git.show_file(head, FORBIDDEN) is None
