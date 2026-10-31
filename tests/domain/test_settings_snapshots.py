"""The settings read which snapshots the stage environment uses and the copy's base directory."""

from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import (
    SNAPSHOT_BASE_VARIABLE,
    SNAPSHOTS_VARIABLE,
    InstanceSettings,
    read_settings,
)
from settings_support import AGENT_HOME, BASE

# A workspace apart from a checkout and a state directory, so that each overlap has its own rows.
APART = {
    "FACTORY_WORKSPACE": "/work",
    "FACTORY_CHECKOUT": "/srv/repo",
    "FACTORY_STATE": "/opt/state",
}
COPY = {SNAPSHOTS_VARIABLE: "copy", **APART}
ONLY_COPY = "is only used with FACTORY_SNAPSHOTS=copy"


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        pytest.param({}, "zfs", id="unset"),
        pytest.param({SNAPSHOTS_VARIABLE: "  "}, "zfs", id="blank"),
        pytest.param({SNAPSHOTS_VARIABLE: "zfs"}, "zfs", id="zfs"),
        pytest.param({SNAPSHOTS_VARIABLE: "copy"}, "copy", id="copy"),
        pytest.param({SNAPSHOTS_VARIABLE: "ZFS"}, None, id="upper-case"),
        pytest.param({SNAPSHOTS_VARIABLE: "btrfs"}, None, id="btrfs"),
        pytest.param({SNAPSHOTS_VARIABLE: "copy now"}, None, id="two-words"),
    ],
)
def test_the_snapshots_setting_is_zfs_or_copy(extra: dict[str, str], expected: str | None) -> None:
    if expected is None:
        with pytest.raises(SettingsInvalid) as raised:
            read_settings({**BASE, **extra})
        assert (raised.value.variable, raised.value.fault) == (
            SNAPSHOTS_VARIABLE,
            "is neither zfs nor copy",
        )
        return

    assert read_settings({**BASE, **extra}).snapshots == expected


def _overlaps(base: str, what: str) -> tuple[str, str]:
    return SNAPSHOT_BASE_VARIABLE, f"{base} overlaps {what}"


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        pytest.param(COPY, None, id="unset"),
        pytest.param({**COPY, SNAPSHOT_BASE_VARIABLE: "  "}, None, id="blank"),
        pytest.param(
            {**COPY, SNAPSHOT_BASE_VARIABLE: "/var/base"}, Path("/var/base"), id="absolute"
        ),
        pytest.param(
            {**COPY, SNAPSHOT_BASE_VARIABLE: "base"},
            (SNAPSHOT_BASE_VARIABLE, "is not an absolute path"),
            id="relative",
        ),
        pytest.param(
            {**COPY, SNAPSHOT_BASE_VARIABLE: "/work"},
            _overlaps("/work", "workspace"),
            id="the-workspace",
        ),
        pytest.param(
            {**COPY, SNAPSHOT_BASE_VARIABLE: "/work/b"},
            _overlaps("/work/b", "workspace"),
            id="inside-the-workspace",
        ),
        pytest.param(
            {**COPY, SNAPSHOT_BASE_VARIABLE: "/"},
            _overlaps("/", "workspace"),
            id="holding-the-workspace",
        ),
        pytest.param(
            {**COPY, SNAPSHOT_BASE_VARIABLE: "/work2"}, Path("/work2"), id="beside-the-workspace"
        ),
        pytest.param(
            {**COPY, SNAPSHOT_BASE_VARIABLE: "/srv/repo"},
            _overlaps("/srv/repo", "checkout"),
            id="the-checkout",
        ),
        pytest.param(
            {**COPY, SNAPSHOT_BASE_VARIABLE: "/srv"},
            _overlaps("/srv", "checkout"),
            id="holding-the-checkout",
        ),
        pytest.param(
            {**COPY, SNAPSHOT_BASE_VARIABLE: "/srv/base"},
            Path("/srv/base"),
            id="beside-the-checkout",
        ),
        pytest.param(
            {**COPY, SNAPSHOT_BASE_VARIABLE: "/opt/state"},
            _overlaps("/opt/state", "state"),
            id="the-state-directory",
        ),
        pytest.param(
            {**COPY, SNAPSHOT_BASE_VARIABLE: "/opt"},
            _overlaps("/opt", "state"),
            id="holding-the-state-directory",
        ),
        pytest.param(
            {**COPY, SNAPSHOT_BASE_VARIABLE: "/opt/base"},
            Path("/opt/base"),
            id="beside-the-state-directory",
        ),
        pytest.param(
            {**APART, SNAPSHOT_BASE_VARIABLE: "/var/base"},
            (SNAPSHOT_BASE_VARIABLE, ONLY_COPY),
            id="zfs-unset",
        ),
        pytest.param(
            {**APART, SNAPSHOTS_VARIABLE: "zfs", SNAPSHOT_BASE_VARIABLE: "/var/base"},
            (SNAPSHOT_BASE_VARIABLE, ONLY_COPY),
            id="zfs",
        ),
    ],
)
def test_the_snapshot_base_is_an_absolute_path_apart_from_the_factory_s_paths(
    extra: dict[str, str], expected: Path | tuple[str, str] | None
) -> None:
    if isinstance(expected, tuple):
        with pytest.raises(SettingsInvalid) as raised:
            read_settings({**BASE, **extra})
        assert (raised.value.variable, raised.value.fault) == expected
        return

    assert read_settings({**BASE, **extra}).snapshot_base == expected


_DIRECT: dict[str, object] = {
    "repository_url": "/srv/project.git",
    "instance": "factory-1",
    "agent_home": AGENT_HOME,
    "workspace": Path("/work"),
    "checkout": Path("/srv/repo"),
    "state_directory": Path("/opt/state"),
    "snapshots": "copy",
}


@pytest.mark.parametrize(
    ("changes", "accepted"),
    [
        pytest.param({"snapshot_base": Path("/work/b")}, False, id="inside-the-workspace"),
        pytest.param({"snapshot_base": Path("/work")}, False, id="the-workspace"),
        pytest.param({"snapshot_base": Path("/")}, False, id="holding-the-workspace"),
        pytest.param({"snapshot_base": Path("/srv/repo/b")}, False, id="inside-the-checkout"),
        pytest.param({"snapshot_base": Path("/srv/repo")}, False, id="the-checkout"),
        pytest.param({"snapshot_base": Path("/srv")}, False, id="holding-the-checkout"),
        pytest.param({"snapshot_base": Path("/opt/state/b")}, False, id="inside-the-state"),
        pytest.param({"snapshot_base": Path("/opt/state")}, False, id="the-state"),
        pytest.param({"snapshot_base": Path("/opt")}, False, id="holding-the-state"),
        pytest.param({"snapshot_base": Path("/var/base")}, True, id="apart"),
        pytest.param(
            {"snapshots": "zfs", "snapshot_base": Path("/var/base")}, False, id="zfs-with-a-base"
        ),
    ],
)
def test_instance_settings_built_directly_keep_the_snapshot_base_apart(
    changes: dict[str, object], *, accepted: bool
) -> None:
    model: type[BaseModel] = InstanceSettings

    if accepted:
        model(**{**_DIRECT, **changes})
        return
    with pytest.raises(ValidationError):
        model(**{**_DIRECT, **changes})
