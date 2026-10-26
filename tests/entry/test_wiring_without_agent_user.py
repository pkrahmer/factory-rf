"""The wiring builds an instance without a second user: no `sudo`, no agent user, no shared git."""

import os
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.make_commands import ContainerMakeCommands
from factory.application.boundaries import Boundaries
from factory.application.preflight import agent_run_probe_item
from factory.application.project_commands import RecordingProjectCommands
from factory.domain.agent_runs import AgentRunResult
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import (
    CREDENTIAL_HELPER,
    build_boundaries,
    git_environment,
    machine_extras,
)
from git_support import install_agents
from podman_support import IMAGE, Podman
from probe_support import ENVIRONMENT
from wiring_support import CONTAINER_ITEMS, CREDENTIAL
from zfs_support import DATASET, Zfs

CONTAINER_PROBED_ITEMS = [*CONTAINER_ITEMS, "agent-run-probe"]


@pytest.fixture
def settings_of(
    tmp_path: Path, agent_home: Path, versioned_podman: Podman, listing_zfs: Zfs
) -> InstanceSettings:
    """Settings of an instance whose paths and tools lie in `tmp_path`."""
    root = tmp_path.resolve()
    workspace = root / "workspace"
    workspace.mkdir(exist_ok=True)
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=root / "checkout",
        state_directory=root / "state",
        agent_home=agent_home,
        workspace=workspace,
        dataset=DATASET,
        stage_image=IMAGE,
        podman_executable=str(versioned_podman.path),
        zfs_executable=str(listing_zfs.path),
        pinned_agent_version="fake",
    )


def test_git_environment_holds_the_credential_helper_and_no_hooks_alone() -> None:
    assert git_environment() == {
        "GIT_CONFIG_COUNT": "3",
        "GIT_CONFIG_KEY_0": "credential.helper",
        "GIT_CONFIG_VALUE_0": CREDENTIAL_HELPER,
        "GIT_CONFIG_KEY_1": "core.hooksPath",
        "GIT_CONFIG_VALUE_1": os.devnull,
        "GIT_CONFIG_KEY_2": "core.fsmonitor",
        "GIT_CONFIG_VALUE_2": "false",
    }


@pytest.mark.parametrize(
    ("fields", "names"),
    [
        pytest.param({}, CONTAINER_PROBED_ITEMS, id="claude"),
        pytest.param(
            {"agent_runtime": "opencode"},
            [*CONTAINER_ITEMS, "opencode", "agent-run-probe"],
            id="opencode",
        ),
    ],
)
def test_the_extras_name_no_agent_user_and_no_sudo(
    boundaries: Boundaries,
    settings_of: InstanceSettings,
    *,
    fields: dict[str, object],
    names: list[str],
) -> None:
    settings = settings_of.model_copy(update=fields)

    extras = machine_extras(boundaries, settings, ENVIRONMENT)

    assert [check().name for check in extras] == names


@pytest.mark.parametrize(
    ("fields", "login", "said"),
    [
        pytest.param(
            {}, None, ["run claude -p by hand as the factory user to see why"], id="claude"
        ),
        pytest.param(
            {"agent_runtime": "opencode", "pinned_opencode_version": "1.19.3"},
            "none",
            [
                "by hand as the factory user",
                "put a key in the file FACTORY_API_LOGIN_FILE names",
            ],
            id="opencode-no-login",
        ),
    ],
)
def test_a_died_probe_names_the_factory_user(
    boundaries: Boundaries,
    settings_of: InstanceSettings,
    agent_runtime: FakeAgentRuntime,
    agent_home: Path,
    *,
    fields: dict[str, object],
    login: str | None,
    said: list[str],
) -> None:
    install_agents(agent_home, ["coder"])
    settings = settings_of.model_copy(update=fields)
    agent_runtime.queue(
        ScriptedRun(
            result=AgentRunResult.model_validate(
                {"end_reason": "died", "duration": timedelta(seconds=5), "login": login}
            )
        )
    )

    item = agent_run_probe_item(boundaries, settings, ENVIRONMENT)

    assert not item.passed
    for words in said:
        assert words in item.detail


def test_the_project_commands_run_without_a_user(settings_of: InstanceSettings) -> None:
    boundaries = build_boundaries(settings_of, CREDENTIAL, hosting=FakeHostingService())

    commands = boundaries.project_commands
    assert isinstance(commands, RecordingProjectCommands)
    assert type(commands.inner) is ContainerMakeCommands
