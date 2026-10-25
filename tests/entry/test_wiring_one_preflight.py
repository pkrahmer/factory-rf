"""The preflight has one list of items, no runtime on the host and only opencode's aliases."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.application.boundaries import Boundaries
from factory.application.preflight import MachineChecks, opencode_item
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import machine_extras
from podman_support import IMAGE, Podman
from wiring_support import CONTAINER_ITEMS, every_tool
from zfs_support import DATASET, Zfs

FIRST_ITEMS = ["tool:git", "tool:uv", "hosting-service", "agents", "agent-runtime-version"]
SONNET = {"sonnet": "anthropic/claude-sonnet-5-5"}


@pytest.fixture
def settings(
    tmp_path: Path, agent_home: Path, versioned_podman: Podman, listing_zfs: Zfs
) -> InstanceSettings:
    """A container instance's settings, its stand-in tools and its workspace under `tmp_path`."""
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        state_directory=tmp_path / "state",
        agent_home=agent_home,
        workspace=workspace,
        dataset=DATASET,
        stage_image=IMAGE,
        podman_executable=str(versioned_podman.path),
        zfs_executable=str(listing_zfs.path),
        pinned_agent_version="fake",
        pinned_opencode_version="fake",
    )


def _extras_under(runtime: str, names: list[str]) -> Callable[[Boundaries, InstanceSettings], None]:
    def check(boundaries: Boundaries, settings: InstanceSettings) -> None:
        chosen = settings.model_copy(update={"agent_runtime": runtime})
        environment = {"PATH": "/usr/bin", "HOME": "/home/factory"}

        extras = machine_extras(boundaries, chosen, environment)

        assert [extra().name for extra in extras] == names

    return check


def _machine_checks(runtime: str) -> Callable[[Boundaries, InstanceSettings], None]:
    def check(boundaries: Boundaries, settings: InstanceSettings) -> None:
        asked: list[str] = []

        def which(name: str) -> str | None:
            asked.append(name)
            return every_tool(name)

        chosen = settings.model_copy(update={"agent_runtime": runtime})

        report = MachineChecks(boundaries, chosen, which).run()

        assert [item.name for item in report.items][: len(FIRST_ITEMS)] == FIRST_ITEMS
        assert not {"make", "claude", "opencode"} & set(asked)

    return check


def _opencode_aliases(models: dict[str, str], detail: str | None) -> Callable[..., None]:
    def check(_boundaries: Boundaries, settings: InstanceSettings) -> None:
        chosen = settings.model_copy(
            update={"agent_runtime": "opencode", "opencode_models": models}
        )

        item = opencode_item(chosen, ["sonnet"])

        assert item.name == "opencode"
        assert item.passed == (detail is None)
        assert item.detail == ("" if detail is None else detail)

    return check


@pytest.mark.parametrize(
    "check",
    [
        pytest.param(
            _extras_under("claude", [*CONTAINER_ITEMS, "agent-run-probe"]), id="extras-claude"
        ),
        pytest.param(
            _extras_under("opencode", [*CONTAINER_ITEMS, "opencode", "agent-run-probe"]),
            id="extras-opencode",
        ),
        pytest.param(_machine_checks("claude"), id="machine-checks-claude"),
        pytest.param(_machine_checks("opencode"), id="machine-checks-opencode"),
        pytest.param(_opencode_aliases(SONNET, None), id="opencode-mapped"),
        pytest.param(
            _opencode_aliases({}, "no model is set for sonnet in FACTORY_OPENCODE_MODELS"),
            id="opencode-unmapped",
        ),
    ],
)
def test_the_preflight_checks_the_one_environment_s_items(
    installed: Boundaries,
    settings: InstanceSettings,
    check: Callable[[Boundaries, InstanceSettings], None],
) -> None:
    check(installed, settings)
