"""The kernel's write guard, its start wrapper and the tool paths are gone."""

import importlib
import importlib.util
from collections.abc import Callable

import pytest

from factory.application.task import TaskContext
from factory.domain.agent_runs import AgentRunRequest, GuardSettings
from factory.domain.pipeline_definition import PipelineDefinition
from module_names import has_name


@pytest.mark.parametrize(
    "module", ["factory.entry.confine", "factory.adapters.landlock", "factory.domain.confinement"]
)
def test_the_wrapper_and_the_kernel_s_modules_are_gone(module: str) -> None:
    assert importlib.util.find_spec(module) is None


@pytest.mark.parametrize(
    ("check", "expected"),
    [
        pytest.param(
            lambda: has_name("factory.adapters.process", "replace_process"),
            False,
            id="replace-process",
        ),
        pytest.param(
            lambda: has_name("factory.domain.agent_runs", "CONFINE_COMMAND"),
            False,
            id="confine-command",
        ),
        *(
            pytest.param(
                lambda name=name: has_name("factory.domain.pipeline_definition", name),
                False,
                id=name,
            )
            for name in ("tool_path_folder", "HOME_PREFIX", "has_wildcard", "CURRENT_SEGMENT")
        ),
        pytest.param(
            lambda: list(GuardSettings.model_fields),
            ["root", "write_paths", "protected_paths"],
            id="guard-settings-fields",
        ),
        pytest.param(lambda: "guard" in AgentRunRequest.model_fields, False, id="request-guard"),
        pytest.param(
            lambda: "tool_paths" in PipelineDefinition.model_fields,
            False,
            id="definition-tool-paths",
        ),
        pytest.param(lambda: "guard" in TaskContext.model_fields, False, id="context-guard"),
    ],
)
def test_the_names_of_the_kernel_s_guard_and_the_tool_paths_are_gone(
    check: Callable[[], object], expected: object
) -> None:
    assert check() == expected
