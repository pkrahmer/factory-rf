"""The agent files' folder and the image identity file are required, absolute settings."""

from collections.abc import Callable
from pathlib import Path

import pytest

import factory.domain.settings as settings_module
from factory.domain.errors import SettingsInvalid
from factory.domain.settings import read_settings
from settings_support import BASE
from source_search import modules, string_literals

AGENT_HOME = "FACTORY_CLAUDE_HOME"
IMAGE_ID_FILE = "FACTORY_IMAGE_ID_FILE"
OLD_IMAGE_PATH = "/opt/factory/image-id"
MISSING = "missing"
NOT_ABSOLUTE = "is not an absolute path"
WITHOUT_AGENT_HOME = {name: value for name, value in BASE.items() if name != AGENT_HOME}
ANN = {"HOME": "/home/ann"}


class RecordingReader:
    """A file reader that records every path it is asked for and answers `build-7`."""

    def __init__(self) -> None:
        self.paths: list[Path] = []

    def __call__(self, path: Path) -> str:
        self.paths.append(path)
        return "build-7\n"


def _missing_agent_home_rows() -> list[object]:
    rows: list[object] = []
    for label, value in (("unset", None), ("empty", ""), ("blank", "  ")):
        for home_label, home in (("without-home", {}), ("with-home", ANN)):
            variables = dict(home) if value is None else {**home, AGENT_HOME: value}
            rows.append(pytest.param(variables, MISSING, id=f"{label}-{home_label}"))
    return rows


@pytest.mark.parametrize(
    ("variables", "expected"),
    [
        *_missing_agent_home_rows(),
        pytest.param({AGENT_HOME: "srv/agents"}, NOT_ABSOLUTE, id="relative"),
        pytest.param({AGENT_HOME: "/srv/agents"}, Path("/srv/agents"), id="absolute-without-home"),
        pytest.param(
            {AGENT_HOME: "/srv/agents", **ANN}, Path("/srv/agents"), id="absolute-with-home"
        ),
    ],
)
def test_the_agent_files_folder_is_a_required_absolute_path(
    variables: dict[str, str], expected: Path | str
) -> None:
    environ = {**WITHOUT_AGENT_HOME, **variables}

    if isinstance(expected, Path):
        assert read_settings(environ).agent_home == expected
    else:
        with pytest.raises(SettingsInvalid) as raised:
            read_settings(environ)
        assert (raised.value.variable, raised.value.fault) == (AGENT_HOME, expected)


@pytest.mark.parametrize(
    ("variables", "expected"),
    [
        pytest.param({}, MISSING, id="unset"),
        pytest.param({IMAGE_ID_FILE: ""}, MISSING, id="empty"),
        pytest.param({IMAGE_ID_FILE: "  "}, MISSING, id="blank"),
        pytest.param({IMAGE_ID_FILE: "image-id"}, NOT_ABSOLUTE, id="relative"),
        pytest.param({IMAGE_ID_FILE: "/srv/factory/vm/image-id"}, "build-7", id="absolute"),
    ],
)
def test_with_a_reader_the_image_identity_file_is_a_required_absolute_path(
    variables: dict[str, str], expected: str
) -> None:
    reader = RecordingReader()

    if expected == "build-7":
        assert read_settings(BASE | variables, reader).image == "build-7"
        assert reader.paths == [Path("/srv/factory/vm/image-id")]
    else:
        with pytest.raises(SettingsInvalid) as raised:
            read_settings(BASE | variables, reader)
        assert (raised.value.variable, raised.value.fault) == (IMAGE_ID_FILE, expected)
        assert reader.paths == []


@pytest.mark.parametrize(
    "variables",
    [
        pytest.param({}, id="unset"),
        pytest.param({IMAGE_ID_FILE: "image-id"}, id="relative"),
        pytest.param({IMAGE_ID_FILE: "/srv/x"}, id="absolute"),
    ],
)
def test_without_a_reader_the_image_identity_file_is_not_read(variables: dict[str, str]) -> None:
    assert read_settings(BASE | variables).image is None


def _no_image_id_file_constant() -> bool:
    return not hasattr(settings_module, "IMAGE_ID_FILE")


def _no_old_image_path_in_the_source() -> bool:
    literals = [literal for tree in modules().values() for literal in string_literals(tree)]
    return not any(OLD_IMAGE_PATH in literal for literal in literals)


def _agent_home_not_under_home() -> bool:
    environ = {**BASE, AGENT_HOME: "/srv/agents", **ANN}
    return read_settings(environ).agent_home != Path("/home/ann/.claude")


@pytest.mark.parametrize(
    "gone",
    [
        pytest.param(_no_image_id_file_constant, id="image-id-file-constant"),
        pytest.param(_no_old_image_path_in_the_source, id="old-image-path"),
        pytest.param(_agent_home_not_under_home, id="agent-home-under-home"),
    ],
)
def test_the_old_defaults_of_the_two_paths_are_gone(gone: Callable[[], bool]) -> None:
    assert gone()
