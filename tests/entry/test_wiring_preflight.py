"""The wiring of the preflight: its stamp in the state directory, its stop in the tick."""

from pathlib import Path

import pytest

from factory.adapters.preflight_stamp_file import JsonPreflightStampFile
from factory.application.boundaries import Boundaries
from factory.application.tick import TickOutcome
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_preflight, build_tick
from git_support import PIPELINE_YAML, install_agents
from human_clone import HumanClone
from wiring_support import every_tool, with_dataset

IMAGE = "build-7"


def _no_git(name: str) -> str | None:
    return None if name == "git" else f"/usr/bin/{name}"


@pytest.fixture
def settings(tmp_path: Path, remote: Path, agent_home: Path) -> InstanceSettings:
    """Return settings of a ready machine whose checkout and state lie in `tmp_path`."""
    return with_dataset(
        InstanceSettings(
            repository_url=str(remote),
            instance="factory-1",
            image=IMAGE,
            checkout=tmp_path / "instance-checkout",
            state_directory=tmp_path / "state",
            agent_home=agent_home,
            claude_executable=str(tmp_path / "no-claude"),
            pinned_agent_version="fake",
        ),
        tmp_path,
    )


@pytest.fixture
def ready(boundaries: Boundaries, *, human: HumanClone, agent_home: Path) -> Boundaries:
    """Return the boundaries with the agents installed and a passing `lint` on `main`."""
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    human.push_file("main", "Makefile", "lint:\n\ttrue\n")
    boundaries.git.fetch()
    return boundaries


def test_the_built_preflight_writes_its_stamp_in_the_state_directory(
    ready: Boundaries, settings: InstanceSettings
) -> None:
    preflight = build_preflight(ready, settings, every_tool)

    preflight.run()

    path = settings.state_directory / "preflight-stamp.json"
    assert path.is_file()
    stamp = JsonPreflightStampFile(path).read()
    assert stamp is not None
    assert stamp.image == settings.image


def test_the_built_tick_stops_at_a_failed_machine_item(
    ready: Boundaries, settings: InstanceSettings
) -> None:
    tick = build_tick(ready, settings, _no_git)

    outcome = tick.run()

    assert outcome == TickOutcome(stopped="preflight_failed")
    stops = ready.health.read().stops
    assert [(stop.scope, stop.reason) for stop in stops] == [("machine", "preflight_failed")]
