"""The tool paths of the pipeline definition: their form, their faults and the verdict."""

from pathlib import Path

import pytest

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.agent_runs import GuardSettings
from factory.domain.errors import PipelineDefinitionInvalid
from factory.domain.write_paths import refusal
from git_support import PIPELINE_YAML

REFUSED = [
    "*.log",
    ".venv",
    "/var/cache/*",
    "../x/*",
    "a/../b/*",
    "a/*/b/*",
    "a/b?/*",
    "a/[b]/*",
    "~/*",
    "~/../x/*",
    "a//b/*",
    "./*",
    "a/./b/*",
    "~/./*",
]


def _with_tool_paths(value: str) -> str:
    return PIPELINE_YAML + f"tool_paths: {value}\n"


def _fault(path: str) -> str:
    return f"tool path {path}: must be <folder>/* or ~/<folder>/*"


def _outcome(text: str) -> str | None:
    """The fault of a refused text, or `None` when the text is accepted."""
    try:
        RuamelPipelineDefinitionReader().parse(text)
    except PipelineDefinitionInvalid as error:
        return error.fault
    return None


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param(
            _with_tool_paths('[".venv/*", "a/b/*", "~/.cache/*"]'),
            [".venv/*", "a/b/*", "~/.cache/*"],
            id="three",
        ),
        pytest.param(PIPELINE_YAML, [], id="absent"),
    ],
)
def test_the_tool_paths_load_in_order_and_default_to_none(text: str, expected: list[str]) -> None:
    definition = RuamelPipelineDefinitionReader().parse(text)

    assert definition.tool_paths == expected


@pytest.mark.parametrize(
    ("value", "faults"),
    [
        *(pytest.param(f'["{path}"]', [_fault(path)], id=path) for path in REFUSED),
        pytest.param('["*.log", "a//b/*"]', [_fault("*.log"), _fault("a//b/*")], id="two"),
        pytest.param(
            '".venv/*"', ["invalid tool_paths: Input should be a valid list"], id="string"
        ),
    ],
)
def test_a_tool_path_of_neither_folder_form_is_refused(value: str, faults: list[str]) -> None:
    fault = _outcome(_with_tool_paths(value))

    assert fault is not None
    assert sorted(fault.split("; ")) == sorted(faults)


@pytest.mark.parametrize(
    ("tool_paths", "path", "expected"),
    [
        pytest.param(
            None, ".venv/x", ".venv/x is outside the write paths of this stage.", id="default-tool"
        ),
        pytest.param(None, "src/x", None, id="default-write"),
        pytest.param(
            [".venv/*"], ".venv/x", ".venv/x is outside the write paths of this stage.", id="tool"
        ),
        pytest.param([".venv/*"], "src/x", None, id="write"),
    ],
)
def test_the_verdict_ignores_the_tool_paths(
    tool_paths: list[str] | None, path: str, expected: str | None
) -> None:
    root = Path("/work/checkout")
    if tool_paths is None:
        guard = GuardSettings(root=root, write_paths=["src/*"], protected_paths=[])
    else:
        guard = GuardSettings(
            root=root, write_paths=["src/*"], protected_paths=[], tool_paths=tool_paths
        )

    assert guard.tool_paths == (tool_paths or [])
    assert refusal(path, guard) == expected
