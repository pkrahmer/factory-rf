"""The opencode runtime ends the agent's leftover processes after every call."""

from pathlib import Path

import pytest

from adapters.opencode_stand_in import MODELS, REPLY, write_opencode
from confine_support import Layout, run_request, write_confine
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.domain.errors import AgentRuntimeError
from leftovers_runtime_support import (
    LEFTOVERS_LINE,
    OTHER_USER,
    kinds,
    own_user,
    program_calls,
    sudo_records,
    write_program,
    write_sudo,
)


@pytest.mark.parametrize(
    ("os_user", "exit_status", "stderr", "expected_kinds", "fault"),
    [
        pytest.param(OTHER_USER, 0, "", ["run", "program", "removal"], None, id="other-user"),
        pytest.param(own_user(), 0, "", ["run", "removal"], None, id="own-user"),
        pytest.param(
            OTHER_USER,
            1,
            f"{LEFTOVERS_LINE}\n",
            ["run", "program", "removal"],
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
    sudo = write_sudo(layout.sudo_bin, program)
    layout.state.mkdir()
    runtime = OpencodeRuntime(
        str(write_opencode(layout.stand_in, [REPLY])),
        layout.state,
        models=MODELS,
        sudo_executable=str(sudo),
        confine_executable=str(write_confine(layout)),
        temporary_root=layout.temporary_root,
        leftovers=[str(program)],
    )
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
