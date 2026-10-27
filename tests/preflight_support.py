"""The preflight's rig, its recording stand-ins and its red main, shared by the preflight tests."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import timedelta
from pathlib import Path
from typing import override

import pytest

from factory.adapters.clock import ManualClock
from factory.adapters.git_cli import GitCli
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.preflight_stamp_file import JsonPreflightStampFile
from factory.application.boundaries import Boundaries
from factory.application.preflight import (
    MachineChecks,
    Preflight,
)
from factory.application.project_commands import ProjectCommands
from factory.application.stops import StopService
from factory.domain.checks import CheckResult
from factory.domain.git import CommitId
from factory.domain.settings import InstanceSettings
from factory.domain.stops import RepositoryStop
from git_support import CHECKOUT, install_agents, run_git
from human_clone import HumanClone

IMAGE = "build-7"


OTHER_IMAGE = "build-8"


MAKEFILE = "lint:\n\ttest ! -f BROKEN\nsync:\n\t@:\n"


TOOLS = {
    "git": "/usr/bin/git",
    "uv": "/usr/local/bin/uv",
}


ROLES = (
    "intake",
    "tester",
    "coder",
    "reviewer",
    "documenter",
    "smoke-tester",
    "acceptance-reviewer",
)


class RecordingWhich:
    """A `which` that answers from a dictionary and records every name it was asked."""

    def __init__(self, paths: dict[str, str]) -> None:
        self.paths = dict(paths)
        self.asked: list[str] = []

    def __call__(self, name: str) -> str | None:
        self.asked.append(name)
        return self.paths.get(name)


class RecordingCommands(ProjectCommands):
    """Records each command and its `time_limit`, then answers through `answer`."""

    def __init__(self, answer: Callable[[str, timedelta], CheckResult]) -> None:
        self.calls: list[tuple[str, timedelta]] = []
        self._answer = answer

    @override
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult:
        self.calls.append((command, time_limit))
        return self._answer(command, time_limit)


@dataclass
class Rig:
    """The preflight's collaborators on the test's checkout, fakes and state directory."""

    boundaries: Boundaries
    which: RecordingWhich
    commands: RecordingCommands
    stamps: JsonPreflightStampFile
    settings: InstanceSettings
    checkout: GitCli
    human: HumanClone
    clock: ManualClock
    directory: Path

    def preflight(self, image: str | None = IMAGE) -> Preflight:
        boundaries = replace(self.boundaries, project_commands=self.commands)
        checks = MachineChecks(boundaries, self.settings, self.which)
        return Preflight(boundaries, checks, self.stamps, StopService(boundaries), image)

    def stops(self) -> list[RepositoryStop]:
        return self.boundaries.health.read().stops

    def reasons(self) -> list[str]:
        return [stop.reason for stop in self.stops()]

    def main(self) -> CommitId:
        main = self.checkout.resolve("origin/main")
        assert main is not None
        return main

    def push_main(self, path: str, text: str) -> None:
        self.human.push_file("main", path, text)
        self.checkout.fetch()

    def remove_from_main(self, path: str) -> None:
        human = self.directory / "human"
        run_git(human, "rm", "-q", path)
        run_git(human, "commit", "-q", "-m", f"remove {path}")
        run_git(human, "push", "-q", "origin", "main")
        self.checkout.fetch()

    def raise_standing(self, stop: RepositoryStop) -> None:
        status = self.boundaries.health.read()
        self.boundaries.health.write(status.with_stop(stop))


@pytest.fixture
def rig(
    tmp_path: Path,
    boundaries: Boundaries,
    *,
    checkout: GitCli,
    human: HumanClone,
    agent_home: Path,
    clock: ManualClock,
) -> Rig:
    """Return a ready machine whose `origin/main` carries a `lint` that passes."""
    install_agents(agent_home, ROLES)
    settings = InstanceSettings.model_validate(
        {
            "repository_url": "/srv/project.git",
            "instance": "factory-1",
            "agent_home": agent_home,
            "pinned_agent_version": "fake",
        }
    )
    make = MakeProjectCommands(tmp_path / CHECKOUT)
    rig = Rig(
        boundaries=boundaries,
        which=RecordingWhich(TOOLS),
        commands=RecordingCommands(lambda command, limit: make.run(command, time_limit=limit)),
        stamps=JsonPreflightStampFile(tmp_path / "state" / "preflight-stamp.json"),
        settings=settings,
        checkout=checkout,
        human=human,
        clock=clock,
        directory=tmp_path,
    )
    rig.push_main("Makefile", MAKEFILE)
    return rig


@pytest.fixture
def red_main(rig: Rig) -> Rig:
    """Return the rig with a file `BROKEN` on `origin/main`, which makes its `lint` red."""
    rig.push_main("BROKEN", "red\n")
    return rig


CLEARED_LINE = "stop cleared main_branch_failing"


def fail_once(rig: Rig) -> Rig:
    """Probe the rig's red main once and return it, the stamp holding `main_failed`."""
    assert rig.preflight(IMAGE).run() == "main_branch_failing"
    stamp = rig.stamps.read()
    assert stamp is not None
    assert stamp.main_failed == rig.main()
    return rig


@pytest.fixture
def failed_once(red_main: Rig) -> Rig:
    """Return the rig after one probe of its red main, the stamp holding `main_failed`."""
    return fail_once(red_main)
