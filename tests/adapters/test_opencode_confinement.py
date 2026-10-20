"""Through the write guard's wrapper, the opencode run's temporary folder is gone after the run."""

import time
from datetime import timedelta
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls
from adapters.opencode_stand_in import (
    BOUND_SECONDS,
    MODELS,
    REPLY,
    WAITING,
    write_opencode,
)
from adapters.test_claude_runtime_os_user import _sudo_calls, _write_sudo
from confine_support import CONFINE, LIMIT, Layout, run_request, write_confine
from factory.adapters.agent_launch import CLEANUP_SCRIPT
from factory.adapters.opencode_runtime import CONFIG_VARIABLE, OpencodeRuntime

# A few seconds, so the child has room to start; the stand-in waits far longer.
SHORT_LIMIT = timedelta(seconds=3)


def _runtime(
    layout: Layout, steps: list[Step], confine: str, sudo: Path | None = None
) -> OpencodeRuntime:
    executable = write_opencode(layout.stand_in, steps)
    layout.state.mkdir()
    if sudo is None:
        return OpencodeRuntime(
            str(executable),
            layout.state,
            models=MODELS,
            confine_executable=confine,
            temporary_root=layout.temporary_root,
        )
    return OpencodeRuntime(
        str(executable),
        layout.state,
        models=MODELS,
        sudo_executable=str(sudo),
        confine_executable=confine,
        temporary_root=layout.temporary_root,
    )


@pytest.mark.parametrize(
    ("step", "time_limit", "end_reason"),
    [
        pytest.param(REPLY, LIMIT, "completed", id="completed"),
        pytest.param(Step(exit_status=1), LIMIT, "died", id="died"),
        pytest.param(
            WAITING,
            SHORT_LIMIT,
            "time_limit",
            id="time-limit",
        ),
    ],
)
def test_through_the_wrapper_the_temporary_root_is_empty_after_the_run(
    layout: Layout, step: Step, time_limit: timedelta, end_reason: str
) -> None:
    runtime = _runtime(layout, [step], CONFINE)

    started = time.monotonic()
    result = runtime.run(run_request(layout, time_limit=time_limit))
    elapsed = time.monotonic() - started

    assert result.end_reason == end_reason
    assert elapsed < BOUND_SECONDS
    assert list(layout.temporary_root.iterdir()) == []


def test_with_an_agent_user_the_temporary_folder_is_removed_through_sudo(layout: Layout) -> None:
    confine = write_confine(layout)
    sudo = _write_sudo(layout.sudo_bin)
    runtime = _runtime(layout, [REPLY], str(confine), sudo)

    runtime.run(run_request(layout, os_user="agent"))

    [call] = read_calls(layout.stand_in)
    run = Path(call.environment[CONFIG_VARIABLE]).name.removeprefix("opencode-")
    folder = layout.temporary_root / f"factory-run-{run.removesuffix('.json')}"
    assert _sudo_calls(layout.sudo_bin)[-1].arguments == [
        "-n",
        "-u",
        "agent",
        "--",
        "/bin/sh",
        "-c",
        CLEANUP_SCRIPT,
        "factory-cleanup",
        str(folder),
    ]
