"""The setting that names the opencode provider file."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import (
    OPENCODE_PROVIDER_FILE_VARIABLE,
    InstanceSettings,
    read_settings,
)
from settings_support import BASE


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, None, id="unset"),
        pytest.param("  ", None, id="blank"),
        pytest.param("/etc/p.json", Path("/etc/p.json"), id="absolute"),
    ],
)
def test_the_provider_file_setting_is_read_as_an_optional_path(
    value: str | None, expected: Path | None
) -> None:
    environ = dict(BASE)
    if value is not None:
        environ[OPENCODE_PROVIDER_FILE_VARIABLE] = value

    assert OPENCODE_PROVIDER_FILE_VARIABLE == "FACTORY_OPENCODE_PROVIDER_FILE"
    assert read_settings(environ).opencode_provider_file == expected


def test_a_relative_provider_file_setting_is_refused_naming_it() -> None:
    with pytest.raises(SettingsInvalid) as raised:
        read_settings({**BASE, OPENCODE_PROVIDER_FILE_VARIABLE: "p.json"})

    assert raised.value.variable == "FACTORY_OPENCODE_PROVIDER_FILE"
    assert raised.value.fault == "is not an absolute path"


@pytest.mark.parametrize(
    ("path", "accepted"),
    [
        pytest.param(Path("/etc/p.json"), True, id="absolute"),
        pytest.param(Path("p.json"), False, id="relative"),
    ],
)
def test_the_settings_model_takes_only_an_absolute_provider_file(
    path: Path, *, accepted: bool
) -> None:
    def build() -> InstanceSettings:
        return InstanceSettings(
            repository_url="/srv/project.git", instance="factory-1", opencode_provider_file=path
        )

    if accepted:
        assert build().opencode_provider_file == path
    else:
        with pytest.raises(ValidationError):
            build()
