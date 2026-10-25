"""`FACTORY_OPENCODE_FOLDERS` is read by nothing: an instance that sets it starts as before."""

import pytest

from factory.domain.settings import read_settings
from settings_support import BASE


@pytest.mark.parametrize(
    "folders",
    [
        pytest.param(".local/x", id="inside-the-home"),
        pytest.param("/etc", id="absolute"),
    ],
)
def test_the_opencode_folders_variable_changes_no_setting(folders: str) -> None:
    settings = read_settings({**BASE, "FACTORY_OPENCODE_FOLDERS": folders})

    assert settings == read_settings(BASE)
