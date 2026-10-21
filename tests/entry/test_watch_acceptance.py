"""The watcher's command line shows a due acceptance as its event and in the board's column."""

import io

import pytest

from factory.application.board import BoardReader
from factory.application.boundaries import Boundaries
from factory.entry.watch import run_watch
from git_support import PIPELINE_YAML
from human_clone import HumanClone
from stage_run_support import INSTANCE
from watch_support import push_complete

pytestmark = pytest.mark.usefixtures("installed_agents")


@pytest.fixture
def todo(human: HumanClone) -> None:
    """Push the due feature `F0002-todo`: its feature file and two archived stories."""
    push_complete(human)


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
