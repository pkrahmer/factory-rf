"""The instance's settings, read from its environment and its image identity file."""

from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import ValidationError

from factory.domain.errors import FactoryError, SettingsInvalid
from factory.domain.git import GitIdentity
from factory.domain.settings import InstanceSettings, read_settings
from settings_support import BASE, raising

URL = "/srv/project.git"
OTHER_IMAGE_PATH = Path("/images/image-id")


def _reader(files: dict[Path, str]) -> Callable[[Path], str]:
    def read_file(path: Path) -> str:
        if path not in files:
            raise FileNotFoundError(path)
        return files[path]

    return read_file


def _variable_of(environ: dict[str, str], read_file: Callable[[Path], str] | None = None) -> str:
    with pytest.raises(SettingsInvalid) as raised:
        read_settings(environ, read_file)
    return raised.value.variable


def test_the_two_required_variables_give_the_settings_and_their_defaults() -> None:
    settings = read_settings(BASE)

    assert settings.repository_url == URL
    assert settings.instance == "factory-1"
    assert settings.git_identity == GitIdentity(name="factory", email="factory@noreply.invalid")
    assert settings.checkout == Path("/work/checkout")
    assert settings.state_directory == Path("/state")
    assert settings.agent_home == Path("/srv/factory/factory-1/factory/claude")


@pytest.mark.parametrize(
    "variable", ["FACTORY_REPOSITORY_URL", "FACTORY_INSTANCE", "FACTORY_CLAUDE_HOME"]
)
@pytest.mark.parametrize("value", [None, "", "   "])
def test_a_missing_or_blank_required_variable_is_refused(variable: str, value: str | None) -> None:
    environ = {key: text for key, text in BASE.items() if key != variable}
    if value is not None:
        environ[variable] = value

    assert _variable_of(environ) == variable


@pytest.mark.parametrize(
    ("url", "accepted"),
    [("a/b,c/d", False), ("a b", False), ("https://github.com/owner/project.git", True)],
)
def test_a_repository_url_names_one_repository(url: str, accepted: bool) -> None:
    environ = {**BASE, "FACTORY_REPOSITORY_URL": url}

    if accepted:
        assert read_settings(environ).repository_url == url
    else:
        assert _variable_of(environ) == "FACTORY_REPOSITORY_URL"


@pytest.mark.parametrize(
    ("name", "accepted"),
    [
        ("factory-1", True),
        ("a", True),
        ("Factory-1", False),
        ("1st", False),
        ("factory_1", False),
        ("-x", False),
    ],
)
def test_an_instance_name_must_be_a_name(name: str, accepted: bool) -> None:
    environ = {**BASE, "FACTORY_INSTANCE": name}

    if accepted:
        assert read_settings(environ).instance == name
    else:
        assert _variable_of(environ) == "FACTORY_INSTANCE"


def test_a_variable_the_settings_do_not_name_is_not_read() -> None:
    environ = {
        **BASE,
        "FACTORY_STATE_DIRECTORY": "/elsewhere/state",
        "SOMETHING_ELSE": "x",
    }

    settings = read_settings(environ)

    assert settings.checkout == Path("/work/checkout")
    assert settings.state_directory == Path("/state")


def test_the_commit_identity_is_read_from_the_environment() -> None:
    environ = {**BASE, "GIT_USER_NAME": "Ann", "GIT_USER_EMAIL": "ann@example.invalid"}

    assert read_settings(environ).git_identity == GitIdentity(
        name="Ann", email="ann@example.invalid"
    )


@pytest.mark.parametrize(
    ("variables", "identity"),
    [
        ({"GIT_USER_NAME": "Ann"}, GitIdentity(name="Ann", email="factory@noreply.invalid")),
        (
            {"GIT_USER_EMAIL": "ann@example.invalid"},
            GitIdentity(name="factory", email="ann@example.invalid"),
        ),
        (
            {"GIT_USER_NAME": "   ", "GIT_USER_EMAIL": "ann@example.invalid"},
            GitIdentity(name="factory", email="ann@example.invalid"),
        ),
        (
            {"GIT_USER_NAME": "Ann", "GIT_USER_EMAIL": "   "},
            GitIdentity(name="Ann", email="factory@noreply.invalid"),
        ),
        ({"GIT_USER_NAME": " Ann "}, GitIdentity(name="Ann", email="factory@noreply.invalid")),
    ],
)
def test_each_half_of_the_commit_identity_falls_back_to_its_default(
    variables: dict[str, str], identity: GitIdentity
) -> None:
    assert read_settings({**BASE, **variables}).git_identity == identity


@pytest.mark.parametrize(
    ("variables", "files", "image"),
    [
        (
            {"FACTORY_IMAGE_ID_FILE": str(OTHER_IMAGE_PATH)},
            {OTHER_IMAGE_PATH: "build-7\n"},
            "build-7",
        ),
    ],
)
def test_the_image_identity_is_read_from_its_file(
    variables: dict[str, str], files: dict[Path, str], image: str
) -> None:
    assert read_settings({**BASE, **variables}, _reader(files)).image == image


def test_without_a_reader_there_is_no_image_identity() -> None:
    assert read_settings(BASE).image is None


@pytest.mark.parametrize(
    "read_file",
    [
        _reader({}),
        raising(PermissionError("denied")),
        _reader({OTHER_IMAGE_PATH: ""}),
        _reader({OTHER_IMAGE_PATH: "   "}),
    ],
    ids=["missing", "unreadable", "empty", "spaces"],
)
def test_an_image_identity_file_that_gives_no_identity_is_refused(
    read_file: Callable[[Path], str],
) -> None:
    environ = {**BASE, "FACTORY_IMAGE_ID_FILE": str(OTHER_IMAGE_PATH)}

    assert _variable_of(environ, read_file) == "FACTORY_IMAGE_ID_FILE"


def test_the_image_label_variable_is_not_the_image_identity() -> None:
    environ = {**BASE, "FACTORY_IMAGE": "other", "FACTORY_IMAGE_ID_FILE": str(OTHER_IMAGE_PATH)}

    assert read_settings(environ, _reader({OTHER_IMAGE_PATH: "build-7\n"})).image == "build-7"
    assert read_settings(environ).image is None


@pytest.mark.parametrize(("name", "accepted"), [("factory-1", True), ("Factory-1", False)])
def test_the_settings_model_checks_the_instance_name(name: str, accepted: bool) -> None:
    if accepted:
        assert InstanceSettings(repository_url=URL, instance=name).instance == name
    else:
        with pytest.raises(ValidationError):
            InstanceSettings(repository_url=URL, instance=name)


@pytest.mark.parametrize(
    ("environ", "variable"),
    [
        ({}, "FACTORY_REPOSITORY_URL"),
        ({"FACTORY_REPOSITORY_URL": URL, "FACTORY_INSTANCE": "Factory-1"}, "FACTORY_INSTANCE"),
    ],
)
def test_the_first_fault_is_reported(environ: dict[str, str], variable: str) -> None:
    assert _variable_of(environ, _reader({})) == variable


def test_settings_invalid_names_the_variable_and_the_fault() -> None:
    error = SettingsInvalid("FACTORY_INSTANCE", "missing")

    assert error.variable == "FACTORY_INSTANCE"
    assert error.fault == "missing"
    assert str(error) == "FACTORY_INSTANCE: missing"
    assert isinstance(error, FactoryError)


@pytest.mark.parametrize(
    ("url", "accepted"),
    [
        ("https://user:" + "example-value" + "@github.com/owner/project.git", False),
        ("ssh://git:" + "example-value" + "@github.com/owner/project.git", False),
        ("ssh://git@github.com/owner/project.git", True),
        ("ssh://git@github.com:22/owner/project.git", True),
        ("git@github.com:owner/project.git", True),
        ("https://user@github.com/owner/project.git", True),
    ],
)
def test_a_repository_url_with_a_password_is_refused(url: str, accepted: bool) -> None:
    environ = {**BASE, "FACTORY_REPOSITORY_URL": url}

    if accepted:
        assert read_settings(environ).repository_url == url
    else:
        assert _variable_of(environ) == "FACTORY_REPOSITORY_URL"
