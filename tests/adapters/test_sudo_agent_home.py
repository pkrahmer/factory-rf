"""`SudoAgentHome` clears the agent's home by running the fresh-home program through `sudo`."""

import errno
import inspect
import os
import sys
import time
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters import agent_home
from factory.adapters.agent_home import SudoAgentHome
from factory.adapters.agent_launch import SUDO_GRACE
from factory.adapters.process import ProcessResult
from factory.application.agent_home import AgentHome
from factory.domain.errors import AgentRuntimeError
from run_process_recorder import Recorder
from sudo_support import write_sudo

PROGRAM = [sys.executable, "-I", "-B", "-m", "factory.entry.fresh_home"]
KEPT = [".claude-token", ".config/sso"]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def home(tmp_path: Path) -> Path:
    """Return an agent's home under `tmp_path`."""
    folder = tmp_path / "home"
    folder.mkdir()
    return folder


def test_the_agent_home_interface_has_reset_alone_and_sudo_agent_home_implements_it() -> None:
    assert inspect.isabstract(AgentHome)
    assert AgentHome.__abstractmethods__ == {"reset"}
    assert issubclass(SudoAgentHome, AgentHome)


def test_reset_runs_the_fresh_home_program_through_sudo_from_the_root_and_keeps_the_kept(
    tmp_path: Path, home: Path
) -> None:
    _write(home / ".claude" / "CLAUDE.md", "steer\n")
    _write(home / ".claude-token", "stand-in\n")
    _write(home / ".config" / "sso" / "login", "stand-in\n")
    sudo = write_sudo(tmp_path / "sudo-bin")
    agent = SudoAgentHome(
        home, KEPT, os_user="agent", sudo_executable=str(sudo.path), program=PROGRAM
    )

    agent.reset()

    [call] = sudo.calls()
    assert call.arguments == [
        "-n",
        "-u",
        "agent",
        "--",
        "timeout",
        "--signal=KILL",
        "60s",
        "env",
        "-i",
        sys.executable,
        "-I",
        "-B",
        "-m",
        "factory.entry.fresh_home",
        "--home",
        str(home),
        "--keep",
        ".claude-token",
        "--keep",
        ".config/sso",
    ]
    assert call.working_directory == Path("/")
    assert not (home / ".claude" / "CLAUDE.md").exists()
    assert (home / ".claude-token").is_file()
    assert (home / ".config" / "sso" / "login").is_file()


@pytest.mark.parametrize(
    ("planned", "line"),
    [
        pytest.param(
            (
                1,
                "sudo: unable to resolve host x\nfactory-fresh-home: .cache/a: Permission denied\n",
            ),
            "factory-fresh-home: .cache/a: Permission denied",
            id="prefixed-line",
        ),
        pytest.param(
            (1, "sudo: a password is required\n"), "sudo: a password is required", id="sudo-line"
        ),
        pytest.param((3, ""), "exit status 3", id="no-standard-error"),
        pytest.param((1, "a\nb\n\n"), "b", id="last-non-blank-line"),
        pytest.param(None, os.strerror(errno.ENOENT), id="no-sudo"),
    ],
)
def test_a_failed_reset_raises_with_the_line_that_says_why(
    tmp_path: Path, home: Path, *, planned: tuple[int, str] | None, line: str
) -> None:
    if planned is None:
        sudo = tmp_path / "missing" / "sudo"
    else:
        exit_status, stderr = planned
        sudo = write_sudo(tmp_path / "sudo-bin", exit_status=exit_status, stderr=stderr).path
    agent = SudoAgentHome(home, KEPT, os_user="agent", sudo_executable=str(sudo), program=PROGRAM)

    with pytest.raises(AgentRuntimeError) as raised:
        agent.reset()

    assert raised.value.detail == f"cannot reset the agent's home {home}: {line}"


@pytest.mark.parametrize(
    ("program", "detail"),
    [
        pytest.param(
            [sys.executable, "-c", "import time; time.sleep(60)"], "no end within 3 s", id="sleeps"
        ),
        pytest.param([sys.executable, "-c", "pass"], None, id="ends-at-once"),
    ],
)
def test_a_reset_that_reaches_its_time_limit_raises(
    tmp_path: Path,
    home: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    program: list[str],
    detail: str | None,
) -> None:
    assert timedelta(seconds=60) == agent_home.FRESH_HOME_TIME_LIMIT
    monkeypatch.setattr(agent_home, "FRESH_HOME_TIME_LIMIT", timedelta(seconds=3))
    sudo = write_sudo(tmp_path / "sudo-bin")
    agent = SudoAgentHome(
        home, [], os_user="agent", sudo_executable=str(sudo.path), program=program
    )

    if detail is None:
        agent.reset()
        return
    started = time.monotonic()
    with pytest.raises(AgentRuntimeError) as raised:
        agent.reset()
    elapsed = time.monotonic() - started

    assert raised.value.detail == f"cannot reset the agent's home {home}: {detail}"
    assert 3 <= elapsed < 25


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> Recorder:
    """Return a `run_process` stand-in put in place of the one `reset` calls."""
    stand_in = Recorder()
    monkeypatch.setattr(agent_home, "run_process", stand_in)
    return stand_in


def test_the_reset_call_has_no_environment_and_the_limit_plus_the_sudo_grace(
    home: Path, recorder: Recorder
) -> None:
    recorder.results = [
        ProcessResult(
            exit_status=0, stdout="", stderr="", timed_out=False, duration=timedelta(seconds=1)
        )
    ]
    agent = SudoAgentHome(home, KEPT, os_user="agent", sudo_executable="sudo", program=PROGRAM)

    agent.reset()

    [request] = recorder.requests
    assert request.env == {}
    assert request.time_limit == agent_home.FRESH_HOME_TIME_LIMIT + SUDO_GRACE
    assert request.time_limit == timedelta(seconds=90)
    assert request.cwd == Path("/")


def test_a_reset_the_factory_ended_at_its_limit_raises(home: Path, recorder: Recorder) -> None:
    recorder.results = [
        ProcessResult(
            exit_status=None,
            stdout="",
            stderr="",
            timed_out=True,
            duration=timedelta(seconds=90),
        )
    ]
    agent = SudoAgentHome(home, KEPT, os_user="agent", sudo_executable="sudo", program=PROGRAM)

    with pytest.raises(AgentRuntimeError) as raised:
        agent.reset()

    assert raised.value.detail == f"cannot reset the agent's home {home}: no end within 60 s"
