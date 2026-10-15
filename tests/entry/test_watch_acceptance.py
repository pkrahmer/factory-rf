"""The watcher's command line shows a due acceptance as its event and in the board's column."""

import io
from pathlib import Path

import pytest

from factory.application.board import BoardReader
from factory.application.boundaries import Boundaries
from factory.entry.watch import run_watch
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone

INSTANCE = "factory-1"
TODO = "factory/features/F0002-todo"


@pytest.fixture(autouse=True)
def _agents(agent_home: Path, boundaries: Boundaries) -> None:
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)


@pytest.fixture
def todo(human: HumanClone) -> None:
    """Push the due feature `F0002-todo`: its feature file and two archived stories."""
    human.push_file("main", f"{TODO}/feature.md", "# Todo service\n")
    human.push_file("main", f"{TODO}/done/F0002-S0001-a.md", "# A\n")
    human.push_file("main", f"{TODO}/done/F0002-S0002-b.md", "# B\n")


def _watch(boundaries: Boundaries) -> str:
    boundaries.git.fetch()
    out, err = io.StringIO(), io.StringIO()
    status = run_watch(boundaries, INSTANCE, out, err)
    assert (status, err.getvalue()) == (0, "")
    return out.getvalue()


def _feature_lines(out: str) -> list[str]:
    return [line for line in out.splitlines() if line.startswith(("F0001  ", "F0002  "))]


@pytest.mark.usefixtures("todo")
def test_run_watch_shows_a_due_acceptance_as_its_event_and_in_the_board(
    boundaries: Boundaries,
) -> None:
    out = _watch(boundaries)

    lines = out.splitlines()
    assert lines[0] == "event: acceptance_due:F0002  acceptance of F0002 is due"
    assert "F0002  Todo service  backlog=0  in-progress=0  done=2  acceptance=due" in lines
    [example] = [line for line in lines if line.startswith("F0001  ")]
    assert example.endswith("  acceptance=incomplete")


@pytest.mark.usefixtures("todo")
def test_without_an_acceptance_stage_the_board_has_no_acceptance_status(
    boundaries: Boundaries, human: HumanClone
) -> None:
    without = PIPELINE_YAML.replace("acceptance_stage: acceptance\n", "")
    human.push_file("main", "factory/pipeline.yml", without)
    boundaries.git.fetch()

    view = BoardReader(boundaries).read(boundaries.pipeline_reader.parse(without))
    out = _watch(boundaries)

    assert [row.acceptance for row in view.features] == [None, None]
    feature_lines = _feature_lines(out)
    assert len(feature_lines) == 2
    assert all(line.endswith("  acceptance=-") for line in feature_lines)
