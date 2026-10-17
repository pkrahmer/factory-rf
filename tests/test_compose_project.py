"""The compose project: one name per instance, so instances and v1 keep their own containers."""

import re
from pathlib import Path

import pytest
from ruamel.yaml import YAML

ROOT = Path(__file__).parent.parent
COMPOSE = ROOT / "image" / "compose.yml"
PROJECT_NAME = "factory-${FACTORY_INSTANCE:?set FACTORY_INSTANCE to this instance's name}"
REQUIRED_MESSAGE = re.compile(r"\$\{FACTORY_INSTANCE:\?([^}]+)\}")


@pytest.fixture
def compose() -> dict[str, object]:
    """Return the compose file, loaded with the safe loader."""
    loaded = YAML(typ="safe").load(COMPOSE.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def test_the_project_is_named_after_the_required_instance_without_a_default(
    compose: dict[str, object],
) -> None:
    name = compose["name"]
    assert isinstance(name, str)

    assert next(iter(compose)) == "name"
    assert name == PROJECT_NAME
    assert name.startswith("factory-")
    assert REQUIRED_MESSAGE.search(name)
    assert ":-" not in name


def test_the_project_name_refuses_with_the_same_message_as_the_service_environment(
    compose: dict[str, object],
) -> None:
    name = compose["name"]
    assert isinstance(name, str)
    services = compose["services"]
    assert isinstance(services, dict)
    instance = services["factory"]["environment"]["FACTORY_INSTANCE"]
    assert isinstance(instance, str)

    in_name = REQUIRED_MESSAGE.search(name)
    in_environment = REQUIRED_MESSAGE.fullmatch(instance)
    assert in_name is not None
    assert in_environment is not None
    assert in_name.group(1) == in_environment.group(1)
