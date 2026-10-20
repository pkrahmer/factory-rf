"""Under `sudo`, an opencode call killed at its time limit ends `time_limit`, others `died`."""

import json
import time
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step
from adapters.opencode_stand_in import (
    MODELS,
    SESSION,
    WAIT_SECONDS,
    opencode_request,
    stdout,
    step_start,
    write_opencode,
)
from adapters.test_agent_launch_login import API_LOGIN
from adapters.test_claude_runtime_os_user import _write_sudo
from confine_support import write_script
from factory.adapters.opencode_runtime import OpencodeRuntime
from time_limits import ROOMY_BOUND_SECONDS, ROOMY_LIMIT

# Past the limit, well inside the grace `sudo` calls get on top of it.
PAST_LIMIT_SECONDS = ROOMY_LIMIT.total_seconds() + 1.5
STARTED = stdout(step_start())

# A `sudo` that runs nothing: it prints a step, waits past the limit, then ends as planned.
ENDING_SUDO = r"""
import json
import os
import signal
import sys
import time
from pathlib import Path

plan = json.loads((Path(__file__).resolve().parent / "plan.json").read_text(encoding="utf-8"))
sys.stdout.write(plan["stdout"])
sys.stdout.flush()
time.sleep(plan["wait_seconds"])
if plan["killed"]:
    os.kill(os.getpid(), signal.SIGKILL)
sys.exit(1)
"""


def _passing_sudo(tmp_path: Path) -> Path:
    return _write_sudo(tmp_path / "sudo-bin")


def _ending_sudo(tmp_path: Path, *, killed: bool) -> Path:
    folder = tmp_path / "sudo-bin"
    path = write_script(folder / "sudo", ENDING_SUDO)
    plan = {"stdout": STARTED, "wait_seconds": PAST_LIMIT_SECONDS, "killed": killed}
    (folder / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("step", "sudo_kind", "end_reason"),
    [
        pytest.param(
            Step(stdout_before_wait=STARTED, wait_seconds=WAIT_SECONDS),
            "passing",
            "time_limit",
            id="killed-at-the-limit",
        ),
        pytest.param(Step(stdout=STARTED, exit_status=137), "passing", "died", id="137-at-once"),
        pytest.param(Step(stdout=STARTED), "killed", "time_limit", id="sigkill-past-the-limit"),
        pytest.param(Step(stdout=STARTED), "exits-1", "died", id="status-1-past-the-limit"),
    ],
)
def test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login(
    tmp_path: Path, step: Step, sudo_kind: str, end_reason: str
) -> None:
    sudo = (
        _passing_sudo(tmp_path)
        if sudo_kind == "passing"
        else _ending_sudo(tmp_path, killed=sudo_kind == "killed")
    )
    api = tmp_path / "login" / "api-login"
    api.parent.mkdir()
    api.write_text(f"{API_LOGIN}\n", encoding="utf-8")
    state = tmp_path / "state"
    state.mkdir()
    runtime = OpencodeRuntime(
        str(write_opencode(tmp_path / "bin", [step])),
        state,
        models=MODELS,
        sudo_executable=str(sudo),
        api_login_file=api,
    )
    request = opencode_request(tmp_path / "work", os_user="agent", time_limit=ROOMY_LIMIT)

    started = time.monotonic()
    result = runtime.run(request)
    elapsed = time.monotonic() - started

    assert result.end_reason == end_reason
    assert elapsed < ROOMY_BOUND_SECONDS
    if sudo_kind == "passing" and end_reason == "time_limit":
        assert (result.session, result.login) == (SESSION, "api_key")
