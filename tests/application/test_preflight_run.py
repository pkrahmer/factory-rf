"""The preflight's run: the machine items keyed to the image, the probe of the main branch."""

import shutil
from collections import Counter
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
    PROBE_COMMAND,
    PROBE_TIME_LIMIT,
    MachineChecks,
    Preflight,
)
from factory.application.project_commands import ProjectCommands
from factory.application.stops import StopService
from factory.domain.checks import CheckResult
from factory.domain.errors import ProjectCommandError
from factory.domain.git import CommitId, GitOptions
from factory.domain.preflight import PreflightStamp
from factory.domain.settings import InstanceSettings
from factory.domain.stops import RepositoryStop
from git_support import CHECKOUT, TEST_IDENTITY, clone, install_agents, run_git
from human_clone import HumanClone

IMAGE = "build-7"
OTHER_IMAGE = "build-8"
MAKEFILE = "lint:\n\ttest ! -f BROKEN\nsync:\n\t@:\n"
TOOLS = {
    "git": "/usr/bin/git",
    "uv": "/usr/local/bin/uv",
    "make": "/usr/bin/make",
    "claude": "/usr/local/bin/claude",
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
WORK_ITEM_BRANCH = "work-item/F0001-S0001"
ONCE_EACH = Counter(list(TOOLS))


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


def _answering(result: CheckResult) -> Callable[[str, timedelta], CheckResult]:
    return lambda _command, _limit: result


def _raising(error: ProjectCommandError) -> Callable[[str, timedelta], CheckResult]:
    def answer(_command: str, _limit: timedelta) -> CheckResult:
        raise error

    return answer


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


def test_a_red_lint_on_a_work_items_branch_does_not_fail_and_the_probe_ends_on_main(
    rig: Rig, tmp_path: Path
) -> None:
    rig.checkout.checkout(WORK_ITEM_BRANCH, start_point="origin/main")
    (tmp_path / CHECKOUT / "BROKEN").write_text("red\n", encoding="utf-8")
    rig.checkout.commit("break the branch")
    branch_lint = MakeProjectCommands(tmp_path / CHECKOUT).run("lint", time_limit=PROBE_TIME_LIMIT)
    assert not branch_lint.passed

    assert rig.preflight().run() is None

    status = rig.checkout.status()
    assert status.branch == "main"
    assert status.head == rig.main()


def test_a_red_main_is_one_repository_stop_naming_the_commit_and_the_last_line(
    red_main: Rig, tmp_path: Path
) -> None:
    reason = red_main.preflight().run()

    last_line = (
        MakeProjectCommands(tmp_path / CHECKOUT).run("lint", time_limit=PROBE_TIME_LIMIT).last_line
    )
    assert reason == "main_branch_failing"
    stops = red_main.stops()
    assert len(stops) == 1
    assert stops[0].scope == "repository"
    assert stops[0].reason == "main_branch_failing"
    assert stops[0].detail == f"lint is red on main at {red_main.main()[:12]}: {last_line}"


def test_a_fix_pushed_to_main_clears_the_stop_of_the_red_main(red_main: Rig) -> None:
    assert red_main.preflight().run() == "main_branch_failing"
    red_main.remove_from_main("BROKEN")

    assert red_main.preflight().run() is None
    assert "main_branch_failing" not in red_main.reasons()


def test_a_failed_machine_item_is_a_machine_stop_and_no_lint_runs(rig: Rig) -> None:
    del rig.which.paths["make"]

    reason = rig.preflight().run()

    assert reason == "preflight_failed"
    stops = rig.stops()
    assert len(stops) == 1
    assert stops[0].scope == "machine"
    assert stops[0].reason == "preflight_failed"
    assert "tool:make" in stops[0].detail
    assert rig.commands.calls == []


def test_a_probe_that_cannot_start_is_a_machine_stop_and_leaves_the_stamp(rig: Rig) -> None:
    before = PreflightStamp(image=IMAGE, main_probed="a" * 40)
    rig.stamps.write(before)
    rig.commands = RecordingCommands(_raising(ProjectCommandError("lint", "make not found")))

    reason = rig.preflight().run()

    assert reason == "preflight_failed"
    stops = rig.stops()
    assert len(stops) == 1
    assert stops[0].scope == "machine"
    assert stops[0].reason == "preflight_failed"
    assert stops[0].detail == (
        "the probe on main could not run: project command lint failed: make not found"
    )
    assert rig.stamps.read() == before


def test_a_probe_that_reaches_its_time_limit_is_the_stop_of_a_failing_main(rig: Rig) -> None:
    timed_out = CheckResult(
        command="lint",
        status="time_limit",
        exit_status=None,
        duration=PROBE_TIME_LIMIT,
        last_line="",
        output_tail="",
    )
    rig.commands = RecordingCommands(_answering(timed_out))

    reason = rig.preflight().run()

    assert reason == "main_branch_failing"
    stops = [stop for stop in rig.stops() if stop.reason == "main_branch_failing"]
    assert len(stops) == 1
    assert stops[0].detail == f"lint reached its time_limit on main at {rig.main()[:12]}"


def test_an_unchanged_image_runs_the_machine_items_once_however_much_time_passes(
    rig: Rig,
) -> None:
    assert rig.preflight().run() is None
    rig.clock.advance(timedelta(days=90))

    assert rig.preflight().run() is None
    assert Counter(rig.which.asked) == ONCE_EACH


def test_a_new_image_runs_the_machine_items_again_and_is_stamped(rig: Rig) -> None:
    assert rig.preflight(IMAGE).run() is None

    assert rig.preflight(OTHER_IMAGE).run() is None
    assert Counter(rig.which.asked) == ONCE_EACH + ONCE_EACH
    stamp = rig.stamps.read()
    assert stamp is not None
    assert stamp.image == OTHER_IMAGE


def test_a_new_image_probes_the_unmoved_main_again(rig: Rig) -> None:
    assert rig.preflight(IMAGE).run() is None

    assert rig.preflight(OTHER_IMAGE).run() is None
    assert [command for command, _limit in rig.commands.calls] == ["lint", "lint"]


def test_without_an_image_identity_the_machine_items_run_every_time(rig: Rig) -> None:
    assert rig.preflight(None).run() is None

    assert rig.preflight(None).run() is None
    assert Counter(rig.which.asked) == ONCE_EACH + ONCE_EACH


def test_a_failed_machine_report_writes_no_stamp_and_its_stop_goes_once_they_pass(
    rig: Rig,
) -> None:
    del rig.which.paths["make"]
    assert rig.preflight().run() == "preflight_failed"
    assert rig.stamps.read() is None
    rig.which.paths["make"] = TOOLS["make"]

    assert rig.preflight().run() is None
    assert rig.which.asked.count("make") == 2
    assert "preflight_failed" not in rig.reasons()


def test_a_main_that_passed_is_probed_again_only_when_it_moves(rig: Rig) -> None:
    assert rig.preflight().run() is None
    assert rig.preflight().run() is None
    assert len(rig.commands.calls) == 1
    rig.push_main("README.md", "moved\n")

    assert rig.preflight().run() is None
    assert len(rig.commands.calls) == 2


def test_a_red_main_is_probed_once_and_its_stop_stays_the_first_ones(red_main: Rig) -> None:
    assert red_main.preflight().run() == "main_branch_failing"
    first = red_main.boundaries.health.read()
    red_main.clock.advance(timedelta(minutes=5))

    assert red_main.preflight().run() == "main_branch_failing"
    assert len(red_main.commands.calls) == 1
    assert red_main.boundaries.health.read() == first


def test_a_lost_stop_of_a_red_main_is_raised_again_without_probing(
    red_main: Rig, tmp_path: Path
) -> None:
    assert red_main.preflight().run() == "main_branch_failing"
    (tmp_path / "state" / "health.json").unlink()

    assert red_main.preflight().run() == "main_branch_failing"
    assert len(red_main.commands.calls) == 1
    stops = red_main.stops()
    assert [stop.reason for stop in stops] == ["main_branch_failing"]
    assert stops[0].detail == (f"lint is red on main at {red_main.main()[:12]} (probed earlier)")


def test_a_valid_stamp_clears_a_standing_preflight_stop(rig: Rig) -> None:
    assert rig.preflight().run() is None
    rig.raise_standing(
        RepositoryStop(
            scope="machine", reason="preflight_failed", detail="settings fault", at=rig.clock.now()
        )
    )

    assert rig.preflight().run() is None
    assert Counter(rig.which.asked) == ONCE_EACH
    assert rig.reasons() == []


def test_without_an_origin_main_no_lint_runs_and_the_preflight_passes(
    rig: Rig, tmp_path: Path
) -> None:
    run_git(tmp_path, "init", "-q", "--bare", "--initial-branch=main", "empty.git")
    directory = clone(tmp_path / "empty.git", tmp_path / "empty-checkout")
    rig.boundaries = replace(
        rig.boundaries,
        git=GitCli(directory, GitOptions(identity=TEST_IDENTITY)),
        checkout=directory,
    )

    assert rig.preflight().run() is None
    assert rig.commands.calls == []


def test_a_git_error_while_probing_is_a_machine_stop_and_leaves_the_stamp(
    rig: Rig, tmp_path: Path
) -> None:
    before = PreflightStamp(image=IMAGE, main_probed="a" * 40)
    rig.stamps.write(before)
    shutil.rmtree(tmp_path / CHECKOUT)

    reason = rig.preflight().run()

    assert reason == "preflight_failed"
    stops = rig.stops()
    assert len(stops) == 1
    assert stops[0].scope == "machine"
    assert stops[0].reason == "preflight_failed"
    assert stops[0].detail.startswith("the probe on main could not run")
    assert rig.stamps.read() == before


def test_a_red_main_also_clears_a_standing_preflight_stop(red_main: Rig) -> None:
    red_main.raise_standing(
        RepositoryStop(
            scope="machine",
            reason="preflight_failed",
            detail="settings fault",
            at=red_main.clock.now(),
        )
    )

    assert red_main.preflight().run() == "main_branch_failing"
    assert red_main.reasons() == ["main_branch_failing"]


def test_the_probe_runs_lint_with_a_time_limit_of_ten_minutes(rig: Rig) -> None:
    passed = CheckResult(
        command="lint",
        status="passed",
        exit_status=0,
        duration=timedelta(seconds=1),
        last_line="",
        output_tail="",
    )
    rig.commands = RecordingCommands(_answering(passed))

    assert rig.preflight().run() is None
    assert rig.commands.calls == [("lint", timedelta(minutes=10))]
    assert PROBE_COMMAND == "lint"
    assert timedelta(minutes=10) == PROBE_TIME_LIMIT


def test_a_main_probed_before_is_not_probed_again_and_its_stale_stop_goes(rig: Rig) -> None:
    rig.stamps.write(PreflightStamp(image=IMAGE, main_probed=rig.main()))
    rig.raise_standing(
        RepositoryStop(
            scope="repository",
            reason="main_branch_failing",
            detail="written by the test",
            at=rig.clock.now(),
        )
    )

    assert rig.preflight().run() is None
    assert rig.commands.calls == []
    assert "main_branch_failing" not in rig.reasons()
