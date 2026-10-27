"""The preflight's run: the machine items keyed to the image, the probe of the main branch."""

import shutil
from collections import Counter
from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import preflight_support
from factory.adapters.git_cli import GitCli
from factory.adapters.make_commands import MakeProjectCommands
from factory.application.preflight import (
    PROBE_COMMAND,
    PROBE_TIME_LIMIT,
)
from factory.domain.checks import CheckResult
from factory.domain.errors import ProjectCommandError
from factory.domain.git import GitOptions
from factory.domain.preflight import PreflightStamp
from factory.domain.stops import RepositoryStop
from git_support import CHECKOUT, TEST_IDENTITY, clone, run_git
from preflight_support import (
    IMAGE,
    OTHER_IMAGE,
    TOOLS,
    RecordingCommands,
    Rig,
)

red_main = preflight_support.red_main
rig = preflight_support.rig

WORK_ITEM_BRANCH = "work-item/F0001-S0001"
ONCE_EACH = Counter(list(TOOLS))


def _answering(result: CheckResult) -> Callable[[str, timedelta], CheckResult]:
    return lambda _command, _limit: result


def _raising(error: ProjectCommandError) -> Callable[[str, timedelta], CheckResult]:
    def answer(_command: str, _limit: timedelta) -> CheckResult:
        raise error

    return answer


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
    del rig.which.paths["uv"]

    reason = rig.preflight().run()

    assert reason == "preflight_failed"
    stops = rig.stops()
    assert len(stops) == 1
    assert stops[0].scope == "machine"
    assert stops[0].reason == "preflight_failed"
    assert "tool:uv" in stops[0].detail
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
    del rig.which.paths["uv"]
    assert rig.preflight().run() == "preflight_failed"
    assert rig.stamps.read() is None
    rig.which.paths["uv"] = TOOLS["uv"]

    assert rig.preflight().run() is None
    assert rig.which.asked.count("uv") == 2
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
