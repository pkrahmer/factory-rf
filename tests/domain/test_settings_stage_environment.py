"""The settings name the stage environment, and a container environment its dataset and image."""

from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import InstanceSettings, read_settings
from settings_support import BASE

CONTAINER = {
    "FACTORY_STAGE_ENVIRONMENT": "container",
    "FACTORY_DATASET": "tank/factory/vm",
    "FACTORY_WORKSPACE": "/srv/factory/vm/work",
    "FACTORY_STAGE_IMAGE": "factory-stage:1",
}
WORKSPACE = Path("/srv/factory/vm/work")
_UNSET = object()


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        pytest.param({}, {"stage_environment": "inline"}, id="unset"),
        pytest.param(
            {"FACTORY_STAGE_ENVIRONMENT": ""}, {"stage_environment": "inline"}, id="empty"
        ),
        pytest.param(
            {"FACTORY_STAGE_ENVIRONMENT": "  inline "},
            {"stage_environment": "inline"},
            id="inline-padded",
        ),
        pytest.param(
            CONTAINER,
            {
                "stage_environment": "container",
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
    ("extra", "variable", "fault"),
    [
        pytest.param(
            {"FACTORY_STAGE_ENVIRONMENT": "Container"},
            "FACTORY_STAGE_ENVIRONMENT",
            "holds Container, which is neither inline nor container",
            id="unknown-environment",
        ),
        pytest.param(
            {"FACTORY_STAGE_ENVIRONMENT": "container"},
            "FACTORY_DATASET",
            "missing for the container environment",
            id="no-dataset",
        ),
        pytest.param(
            {**CONTAINER, "FACTORY_DATASET": "  "},
            "FACTORY_DATASET",
            "missing for the container environment",
            id="blank-dataset",
        ),
        pytest.param(
            {"FACTORY_STAGE_ENVIRONMENT": "container", "FACTORY_DATASET": "tank/factory/vm"},
            "FACTORY_WORKSPACE",
            "missing for the container environment",
            id="no-workspace",
        ),
        pytest.param(
            {**CONTAINER, "FACTORY_WORKSPACE": "srv/work"},
            "FACTORY_WORKSPACE",
            "is not an absolute path",
            id="relative-workspace",
        ),
        pytest.param(
            {
                "FACTORY_STAGE_ENVIRONMENT": "container",
                "FACTORY_DATASET": "tank/factory/vm",
                "FACTORY_WORKSPACE": "/srv/factory/vm/work",
            },
            "FACTORY_STAGE_IMAGE",
            "missing for the container environment",
            id="no-image",
        ),
        pytest.param(
            {**CONTAINER, "FACTORY_AGENT_USER": "agent"},
            "FACTORY_AGENT_USER",
            "is set, but the container environment runs no second user",
            id="agent-user",
        ),
    ],
)
def test_read_settings_refuses_a_stage_environment_it_cannot_run(
    extra: dict[str, str], variable: str, fault: str
) -> None:
    with pytest.raises(SettingsInvalid) as raised:
        read_settings({**BASE, **extra})

    assert (raised.value.variable, raised.value.fault) == (variable, fault)


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        pytest.param({"FACTORY_STAGE_ENVIRONMENT": "inline"}, {"dataset": None}, id="none"),
        pytest.param(
            {
                "FACTORY_STAGE_ENVIRONMENT": "inline",
                "FACTORY_AGENT_USER": "agent",
                "FACTORY_DATASET": "tank/x",
            },
            {"agent_user": "agent", "dataset": "tank/x"},
            id="agent-user-and-dataset",
        ),
        pytest.param(
            {"FACTORY_STAGE_ENVIRONMENT": "inline", "FACTORY_WORKSPACE": "srv/work"},
            {"workspace": Path("srv/work")},
            id="relative-workspace",
        ),
    ],
)
def test_read_settings_accepts_any_values_for_the_inline_environment(
    extra: dict[str, str], expected: dict[str, object]
) -> None:
    settings = read_settings({**BASE, **extra})

    assert settings.stage_environment == "inline"
    assert {name: getattr(settings, name) for name in expected} == expected


_DIRECT_CONTAINER: dict[str, object] = {
    "repository_url": "/srv/project.git",
    "instance": "factory-1",
    "stage_environment": "container",
    "dataset": "tank/factory/vm",
    "workspace": WORKSPACE,
    "stage_image": "factory-stage:1",
}


@pytest.mark.parametrize(
    ("changes", "accepted"),
    [
        pytest.param({}, True, id="container"),
        pytest.param({"dataset": _UNSET}, False, id="no-dataset"),
        pytest.param({"workspace": _UNSET}, False, id="no-workspace"),
        pytest.param({"stage_image": _UNSET}, False, id="no-image"),
        pytest.param({"workspace": Path("srv/work")}, False, id="relative-workspace"),
        pytest.param({"agent_user": "agent"}, False, id="agent-user"),
        pytest.param({"stage_environment": "podman"}, False, id="unknown-environment"),
        pytest.param(
            {
                "stage_environment": "inline",
                "dataset": _UNSET,
                "workspace": _UNSET,
                "stage_image": _UNSET,
            },
            True,
            id="inline",
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
