"""The wiring builds an instance without a second user: no `sudo`, no agent user, no shared git."""

import os
from datetime import timedelta
from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.make_commands import ContainerMakeCommands, MakeProjectCommands
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
from podman_support import IMAGE, Podman, PodmanPlan, write_podman
from probe_support import ENVIRONMENT
from wiring_support import CREDENTIAL
from zfs_support import DATASET, Answer, Zfs, write_zfs

CONTAINER_ITEMS = ["token-file", "podman", "zfs", "dataset", "stage-image", "agent-run-probe"]


@pytest.fixture
def podman(tmp_path: Path) -> Podman:
    """The stand-in `podman`, printing its version and exiting 0 for every call."""
    folder = tmp_path / "podman-bin"
    folder.mkdir()
    return write_podman(folder, PodmanPlan(stdout="podman version 4.9.3\n"))


@pytest.fixture
def zfs(tmp_path: Path) -> Zfs:
    """The stand-in `zfs`, answering `--version` and naming the dataset for `list`."""
    folder = tmp_path / "zfs-bin"
    folder.mkdir()
    return write_zfs(
        folder,
        {"--version": Answer(stdout="zfs-2.2.2\n"), "list": Answer(stdout=f"{DATASET}\n")},
    )


@pytest.fixture
def settings_of(tmp_path: Path, agent_home: Path, podman: Podman, zfs: Zfs) -> InstanceSettings:
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
        podman_executable=str(podman.path),
        zfs_executable=str(zfs.path),
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
        pytest.param(
            {}, ["token-file", "agent-environment", "agent-run-probe"], id="inline-claude"
        ),
        pytest.param(
            {"agent_runtime": "opencode"},
            ["token-file", "agent-environment", "opencode", "agent-run-probe"],
            id="inline-opencode",
        ),
        pytest.param({"stage_environment": "container"}, CONTAINER_ITEMS, id="container"),
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
            ["by hand as the factory user", "log in once as the factory user"],
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


@pytest.mark.parametrize(
    ("fields", "inner"),
    [
        pytest.param({}, MakeProjectCommands, id="inline"),
        pytest.param({"stage_environment": "container"}, ContainerMakeCommands, id="container"),
    ],
)
def test_the_project_commands_run_without_a_user(
    settings_of: InstanceSettings, *, fields: dict[str, object], inner: type[object]
) -> None:
    settings = settings_of.model_copy(update=fields)

    boundaries = build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    commands = boundaries.project_commands
    assert isinstance(commands, RecordingProjectCommands)
    assert type(commands.inner) is inner
