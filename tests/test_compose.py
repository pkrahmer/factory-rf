"""The compose file: a restart policy, the health check, required settings and the volumes."""

import re

import pytest
from ruamel.yaml import YAML

from compose_support import COMPOSE


def test_the_service_restarts_unless_stopped_and_runs_the_health_check(
    compose_service: dict[str, object],
) -> None:
    assert compose_service["restart"] == "unless-stopped"
    assert compose_service["healthcheck"] == {
        "test": ["CMD", "python", "-m", "factory.entry.health"],
        "interval": "30s",
        "timeout": "10s",
        "retries": 3,
        "start_period": "60s",
    }
    build = compose_service["build"]
    assert isinstance(build, dict)
    assert (build["context"], build["dockerfile"]) == ("..", "image/Dockerfile")


@pytest.mark.parametrize("name", ["FACTORY_REPOSITORY_URL", "FACTORY_INSTANCE"])
def test_each_required_variable_refuses_to_start_unset_and_has_no_default(
    compose_service: dict[str, object], name: str
) -> None:
    environment = compose_service["environment"]
    assert isinstance(environment, dict)
    value = environment[name]

    assert re.fullmatch(rf"\$\{{{name}:\?[^}}]+\}}", value)
    assert ":-" not in value


def test_the_image_label_defaults_to_unlabelled(compose_service: dict[str, object]) -> None:
    build = compose_service["build"]
    assert isinstance(build, dict)

    assert build["args"]["FACTORY_IMAGE"] == "${FACTORY_IMAGE:-unlabelled}"


def test_the_three_volumes_are_mounted_and_declared() -> None:
    loaded = YAML(typ="safe").load(COMPOSE.read_text(encoding="utf-8"))

    assert loaded["services"]["factory"]["volumes"] == [
        "work:/work",
        "state:/state",
        "claude-home:/home/agent/.claude",
        {
            "type": "bind",
            "source": "./secrets/claude-token",
            "target": "/home/agent/.claude-token",
            "read_only": True,
            "bind": {"create_host_path": False},
        },
        {
            "type": "bind",
            "source": "${FACTORY_API_KEY_FILE:-./secrets/anthropic-api-key}",
            "target": "/home/agent/.anthropic-api-key",
            "read_only": True,
            "bind": {"create_host_path": False},
        },
        {
            "type": "bind",
            "source": "./secrets/hosting-token",
            "target": "/home/factory/.secrets/hosting-token",
            "read_only": True,
            "bind": {"create_host_path": False},
        },
    ]
    assert set(loaded["volumes"]) == {"work", "state", "claude-home"}
