"""The compose file: a restart policy, the health check, required settings and the volumes."""

import re
from pathlib import Path

import pytest
from ruamel.yaml import YAML

ROOT = Path(__file__).parent.parent
COMPOSE = ROOT / "image" / "compose.yml"


@pytest.fixture
def service() -> dict[str, object]:
    """Return the service `factory` of the compose file."""
    loaded = YAML(typ="safe").load(COMPOSE.read_text(encoding="utf-8"))
    services = loaded["services"]
    assert isinstance(services, dict)
    found = services["factory"]
    assert isinstance(found, dict)
    return found


def test_the_service_restarts_unless_stopped_and_runs_the_health_check(
    service: dict[str, object],
) -> None:
    assert service["restart"] == "unless-stopped"
    assert service["healthcheck"] == {
        "test": ["CMD", "python", "-m", "factory.entry.health"],
        "interval": "30s",
        "timeout": "10s",
        "retries": 3,
        "start_period": "60s",
    }
    build = service["build"]
    assert isinstance(build, dict)
    assert (build["context"], build["dockerfile"]) == ("..", "image/Dockerfile")


@pytest.mark.parametrize("name", ["FACTORY_REPOSITORY_URL", "FACTORY_INSTANCE"])
def test_each_required_variable_refuses_to_start_unset_and_has_no_default(
    service: dict[str, object], name: str
) -> None:
    environment = service["environment"]
    assert isinstance(environment, dict)
    value = environment[name]

    assert re.fullmatch(rf"\$\{{{name}:\?[^}}]+\}}", value)
    assert ":-" not in value


def test_the_image_label_defaults_to_unlabelled(service: dict[str, object]) -> None:
    build = service["build"]
    assert isinstance(build, dict)

    assert build["args"]["FACTORY_IMAGE"] == "${FACTORY_IMAGE:-unlabelled}"


def test_the_three_volumes_are_mounted_and_declared() -> None:
    loaded = YAML(typ="safe").load(COMPOSE.read_text(encoding="utf-8"))

    assert loaded["services"]["factory"]["volumes"] == [
        "work:/work",
        "state:/state",
        "claude-home:/home/agent/.claude",
    ]
    assert set(loaded["volumes"]) == {"work", "state", "claude-home"}
