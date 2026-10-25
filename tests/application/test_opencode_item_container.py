"""The preflight item `opencode` of a container instance checks the model aliases only."""

import pytest

from container_support import CONTAINER
from factory.application.preflight import opencode_item
from factory.domain.settings import InstanceSettings


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


@pytest.mark.parametrize(
    ("models", "detail"),
    [
        pytest.param(["opus"], None, id="mapped"),
        pytest.param(
            ["opus", "sonnet"],
            "no model is set for sonnet in FACTORY_OPENCODE_MODELS",
            id="unmapped-alias",
        ),
    ],
)
def test_a_container_instance_s_opencode_item_ignores_the_path_and_checks_the_aliases(
    models: list[str], detail: str | None
) -> None:
    item = opencode_item(_settings(CONTAINER), models)

    assert item.name == "opencode"
    assert item.passed == (detail is None)
    assert item.detail == ("" if detail is None else detail)
