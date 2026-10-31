"""The setting that chooses the container profile of an instance."""

import pytest

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import CONTAINER_PROFILE_VARIABLE, read_settings
from settings_support import BASE


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, "rootless", id="unset"),
        pytest.param("", "rootless", id="empty"),
        pytest.param(" ", "rootless", id="blank"),
        pytest.param("job", "job", id="job"),
        pytest.param("Job", None, id="capital"),
        pytest.param("root", None, id="root"),
        pytest.param("job now", None, id="job-now"),
    ],
)
def test_the_container_profile_is_rootless_by_default_or_job(
    value: str | None, expected: str | None
) -> None:
    environ = dict(BASE)
    if value is not None:
        environ[CONTAINER_PROFILE_VARIABLE] = value

    if expected is None:
        with pytest.raises(SettingsInvalid) as raised:
            read_settings(environ)
        assert raised.value.variable == "FACTORY_CONTAINER_PROFILE"
        assert "is neither rootless nor job" in raised.value.fault
        return
    assert read_settings(environ).container_profile == expected
