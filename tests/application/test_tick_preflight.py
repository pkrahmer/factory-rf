"""The tick runs the preflight after the fetch, the load and the restore, before anything else."""

from collections.abc import Callable, Mapping
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.preflight_stamp_file import JsonPreflightStampFile
from factory.application.boundaries import Boundaries
from factory.application.dispatcher import Handler
from factory.application.handlers.run import RunHandler
from factory.application.preflight import MachineChecks, Preflight
from factory.application.stops import StopService
from factory.application.tick import IdleHandler, Tick, TickOutcome
from factory.domain.events import EventKind
from factory.domain.identifiers import branch_name
from factory.domain.pipeline_definition import PipelineDefinition
from factory.domain.settings import InstanceSettings
from git_support import CHECKOUT, PIPELINE_YAML, install_agents, remote_commit, run_git
from human_clone import HumanClone
from stage_run_support import INSTANCE
from wiring_support import every_tool

IMAGE = "build-7"
MAKEFILE = "lint:\n\ttest ! -f BROKEN\n"
BACKLOG_PATH = "factory/features/F0001-example/backlog/F0001-S0001-first.md"
BRANCH = branch_name("F0001-S0001")


def _no_git(name: str) -> str | None:
    return None if name == "git" else f"/usr/bin/{name}"


class Machine:
    """The tick's collaborators on the test's remote, checkout and fakes."""

    def __init__(
        self, boundaries: Boundaries, checkout: GitCli, human: HumanClone, directory: Path
    ) -> None:
        self.boundaries = boundaries
        self.checkout = checkout
        self.human = human
        self.directory = directory
        self.settings = InstanceSettings.model_validate(
            {
                "repository_url": "/srv/project.git",
                "instance": INSTANCE,
                "agent_home": directory / "agent-home",
                "state_directory": directory / "state",
                "pinned_agent_version": "fake",
                "image": IMAGE,
            }
        )

    def tick(self, which: Callable[[str], str | None] = every_tool) -> Tick:
        boundaries = self.boundaries
        checks = MachineChecks(boundaries, self.settings, which)
        stamps = JsonPreflightStampFile(self.directory / "state" / "preflight-stamp.json")
        preflight = Preflight(boundaries, checks, stamps, StopService(boundaries), IMAGE)

        def handlers(definition: PipelineDefinition) -> Mapping[EventKind, Handler]:
            return {
                "idle": IdleHandler(),
                "run": RunHandler(boundaries, INSTANCE, definition, {}),
            }

        return Tick(boundaries, INSTANCE, handlers, preflight=preflight)

    def reasons(self) -> list[str]:
        return [stop.reason for stop in self.boundaries.health.read().stops]

    def push_main(self, path: str, text: str) -> None:
        self.human.push_file("main", path, text)

    def remove_from_main(self, path: str) -> None:
        human = self.directory / "human"
        run_git(human, "rm", "-q", path)
        run_git(human, "commit", "-q", "-m", f"remove {path}")
        run_git(human, "push", "-q", "origin", "main")

    def log_lines(self) -> list[str]:
        log = self.directory / "state" / "factory.log"
        return log.read_text(encoding="utf-8").splitlines() if log.exists() else []


@pytest.fixture
def machine(
    tmp_path: Path,
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    human: HumanClone,
    agent_home: Path,
) -> Machine:
    """Return a ready machine whose `origin/main` carries a `lint` that passes, agents installed."""
    install_agents(agent_home, boundaries.pipeline_reader.parse(PIPELINE_YAML).roles)
    machine = Machine(boundaries, checkout, human, tmp_path)
    machine.push_main("Makefile", MAKEFILE)
    checkout.fetch()
    return machine


@pytest.fixture
def red_main(machine: Machine) -> Machine:
    """Return the machine with a file `BROKEN` on `origin/main`, which makes its `lint` red."""
    machine.push_main("BROKEN", "red\n")
    return machine


def test_a_fix_pushed_after_the_clone_is_fetched_before_the_preflight(machine: Machine) -> None:
    machine.push_main("BROKEN", "red\n")
    machine.checkout.fetch()
    machine.remove_from_main("BROKEN")

    outcome = machine.tick().run()

    assert outcome.stopped is None
    assert outcome.event is not None
    assert "main_branch_failing" not in machine.reasons()


def test_a_break_pushed_after_the_clone_is_fetched_and_stops_the_tick(machine: Machine) -> None:
    machine.push_main("BROKEN", "red\n")

    outcome = machine.tick().run()

    assert outcome == TickOutcome(stopped="main_branch_failing")
    assert "main_branch_failing" in machine.reasons()


def test_a_tick_the_preflight_stops_runs_no_agent_and_dispatches_nothing(
    red_main: Machine, agent_runtime: FakeAgentRuntime, hosting: FakeHostingService
) -> None:
    red_main.human.start(BACKLOG_PATH)

    outcome = red_main.tick().run()

    assert outcome.stopped == "main_branch_failing"
    assert outcome.event is None
    assert agent_runtime.requests() == []
    assert hosting.pull_requests() == []


def test_a_tick_the_preflight_stops_leaves_a_stale_branch_on_the_remote(
    red_main: Machine, remote: Path
) -> None:
    red_main.human.push_file(BRANCH, "marker.txt", "x\n")
    before = remote_commit(remote, BRANCH)
    assert before is not None

    outcome = red_main.tick().run()

    assert outcome == TickOutcome(stopped="main_branch_failing")
    assert remote_commit(remote, BRANCH) == before


def test_an_invalid_definition_stops_the_tick_before_the_preflight(machine: Machine) -> None:
    machine.push_main("factory/pipeline.yml", "contract: [\n")

    outcome = machine.tick(_no_git).run()

    assert outcome == TickOutcome(stopped="pipeline_definition_invalid")
    assert "preflight_failed" not in machine.reasons()


def test_the_checkout_is_restored_before_the_preflight_stops_the_tick(
    red_main: Machine, tmp_path: Path
) -> None:
    (tmp_path / CHECKOUT / "notes.txt").write_text("left behind\n", encoding="utf-8")

    outcome = red_main.tick().run()

    assert outcome == TickOutcome(stopped="main_branch_failing")
    assert any(
        line.endswith(" discarded uncommitted changes: notes.txt") for line in red_main.log_lines()
    )
