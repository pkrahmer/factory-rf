"""The reset of the agent's home is gone, with every module and name that existed only for it."""

import dataclasses
import importlib.util
import inspect
from collections.abc import Callable
from types import ModuleType

import pytest

from factory.adapters import claude_runtime, opencode_runtime
from factory.application.boundaries import Boundaries
from factory.application.sealed_runs import SealedProjectCommands
from factory.domain import settings
from factory.domain.settings import InstanceSettings
from factory.entry import wiring


@pytest.mark.parametrize(
    "module",
    [
        "factory.entry.fresh_home",
        "factory.adapters.agent_home",
        "factory.adapters.home_files",
        "factory.domain.agent_home",
        "factory.application.agent_home",
    ],
)
def test_the_modules_of_the_home_reset_are_gone(module: str) -> None:
    assert importlib.util.find_spec(module) is None


def _lacks(module: ModuleType, name: str) -> Callable[[], bool]:
    return lambda: not hasattr(module, name)


@pytest.mark.parametrize(
    "holds",
    [
        pytest.param(
            lambda: "agent_home" not in {field.name for field in dataclasses.fields(Boundaries)},
            id="boundaries-agent-home",
        ),
        pytest.param(
            lambda: "opencode_folders" not in InstanceSettings.model_fields,
            id="settings-opencode-folders",
        ),
        pytest.param(
            lambda: "agent_home" in InstanceSettings.model_fields, id="settings-keep-agent-home"
        ),
        pytest.param(_lacks(settings, "OPENCODE_FOLDERS_VARIABLE"), id="opencode-folders-variable"),
        pytest.param(_lacks(claude_runtime, "LOGIN_STATE_FILE"), id="claude-login-state-file"),
        pytest.param(_lacks(opencode_runtime, "LOGIN_STATE_FILE"), id="opencode-login-state-file"),
        pytest.param(_lacks(wiring, "fresh_home_command"), id="fresh-home-command"),
        pytest.param(_lacks(wiring, "agent_home_of"), id="agent-home-of"),
        pytest.param(_lacks(wiring, "FRESH_HOME_MODULE"), id="fresh-home-module"),
        pytest.param(_lacks(wiring, "UV_CACHE_FOLDER"), id="uv-cache-folder"),
        pytest.param(
            lambda: (
                list(inspect.signature(SealedProjectCommands.__init__).parameters)
                == ["self", "inner", "git", "log"]
            ),
            id="sealed-project-commands-parameters",
        ),
    ],
)
def test_the_names_of_the_home_reset_are_gone(holds: Callable[[], bool]) -> None:
    assert holds()
