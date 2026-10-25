"""The `claude -p` runtime ends the agent's leftover processes after every call."""

from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls, write_stand_in
from adapters.test_claude_runtime_login import BUDGET_STOP
from adapters.test_claude_runtime_os_user import REPLY
from confine_support import Layout, run_request
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.domain.errors import AgentRuntimeError
from leftovers_runtime_support import (
    LEFTOVERS_LINE,
    OTHER_USER,
    SUDO_LINE,
    kinds,
    own_user,
    program_calls,
    sudo_records,
    write_program,
    write_sudo,
)

FAULT = "cannot end the agent's processes: "


def _program_bin(layout: Layout) -> Path:
    return layout.checkout.parent / "leftovers-bin"


def _runtime(
    layout: Layout,
    steps: list[Step],
    *,
    program: Path,
    with_leftovers: bool = True,
    sudo_refusal: str = "",
) -> ClaudeCodeRuntime:
    claude = write_stand_in(layout.stand_in, steps)
    sudo = write_sudo(layout.sudo_bin, program, refusal=sudo_refusal)
    return ClaudeCodeRuntime(
        str(claude),
        layout.state,
        sudo_executable=str(sudo),
        leftovers=[str(program)] if with_leftovers else None,
    )


@pytest.mark.parametrize(
    ("os_user", "with_leftovers", "expected_kinds", "expected_program_calls"),
    [
        pytest.param(
            OTHER_USER,
            True,
            ["run", "program"],
            [["--user", OTHER_USER]],
            id="other-user",
        ),
        pytest.param(own_user(), True, ["run"], [], id="own-user"),
        pytest.param(OTHER_USER, False, ["run"], [], id="without-leftovers"),
    ],
)
def test_after_the_call_the_program_runs_as_the_user_from_the_root_before_the_removal(
    layout: Layout,
    os_user: str,
    *,
    with_leftovers: bool,
    expected_kinds: list[str],
    expected_program_calls: list[list[str]],
) -> None:
    program = write_program(_program_bin(layout))
    runtime = _runtime(layout, [Step(stdout=REPLY)], program=program, with_leftovers=with_leftovers)

    result = runtime.run(run_request(layout, os_user=os_user))

    records = sudo_records(layout.sudo_bin)
    assert kinds(layout.sudo_bin, program) == expected_kinds
    if "program" in expected_kinds:
        started = records[1]
        assert started.arguments == [
            "-n",
            "-u",
            OTHER_USER,
            "--",
            str(program),
            "--user",
            OTHER_USER,
        ]
        assert started.working_directory == Path("/")
    assert program_calls(_program_bin(layout)) == expected_program_calls
    assert (result.end_reason, result.decision) == ("completed", "doing")


def test_a_run_without_a_user_and_the_version_start_neither_sudo_nor_the_program(
    layout: Layout,
) -> None:
    program = write_program(_program_bin(layout))
    steps = [Step(stdout=REPLY), Step(stdout="2.1.289 (Claude Code)\n")]
    runtime = _runtime(layout, steps, program=program)

    result = runtime.run(run_request(layout))
    runtime.version()

    assert (result.end_reason, result.decision, result.entry) == ("completed", "doing", "Done.")
    assert read_calls(layout.stand_in)[-1].arguments == ["--version"]
    assert sudo_records(layout.sudo_bin) == []
    assert program_calls(_program_bin(layout)) == []


def test_a_resumed_run_starts_the_program_after_each_of_its_calls(layout: Layout) -> None:
    program = write_program(_program_bin(layout))
    steps = [Step(stdout=BUDGET_STOP), Step(stdout=REPLY)]
    runtime = _runtime(layout, steps, program=program)

    runtime.run(run_request(layout, os_user=OTHER_USER))

    assert len(read_calls(layout.stand_in)) == len(steps)
    assert program_calls(_program_bin(layout)) == [["--user", OTHER_USER]] * 2
    assert kinds(layout.sudo_bin, program) == ["run", "program"] * 2


@pytest.mark.parametrize(
    ("exit_status", "stderr", "fault"),
    [
        pytest.param(0, "", None, id="ended"),
        pytest.param(1, f"{LEFTOVERS_LINE}\n", f"{FAULT}{LEFTOVERS_LINE}", id="program-line"),
        pytest.param(3, "", f"{FAULT}exit status 3", id="exit-status"),
    ],
)
def test_a_failed_program_after_a_good_call_is_a_runtime_error_after_the_removal(
    layout: Layout, exit_status: int, stderr: str, fault: str | None
) -> None:
    program = write_program(_program_bin(layout), exit_status=exit_status, stderr=stderr)
    runtime = _runtime(layout, [Step(stdout=REPLY)], program=program)
    request = run_request(layout, os_user=OTHER_USER)

    if fault is not None:
        with pytest.raises(AgentRuntimeError) as raised:
            runtime.run(request)
        assert raised.value.detail == fault
    else:
        result = runtime.run(request)
        assert (result.end_reason, result.decision, result.entry) == ("completed", "doing", "Done.")
    assert kinds(layout.sudo_bin, program) == ["run", "program"]


@pytest.mark.parametrize("refuser", [pytest.param("sudo")])
def test_a_call_refused_by_sudo_or_the_wrapper_keeps_its_own_error_and_still_starts_the_program(
    layout: Layout, refuser: str
) -> None:
    program = write_program(_program_bin(layout), exit_status=1, stderr=f"{LEFTOVERS_LINE}\n")
    runtime = _runtime(
        layout,
        [Step(stdout=REPLY)],
        program=program,
        sudo_refusal=f"{SUDO_LINE}\n" if refuser == "sudo" else "",
    )
    refused_by = layout.sudo_bin / refuser
    line = SUDO_LINE

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(run_request(layout, os_user=OTHER_USER))

    assert raised.value.detail.startswith(f"{refused_by} refused the agent run: {line}")
    assert program_calls(_program_bin(layout)) == [["--user", OTHER_USER]]
