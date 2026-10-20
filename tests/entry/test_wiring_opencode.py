"""The wiring builds the runtime the instance names and the preflight items it needs."""

import json
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step, read_calls
from adapters.opencode_stand_in import (
    REPLY_EVENTS,
    error,
    opencode_request,
    stdout,
    step_start,
    write_agent_settings,
    write_opencode,
)
from adapters.test_agent_launch_login import API_LOGIN
from confine_support import ConfineCall, Layout, read_records, run_request, write_confine
from factory.adapters.agent_launch import API_LOGIN_VARIABLE
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.opencode_runtime import CONFIG_VARIABLE, OpencodeRuntime
from factory.application.boundaries import Boundaries
from factory.domain.confinement import Confinement
from factory.domain.provider_limits import ProviderLimit
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries, machine_extras
from wiring_support import CREDENTIAL, every_tool

LIMIT_REPLY = stdout(step_start(), error("limit reached", status_code=429))
DENY_PUSH = json.dumps({"permissions": {"allow": [], "deny": ["Bash(git push*)"]}})
OPENCODE_THREE = [".local/share/opencode", ".local/state/opencode", ".cache/opencode"]


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
        confine_executable=None,
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
    executable = write_opencode(tmp_path / "bin", [Step(stdout=reply)])
    api_login = tmp_path / "api-login"
    api_login.write_text(f"{API_LOGIN}\n", encoding="utf-8")
    settings = local_settings.model_copy(
        update={
            "agent_runtime": "opencode",
            "opencode_executable": str(executable),
            "opencode_models": {"sonnet": "anthropic/claude-sonnet-5-5"},
            "api_login_file": api_login,
            "provider_limit": ProviderLimit(status=429),
        }
    )
    write_agent_settings(settings.agent_home, DENY_PUSH)
    runs = settings.state_directory / "runs"
    runs.mkdir(parents=True)
    boundaries = build_boundaries(
        settings, CREDENTIAL, hosting=FakeHostingService(), confine_executable=None
    )

    result = boundaries.agent_runtime.run(opencode_request(tmp_path / "work"))

    [call] = read_calls(tmp_path / "bin")
    config_path = Path(call.environment[CONFIG_VARIABLE])
    config = json.loads(call.files[str(config_path)])
    arguments = call.arguments
    assert arguments[arguments.index("--model") + 1] == "anthropic/claude-sonnet-5-5"
    assert config["agent"]["factory-coder"]["permission"]["bash"]["git push*"] == "deny"
    assert call.environment.get(API_LOGIN_VARIABLE) == API_LOGIN
    assert config_path.parent == runs
    assert result.end_reason == end_reason


@pytest.mark.parametrize(
    ("folders", "expected"),
    [
        pytest.param([".config/sso-opencode"], [*OPENCODE_THREE, ".config/sso-opencode"], id="set"),
        pytest.param([], OPENCODE_THREE, id="unset"),
    ],
)
def test_the_built_opencode_runtime_allows_the_instance_s_folders_after_opencode_s(
    local_settings: InstanceSettings, layout: Layout, folders: list[str], expected: list[str]
) -> None:
    confine = write_confine(layout)
    executable = write_opencode(layout.stand_in, [Step(stdout=REPLY_EVENTS)])
    settings = local_settings.model_copy(
        update={
            "checkout": layout.checkout,
            "agent_runtime": "opencode",
            "opencode_executable": str(executable),
            "opencode_models": {"sonnet": "anthropic/claude-sonnet-5-5"},
            "opencode_folders": folders,
        }
    )
    write_agent_settings(settings.agent_home, DENY_PUSH)
    (settings.state_directory / "runs").mkdir(parents=True)
    boundaries = build_boundaries(
        settings, CREDENTIAL, hosting=FakeHostingService(), confine_executable=str(confine)
    )

    boundaries.agent_runtime.run(run_request(layout))

    [confined] = read_records(layout.confine_bin / "confine-calls.jsonl", ConfineCall)
    rules = Confinement.model_validate_json(confined.rules_text)
    in_home = [folder for folder in rules.folders if folder.is_relative_to(layout.home)]
    assert in_home == [layout.home / folder for folder in expected]


SUDO = ["tool:sudo"]


@pytest.mark.parametrize(
    ("runtime", "agent_user", "names"),
    [
        pytest.param(
            "opencode",
            "agent",
            ["token-file", "agent-user", *SUDO, "agent-environment", "confinement", "opencode"],
            id="opencode-agent-user",
        ),
        pytest.param(
            "opencode",
            None,
            ["token-file", "agent-user", "agent-environment", "confinement", "opencode"],
            id="opencode-no-agent-user",
        ),
        pytest.param(
            "claude",
            "agent",
            ["token-file", "agent-user", *SUDO, "agent-environment", "confinement"],
            id="claude-agent-user",
        ),
        pytest.param(
            "claude",
            None,
            ["token-file", "agent-user", "agent-environment", "confinement"],
            id="claude-no-agent-user",
        ),
    ],
)
def test_the_opencode_item_comes_after_confinement_only_under_opencode(
    boundaries: Boundaries,
    tmp_path: Path,
    agent_home: Path,
    *,
    runtime: str,
    agent_user: str | None,
    names: list[str],
) -> None:
    settings = InstanceSettings.model_validate(
        {
            "repository_url": "/srv/project.git",
            "instance": "factory-1",
            "state_directory": tmp_path / "state",
            "agent_home": agent_home,
            "agent_user": agent_user,
            "agent_runtime": runtime,
        }
    )
    environment = {"PATH": "/usr/bin", "HOME": str(tmp_path)}

    extras = machine_extras(boundaries, settings, every_tool, environment)

    assert [check().name for check in extras] == [*names, "agent-run-probe"]
