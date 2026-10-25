"""The checkout and the state directory are read from the environment, as absolute paths."""

from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import InstanceSettings, read_settings
from settings_support import BASE, raising

CONTAINER = {
    "FACTORY_DATASET": "tank/factory/vm",
    "FACTORY_STAGE_IMAGE": "factory-stage:1",
}
DIRECT_CONTAINER: dict[str, object] = {
    "dataset": "tank/factory/vm",
    "stage_image": "factory-stage:1",
}
REQUIRED: dict[str, object] = {"repository_url": "/srv/project.git", "instance": "factory-1"}
NOT_ABSOLUTE = "is not an absolute path"


def _fault(
    environ: dict[str, str], read_file: Callable[[Path], str] | None = None
) -> tuple[str, str]:
    with pytest.raises(SettingsInvalid) as raised:
        read_settings(environ, read_file)
    return raised.value.variable, raised.value.fault


@pytest.mark.parametrize(
    ("extra", "checkout", "state_directory"),
    [
        pytest.param({}, "/work/checkout", "/state", id="unset"),
        pytest.param(
            {"FACTORY_CHECKOUT": "/srv/factory/vm/repo", "FACTORY_STATE": "/srv/factory/vm/state"},
            "/srv/factory/vm/repo",
            "/srv/factory/vm/state",
            id="set",
        ),
        pytest.param(
            {"FACTORY_CHECKOUT": "  /srv/factory/vm/repo  "},
            "/srv/factory/vm/repo",
            "/state",
            id="checkout-padded",
        ),
        pytest.param(
            {"FACTORY_STATE": "  /srv/factory/vm/state  "},
            "/work/checkout",
            "/srv/factory/vm/state",
            id="state-padded",
        ),
        pytest.param({"FACTORY_STATE": ""}, "/work/checkout", "/state", id="state-empty"),
        pytest.param({"FACTORY_CHECKOUT": "   "}, "/work/checkout", "/state", id="checkout-blank"),
    ],
)
def test_the_checkout_and_the_state_directory_are_read_with_their_defaults(
    extra: dict[str, str], checkout: str, state_directory: str
) -> None:
    settings = read_settings({**BASE, **extra})

    assert (settings.checkout, settings.state_directory) == (Path(checkout), Path(state_directory))


@pytest.mark.parametrize(
    ("extra", "read_file", "fault"),
    [
        pytest.param(
            {"FACTORY_CHECKOUT": "srv/repo"},
            None,
            ("FACTORY_CHECKOUT", NOT_ABSOLUTE),
            id="checkout",
        ),
        pytest.param({"FACTORY_STATE": "state"}, None, ("FACTORY_STATE", NOT_ABSOLUTE), id="state"),
        pytest.param(
            {"FACTORY_STATE": "./state"}, None, ("FACTORY_STATE", NOT_ABSOLUTE), id="state-dot"
        ),
        pytest.param(
            {"FACTORY_INSTANCE": "Bad", "FACTORY_CHECKOUT": "relative"},
            None,
            ("FACTORY_INSTANCE", "is not a name"),
            id="instance-before-checkout",
        ),
        pytest.param(
            {"FACTORY_CHECKOUT": "relative", "FACTORY_MIN_FREE_GB": "0"},
            None,
            ("FACTORY_CHECKOUT", NOT_ABSOLUTE),
            id="before-min-free",
        ),
        pytest.param(
            {"FACTORY_CHECKOUT": "relative"},
            raising(OSError("unreadable")),
            ("FACTORY_CHECKOUT", NOT_ABSOLUTE),
            id="checkout-before-image",
        ),
        pytest.param(
            {"FACTORY_STATE": "relative"},
            raising(OSError("unreadable")),
            ("FACTORY_STATE", NOT_ABSOLUTE),
            id="state-before-image",
        ),
        pytest.param(
            {"FACTORY_CHECKOUT": "relative", "FACTORY_STATE": "relative"},
            None,
            ("FACTORY_CHECKOUT", NOT_ABSOLUTE),
            id="checkout-before-state",
        ),
    ],
)
def test_a_relative_checkout_or_state_directory_is_refused_in_its_order(
    extra: dict[str, str], read_file: Callable[[Path], str] | None, fault: tuple[str, str]
) -> None:
    assert _fault({**BASE, **extra}, read_file) == fault


@pytest.mark.parametrize(
    ("fields", "accepted"),
    [
        pytest.param({"checkout": Path("/srv/factory/vm/repo")}, True, id="checkout-absolute"),
        pytest.param({"checkout": Path("srv/repo")}, False, id="checkout-relative"),
        pytest.param({"state_directory": Path("/srv/factory/vm/state")}, True, id="state-absolute"),
        pytest.param({"state_directory": Path("state")}, False, id="state-relative"),
    ],
)
def test_settings_built_directly_refuse_a_relative_checkout_or_state_directory(
    fields: dict[str, object], accepted: bool
) -> None:
    model: type[BaseModel] = InstanceSettings
    if accepted:
        model(**REQUIRED, **fields)
    else:
        with pytest.raises(ValidationError):
            model(**REQUIRED, **fields)


@pytest.mark.parametrize(
    ("extra", "fault"),
    [
        pytest.param(
            {**CONTAINER, "FACTORY_WORKSPACE": "/work"},
            ("FACTORY_CHECKOUT", "/work/checkout lies inside FACTORY_WORKSPACE"),
            id="default-checkout-inside",
        ),
        pytest.param(
            {
                **CONTAINER,
                "FACTORY_WORKSPACE": "/srv/factory/vm/work",
                "FACTORY_CHECKOUT": "/srv/factory/vm/work",
            },
            ("FACTORY_CHECKOUT", "/srv/factory/vm/work lies inside FACTORY_WORKSPACE"),
            id="checkout-is-workspace",
        ),
        pytest.param(
            {
                **CONTAINER,
                "FACTORY_WORKSPACE": "/srv/factory/vm/work",
                "FACTORY_CHECKOUT": "/srv/factory/vm/repo",
                "FACTORY_STATE": "/srv/factory/vm/work/state",
            },
            ("FACTORY_STATE", "/srv/factory/vm/work/state lies inside FACTORY_WORKSPACE"),
            id="state-inside",
        ),
        pytest.param(
            {
                **CONTAINER,
                "FACTORY_WORKSPACE": "/srv/factory/vm/work",
                "FACTORY_CHECKOUT": "/srv/factory/vm/work/checkout",
                "FACTORY_STATE": "/srv/factory/vm/work/state",
            },
            ("FACTORY_CHECKOUT", "/srv/factory/vm/work/checkout lies inside FACTORY_WORKSPACE"),
            id="checkout-first",
        ),
        pytest.param(
            {**CONTAINER, "FACTORY_WORKSPACE": "srv/work"},
            ("FACTORY_WORKSPACE", "is not an absolute path"),
            id="workspace-fault-first",
        ),
        pytest.param(
            {
                **CONTAINER,
                "FACTORY_WORKSPACE": "/srv/factory/vm/work",
                "FACTORY_CHECKOUT": "/srv/factory/vm/repo",
                "FACTORY_STATE": "/srv/factory/vm/state",
            },
            None,
            id="outside",
        ),
        pytest.param(
            {
                **CONTAINER,
                "FACTORY_WORKSPACE": "/srv/factory/vm/work",
                "FACTORY_CHECKOUT": "/srv/factory/vm/workrepo",
                "FACTORY_STATE": "/srv/factory/vm/state",
            },
            None,
            id="sibling",
        ),
        pytest.param(
            {"FACTORY_WORKSPACE": "/work"},
            ("FACTORY_CHECKOUT", "/work/checkout lies inside FACTORY_WORKSPACE"),
            id="inline",
        ),
    ],
)
def test_a_container_instance_keeps_its_checkout_and_state_outside_the_workspace(
    extra: dict[str, str], fault: tuple[str, str] | None
) -> None:
    environ = {**BASE, **extra}
    if fault is not None:
        assert _fault(environ) == fault
    else:
        settings = read_settings(environ)
        assert settings.checkout == Path(environ.get("FACTORY_CHECKOUT", "/work/checkout"))


@pytest.mark.parametrize(
    ("fields", "accepted"),
    [
        pytest.param({"workspace": Path("/work")}, False, id="default-checkout-inside"),
        pytest.param(
            {"workspace": Path("/srv/factory/vm/work"), "checkout": Path("/srv/factory/vm/repo")},
            True,
            id="outside",
        ),
        pytest.param(
            {
                "workspace": Path("/srv/factory/vm/work"),
                "checkout": Path("/srv/factory/vm/repo"),
                "state_directory": Path("/srv/factory/vm/work/state"),
            },
            False,
            id="state-inside",
        ),
    ],
)
def test_settings_built_directly_keep_a_container_checkout_and_state_outside_the_workspace(
    fields: dict[str, object], accepted: bool
) -> None:
    model: type[BaseModel] = InstanceSettings
    if accepted:
        model(**REQUIRED, **DIRECT_CONTAINER, **fields)
    else:
        with pytest.raises(ValidationError):
            model(**REQUIRED, **DIRECT_CONTAINER, **fields)
