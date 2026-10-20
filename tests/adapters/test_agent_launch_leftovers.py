"""After a call, the runtimes start the program that ends the agent's leftover processes."""

from datetime import timedelta

import pytest

from factory.adapters.agent_launch import (
    LoginFiles,
    Starters,
    leftovers_due,
    leftovers_fault,
    leftovers_launch,
)

FAULT = "cannot end the agent's processes: "
STOPPED = "factory-leftovers: 2 processes left after 50 rounds: 7, 10"
HOST_LINE = "sudo: unable to resolve host x\n"


@pytest.mark.parametrize(
    ("leftovers", "os_user", "due"),
    [
        pytest.param(["prog"], "agent", True, id="other-user"),
        pytest.param(None, "agent", False, id="no-program"),
        pytest.param(["prog"], None, False, id="no-user"),
        pytest.param(["prog"], "factory", False, id="own-user"),
    ],
)
def test_the_program_is_due_only_with_a_program_and_a_user_other_than_the_own(
    leftovers: list[str] | None, os_user: str | None, *, due: bool
) -> None:
    starters = Starters(
        sudo_executable="/usr/bin/sudo",
        confine_executable=None,
        login_files=LoginFiles(),
        leftovers=leftovers,
    )

    assert leftovers_due(starters, os_user, "factory") is due


def test_the_program_starts_through_sudo_as_the_user_with_an_empty_environment() -> None:
    launch = leftovers_launch(
        ["/opt/py", "-I", "-m", "factory.entry.leftovers"],
        os_user="agent",
        sudo_executable="/usr/bin/sudo",
    )

    assert launch.argv == [
        "/usr/bin/sudo",
        "-n",
        "-u",
        "agent",
        "--",
        "/opt/py",
        "-I",
        "-m",
        "factory.entry.leftovers",
        "--user",
        "agent",
    ]
    assert launch.env == {}
    assert launch.time_limit == timedelta(seconds=30)


@pytest.mark.parametrize(
    ("exit_status", "timed_out", "stderr", "fault"),
    [
        pytest.param(0, False, "", None, id="ended"),
        pytest.param(0, False, HOST_LINE, None, id="ended-with-sudo-warning"),
        pytest.param(1, False, f"{HOST_LINE}{STOPPED}\n", f"{FAULT}{STOPPED}", id="program-line"),
        pytest.param(
            1, False, "sudo: a password is required\n", f"{FAULT}exit status 1", id="sudo-only"
        ),
        pytest.param(None, True, "", f"{FAULT}no end within 30 s", id="timed-out"),
        pytest.param(0, True, "", f"{FAULT}no end within 30 s", id="timed-out-status-0"),
    ],
)
def test_the_program_s_fault_names_its_line_its_status_or_its_time_limit(
    exit_status: int | None, *, timed_out: bool, stderr: str, fault: str | None
) -> None:
    assert leftovers_fault(exit_status=exit_status, timed_out=timed_out, stderr=stderr) == fault
