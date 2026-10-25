"""A pipeline definition that holds `tool_paths` is refused as an unknown key."""

from pathlib import Path

import pytest

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from git_support import PIPELINE_YAML, pipeline_outcome

ROOT = Path(__file__).parent.parent.parent


@pytest.mark.parametrize(
    ("text", "refused"),
    [
        pytest.param(PIPELINE_YAML, False, id="without-tool-paths"),
        pytest.param(PIPELINE_YAML + 'tool_paths: [".venv/*"]\n', True, id="with-tool-paths"),
    ],
)
def test_a_definition_with_tool_paths_is_refused(text: str, *, refused: bool) -> None:
    fault = pipeline_outcome(text)

    if refused:
        assert fault is not None
        assert "tool_paths" in fault
    else:
        assert fault is None


@pytest.mark.parametrize("path", ["template/factory/pipeline.yml", "factory/pipeline.yml"])
def test_the_shipped_definitions_hold_no_tool_paths_and_load(path: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")

    assert "tool_paths" not in text
    RuamelPipelineDefinitionReader().parse(text)
