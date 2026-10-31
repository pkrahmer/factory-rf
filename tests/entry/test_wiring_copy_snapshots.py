"""The wiring builds the copy snapshots for `FACTORY_SNAPSHOTS=copy` and the ZFS ones by default."""

from collections.abc import Callable
from pathlib import Path

import pytest

from factory.adapters.copy_snapshots import CopySnapshots
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.zfs_snapshots import ZfsSnapshots
from factory.application.boundaries import Boundaries
from factory.domain.errors import SettingsInvalid
from factory.domain.settings import SNAPSHOT_BASE_VARIABLE, InstanceSettings, read_settings
from factory.entry.wiring import build_boundaries, machine_extras
from podman_support import IMAGE, Podman
from settings_support import BASE, CONTAINER
from wiring_support import CONTAINER_ITEMS, CREDENTIAL


@pytest.fixture
def environment(tmp_path: Path) -> dict[str, str]:
    """The agent runs' environment."""
    return {"PATH": "/usr/bin", "HOME": str(tmp_path)}


@pytest.fixture
def copy_settings(tmp_path: Path, agent_home: Path, versioned_podman: Podman) -> InstanceSettings:
    """Settings of a copy instance: a workspace and a base that exist in `tmp_path`, no dataset."""
    root = tmp_path.resolve()
    (root / "work").mkdir()
    (root / "base").mkdir()
    return InstanceSettings(
        repository_url="/srv/project.git",
        instance="factory-1",
        checkout=root / "checkout",
        state_directory=root / "state",
        agent_home=agent_home,
        snapshots="copy",
        snapshot_base=root / "base",
        workspace=root / "work",
        stage_image=IMAGE,
        podman_executable=str(versioned_podman.path),
    )


def _settings_fields(
    _settings: InstanceSettings, _boundaries: Boundaries, _environment: dict[str, str]
) -> object:
    settings = read_settings({**BASE, **CONTAINER})
    return settings.snapshots, settings.snapshot_base


def _snapshots_type(
    settings: InstanceSettings, _boundaries: Boundaries, _environment: dict[str, str]
) -> object:
    return type(build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService()).snapshots)


def _item_names(
    settings: InstanceSettings, boundaries: Boundaries, environment: dict[str, str]
) -> object:
    return [check().name for check in machine_extras(boundaries, settings, environment)]


@pytest.mark.parametrize(
    ("observe", "expected"),
    [
        pytest.param(_settings_fields, ("zfs", None), id="settings-fields"),
        pytest.param(_snapshots_type, ZfsSnapshots, id="snapshots-type"),
        pytest.param(_item_names, [*CONTAINER_ITEMS, "agent-run-probe"], id="item-names"),
    ],
)
def test_without_the_snapshots_setting_the_instance_is_the_zfs_one_of_before(
    local_settings: InstanceSettings,
    boundaries: Boundaries,
    environment: dict[str, str],
    observe: Callable[[InstanceSettings, Boundaries, dict[str, str]], object],
    expected: object,
) -> None:
    assert observe(local_settings, boundaries, environment) == expected


def test_a_copy_instance_gets_copy_snapshots_on_its_workspace_and_base(
    copy_settings: InstanceSettings,
) -> None:
    workspace = copy_settings.workspace
    base = copy_settings.snapshot_base
    assert workspace is not None
    assert base is not None
    (workspace / "a.txt").write_text("one\n", encoding="utf-8")

    snapshots = build_boundaries(copy_settings, CREDENTIAL, hosting=FakeHostingService()).snapshots

    assert isinstance(snapshots, CopySnapshots)
    assert snapshots.mount_point == workspace
    snapshots.advance()
    assert (base / "a.txt").read_text(encoding="utf-8") == "one\n"


@pytest.mark.parametrize(
    "missing",
    [
        pytest.param({}, id="base"),
        pytest.param({"workspace": None}, id="base-and-workspace"),
        pytest.param({"stage_image": None}, id="base-and-stage-image"),
    ],
)
def test_a_copy_instance_without_a_base_names_the_base_first(
    copy_settings: InstanceSettings, missing: dict[str, object]
) -> None:
    settings = copy_settings.model_copy(update={"snapshot_base": None, **missing})

    with pytest.raises(SettingsInvalid) as raised:
        build_boundaries(settings, CREDENTIAL, hosting=FakeHostingService())

    assert (raised.value.variable, raised.value.fault) == (SNAPSHOT_BASE_VARIABLE, "missing")


def test_a_copy_instance_checks_its_snapshots_and_neither_zfs_nor_a_dataset(
    copy_settings: InstanceSettings, boundaries: Boundaries, environment: dict[str, str]
) -> None:
    names = [check().name for check in machine_extras(boundaries, copy_settings, environment)]

    assert {"podman", "snapshots", "stage-image", "agent-run-probe"} <= set(names)
    assert not {"zfs", "dataset"} & set(names)
