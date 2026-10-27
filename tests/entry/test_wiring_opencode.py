"""The wiring builds the runtime the instance names and the preflight items it needs."""

import json
from pathlib import Path

import pytest

from adapters.opencode_stand_in import (
    REPLY_EVENTS,
    error,
    opencode_request,
    stdout,
    step_start,
    write_agent_settings,
)
from agent_login_support import API_LOGIN
from factory.adapters.agent_launch import LoginFiles, login_argv
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.opencode_runtime import CONFIG_VARIABLE, OpencodeRuntime
from factory.application.boundaries import Boundaries
from factory.domain.provider_limits import ProviderLimit
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries, machine_extras
from podman_support import PodmanPlan
from wiring_support import (
    CONTAINER_ITEMS,
    CREDENTIAL,
    after_image,
    dataset_podman,
    run_words,
    with_dataset,
)

LIMIT_REPLY = stdout(step_start(), error("limit reached", status_code=429))
DENY_PUSH = json.dumps({"permissions": {"allow": [], "deny": ["Bash(git push*)"]}})


@pytest.mark.parametrize(
    ("runtime", "expected"),
    [
        pytest.param("opencode", OpencodeRuntime, id="opencode"),
        pytest.param("claude", ClaudeCodeRuntime, id="claude"),
    ],
)
def test_the_built_runtime_is_the_one_the_instance_names(
    local_settings: InstanceSettings, runtime: str, expected: type[object]
) -> None:
    boundaries = build_boundaries(
        local_settings.model_copy(update={"agent_runtime": runtime}),
        CREDENTIAL,
        hosting=FakeHostingService(),
    )

    assert type(boundaries.agent_runtime) is expected


@pytest.mark.parametrize(
    ("reply", "end_reason"),
    [
        pytest.param(REPLY_EVENTS, "completed", id="reply"),
        pytest.param(LIMIT_REPLY, "provider_limit", id="limit-status"),
    ],
)
def test_the_built_opencode_runtime_runs_with_the_instance_s_models_denies_key_and_limit(
    tmp_path: Path, local_settings: InstanceSettings, reply: str, end_reason: str
) -> None:
    executable = "/usr/local/bin/opencode"
    api_login = tmp_path / "api-login"
    api_login.write_text(f"{API_LOGIN}\n", encoding="utf-8")
    settings = local_settings.model_copy(
        update={
            "agent_runtime": "opencode",
            "opencode_executable": executable,
            "opencode_models": {"sonnet": "anthropic/claude-sonnet-5-5"},
            "api_login_file": api_login,
            "provider_limit": ProviderLimit(status=429),
        }
    )
    write_agent_settings(settings.agent_home, DENY_PUSH)
    runs = settings.state_directory / "runs"
    runs.mkdir(parents=True)
    podman = dataset_podman(tmp_path, PodmanPlan(stdout=reply))
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    result = boundaries.agent_runtime.run(opencode_request(tmp_path / "work"))

    words = run_words(podman)
    command = after_image(words)
    start = command.index(executable)
    [config_word] = [word for word in words if word.startswith(f"{CONFIG_VARIABLE}=")]
    config_path = Path(config_word.removeprefix(f"{CONFIG_VARIABLE}="))
    assert command[command.index("--model") + 1] == "anthropic/claude-sonnet-5-5"
    assert f"{config_path}:{config_path}:ro" in words
    assert config_path.parent == runs
    assert command[:start] == login_argv(LoginFiles(api=api_login))
    assert f"{api_login}:{api_login}:ro" in words
    assert not any(API_LOGIN in word for word in words)
    assert result.end_reason == end_reason


@pytest.mark.parametrize(
    ("runtime", "names"),
    [
        pytest.param("opencode", [*CONTAINER_ITEMS, "opencode"], id="opencode-no-agent-user"),
        pytest.param("claude", CONTAINER_ITEMS, id="claude-no-agent-user"),
    ],
)
def test_the_opencode_item_comes_after_confinement_only_under_opencode(
    boundaries: Boundaries,
    tmp_path: Path,
    agent_home: Path,
    *,
    runtime: str,
    names: list[str],
) -> None:
    settings = with_dataset(
        InstanceSettings.model_validate(
            {
                "repository_url": "/srv/project.git",
                "instance": "factory-1",
                "state_directory": tmp_path / "state",
                "agent_home": agent_home,
                "agent_runtime": runtime,
            }
        ),
        tmp_path,
    )
    environment = {"PATH": "/usr/bin", "HOME": str(tmp_path)}

    extras = machine_extras(boundaries, settings, environment)

    assert [check().name for check in extras] == [*names, "agent-run-probe"]
