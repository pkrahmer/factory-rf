"""The wiring hands the setting that names the API login file to the agent runtime."""

from pathlib import Path

import pytest

from adapters.claude_stand_in import claude_request
from adapters.test_agent_launch_login import API_LOGIN
from adapters.test_claude_runtime_login import REPLY
from factory.adapters.agent_launch import LoginFiles, login_argv
from factory.adapters.fake_hosting import FakeHostingService
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from podman_support import PodmanPlan
from wiring_support import CREDENTIAL, after_image, dataset_podman, run_words, with_dataset


@pytest.mark.parametrize(
    "configured",
    [
        pytest.param(True, id="api-login-file"),
        pytest.param(False, id="no-api-login-file"),
    ],
)
def test_the_built_runtime_hands_the_api_login_file_s_key_to_claude(
    tmp_path: Path, *, configured: bool
) -> None:
    api_login = tmp_path / "api-login"
    api_login.write_text(f"{API_LOGIN}\n", encoding="utf-8")
    executable = "/usr/local/bin/claude"
    root = tmp_path.resolve()
    settings = with_dataset(
        InstanceSettings(
            repository_url="/srv/project.git",
            instance="factory-1",
            checkout=root / "checkout",
            state_directory=root / "state",
            agent_home=root / "agents-home",
            claude_executable=executable,
            api_login_file=api_login if configured else None,
        ),
        tmp_path,
    )
    podman = dataset_podman(tmp_path, PodmanPlan(stdout=REPLY))
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    boundaries.agent_runtime.run(claude_request(tmp_path))

    words = run_words(podman)
    command = after_image(words)
    start = command.index(executable)
    assert command[:start] == login_argv(LoginFiles(api=api_login if configured else None))
    assert (f"{api_login}:{api_login}:ro" in words) is configured
    assert not any(API_LOGIN in word for word in words)
