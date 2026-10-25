"""The make class runs its commands as another user through `sudo -n -u ... timeout ... env -i`."""

import time
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.make_commands import CommandUser, MakeProjectCommands
from factory.domain.errors import ProjectCommandError
from leftovers_runtime_support import SUDO_LINE
from sudo_support import write_sudo

LIMIT = timedelta(seconds=30)
SHORT_LIMIT = timedelta(seconds=3)
UPPER_BOUND_SECONDS = 25
PATH = "/usr/bin:/bin"
WARNING = "sudo: unable to resolve host x"

CHECK_RECIPES = (
    '@echo "home=$$HOME token=$${FACTORY_TOKEN_FILE:-unset}"',
    '@echo "to-stderr" >&2',
    '@echo "check: green (0.1 s)"',
)


def _write_makefile(directory: Path, *, removes: Path | None = None) -> None:
    recipes = (*CHECK_RECIPES, f"@rm -f '{removes}'") if removes is not None else CHECK_RECIPES
    check = "".join(f"\t{recipe}\n" for recipe in recipes)
    makefile = f"check:\n{check}\nslow:\n\t@sleep 60\n"
    (directory / "Makefile").write_text(makefile, encoding="utf-8")


def _user(
    sudo: str,
    *,
    environment: dict[str, str] | None = None,
    os_user: str = "agent",
) -> CommandUser:
    return CommandUser(
        os_user=os_user,
        sudo_executable=sudo,
        environment={"PATH": PATH} if environment is None else environment,
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    directory = tmp_path / "project"
    directory.mkdir()
    _write_makefile(directory)
    return directory


def test_the_command_runs_through_sudo_timeout_and_env_with_only_the_user_s_environment(
    tmp_path: Path, project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FACTORY_TOKEN_FILE", "/run/token")
    home = tmp_path / "home"
    sudo = write_sudo(tmp_path / "sudo-bin")
    user = _user(str(sudo.path), environment={"PATH": PATH, "HOME": str(home)})

    result = MakeProjectCommands(project, user=user).run("check", time_limit=LIMIT)

    [call] = sudo.calls()
    assert call.arguments == [
        "-n",
        "-u",
        "agent",
        "--",
        "timeout",
        "--signal=KILL",
        "30s",
        "env",
        "-i",
        f"PATH={PATH}",
        f"HOME={home}",
        "make",
        "--no-print-directory",
        "check",
    ]
    assert "FACTORY_TOKEN_FILE" not in call.environment
    assert result.status == "passed"
    lines = result.output_tail.splitlines()
    assert f"home={home} token=unset" in lines
    assert "to-stderr" in lines
    assert [target.target for target in result.targets] == ["check"]


@pytest.mark.parametrize(
    ("time_limit", "word"),
    [(timedelta(seconds=30), "30s"), (timedelta(seconds=1.5), "2s")],
)
def test_the_limit_is_given_to_timeout_in_whole_seconds_rounded_up(
    tmp_path: Path, project: Path, time_limit: timedelta, word: str
) -> None:
    sudo = write_sudo(tmp_path / "sudo-bin")

    MakeProjectCommands(project, user=_user(str(sudo.path))).run("check", time_limit=time_limit)

    [call] = sudo.calls()
    assert call.arguments[4:8] == ["timeout", "--signal=KILL", word, "env"]


@pytest.mark.parametrize("variable", ["MAKELEVEL=1", "MAKEFLAGS=w", "MFLAGS=-w"])
def test_the_outer_make_variables_of_the_user_s_environment_are_left_out(
    tmp_path: Path, project: Path, variable: str
) -> None:
    name, value = variable.split("=", 1)
    sudo = write_sudo(tmp_path / "sudo-bin")
    user = _user(str(sudo.path), environment={"PATH": PATH, name: value})

    MakeProjectCommands(project, user=user).run("check", time_limit=LIMIT)

    [call] = sudo.calls()
    assert variable not in call.arguments
    assert f"PATH={PATH}" in call.arguments


@pytest.mark.parametrize("warning", ["", f"{WARNING}\n"], ids=["quiet", "sudo-warning"])
def test_a_command_killed_by_its_own_timeout_is_a_time_limit_result(
    tmp_path: Path, project: Path, warning: str
) -> None:
    sudo = write_sudo(tmp_path / "sudo-bin", warning=warning)
    commands = MakeProjectCommands(project, user=_user(str(sudo.path)))
    start = time.monotonic()

    result = commands.run("slow", time_limit=SHORT_LIMIT)

    elapsed = time.monotonic() - start
    assert result.status == "time_limit"
    assert result.exit_status is None
    assert SHORT_LIMIT.total_seconds() <= elapsed < UPPER_BOUND_SECONDS


def test_the_factory_s_own_kill_waits_the_grace_beyond_the_limit(
    tmp_path: Path, project: Path
) -> None:
    sudo = write_sudo(tmp_path / "sudo-bin", exit_status=0, wait_seconds=5)
    commands = MakeProjectCommands(project, user=_user(str(sudo.path)))
    start = time.monotonic()

    result = commands.run("check", time_limit=SHORT_LIMIT)

    elapsed = time.monotonic() - start
    assert result.status == "passed"
    assert result.exit_status == 0
    assert 5 <= elapsed < UPPER_BOUND_SECONDS


@pytest.mark.parametrize("exit_status", [137, 1])
def test_an_exit_before_the_limit_is_a_failed_command_with_its_status(
    tmp_path: Path, project: Path, exit_status: int
) -> None:
    sudo = write_sudo(tmp_path / "sudo-bin", exit_status=exit_status, stderr="boom\n")

    result = MakeProjectCommands(project, user=_user(str(sudo.path))).run("check", time_limit=LIMIT)

    assert result.status == "failed"
    assert result.exit_status == exit_status
    assert result.duration < LIMIT


# The outcome is the refusal's line, or the exit status of the result when it is none.
@pytest.mark.parametrize(
    ("exit_status", "stderr", "outcome"),
    [
        pytest.param(1, f"{SUDO_LINE}\n", SUDO_LINE, id="refused"),
        pytest.param(1, f"{WARNING}\n{SUDO_LINE}\n", SUDO_LINE, id="last-sudo-line"),
        pytest.param(0, f"{WARNING}\n", 0, id="status-0"),
        pytest.param(1, f"{WARNING}\nboom\n", 1, id="beside-other-output"),
        pytest.param(1, "", 1, id="no-output"),
    ],
)
def test_only_sudo_lines_and_a_failing_status_are_a_refusal(
    tmp_path: Path, project: Path, exit_status: int, stderr: str, outcome: str | int
) -> None:
    sudo = write_sudo(tmp_path / "sudo-bin", exit_status=exit_status, stderr=stderr)
    commands = MakeProjectCommands(project, user=_user(str(sudo.path)))

    if isinstance(outcome, str):
        with pytest.raises(ProjectCommandError) as caught:
            commands.run("check", time_limit=LIMIT)
        assert caught.value.detail == f"{sudo.path} refused the command: {outcome}"
        return
    result = commands.run("check", time_limit=LIMIT)
    assert result.exit_status == outcome
    assert result.status == ("passed" if outcome == 0 else "failed")


@pytest.mark.parametrize(
    ("command", "time_limit", "error"),
    [
        pytest.param("check", timedelta(0), ValueError, id="zero-limit"),
        pytest.param("Check", LIMIT, ProjectCommandError, id="bad-name"),
    ],
)
def test_the_checks_before_the_start_refuse_without_calling_sudo(
    tmp_path: Path, project: Path, command: str, time_limit: timedelta, error: type[Exception]
) -> None:
    sudo = write_sudo(tmp_path / "sudo-bin")
    commands = MakeProjectCommands(project, user=_user(str(sudo.path)))

    with pytest.raises(error):
        commands.run(command, time_limit=time_limit)

    assert sudo.calls() == []


def test_a_sudo_that_does_not_exist_is_a_project_command_error(
    tmp_path: Path, project: Path
) -> None:
    commands = MakeProjectCommands(project, user=_user(str(tmp_path / "missing" / "sudo")))

    with pytest.raises(ProjectCommandError) as caught:
        commands.run("check", time_limit=LIMIT)

    assert caught.value.detail.startswith("[Errno 2] No such file or directory")


def test_the_user_property_returns_what_the_constructor_was_given(tmp_path: Path) -> None:
    user = _user("/usr/bin/sudo")

    assert MakeProjectCommands(tmp_path).user is None
    assert MakeProjectCommands(tmp_path, user=user).user is user
