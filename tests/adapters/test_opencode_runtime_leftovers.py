"""The opencode runtime ends the agent's leftover processes after every call."""

from pathlib import Path

import pytest

from adapters.opencode_stand_in import MODELS, REPLY, write_opencode
from confine_support import Layout, run_request
from factory.adapters.opencode_runtime import OpencodeRuntime
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


def _runtime(
    layout: Layout,
    program: Path,
    *,
    sudo_refusal: str = "",
) -> OpencodeRuntime:
    sudo = write_sudo(layout.sudo_bin, program, refusal=sudo_refusal)
    layout.state.mkdir()
    return OpencodeRuntime(
        str(write_opencode(layout.stand_in, [REPLY])),
        layout.state,
        models=MODELS,
        sudo_executable=str(sudo),
        leftovers=[str(program)],
    )


@pytest.mark.parametrize(
    ("os_user", "exit_status", "stderr", "expected_kinds", "fault"),
    [
        pytest.param(OTHER_USER, 0, "", ["run", "program"], None, id="other-user"),
        pytest.param(own_user(), 0, "", ["run"], None, id="own-user"),
        pytest.param(
            OTHER_USER,
            1,
            f"{LEFTOVERS_LINE}\n",
            ["run", "program"],
            f"cannot end the agent's processes: {LEFTOVERS_LINE}",
            id="program-fails",
        ),
    ],
)
def test_after_the_call_the_program_runs_as_the_user_from_the_root_before_the_removal(  # noqa: PLR0913 - one parameter per column of the table
    layout: Layout,
    os_user: str,
    *,
    exit_status: int,
    stderr: str,
    expected_kinds: list[str],
    fault: str | None,
) -> None:
    program_bin = layout.checkout.parent / "leftovers-bin"
    program = write_program(program_bin, exit_status=exit_status, stderr=stderr)
    runtime = _runtime(layout, program)
    request = run_request(layout, os_user=os_user)

    if fault is not None:
        with pytest.raises(AgentRuntimeError) as raised:
            runtime.run(request)
        assert raised.value.detail == fault
    else:
        assert runtime.run(request).end_reason == "completed"
    records = sudo_records(layout.sudo_bin)
    assert kinds(layout.sudo_bin, program) == expected_kinds
    if "program" in expected_kinds:
        assert records[1].arguments == [
            "-n",
            "-u",
            OTHER_USER,
            "--",
            str(program),
            "--user",
            OTHER_USER,
        ]
        assert records[1].working_directory == Path("/")
        assert program_calls(program_bin) == [["--user", OTHER_USER]]
    else:
        assert program_calls(program_bin) == []


@pytest.mark.parametrize("refuser", [pytest.param("sudo")])
def test_a_call_refused_by_sudo_or_the_wrapper_keeps_its_own_error_and_still_starts_the_program(
    layout: Layout, refuser: str
) -> None:
    program_bin = layout.checkout.parent / "leftovers-bin"
    program = write_program(program_bin, exit_status=1, stderr=f"{LEFTOVERS_LINE}\n")
    runtime = _runtime(
        layout,
        program,
        sudo_refusal=f"{SUDO_LINE}\n" if refuser == "sudo" else "",
    )
    refused_by = layout.sudo_bin / refuser
    line = SUDO_LINE

    with pytest.raises(AgentRuntimeError) as raised:
        runtime.run(run_request(layout, os_user=OTHER_USER))

    assert raised.value.detail.startswith(f"{refused_by} refused the agent run: {line}")
    assert program_calls(program_bin) == [["--user", OTHER_USER]]
