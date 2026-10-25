"""The preflight's failed machine items and a stop of a red main that `main` has moved on from."""

import shutil
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

import preflight_support
from application import test_preflight_run
from application.test_preflight_run import IMAGE, OTHER_IMAGE, TOOLS, Rig
from factory.adapters.git_cli import GitCli
from factory.domain.git import GitOptions
from factory.domain.stops import RepositoryStop
from git_support import CHECKOUT, TEST_IDENTITY, clone, run_git
from log_support import log_lines
from preflight_support import CLEARED_LINE

rig = test_preflight_run.rig
red_main = test_preflight_run.red_main
failed_once = preflight_support.failed_once


def _failing_details(rig: Rig) -> list[str]:
    return [stop.detail for stop in rig.stops() if stop.reason == "main_branch_failing"]


def _push_fix(rig: Rig, _tmp_path: Path) -> None:
    rig.remove_from_main("BROKEN")


def _empty_remote(rig: Rig, tmp_path: Path) -> None:
    run_git(tmp_path, "init", "-q", "--bare", "--initial-branch=main", "empty.git")
    directory = clone(tmp_path / "empty.git", tmp_path / "empty-checkout")
    rig.boundaries = replace(
        rig.boundaries,
        git=GitCli(directory, GitOptions(identity=TEST_IDENTITY)),
        checkout=directory,
    )


@pytest.mark.parametrize(
    "move_main",
    [
        pytest.param(_push_fix, id="moved"),
        pytest.param(_empty_remote, id="gone"),
    ],
)
def test_a_failed_machine_clears_the_stop_of_a_main_that_moved_on(
    failed_once: Rig, tmp_path: Path, move_main: Callable[[Rig, Path], None]
) -> None:
    before = failed_once.stamps.read()
    move_main(failed_once, tmp_path)
    del failed_once.which.paths["uv"]

    assert failed_once.preflight(OTHER_IMAGE).run() == "preflight_failed"
    assert failed_once.reasons() == ["preflight_failed"]
    assert any(line.endswith(CLEARED_LINE) for line in log_lines(tmp_path))
    assert failed_once.stamps.read() == before


def test_a_failed_machine_keeps_the_stop_of_a_main_that_has_not_moved(failed_once: Rig) -> None:
    before = failed_once.stamps.read()
    earlier = _failing_details(failed_once)
    del failed_once.which.paths["uv"]

    assert failed_once.preflight(OTHER_IMAGE).run() == "preflight_failed"
    assert sorted(failed_once.reasons()) == ["main_branch_failing", "preflight_failed"]
    assert _failing_details(failed_once) == earlier
    assert failed_once.stamps.read() == before


def test_a_failed_machine_keeps_a_standing_stop_when_the_stamp_names_no_failed_main(
    rig: Rig,
) -> None:
    assert rig.preflight(IMAGE).run() is None
    rig.raise_standing(
        RepositoryStop(
            scope="repository",
            reason="main_branch_failing",
            detail="written by the test",
            at=rig.clock.now(),
        )
    )
    del rig.which.paths["uv"]

    assert rig.preflight(OTHER_IMAGE).run() == "preflight_failed"
    assert sorted(rig.reasons()) == ["main_branch_failing", "preflight_failed"]


def test_a_failed_machine_keeps_the_stop_when_git_cannot_resolve_main(
    failed_once: Rig, tmp_path: Path
) -> None:
    shutil.rmtree(tmp_path / CHECKOUT)
    del failed_once.which.paths["uv"]

    assert failed_once.preflight(OTHER_IMAGE).run() == "preflight_failed"
    assert "main_branch_failing" in failed_once.reasons()


def _push_unrelated(rig: Rig) -> None:
    rig.push_main("README.md", "moved\n")


def _remove_broken(rig: Rig) -> None:
    rig.remove_from_main("BROKEN")


@pytest.mark.parametrize(
    ("move_main", "expected"),
    [
        pytest.param(_remove_broken, None, id="green"),
        pytest.param(_push_unrelated, "main_branch_failing", id="red"),
    ],
)
def test_the_moved_main_is_probed_once_when_the_machine_passes_again(
    failed_once: Rig, move_main: Callable[[Rig], None], expected: str | None
) -> None:
    move_main(failed_once)
    del failed_once.which.paths["uv"]
    assert failed_once.preflight(OTHER_IMAGE).run() == "preflight_failed"
    failed_once.which.paths["uv"] = TOOLS["uv"]

    assert failed_once.preflight(OTHER_IMAGE).run() == expected
    assert [command for command, _limit in failed_once.commands.calls] == ["lint", "lint"]
    assert "preflight_failed" not in failed_once.reasons()
    details = _failing_details(failed_once)
    if expected is None:
        assert details == []
    else:
        assert len(details) == 1
        assert details[0].startswith(f"lint is red on main at {failed_once.main()[:12]}")
