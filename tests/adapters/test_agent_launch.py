"""The shared words of a run's start, its rules, its refusals and its resume share."""

from collections.abc import Sequence
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from confine_support import build_layout, run_request
from factory.adapters.agent_launch import (
    CLEANUP_SCRIPT,
    Launch,
    cleanup_argv,
    confined_argv,
    existing_devices,
    first_word,
    killed_at_limit,
    launch,
    line_starting,
    resume_budget,
    run_confinement,
    temporary_folder,
)
from factory.domain.confinement import WriteTarget

SUDO = "/usr/bin/sudo"
ARGV = ["claude", "-p", "x"]
ENVIRONMENT = {"HOME": "/home/agent", "PATH": "/bin"}
# Built from parts: the value is a word of the call, and no file is made in `/tmp`.
TEMPORARY_ROOT = Path("/", "tmp")
TEMPORARY = TEMPORARY_ROOT / "factory-run-r"
LIMIT = timedelta(seconds=30)


@pytest.mark.parametrize(
    ("os_user", "time_limit", "expected"),
    [
        pytest.param(
            None,
            timedelta(seconds=30),
            Launch(argv=ARGV, env=ENVIRONMENT, time_limit=timedelta(seconds=30)),
            id="without-user",
        ),
        pytest.param(
            "agent",
            timedelta(seconds=29.2),
            Launch(
                argv=[
                    *(SUDO, "-n", "-u", "agent", "--"),
                    *("timeout", "--signal=KILL", "30s"),
                    *("env", "-i", "HOME=/home/agent", "PATH=/bin"),
                    *ARGV,
                ],
                env={},
                time_limit=timedelta(seconds=59.2),
            ),
            id="with-user-rounded-up",
        ),
        pytest.param(
            "agent",
            timedelta(seconds=30),
            Launch(
                argv=[
                    *(SUDO, "-n", "-u", "agent", "--"),
                    *("timeout", "--signal=KILL", "30s"),
                    *("env", "-i", "HOME=/home/agent", "PATH=/bin"),
                    *ARGV,
                ],
                env={},
                time_limit=timedelta(seconds=60),
            ),
            id="with-user-whole-seconds",
        ),
    ],
)
def test_launch_runs_the_call_as_the_user_under_a_kill_timeout_with_its_environment_alone(
    os_user: str | None, time_limit: timedelta, expected: Launch
) -> None:
    started = launch(
        ARGV, ENVIRONMENT, os_user=os_user, sudo_executable=SUDO, time_limit=time_limit
    )

    assert started == expected


@pytest.mark.parametrize(
    ("confine_executable", "expected"),
    [
        pytest.param(None, ["claude"], id="without-wrapper"),
        pytest.param(
            "factory-confine",
            ["factory-confine", "--rules", "/state/runs/confine-r.json", "--", "claude"],
            id="with-wrapper",
        ),
    ],
)
def test_confined_argv_puts_the_wrapper_and_its_rules_before_the_call(
    confine_executable: str | None, expected: list[str]
) -> None:
    argv = confined_argv(["claude"], confine_executable, Path("/state/runs/confine-r.json"))

    assert argv == expected


@pytest.mark.parametrize(
    ("os_user", "prefix"),
    [
        pytest.param(None, [], id="without-user"),
        pytest.param("agent", [SUDO, "-n", "-u", "agent", "--"], id="with-user"),
    ],
)
def test_cleanup_argv_removes_the_temporary_folder_as_the_runs_user(
    os_user: str | None, prefix: list[str]
) -> None:
    argv = cleanup_argv("/bin/sh", TEMPORARY, os_user=os_user, sudo_executable=SUDO)

    assert argv == [*prefix, "/bin/sh", "-c", CLEANUP_SCRIPT, "factory-cleanup", str(TEMPORARY)]


def test_temporary_folder_is_named_after_the_run_under_the_root() -> None:
    folder = temporary_folder(TEMPORARY_ROOT, "r")

    assert folder == TEMPORARY


def test_existing_devices_holds_the_existing_folders_then_the_existing_files(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "device-folder"
    folder.mkdir()
    file = tmp_path / "device-file"
    file.write_text("", encoding="utf-8")

    devices = existing_devices(
        [str(tmp_path / "missing-folder"), str(folder)],
        [str(file), str(tmp_path / "missing-file")],
    )

    assert devices == [
        WriteTarget(path=folder, kind="folder"),
        WriteTarget(path=file, kind="file"),
    ]


@pytest.mark.parametrize(
    ("runtime_folders", "with_home", "with_guard", "expected_folders"),
    [
        pytest.param([".claude"], True, True, [".claude"], id="claude-folder"),
        pytest.param(
            [".local/share/opencode", ".cache/opencode"],
            True,
            True,
            [".local/share/opencode", ".cache/opencode"],
            id="opencode-folders-in-order",
        ),
        pytest.param(
            [".local/share/opencode", ".cache/opencode"], False, True, [], id="without-home"
        ),
        pytest.param([".claude"], True, False, [".claude"], id="without-guard"),
    ],
)
def test_run_confinement_allows_the_runtime_folders_under_home_and_the_guarded_checkout(
    tmp_path: Path,
    runtime_folders: Sequence[str],
    with_home: bool,
    with_guard: bool,
    expected_folders: list[str],
) -> None:
    layout = build_layout(tmp_path)
    request = run_request(layout, with_home=with_home)
    if not with_guard:
        request = request.model_copy(update={"guard": None})
    temporary = temporary_folder(layout.temporary_root, "r")

    confinement = run_confinement(request, temporary, runtime_folders=runtime_folders, devices=[])

    candidates = {layout.home / folder for folder in runtime_folders}
    in_home = [folder for folder in confinement.folders if folder in candidates]
    in_checkout = [
        path
        for path in [*confinement.folders, *confinement.files]
        if path.is_relative_to(layout.checkout)
    ]
    assert in_home == [layout.home / folder for folder in expected_folders]
    assert bool(in_checkout) == with_guard


@pytest.mark.parametrize(
    ("stderr", "expected"),
    [
        pytest.param(
            "a note\nfactory-confine: first\nfactory-confine: second\n",
            "factory-confine: first",
            id="first-of-two",
        ),
        pytest.param("a note\nsudo: other\n", None, id="no-match"),
        pytest.param("a note factory-confine: inside\n", None, id="not-at-line-start"),
    ],
)
def test_line_starting_finds_the_first_line_that_starts_with_the_prefix(
    stderr: str, expected: str | None
) -> None:
    assert line_starting(stderr, "factory-confine:") == expected


@pytest.mark.parametrize(
    ("os_user", "exit_status", "duration", "expected"),
    [
        pytest.param("agent", 137, LIMIT, True, id="137-at-limit"),
        pytest.param("agent", -9, LIMIT, True, id="minus-9-at-limit"),
        pytest.param("agent", 137, LIMIT + timedelta(seconds=1), True, id="above-limit"),
        pytest.param("agent", 137, LIMIT - timedelta(milliseconds=1), False, id="below-limit"),
        pytest.param(None, 137, LIMIT, False, id="without-user"),
        pytest.param("agent", 1, LIMIT, False, id="exit-1"),
    ],
)
def test_killed_at_limit_needs_a_user_a_kill_status_and_the_limit_reached(
    os_user: str | None, exit_status: int, duration: timedelta, expected: bool
) -> None:
    killed = killed_at_limit(
        os_user=os_user, exit_status=exit_status, duration=duration, time_limit=LIMIT
    )

    assert killed is expected


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        pytest.param("\n2.1.296 (Claude Code)\n", "2.1.296", id="version"),
        pytest.param("", None, id="empty"),
        pytest.param("  \n", None, id="blank"),
    ],
)
def test_first_word_is_the_first_word_of_the_first_non_blank_line(
    output: str, expected: str | None
) -> None:
    assert first_word(output) == expected


@pytest.mark.parametrize(
    ("budget", "expected"),
    [
        pytest.param("1", "0.50", id="below-minimum"),
        pytest.param("2", "0.50", id="at-minimum"),
        pytest.param("4", "1.00", id="quarter"),
        pytest.param("2.50", "0.63", id="rounded-up"),
    ],
)
def test_resume_budget_is_a_quarter_at_least_fifty_cents(budget: str, expected: str) -> None:
    result = resume_budget(Decimal(budget))

    assert result == Decimal(expected)
    assert str(result) == expected
