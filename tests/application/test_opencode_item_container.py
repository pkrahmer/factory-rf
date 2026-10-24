"""The preflight item `opencode` of a container instance checks the model aliases only."""

from collections.abc import Callable

import pytest

from container_support import CONTAINER
from factory.application.preflight import opencode_item
from factory.domain.settings import InstanceSettings

PATH = "/opt/factory/bin:/usr/bin"
WITH_PATH = {"PATH": PATH, "HOME": "/home/agent"}
WITHOUT_PATH = {"HOME": "/home/agent"}


def _settings(fields: dict[str, object]) -> InstanceSettings:
    return InstanceSettings.model_validate(
        {
            "repository_url": "/srv/project.git",
            "instance": "factory-1",
            "agent_runtime": "opencode",
            "opencode_models": {"opus": "anthropic/claude-opus-5-5"},
            **fields,
        }
    )


def _finds_nothing(_name: str, _path: str) -> str | None:
    return None


def _finds_every_tool(name: str, path: str) -> str | None:
    return f"/usr/bin/{name}" if path else None


@pytest.mark.parametrize(
    ("fields", "environment", "find", "models", "detail"),
    [
        pytest.param(CONTAINER, WITHOUT_PATH, _finds_every_tool, ["opus"], None, id="no-path"),
        pytest.param(CONTAINER, WITH_PATH, _finds_nothing, ["opus"], None, id="not-on-path"),
        pytest.param(
            CONTAINER,
            WITH_PATH,
            _finds_nothing,
            ["opus", "sonnet"],
            "no model is set for sonnet in FACTORY_OPENCODE_MODELS",
            id="unmapped-alias",
        ),
        pytest.param(
            {}, WITHOUT_PATH, _finds_every_tool, ["opus"], "the agent run has no PATH", id="inline"
        ),
    ],
)
def test_a_container_instance_s_opencode_item_ignores_the_path_and_checks_the_aliases(
    fields: dict[str, object],
    environment: dict[str, str],
    find: Callable[[str, str], str | None],
    *,
    models: list[str],
    detail: str | None,
) -> None:
    item = opencode_item(_settings(fields), environment, find, models)

    assert item.name == "opencode"
    assert item.passed == (detail is None)
    assert item.detail == ("" if detail is None else detail)
