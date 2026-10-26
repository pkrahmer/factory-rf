"""The settings read the dataset, the workspace and the stage image of the container environment."""

from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import InstanceSettings, read_settings
from settings_support import AGENT_HOME, BASE

CONTAINER = {
    "FACTORY_DATASET": "tank/factory/vm",
    "FACTORY_WORKSPACE": "/srv/factory/vm/work",
    "FACTORY_STAGE_IMAGE": "factory-stage:1",
}
WORKSPACE = Path("/srv/factory/vm/work")
_UNSET = object()


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        pytest.param(
            CONTAINER,
            {
                "dataset": "tank/factory/vm",
                "workspace": WORKSPACE,
                "stage_image": "factory-stage:1",
                "podman_executable": "podman",
                "zfs_executable": "zfs",
            },
            id="container",
        ),
        pytest.param(
            {
                **CONTAINER,
                "FACTORY_PODMAN": "/usr/bin/podman",
                "FACTORY_ZFS": "/usr/local/bin/factory-zfs",
            },
            {
                "podman_executable": "/usr/bin/podman",
                "zfs_executable": "/usr/local/bin/factory-zfs",
            },
            id="executables",
        ),
        pytest.param(
            {**CONTAINER, "FACTORY_PODMAN": "  ", "FACTORY_ZFS": ""},
            {"podman_executable": "podman", "zfs_executable": "zfs"},
            id="blank-executables",
        ),
        pytest.param(
            {
                **CONTAINER,
                "FACTORY_DATASET": " tank/factory/vm ",
                "FACTORY_WORKSPACE": " /srv/factory/vm/work ",
                "FACTORY_STAGE_IMAGE": " factory-stage:1 ",
            },
            {
                "dataset": "tank/factory/vm",
                "workspace": WORKSPACE,
                "stage_image": "factory-stage:1",
            },
            id="padded-values",
        ),
    ],
)
def test_read_settings_reads_the_stage_environment_and_its_values(
    extra: dict[str, str], expected: dict[str, object]
) -> None:
    settings = read_settings({**BASE, **extra})

    assert {name: getattr(settings, name) for name in expected} == expected


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        pytest.param(
            {**CONTAINER, "FACTORY_WORKSPACE": "srv/work"},
            ("FACTORY_WORKSPACE", "is not an absolute path"),
            id="relative-workspace",
        ),
        pytest.param(
            {"FACTORY_DATASET": "tank/factory/vm", "FACTORY_WORKSPACE": "srv/work"},
            ("FACTORY_WORKSPACE", "is not an absolute path"),
            id="relative-workspace-before-no-image",
        ),
        pytest.param({}, {"dataset": None, "workspace": None, "stage_image": None}, id="none"),
        pytest.param(
            {**CONTAINER, "FACTORY_DATASET": "  ", "FACTORY_STAGE_IMAGE": "  "},
            {"dataset": None, "stage_image": None},
            id="blank-values",
        ),
    ],
)
def test_read_settings_runs_a_container_only_with_its_values_and_inline_with_any(
    extra: dict[str, str], expected: tuple[str, str] | dict[str, object]
) -> None:
    if isinstance(expected, tuple):
        with pytest.raises(SettingsInvalid) as raised:
            read_settings({**BASE, **extra})
        assert (raised.value.variable, raised.value.fault) == expected
        return
    settings = read_settings({**BASE, **extra})

    assert {name: getattr(settings, name) for name in expected} == expected


_DIRECT_CONTAINER: dict[str, object] = {
    "repository_url": "/srv/project.git",
    "instance": "factory-1",
    "agent_home": AGENT_HOME,
    "dataset": "tank/factory/vm",
    "workspace": WORKSPACE,
    "stage_image": "factory-stage:1",
}


@pytest.mark.parametrize(
    ("changes", "accepted"),
    [
        pytest.param({}, True, id="container"),
        pytest.param({"workspace": Path("srv/work")}, False, id="relative-workspace"),
        pytest.param(
            {"dataset": _UNSET, "workspace": _UNSET, "stage_image": _UNSET}, True, id="none"
        ),
    ],
)
def test_instance_settings_built_directly_follow_the_stage_environment_rules(
    changes: dict[str, object], *, accepted: bool
) -> None:
    fields = {**_DIRECT_CONTAINER, **changes}
    arguments = {name: value for name, value in fields.items() if value is not _UNSET}
    model: type[BaseModel] = InstanceSettings

    if accepted:
        model(**arguments)
        return
    with pytest.raises(ValidationError):
        model(**arguments)
