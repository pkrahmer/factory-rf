"""The inline environment, its setting and the items only it ran are gone."""

import dataclasses
from collections.abc import Callable
from pathlib import Path

import pytest

from factory.application import preflight, stage_environment
from factory.application.boundaries import Boundaries
from factory.domain import settings
from factory.domain.settings import InstanceSettings

SETUP = Path(__file__).resolve().parents[1] / "vm" / "setup.sh"


def _required_without_default(name: str) -> bool:
    [field] = [field for field in dataclasses.fields(Boundaries) if field.name == name]
    return field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING


@pytest.mark.parametrize(
    "holds",
    [
        pytest.param(
            lambda: not hasattr(stage_environment, "InlineEnvironment"), id="inline-environment"
        ),
        pytest.param(
            lambda: not hasattr(settings, "STAGE_ENVIRONMENT_VARIABLE"), id="stage-variable"
        ),
        pytest.param(lambda: not hasattr(settings, "StageEnvironmentName"), id="stage-name"),
        pytest.param(
            lambda: "stage_environment" not in InstanceSettings.model_fields,
            id="no-stage-environment-field",
        ),
        pytest.param(
            lambda: {"dataset", "workspace", "stage_image"} <= set(InstanceSettings.model_fields),
            id="container-fields-kept",
        ),
        pytest.param(
            lambda: not hasattr(preflight, "agent_environment_item"),
            id="agent-environment-item",
        ),
        pytest.param(lambda: preflight.REQUIRED_TOOLS == ("git", "uv"), id="required-tools"),
        pytest.param(lambda: _required_without_default("snapshots"), id="snapshots-required"),
        pytest.param(lambda: _required_without_default("containers"), id="containers-required"),
        pytest.param(lambda: not hasattr(preflight, "CONTAINER_TOOLS"), id="container-tools"),
        pytest.param(
            lambda: "FACTORY_STAGE_ENVIRONMENT" not in SETUP.read_text(encoding="utf-8"),
            id="setup-script",
        ),
    ],
)
def test_the_inline_environment_s_names_are_gone(holds: Callable[[], bool]) -> None:
    assert holds()
