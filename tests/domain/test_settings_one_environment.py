"""The settings read no stage environment; a workspace keeps its faults."""

from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import ValidationError

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import InstanceSettings, read_settings, workspace_overlap_fault
from settings_support import AGENT_HOME, BASE

CONTAINER = {
    "FACTORY_DATASET": "tank/factory/vm",
    "FACTORY_WORKSPACE": "/srv/factory/vm/work",
    "FACTORY_STAGE_IMAGE": "factory-stage:1",
}
STAGE_ENVIRONMENT = "FACTORY_STAGE_ENVIRONMENT"
WORKSPACE = Path("/srv/work")
INNER_CHECKOUT = WORKSPACE / "checkout"
INNER_STATE = WORKSPACE / "state"
OUTER_CHECKOUT = Path("/srv/checkout")
OUTER_STATE = Path("/srv/state")


@pytest.mark.parametrize(
    ("environ", "fault"),
    [
        pytest.param({**BASE, **CONTAINER, STAGE_ENVIRONMENT: "inline"}, None, id="inline"),
        pytest.param({**BASE, **CONTAINER, STAGE_ENVIRONMENT: "podman"}, None, id="podman"),
        pytest.param({**BASE, **CONTAINER}, None, id="unset"),
        pytest.param(
            {**BASE, **CONTAINER, "FACTORY_WORKSPACE": "srv/work"},
            ("FACTORY_WORKSPACE", "is not an absolute path"),
            id="relative-workspace",
        ),
        pytest.param(
            {**BASE, **CONTAINER, "FACTORY_WORKSPACE": "srv/work", STAGE_ENVIRONMENT: "container"},
            ("FACTORY_WORKSPACE", "is not an absolute path"),
            id="relative-workspace-with-setting",
        ),
        pytest.param(
            {**BASE, **CONTAINER, "FACTORY_WORKSPACE": "/work"},
            ("FACTORY_CHECKOUT", "/work/checkout lies inside FACTORY_WORKSPACE"),
            id="default-checkout-in-workspace",
        ),
        pytest.param(dict(BASE), None, id="without-the-three"),
    ],
)
def test_the_stage_environment_setting_is_read_by_nothing(
    environ: dict[str, str], fault: tuple[str, str] | None
) -> None:
    if fault is not None:
        with pytest.raises(SettingsInvalid) as raised:
            read_settings(environ)
        assert (raised.value.variable, raised.value.fault) == fault
        return
    without = {name: value for name, value in environ.items() if name != STAGE_ENVIRONMENT}

    assert read_settings(environ) == read_settings(without)


def _built_directly(workspace: Path | None, checkout: Path, state_directory: Path) -> str:
    try:
        InstanceSettings(
            repository_url="/srv/project.git",
            instance="factory-1",
            agent_home=AGENT_HOME,
            checkout=checkout,
            state_directory=state_directory,
            workspace=workspace,
        )
    except ValidationError as error:
        return str(error)
    return ""


@pytest.mark.parametrize(
    ("fault_of", "workspace", "checkout", "state_directory", "expected"),
    [
        pytest.param(
            workspace_overlap_fault,
            WORKSPACE,
            OUTER_CHECKOUT,
            INNER_STATE,
            ("FACTORY_STATE", f"{INNER_STATE} lies inside FACTORY_WORKSPACE"),
            id="state-inside",
        ),
        pytest.param(
            workspace_overlap_fault,
            Path("srv/work"),
            Path("srv/work/checkout"),
            OUTER_STATE,
            ("FACTORY_WORKSPACE", "is not an absolute path"),
            id="relative-before-checkout",
        ),
        pytest.param(
            workspace_overlap_fault,
            WORKSPACE,
            INNER_CHECKOUT,
            INNER_STATE,
            ("FACTORY_CHECKOUT", f"{INNER_CHECKOUT} lies inside FACTORY_WORKSPACE"),
            id="checkout-before-state",
        ),
        pytest.param(
            workspace_overlap_fault, None, INNER_CHECKOUT, INNER_STATE, None, id="no-workspace"
        ),
        pytest.param(
            _built_directly,
            WORKSPACE,
            INNER_CHECKOUT,
            OUTER_STATE,
            f"FACTORY_CHECKOUT: {INNER_CHECKOUT} lies inside FACTORY_WORKSPACE",
            id="built-directly",
        ),
    ],
)
def test_a_workspace_refuses_a_relative_path_and_an_inner_checkout_or_state(
    fault_of: Callable[[Path | None, Path, Path], object],
    workspace: Path | None,
    checkout: Path,
    state_directory: Path,
    expected: object,
) -> None:
    found = fault_of(workspace, checkout, state_directory)

    if isinstance(expected, str):
        assert isinstance(found, str)
        assert expected in found
        return
    assert found == expected
