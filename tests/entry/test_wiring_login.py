"""The wiring hands the setting that names the login file to the agent runtime."""

from pathlib import Path

import pytest

from adapters.claude_stand_in import REPLY, claude_request
from factory.adapters.agent_launch import LoginFiles, login_argv
from factory.adapters.fake_hosting import FakeHostingService
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from podman_support import PodmanPlan
from wiring_support import CREDENTIAL, after_image, dataset_podman, run_words, with_dataset

LOGIN = "stand-in-login"


@pytest.mark.parametrize(
    "configured",
    [pytest.param(True, id="login-file"), pytest.param(False, id="no-login-file")],
)
def test_the_built_runtime_hands_the_login_file_s_token_to_claude(
    tmp_path: Path, *, configured: bool
) -> None:
    login = tmp_path / "claude-login"
    login.write_text(f"{LOGIN}\n", encoding="utf-8")
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
            claude_login_file=login if configured else None,
        ),
        tmp_path,
    )
    podman = dataset_podman(tmp_path, PodmanPlan(stdout=REPLY))
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    boundaries.agent_runtime.run(claude_request(tmp_path))

    words = run_words(podman)
    command = after_image(words)
    start = command.index(executable)
    files = LoginFiles(subscription=login if configured else None)
    assert command[:start] == login_argv(files)
    assert (f"{login}:{login}:ro" in words) is configured
    assert not any(LOGIN in word for word in words)
