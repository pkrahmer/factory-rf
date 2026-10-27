"""The wiring builds only container instances: their three settings, the agent's home."""

from pathlib import Path

import pytest

from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.make_commands import ContainerMakeCommands
from factory.adapters.opencode_runtime import OpencodeRuntime
from factory.adapters.podman_runs import PodmanRuns
from factory.adapters.zfs_snapshots import ZfsSnapshots
from factory.application.project_commands import RecordingProjectCommands
from factory.domain.errors import SettingsInvalid
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import agent_run_environment, build_boundaries
from podman_support import IMAGE, Podman
from wiring_support import CREDENTIAL, HOSTED_URL, _record_get_repo
from zfs_support import DATASET, Zfs


@pytest.fixture
def complete_settings(
    tmp_path: Path, versioned_podman: Podman, listing_zfs: Zfs
) -> InstanceSettings:
    """Settings with a dataset, a workspace under `tmp_path` and an image, the stand-ins' tools."""
    root = tmp_path.resolve()
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=root / "checkout",
        state_directory=root / "state",
        agent_home=root / "agents-home",
        dataset=DATASET,
        workspace=root / "work",
        stage_image=IMAGE,
        zfs_executable=str(listing_zfs.path),
        podman_executable=str(versioned_podman.path),
    )


@pytest.mark.parametrize(
    ("changes", "hosted", "variable"),
    [
        pytest.param({"dataset": None}, True, "FACTORY_DATASET", id="no-dataset"),
        pytest.param({"workspace": None}, True, "FACTORY_WORKSPACE", id="no-workspace"),
        pytest.param(
            {"workspace": None, "stage_image": None},
            True,
            "FACTORY_WORKSPACE",
            id="workspace-before-image",
        ),
        pytest.param(
            {"dataset": None, "workspace": None, "stage_image": None},
            True,
            "FACTORY_DATASET",
            id="dataset-before-workspace-and-image",
        ),
        pytest.param({"stage_image": None}, True, "FACTORY_STAGE_IMAGE", id="no-image"),
        pytest.param(
            {"dataset": None, "repository_url": HOSTED_URL},
            False,
            "FACTORY_DATASET",
            id="no-dataset-before-pygithub",
        ),
        pytest.param({}, True, None, id="complete"),
    ],
)
def test_build_boundaries_needs_the_dataset_the_workspace_and_the_image(
    monkeypatch: pytest.MonkeyPatch,
    complete_settings: InstanceSettings,
    *,
    versioned_podman: Podman,
    listing_zfs: Zfs,
    changes: dict[str, object],
    hosted: bool,
    variable: str | None,
) -> None:
    repositories = _record_get_repo(monkeypatch)
    settings = complete_settings.model_copy(update=changes)
    hosting = FakeHostingService() if hosted else None

    if variable is not None:
        with pytest.raises(SettingsInvalid) as raised:
            build_boundaries(settings, CREDENTIAL, hosting=hosting)
        assert (raised.value.variable, raised.value.fault) == (variable, "missing")
        assert repositories == []
        return
    boundaries = build_boundaries(settings, CREDENTIAL, hosting=hosting)

    assert isinstance(boundaries.snapshots, ZfsSnapshots)
    assert isinstance(boundaries.containers, PodmanRuns)
    runtime = boundaries.agent_runtime
    assert isinstance(runtime, ClaudeCodeRuntime | OpencodeRuntime)
    assert runtime.containers is boundaries.containers
    project_commands = boundaries.project_commands
    assert isinstance(project_commands, RecordingProjectCommands)
    assert isinstance(project_commands.inner, ContainerMakeCommands)
    assert listing_zfs.calls() == []
    assert versioned_podman.calls() == []


def test_the_agent_run_s_home_is_the_dataset_s(complete_settings: InstanceSettings) -> None:
    base = {"HOME": "/home/x", "PATH": "/usr/bin", "LANG": "C.UTF-8"}

    environment = agent_run_environment(complete_settings, base)

    assert environment == {"HOME": "/work/home", "PATH": "/usr/bin", "LANG": "C.UTF-8"}
    assert base == {"HOME": "/home/x", "PATH": "/usr/bin", "LANG": "C.UTF-8"}
