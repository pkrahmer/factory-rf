"""The runtime writes the run's temporary folder into the guard settings file."""

import json
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls, write_stand_in
from adapters.test_claude_runtime_os_user import REPLY
from confine_support import Layout, confined_runtime, run_request
from factory.adapters.claude_runtime import ClaudeCodeRuntime


@pytest.mark.parametrize(
    "confined", [pytest.param(True, id="confined"), pytest.param(False, id="unconfined")]
)
def test_the_guard_settings_file_names_the_run_s_temporary_folder_when_confined(
    layout: Layout, *, confined: bool
) -> None:
    claude = write_stand_in(layout.stand_in, [Step(stdout=REPLY)])
    runtime = (
        confined_runtime(layout, claude)
        if confined
        else ClaudeCodeRuntime(str(claude), layout.state)
    )

    runtime.run(run_request(layout))

    [call] = read_calls(layout.stand_in)
    [guard] = [text for name, text in call.files.items() if Path(name).name.startswith("guard-")]
    expected = call.environment["TMPDIR"] if confined else None
    assert json.loads(guard)["temporary_directory"] == expected
