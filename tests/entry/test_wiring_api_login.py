"""The wiring hands the setting that names the API login file to the agent runtime."""

from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, claude_request, read_calls, write_stand_in
from adapters.test_agent_launch_login import API_LOGIN
from adapters.test_claude_runtime_login import REPLY
from factory.adapters.agent_launch import API_LOGIN_VARIABLE
from factory.adapters.fake_hosting import FakeHostingService
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from wiring_support import CREDENTIAL, with_dataset


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        pytest.param(True, API_LOGIN, id="api-login-file"),
        pytest.param(False, None, id="no-api-login-file"),
    ],
)
def test_the_built_runtime_hands_the_api_login_file_s_key_to_claude(
    tmp_path: Path, *, configured: bool, expected: str | None
) -> None:
    api_login = tmp_path / "api-login"
    api_login.write_text(f"{API_LOGIN}\n", encoding="utf-8")
    executable = write_stand_in(tmp_path / "bin", [Step(stdout=REPLY)])
    root = tmp_path.resolve()
    settings = with_dataset(
        InstanceSettings(
            repository_url="/srv/project.git",
            instance="factory-1",
            checkout=root / "checkout",
            state_directory=root / "state",
            agent_home=root / "agents-home",
            claude_executable=str(executable),
            api_login_file=api_login if configured else None,
        ),
        tmp_path,
    )
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    boundaries.agent_runtime.run(claude_request(tmp_path))

    [call] = read_calls(tmp_path / "bin")
    assert call.environment.get(API_LOGIN_VARIABLE) == expected
