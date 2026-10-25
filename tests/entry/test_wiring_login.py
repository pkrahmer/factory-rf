"""The wiring hands the setting that names the login file to the agent runtime."""

import json
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, claude_request, read_calls, write_stand_in
from factory.adapters.claude_runtime import LOGIN_VARIABLE
from factory.adapters.fake_hosting import FakeHostingService
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from wiring_support import CREDENTIAL

LOGIN = "stand-in-login"
REPLY = json.dumps(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "total_cost_usd": 0.1,
        "duration_ms": 100,
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "permission_denials": [],
        "structured_output": {"decision": "doing", "entry": "Done."},
    }
)


@pytest.mark.parametrize(
    ("configured", "expected"),
    [pytest.param(True, LOGIN, id="login-file"), pytest.param(False, None, id="no-login-file")],
)
def test_the_built_runtime_hands_the_login_file_s_token_to_claude(
    tmp_path: Path, *, configured: bool, expected: str | None
) -> None:
    login = tmp_path / "claude-login"
    login.write_text(f"{LOGIN}\n", encoding="utf-8")
    executable = write_stand_in(tmp_path / "bin", [Step(stdout=REPLY)])
    root = tmp_path.resolve()
    settings = InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=root / "checkout",
        state_directory=root / "state",
        agent_home=root / "agents-home",
        claude_executable=str(executable),
        claude_login_file=login if configured else None,
    )
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    boundaries.agent_runtime.run(claude_request(tmp_path))

    [call] = read_calls(tmp_path / "bin")
    assert call.environment.get(LOGIN_VARIABLE) == expected
